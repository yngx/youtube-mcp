from youtube_transcript_api import YouTubeTranscriptApi
from server import extract_video_id

test_url = "https://www.youtube.com/watch?v=5Byg-9K8JnM"
video_id = extract_video_id(test_url)  # Should extract: 5Byg-9K8JnM

transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
print(f"transcript_list: {transcript_list}")
