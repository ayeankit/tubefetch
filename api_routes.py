from flask import Blueprint, request, jsonify, current_app
from models import Video
from youtube_service import YouTubeService
from extensions import db
from sqlalchemy import or_, desc, text
import logging

api_bp = Blueprint('api', __name__)

youtube_service = YouTubeService()

@api_bp.route('/videos', methods=['GET'])
def get_videos():
    """Get paginated list of videos sorted by publish date (descending)"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)  # Max 100 per page
        query = request.args.get('query', 'programming')  # Default search query
        fetch_new = request.args.get('fetch_new', 'false').lower() == 'true'
        
        # Fetch new videos if requested or if database is empty
        total_videos = Video.query.count()
        if fetch_new or total_videos == 0:
            try:
                result = youtube_service.fetch_videos(query, max_results=50)
                logging.info(f"Fetched videos result: {result}")
            except Exception as e:
                logging.error(f"Error fetching videos from YouTube: {e}")
                # Continue with existing data if fetch fails
        
        # Query videos from database
        videos_query = Video.query.order_by(desc(Video.published_at))
        
        # Paginate results
        pagination = videos_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        videos = [video.to_dict() for video in pagination.items]
        
        return jsonify({
            'videos': videos,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': page + 1 if pagination.has_next else None,
                'prev_page': page - 1 if pagination.has_prev else None
            },
            'query': query
        })
        
    except Exception as e:
        logging.error(f"Error in get_videos: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/videos/search', methods=['GET'])
def search_videos():
    """Search videos by title and description with partial matching"""
    try:
        # Get query parameters
        search_query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        if not search_query:
            return jsonify({'error': 'Search query parameter "q" is required'}), 400
        
        # Split search query into words for partial matching
        search_words = search_query.split()
        
        # Build search conditions for partial matching
        search_conditions = []
        for word in search_words:
            word_pattern = f'%{word}%'
            search_conditions.append(
                or_(
                    Video.title.ilike(word_pattern),
                    Video.description.ilike(word_pattern)
                )
            )
        
        # Combine all conditions with AND (all words must match somewhere)
        if search_conditions:
            combined_condition = search_conditions[0]
            for condition in search_conditions[1:]:
                combined_condition = combined_condition & condition
            
            # Query videos with search conditions
            videos_query = Video.query.filter(combined_condition).order_by(desc(Video.published_at))
        else:
            # If no search conditions, return empty results
            videos_query = Video.query.filter(Video.id == -1).order_by(desc(Video.published_at))
        
        # Paginate results
        pagination = videos_query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        videos = [video.to_dict() for video in pagination.items]
        
        return jsonify({
            'videos': videos,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': page + 1 if pagination.has_next else None,
                'prev_page': page - 1 if pagination.has_prev else None
            },
            'search_query': search_query
        })
        
    except Exception as e:
        logging.error(f"Error in search_videos: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/videos/fetch', methods=['POST'])
def fetch_new_videos():
    """Manually trigger fetching of new videos"""
    try:
        data = request.get_json() or {}
        query = data.get('query', 'programming')
        max_results = min(data.get('max_results', 50), 50)
        
        result = youtube_service.fetch_videos(query, max_results)
        
        return jsonify({
            'message': 'Videos fetched successfully',
            'stored_count': result.get('stored_count', 0),
            'total_fetched': len(result.get('items', [])),
            'query': query
        })
        
    except Exception as e:
        logging.error(f"Error in fetch_new_videos: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get basic statistics about stored videos"""
    try:
        total_videos = Video.query.count()
        
        # Get latest video
        latest_video = Video.query.order_by(desc(Video.published_at)).first()
        latest_published = latest_video.published_at.isoformat() if latest_video else None
        
        # Get oldest video
        oldest_video = Video.query.order_by(Video.published_at).first()
        oldest_published = oldest_video.published_at.isoformat() if oldest_video else None
        
        return jsonify({
            'total_videos': total_videos,
            'latest_published': latest_published,
            'oldest_published': oldest_published
        })
        
    except Exception as e:
        logging.error(f"Error in get_stats: {e}")
        return jsonify({'error': str(e)}), 500
