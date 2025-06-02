from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
import sys
import re
from typing import Any, Dict

# Create our server
server = Server("youtube-summarizer")

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
        )
    ]

# Handle Tool Execution
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> list[TextContent]:
    if name == "get_transcript":
        try:
            print(f"DEBUG: arguments received: {arguments}", file=sys.stderr)
            video_url = arguments["video_url"]
            video_id = extract_video_id(video_url)

            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            if transcript_list:
                last_segment = transcript_list[-1]
                duration_seconds = last_segment['start'] + last_segment['duration']
                duration_minutes = int(duration_seconds / 60)
                
                # Combine all transcript segments into full text
                full_transcript = ' '.join([segment['text'] for segment in transcript_list])
                
                response = f"Video duration: {duration_minutes} minutes\n\n{full_transcript}"
            else:
                response = "No transcript available for this video"
            
            return [TextContent(
                type="text",
                text=response
            )]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching transcript: {str(e)}"
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