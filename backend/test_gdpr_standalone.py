"""
Standalone GDPR Tests
Tests GDPR functionality without external dependencies
"""

import os
import sys

# Set environment before imports
os.environ['FLASK_ENV'] = 'development'

from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import json

# Import GDPR modules
from gdpr_service import GDPRService, BreachNotifier
from encryption_service import EncryptionService


def test_encryption_basic():
    """Test basic encryption/decryption"""
    print("Testing encryption service...")
    
    service = EncryptionService()
    
    # Test encryption
    plaintext = "sensitive data"
    ciphertext = service.encrypt(plaintext)
    
    assert ciphertext != plaintext, "Ciphertext should differ from plaintext"
    
    # Test decryption
    decrypted = service.decrypt(ciphertext)
    assert decrypted == plaintext, "Decryption should recover plaintext"
    
    print("✓ Encryption test passed")


def test_encryption_dict():
    """Test dictionary field encryption"""
    print("Testing dictionary encryption...")
    
    service = EncryptionService()
    
    data = {
        'email': 'user@example.com',
        'phone': '555-1234',
        'name': 'John Doe'
    }
    
    # Encrypt specific fields
    encrypted = service.encrypt_dict(data, ['email', 'phone'])
    
    assert encrypted['email'] != data['email'], "Email should be encrypted"
    assert encrypted['phone'] != data['phone'], "Phone should be encrypted"
    assert encrypted['name'] == data['name'], "Name should not be encrypted"
    
    # Decrypt fields
    decrypted = service.decrypt_dict(encrypted, ['email', 'phone'])
    
    assert decrypted['email'] == data['email'], "Email should be decrypted"
    assert decrypted['phone'] == data['phone'], "Phone should be decrypted"
    
    print("✓ Dictionary encryption test passed")


def test_gdpr_service_audit_logging():
    """Test audit logging"""
    print("Testing audit logging...")
    
    # Mock database session
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    
    # Create services
    encryption = EncryptionService()
    gdpr = GDPRService(mock_db, encryption)
    
    # Log audit event
    gdpr._log_audit_event(
        user_id='test-user',
        event_type='data_access',
        event_category='data_access',
        resource_type='user',
        resource_id='test-user'
    )
    
    # Verify database operations
    assert mock_db.add.called, "Audit log should be added to database"
    assert mock_db.commit.called, "Changes should be committed"
    
    print("✓ Audit logging test passed")


def test_gdpr_service_consent():
    """Test consent management"""
    print("Testing consent management...")
    
    # Mock database and user
    mock_db = MagicMock()
    mock_user = Mock()
    mock_user.id = 'test-user'
    mock_user.consent_given_at = None
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    
    # Create services
    encryption = EncryptionService()
    gdpr = GDPRService(mock_db, encryption)
    
    # Record consent
    consent_record = gdpr.record_consent(
        user_id='test-user',
        consent_type='marketing',
        given=True
    )
    
    # Verify consent record
    assert consent_record['user_id'] == 'test-user'
    assert consent_record['consent_type'] == 'marketing'
    assert consent_record['given'] is True
    assert 'timestamp' in consent_record
    
    print("✓ Consent management test passed")


def test_breach_notifier():
    """Test breach notification"""
    print("Testing breach notification...")
    
    # Mock database
    mock_db = MagicMock()
    
    # Create notifier
    notifier = BreachNotifier(mock_db)
    
    # Detect breach
    breach_record = notifier.detect_breach(
        breach_type='unauthorized_access',
        affected_data='user emails',
        severity='high'
    )
    
    # Verify breach record
    assert 'breach_id' in breach_record
    assert breach_record['breach_type'] == 'unauthorized_access'
    assert breach_record['severity'] == 'high'
    assert 'detected_at' in breach_record
    assert 'notification_deadline' in breach_record
    
    # Verify 72-hour deadline
    detected_at = datetime.fromisoformat(breach_record['detected_at'].replace('Z', '+00:00'))
    deadline = datetime.fromisoformat(breach_record['notification_deadline'].replace('Z', '+00:00'))
    time_diff = deadline - detected_at
    
    assert time_diff <= timedelta(hours=72), "Notification deadline should be within 72 hours"
    
    print("✓ Breach notification test passed")


def test_data_export():
    """Test data export"""
    print("Testing data export...")
    
    # Mock database and user
    mock_db = MagicMock()
    mock_user = Mock()
    mock_user.id = 'test-user'
    mock_user.email = 'test@example.com'
    mock_user.role = Mock(value='user')
    mock_user.quota_tier = Mock(value='free')
    mock_user.created_at = datetime.utcnow()
    mock_user.updated_at = datetime.utcnow()
    mock_user.last_login = datetime.utcnow()
    mock_user.email_verified = True
    mock_user.consent_given_at = datetime.utcnow()
    mock_user.data_export_requested_at = None
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_query.filter.return_value.all.return_value = []
    mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
    mock_db.query.return_value = mock_query
    
    # Create services
    encryption = EncryptionService()
    gdpr = GDPRService(mock_db, encryption)
    
    # Export data
    export_data = gdpr.export_user_data('test-user')
    
    # Verify export structure
    assert 'export_info' in export_data
    assert 'account' in export_data
    assert 'sessions' in export_data
    assert 'audit_logs' in export_data
    assert 'consent_records' in export_data
    assert 'metadata' in export_data
    
    # Verify GDPR compliance
    assert export_data['export_info']['gdpr_article'] == 'Article 15 - Right to Access'
    assert export_data['export_info']['format'] == 'JSON'
    
    print("✓ Data export test passed")


def test_data_deletion():
    """Test data deletion"""
    print("Testing data deletion...")
    
    # Mock database and user
    mock_db = MagicMock()
    mock_user = Mock()
    mock_user.id = 'test-user'
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_query.filter.return_value.delete.return_value = 5
    mock_query.filter.return_value.update.return_value = 10
    mock_db.query.return_value = mock_query
    
    # Create services
    encryption = EncryptionService()
    gdpr = GDPRService(mock_db, encryption)
    
    # Delete user data
    result = gdpr.delete_user_data('test-user', 'Test deletion')
    
    # Verify deletion
    assert 'deleted_at' in result
    assert 'data_removed' in result
    assert 'reason' in result
    assert result['reason'] == 'Test deletion'
    
    # Verify database operations
    assert mock_db.delete.called
    assert mock_db.commit.called
    
    print("✓ Data deletion test passed")


def run_all_tests():
    """Run all GDPR tests"""
    print("\n" + "=" * 80)
    print("GDPR Compliance Tests")
    print("=" * 80 + "\n")
    
    tests = [
        test_encryption_basic,
        test_encryption_dict,
        test_gdpr_service_audit_logging,
        test_gdpr_service_consent,
        test_breach_notifier,
        test_data_export,
        test_data_deletion
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
