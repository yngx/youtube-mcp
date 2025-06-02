#!/usr/bin/env python3
"""Debug YouTube access issues"""

import requests
from youtube_transcript_api import YouTubeTranscriptApi
import time

# Test basic YouTube connectivity
print("1. Testing basic YouTube connectivity...")
try:
    response = requests.get("https://www.youtube.com", timeout=10)
    print(f"   ✓ YouTube.com responded with status {response.status_code}")
except Exception as e:
    print(f"   ✗ Failed to reach YouTube: {e}")

# Test with a simple, known video
test_videos = [
    ("dQw4w9WgXcQ", "Rick Astley - Never Gonna Give You Up"),
    ("jNQXAC9IVRw", "Me at the zoo (first YouTube video)"),
    ("9bZkp7q19f0", "PSY - Gangnam Style")
]

print("\n2. Testing transcript API with known videos...")
for video_id, title in test_videos:
    print(f"\n   Testing: {title} ({video_id})")
    try:
        # Add a small delay between requests
        time.sleep(1)
        
        # Try to get available transcripts
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        available = []
        for t in transcript_list:
            available.append(f"{t.language} ({'auto' if t.is_generated else 'manual'})")
        
        print(f"   ✓ Available transcripts: {', '.join(available)}")
        
        # Try to fetch the first one
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"   ✓ Successfully fetched {len(transcript)} segments")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        if "429" in str(e):
            print("   → This appears to be rate limiting")
        elif "no element found" in str(e):
            print("   → YouTube returned empty response")

# Check if using a different user agent helps
print("\n3. Testing with custom headers...")
try:
    # The library doesn't easily allow custom headers, but we can test the URL directly
    video_id = "dQw4w9WgXcQ"
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers, timeout=10)
    print(f"   ✓ YouTube video page responded with status {response.status_code}")
    if "captcha" in response.text.lower():
        print("   ⚠️  YouTube is showing a CAPTCHA - this indicates bot detection")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\nDiagnosis: Based on the tests above, the issue is likely:")
print("- If all tests fail with 'no element found': YouTube API changes or rate limiting")
print("- If some videos work: Video-specific issues (private, no captions, etc.)")
print("- If CAPTCHA detected: Your IP has been flagged for bot-like behavior")