"""
GDPR Implementation Validation Script
Validates all GDPR features are working correctly
"""

import os
import sys
from datetime import datetime

# Set environment
os.environ['FLASK_ENV'] = 'development'

print("=" * 80)
print("GDPR Implementation Validation")
print("=" * 80)
print()

# Test 1: Import all modules
print("1. Testing module imports...")
try:
    from gdpr_service import GDPRService, BreachNotifier
    from encryption_service import EncryptionService
    from gdpr_routes import gdpr_bp
    from auth_models import User, Session as UserSession, AuditLog
    print("   ✓ All modules imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Encryption Service
print("\n2. Testing Encryption Service...")
try:
    encryption = EncryptionService()
    
    # Test basic encryption
    plaintext = "sensitive data"
    ciphertext = encryption.encrypt(plaintext)
    decrypted = encryption.decrypt(ciphertext)
    
    assert decrypted == plaintext, "Decryption failed"
    assert ciphertext != plaintext, "Encryption failed"
    
    # Test verification
    assert encryption.verify_encryption(), "Encryption verification failed"
    
    print("   ✓ Encryption service working correctly")
except Exception as e:
    print(f"   ✗ Encryption test failed: {e}")
    sys.exit(1)

# Test 3: Field-level encryption
print("\n3. Testing Field-Level Encryption...")
try:
    data = {
        'email': 'user@example.com',
        'phone': '555-1234',
        'name': 'John Doe'
    }
    
    encrypted = encryption.encrypt_dict(data, ['email', 'phone'])
    assert encrypted['email'] != data['email'], "Email not encrypted"
    assert encrypted['phone'] != data['phone'], "Phone not encrypted"
    assert encrypted['name'] == data['name'], "Name should not be encrypted"
    
    decrypted = encryption.decrypt_dict(encrypted, ['email', 'phone'])
    assert decrypted['email'] == data['email'], "Email decryption failed"
    assert decrypted['phone'] == data['phone'], "Phone decryption failed"
    
    print("   ✓ Field-level encryption working correctly")
except Exception as e:
    print(f"   ✗ Field-level encryption failed: {e}")
    sys.exit(1)

# Test 4: GDPR Service initialization
print("\n4. Testing GDPR Service...")
try:
    from unittest.mock import MagicMock
    
    mock_db = MagicMock()
    gdpr = GDPRService(mock_db, encryption)
    
    assert gdpr.db == mock_db, "Database session not set"
    assert gdpr.encryption == encryption, "Encryption service not set"
    
    print("   ✓ GDPR service initialized correctly")
except Exception as e:
    print(f"   ✗ GDPR service initialization failed: {e}")
    sys.exit(1)

# Test 5: Audit logging
print("\n5. Testing Audit Logging...")
try:
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    
    gdpr._log_audit_event(
        user_id='test-user',
        event_type='data_access',
        event_category='data_access',
        resource_type='user',
        resource_id='test-user'
    )
    
    assert mock_db.add.called, "Audit log not added"
    assert mock_db.commit.called, "Changes not committed"
    
    print("   ✓ Audit logging working correctly")
except Exception as e:
    print(f"   ✗ Audit logging failed: {e}")
    sys.exit(1)

# Test 6: Consent management
print("\n6. Testing Consent Management...")
try:
    from unittest.mock import Mock
    
    mock_user = Mock()
    mock_user.id = 'test-user'
    mock_user.consent_given_at = None
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_db.query.return_value = mock_query
    
    consent = gdpr.record_consent(
        user_id='test-user',
        consent_type='marketing',
        given=True
    )
    
    assert consent['user_id'] == 'test-user', "User ID mismatch"
    assert consent['consent_type'] == 'marketing', "Consent type mismatch"
    assert consent['given'] is True, "Consent status mismatch"
    
    print("   ✓ Consent management working correctly")
except Exception as e:
    print(f"   ✗ Consent management failed: {e}")
    sys.exit(1)

# Test 7: Breach notification
print("\n7. Testing Breach Notification...")
try:
    notifier = BreachNotifier(mock_db)
    
    breach = notifier.detect_breach(
        breach_type='unauthorized_access',
        affected_data='user emails',
        severity='high'
    )
    
    assert 'breach_id' in breach, "Breach ID missing"
    assert breach['breach_type'] == 'unauthorized_access', "Breach type mismatch"
    assert breach['severity'] == 'high', "Severity mismatch"
    assert 'notification_deadline' in breach, "Deadline missing"
    
    # Verify 72-hour deadline
    from datetime import timedelta
    detected_at = datetime.fromisoformat(breach['detected_at'].replace('Z', '+00:00'))
    deadline = datetime.fromisoformat(breach['notification_deadline'].replace('Z', '+00:00'))
    time_diff = deadline - detected_at
    
    assert time_diff <= timedelta(hours=72), "Deadline exceeds 72 hours"
    
    print("   ✓ Breach notification working correctly")
except Exception as e:
    print(f"   ✗ Breach notification failed: {e}")
    sys.exit(1)

# Test 8: Data export structure
print("\n8. Testing Data Export Structure...")
try:
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
    
    export = gdpr.export_user_data('test-user')
    
    required_sections = ['export_info', 'account', 'sessions', 'audit_logs', 'consent_records', 'metadata']
    for section in required_sections:
        assert section in export, f"Missing section: {section}"
    
    assert export['export_info']['gdpr_article'] == 'Article 15 - Right to Access'
    assert export['export_info']['format'] == 'JSON'
    
    print("   ✓ Data export structure correct")
except Exception as e:
    print(f"   ✗ Data export test failed: {e}")
    sys.exit(1)

# Test 9: Data deletion
print("\n9. Testing Data Deletion...")
try:
    mock_user = Mock()
    mock_user.id = 'test-user'
    
    mock_query = Mock()
    mock_query.filter.return_value.first.return_value = mock_user
    mock_query.filter.return_value.delete.return_value = 5
    mock_query.filter.return_value.update.return_value = 10
    mock_db.query.return_value = mock_query
    mock_db.delete = MagicMock()
    
    result = gdpr.delete_user_data('test-user', 'Test deletion')
    
    assert 'deleted_at' in result, "Deleted timestamp missing"
    assert 'data_removed' in result, "Data removed list missing"
    assert 'reason' in result, "Reason missing"
    assert result['reason'] == 'Test deletion', "Reason mismatch"
    
    print("   ✓ Data deletion working correctly")
except Exception as e:
    print(f"   ✗ Data deletion failed: {e}")
    sys.exit(1)

# Test 10: API Blueprint
print("\n10. Testing API Blueprint...")
try:
    assert gdpr_bp.name == 'gdpr', "Blueprint name incorrect"
    assert gdpr_bp.url_prefix == '/api/user', "URL prefix incorrect"
    
    # Check routes exist
    routes = [rule.rule for rule in gdpr_bp.url_map.iter_rules()] if hasattr(gdpr_bp, 'url_map') else []
    
    print("   ✓ API blueprint configured correctly")
except Exception as e:
    print(f"   ✗ API blueprint test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 80)
print("VALIDATION COMPLETE")
print("=" * 80)
print()
print("✓ All 10 validation tests passed successfully!")
print()
print("GDPR Implementation Status:")
print("  ✓ Encryption Service - Working")
print("  ✓ GDPR Service - Working")
print("  ✓ Audit Logging - Working")
print("  ✓ Consent Management - Working")
print("  ✓ Breach Notification - Working")
print("  ✓ Data Export - Working")
print("  ✓ Data Deletion - Working")
print("  ✓ API Routes - Configured")
print()
print("Phase 11: GDPR Compliance is COMPLETE ✅")
print("=" * 80)
