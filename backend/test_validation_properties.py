"""
Property-Based Tests for Input Validation

Tests input validation properties using Hypothesis
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from request_validator import RequestValidator, ValidationResult, request_validator
from unittest.mock import Mock


# **Feature: production-readiness, Property 8: Content-Type validation**
# **Validates: Requirements 2.1**
@given(
    content_type=st.one_of(
        st.just('application/json'),
        st.just('application/json; charset=utf-8'),
        st.just('text/plain'),
        st.just('text/html'),
        st.just('application/xml'),
        st.just('')
    )
)
@settings(max_examples=100)
def test_property_content_type_validation(content_type):
    """
    Property 8: Content-Type validation
    
    For any Content-Type header:
    1. 'application/json' should be accepted
    2. Other content types should be rejected
    3. Validation should return appropriate error messages
    """
    # Create mock request
    mock_request = Mock()
    mock_request.headers = {'Content-Type': content_type}
    mock_request.get_json = Mock(return_value={'test': 'data'})
    
    # Validate
    result = request_validator.validate_json(mock_request)
    
    # Property 8a: application/json should be accepted
    if 'application/json' in content_type:
        assert result.is_valid, f"application/json should be accepted: {content_type}"
        assert len(result.errors) == 0, "Valid content type should have no errors"
    else:
        # Property 8b: Other content types should be rejected
        assert not result.is_valid, f"Non-JSON content type should be rejected: {content_type}"
        assert len(result.errors) > 0, "Invalid content type should have errors"
        assert any('Content-Type' in error for error in result.errors), \
            "Error should mention Content-Type"


# **Feature: production-readiness, Property 9: Topic length validation**
# **Validates: Requirements 2.2**
@given(
    topic_length=st.integers(min_value=0, max_value=1000)
)
@settings(max_examples=100)
def test_property_topic_length_validation(topic_length):
    """
    Property 9: Topic length validation
    
    For any topic length:
    1. Topics <= MAX_TOPIC_LENGTH should be accepted
    2. Topics > MAX_TOPIC_LENGTH should be rejected
    3. Empty topics should be rejected
    """
    # Generate topic of specified length
    topic = 'a' * topic_length
    
    # Validate
    result = request_validator.validate_topic(topic)
    
    # Property 9a: Empty topics should be rejected
    if topic_length == 0:
        assert not result.is_valid, "Empty topic should be rejected"
        assert any('empty' in error.lower() or 'required' in error.lower() 
                  for error in result.errors), "Error should mention empty/required"
    
    # Property 9b: Topics within limit should be accepted
    elif topic_length <= request_validator.MAX_TOPIC_LENGTH:
        assert result.is_valid, f"Topic of length {topic_length} should be accepted"
        assert len(result.errors) == 0, "Valid topic should have no errors"
        assert result.sanitized_value == topic, "Sanitized value should match input"
    
    # Property 9c: Topics exceeding limit should be rejected
    else:
        assert not result.is_valid, f"Topic of length {topic_length} should be rejected"
        assert any('maximum length' in error.lower() for error in result.errors), \
            "Error should mention maximum length"


# **Feature: production-readiness, Property 10: Array length validation**
# **Validates: Requirements 2.3**
@given(
    array_length=st.integers(min_value=0, max_value=200)
)
@settings(max_examples=100)
def test_property_array_length_validation(array_length):
    """
    Property 10: Array length validation
    
    For any array length:
    1. Arrays <= MAX_ARRAY_LENGTH should be accepted
    2. Arrays > MAX_ARRAY_LENGTH should be rejected
    3. Empty arrays should be rejected
    """
    # Generate array of specified length
    test_array = list(range(array_length))
    
    # Validate
    result = request_validator.validate_array(test_array, "test_array")
    
    # Property 10a: Empty arrays should be rejected
    if array_length == 0:
        assert not result.is_valid, "Empty array should be rejected"
        assert any('empty' in error.lower() for error in result.errors), \
            "Error should mention empty"
    
    # Property 10b: Arrays within limit should be accepted
    elif array_length <= request_validator.MAX_ARRAY_LENGTH:
        assert result.is_valid, f"Array of length {array_length} should be accepted"
        assert len(result.errors) == 0, "Valid array should have no errors"
        assert result.sanitized_value == test_array, "Sanitized value should match input"
    
    # Property 10c: Arrays exceeding limit should be rejected
    else:
        assert not result.is_valid, f"Array of length {array_length} should be rejected"
        assert any('maximum length' in error.lower() for error in result.errors), \
            "Error should mention maximum length"


# **Feature: production-readiness, Property 11: File upload validation**
# **Validates: Requirements 2.4**
@given(
    file_extension=st.sampled_from(['txt', 'pdf', 'doc', 'docx', 'md', 'json', 
                                    'jpg', 'jpeg', 'png', 'gif', 'exe', 'sh', 'bat'])
)
@settings(max_examples=50)
def test_property_file_upload_validation(file_extension):
    """
    Property 11: File upload validation
    
    For any file extension:
    1. Allowed extensions should be accepted
    2. Dangerous extensions should be rejected
    """
    # Property 11a: Check if extension is in allowed list
    is_allowed = file_extension in request_validator.ALLOWED_FILE_EXTENSIONS
    
    # Property 11b: Dangerous extensions should not be allowed
    dangerous_extensions = {'exe', 'sh', 'bat', 'cmd', 'com', 'scr', 'vbs', 'js'}
    is_dangerous = file_extension in dangerous_extensions
    
    if is_dangerous:
        assert not is_allowed, f"Dangerous extension {file_extension} should not be allowed"
    
    if is_allowed:
        assert not is_dangerous, f"Allowed extension {file_extension} should not be dangerous"


# **Feature: production-readiness, Property 12: SQL injection prevention**
# **Validates: Requirements 2.5**
@given(
    sql_keyword=st.sampled_from(['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 
                                 'UNION', 'CREATE', 'ALTER', 'select', 'union'])
)
@settings(max_examples=50)
def test_property_sql_injection_prevention(sql_keyword):
    """
    Property 12: SQL injection prevention
    
    For any SQL keyword:
    1. Strings containing SQL keywords should be detected
    2. Validation should reject potentially malicious input
    """
    # Create string with SQL keyword
    malicious_input = f"test {sql_keyword} * FROM users"
    
    # Validate
    result = request_validator.validate_topic(malicious_input)
    
    # Property 12a: SQL keywords should be detected and rejected
    assert not result.is_valid, f"Input with SQL keyword '{sql_keyword}' should be rejected"
    assert any('dangerous' in error.lower() for error in result.errors), \
        "Error should mention dangerous content"


# **Feature: production-readiness, Property 13: XSS prevention**
# **Validates: Requirements 2.6**
@given(
    xss_pattern=st.sampled_from([
        '<script>alert("xss")</script>',
        '<img src=x onerror=alert(1)>',
        'javascript:alert(1)',
        '<iframe src="evil.com">',
        'onclick="alert(1)"',
        '<SCRIPT>alert("XSS")</SCRIPT>'
    ])
)
@settings(max_examples=50)
def test_property_xss_prevention(xss_pattern):
    """
    Property 13: XSS prevention
    
    For any XSS pattern:
    1. Dangerous patterns should be detected
    2. Validation should reject XSS attempts
    3. Sanitization should remove dangerous content
    """
    # Validate
    result = request_validator.validate_topic(xss_pattern)
    
    # Property 13a: XSS patterns should be rejected
    assert not result.is_valid, f"XSS pattern should be rejected: {xss_pattern}"
    assert any('dangerous' in error.lower() for error in result.errors), \
        "Error should mention dangerous content"
    
    # Property 13b: Sanitization should remove dangerous content
    sanitized = request_validator.sanitize_html(xss_pattern)
    assert '<script' not in sanitized.lower(), "Sanitized content should not contain script tags"
    assert 'javascript:' not in sanitized.lower(), "Sanitized content should not contain javascript:"


# **Feature: production-readiness, Property 14: Special character handling**
# **Validates: Requirements 2.7**
@given(
    text=st.text(alphabet=st.characters(blacklist_categories=('Cs', 'Cc')), min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_property_special_character_handling(text):
    """
    Property 14: Special character handling
    
    For any text with special characters:
    1. Safe characters should be accepted
    2. Dangerous characters should be rejected or escaped
    """
    # Validate with special character check
    result = request_validator.validate_special_characters(text, "test_field")
    
    # Property 14a: Check if text contains only safe characters
    has_only_safe_chars = request_validator.SAFE_CHARS_PATTERN.match(text) is not None
    
    if has_only_safe_chars:
        # Property 14b: Safe characters should be accepted
        assert result.is_valid, f"Text with only safe characters should be accepted"
    else:
        # Property 14c: Unsafe characters should be rejected
        assert not result.is_valid, f"Text with unsafe characters should be rejected"
        assert any('invalid characters' in error.lower() for error in result.errors), \
            "Error should mention invalid characters"


# Property: Validation result consistency
@given(
    topic=st.text(min_size=1, max_size=100, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126
    ))
)
@settings(max_examples=100)
def test_property_validation_consistency(topic):
    """
    Property: Validation result consistency
    
    For any input, validation should be deterministic and consistent
    """
    # Validate twice
    result1 = request_validator.validate_topic(topic)
    result2 = request_validator.validate_topic(topic)
    
    # Property: Results should be identical
    assert result1.is_valid == result2.is_valid, "Validation should be consistent"
    assert result1.errors == result2.errors, "Errors should be consistent"
    assert result1.sanitized_value == result2.sanitized_value, "Sanitized values should be consistent"


# Property: Type validation
@given(
    value=st.one_of(
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    )
)
@settings(max_examples=100)
def test_property_type_validation(value):
    """
    Property: Type validation
    
    For any non-string value, topic validation should reject it
    """
    # Validate non-string value
    result = request_validator.validate_topic(value)
    
    # Property: Non-string values should be rejected
    assert not result.is_valid, f"Non-string value should be rejected: {type(value)}"
    assert any('string' in error.lower() for error in result.errors), \
        "Error should mention string type requirement"


# Property: Whitespace handling
@given(
    topic=st.text(min_size=1, max_size=100),
    leading_spaces=st.integers(min_value=0, max_value=10),
    trailing_spaces=st.integers(min_value=0, max_value=10)
)
@settings(max_examples=100)
def test_property_whitespace_handling(topic, leading_spaces, trailing_spaces):
    """
    Property: Whitespace handling
    
    For any topic with leading/trailing whitespace, sanitization should strip it
    """
    # Add whitespace
    padded_topic = ' ' * leading_spaces + topic + ' ' * trailing_spaces
    
    # Validate
    result = request_validator.validate_topic(padded_topic)
    
    if result.is_valid:
        # Property: Sanitized value should have whitespace stripped
        assert result.sanitized_value == topic.strip(), \
            "Sanitized value should have leading/trailing whitespace stripped"


# Property: Error message clarity
@given(
    invalid_input=st.one_of(
        st.just(''),  # Empty
        st.text(min_size=501, max_size=600),  # Too long
        st.just('<script>alert(1)</script>'),  # XSS
        st.just('SELECT * FROM users')  # SQL injection
    )
)
@settings(max_examples=50)
def test_property_error_message_clarity(invalid_input):
    """
    Property: Error message clarity
    
    For any invalid input, error messages should be clear and informative
    """
    # Validate
    result = request_validator.validate_topic(invalid_input)
    
    # Property: Invalid input should be rejected
    assert not result.is_valid, "Invalid input should be rejected"
    
    # Property: Error messages should exist and be non-empty
    assert len(result.errors) > 0, "Should have error messages"
    assert all(len(error) > 0 for error in result.errors), "Error messages should be non-empty"
    assert all(isinstance(error, str) for error in result.errors), "Error messages should be strings"


# Property: Array type validation
@given(
    value=st.one_of(
        st.integers(),
        st.text(),
        st.dictionaries(st.text(), st.integers()),
        st.none()
    )
)
@settings(max_examples=50)
def test_property_array_type_validation(value):
    """
    Property: Array type validation
    
    For any non-array value, array validation should reject it
    """
    # Validate non-array value
    result = request_validator.validate_array(value, "test_field")
    
    # Property: Non-array values should be rejected
    assert not result.is_valid, f"Non-array value should be rejected: {type(value)}"
    assert any('array' in error.lower() or 'required' in error.lower() 
              for error in result.errors), "Error should mention array type requirement"


if __name__ == '__main__':
    # Run property tests
    print("Running property-based tests for input validation...")
    pytest.main([__file__, '-v', '--tb=short'])
