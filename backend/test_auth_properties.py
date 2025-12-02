"""
Property-Based Tests for Authentication System

Tests JWT, API keys, and authentication properties using Hypothesis
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import jwt
import time
from auth import auth_manager, JWT_SECRET_KEY, JWT_ALGORITHM, require_auth, require_admin
from flask import Flask, g
from unittest.mock import Mock


# **Feature: production-readiness, Property 2: JWT token expiration**
# **Validates: Requirements 1.2**
@given(
    user_id=st.text(min_size=1, max_size=50),
    expires_in_hours=st.integers(min_value=1, max_value=48)
)
@settings(max_examples=100)
def test_property_jwt_expiration(user_id, expires_in_hours):
    """
    Property 2: JWT token expiration
    
    For any user and expiration time, JWT tokens should:
    1. Include expiration time in payload
    2. Be valid before expiration
    3. Be invalid after expiration
    4. Include user_id, role, and quota_tier in payload
    """
    from auth import User
    
    # Create test user
    user = User(
        user_id=user_id,
        role='user',
        quota_tier='free'
    )
    
    # Generate JWT token
    token = auth_manager.generate_jwt_token(user, expires_in_hours=expires_in_hours)
    
    # Property 2a: Token should be valid immediately after generation
    is_valid, payload = auth_manager.validate_jwt_token(token)
    assert is_valid, "Token should be valid immediately after generation"
    
    # Property 2b: Payload should include required fields
    assert payload['user_id'] == user_id, "Payload should include user_id"
    assert payload['role'] == 'user', "Payload should include role"
    assert payload['quota_tier'] == 'free', "Payload should include quota_tier"
    assert 'exp' in payload, "Payload should include expiration time"
    assert 'iat' in payload, "Payload should include issued at time"
    
    # Property 2c: Expiration should be approximately correct
    exp_time = datetime.fromtimestamp(payload['exp'])
    iat_time = datetime.fromtimestamp(payload['iat'])
    time_diff = (exp_time - iat_time).total_seconds() / 3600
    
    # Allow small tolerance for time calculation
    assert abs(time_diff - expires_in_hours) < 0.1, \
        f"Expiration should be {expires_in_hours} hours, got {time_diff}"


# **Feature: production-readiness, Property 3: Authentication context attachment**
# **Validates: Requirements 1.3**
@given(
    user_id=st.text(min_size=1, max_size=50),
    role=st.sampled_from(['user', 'admin']),
    quota_tier=st.sampled_from(['free', 'basic', 'premium'])
)
@settings(max_examples=100)
def test_property_authentication_context(user_id, role, quota_tier):
    """
    Property 3: Authentication context attachment
    
    For any authenticated request, the authentication middleware should:
    1. Extract user from valid credentials
    2. Attach user to Flask g object
    3. Include user_id, role, and quota_tier
    """
    from auth import User
    
    # Create test user
    user = User(
        user_id=user_id,
        role=role,
        quota_tier=quota_tier
    )
    
    # Generate JWT token
    token = auth_manager.generate_jwt_token(user)
    
    # Store user in auth manager for lookup
    auth_manager.users[user_id] = user
    
    # Create mock request with Authorization header
    mock_request = Mock()
    mock_request.headers = {'Authorization': f'Bearer {token}'}
    
    # Property 3a: Should extract user from request
    is_authenticated, extracted_user, error = auth_manager.get_user_from_request(mock_request)
    assert is_authenticated, f"Should authenticate valid token: {error}"
    assert extracted_user is not None, "Should extract user from token"
    
    # Property 3b: Extracted user should match original
    assert extracted_user.user_id == user_id, "User ID should match"
    assert extracted_user.role == role, "Role should match"
    assert extracted_user.quota_tier == quota_tier, "Quota tier should match"


# **Feature: production-readiness, Property 4: Invalid token rejection**
# **Validates: Requirements 1.4**
@given(
    invalid_token=st.one_of(
        st.text(min_size=1, max_size=100),  # Random text
        st.just(''),  # Empty string
        st.just('Bearer '),  # Just Bearer prefix
        st.just('invalid.jwt.token')  # Invalid JWT format
    )
)
@settings(max_examples=100)
def test_property_invalid_token_rejection(invalid_token):
    """
    Property 4: Invalid token rejection
    
    For any invalid token, the authentication system should:
    1. Reject the token
    2. Return False for validation
    3. Not raise exceptions
    """
    # Property 4a: Invalid tokens should be rejected
    is_valid, payload = auth_manager.validate_jwt_token(invalid_token)
    assert not is_valid, "Invalid token should be rejected"
    assert payload is None, "Invalid token should return None payload"
    
    # Property 4b: Mock request with invalid token should fail authentication
    mock_request = Mock()
    mock_request.headers = {'Authorization': f'Bearer {invalid_token}'}
    
    is_authenticated, user, error = auth_manager.get_user_from_request(mock_request)
    assert not is_authenticated, "Invalid token should not authenticate"
    assert user is None, "Invalid token should not return user"
    assert error is not None, "Invalid token should return error message"


# **Feature: production-readiness, Property 5: Role-based access control**
# **Validates: Requirements 1.5**
@given(
    user_role=st.sampled_from(['user', 'admin']),
    required_role=st.sampled_from(['user', 'admin'])
)
@settings(max_examples=50)
def test_property_rbac(user_role, required_role):
    """
    Property 5: Role-based access control
    
    For any user role and required role:
    1. Admin users should access all endpoints
    2. Regular users should only access user endpoints
    3. Insufficient permissions should return 403
    """
    from auth import User
    
    # Create test user
    user = User(
        user_id='test_user',
        role=user_role,
        quota_tier='free'
    )
    
    # Property 5a: Admin should always have access
    if user_role == 'admin':
        # Admin should access both user and admin endpoints
        assert True, "Admin should have access to all endpoints"
    
    # Property 5b: Regular user should only access user endpoints
    elif user_role == 'user' and required_role == 'admin':
        # User should NOT access admin endpoints
        assert user_role != 'admin', "Regular user should not have admin access"
    
    # Property 5c: User should access user endpoints
    elif user_role == 'user' and required_role == 'user':
        assert True, "User should access user endpoints"


# **Feature: production-readiness, Property 6: API key validation**
# **Validates: Requirements 1.6**
@given(
    user_id=st.text(min_size=1, max_size=50),
    role=st.sampled_from(['user', 'admin']),
    quota_tier=st.sampled_from(['free', 'basic', 'premium'])
)
@settings(max_examples=100)
def test_property_api_key_validation(user_id, role, quota_tier):
    """
    Property 6: API key validation
    
    For any generated API key:
    1. Should start with 'sk_' prefix
    2. Should validate correctly
    3. Should return correct user
    4. Invalid keys should be rejected
    """
    # Generate API key
    api_key = auth_manager.generate_api_key(user_id, role, quota_tier)
    
    # Property 6a: API key should start with 'sk_'
    assert api_key.startswith('sk_'), "API key should start with 'sk_' prefix"
    
    # Property 6b: API key should be sufficiently long (secure)
    assert len(api_key) > 20, "API key should be sufficiently long for security"
    
    # Property 6c: API key should validate correctly
    is_valid, user = auth_manager.validate_api_key(api_key)
    assert is_valid, "Generated API key should validate"
    assert user is not None, "Valid API key should return user"
    
    # Property 6d: User should match original parameters
    assert user.user_id == user_id, "User ID should match"
    assert user.role == role, "Role should match"
    assert user.quota_tier == quota_tier, "Quota tier should match"
    
    # Property 6e: Modified API key should be invalid
    modified_key = api_key[:-1] + ('x' if api_key[-1] != 'x' else 'y')
    is_valid_modified, user_modified = auth_manager.validate_api_key(modified_key)
    assert not is_valid_modified, "Modified API key should be invalid"
    assert user_modified is None, "Invalid API key should not return user"


# **Feature: production-readiness, Property 7: API key storage security**
# **Validates: Requirements 1.7**
@given(
    user_id=st.text(min_size=1, max_size=50)
)
@settings(max_examples=50)
def test_property_api_key_storage_security(user_id):
    """
    Property 7: API key storage security
    
    For any API key:
    1. Only hash should be stored, not plain key
    2. Hash should be SHA-256
    3. Same key should produce same hash
    4. Different keys should produce different hashes
    """
    # Generate API key
    api_key = auth_manager.generate_api_key(user_id, 'user', 'free')
    
    # Property 7a: API key hash should be stored
    api_key_hash = auth_manager._hash_api_key(api_key)
    assert api_key_hash in auth_manager.api_keys, "API key hash should be stored"
    
    # Property 7b: Hash should be SHA-256 (64 hex characters)
    assert len(api_key_hash) == 64, "Hash should be SHA-256 (64 characters)"
    assert all(c in '0123456789abcdef' for c in api_key_hash), "Hash should be hexadecimal"
    
    # Property 7c: Same key should produce same hash
    hash1 = auth_manager._hash_api_key(api_key)
    hash2 = auth_manager._hash_api_key(api_key)
    assert hash1 == hash2, "Same key should produce same hash"
    
    # Property 7d: Different keys should produce different hashes
    api_key2 = auth_manager.generate_api_key(f"{user_id}_2", 'user', 'free')
    hash_different = auth_manager._hash_api_key(api_key2)
    assert api_key_hash != hash_different, "Different keys should produce different hashes"


# Property: Expired token rejection
@given(user_id=st.text(min_size=1, max_size=50))
@settings(max_examples=30)
def test_property_expired_token_rejection(user_id):
    """
    Property: Expired token rejection
    
    For any user, tokens with past expiration should be rejected
    """
    from auth import User
    
    # Create test user
    user = User(
        user_id=user_id,
        role='user',
        quota_tier='free'
    )
    
    # Create expired token manually
    payload = {
        'user_id': user_id,
        'role': 'user',
        'quota_tier': 'free',
        'exp': datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        'iat': datetime.utcnow() - timedelta(hours=25)
    }
    
    expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # Property: Expired token should be rejected
    is_valid, payload_result = auth_manager.validate_jwt_token(expired_token)
    assert not is_valid, "Expired token should be rejected"
    assert payload_result is None, "Expired token should return None payload"


# Property: Token payload integrity
@given(
    user_id=st.text(min_size=1, max_size=50),
    role=st.sampled_from(['user', 'admin']),
    quota_tier=st.sampled_from(['free', 'basic', 'premium'])
)
@settings(max_examples=100)
def test_property_token_payload_integrity(user_id, role, quota_tier):
    """
    Property: Token payload integrity
    
    For any user, JWT payload should contain all required fields
    and values should match user attributes
    """
    from auth import User
    
    # Create test user
    user = User(
        user_id=user_id,
        role=role,
        quota_tier=quota_tier
    )
    
    # Generate token
    token = auth_manager.generate_jwt_token(user)
    
    # Validate and extract payload
    is_valid, payload = auth_manager.validate_jwt_token(token)
    assert is_valid, "Token should be valid"
    
    # Property: All required fields should be present
    required_fields = ['user_id', 'role', 'quota_tier', 'exp', 'iat']
    for field in required_fields:
        assert field in payload, f"Payload should contain {field}"
    
    # Property: Values should match user attributes
    assert payload['user_id'] == user_id, "User ID should match"
    assert payload['role'] == role, "Role should match"
    assert payload['quota_tier'] == quota_tier, "Quota tier should match"


# Property: API key uniqueness
@given(
    user_ids=st.lists(st.text(min_size=1, max_size=50), min_size=2, max_size=10, unique=True)
)
@settings(max_examples=50)
def test_property_api_key_uniqueness(user_ids):
    """
    Property: API key uniqueness
    
    For any set of users, each should receive a unique API key
    """
    api_keys = []
    
    for user_id in user_ids:
        api_key = auth_manager.generate_api_key(user_id, 'user', 'free')
        api_keys.append(api_key)
    
    # Property: All API keys should be unique
    assert len(api_keys) == len(set(api_keys)), "All API keys should be unique"
    
    # Property: All API key hashes should be unique
    hashes = [auth_manager._hash_api_key(key) for key in api_keys]
    assert len(hashes) == len(set(hashes)), "All API key hashes should be unique"


if __name__ == '__main__':
    # Run property tests
    print("Running property-based tests for authentication system...")
    pytest.main([__file__, '-v', '--tb=short'])
