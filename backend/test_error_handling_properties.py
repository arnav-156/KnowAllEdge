"""
Property-Based Tests for Error Handling

Tests error handling properties using Hypothesis
"""

import pytest
from hypothesis import given, strategies as st, settings
from error_handler import ErrorHandler, ErrorResponse, error_handler
from datetime import datetime


# **Feature: production-readiness, Property 15: Exception handling**
# **Validates: Requirements 3.1**
@given(
    error_message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=100)
def test_property_exception_handling(error_message):
    """
    Property 15: Exception handling
    
    For any exception:
    1. Should return standardized error response
    2. Should include request_id
    3. Should return 500 status code
    4. Should include timestamp
    """
    # Create exception
    error = Exception(error_message)
    
    # Handle exception
    response, status_code = error_handler.handle_exception(error)
    
    # Property 15a: Should return 500 status code
    assert status_code == 500, "Exception should return 500 status code"
    
    # Property 15b: Response should include required fields
    assert 'error_code' in response, "Response should include error_code"
    assert 'message' in response, "Response should include message"
    assert 'request_id' in response, "Response should include request_id"
    assert 'timestamp' in response, "Response should include timestamp"
    
    # Property 15c: Error code should be INTERNAL_SERVER_ERROR
    assert response['error_code'] == 'INTERNAL_SERVER_ERROR', \
        "Error code should be INTERNAL_SERVER_ERROR"
    
    # Property 15d: Request ID should be valid UUID format
    request_id = response['request_id']
    assert len(request_id) == 36, "Request ID should be UUID format (36 characters)"
    assert request_id.count('-') == 4, "Request ID should have UUID structure"


# **Feature: production-readiness, Property 16: Validation error responses**
# **Validates: Requirements 3.2**
@given(
    errors=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10)
)
@settings(max_examples=100)
def test_property_validation_error_responses(errors):
    """
    Property 16: Validation error responses
    
    For any validation errors:
    1. Should return standardized error response
    2. Should include all validation errors
    3. Should return 400 status code
    4. Should include documentation URL
    """
    # Handle validation error
    response, status_code = error_handler.handle_validation_error(errors)
    
    # Property 16a: Should return 400 status code
    assert status_code == 400, "Validation error should return 400 status code"
    
    # Property 16b: Response should include required fields
    assert 'error_code' in response, "Response should include error_code"
    assert 'message' in response, "Response should include message"
    assert 'details' in response, "Response should include details"
    
    # Property 16c: Error code should be VALIDATION_ERROR
    assert response['error_code'] == 'VALIDATION_ERROR', \
        "Error code should be VALIDATION_ERROR"
    
    # Property 16d: Details should include all validation errors
    assert 'validation_errors' in response['details'], \
        "Details should include validation_errors"
    assert response['details']['validation_errors'] == errors, \
        "All validation errors should be included"
    
    # Property 16e: Should include documentation URL
    assert 'documentation_url' in response, "Response should include documentation_url"


# **Feature: production-readiness, Property 17: Database error handling**
# **Validates: Requirements 3.3**
@given(
    error_message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=50)
def test_property_database_error_handling(error_message):
    """
    Property 17: Database error handling
    
    For any database error:
    1. Should return standardized error response
    2. Should return 500 status code
    3. Should not expose sensitive database details
    4. Should include error type
    """
    # Create database error
    error = Exception(error_message)
    
    # Handle database error
    response, status_code = error_handler.handle_database_error(error)
    
    # Property 17a: Should return 500 status code
    assert status_code == 500, "Database error should return 500 status code"
    
    # Property 17b: Error code should be DATABASE_ERROR
    assert response['error_code'] == 'DATABASE_ERROR', \
        "Error code should be DATABASE_ERROR"
    
    # Property 17c: Should not expose sensitive details in message
    assert 'password' not in response['message'].lower(), \
        "Error message should not contain sensitive information"
    assert 'connection string' not in response['message'].lower(), \
        "Error message should not contain connection details"
    
    # Property 17d: Should include error type in details
    assert 'details' in response, "Response should include details"
    assert 'error_type' in response['details'], "Details should include error_type"


# **Feature: production-readiness, Property 20: Rate limit error responses**
# **Validates: Requirements 3.6**
@given(
    retry_after=st.integers(min_value=1, max_value=3600)
)
@settings(max_examples=100)
def test_property_rate_limit_error_responses(retry_after):
    """
    Property 20: Rate limit error responses
    
    For any rate limit error:
    1. Should return 429 status code
    2. Should include retry_after in details
    3. Should include human-readable retry time
    4. Should include error code RATE_LIMIT_EXCEEDED
    """
    # Handle rate limit error
    response, status_code = error_handler.handle_rate_limit_error(retry_after)
    
    # Property 20a: Should return 429 status code
    assert status_code == 429, "Rate limit error should return 429 status code"
    
    # Property 20b: Error code should be RATE_LIMIT_EXCEEDED
    assert response['error_code'] == 'RATE_LIMIT_EXCEEDED', \
        "Error code should be RATE_LIMIT_EXCEEDED"
    
    # Property 20c: Should include retry_after in details
    assert 'details' in response, "Response should include details"
    assert 'retry_after' in response['details'], "Details should include retry_after"
    assert response['details']['retry_after'] == retry_after, \
        "retry_after should match input"
    
    # Property 20d: Should include human-readable retry time
    assert 'retry_after_human' in response['details'], \
        "Details should include retry_after_human"
    assert 'seconds' in response['details']['retry_after_human'], \
        "Human-readable time should mention seconds"


