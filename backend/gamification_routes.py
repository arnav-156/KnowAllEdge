"""
Gamification API Routes
Handles achievements, streaks, leaderboards, challenges, and skill trees
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from gamification_db import GamificationDB

logger = logging.getLogger(__name__)

gamification_bp = Blueprint('gamification', __name__, url_prefix='/api/gamification')
gamification_db = GamificationDB()

def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function

# User Progress Endpoints
@gamification_bp.route('/progress', methods=['GET'])
@require_user_id
def get_progress(user_id):
    """Get user's gamification progress"""
    try:
        progress = gamification_db.get_user_progress(user_id)
        if not progress:
            progress = gamification_db.create_user_progress(user_id)
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/progress/activity', methods=['POST'])
@require_user_id
def update_activity(user_id):
    """Update user activity and streak"""
    try:
        progress = gamification_db.update_user_activity(user_id)
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Error updating activity: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/progress/topic', methods=['POST'])
@require_user_id
def record_topic(user_id):
    """Record topic completion"""
    try:
        data = request.get_json()
        topic_id = data.get('topic_id')
        time_spent = data.get('time_spent', 0)
        
        progress = gamification_db.record_topic_completion(user_id, topic_id, time_spent)
        
        return jsonify({
            'success': True,
            'progress': progress,
            'xp_earned': 50
        })
    except Exception as e:
        logger.error(f"Error recording topic: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/progress/quiz', methods=['POST'])
@require_user_id
def record_quiz(user_id):
    """Record quiz completion"""
    try:
        data = request.get_json()
        quiz_id = data.get('quiz_id')
        score = data.get('score', 0)
        time_taken = data.get('time_taken', 0)
        
        progress = gamification_db.record_quiz_completion(user_id, quiz_id, score, time_taken)
        xp_earned = int(score * 2)
        
        return jsonify({
            'success': True,
            'progress': progress,
            'xp_earned': xp_earned
        })
    except Exception as e:
        logger.error(f"Error recording quiz: {e}")
        return jsonify({'error': str(e)}), 500

# Achievement Endpoints
@gamification_bp.route('/achievements', methods=['GET'])
def get_achievements():
    """Get all achievements"""
    try:
        include_secret = request.args.get('include_secret', 'false').lower() == 'true'
        achievements = gamification_db.get_all_achievements(include_secret)
        
        return jsonify({
            'success': True,
            'achievements': achievements
        })
    except Exception as e:
        logger.error(f"Error getting achievements: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/achievements/user', methods=['GET'])
@require_user_id
def get_user_achievements(user_id):
    """Get user's unlocked achievements"""
    try:
        achievements = gamification_db.get_user_achievements(user_id)
        all_achievements = gamification_db.get_all_achievements(include_secret=False)
        
        return jsonify({
            'success': True,
            'unlocked': achievements,
            'total': all_achievements,
            'unlocked_count': len(achievements),
            'total_count': len(all_achievements)
        })
    except Exception as e:
        logger.error(f"Error getting user achievements: {e}")
        return jsonify({'error': str(e)}), 500

# Skill Tree Endpoints
@gamification_bp.route('/skills', methods=['GET'])
def get_skills():
    """Get complete skill tree"""
    try:
        skills = gamification_db.get_skill_tree()
        return jsonify({
            'success': True,
            'skills': skills
        })
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/skills/user', methods=['GET'])
@require_user_id
def get_user_skills(user_id):
    """Get user's unlocked skills"""
    try:
        unlocked_skills = gamification_db.get_user_skills(user_id)
        all_skills = gamification_db.get_skill_tree()
        
        return jsonify({
            'success': True,
            'unlocked': unlocked_skills,
            'all_skills': all_skills
        })
    except Exception as e:
        logger.error(f"Error getting user skills: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/skills/unlock', methods=['POST'])
@require_user_id
def unlock_skill(user_id):
    """Unlock a skill"""
    try:
        data = request.get_json()
        skill_id = data.get('skill_id')
        
        result = gamification_db.unlock_skill(user_id, skill_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error unlocking skill: {e}")
        return jsonify({'error': str(e)}), 500

# Challenge Endpoints
@gamification_bp.route('/challenges', methods=['GET'])
def get_challenges():
    """Get all active challenges"""
    try:
        challenges = gamification_db.get_active_challenges()
        return jsonify({
            'success': True,
            'challenges': challenges
        })
    except Exception as e:
        logger.error(f"Error getting challenges: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/challenges/user', methods=['GET'])
@require_user_id
def get_user_challenges(user_id):
    """Get user's challenges"""
    try:
        challenges = gamification_db.get_user_challenges(user_id)
        return jsonify({
            'success': True,
            'challenges': challenges
        })
    except Exception as e:
        logger.error(f"Error getting user challenges: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/challenges/start', methods=['POST'])
@require_user_id
def start_challenge(user_id):
    """Start a challenge"""
    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id')
        
        result = gamification_db.start_challenge(user_id, challenge_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error starting challenge: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/challenges/complete', methods=['POST'])
@require_user_id
def complete_challenge(user_id):
    """Complete a challenge"""
    try:
        data = request.get_json()
        challenge_id = data.get('challenge_id')
        score = data.get('score', 100)
        
        result = gamification_db.complete_challenge(user_id, challenge_id, score)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error completing challenge: {e}")
        return jsonify({'error': str(e)}), 500

# Leaderboard Endpoints
@gamification_bp.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    """Get leaderboard"""
    try:
        limit = int(request.args.get('limit', 100))
        leaderboard = gamification_db.get_leaderboard(limit)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard
        })
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'error': str(e)}), 500

@gamification_bp.route('/leaderboard/rank', methods=['GET'])
@require_user_id
def get_rank(user_id):
    """Get user's rank"""
    try:
        rank = gamification_db.get_user_rank(user_id)
        
        if rank:
            return jsonify({
                'success': True,
                'rank': rank
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not on leaderboard'
            }), 404
    except Exception as e:
        logger.error(f"Error getting rank: {e}")
        return jsonify({'error': str(e)}), 500

# Stats Endpoint
@gamification_bp.route('/stats', methods=['GET'])
@require_user_id
def get_stats(user_id):
    """Get comprehensive user stats"""
    try:
        progress = gamification_db.get_user_progress(user_id)
        if not progress:
            progress = gamification_db.create_user_progress(user_id)
        
        achievements = gamification_db.get_user_achievements(user_id)
        skills = gamification_db.get_user_skills(user_id)
        rank = gamification_db.get_user_rank(user_id)
        challenges = gamification_db.get_user_challenges(user_id)
        
        return jsonify({
            'success': True,
            'stats': {
                'progress': progress,
                'achievements': {
                    'unlocked': len(achievements),
                    'recent': achievements[:5]
                },
                'skills': {
                    'unlocked': len(skills),
                    'recent': skills[:5]
                },
                'rank': rank,
                'challenges': {
                    'active': len([c for c in challenges if c['status'] == 'active']),
                    'completed': len([c for c in challenges if c['status'] == 'completed'])
                }
            }
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500
