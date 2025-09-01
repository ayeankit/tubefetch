import os
import logging
import hashlib
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from models import Video, APIKeyUsage, SearchCache
from app import db
from cache_service import cache_service

class YouTubeService:
    def __init__(self):
        # Get API keys from environment variables
        self.api_keys = []
        
        # Support multiple API keys
        api_key_1 = os.getenv("YOUTUBE_API_KEY", "")
        api_key_2 = os.getenv("YOUTUBE_API_KEY_2", "")
        api_key_3 = os.getenv("YOUTUBE_API_KEY_3", "")
        
        if api_key_1:
            self.api_keys.append(api_key_1)
        if api_key_2:
            self.api_keys.append(api_key_2)
        if api_key_3:
            self.api_keys.append(api_key_3)
            
        if not self.api_keys:
            logging.warning("No YouTube API keys found in environment variables")
            
        self.current_key_index = 0
        self.youtube = None
        self._initialize_youtube_client()
        
    def _initialize_youtube_client(self):
        """Initialize YouTube client with current API key"""
        if self.api_keys and self.current_key_index < len(self.api_keys):
            try:
                api_key = self.api_keys[self.current_key_index]
                self.youtube = build('youtube', 'v3', developerKey=api_key)
                logging.info(f"Initialized YouTube client with API key index {self.current_key_index}")
            except Exception as e:
                logging.error(f"Failed to initialize YouTube client: {e}")
                
    def _switch_api_key(self):
        """Switch to next available API key"""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            self._initialize_youtube_client()
            return True
        return False
        
    def _track_api_usage(self, quota_cost=1):
        """Track API usage for current key"""
        if not self.api_keys or self.current_key_index >= len(self.api_keys):
            return
            
        api_key = self.api_keys[self.current_key_index]
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        usage = APIKeyUsage.query.filter_by(api_key_hash=api_key_hash).first()
        if not usage:
            usage = APIKeyUsage()
            usage.api_key_hash = api_key_hash
            db.session.add(usage)
            
        # Reset quota if it's a new day
        if usage.last_reset is None or usage.last_reset.date() < datetime.now().date():
            usage.quota_used = 0
            usage.is_exhausted = False
            usage.last_reset = datetime.now()
            
        usage.quota_used += quota_cost
        
        # Mark as exhausted if quota exceeds limit (YouTube API has 10,000 units per day)
        if usage.quota_used >= 9500:  # Leave some buffer
            usage.is_exhausted = True
            
        db.session.commit()
        
    def _should_fetch_new_videos(self, query, cache_duration_minutes=10):
        """Check if we should fetch new videos based on cache"""
        from app import db
        cache = db.session.query(SearchCache).filter(SearchCache.query == query).first()
        if not cache:
            return True
            
        time_since_last_fetch = datetime.utcnow() - cache.last_fetched
        return time_since_last_fetch > timedelta(minutes=cache_duration_minutes)
        
    def fetch_videos(self, query="programming", max_results=50, page_token=None):
        """Fetch videos from YouTube API with Redis caching and fallback API key support"""
        if not self.youtube:
            raise Exception("YouTube API client not initialized")
            
        try:
            # Check Redis cache first for recent search results
            if not page_token:
                # Check if query should be skipped due to no recent activity
                if cache_service.should_skip_query(query):
                    return {"items": [], "nextPageToken": None, "cached": True, "skipped": True}
                
                # Try to get cached search results
                cached_results = cache_service.get_cached_search_results(query)
                if cached_results:
                    logging.info(f"Using Redis cached search results for query: {query}")
                    return {"items": cached_results.get('items', []), "nextPageToken": None, "cached": True}
            
            # Check quota before making API call
            quota_info = cache_service.get_quota_usage(self.current_key_index)
            if quota_info.get('quota_exhausted', False):
                logging.warning(f"API key {self.current_key_index} quota already marked as exhausted in cache")
                if not self._switch_api_key():
                    raise Exception("All API keys exhausted")
            
            # Calculate publishedAfter timestamp (last 7 days to get recent videos)
            published_after = (datetime.utcnow() - timedelta(days=7)).isoformat() + 'Z'
            
            # Search for videos
            search_response = self.youtube.search().list(
                q=query,
                part='id,snippet',
                type='video',
                order='date',
                publishedAfter=published_after,
                maxResults=min(max_results, 50),  # YouTube API limit
                pageToken=page_token
            ).execute()
            
            self._track_api_usage(100)  # Search costs 100 units
            
            videos = []
            video_ids = []
            
            for search_result in search_response.get('items', []):
                video_id = search_result['id']['videoId']
                video_ids.append(video_id)
                
                snippet = search_result['snippet']
                
                # Extract thumbnail URLs
                thumbnails = snippet.get('thumbnails', {})
                thumbnail_default = thumbnails.get('default', {}).get('url', '')
                thumbnail_medium = thumbnails.get('medium', {}).get('url', '')
                thumbnail_high = thumbnails.get('high', {}).get('url', '')
                
                video_data = {
                    'video_id': video_id,
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'published_at': datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                    'thumbnail_default': thumbnail_default,
                    'thumbnail_medium': thumbnail_medium,
                    'thumbnail_high': thumbnail_high,
                    'channel_id': snippet.get('channelId', ''),
                    'channel_title': snippet.get('channelTitle', '')
                }
                
                videos.append(video_data)
            
            # Get additional video details (duration, view count)
            if video_ids:
                video_details = self.youtube.videos().list(
                    part='contentDetails,statistics',
                    id=','.join(video_ids)
                ).execute()
                
                self._track_api_usage(1)  # Videos.list costs 1 unit per video
                
                # Map details back to videos
                details_map = {}
                for video_detail in video_details.get('items', []):
                    video_id = video_detail['id']
                    details_map[video_id] = {
                        'duration': video_detail.get('contentDetails', {}).get('duration', ''),
                        'view_count': int(video_detail.get('statistics', {}).get('viewCount', 0))
                    }
                
                # Update videos with additional details
                for video in videos:
                    if video['video_id'] in details_map:
                        video.update(details_map[video['video_id']])
            
            # Store videos in database
            stored_count = 0
            for video_data in videos:
                existing_video = Video.query.filter_by(video_id=video_data['video_id']).first()
                if not existing_video:
                    video = Video(**video_data)
                    db.session.add(video)
                    stored_count += 1
                else:
                    # Update existing video with new information
                    for key, value in video_data.items():
                        if key != 'video_id':  # Don't update the ID
                            setattr(existing_video, key, value)
            
            db.session.commit()
            
            # Update search cache
            cache = db.session.query(SearchCache).filter(SearchCache.query == query).first()
            if not cache:
                cache = SearchCache()
                setattr(cache, 'query', query)
                db.session.add(cache)
                
            cache.last_fetched = datetime.utcnow()
            cache.total_results = len(videos)
            cache.next_page_token = search_response.get('nextPageToken')
            db.session.commit()
            
            logging.info(f"Fetched {len(videos)} videos, stored {stored_count} new videos for query: {query}")
            
            return {
                'items': videos,
                'nextPageToken': search_response.get('nextPageToken'),
                'totalResults': search_response.get('pageInfo', {}).get('totalResults', 0),
                'stored_count': stored_count
            }
            
        except HttpError as e:
            error_details = e.resp.get('content', b'').decode('utf-8')
            logging.error(f"YouTube API error: {e.resp.status} - {error_details}")
            
            # Check if quota exhausted
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                logging.warning(f"Quota exhausted for API key {self.current_key_index}")
                if self._switch_api_key():
                    logging.info("Switched to next API key, retrying...")
                    return self.fetch_videos(query, max_results, page_token)
                else:
                    raise Exception("All API keys exhausted")
            
            raise Exception(f"YouTube API error: {e}")
        
        except Exception as e:
            logging.error(f"Error fetching videos: {e}")
            raise
