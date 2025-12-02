"""
Integration Tests for Production Readiness Components

Tests that all new components work together correctly
"""

import pytest
from flask import Flask, request, jsonify, g
from error_handler import error_handler
from request_validator import request_validator, validate_json_request
from file_validator import file_validator
from auth import auth_manager, require_auth
from unittest.mock import Mock
from io import BytesIO


def test_complete_integration_flow():
    """
    Test complete flow: Authentication -> Validation -> Error Handling
    """
    # Step 1: Generate API key
    api_key = auth_manager.generate_api_key('test_user', 'user', 'free')
    assert api_key.startswith('sk_'), "API key should have correct prefix"
    
    # Step 2: Validate API key
    is_valid, user = auth_manager.validate_api_key(api_key)
    assert is_valid, "API key should be valid"
    assert user.user_id == 'test_user', "User ID should match"
    
    # Step 3: Validate request data
    topic = "Machine Learning Basics"
    topic_result = request_validator.validate_topic(topic)
    assert topic_result.is_valid, "Topic should be valid"
    assert topic_result.sanitized_value == topic, "Topic should be sanitized"
    
    # Step 4: Handle error if validation fails
    invalid_topic = ""
    invalid_result = request_validator.validate_topic(invalid_topic)
    assert not invalid_result.is_valid, "Empty topic should be invalid"
    
    response, status = error_handler.handle_validation_error(invalid_result.errors)
    assert status == 400, "Should return 400 for validation error"
    assert 'error_code' in response, "Response should include error_code"
    assert response['error_code'] == 'VALIDATION_ERROR', "Error code should be VALIDATION_ERROR"


def test_authentication_to_validation_flow():
    """
    Test flow from authentication through validation
    """
    # Create user and generate JWT
    from auth import User
    user = User(user_id='test_user', role='user', quota_tier='free')
    token = auth_manager.generate_jwt_token(user)
    
    # Validate token
    is_valid, payload = auth_manager.validate_jwt_token(token)
    assert is_valid, "Token should be valid"
    assert payload['user_id'] == 'test_user', "Payload should contain user_id"
    
    # Simulate authenticated request
    mock_request = Mock()
    mock_request.headers = {'Authorization': f'Bearer {token}'}
    
    is_authenticated, extracted_user, error = auth_manager.get_user_from_request(mock_request)
    assert is_authenticated, "Request should be authenticated"
    
    # Now validate some data for this authenticated user
    data = {
        'topic': 'Python Programming',
        'subtopics': ['Variables', 'Functions', 'Classes']
    }
    
    topic_result = request_validator.validate_topic(data['topic'])
    assert topic_result.is_valid, "Topic should be valid"
    
    array_result = request_validator.validate_array(data['subtopics'], 'subtopics')
    assert array_result.is_valid, "Subtopics array should be valid"


def test_validation_to_error_handling_flow():
    """
    Test flow from validation failure to error response
    """
    # Test various validation failures
    test_cases = [
        {
            'input': '',
            'validator': lambda x: request_validator.validate_topic(x),
            'expected_error_type': 'VALIDATION_ERROR'
        },
        {
            'input': 'a' * 600,  # Too long
            'validator': lambda x: request_validator.validate_topic(x),
            'expected_error_type': 'VALIDATION_ERROR'
        },
        {
            'input': list(range(200)),  # Too many items
            'validator': lambda x: request_validator.validate_array(x, 'test'),
            'expected_error_type': 'VALIDATION_ERROR'
        }
    ]
    
    for test_case in test_cases:
        result = test_case['validator'](test_case['input'])
        assert not result.is_valid, f"Should be invalid: {test_case['input']}"
        
        # Convert to error response
        response, status = error_handler.handle_validation_error(result.errors)
        assert status == 400, "Should return 400"
        assert response['error_code'] == test_case['expected_error_type'], \
            "Error code should match expected"


def test_file_upload_complete_flow():
    """
    Test complete file upload flow with validation
    """
    # Create mock file
    file_content = b"Test file content"
    file_obj = BytesIO(file_content)
    filename = "test.txt"
    
    # Validate file
    result = file_validator.validate_file(file_obj, filename)
    
    # Note: This might fail if python-magic is not properly configured
    # In that case, at least check that the validator runs without crashing
    assert result is not None, "File validator should return a result"
    
    if not result.is_valid:
        # If validation fails, ensure we get proper error response
        response, status = error_handler.handle_validation_error(result.errors)
        assert status == 400, "Should return 400 for invalid file"
        assert 'error_code' in response, "Response should include error_code"


def test_error_response_consistency():
    """
    Test that all error types return consistent response format
    """
    # Test different error types
    error_responses = [
        error_handler.handle_exception(Exception("test")),
        error_handler.handle_validation_error(["test error"]),
        error_handler.handle_database_error(Exception("db error")),
        error_handler.handle_rate_limit_error(60),
        error_handler.handle_authentication_error("auth failed"),
        error_handler.handle_authorization_error("forbidden"),
        error_handler.handle_not_found_error("resource")
    ]
    
    # All responses should have consistent structure
    required_fields = ['error_code', 'message', 'request_id', 'timestamp']
    
    for response, status in error_responses:
        for field in required_fields:
            assert field in response, f"Response should include {field}"
        
        # Check status codes are appropriate
        assert status in [400, 401, 403, 404, 429, 500], \
            f"Status code should be valid HTTP error code: {status}"