# Property: Error response consistency
@given(
    error_message=st.text(min_size=1, max_size=100)
)
@settings(max_examples=100)
def test_property_error_response_consistency(error_message):
    """
    Property: Error response consistency
    
    For any error, handling it multiple times should produce consistent responses
    (except for request_id and timestamp which should be unique)
    """
    error = Exception(error_message)
    
    # Handle error twice
    response1, status1 = error_handler.handle_exception(error)
    response2, status2 = error_handler.handle_exception(error)
    
    # Property: Status codes should be consistent
    assert status1 == status2, "Status codes should be consistent"
    
    # Property: Error codes should be consistent
    assert response1['error_code'] == response2['error_code'], \
        "Error codes should be consistent"
    
    # Property: Messages should be consistent
    assert response1['message'] == response2['message'], \
        "Error messages should be consistent"
    
    # Property: Request IDs should be unique
    assert response1['request_id'] != response2['request_id'], \
        "Request IDs should be unique"


# Property: Request ID uniqueness
@given(
    num_requests=st.integers(min_value=2, max_value=20)
)
@settings(max_examples=50)
def test_property_request_id_uniqueness(num_requests):
    """
    Property: Request ID uniqueness
    
    For any number of errors, each should receive a unique request ID
    """
    request_ids = []
    
    for _ in range(num_requests):
        request_id = error_handler.generate_request_id()
        request_ids.append(request_id)
    
    # Property: All request IDs should be unique
    assert len(request_ids) == len(set(request_ids)), \
        "All request IDs should be unique"
    
    # Property: All request IDs should be valid UUIDs
    for request_id in request_ids:
        assert len(request_id) == 36, "Request ID should be UUID format"
        assert request_id.count('-') == 4, "Request ID should have UUID structure"


# Property: Timestamp format
@given(
    error_message=st.text(min_size=1, max_size=100)
)
@settings(max_examples=50)
def test_property_timestamp_format(error_message):
    """
    Property: Timestamp format
    
    For any error, timestamp should be in ISO 8601 format
    """
    error = Exception(error_message)
    response, _ = error_handler.handle_exception(error)
    
    # Property: Timestamp should be present
    assert 'timestamp' in response, "Response should include timestamp"
    
    # Property: Timestamp should be valid ISO 8601 format
    timestamp = response['timestamp']
    try:
        parsed_time = datetime.fromisoformat(timestamp)
        assert isinstance(parsed_time, datetime), "Timestamp should be parseable as datetime"
    except ValueError:
        pytest.fail(f"Timestamp '{timestamp}' is not valid ISO 8601 format")


# Property: Documentation URL format
@given(
    error_type=st.sampled_from(['exception', 'validation', 'database', 'rate_limit'])
)
@settings(max_examples=50)
def test_property_documentation_url_format(error_type):
    """
    Property: Documentation URL format
    
    For any error type, documentation URL should be properly formatted
    """
    # Handle different error types
    if error_type == 'exception':
        response, _ = error_handler.handle_exception(Exception("test"))
    elif error_type == 'validation':
        response, _ = error_handler.handle_validation_error(["test error"])
    elif error_type == 'database':
        response, _ = error_handler.handle_database_error(Exception("test"))
    else:  # rate_limit
        response, _ = error_handler.handle_rate_limit_error(60)
    
    # Property: Documentation URL should be present
    assert 'documentation_url' in response, "Response should include documentation_url"
    
    # Property: URL should start with base URL
    doc_url = response['documentation_url']
    assert doc_url.startswith('https://'), "Documentation URL should be HTTPS"
    assert 'docs.KNOWALLEDGE.com' in doc_url, "Documentation URL should point to docs site"


# Property: Error message non-empty
@given(
    error_message=st.text(min_size=1, max_size=200)
)
@settings(max_examples=100)
def test_property_error_message_non_empty(error_message):
    """
    Property: Error message non-empty
    
    For any error, the error message should be non-empty and informative
    """
    error = Exception(error_message)
    response, _ = error_handler.handle_exception(error)
    
    # Property: Message should be non-empty
    assert 'message' in response, "Response should include message"
    assert len(response['message']) > 0, "Error message should be non-empty"
    assert isinstance(response['message'], str), "Error message should be a string"


if __name__ == '__main__':
    # Run property tests
    print("Running property-based tests for error handling...")
    pytest.main([__file__, '-v', '--tb=short'])
