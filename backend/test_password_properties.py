"""
Property-Based Tests for Password Hashing

Tests password hashing correctness properties using Hypothesis
"""

import pytest
from hypothesis import given, strategies as st, settings
from password_hasher import PasswordHasher, password_hasher
import bcrypt


# **Feature: production-readiness, Property 1: Password hashing consistency**
# **Validates: Requirements 1.1**
@given(password=st.text(min_size=1, max_size=72))
@settings(max_examples=100)
def test_property_password_hashing_consistency(password):
    """
    Property 1: Password hashing consistency
    
    For any password string, when hashed using bcrypt, the resulting hash 
    should use cost factor >= 12 and verify correctly against the original password
    
    This property ensures:
    1. All passwords are hashed with secure cost factor (>= 12)
    2. Hashed passwords can be verified against original
    3. Hash format is valid bcrypt format
    """
    # Hash the password
    hashed = password_hasher.hash_password(password)
    
    # Property 1a: Hash should be a valid bcrypt hash
    assert hashed.startswith('$2'), f"Hash should start with bcrypt identifier: {hashed[:5]}"
    
    # Property 1b: Hash should use cost factor >= 12
    hash_info = password_hasher.get_hash_info(hashed)
    assert hash_info['valid'], "Hash should be valid bcrypt format"
    assert hash_info['cost_factor'] >= 12, f"Cost factor should be >= 12, got {hash_info['cost_factor']}"
    
    # Property 1c: Hash should verify correctly against original password
    is_valid = password_hasher.verify_password(password, hashed)
    assert is_valid, f"Hash should verify against original password"
    
    # Property 1d: Hash should NOT verify against different password
    if len(password) > 1:
        # Create a different password by modifying the original
        different_password = password[:-1] + ('x' if password[-1] != 'x' else 'y')
        is_invalid = password_hasher.verify_password(different_password, hashed)
        assert not is_invalid, "Hash should NOT verify against different password"


# Additional property: Hash uniqueness (same password produces different hashes due to salt)
@given(password=st.text(min_size=8, max_size=72))
@settings(max_examples=50)
def test_property_hash_uniqueness_with_salt(password):
    """
    Property: Hash uniqueness
    
    For any password, hashing it multiple times should produce different hashes
    (due to random salt), but all should verify correctly
    """
    # Hash the same password multiple times
    hash1 = password_hasher.hash_password(password)
    hash2 = password_hasher.hash_password(password)
    hash3 = password_hasher.hash_password(password)
    
    # Property: Hashes should be different (due to random salt)
    assert hash1 != hash2, "Same password should produce different hashes"
    assert hash2 != hash3, "Same password should produce different hashes"
    assert hash1 != hash3, "Same password should produce different hashes"
    
    # Property: All hashes should verify correctly
    assert password_hasher.verify_password(password, hash1)
    assert password_hasher.verify_password(password, hash2)
    assert password_hasher.verify_password(password, hash3)


