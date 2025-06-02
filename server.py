from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from youtube_transcript_api import YouTubeTranscriptApi
from cache import TranscriptionCache
import asyncio
import sys
import re
import time
import logging
from typing import Any, Dict, Text
import random

# Configure logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)

# Create server instance
server = Server("youtube-summarizer")

# Initialize cache lazily
cache = None

def get_cache():
    global cache
    if cache is None:
        # Use a cache directory in the user's home directory
        from pathlib import Path
        cache_dir = Path.home() / ".youtube_mcp_cache"
        cache = TranscriptionCache(cache_dir=str(cache_dir))
    return cache

# Helper function to extract YouTube video Id
def extract_video_id(url: str) -> str:
    """Extract video ID from various YouTube URL formats"""
    # https://gist.github.com/rodrigoborgesdeoliveira/987683cfbfcc8d800192da1e73adc486
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)',
        r'youtube\.com\/watch\?.*v=([^&\s]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    raise ValueError("Could not extract video ID from URL")


def get_transcript_with_cache(video_id: str) -> str:
    """Get transcript with caching"""

    cached_data = get_cache().get(video_id)
    if cached_data:
        logging.info(f"Cache hit for video {video_id}")
        return cached_data

    # Fetch from YouTube
    logging.info(f"Fetching transcript for video {video_id} from YouTube")
    
    try:
        # Try to get transcript with multiple language fallbacks
        transcript_list = None
        error_msg = None
        
        # Add a small random delay to avoid rate limiting
        delay = random.uniform(0.5, 1.5)
        logging.info(f"Waiting {delay:.1f}s before YouTube API call...")
        time.sleep(delay)
        
        try:
            # First try to get any available transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            error_msg = str(e)
            logging.warning(f"Failed to get default transcript: {error_msg}")
            
            # If rate limited, wait longer and retry
            if "429" in str(e) or "no element found" in str(e):
                logging.info("Possible rate limiting detected, waiting 5 seconds...")
                time.sleep(5)
            
            # Try to list available transcripts and get the first one
            try:
                transcript_info = YouTubeTranscriptApi.list_transcripts(video_id)
                for transcript in transcript_info:
                    try:
                        transcript_list = transcript.fetch()
                        logging.info(f"Successfully fetched transcript in language: {transcript.language}")
                        break
                    except:
                        continue
            except Exception as list_error:
                logging.error(f"Failed to list transcripts: {str(list_error)}")
        
        if transcript_list is None:
            if "no element found" in str(error_msg):
                raise Exception(f"YouTube returned empty response. The video may not have captions available, may be private, or YouTube may be temporarily blocking requests. Video ID: {video_id}")
            else:
                raise Exception(f"Could not retrieve transcript: {error_msg}")
                
    except Exception as e:
        logging.error(f"YouTube API error: {str(e)}")
        raise
    if transcript_list:
        last_segment = transcript_list[-1]
        duration_seconds = last_segment['start'] + last_segment['duration']
        duration_minutes = int(duration_seconds / 60)
        
        # Combine all transcript segments into full text
        full_transcript = ' '.join([segment['text'] for segment in transcript_list])
    else:
        duration_seconds = 0
        duration_minutes = 0
        full_transcript = ""

    # Prepare Data
    data = {
        'video_id': video_id,
        'transcript_segments': transcript_list,
        'full_transcript': full_transcript,
        'duration_seconds': duration_seconds,
        'duration_minutes': duration_minutes,
        'fetched_at': time.time()
    }

    # Cache the data
    get_cache().set(video_id, data)
    return data

# Define available tools
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_transcript",
            description="Fetch the transcript of a YouTube video",
            inputSchema={
                "type": "object",
                "properties": {
                    "video_url": {
                        "type": "string",
                        "description": "The YouTube video URL"
                    }
                },
                "required": ["video_url"]
            }
        ),
        Tool(
            name="cache_stats",
            description="Get cache statistics",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

# Handle Tool Execution
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    if name == "get_transcript":
        try:
            video_url = arguments["video_url"]
            use_cache = arguments.get("use_cache", True)
            
            # Log the URL for debugging
            logging.info(f"Processing video URL: {video_url}")
            
            try:
                video_id = extract_video_id(video_url)
                logging.info(f"Extracted video ID: {video_id}")
            except ValueError as e:
                return [TextContent(
                    type="text",
                    text=f"Invalid YouTube URL: {str(e)}"
                )]
            
            if use_cache:
                data = get_transcript_with_cache(video_id)
            else:
                # Force fresh fetch
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                full_transcript = " ".join([entry['text'] for entry in transcript_list])
                
                if transcript_list:
                    last_segment = transcript_list[-1]
                    duration_seconds = last_segment['start'] + last_segment['duration']
                    duration_minutes = int(duration_seconds / 60)
                else:
                    duration_minutes = 0
                
                data = {
                    'full_transcript': full_transcript,
                    'duration_minutes': duration_minutes
                }
            
            response = f"Video duration: {data['duration_minutes']} minutes\n\n{data['full_transcript']}"
            
            return [TextContent(
                type="text",
                text=response
            )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching transcript: {str(e)}"
            )]
    
    elif name == "cache_stats":
        try:
            stats = get_cache().get_stats()
            return [TextContent(
                type="text",
                text=f"Cache Statistics:\n"
                 f"- Total videos cached: {stats['total_videos']}\n"
                 f"- Total cache size: {stats['total_size_mb']} MB\n"
                 f"- Maximum cache size: {stats['max_size_mb']} MB\n"
                 f"- Cache directory: {stats['cache_dir']}\n"
                 f"- Cache expiration: {stats['max_age_hours']} hours"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting stats: {str(e)}"
            )]
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())