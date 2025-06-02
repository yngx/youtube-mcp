#!/usr/bin/env python3
"""Test script to verify YouTube Transcript API is working"""

from youtube_transcript_api import YouTubeTranscriptApi
import sys

# Test with a known video that should have captions
test_video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up

print(f"Testing YouTube Transcript API with video ID: {test_video_id}")

try:
    transcript = YouTubeTranscriptApi.get_transcript(test_video_id)
    print(f"✓ Success! Retrieved {len(transcript)} transcript segments")
    print(f"First segment: {transcript[0] if transcript else 'No segments'}")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

# Test with custom video ID if provided
if len(sys.argv) > 1:
    custom_id = sys.argv[1]
    print(f"\nTesting with custom video ID: {custom_id}")
    try:
        transcript = YouTubeTranscriptApi.get_transcript(custom_id)
        print(f"✓ Success! Retrieved {len(transcript)} transcript segments")
    except Exception as e:
        print(f"✗ Error: {e}")