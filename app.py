import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL", "sqlite:///youtube_videos.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    from models import Video, APIKeyUsage, SearchCache  # noqa: F401
    
    # Create all tables
    db.create_all()
    
    # Create indexes for better performance
    from sqlalchemy import text, inspect
    
    try:
        # Only create indexes if they don't exist
        inspector = inspect(db.engine)
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('video')]
        
        if 'idx_video_published_at' not in existing_indexes:
            db.session.execute(text("CREATE INDEX idx_video_published_at ON video(published_at DESC)"))
        if 'idx_video_title' not in existing_indexes:
            db.session.execute(text("CREATE INDEX idx_video_title ON video(title)"))
        if 'idx_video_description' not in existing_indexes:
            db.session.execute(text("CREATE INDEX idx_video_description ON video(description)"))
        if 'idx_video_video_id' not in existing_indexes:
            db.session.execute(text("CREATE INDEX idx_video_video_id ON video(video_id)"))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.warning(f"Index creation failed (may already exist): {e}")

# Register blueprints
from api_routes import api_bp
from dashboard_routes import dashboard_bp

app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(dashboard_bp)

# Start background video fetching
from background_fetcher import start_background_fetching
start_background_fetching()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
