"""
Integration Ecosystem API Routes
Handles LMS, Google Classroom, Calendar, API keys, and Webhooks
"""
from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from integration_hub import IntegrationHub

logger = logging.getLogger(__name__)

integration_bp = Blueprint('integrations', __name__, url_prefix='/api/integrations')
hub = IntegrationHub()

def require_user_id(f):
    """Decorator to require user_id in request"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-User-ID') or request.args.get('user_id')
        if not user_id:
            return jsonify({'error': 'User ID required'}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function

# ==================== LMS ENDPOINTS ====================

@integration_bp.route('/lms/connect', methods=['POST'])
@require_user_id
def connect_lms(user_id):
    """Connect to an LMS"""
    try:
        data = request.get_json()
        
        if not data.get('lms_type'):
            return jsonify({'error': 'lms_type is required'}), 400
        
        result = hub.connect_lms(user_id, data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error connecting LMS: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/lms/connection', methods=['GET'])
@require_user_id
def get_lms_connection(user_id):
    """Get LMS connection details"""
    try:
        lms_type = request.args.get('lms_type')
        connection = hub.get_lms_connection(user_id, lms_type)
        
        if connection:
            # Don't send sensitive tokens to frontend
            connection.pop('access_token', None)
            connection.pop('refresh_token', None)
            return jsonify({'success': True, 'connection': connection})
        else:
            return jsonify({'success': False, 'message': 'No LMS connection found'}), 404
    except Exception as e:
        logger.error(f"Error getting LMS connection: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/lms/sync', methods=['POST'])
@require_user_id
def sync_lms(user_id):
    """Sync courses from LMS"""
    try:
        data = request.get_json()
        lms_type = data.get('lms_type')
        
        if not lms_type:
            return jsonify({'error': 'lms_type is required'}), 400
        
        result = hub.sync_lms_courses(user_id, lms_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error syncing LMS: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== GOOGLE CLASSROOM ENDPOINTS ====================

@integration_bp.route('/google-classroom/connect', methods=['POST'])
@require_user_id
def connect_google_classroom(user_id):
    """Connect to Google Classroom"""
    try:
        data = request.get_json()
        result = hub.connect_google_classroom(user_id, data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error connecting Google Classroom: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/google-classroom/connection', methods=['GET'])
@require_user_id
def get_google_classroom_connection(user_id):
    """Get Google Classroom connection"""
    try:
        connection = hub.get_google_classroom_connection(user_id)
        
        if connection:
            # Don't send sensitive tokens
            connection.pop('access_token', None)
            connection.pop('refresh_token', None)
            return jsonify({'success': True, 'connection': connection})
        else:
            return jsonify({'success': False, 'message': 'Not connected'}), 404
    except Exception as e:
        logger.error(f"Error getting Google Classroom connection: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/google-classroom/sync', methods=['POST'])
@require_user_id
def sync_google_classroom(user_id):
    """Sync Google Classroom assignments"""
    try:
        result = hub.sync_google_classroom(user_id)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error syncing Google Classroom: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== CALENDAR ENDPOINTS ====================

@integration_bp.route('/calendar/connect', methods=['POST'])
@require_user_id
def connect_calendar(user_id):
    """Connect to calendar app"""
    try:
        data = request.get_json()
        
        if not data.get('calendar_type'):
            return jsonify({'error': 'calendar_type is required'}), 400
        
        result = hub.connect_calendar(user_id, data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error connecting calendar: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/calendar/connection', methods=['GET'])
@require_user_id
def get_calendar_connection(user_id):
    """Get calendar connection"""
    try:
        calendar_type = request.args.get('calendar_type')
        connection = hub.get_calendar_connection(user_id, calendar_type)
        
        if connection:
            # Don't send sensitive tokens
            connection.pop('access_token', None)
            connection.pop('refresh_token', None)
            return jsonify({'success': True, 'connection': connection})
        else:
            return jsonify({'success': False, 'message': 'No calendar connection found'}), 404
    except Exception as e:
        logger.error(f"Error getting calendar connection: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/calendar/sync', methods=['POST'])
@require_user_id
def sync_calendar(user_id):
    """Sync calendar events"""
    try:
        data = request.get_json()
        calendar_type = data.get('calendar_type')
        
        if not calendar_type:
            return jsonify({'error': 'calendar_type is required'}), 400
        
        result = hub.sync_calendar(user_id, calendar_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error syncing calendar: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== API KEY ENDPOINTS ====================

@integration_bp.route('/api-keys', methods=['GET'])
@require_user_id
def get_api_keys(user_id):
    """Get user's API keys"""
    try:
        keys = hub.get_user_api_keys(user_id)
        return jsonify({'success': True, 'api_keys': keys, 'count': len(keys)})
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/api-keys/generate', methods=['POST'])
@require_user_id
def generate_api_key(user_id):
    """Generate a new API key"""
    try:
        data = request.get_json() or {}
        result = hub.generate_api_key(user_id, data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error generating API key: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/api-keys/<key_id>/revoke', methods=['POST'])
def revoke_api_key(key_id):
    """Revoke an API key"""
    try:
        revoked = hub.revoke_api_key(key_id)
        
        if revoked:
            return jsonify({'success': True, 'message': 'API key revoked'})
        else:
            return jsonify({'success': False, 'message': 'API key not found'}), 404
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/api-keys/validate', methods=['POST'])
def validate_api_key():
    """Validate an API key"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'api_key is required'}), 400
        
        key_data = hub.validate_api_key(api_key)
        
        if key_data:
            # Don't send secret
            key_data.pop('api_secret', None)
            return jsonify({'success': True, 'valid': True, 'key_data': key_data})
        else:
            return jsonify({'success': True, 'valid': False})
    except Exception as e:
        logger.error(f"Error validating API key: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== WEBHOOK ENDPOINTS ====================

@integration_bp.route('/webhooks', methods=['GET'])
@require_user_id
def get_webhooks(user_id):
    """Get user's webhooks"""
    try:
        webhooks = hub.get_user_webhooks(user_id)
        return jsonify({'success': True, 'webhooks': webhooks, 'count': len(webhooks)})
    except Exception as e:
        logger.error(f"Error getting webhooks: {e}")
        return jsonify({'error': str(e)}), 500

@integration_bp.route('/webhooks/create', methods=['POST'])
@require_user_id
def create_webhook(user_id):
    """Create a webhook subscription"""
    try:
        data = request.get_json()
        
        required_fields = ['api_key_id', 'webhook_url', 'events']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = hub.create_webhook(user_id, data['api_key_id'], data)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== LOGS ENDPOINTS ====================

@integration_bp.route('/logs', methods=['GET'])
@require_user_id
def get_integration_logs(user_id):
    """Get integration activity logs"""
    try:
        limit = int(request.args.get('limit', 50))
        logs = hub.get_integration_logs(user_id, limit)
        
        return jsonify({'success': True, 'logs': logs, 'count': len(logs)})
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500

# ==================== OVERVIEW ENDPOINT ====================

@integration_bp.route('/overview', methods=['GET'])
@require_user_id
def get_integrations_overview(user_id):
    """Get overview of all integrations"""
    try:
        overview = {
            'lms': hub.get_lms_connection(user_id),
            'google_classroom': hub.get_google_classroom_connection(user_id),
            'calendar': hub.get_calendar_connection(user_id),
            'api_keys_count': len(hub.get_user_api_keys(user_id)),
            'webhooks_count': len(hub.get_user_webhooks(user_id))
        }
        
        # Remove sensitive data
        for key in ['lms', 'google_classroom', 'calendar']:
            if overview[key]:
                overview[key].pop('access_token', None)
                overview[key].pop('refresh_token', None)
        
        return jsonify({'success': True, 'overview': overview})
    except Exception as e:
        logger.error(f"Error getting overview: {e}")
        return jsonify({'error': str(e)}), 500
