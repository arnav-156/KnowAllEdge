"""
Integration Tests for GDPR API
Tests GDPR endpoints with real database operations
"""

import pytest
import json
from datetime import datetime
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from gdpr_routes import gdpr_bp, init_gdpr_routes
from gdpr_service import GDPRService, BreachNotifier
from encryption_service import EncryptionService
from auth_models import Base, User, Session as UserSession, AuditLog, UserRole, QuotaTier


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Initialize GDPR routes
    init_gdpr_routes(app)
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session():
    """Create test database session"""
    # Use in-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    user = User(
        id='test-user-123',
        email='test@example.com',
        password_hash='hashed_password',
        role=UserRole.USER,
        quota_tier=QuotaTier.FREE,
        email_verified=True,
        consent_given_at=datetime.utcnow()
    )
    
    db_session.add(user)
    db_session.commit()
    
    return user


@pytest.fixture
def encryption_service():
    """Create encryption service"""
    return EncryptionService()


@pytest.fixture
def gdpr_service(db_session, encryption_service):
    """Create GDPR service"""
    return GDPRService(db_session, encryption_service)


# ==================== Data Export Tests ====================

def test_export_user_data_endpoint(client, test_user):
    """Test data export endpoint"""
    response = client.get(
        '/api/user/export',
        headers={'X-User-ID': test_user.id}
    )
    
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    
    # Verify filename
    assert 'data_export' in response.headers.get('Content-Disposition', '')


def test_export_user_data_service(gdpr_service, test_user):
    """Test data export service method"""
    export_data = gdpr_service.export_user_data(test_user.id)
    
    # Verify structure
    assert 'export_info' in export_data
    assert 'account' in export_data
    assert 'sessions' in export_data
    assert 'audit_logs' in export_data
    assert 'consent_records' in export_data
    assert 'metadata' in export_data
    
    # Verify account data
    assert export_data['account']['user_id'] == test_user.id
    assert export_data['account']['email'] == test_user.email
    
    # Verify GDPR compliance
    assert export_data['export_info']['gdpr_article'] == 'Article 15 - Right to Access'


def test_export_includes_sessions(gdpr_service, db_session, test_user):
    """Test export includes user sessions"""
    # Create test session
    session = UserSession(
        user_id=test_user.id,
        token_hash='test_token_hash',
        expires_at=datetime.utcnow(),
        ip_address='192.168.1.1',
        device_type='desktop'
    )
    db_session.add(session)
    db_session.commit()
    
    # Export data
    export_data = gdpr_service.export_user_data(test_user.id)
    
    # Verify sessions included
    assert len(export_data['sessions']) > 0
    assert export_data['sessions'][0]['ip_address'] == '192.168.1.1'


def test_export_includes_audit_logs(gdpr_service, db_session, test_user):
    """Test export includes audit logs"""
    # Create test audit log
    audit_log = AuditLog(
        user_id=test_user.id,
        event_type='login',
        event_category='auth',
        resource_type='session'
    )
    db_session.add(audit_log)
    db_session.commit()
    
    # Export data
    export_data = gdpr_service.export_user_data(test_user.id)
    
    # Verify audit logs included
    assert len(export_data['audit_logs']) > 0
    assert export_data['audit_logs'][0]['event_type'] == 'login'


# ==================== Data Deletion Tests ====================

