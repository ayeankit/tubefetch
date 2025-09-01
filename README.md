# YouTube Video Fetcher API

A scalable Flask-based YouTube video fetching API that continuously fetches the latest videos from YouTube Data API v3 in the background. Features paginated REST API endpoints, advanced search capabilities, and a modern web dashboard for video management.

## 🚀 Features

### Core Requirements
- **Continuous Background Fetching**: Automatically fetches latest videos every 10 seconds using threading
- **Multiple Search Queries**: Rotates through predefined high-frequency queries (programming, coding tutorial, tech news, etc.)
- **Paginated REST API**: Clean API endpoints with pagination support (max 100 items per page)
- **Advanced Search**: Partial matching search across video titles and descriptions
- **PostgreSQL Database**: Robust database with proper indexing for performance
- **Docker Support**: Fully containerized with docker-compose setup

### Bonus Features
- **Multiple API Key Support**: Automatic failover when quota is exhausted (supports up to 3 API keys)
- **Web Dashboard**: Modern Bootstrap-based UI for browsing and managing videos
- **Smart Caching**: Prevents unnecessary API calls with intelligent caching system
- **Optimized Search**: Partial word matching (e.g., "tea how" matches "How to make tea?")

### System Architecture
- **Scalable Design**: Thread-based background fetching with proper error handling
- **Database Optimization**: Strategic indexes on frequently queried fields
- **API Quota Management**: Automatic tracking and rotation of API keys
- **RESTful Design**: Clean separation between API routes and dashboard routes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, SQLite is used by default)
- Redis (for caching, optional but recommended)
- YouTube Data API v3 key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ayeankit/tubefetch.git
   cd tubefetch
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Copy the example environment file and update it with your configuration:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` to add your YouTube API key and other settings.

5. **Database Setup**
   - For SQLite (default): No additional setup needed
   - For PostgreSQL: Update `DATABASE_URL` in `.env`
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/youtube_videos
   ```

6. **Initialize the database**
   ```bash
   python -c "from app import app, db; with app.app_context(): db.create_all()"
   ```

### Running the Application

1. **Start the development server**
   ```bash
   python -c "from app import app; app.run(debug=True)"
   ```

2. **Access the application**
   - Web Dashboard: http://localhost:5000
   - API Documentation: http://localhost:5000/api

### Testing

1. **Run unit tests**
   ```bash
   python -m pytest tests/
   ```

2. **Test API Endpoints**
   ```bash
   # Get list of videos
   curl "http://localhost:5000/api/videos?page=1&per_page=5"
   
   # Search videos
   curl "http://localhost:5000/api/search?q=programming"
   
   # Get statistics
   curl http://localhost:5000/api/stats
   ```

### Docker Setup (Alternative)

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Access the application**
   - Web Dashboard: http://localhost:5000
   - API: http://localhost:5000/api

## 🏗️ Project Structure

