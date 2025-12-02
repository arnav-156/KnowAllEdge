"""
Social API - Likes, Ratings, and Graph Statistics
Handles community engagement features for concept maps
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Optional
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
social_api = Blueprint('social_api', __name__)

# Simple JSON file-based storage (upgrade to database later)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
SOCIAL_DATA_FILE = os.path.join(DATA_DIR, 'social_data.json')
USER_INTERACTIONS_FILE = os.path.join(DATA_DIR, 'user_interactions.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize data files if they don't exist
if not os.path.exists(SOCIAL_DATA_FILE):
    with open(SOCIAL_DATA_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(USER_INTERACTIONS_FILE):
    with open(USER_INTERACTIONS_FILE, 'w') as f:
        json.dump({}, f)


def get_graph_id(topic: str) -> str:
    """Generate consistent graph ID from topic"""
    return hashlib.sha256(topic.encode()).hexdigest()[:16]


def load_social_data() -> Dict:
    """Load social data from JSON file"""
    try:
        with open(SOCIAL_DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load social data: {e}")
        return {}


def save_social_data(data: Dict) -> bool:
    """Save social data to JSON file"""
    try:
        with open(SOCIAL_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save social data: {e}")
        return False


def load_user_interactions() -> Dict:
    """Load user interactions from JSON file"""
    try:
        with open(USER_INTERACTIONS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load user interactions: {e}")
        return {}


def save_user_interactions(data: Dict) -> bool:
    """Save user interactions to JSON file"""
    try:
        with open(USER_INTERACTIONS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Failed to save user interactions: {e}")
        return False


def get_user_id(request) -> str:
    """
    Get user ID from request
    Uses authenticated user ID if available, otherwise creates anonymous ID from IP
    """
    # Try to get authenticated user ID
    if hasattr(request, 'user') and request.user:
        return f"user_{request.user.get('id', 'anonymous')}"
    
    # Fallback to IP-based anonymous ID
    ip = request.remote_addr or 'unknown'
    return f"anon_{hashlib.sha256(ip.encode()).hexdigest()[:12]}"


# ============================================================================
# API Routes
# ============================================================================

@social_api.route('/graphs/<graph_id>/like', methods=['POST'])
def like_graph(graph_id: str):
    """
    Like or unlike a graph
    POST /api/social/graphs/{graph_id}/like
    Body: { "liked": true }
    """
    try:
        user_id = get_user_id(request)
        data = request.get_json() or {}
        liked = data.get('liked', True)
        
        # Load data
        social_data = load_social_data()
        user_interactions = load_user_interactions()
        
        # Initialize graph data if not exists
        if graph_id not in social_data:
            social_data[graph_id] = {
                'likes': 0,
                'total_ratings': 0,
                'average_rating': 0.0,
                'rating_sum': 0,
                'views': 0,
                'shares': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        
        # Initialize user interaction if not exists
        interaction_key = f"{user_id}_{graph_id}"
        if interaction_key not in user_interactions:
            user_interactions[interaction_key] = {
                'user_id': user_id,
                'graph_id': graph_id,
                'liked': False,
                'rating': None,
                'created_at': datetime.utcnow().isoformat()
            }
        
        # Update like status
        previous_liked = user_interactions[interaction_key].get('liked', False)
        user_interactions[interaction_key]['liked'] = liked
        user_interactions[interaction_key]['updated_at'] = datetime.utcnow().isoformat()
        
        # Update like count
        if liked and not previous_liked:
            social_data[graph_id]['likes'] += 1
        elif not liked and previous_liked:
            social_data[graph_id]['likes'] = max(0, social_data[graph_id]['likes'] - 1)
        
        social_data[graph_id]['updated_at'] = datetime.utcnow().isoformat()
        
        # Save data
        save_social_data(social_data)
        save_user_interactions(user_interactions)
        
        return jsonify({
            'success': True,
            'liked': liked,
            'likes': social_data[graph_id]['likes']
        })
    
    except Exception as e:
        logger.error(f"Error liking graph: {e}")
        return jsonify({'error': str(e)}), 500


@social_api.route('/graphs/<graph_id>/rate', methods=['POST'])
def rate_graph(graph_id: str):
    """
    Rate a graph (1-5 stars)
    POST /api/social/graphs/{graph_id}/rate
    Body: { "rating": 4 }
    """
    try:
        user_id = get_user_id(request)
        data = request.get_json() or {}
        rating = data.get('rating')
        
        # Validate rating
        if rating is not None and (not isinstance(rating, (int, float)) or rating < 1 or rating > 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        # Load data
        social_data = load_social_data()
        user_interactions = load_user_interactions()
        
        # Initialize graph data if not exists
        if graph_id not in social_data:
            social_data[graph_id] = {
                'likes': 0,
                'total_ratings': 0,
                'average_rating': 0.0,
                'rating_sum': 0,
                'views': 0,
                'shares': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        
        # Initialize user interaction if not exists
        interaction_key = f"{user_id}_{graph_id}"
        if interaction_key not in user_interactions:
            user_interactions[interaction_key] = {
                'user_id': user_id,
                'graph_id': graph_id,
                'liked': False,
                'rating': None,
                'created_at': datetime.utcnow().isoformat()
            }
        
        # Get previous rating
        previous_rating = user_interactions[interaction_key].get('rating')
        
        # Update rating
        if rating is None:
            # Remove rating
            if previous_rating is not None:
                social_data[graph_id]['rating_sum'] -= previous_rating
                social_data[graph_id]['total_ratings'] -= 1
                user_interactions[interaction_key]['rating'] = None
        else:
            # Add or update rating
            if previous_rating is None:
                # New rating
                social_data[graph_id]['rating_sum'] = social_data[graph_id].get('rating_sum', 0) + rating
                social_data[graph_id]['total_ratings'] += 1
            else:
                # Update existing rating
                social_data[graph_id]['rating_sum'] = social_data[graph_id].get('rating_sum', 0) - previous_rating + rating
            
            user_interactions[interaction_key]['rating'] = rating
        
        # Calculate new average
        if social_data[graph_id]['total_ratings'] > 0:
            social_data[graph_id]['average_rating'] = round(
                social_data[graph_id]['rating_sum'] / social_data[graph_id]['total_ratings'], 
                2
            )
        else:
            social_data[graph_id]['average_rating'] = 0.0
        
        user_interactions[interaction_key]['updated_at'] = datetime.utcnow().isoformat()
        social_data[graph_id]['updated_at'] = datetime.utcnow().isoformat()
        
        # Save data
        save_social_data(social_data)
        save_user_interactions(user_interactions)
        
        return jsonify({
            'success': True,
            'rating': rating,
            'average_rating': social_data[graph_id]['average_rating'],
            'total_ratings': social_data[graph_id]['total_ratings']
        })
    
    except Exception as e:
        logger.error(f"Error rating graph: {e}")
        return jsonify({'error': str(e)}), 500


@social_api.route('/graphs/<graph_id>/stats', methods=['GET'])
def get_graph_stats(graph_id: str):
    """
    Get statistics for a graph
    GET /api/social/graphs/{graph_id}/stats
    """
    try:
        user_id = get_user_id(request)
        
        # Load data
        social_data = load_social_data()
        user_interactions = load_user_interactions()
        
        # Get graph stats
        stats = social_data.get(graph_id, {
            'likes': 0,
            'total_ratings': 0,
            'average_rating': 0.0,
            'views': 0,
            'shares': 0
        })
        
        # Get user's interaction
        interaction_key = f"{user_id}_{graph_id}"
        user_interaction = user_interactions.get(interaction_key, {
            'liked': False,
            'rating': None
        })
        
        # Increment view count
        if graph_id in social_data:
            social_data[graph_id]['views'] = social_data[graph_id].get('views', 0) + 1
            social_data[graph_id]['updated_at'] = datetime.utcnow().isoformat()
            save_social_data(social_data)
        
        return jsonify({
            'success': True,
            'stats': {
                'likes': stats.get('likes', 0),
                'average_rating': stats.get('average_rating', 0.0),
                'total_ratings': stats.get('total_ratings', 0),
                'views': stats.get('views', 0),
                'shares': stats.get('shares', 0)
            },
            'user_interaction': {
                'liked': user_interaction.get('liked', False),
                'rating': user_interaction.get('rating')
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        return jsonify({'error': str(e)}), 500


@social_api.route('/graphs/<graph_id>/share', methods=['POST'])
def track_share(graph_id: str):
    """
    Track when a graph is shared
    POST /api/social/graphs/{graph_id}/share
    """
    try:
        # Load data
        social_data = load_social_data()
        
        # Initialize if not exists
        if graph_id not in social_data:
            social_data[graph_id] = {
                'likes': 0,
                'total_ratings': 0,
                'average_rating': 0.0,
                'rating_sum': 0,
                'views': 0,
                'shares': 0,
                'created_at': datetime.utcnow().isoformat()
            }
        
        # Increment share count
        social_data[graph_id]['shares'] = social_data[graph_id].get('shares', 0) + 1
        social_data[graph_id]['updated_at'] = datetime.utcnow().isoformat()
        
        # Save data
        save_social_data(social_data)
        
        return jsonify({
            'success': True,
            'shares': social_data[graph_id]['shares']
        })
    
    except Exception as e:
        logger.error(f"Error tracking share: {e}")
        return jsonify({'error': str(e)}), 500


@social_api.route('/graphs/trending', methods=['GET'])
def get_trending_graphs():
    """
    Get trending graphs based on likes, ratings, and recent activity
    GET /api/social/graphs/trending?limit=10
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        # Load data
        social_data = load_social_data()
        
        # Calculate trending score (likes * 2 + average_rating * total_ratings)
        trending = []
        for graph_id, stats in social_data.items():
            score = (
                stats.get('likes', 0) * 2 + 
                stats.get('average_rating', 0) * stats.get('total_ratings', 0)
            )
            trending.append({
                'graph_id': graph_id,
                'score': score,
                'likes': stats.get('likes', 0),
                'average_rating': stats.get('average_rating', 0.0),
                'total_ratings': stats.get('total_ratings', 0),
                'views': stats.get('views', 0),
                'shares': stats.get('shares', 0)
            })
        
        # Sort by score and limit
        trending.sort(key=lambda x: x['score'], reverse=True)
        trending = trending[:limit]
        
        return jsonify({
            'success': True,
            'trending': trending
        })
    
    except Exception as e:
        logger.error(f"Error getting trending graphs: {e}")
        return jsonify({'error': str(e)}), 500