def test_delete_user_account_endpoint(client, test_user):
    """Test account deletion endpoint"""
    response = client.delete(
        '/api/user/account',
        headers={'X-User-ID': test_user.id},
        json={'reason': 'Test deletion'}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['message'] == 'Account successfully deleted'
    assert 'deleted_at' in data
    assert 'data_removed' in data


def test_delete_user_data_service(gdpr_service, db_session, test_user):
    """Test user data deletion service method"""
    # Create related data
    session = UserSession(
        user_id=test_user.id,
        token_hash='test_token',
        expires_at=datetime.utcnow()
    )
    db_session.add(session)
    db_session.commit()
    
    # Delete user
    result = gdpr_service.delete_user_data(test_user.id, 'Test deletion')
    
    # Verify deletion
    assert 'deleted_at' in result
    assert 'data_removed' in result
    assert 'account' in result['data_removed']
    
    # Verify user is deleted
    deleted_user = db_session.query(User).filter(User.id == test_user.id).first()
    assert deleted_user is None
    
    # Verify sessions are deleted
    sessions = db_session.query(UserSession).filter(UserSession.user_id == test_user.id).all()
    assert len(sessions) == 0


def test_delete_anonymizes_audit_logs(gdpr_service, db_session, test_user):
    """Test deletion anonymizes audit logs"""
    # Create audit log
    audit_log = AuditLog(
        user_id=test_user.id,
        event_type='data_access',
        event_category='data_access'
    )
    db_session.add(audit_log)
    db_session.commit()
    
    audit_log_id = audit_log.id
    
    # Delete user
    gdpr_service.delete_user_data(test_user.id)
    
    # Verify audit log is anonymized
    anonymized_log = db_session.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    assert anonymized_log is not None
    assert anonymized_log.user_id is None


def test_deletion_eligibility_check(gdpr_service, test_user):
    """Test deletion eligibility check"""
    can_delete, reasons = gdpr_service.check_deletion_eligibility(test_user.id)
    
    assert isinstance(can_delete, bool)
    assert isinstance(reasons, list)
    assert can_delete is True  # Test user should be deletable


def test_deletion_nonexistent_user(gdpr_service):
    """Test deletion of nonexistent user fails"""
    with pytest.raises(ValueError, match='User .* not found'):
        gdpr_service.delete_user_data('nonexistent-user')


# ==================== Consent Management Tests ====================

def test_get_consent_status_endpoint(client, test_user):
    """Test get consent status endpoint"""
    response = client.get(
        '/api/user/consent',
        headers={'X-User-ID': test_user.id}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'user_id' in data
    assert 'consent_given' in data


def test_update_consent_endpoint(client, test_user):
    """Test update consent endpoint"""
    response = client.post(
        '/api/user/consent',
        headers={'X-User-ID': test_user.id},
        json={
            'type': 'marketing',
            'given': True
        }
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['message'] == 'Consent updated successfully'
    assert 'consent' in data


def test_record_consent_service(gdpr_service, test_user):
    """Test consent recording service method"""
    consent_record = gdpr_service.record_consent(
        user_id=test_user.id,
        consent_type='analytics',
        given=True,
        ip_address='192.168.1.1'
    )
    
    assert consent_record['user_id'] == test_user.id
    assert consent_record['consent_type'] == 'analytics'
    assert consent_record['given'] is True
    assert 'timestamp' in consent_record


def test_get_consent_status_service(gdpr_service, test_user):
    """Test get consent status service method"""
    consent_status = gdpr_service.get_consent_status(test_user.id)
    
    assert consent_status['user_id'] == test_user.id
    assert 'consent_given' in consent_status
    assert consent_status['consent_given'] is True  # Test user has consent


def test_consent_withdrawal(gdpr_service, db_session, test_user):
    """Test consent can be withdrawn"""
    # Give consent
    gdpr_service.record_consent(test_user.id, 'marketing', True)
    
    # Withdraw consent
    gdpr_service.record_consent(test_user.id, 'marketing', False)
    
    # Verify withdrawal was logged
    audit_logs = gdpr_service.get_audit_logs(test_user.id)
    consent_logs = [log for log in audit_logs if log['event_type'] == 'consent_update']
    assert len(consent_logs) >= 2


# ==================== Audit Logging Tests ====================

def test_get_audit_logs_endpoint(client, test_user):
    """Test get audit logs endpoint"""
    response = client.get(
        '/api/user/audit-logs',
        headers={'X-User-ID': test_user.id}
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert 'audit_logs' in data
    assert 'count' in data


def test_audit_log_creation(gdpr_service, test_user):
    """Test audit log is created"""
    audit_log = gdpr_service._log_audit_event(
        user_id=test_user.id,
        event_type='data_access',
        event_category='data_access',
        resource_type='user',
        resource_id=test_user.id
    )
    
    assert audit_log.user_id == test_user.id
    assert audit_log.event_type == 'data_access'
    assert audit_log.event_category == 'data_access'


def test_get_audit_logs_service(gdpr_service, db_session, test_user):
    """Test get audit logs service method"""
    # Create audit logs
    for i in range(5):
        audit_log = AuditLog(
            user_id=test_user.id,
            event_type=f'event_{i}',
            event_category='data_access'
        )
        db_session.add(audit_log)
    db_session.commit()
    
    # Get audit logs
    logs = gdpr_service.get_audit_logs(test_user.id, limit=10)
    
    assert len(logs) >= 5


def test_audit_log_retention_cleanup(gdpr_service, db_session, test_user):
    """Test old audit logs are cleaned up"""
    # Create old audit log
    old_log = AuditLog(
        user_id=test_user.id,
        event_type='old_event',
        event_category='data_access',
        created_at=datetime(2015, 1, 1)  # Very old
    )
    db_session.add(old_log)
    db_session.commit()
    
    # Cleanup old logs (1 day retention for testing)
    deleted_count = gdpr_service.cleanup_old_audit_logs(retention_days=1)
    
    assert deleted_count >= 1


# ==================== Encryption Tests ====================

def test_encryption_service_encrypt_decrypt(encryption_service):
    """Test encryption and decryption"""
    plaintext = 'sensitive data'
    
    ciphertext = encryption_service.encrypt(plaintext)
    assert ciphertext != plaintext
    
    decrypted = encryption_service.decrypt(ciphertext)
    assert decrypted == plaintext


def test_encryption_dict_fields(encryption_service):
    """Test dictionary field encryption"""
    data = {
        'email': 'user@example.com',
        'phone': '555-1234',
        'name': 'John Doe'
    }
    
    encrypted = encryption_service.encrypt_dict(data, ['email', 'phone'])
    
    assert encrypted['email'] != data['email']
    assert encrypted['phone'] != data['phone']
    assert encrypted['name'] == data['name']  # Not encrypted
    
    decrypted = encryption_service.decrypt_dict(encrypted, ['email', 'phone'])
    
    assert decrypted['email'] == data['email']
    assert decrypted['phone'] == data['phone']


def test_encryption_verification(encryption_service):
    """Test encryption service verification"""
    assert encryption_service.verify_encryption() is True


# ==================== Breach Notification Tests ====================

def test_breach_detection(db_session):
    """Test breach detection"""
    notifier = BreachNotifier(db_session)
    
    breach_record = notifier.detect_breach(
        breach_type='unauthorized_access',
        affected_data='user emails',
        severity='high'
    )
    
    assert 'breach_id' in breach_record
    assert breach_record['breach_type'] == 'unauthorized_access'
    assert breach_record['severity'] == 'high'
    assert 'notification_deadline' in breach_record


def test_breach_notification_to_users(db_session, test_user):
    """Test breach notification to users"""
    notifier = BreachNotifier(db_session)
    
    breach_info = {
        'breach_type': 'data_leak',
        'severity': 'high'
    }
    
    notified_count = notifier.notify_affected_users([test_user.id], breach_info)
    
    assert notified_count == 1


# ==================== Error Handling Tests ====================

def test_export_nonexistent_user(gdpr_service):
    """Test export of nonexistent user fails"""
    with pytest.raises(ValueError, match='User .* not found'):
        gdpr_service.export_user_data('nonexistent-user')


def test_consent_nonexistent_user(gdpr_service):
    """Test consent for nonexistent user fails"""
    with pytest.raises(ValueError, match='User .* not found'):
        gdpr_service.record_consent('nonexistent-user', 'marketing', True)


def test_unauthorized_access(client):
    """Test unauthorized access is rejected"""
    response = client.get('/api/user/export')
    
    assert response.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