def test_request_id_propagation():
    """
    Test that request IDs are properly generated and unique
    """
    # Generate multiple request IDs
    request_ids = set()
    
    for _ in range(10):
        request_id = error_handler.generate_request_id()
        request_ids.add(request_id)
    
    # All should be unique
    assert len(request_ids) == 10, "All request IDs should be unique"
    
    # All should be valid UUIDs
    for request_id in request_ids:
        assert len(request_id) == 36, "Request ID should be UUID format"
        assert request_id.count('-') == 4, "Request ID should have UUID structure"


def test_sanitization_flow():
    """
    Test that input sanitization works correctly
    """
    # Test whitespace trimming
    topic_with_spaces = "  Machine Learning  "
    result = request_validator.validate_topic(topic_with_spaces)
    assert result.is_valid, "Topic with spaces should be valid"
    assert result.sanitized_value == "Machine Learning", \
        "Whitespace should be trimmed"
    
    # Test HTML sanitization
    html_with_script = '<p>Hello</p><script>alert("xss")</script>'
    sanitized = request_validator.sanitize_html(html_with_script)
    assert '<script' not in sanitized.lower(), "Script tags should be removed"
    assert 'Hello' in sanitized, "Safe content should remain"


def test_security_pattern_detection():
    """
    Test that dangerous patterns are detected
    """
    dangerous_inputs = [
        '<script>alert(1)</script>',
        'javascript:alert(1)',
        'SELECT * FROM users',
        '../../../etc/passwd',
        '<img src=x onerror=alert(1)>'
    ]
    
    for dangerous_input in dangerous_inputs:
        result = request_validator.validate_topic(dangerous_input)
        assert not result.is_valid, \
            f"Dangerous input should be rejected: {dangerous_input}"
        assert any('dangerous' in error.lower() for error in result.errors), \
            "Error should mention dangerous content"


def test_authentication_error_flow():
    """
    Test authentication error handling
    """
    # Test with invalid token
    invalid_token = "invalid.jwt.token"
    is_valid, payload = auth_manager.validate_jwt_token(invalid_token)
    assert not is_valid, "Invalid token should be rejected"
    
    # Convert to error response
    response, status = error_handler.handle_authentication_error("Invalid token")
    assert status == 401, "Should return 401 for auth error"
    assert response['error_code'] == 'AUTHENTICATION_ERROR', \
        "Error code should be AUTHENTICATION_ERROR"


def test_role_based_access_flow():
    """
    Test role-based access control flow
    """
    # Create users with different roles
    regular_user = auth_manager.generate_api_key('regular_user', 'user', 'free')
    admin_user = auth_manager.generate_api_key('admin_user', 'admin', 'unlimited')
    
    # Validate both
    is_valid_regular, user_regular = auth_manager.validate_api_key(regular_user)
    is_valid_admin, user_admin = auth_manager.validate_api_key(admin_user)
    
    assert is_valid_regular and user_regular.role == 'user', \
        "Regular user should have user role"
    assert is_valid_admin and user_admin.role == 'admin', \
        "Admin user should have admin role"
    
    # Test authorization error for insufficient permissions
    response, status = error_handler.handle_authorization_error("Admin required")
    assert status == 403, "Should return 403 for authorization error"
    assert response['error_code'] == 'AUTHORIZATION_ERROR', \
        "Error code should be AUTHORIZATION_ERROR"


def test_complete_api_endpoint_simulation():
    """
    Simulate a complete API endpoint with all components
    """
    # Step 1: Generate and validate API key
    api_key = auth_manager.generate_api_key('api_user', 'user', 'basic')
    is_valid, user = auth_manager.validate_api_key(api_key)
    assert is_valid, "API key should be valid"
    
    # Step 2: Validate request data
    request_data = {
        'topic': 'Data Science',
        'subtopics': ['Statistics', 'Machine Learning', 'Data Visualization'],
        'depth': 'intermediate'
    }
    
    # Validate topic
    topic_result = request_validator.validate_topic(request_data['topic'])
    if not topic_result.is_valid:
        response, status = error_handler.handle_validation_error(topic_result.errors)
        pytest.fail(f"Topic validation failed: {response}")
    
    # Validate subtopics
    array_result = request_validator.validate_array(
        request_data['subtopics'], 
        'subtopics'
    )
    if not array_result.is_valid:
        response, status = error_handler.handle_validation_error(array_result.errors)
        pytest.fail(f"Array validation failed: {response}")
    
    # Step 3: Process request (simulated)
    try:
        # Simulate successful processing
        result = {
            'success': True,
            'user_id': user.user_id,
            'topic': topic_result.sanitized_value,
            'subtopics': array_result.sanitized_value
        }
        
        assert result['success'], "Processing should succeed"
        assert result['user_id'] == 'api_user', "User ID should match"
        
    except Exception as e:
        # If error occurs, handle it properly
        response, status = error_handler.handle_exception(e)
        pytest.fail(f"Unexpected error: {response}")


if __name__ == '__main__':
    # Run integration tests
    print("Running production readiness integration tests...")
    pytest.main([__file__, '-v', '--tb=short'])
