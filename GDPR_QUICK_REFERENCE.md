# GDPR Compliance - Quick Reference Guide

## Quick Start

### 1. Initialize Services
```python
from gdpr_service import GDPRService, BreachNotifier
from encryption_service import EncryptionService
from auth_models import create_database_engine, create_session_factory

# Create database session
engine = create_database_engine()
SessionFactory = create_session_factory(engine)
db_session = SessionFactory()

# Create services
encryption = EncryptionService()
gdpr = GDPRService(db_session, encryption)
```

### 2. Export User Data
```python
# Export all user data (GDPR Article 15)
export_data = gdpr.export_user_data(user_id='user-123')

# Returns JSON with:
# - account info
# - sessions
# - audit logs
# - consent records
# - metadata
```

### 3. Delete User Account
```python
# Delete user and all data (GDPR Article 17)
result = gdpr.delete_user_data(
    user_id='user-123',
    reason='User requested deletion'
)

# Deletes:
# - User account
# - All sessions
# - Anonymizes audit logs (retained for compliance)
```

### 4. Manage Consent
```python
# Record consent (GDPR Article 7)
consent = gdpr.record_consent(
    user_id='user-123',
    consent_type='marketing',
    given=True,
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...'
)

# Get consent status
status = gdpr.get_consent_status(user_id='user-123')
```

### 5. Encrypt Sensitive Data
```python
# Encrypt single value
encrypted = encryption.encrypt('sensitive data')
decrypted = encryption.decrypt(encrypted)

# Encrypt dictionary fields
data = {
    'email': 'user@example.com',
    'phone': '555-1234',
    'name': 'John Doe'
}
encrypted_data = encryption.encrypt_dict(data, ['email', 'phone'])
decrypted_data = encryption.decrypt_dict(encrypted_data, ['email', 'phone'])
```

### 6. Handle Data Breaches
```python
# Detect breach (GDPR Articles 33 & 34)
notifier = BreachNotifier(db_session)

breach = notifier.detect_breach(
    breach_type='unauthorized_access',
    affected_data='user emails',
    severity='high'
)

# Notify affected users (within 72 hours)
notified_count = notifier.notify_affected_users(
    user_ids=['user-1', 'user-2', 'user-3'],
    breach_info=breach
)
```

## API Endpoints

### Export Data
```bash
GET /api/user/export
Headers: X-User-ID: user-123
Response: JSON file download
```

### Delete Account
```bash
DELETE /api/user/account
Headers: X-User-ID: user-123
Body: {"reason": "User requested deletion"}
Response: {"message": "Account successfully deleted", ...}
```

### Get Consent Status
```bash
GET /api/user/consent
Headers: X-User-ID: user-123
Response: {"user_id": "user-123", "consent_given": true, ...}
```

### Update Consent
```bash
POST /api/user/consent
Headers: X-User-ID: user-123
Body: {"type": "marketing", "given": true}
Response: {"message": "Consent updated successfully", ...}
```

### Get Audit Logs
```bash
GET /api/user/audit-logs?limit=100
Headers: X-User-ID: user-123
Response: {"audit_logs": [...], "count": 50}
```

## Environment Variables

### Required
```bash
# Encryption key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-base64-encoded-key

# Database connection
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Flask secret
SECRET_KEY=your-secret-key
```

### Optional
```bash
# Flask environment
FLASK_ENV=development

# Logging level
LOG_LEVEL=INFO
```

## GDPR Articles Reference

### Article 15: Right to Access
- Users can request all their personal data
- Data must be provided in machine-readable format
- Must respond within 30 days

### Article 17: Right to Erasure
- Users can request deletion of their data
- Must delete within 30 days
- Some data may be retained for legal compliance

### Article 7: Conditions for Consent
- Consent must be freely given and specific
- Users can withdraw consent at any time
- Consent must be logged with timestamp

### Article 30: Records of Processing
- Must maintain records of all data processing
- Logs must include who, what, when, why
- Retain for 7 years

### Article 32: Security of Processing
- Must implement appropriate security measures
- Encryption at rest and in transit
- Regular security testing

### Articles 33 & 34: Breach Notification
- Must notify authorities within 72 hours
- Must notify affected users without undue delay
- Must log all breaches

## Testing

### Run All Tests
```bash
python test_gdpr_standalone.py
```

### Run Property Tests
```bash
python -m pytest test_gdpr_properties.py -v
```

### Run Integration Tests
```bash
python -m pytest test_gdpr_integration.py -v
```

## Common Tasks

### Generate Encryption Key
```python
from encryption_service import EncryptionService
key = EncryptionService.generate_key()
print(f"ENCRYPTION_KEY={key}")
```

### Check Deletion Eligibility
```python
can_delete, reasons = gdpr.check_deletion_eligibility(user_id)
if not can_delete:
    print(f"Cannot delete: {reasons}")
```

### Cleanup Old Audit Logs
```python
# Delete logs older than 7 years (2555 days)
deleted_count = gdpr.cleanup_old_audit_logs(retention_days=2555)
print(f"Deleted {deleted_count} old logs")
```

### Verify Encryption
```python
if encryption.verify_encryption():
    print("Encryption working correctly")
else:
    print("Encryption verification failed")
```

## Troubleshooting

### Issue: ImportError for cryptography
```bash
pip install cryptography
```

### Issue: Missing encryption key
```bash
# Generate and set key
export ENCRYPTION_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

### Issue: Database connection error
```bash
# Check DATABASE_URL is set
echo $DATABASE_URL

# Test connection
python -c "from auth_models import create_database_engine; create_database_engine()"
```

### Issue: Tests failing
```bash
# Set required environment variables
export FLASK_ENV=development
export SECRET_KEY=test-key
export DATABASE_URL=sqlite:///test.db

# Run tests
python test_gdpr_standalone.py
```

## Security Best Practices

1. **Key Management**
   - Store encryption keys in secure key management service
   - Rotate keys regularly
   - Never commit keys to version control

2. **Access Control**
   - Require authentication for all GDPR endpoints
   - Implement role-based access control
   - Log all access attempts

3. **Data Minimization**
   - Only collect necessary data
   - Delete data when no longer needed
   - Anonymize data where possible

4. **Regular Audits**
   - Review audit logs regularly
   - Conduct security assessments
   - Test breach notification procedures

5. **Documentation**
   - Maintain data processing records
   - Document consent procedures
   - Keep breach notification logs

## Support

For issues or questions:
1. Check the comprehensive guide: `PHASE_11_GDPR_COMPLIANCE_COMPLETE.md`
2. Review test files for usage examples
3. Check audit logs for debugging

## License & Compliance

This implementation provides tools for GDPR compliance but does not guarantee legal compliance. Consult with legal counsel to ensure your specific use case meets all GDPR requirements.
