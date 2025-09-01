import threading
import time
import logging
from datetime import datetime
from youtube_service import YouTubeService
from app import app, db

class BackgroundVideoFetcher:
    def __init__(self, search_queries=None, fetch_interval=10):
        """
        Initialize background video fetcher
        
        Args:
            search_queries (list): List of search queries to fetch videos for
            fetch_interval (int): Interval in seconds between fetches
        """
        self.search_queries = search_queries or ["programming", "technology", "coding", "software development"]
        self.fetch_interval = fetch_interval
        self.youtube_service = YouTubeService()
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the background fetching thread"""
        if self.running:
            logging.warning("Background fetcher is already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self.thread.start()
        logging.info(f"Started background video fetcher with {len(self.search_queries)} queries, interval: {self.fetch_interval}s")
        
    def stop(self):
        """Stop the background fetching thread"""
        self.running = False
        if self.thread:
            self.thread.join()
        logging.info("Stopped background video fetcher")
        
    def _fetch_loop(self):
        """Main fetching loop that runs in background thread"""
        query_index = 0
        
        while self.running:
            try:
                # Use app context for database operations
                with app.app_context():
                    # Rotate through search queries
                    current_query = self.search_queries[query_index % len(self.search_queries)]
                    query_index += 1
                    
                    logging.info(f"Background fetch starting for query: '{current_query}'")
                    
                    # Fetch videos for current query
                    result = self.youtube_service.fetch_videos(
                        query=current_query,
                        max_results=25  # Smaller batch for continuous fetching
                    )
                    
                    if result.get('stored_count', 0) > 0:
                        logging.info(f"Background fetch stored {result['stored_count']} new videos for query: '{current_query}'")
                    else:
                        logging.debug(f"Background fetch: No new videos for query: '{current_query}'")
                        
            except Exception as e:
                error_msg = str(e).lower()
                if "exhausted" in error_msg or "quota" in error_msg:
                    logging.warning(f"All API keys exhausted. Pausing background fetching for 1 hour.")
                    # Sleep for 1 hour when quota is exhausted
                    time.sleep(3600)  # 1 hour = 3600 seconds
                    continue
                else:
                    logging.error(f"Error in background fetch for query '{current_query}': {e}")
                
            # Wait for next fetch interval
            time.sleep(self.fetch_interval)

# Global instance of background fetcher
background_fetcher = None

def start_background_fetching():
    """Start background video fetching"""
    global background_fetcher
    
    if background_fetcher is None:
        # Comprehensive high-frequency search queries across all major categories
        search_queries = [
            # Technology & Programming
            "programming",
            "coding tutorial", 
            "software development",
            "tech news",
            "python programming",
            "javascript tutorial",
            "react js",
            "machine learning",
            "artificial intelligence",
            "web development",
            
            # Sports & Fitness
            "football",
            "cricket",
            "basketball",
            "soccer highlights",
            "tennis",
            "fitness workout",
            "gym training",
            "yoga",
            
            # Entertainment & Gaming
            "music videos",
            "movie trailers",
            "comedy",
            "gaming",
            "funny videos",
            "stand up comedy",
            "video games",
            "entertainment news",
            
            # News & Politics
            "breaking news",
            "world news",
            "politics",
            "economics",
            "current events",
            "news today",
            
            # Lifestyle & Culture
            "cooking",
            "travel",
            "fashion",
            "beauty",
            "food recipes",
            "lifestyle",
            "vlog",
            "tutorial",
            
            # Education & Learning
            "education",
            "science",
            "history",
            "documentary",
            "how to",
            "diy",
            "learning",
            "explainer",
            
            # Music & Arts
            "music",
            "songs",
            "cover songs",
            "live performance",
            "concert",
            "art tutorial",
            "drawing",
            
            # Popular Culture
            "viral videos",
            "trending",
            "memes",
            "tiktok",
            "social media",
            "influencer",
            
            # Health & Wellness
            "health tips",
            "mental health",
            "meditation",
            "wellness",
            "nutrition"
        ]
        
        background_fetcher = BackgroundVideoFetcher(
            search_queries=search_queries,
            fetch_interval=10  # 10 seconds as per requirements
        )
        
    background_fetcher.start()
    
def stop_background_fetching():
    """Stop background video fetching"""
    global background_fetcher
    if background_fetcher:
        background_fetcher.stop()