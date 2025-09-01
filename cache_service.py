"""
Redis cache service for YouTube video data
"""
import redis
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class CacheService:
    """Redis-based caching service for YouTube data"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
        except redis.ConnectionError:
            logger.error("Failed to connect to Redis server")
            self.redis_client = None
    
    def _get_cache_key(self, prefix: str, query: str, **kwargs) -> str:
        """Generate consistent cache key"""
        key_data = f"{query}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        hash_key = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_key}"
    
    def cache_search_results(self, query: str, results: Dict[str, Any], expiry_hours: int = 2):
        """Cache YouTube search results"""
        if not self.redis_client:
            return
            
        try:
            cache_key = self._get_cache_key("search", query)
            cache_data = {
                'query': query,
                'results': results,
                'cached_at': datetime.utcnow().isoformat(),
                'total_results': results.get('pageInfo', {}).get('totalResults', 0)
            }
            
            self.redis_client.setex(
                cache_key,
                timedelta(hours=expiry_hours),
                json.dumps(cache_data, default=str)
            )
            logger.debug(f"Cached search results for query: {query}")
            
        except Exception as e:
            logger.error(f"Error caching search results: {e}")
    
    def get_cached_search_results(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached search results"""
        if not self.redis_client:
            return None
            
        try:
            cache_key = self._get_cache_key("search", query)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(str(cached_data))
                cached_at = datetime.fromisoformat(data['cached_at'])
                
                # Check if cache is still fresh (within last 2 hours for active queries)
                if datetime.utcnow() - cached_at < timedelta(hours=2):
                    logger.debug(f"Retrieved cached search results for query: {query}")
                    return data['results']
                    
        except Exception as e:
            logger.error(f"Error retrieving cached search results: {e}")
            
        return None
    
    def cache_video_details(self, video_ids: List[str], details: Dict[str, Any], expiry_hours: int = 24):
        """Cache video detail information"""
        if not self.redis_client or not video_ids:
            return
            
        try:
            cache_key = self._get_cache_key("videos", ",".join(sorted(video_ids)))
            cache_data = {
                'video_ids': video_ids,
                'details': details,
                'cached_at': datetime.utcnow().isoformat()
            }
            
            self.redis_client.setex(
                cache_key,
                timedelta(hours=expiry_hours),
                json.dumps(cache_data, default=str)
            )
            logger.debug(f"Cached details for {len(video_ids)} videos")
            
        except Exception as e:
            logger.error(f"Error caching video details: {e}")
    
    def get_cached_video_details(self, video_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Get cached video details"""
        if not self.redis_client or not video_ids:
            return None
            
        try:
            cache_key = self._get_cache_key("videos", ",".join(sorted(video_ids)))
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(str(cached_data))
                cached_at = datetime.fromisoformat(data['cached_at'])
                
                # Video details can be cached longer (24 hours)
                if datetime.utcnow() - cached_at < timedelta(hours=24):
                    logger.debug(f"Retrieved cached details for {len(video_ids)} videos")
                    return data['details']
                    
        except Exception as e:
            logger.error(f"Error retrieving cached video details: {e}")
            
        return None
    
    def should_skip_query(self, query: str, hours_threshold: int = 6) -> bool:
        """Check if query was recently processed and returned few results"""
        if not self.redis_client:
            return False
            
        try:
            skip_key = f"skip:{query}"
            skip_data = self.redis_client.get(skip_key)
            
            if skip_data:
                data = json.loads(str(skip_data))
                last_attempt = datetime.fromisoformat(data['last_attempt'])
                
                # Skip if recent attempt had no new videos
                if (datetime.utcnow() - last_attempt < timedelta(hours=hours_threshold) 
                    and data['new_videos'] == 0):
                    logger.debug(f"Skipping query '{query}' - no new videos in last {hours_threshold} hours")
                    return True
                    
        except Exception as e:
            logger.error(f"Error checking skip status: {e}")
            
        return False
    
    def mark_query_processed(self, query: str, new_videos_count: int):
        """Mark query as processed with result count"""
        if not self.redis_client:
            return
            
        try:
            skip_key = f"skip:{query}"
            skip_data = {
                'query': query,
                'last_attempt': datetime.utcnow().isoformat(),
                'new_videos': new_videos_count
            }
            
            # Cache for 6 hours
            self.redis_client.setex(
                skip_key,
                timedelta(hours=6),
                json.dumps(skip_data, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error marking query processed: {e}")
    
    def get_quota_usage(self, api_key_index: int) -> Dict[str, Any]:
        """Get quota usage for specific API key"""
        if not self.redis_client:
            return {'calls_today': 0, 'quota_exhausted': False}
            
        try:
            quota_key = f"quota:{api_key_index}:{datetime.utcnow().date()}"
            quota_data = self.redis_client.get(quota_key)
            
            if quota_data:
                return json.loads(str(quota_data))
                
        except Exception as e:
            logger.error(f"Error getting quota usage: {e}")
            
        return {'calls_today': 0, 'quota_exhausted': False}
    
    def update_quota_usage(self, api_key_index: int, calls_made: int = 1, quota_exhausted: bool = False):
        """Update quota usage for API key"""
        if not self.redis_client:
            return
            
        try:
            quota_key = f"quota:{api_key_index}:{datetime.utcnow().date()}"
            current_usage = self.get_quota_usage(api_key_index)
            
            new_usage = {
                'calls_today': current_usage['calls_today'] + calls_made,
                'quota_exhausted': quota_exhausted,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Cache until end of day
            seconds_until_midnight = int((datetime.utcnow().replace(hour=23, minute=59, second=59) - datetime.utcnow()).total_seconds())
            self.redis_client.setex(quota_key, seconds_until_midnight, json.dumps(new_usage, default=str))
            
        except Exception as e:
            logger.error(f"Error updating quota usage: {e}")
    
    def clear_cache(self, pattern: str = None):
        """Clear cache entries matching pattern"""
        if not self.redis_client:
            return
            
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
            else:
                self.redis_client.flushdb()
                logger.info("Cleared all cache entries")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# Global cache service instance
cache_service = CacheService()