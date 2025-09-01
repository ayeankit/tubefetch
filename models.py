from datetime import datetime
from sqlalchemy import Index
from extensions import db

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    published_at = db.Column(db.DateTime, nullable=False, index=True)
    thumbnail_default = db.Column(db.String(500))
    thumbnail_medium = db.Column(db.String(500))
    thumbnail_high = db.Column(db.String(500))
    channel_id = db.Column(db.String(100))
    channel_title = db.Column(db.String(200))
    duration = db.Column(db.String(50))
    view_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'title': self.title,
            'description': self.description,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'thumbnails': {
                'default': self.thumbnail_default,
                'medium': self.thumbnail_medium,
                'high': self.thumbnail_high
            },
            'channel_id': self.channel_id,
            'channel_title': self.channel_title,
            'duration': self.duration,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class APIKeyUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key_hash = db.Column(db.String(64), nullable=False)
    quota_used = db.Column(db.Integer, default=0)
    last_reset = db.Column(db.DateTime, default=datetime.utcnow)
    is_exhausted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SearchCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(200), nullable=False, index=True)
    last_fetched = db.Column(db.DateTime, default=datetime.utcnow)
    total_results = db.Column(db.Integer, default=0)
    next_page_token = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
