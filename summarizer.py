import re
from typing import List, Dict, Any, Optional
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class TranscriptSummarizer:
    """Smart summarization for YouTube transcripts"""

    def __init__(self) -> None:
        # Common filler words to filter out
        self.filler_words = {
            'um', 'uh', 'like', 'you know', 'i mean', 'basically', 
            'actually', 'literally', 'right', 'so', 'well'
        }

        # Sentence endings for better splitting
        self.sentence_endings = re.compile(r'[.!?]+')
    
    def summarize(
        self, 
        transcript_data: Dict[str, Any], 
        summary_type: str = "detailed",
        max_length: Optional[int] = None
    ) -> str:
        """
        Create different types of summaries from transcript data.
        
        Args:
            transcript_data: Dictionary with 'transcript_segments' and 'full_transcript'
            summary_type: One of 'brief', 'detailed', 'bullet_points', 'key_quotes', 'chapters'
            max_length: Maximum length in words (optional)
        
        Returns:
            Formatted summary string
        """

         segments = transcript_data.get('transcript_segments', [])
        full_text = transcript_data.get('full_transcript', '')
        duration_minutes = transcript_data.get('duration_minutes', 0)
        
        if not segments or not full_text:
            return "No transcript available to summarize."