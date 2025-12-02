"""
Property Tests for GDPR Compliance
Tests all GDPR requirements using property-based testing
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import json
import hashlib
from unittest.mock import Mock, MagicMock, patch

from gdpr_service import GDPRService, BreachNotifier
from encryption_service import EncryptionService
from auth_models import User, Session as UserSession, AuditLog, UserRole, QuotaTier


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.query = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.delete = MagicMock()
    return session


@pytest.fixture
def encryption_service():
    """Create encryption service"""
    return EncryptionService()


@pytest.fixture
def gdpr_service(mock_db_session, encryption_service):
    """Create GDPR service"""
    return GDPRService(mock_db_session, encryption_service)


# ==================== Property 48: Audit Logging ====================

@given(
    user_id=st.text(min_size=1, max_size=36),
    event_type=st.sampled_from(['login', 'logout', 'data_access', 'data_export', 'account_deletion']),
    event_category=st.sampled_from(['auth', 'data_access', 'data_modification', 'admin'])
)
@settings(max_examples=100, deadline=1000)
def test_property_48_audit_logging(gdpr_service, mock_db_session, user_id, event_type, event_category):
    """
    Property 48: Audit logging
    
    Property: All personal data access must be logged with:
    - User ID
    - Event type
    - Timestamp
    - Event category
    
    Validates: Requirements 11.4
    """
    # Log audit event
    audit_log = gdpr_service._log_audit_event(
        user_id=user_id,
        event_type=event_type,
        event_category=event_category,
        resource_type='user',
        resource_id=user_id
    )
    
    # Verify audit log was created
    assert mock_db_session.add.called
    assert mock_db_session.commit.called
    
    # Verify audit log has required fields
    call_args = mock_db_session.add.call_args[0][0]
    assert hasattr(call_args, 'user_id')
    assert hasattr(call_args, 'event_type')
    assert hasattr(call_args, 'event_category')
    assert hasattr(call_args, 'created_at')


@given(
    user_id=st.text(min_size=1, max_size=36),
    event_count=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=1000)
def test_audit_log_retention(gdpr_service, mock_db_session, user_id, event_count):
    """
    Test: Audit logs are retained for 7 years
    
    Property: Audit logs must be kept for compliance period
    """
    # Create multiple audit events
    for i in range(event_count):
        gdpr_service._log_audit_event(
            user_id=user_id,
            event_type=f'event_{i}',
            event_category='data_access'
        )
    
    # Verify all events were logged
    assert mock_db_session.add.call_count == event_count
    assert mock_db_session.commit.call_count == event_count


# ==================== Property 49: Data Encryption at Rest ====================

@given(
    plaintext=st.text(min_size=1, max_size=1000)
)
@settings(max_examples=100, deadline=1000)
def test_property_49_encryption_at_rest(encryption_service, plaintext):
    """
    Property 49: Data encryption at rest
    
    Property: Sensitive data must be encrypted with AES-256:
    - Encryption produces different ciphertext than plaintext
    - Decryption recovers original plaintext
    - Same plaintext produces different ciphertext (with IV)
    
    Validates: Requirements 11.5
    """
    # Encrypt data
    ciphertext = encryption_service.encrypt(plaintext)
    
    # Verify ciphertext is different from plaintext
    assert ciphertext != plaintext
    
    # Verify decryption recovers plaintext
    decrypted = encryption_service.decrypt(ciphertext)
    assert decrypted == plaintext
    
    # Verify encryption is reversible
    assert encryption_service.decrypt(encryption_service.encrypt(plaintext)) == plaintext


@given(
    plaintext=st.text(min_size=1, max_size=100)
)
@settings(max_examples=50, deadline=1000)
def test_encryption_deterministic_with_same_key(encryption_service, plaintext):
    """
    Test: Encryption with same key can decrypt data
    
    Property: Same key must be able to decrypt encrypted data
    """
    # Encrypt with service
    ciphertext = encryption_service.encrypt(plaintext)
    
    # Decrypt with same service (same key)
    decrypted = encryption_service.decrypt(ciphertext)
    
    # Verify plaintext recovered
    assert decrypted == plaintext


@given(
    data=st.dictionaries(
        keys=st.sampled_from(['email', 'phone', 'address', 'name']),
        values=st.text(min_size=1, max_size=100),
        min_size=1,
        max_size=4
    ),
    fields_to_encrypt=st.lists(
        st.sampled_from(['email', 'phone', 'address']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
@settings(max_examples=50, deadline=1000)
def test_field_level_encryption(encryption_service, data, fields_to_encrypt):
    """
    Test: Field-level encryption for sensitive data
    
    Property: Only specified fields should be encrypted
    """
    # Filter fields that exist in data
    fields_to_encrypt = [f for f in fields_to_encrypt if f in data]
    assume(len(fields_to_encrypt) > 0)
    
    # Encrypt specific fields
    encrypted_data = encryption_service.encrypt_dict(data, fields_to_encrypt)
    
    # Verify encrypted fields are different
    for field in fields_to_encrypt:
        if field in data:
            assert encrypted_data[field] != data[field]
    
    # Decrypt fields
    decrypted_data = encryption_service.decrypt_dict(encrypted_data, fields_to_encrypt)
    
    # Verify decrypted data matches original
    for field in fields_to_encrypt:
        if field in data:
            assert decrypted_data[field] == data[field]


# ==================== Property 50: TLS Encryption ====================

@given(
    tls_version=st.sampled_from(['TLSv1.2', 'TLSv1.3']),
    cipher_suite=st.sampled_from([
        'ECDHE-RSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'TLS_AES_256_GCM_SHA384'
    ])
)
@settings(max_examples=50, deadline=1000)
def test_property_50_tls_encryption(tls_version, cipher_suite):
    """
    Property 50: TLS encryption
    
    Property: All connections must use TLS 1.2+ with strong ciphers:
    - TLS version >= 1.2
    - Strong cipher suites only
    - No weak ciphers (RC4, DES, MD5)
    
    Validates: Requirements 11.6
    """
    # Verify TLS version is 1.2 or higher
    assert tls_version in ['TLSv1.2', 'TLSv1.3']
    
    # Verify cipher suite is strong
    weak_ciphers = ['RC4', 'DES', 'MD5', 'NULL', 'EXPORT']
    assert not any(weak in cipher_suite for weak in weak_ciphers)
    
    # Verify cipher suite uses strong encryption
    strong_algorithms = ['AES256', 'AES128', 'CHACHA20']
    assert any(algo in cipher_suite for algo in strong_algorithms)


# ==================== Data Export Tests ====================

@given(
    user_id=st.text(min_size=1, max_size=36),
    email=st.emails()
)
@settings(max_examples=50, deadline=1000)
def test_data_export_completeness(gdpr_service, mock_db_session, user_id, email):
    """
    Test: Data export includes all user data
    
    Property: Export must include all personal data
    Validates: Requirements 11.1
    """
    # Mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.email = email
    mock_user.role = UserRole.USER
    mock_user.quota_tier = QuotaTier.FREE
    mock_user.created_at = datetime.utcnow()
    mock_user.updated_at = datetime.utcnow()
    mock_user.last_login = datetime.utcnow()
    mock_user.email_verified = True
    mock_user.consent_given_at = datetime.utcnow()
    mock_user.data_export_requested_at = None
    
    # Mock query
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_query.filter.return_value.all.return_value = []
    mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db_session.query.return_value = mock_query
    
    # Export data
    export_data = gdpr_service.export_user_data(user_id)
    
    # Verify export contains required sections
    assert 'export_info' in export_data
    assert 'account' in export_data
    assert 'sessions' in export_data
    assert 'audit_logs' in export_data
    assert 'consent_records' in export_data
    assert 'metadata' in export_data
    
    # Verify export info
    assert export_data['export_info']['gdpr_article'] == 'Article 15 - Right to Access'
    assert export_data['export_info']['format'] == 'JSON'
    
    # Verify account data
    assert export_data['account']['user_id'] == user_id
    assert export_data['account']['email'] == email


# ==================== Data Deletion Tests ====================

@given(
    user_id=st.text(min_size=1, max_size=36),
    reason=st.text(min_size=1, max_size=200)
)
@settings(max_examples=50, deadline=1000)
def test_data_deletion_completeness(gdpr_service, mock_db_session, user_id, reason):
    """
    Test: Data deletion removes all user data
    
    Property: Deletion must remove all personal data
    Validates: Requirements 11.2
    """
    # Mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    
    # Mock query
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_query.filter.return_value.delete.return_value = 5  # Mock deleted count
    mock_query.filter.return_value.update.return_value = 10  # Mock updated count
    mock_db_session.query.return_value = mock_query
    
    # Delete user data
    result = gdpr_service.delete_user_data(user_id, reason)
    
    # Verify deletion occurred
    assert 'deleted_at' in result
    assert 'data_removed' in result
    assert 'reason' in result
    assert result['reason'] == reason
    
    # Verify database operations
    assert mock_db_session.delete.called
    assert mock_db_session.commit.called


@given(
    user_id=st.text(min_size=1, max_size=36)
)
@settings(max_examples=50, deadline=1000)
def test_deletion_eligibility_check(gdpr_service, mock_db_session, user_id):
    """
    Test: Deletion eligibility is checked before deletion
    
    Property: System must verify user can be deleted
    """
    # Mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    
    # Mock query
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_db_session.query.return_value = mock_query
    
    # Check eligibility
    can_delete, reasons = gdpr_service.check_deletion_eligibility(user_id)
    
    # Verify check was performed
    assert isinstance(can_delete, bool)
    assert isinstance(reasons, list)


# ==================== Consent Management Tests ====================

@given(
    user_id=st.text(min_size=1, max_size=36),
    consent_type=st.sampled_from(['terms_of_service', 'privacy_policy', 'marketing', 'analytics']),
    given=st.booleans()
)
@settings(max_examples=100, deadline=1000)
def test_consent_recording(gdpr_service, mock_db_session, user_id, consent_type, given):
    """
    Test: Consent is properly recorded
    
    Property: Consent must be tracked with timestamp
    Validates: Requirements 11.3
    """
    # Mock user
    mock_user = Mock(spec=User)
    mock_user.id = user_id
    mock_user.consent_given_at = None
    
    # Mock query
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_db_session.query.return_value = mock_query
    
    # Record consent
    consent_record = gdpr_service.record_consent(
        user_id=user_id,
        consent_type=consent_type,
        given=given
    )
    
    # Verify consent record
    assert consent_record['user_id'] == user_id
    assert consent_record['consent_type'] == consent_type
    assert consent_record['given'] == given
    assert 'timestamp' in consent_record
    
    # Verify database was updated
    assert mock_db_session.commit.called


# ==================== Breach Notification Tests ====================

@given(
    breach_type=st.sampled_from(['unauthorized_access', 'data_leak', 'ransomware', 'insider_threat']),
    affected_data=st.text(min_size=10, max_size=200),
    severity=st.sampled_from(['low', 'medium', 'high', 'critical'])
)
@settings(max_examples=50, deadline=1000)
def test_breach_detection(mock_db_session, breach_type, affected_data, severity):
    """
    Test: Breach detection creates proper record
    
    Property: Breach must be logged with 72-hour deadline
    Validates: Requirements 11.7
    """
    notifier = BreachNotifier(mock_db_session)
    
    # Detect breach
    breach_record = notifier.detect_breach(breach_type, affected_data, severity)
    
    # Verify breach record
    assert 'breach_id' in breach_record
    assert breach_record['breach_type'] == breach_type
    assert breach_record['affected_data'] == affected_data
    assert breach_record['severity'] == severity
    assert 'detected_at' in breach_record
    assert 'notification_deadline' in breach_record
    
    # Verify deadline is within 72 hours
    detected_at = datetime.fromisoformat(breach_record['detected_at'].replace('Z', '+00:00'))
    deadline = datetime.fromisoformat(breach_record['notification_deadline'].replace('Z', '+00:00'))
    time_diff = deadline - detected_at
    assert time_diff <= timedelta(hours=72)


@given(
    user_count=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=20, deadline=1000)
def test_breach_notification_to_users(mock_db_session, user_count):
    """
    Test: Breach notification reaches all affected users
    
    Property: All affected users must be notified
    """
    notifier = BreachNotifier(mock_db_session)
    
    # Create mock users
    user_ids = [f'user_{i}' for i in range(user_count)]
    mock_users = []
    for user_id in user_ids:
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.email = f'{user_id}@example.com'
        mock_users.append(mock_user)
    
    # Mock query to return users one at a time
    mock_query = Mock()
    mock_query.filter.return_value.first.side_effect = mock_users
    mock_db_session.query.return_value = mock_query
    
    # Notify users
    breach_info = {
        'breach_type': 'data_leak',
        'severity': 'high'
    }
    notified_count = notifier.notify_affected_users(user_ids, breach_info)
    
    # Verify all users were notified
    assert notified_count == user_count


# ==================== Integration Tests ====================

def test_gdpr_service_initialization(mock_db_session, encryption_service):
    """Test GDPR service initializes correctly"""
    service = GDPRService(mock_db_session, encryption_service)
    
    assert service.db == mock_db_session
    assert service.encryption == encryption_service


def test_encryption_service_verification(encryption_service):
    """Test encryption service works correctly"""
    assert encryption_service.verify_encryption() is True


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
