"""
Sprint 11: Result caching for extraction

Caches extraction results keyed on segment content hash.
Re-running the same segments doesn't re-call the LLM.
"""
import hashlib
import json
from typing import Optional
from datetime import datetime, timedelta


class ExtractionCache:
    """
    Simple in-memory cache for extraction results.
    
    In production, this would use Redis or similar.
    For now, using a dict with TTL.
    """
    
    def __init__(self, ttl_hours: int = 24):
        self._cache = {}
        self._ttl = timedelta(hours=ttl_hours)
    
    def _generate_cache_key(self, segments: list) -> str:
        """Generate cache key from segment content"""
        hasher = hashlib.sha256()
        
        # Sort segments by index to ensure consistency
        sorted_segments = sorted(segments, key=lambda s: s.get('index', 0))
        
        for seg in sorted_segments:
            hasher.update(seg['id'].encode('utf-8'))
            hasher.update(seg['text'].encode('utf-8'))
        
        return f"extract_{hasher.hexdigest()[:16]}"
    
    def get(self, segments: list) -> Optional[dict]:
        """Get cached extraction result if available and not expired"""
        cache_key = self._generate_cache_key(segments)
        
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            
            # Check if expired
            if datetime.utcnow() - entry['timestamp'] < self._ttl:
                return entry['result']
            else:
                # Remove expired entry
                del self._cache[cache_key]
        
        return None
    
    def set(self, segments: list, result: dict):
        """Cache an extraction result"""
        cache_key = self._generate_cache_key(segments)
        
        self._cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }
    
    def clear(self):
        """Clear all cached results"""
        self._cache.clear()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired = 0
        
        now = datetime.utcnow()
        for entry in self._cache.values():
            if now - entry['timestamp'] >= self._ttl:
                expired += 1
        
        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired,
            'expired_entries': expired,
            'ttl_hours': self._ttl.total_seconds() / 3600
        }


# Global cache instance
_extraction_cache = ExtractionCache(ttl_hours=24)


def get_extraction_cache() -> ExtractionCache:
    """Get the global extraction cache instance"""
    return _extraction_cache