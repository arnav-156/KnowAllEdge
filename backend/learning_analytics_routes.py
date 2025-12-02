"""
Learning Analytics API Routes
Handles analytics dashboard, patterns, gaps, and predictions
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from learning_analytics_db import LearningAnalyticsDB

logger = logging.getLogger(__name__)

learning_analytics_bp = Blueprint('learning_analytics', __name__, url_prefix='/api/analytics')
analytics_db = LearningAnalyticsDB()

def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function

# ==================== DASHBOARD ENDPOINTS ====================

@learning_analytics_bp.route('/dashboard', methods=['GET'])
@require_user_id
def get_dashboard(user_id):
    """Get comprehensive analytics dashboard"""
    try:
        days = int(request.args.get('days', 30))
        analytics = analytics_db.get_dashboard_analytics(user_id, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== SESSION ENDPOINTS ====================

@learning_analytics_bp.route('/sessions/start', methods=['POST'])
@require_user_id
def start_session(user_id):
    """Start a learning session"""
    try:
        data = request.get_json()
        
        if not data.get('topic_id'):
            return jsonify({'error': 'topic_id is required'}), 400
        
        session_id = analytics_db.start_session(
            user_id, 
            data['topic_id'],
            data.get('subtopic_id')
        )
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        return jsonify({'error': str(e)}), 500

@learning_analytics_bp.route('/sessions/<session_id>/end', methods=['POST'])
def end_session(session_id):
    """End a learning session"""
    try:
        data = request.get_json() or {}
        
        result = analytics_db.end_session(
            session_id,
            data.get('concepts_covered'),
            data.get('activities'),
            data.get('focus_score')
        )
        
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        return jsonify({'error': str(e)}), 500

@learning_analytics_bp.route('/sessions', methods=['GET'])
@require_user_id
def get_sessions(user_id):
    """Get user's learning sessions"""
    try:
        days = int(request.args.get('days', 30))
        sessions = analytics_db.get_user_sessions(user_id, days)
        
        return jsonify({
            'success': True,
            'sessions': sessions,
            'count': len(sessions)
        })
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== PERFORMANCE ENDPOINTS ====================

@learning_analytics_bp.route('/performance', methods=['POST'])
@require_user_id
def record_performance(user_id):
    """Record a performance assessment"""
    try:
        data = request.get_json()
        
        required_fields = ['topic_id', 'score', 'max_score']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = analytics_db.record_performance(user_id, data)
        
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        logger.error(f"Error recording performance: {e}")
        return jsonify({'error': str(e)}), 500

@learning_analytics_bp.route('/performance/history', methods=['GET'])
@require_user_id
def get_performance_history(user_id):
    """Get performance history"""
    try:
        topic_id = request.args.get('topic_id')
        days = int(request.args.get('days', 90))
        
        history = analytics_db.get_performance_history(user_id, topic_id, days)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
    except Exception as e:
        logger.error(f"Error getting performance history: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CONCEPT MASTERY ENDPOINTS ====================

@learning_analytics_bp.route('/concepts/mastery', methods=['GET'])
@require_user_id
def get_concept_mastery(user_id):
    """Get concept mastery levels"""
    try:
        topic_id = request.args.get('topic_id')
        concepts = analytics_db.get_concept_mastery(user_id, topic_id)
        
        return jsonify({
            'success': True,
            'concepts': concepts,
            'count': len(concepts)
        })
    except Exception as e:
        logger.error(f"Error getting concept mastery: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== STUDY PATTERNS ENDPOINTS ====================

@learning_analytics_bp.route('/patterns', methods=['GET'])
@require_user_id
def get_study_patterns(user_id):
    """Get study patterns and optimal study times"""
    try:
        patterns = analytics_db.get_study_patterns(user_id)
        
        return jsonify({
            'success': True,
            **patterns
        })
    except Exception as e:
        logger.error(f"Error getting study patterns: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== KNOWLEDGE GAPS ENDPOINTS ====================

@learning_analytics_bp.route('/gaps', methods=['GET'])
@require_user_id
def get_knowledge_gaps(user_id):
    """Get identified knowledge gaps"""
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        gaps = analytics_db.get_knowledge_gaps(user_id, resolved)
        
        return jsonify({
            'success': True,
            'gaps': gaps,
            'count': len(gaps)
        })
    except Exception as e:
        logger.error(f"Error getting knowledge gaps: {e}")
        return jsonify({'error': str(e)}), 500

@learning_analytics_bp.route('/gaps/<gap_id>/resolve', methods=['POST'])
def resolve_gap(gap_id):
    """Mark a knowledge gap as resolved"""
    try:
        resolved = analytics_db.resolve_gap(gap_id)
        
        if resolved:
            return jsonify({
                'success': True,
                'message': 'Gap resolved'
            })
        else:
            return jsonify({'error': 'Gap not found'}), 404
    except Exception as e:
        logger.error(f"Error resolving gap: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== PREDICTIVE INSIGHTS ENDPOINTS ====================

@learning_analytics_bp.route('/predict/readiness', methods=['GET'])
@require_user_id
def predict_readiness(user_id):
    """Get predictive insights for exam readiness"""
    try:
        topic_id = request.args.get('topic_id')
        insights = analytics_db.generate_predictive_insights(user_id, topic_id)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== SUMMARY ENDPOINTS ====================

@learning_analytics_bp.route('/summary', methods=['GET'])
@require_user_id
def get_summary(user_id):
    """Get quick summary of key metrics"""
    try:
        days = int(request.args.get('days', 7))
        
        # Get dashboard analytics
        analytics = analytics_db.get_dashboard_analytics(user_id, days)
        
        # Get predictive insights
        insights = analytics_db.generate_predictive_insights(user_id)
        
        # Get knowledge gaps
        gaps = analytics_db.get_knowledge_gaps(user_id, resolved=False)
        
        summary = {
            'study_time_hours': analytics['time_invested']['total_hours'],
            'sessions_completed': analytics['time_invested']['total_sessions'],
            'concepts_mastered': analytics['concepts']['mastered'],
            'average_score': analytics['performance']['average_score'],
            'performance_trend': analytics['performance']['trend_direction'],
            'exam_readiness': insights['readiness'],
            'readiness_score': insights['prediction_score'],
            'active_gaps': len(gaps),
            'best_study_time': analytics['study_patterns'].get('best_hour'),
            'best_study_day': analytics['study_patterns'].get('best_day')
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        logger.error(f"Error getting summary: {e}")
        return jsonify({'error': str(e)}), 500