# Property: Password strength validation consistency
@given(password=st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_property_password_strength_validation_consistency(password):
    """
    Property: Password strength validation consistency
    
    For any password, validation should be deterministic and consistent
    """
    # Validate the password twice
    result1 = password_hasher.validate_password_strength(password)
    result2 = password_hasher.validate_password_strength(password)
    
    # Property: Results should be identical
    assert result1['valid'] == result2['valid']
    assert result1['score'] == result2['score']
    assert result1['strength'] == result2['strength']
    assert result1['errors'] == result2['errors']


# Property: Empty password rejection
@given(empty_str=st.just('') | st.text(max_size=0))
@settings(max_examples=10)
def test_property_empty_password_rejection(empty_str):
    """
    Property: Empty password rejection
    
    For any empty string, hashing should raise ValueError
    """
    with pytest.raises(ValueError, match="Password cannot be empty"):
        password_hasher.hash_password(empty_str)


# Property: Verification with empty inputs
@given(password=st.text(min_size=1, max_size=50))
@settings(max_examples=50)
def test_property_verification_empty_inputs(password):
    """
    Property: Verification with empty inputs
    
    For any password, verification should fail gracefully with empty inputs
    """
    hashed = password_hasher.hash_password(password)
    
    # Empty password should raise ValueError
    with pytest.raises(ValueError, match="Password cannot be empty"):
        password_hasher.verify_password('', hashed)
    
    # Empty hash should raise ValueError
    with pytest.raises(ValueError, match="Hashed password cannot be empty"):
        password_hasher.verify_password(password, '')


# Property: Cost factor configuration
@given(
    password=st.text(min_size=8, max_size=50),
    cost_factor=st.integers(min_value=12, max_value=15)
)
@settings(max_examples=50)
def test_property_cost_factor_configuration(password, cost_factor):
    """
    Property: Cost factor configuration
    
    For any password and cost factor >= 12, the hasher should use the specified cost factor
    """
    # Create hasher with specific cost factor
    hasher = PasswordHasher(cost_factor=cost_factor)
    
    # Hash password
    hashed = hasher.hash_password(password)
    
    # Property: Hash should use the specified cost factor
    hash_info = hasher.get_hash_info(hashed)
    assert hash_info['cost_factor'] == cost_factor, \
        f"Expected cost factor {cost_factor}, got {hash_info['cost_factor']}"
    
    # Property: Hash should still verify correctly
    assert hasher.verify_password(password, hashed)


# Property: Minimum cost factor enforcement
@given(
    password=st.text(min_size=8, max_size=50),
    low_cost=st.integers(min_value=4, max_value=11)
)
@settings(max_examples=30)
def test_property_minimum_cost_factor_enforcement(password, low_cost):
    """
    Property: Minimum cost factor enforcement
    
    For any cost factor below 12, the hasher should enforce minimum of 12
    """
    # Create hasher with low cost factor
    hasher = PasswordHasher(cost_factor=low_cost)
    
    # Hash password
    hashed = hasher.hash_password(password)
    
    # Property: Hash should use minimum cost factor of 12
    hash_info = hasher.get_hash_info(hashed)
    assert hash_info['cost_factor'] >= 12, \
        f"Cost factor should be >= 12, got {hash_info['cost_factor']}"


# Property: Password truncation at 72 bytes
@given(password=st.text(min_size=73, max_size=200))
@settings(max_examples=30)
def test_property_password_truncation(password):
    """
    Property: Password truncation
    
    For any password longer than 72 characters, bcrypt truncates to 72 bytes
    This test ensures we handle this correctly
    """
    # Hash the long password
    hashed = password_hasher.hash_password(password)
    
    # Property: First 72 characters should verify
    truncated = password[:72]
    assert password_hasher.verify_password(truncated, hashed), \
        "First 72 characters should verify against hash"
    
    # Property: Hash should be valid
    hash_info = password_hasher.get_hash_info(hashed)
    assert hash_info['valid'], "Hash should be valid"


# Property: Hash info extraction
@given(password=st.text(min_size=8, max_size=50))
@settings(max_examples=50)
def test_property_hash_info_extraction(password):
    """
    Property: Hash info extraction
    
    For any hashed password, we should be able to extract valid hash information
    """
    hashed = password_hasher.hash_password(password)
    hash_info = password_hasher.get_hash_info(hashed)
    
    # Property: Hash info should be valid
    assert hash_info['valid'] is True
    assert 'algorithm' in hash_info
    assert 'cost_factor' in hash_info
    assert 'salt' in hash_info
    assert 'is_secure' in hash_info
    
    # Property: Algorithm should be bcrypt variant
    assert hash_info['algorithm'] in ['$2a$', '$2b$', '$2x$', '$2y$']
    
    # Property: Cost factor should match expected
    assert hash_info['cost_factor'] == password_hasher.cost_factor
    
    # Property: Should be marked as secure (cost >= 12)
    assert hash_info['is_secure'] is True


# Property: Needs rehash detection
@given(password=st.text(min_size=8, max_size=50))
@settings(max_examples=30)
def test_property_needs_rehash_detection(password):
    """
    Property: Needs rehash detection
    
    For any password hashed with lower cost factor, needs_rehash should return True
    """
    # Create hasher with cost factor 12
    hasher_low = PasswordHasher(cost_factor=12)
    hash_low = hasher_low.hash_password(password)
    
    # Create hasher with cost factor 13
    hasher_high = PasswordHasher(cost_factor=13)
    
    # Property: Hash with lower cost should need rehash
    needs_rehash = hasher_high.needs_rehash(hash_low)
    assert needs_rehash is True, "Hash with lower cost factor should need rehash"
    
    # Property: Hash with same cost should NOT need rehash
    hash_same = hasher_high.hash_password(password)
    needs_rehash_same = hasher_high.needs_rehash(hash_same)
    assert needs_rehash_same is False, "Hash with same cost factor should not need rehash"


if __name__ == '__main__':
    # Run property tests
    print("Running property-based tests for password hashing...")
    pytest.main([__file__, '-v', '--tb=short'])
