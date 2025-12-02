"""
GDPR API Routes
Implements GDPR compliance endpoints
"""

from flask import Blueprint, request, jsonify, send_file, g
from functools import wraps
import json
import io
from datetime import datetime
from typing import Optional
import logging

from gdpr_service import GDPRService, BreachNotifier
from encryption_service import EncryptionService
from auth_models import create_database_engine, create_session_factory

logger = logging.getLogger(__name__)

# Create blueprint
gdpr_bp = Blueprint('gdpr', __name__, url_prefix='/api/user')

# Initialize services (will be properly initialized in app)
_db_session_factory = None
_encryption_service = None


def init_gdpr_routes(app):
    """Initialize GDPR routes with app context"""
    global _db_session_factory, _encryption_service
    
    engine = create_database_engine()
    _db_session_factory = create_session_factory(engine)
    _encryption_service = EncryptionService()
    
    app.register_blueprint(gdpr_bp)


def get_gdpr_service():
    """Get GDPR service instance"""
    if not hasattr(g, 'gdpr_service'):
        db_session = _db_session_factory()
        g.gdpr_service = GDPRService(db_session, _encryption_service)
    return g.gdpr_service


def require_auth(f):
    """Authentication decorator (simplified for now)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get user from request context
        # In production, validate JWT token
        user_id = request.headers.get('X-User-ID') or g.get('user_id')
        if not user_id:
            return jsonify({'error': 'Authentication required'}), 401
        
        g.user_id = user_id
        return f(*args, **kwargs)
    return decorated


# ==================== DATA EXPORT (Article 15) ====================

@gdpr_bp.route('/export', methods=['GET'])
@require_auth
def export_user_data():
    """
    Export all user data in JSON format
    GDPR Article 15: Right to Access
    """
    try:
        user_id = g.user_id
        gdpr_service = get_gdpr_service()
        
        # Export user data
        user_data = gdpr_service.export_user_data(user_id)
        
        # Create JSON file
        json_data = json.dumps(user_data, indent=2, ensure_ascii=False)
        json_bytes = io.BytesIO(json_data.encode('utf-8'))
        
        filename = f'data_export_{user_id}_{datetime.now().strftime("%Y%m%d")}.json'
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        return jsonify({
            'error': 'Failed to export data',
            'message': str(e)
        }), 500


# ==================== DATA DELETION (Article 17) ====================

@gdpr_bp.route('/account', methods=['DELETE'])
@require_auth
def delete_user_account():
    """
    Delete user account and all data
    GDPR Article 17: Right to Erasure
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}
        reason = data.get('reason', 'User requested deletion')
        
        gdpr_service = get_gdpr_service()
        
        # Delete user data
        result = gdpr_service.delete_user_data(user_id, reason)
        
        return jsonify({
            'message': 'Account successfully deleted',
            'deleted_at': result['deleted_at'],
            'data_removed': result['data_removed'],
            'gdpr_article': 'Article 17 - Right to Erasure'
        }), 200
        
    except ValueError as e:
        return jsonify({
            'error': 'Cannot delete account',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Account deletion failed: {e}")
        return jsonify({
            'error': 'Failed to delete account',
            'message': str(e)
        }), 500


# ==================== CONSENT MANAGEMENT ====================

@gdpr_bp.route('/consent', methods=['GET'])
@require_auth
def get_consent_status():
    """Get user consent status"""
    try:
        user_id = g.user_id
        gdpr_service = get_gdpr_service()
        
        consent_status = gdpr_service.get_consent_status(user_id)
        
        return jsonify(consent_status), 200
        
    except Exception as e:
        logger.error(f"Failed to get consent status: {e}")
        return jsonify({
            'error': 'Failed to get consent status',
            'message': str(e)
        }), 500


@gdpr_bp.route('/consent', methods=['POST'])
@require_auth
def update_consent():
    """Update user consent"""
    try:
        user_id = g.user_id
        data = request.get_json()
        
        consent_type = data.get('type', 'terms_of_service')
        given = data.get('given', False)
        
        gdpr_service = get_gdpr_service()
        
        consent_record = gdpr_service.record_consent(
            user_id=user_id,
            consent_type=consent_type,
            given=given,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Consent updated successfully',
            'consent': consent_record
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to update consent: {e}")
        return jsonify({
            'error': 'Failed to update consent',
            'message': str(e)
        }), 500


# ==================== AUDIT LOGS ====================

@gdpr_bp.route('/audit-logs', methods=['GET'])
@require_auth
def get_audit_logs():
    """Get user audit logs"""
    try:
        user_id = g.user_id
        limit = request.args.get('limit', 100, type=int)
        
        gdpr_service = get_gdpr_service()
        
        logs = gdpr_service.get_audit_logs(user_id, limit)
        
        return jsonify({
            'audit_logs': logs,
            'count': len(logs)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return jsonify({
            'error': 'Failed to get audit logs',
            'message': str(e)
        }), 500


# ==================== BREACH NOTIFICATION (Admin only) ====================

@gdpr_bp.route('/breach/notify', methods=['POST'])
def notify_breach():
    """
    Notify users of a data breach (Admin only)
    GDPR Article 34: Communication of personal data breach to data subject
    """
    try:
        # Check admin authorization
        # In production, verify admin role
        
        data = request.get_json()
        breach_type = data.get('breach_type')
        affected_data = data.get('affected_data')
        user_ids = data.get('user_ids', [])
        severity = data.get('severity', 'high')
        
        db_session = _db_session_factory()
        notifier = BreachNotifier(db_session)
        
        # Detect and log breach
        breach_record = notifier.detect_breach(breach_type, affected_data, severity)
        
        # Notify affected users
        notified_count = notifier.notify_affected_users(user_ids, breach_record)
        
        return jsonify({
            'message': 'Breach notification sent',
            'breach_id': breach_record['breach_id'],
            'notified_users': notified_count,
            'notification_deadline': breach_record['notification_deadline']
        }), 200
        
    except Exception as e:
        logger.error(f"Breach notification failed: {e}")
        return jsonify({
            'error': 'Failed to send breach notification',
            'message': str(e)
        }), 500


__all__ = ['gdpr_bp', 'init_gdpr_routes']