@social_api.route('/graphs/top-rated', methods=['GET'])
def get_top_rated_graphs():
    """
    Get top-rated graphs
    GET /api/social/graphs/top-rated?limit=10&min_ratings=5
    """
    try:
        limit = int(request.args.get('limit', 10))
        min_ratings = int(request.args.get('min_ratings', 5))
        
        # Load data
        social_data = load_social_data()
        
        # Filter and sort by average rating
        top_rated = []
        for graph_id, stats in social_data.items():
            if stats.get('total_ratings', 0) >= min_ratings:
                top_rated.append({
                    'graph_id': graph_id,
                    'average_rating': stats.get('average_rating', 0.0),
                    'total_ratings': stats.get('total_ratings', 0),
                    'likes': stats.get('likes', 0),
                    'views': stats.get('views', 0)
                })
        
        # Sort by average rating
        top_rated.sort(key=lambda x: x['average_rating'], reverse=True)
        top_rated = top_rated[:limit]
        
        return jsonify({
            'success': True,
            'top_rated': top_rated
        })
    
    except Exception as e:
        logger.error(f"Error getting top-rated graphs: {e}")
        return jsonify({'error': str(e)}), 500


# Helper route to get graph ID from topic (for frontend)
@social_api.route('/graphs/id', methods=['POST'])
def get_graph_id_from_topic():
    """
    Get graph ID from topic
    POST /api/social/graphs/id
    Body: { "topic": "Machine Learning" }
    """
    try:
        data = request.get_json() or {}
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        graph_id = get_graph_id(topic)
        
        return jsonify({
            'success': True,
            'graph_id': graph_id,
            'topic': topic
        })
    
    except Exception as e:
        logger.error(f"Error getting graph ID: {e}")
        return jsonify({'error': str(e)}), 500
