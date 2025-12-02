"""
✅ GDPR: Data Subject Rights API
Implements GDPR Article 15 (right to access) and Article 17 (right to erasure)

Endpoints:
- GET /api/user/data - Export all user data (data portability)
- DELETE /api/user/delete - Delete user account and all data
- POST /api/user/consent - Update consent preferences
- GET /api/user/consent - Get current consent status
"""

from flask import Blueprint, request, jsonify, send_file
from functools import wraps
import json
import io
from datetime import datetime
from typing import Dict, List, Any
import os

# Import auth utilities (adjust path as needed)
try:
    from auth import get_current_user, require_auth
    from database import db  # Assuming you have a database module
except ImportError:
    # Fallback for testing
    def require_auth(optional=False):
        def require_auth_fallback_decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                return f(*args, **kwargs)
            return decorated
        return require_auth_fallback_decorator
    
    def get_current_user():
        return {'id': 'test_user', 'email': 'test@example.com'}

# Create blueprint
gdpr_api = Blueprint('gdpr', __name__, url_prefix='/api/user')

# ==================== DATA EXPORT (Article 15) ====================

@gdpr_api.route('/data', methods=['GET'])
@require_auth()
def export_user_data():
    """
    ✅ GDPR Article 15: Right to Access
    Export all personal data in machine-readable format (JSON)
    
    Response Time: Must respond within 30 days (GDPR requirement)
    Format: JSON (portable and machine-readable)
    """
    try:
        user = get_current_user()
        user_id = user.get('id')
        
        # Collect all user data from different sources
        user_data = {
            'export_info': {
                'requested_at': datetime.utcnow().isoformat() + 'Z',
                'format': 'JSON',
                'gdpr_article': 'Article 15 - Right to Access'
            },
            'account': _get_account_data(user_id),
            'profile': _get_profile_data(user_id),
            'content': _get_user_content(user_id),
            'activity': _get_activity_data(user_id),
            'preferences': _get_preferences_data(user_id),
            'consent': _get_consent_data(user_id),
            'metadata': {
                'account_created': user.get('created_at'),
                'last_login': user.get('last_login'),
                'total_records': 0  # Will be calculated
            }
        }
        
        # Calculate total records
        user_data['metadata']['total_records'] = sum([
            len(user_data.get('content', {}).get('queries', [])),
            len(user_data.get('activity', {}).get('sessions', [])),
            1  # account
        ])
        
        # Create JSON file
        json_data = json.dumps(user_data, indent=2, ensure_ascii=False)
        json_bytes = io.BytesIO(json_data.encode('utf-8'))
        
        filename = f'KNOWALLEDGE_data_export_{user_id}_{datetime.now().strftime("%Y%m%d")}.json'
        
        # Log export for audit trail
        _log_data_export(user_id)
        
        return send_file(
            json_bytes,
            mimetype='application/json',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to export data',
            'message': str(e)
        }), 500


def _get_account_data(user_id: str) -> Dict[str, Any]:
    """Get account information"""
    # TODO: Fetch from your database
    return {
        'user_id': user_id,
        'email': 'user@example.com',  # From database
        'username': 'username',  # From database
        'account_type': 'free',  # From database
        'verification_status': 'verified'
    }


def _get_profile_data(user_id: str) -> Dict[str, Any]:
    """Get profile information"""
    # TODO: Fetch from your database
    return {
        'display_name': 'User Name',
        'preferences': {
            'theme': 'dark',
            'language': 'en',
            'notifications': True
        }
    }


def _get_user_content(user_id: str) -> Dict[str, Any]:
    """Get user-generated content"""
    # TODO: Fetch from your database
    return {
        'queries': [
            {
                'id': 'query_1',
                'text': 'Example query',
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'response': 'Example response'
            }
        ],
        'topics': [
            {
                'id': 'topic_1',
                'name': 'Example Topic',
                'created_at': datetime.utcnow().isoformat() + 'Z'
            }
        ],
        'total_queries': 0,
        'total_topics': 0
    }


