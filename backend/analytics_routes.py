"""
Analytics endpoint for receiving frontend metrics
Now with SQLite persistence for production-ready analytics
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import json
import os
import logging

# Import analytics database
try:
    from analytics_db import analytics_db
    ANALYTICS_DB_AVAILABLE = True
except ImportError:
    ANALYTICS_DB_AVAILABLE = False
    logging.warning("Analytics database not available, using in-memory storage")

analytics_bp = Blueprint('analytics', __name__)
logger = logging.getLogger(__name__)

# Fallback: Store metrics in memory if database not available
frontend_metrics = []
METRICS_FILE = 'frontend_metrics.jsonl'
MAX_JSONL_SIZE_MB = 50  # Rotate log when it exceeds 50MB

def rotate_jsonl_if_needed():
    """Rotate JSONL file if it exceeds size limit"""
    try:
        if os.path.exists(METRICS_FILE):
            file_size_mb = os.path.getsize(METRICS_FILE) / (1024 * 1024)
            if file_size_mb > MAX_JSONL_SIZE_MB:
                # Rename old file with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                archive_name = f'frontend_metrics_{timestamp}.jsonl'
                os.rename(METRICS_FILE, archive_name)
                logger.info(f"Rotated JSONL file to {archive_name}")
    except Exception as e:
        logger.error(f"Failed to rotate JSONL file: {e}")

@analytics_bp.route('/api/analytics', methods=['POST'])
def receive_analytics():
    """Receive and store frontend analytics in database"""
    try:
        data = request.get_json()
        
        event_type = data.get('eventType')
        event_data = data.get('data', {})
        session_id = event_data.get('sessionId', 'unknown')
        
        # Store in database if available
        if ANALYTICS_DB_AVAILABLE:
            analytics_db.insert_event(
                session_id=session_id,
                event_type=event_type,
                event_data=event_data,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
        else:
            # Fallback: in-memory storage
            metric = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'data': event_data,
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
            
            frontend_metrics.append(metric)
            
            # Keep only last 10000 metrics
            if len(frontend_metrics) > 10000:
                frontend_metrics.pop(0)
            
            # Rotate JSONL file if too large
            rotate_jsonl_if_needed()
            
            # Append to file for persistence
            with open(METRICS_FILE, 'a') as f:
                f.write(json.dumps(metric) + '\n')
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/summary', methods=['GET'])
def get_analytics_summary():
    """Get summary of frontend analytics"""
    try:
        if ANALYTICS_DB_AVAILABLE:
            # Use database statistics
            days = int(request.args.get('days', 7))
            funnel = analytics_db.get_funnel_stats(days=days)
            performance = analytics_db.get_performance_stats(days=days)
            
            return jsonify({
                'funnel': funnel,
                'performance': performance,
                'database_size_mb': round(analytics_db.get_database_size() / (1024 * 1024), 2)
            }), 200
        else:
            # Fallback: in-memory statistics
            page_loads = [m for m in frontend_metrics if m['event_type'] == 'page_load']
            interactions = [m for m in frontend_metrics if m['event_type'] == 'interaction']
            errors = [m for m in frontend_metrics if m['event_type'] == 'error']
            api_calls = [m for m in frontend_metrics if m['event_type'] == 'api_call']
            
            avg_load_time = sum(m['data'].get('loadTime', 0) for m in page_loads) / len(page_loads) if page_loads else 0
            avg_interaction_time = sum(m['data'].get('timeToInteraction', 0) for m in interactions) / len(interactions) if interactions else 0
            
            total_events = len(frontend_metrics)
            error_rate = (len(errors) / total_events * 100) if total_events > 0 else 0
            
            successful_api = [m for m in api_calls if m['data'].get('success', False)]
            api_success_rate = (len(successful_api) / len(api_calls) * 100) if api_calls else 0
            
            return jsonify({
                'total_events': total_events,
                'page_loads': len(page_loads),
                'avg_load_time_ms': round(avg_load_time, 2),
                'interactions': len(interactions),
                'avg_time_to_interaction_ms': round(avg_interaction_time, 2),
                'errors': len(errors),
                'error_rate_percent': round(error_rate, 2),
                'api_calls': len(api_calls),
                'api_success_rate_percent': round(api_success_rate, 2)
            }), 200
    
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/errors', methods=['GET'])
def get_error_logs():
    """Get recent error logs"""
    try:
        if ANALYTICS_DB_AVAILABLE:
            days = int(request.args.get('days', 7))
            errors = analytics_db.get_error_summary(days=days)
            
            return jsonify({
                'total_errors': sum(e['count'] for e in errors),
                'unique_errors': len(errors),
                'error_summary': errors
            }), 200
        else:
            # Fallback: in-memory errors
            errors = [m for m in frontend_metrics if m['event_type'] == 'error']
            recent_errors = sorted(errors, key=lambda x: x['timestamp'], reverse=True)[:50]
            
            return jsonify({
                'total_errors': len(errors),
                'recent_errors': recent_errors
            }), 200
    
    except Exception as e:
        logger.error(f"Failed to get error logs: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/funnel', methods=['GET'])
def get_funnel():
    """Get funnel conversion rates"""
    try:
        if ANALYTICS_DB_AVAILABLE:
            days = int(request.args.get('days', 7))
            stats = analytics_db.get_funnel_stats(days=days)
            return jsonify(stats), 200
        else:
            return jsonify({'error': 'Analytics database not available'}), 503
    except Exception as e:
        logger.error(f"Failed to get funnel stats: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/performance', methods=['GET'])
def get_performance():
    """Get performance metrics"""
    try:
        if ANALYTICS_DB_AVAILABLE:
            days = int(request.args.get('days', 7))
            stats = analytics_db.get_performance_stats(days=days)
            return jsonify(stats), 200
        else:
            return jsonify({'error': 'Analytics database not available'}), 503
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/cleanup', methods=['POST'])
def cleanup_old_data():
    """Cleanup analytics data older than specified days (admin only)"""
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        days = int(request.args.get('days', 30))
        result = analytics_db.cleanup_old_data(days=days)
        
        return jsonify({
            'success': True,
            'message': f'Deleted analytics data older than {days} days',
            'deleted': result
        }), 200
    except Exception as e:
        logger.error(f"Failed to cleanup data: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/cohorts', methods=['GET'])
def get_cohort_analysis():
    """
    Get cohort analysis - track user retention over time
    Groups users by week/month of first visit and tracks return rates
    """
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        period = request.args.get('period', 'week')  # 'week' or 'month'
        stats = analytics_db.get_cohort_analysis(period=period)
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get cohort analysis: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/segments', methods=['GET'])
def get_user_segments():
    """
    Get user segmentation by device, browser, location
    Useful for understanding different user groups
    """
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        days = int(request.args.get('days', 7))
        stats = analytics_db.get_user_segments(days=days)
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get user segments: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/realtime', methods=['GET'])
def get_realtime_stats():
    """
    Get real-time analytics (last 5 minutes)
    Shows active users, current events, recent errors
    """
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        stats = analytics_db.get_realtime_stats()
        
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Failed to get realtime stats: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/export', methods=['GET'])
def export_analytics():
    """
    Export analytics data for external analysis
    Supports CSV, JSON formats
    """
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        format_type = request.args.get('format', 'json')  # 'json' or 'csv'
        days = int(request.args.get('days', 7))
        event_type = request.args.get('event_type')  # optional filter
        
        data = analytics_db.export_data(days=days, event_type=event_type, format_type=format_type)
        
        if format_type == 'csv':
            return data, 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=analytics.csv'}
        else:
            return jsonify(data), 200
    except Exception as e:
        logger.error(f"Failed to export analytics: {e}")
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/api/analytics/user-journey', methods=['GET'])
def get_user_journey():
    """
    Get user journey for a specific user (tracks across sessions)
    Shows all events for a user in chronological order
    """
    try:
        if not ANALYTICS_DB_AVAILABLE:
            return jsonify({'error': 'Analytics database not available'}), 503
        
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'user_id parameter required'}), 400
        
        journey = analytics_db.get_user_journey(user_id)
        return jsonify(journey), 200
    except Exception as e:
        logger.error(f"Failed to get user journey: {e}")
        return jsonify({'error': str(e)}), 500

