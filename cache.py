import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TranscriptionCache:
    """Cache system for YouTube transcripts"""

    def __init__(
        self,
        cache_dir: str,
        max_age_hours: int = 24 * 7,  # 1 week default
        max_cache_size_mb: int = 100
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True) 
        self.max_age = timedelta(hours=max_age_hours)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convert to bytes

        # Create metadata file if it doesn't exist
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        if not self.metadata_file.exists():
            self._save_metadata({})

    def _get_cache_key(self, video_id: str) -> str:
        """Generate cache key from video ID"""
        return hashlib.md5(video_id.encode()).hexdigest()

    def _get_cache_path(self, video_id: str) -> Path:
        """Get the cache file path for a video ID"""
        cache_key = self._get_cache_key(video_id)
        return self.cache_dir / f"{cache_key}.json"

    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata"""
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except:
            return {}

    def _save_metadata(self, metadata: Dict[str, Any]):
        """Save cache metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def get(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript from cache if it exists and is valid"""
        cache_path = self._get_cache_path(video_id)
        
        if not cache_path.exists():
            logger.debug(f"Cache miss for video {video_id}")
            return None
        
        # Check age
        metadata = self._load_metadata()
        cache_key = self._get_cache_key(video_id)
        
        if cache_key in metadata:
            cached_time = datetime.fromisoformat(metadata[cache_key]['timestamp'])
            if datetime.now() - cached_time > self.max_age:
                logger.debug(f"Cache expired for video {video_id}")
                self.delete(video_id)
                return None
        
        # Load and return cached data
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Cache hit for video {video_id}")
                return data
        except Exception as e:
            logger.error(f"Error reading cache for {video_id}: {e}")
            self.delete(video_id)
            return None
    
    def set(self, video_id: str, data: Dict[str, Any]):
        """Save transcript to cache"""
        cache_path = self._get_cache_path(video_id)
        cache_key = self._get_cache_key(video_id)
        
        # Save transcript data
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Update metadata
        metadata = self._load_metadata()
        metadata[cache_key] = {
            'video_id': video_id,
            'timestamp': datetime.now().isoformat(),
            'size': cache_path.stat().st_size
        }
        self._save_metadata(metadata)
        
        logger.debug(f"Cached transcript for video {video_id}")
        
        # Clean up if cache is too large
        self._cleanup_if_needed()
    
    def delete(self, video_id: str):
        """Delete a specific video from cache"""
        cache_path = self._get_cache_path(video_id)
        cache_key = self._get_cache_key(video_id)
        
        if cache_path.exists():
            cache_path.unlink()
        
        metadata = self._load_metadata()
        if cache_key in metadata:
            del metadata[cache_key]
            self._save_metadata(metadata)
    
    def clear(self):
        """Clear entire cache"""
        for cache_file in self.cache_dir.glob("*.json"):
            if cache_file != self.metadata_file:
                cache_file.unlink()
        
        self._save_metadata({})
        logger.info("Cache cleared")
    
    def _cleanup_if_needed(self):
        """Remove old entries if cache is too large"""
        metadata = self._load_metadata()
        
        # Calculate total size
        total_size = sum(entry['size'] for entry in metadata.values())
        
        if total_size > self.max_cache_size:
            # Sort by timestamp (oldest first)
            sorted_entries = sorted(
                metadata.items(),
                key=lambda x: x[1]['timestamp']
            )
            
            # Remove oldest entries until under size limit
            while total_size > self.max_cache_size and sorted_entries:
                cache_key, entry = sorted_entries.pop(0)
                video_id = entry['video_id']
                self.delete(video_id)
                total_size -= entry['size']
                logger.debug(f"Removed {video_id} from cache to free space")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        metadata = self._load_metadata()
        
        total_size = sum(entry['size'] for entry in metadata.values())
        
        return {
            'total_videos': len(metadata),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'max_size_mb': self.max_cache_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir),
            'max_age_hours': self.max_age.total_seconds() / 3600
        }