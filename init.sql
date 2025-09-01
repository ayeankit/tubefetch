-- Initialize YouTube Videos Database

-- Create database if it doesn't exist
-- (This file is for docker-compose initialization)

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (these will be created by SQLAlchemy as well)
-- This file serves as documentation of the expected database structure

-- Note: Actual table creation is handled by SQLAlchemy models
-- The indexes are created in app.py for compatibility

-- Example queries for monitoring:
-- SELECT COUNT(*) FROM video;
-- SELECT MAX(published_at) as latest_video FROM video;
-- SELECT query, COUNT(*) as fetch_count FROM searchcache GROUP BY query;