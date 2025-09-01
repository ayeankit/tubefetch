from flask import Blueprint, render_template, request, jsonify, current_app
from models import Video
from youtube_service import YouTubeService
from extensions import db
from sqlalchemy import or_, desc, text
import logging

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@dashboard_bp.route('/dashboard')
def dashboard_redirect():
    """Redirect to main dashboard"""
    return render_template('dashboard.html')