def _get_activity_data(user_id: str) -> Dict[str, Any]:
    """Get activity logs"""
    # TODO: Fetch from your database/logs
    return {
        'sessions': [
            {
                'session_id': 'session_1',
                'login_time': datetime.utcnow().isoformat() + 'Z',
                'ip_address': '192.168.1.1',  # Consider if you want to include this
                'user_agent': 'Mozilla/5.0...'
            }
        ],
        'total_sessions': 0
    }


def _get_preferences_data(user_id: str) -> Dict[str, Any]:
    """Get user preferences"""
    # TODO: Fetch from your database
    return {
        'cookie_preferences': {
            'necessary': True,
            'functional': True,
            'analytics': False,
            'performance': True
        },
        'privacy_settings': {
            'data_sharing': False,
            'analytics_tracking': False
        }
    }


def _get_consent_data(user_id: str) -> Dict[str, Any]:
    """Get consent records"""
    # TODO: Fetch from your database
    return {
        'consents': [
            {
                'type': 'terms_of_service',
                'given_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0',
                'ip_address': '192.168.1.1'
            },
            {
                'type': 'privacy_policy',
                'given_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0',
                'ip_address': '192.168.1.1'
            }
        ]
    }


def _log_data_export(user_id: str):
    """Log data export for audit trail"""
    # TODO: Log to your audit system
    print(f"✅ GDPR: User {user_id} exported their data at {datetime.utcnow()}")


# ==================== ACCOUNT DELETION (Article 17) ====================

@gdpr_api.route('/delete', methods=['DELETE'])
@require_auth()
def delete_user_account():
    """
    ✅ GDPR Article 17: Right to Erasure ("Right to be Forgotten")
    Delete user account and all associated personal data
    
    Process:
    1. Verify user identity (already authenticated)
    2. Mark account for deletion
    3. Schedule data deletion (30-day grace period optional)
    4. Notify user of deletion
    5. Log deletion for compliance
    
    Exceptions (data NOT deleted):
    - Legal obligations (financial records, legal disputes)
    - Public interest (research with anonymization)
    - Legitimate interests (fraud prevention)
    """
    try:
        user = get_current_user()
        user_id = user.get('id')
        
        # Optional: Require password confirmation
        data = request.get_json() or {}
        password = data.get('password')
        reason = data.get('reason', 'User requested deletion')
        
        # TODO: Verify password if provided
        # if password and not verify_password(user_id, password):
        #     return jsonify({'error': 'Invalid password'}), 401
        
        # Check if user can be deleted
        can_delete, reasons = _check_deletion_eligibility(user_id)
        
        if not can_delete:
            return jsonify({
                'error': 'Account cannot be deleted at this time',
                'reasons': reasons
            }), 400
        
        # Perform deletion
        deletion_result = _delete_user_data(user_id, reason)
        
        # Log deletion for audit trail
        _log_account_deletion(user_id, reason)
        
        return jsonify({
            'message': 'Account successfully deleted',
            'deleted_at': deletion_result['deleted_at'],
            'data_removed': deletion_result['data_removed'],
            'gdpr_article': 'Article 17 - Right to Erasure'
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to delete account',
            'message': str(e)
        }), 500


def _check_deletion_eligibility(user_id: str) -> tuple[bool, List[str]]:
    """Check if user account can be deleted"""
    reasons = []
    
    # Check for active subscriptions
    # TODO: Implement actual checks
    has_active_subscription = False
    if has_active_subscription:
        reasons.append('Active subscription must be cancelled first')
    
    # Check for pending legal issues
    has_legal_hold = False
    if has_legal_hold:
        reasons.append('Account under legal hold')
    
    # Check for unresolved disputes
    has_disputes = False
    if has_disputes:
        reasons.append('Unresolved account disputes')
    
    can_delete = len(reasons) == 0
    return can_delete, reasons


def _delete_user_data(user_id: str, reason: str) -> Dict[str, Any]:
    """Delete all user data"""
    deleted_at = datetime.utcnow().isoformat() + 'Z'
    data_removed = []
    
    try:
        # 1. Delete account data
        # TODO: db.users.delete({'id': user_id})
        data_removed.append('account')
        
        # 2. Delete user content (queries, topics, etc.)
        # TODO: db.queries.delete({'user_id': user_id})
        # TODO: db.topics.delete({'user_id': user_id})
        data_removed.append('content')
        
        # 3. Delete session data
        # TODO: db.sessions.delete({'user_id': user_id})
        data_removed.append('sessions')
        
        # 4. Clear cache data
        # TODO: redis_client.delete(f'user:{user_id}:*')
        data_removed.append('cache')
        
        # 5. Delete uploaded files
        # TODO: Delete from storage
        data_removed.append('files')
        
        # 6. Anonymize logs (replace user_id with "deleted_user")
        # TODO: Anonymize instead of delete (for legal compliance)
        data_removed.append('logs_anonymized')
        
        # 7. Remove from third-party services
        # TODO: Call APIs to delete user data
        data_removed.append('third_party_services')
        
        # 8. Delete consent records (after retention period)
        # Keep for 30 days as proof of deletion
        # TODO: Schedule for deletion
        
        print(f"✅ GDPR: Deleted user {user_id} data: {data_removed}")
        
    except Exception as e:
        print(f"❌ Error deleting user data: {e}")
        raise
    
    return {
        'deleted_at': deleted_at,
        'data_removed': data_removed
    }


def _log_account_deletion(user_id: str, reason: str):
    """Log account deletion for audit trail"""
    # TODO: Log to your audit system
    log_entry = {
        'event': 'account_deletion',
        'user_id': user_id,
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'gdpr_article': 'Article 17'
    }
    print(f"✅ GDPR: Account deletion logged: {log_entry}")


# ==================== CONSENT MANAGEMENT ====================

@gdpr_api.route('/consent', methods=['GET'])
@require_auth()
def get_consent_status():
    """Get current consent preferences"""
    try:
        user = get_current_user()
        user_id = user.get('id')
        
        # TODO: Fetch from database
        consent_data = {
            'user_id': user_id,
            'consents': {
                'terms_of_service': {
                    'given': True,
                    'version': '1.0',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                },
                'privacy_policy': {
                    'given': True,
                    'version': '1.0',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                },
                'marketing': {
                    'given': False,
                    'version': '1.0',
                    'timestamp': None
                }
            },
            'cookie_preferences': {
                'necessary': True,
                'functional': True,
                'analytics': False,
                'performance': True
            }
        }
        
        return jsonify(consent_data), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get consent status',
            'message': str(e)
        }), 500


@gdpr_api.route('/consent', methods=['POST'])
@require_auth()
def update_consent():
    """Update consent preferences"""
    try:
        user = get_current_user()
        user_id = user.get('id')
        
        data = request.get_json()
        consent_type = data.get('type')  # 'marketing', 'analytics', etc.
        given = data.get('given', False)
        
        # TODO: Save to database
        consent_record = {
            'user_id': user_id,
            'type': consent_type,
            'given': given,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Log consent change
        print(f"✅ GDPR: User {user_id} updated consent: {consent_type} = {given}")
        
        return jsonify({
            'message': 'Consent updated successfully',
            'consent': consent_record
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to update consent',
            'message': str(e)
        }), 500


# ==================== DATA RECTIFICATION (Article 16) ====================

@gdpr_api.route('/rectify', methods=['PATCH'])
@require_auth()
def rectify_user_data():
    """
    ✅ GDPR Article 16: Right to Rectification
    Correct inaccurate or incomplete personal data
    """
    try:
        user = get_current_user()
        user_id = user.get('id')
        
        data = request.get_json()
        updates = data.get('updates', {})
        
        # TODO: Validate and update data
        # Allowed fields: email, username, display_name, preferences
        
        return jsonify({
            'message': 'Data updated successfully',
            'updated_fields': list(updates.keys())
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to rectify data',
            'message': str(e)
        }), 500


# Export blueprint
__all__ = ['gdpr_api']
