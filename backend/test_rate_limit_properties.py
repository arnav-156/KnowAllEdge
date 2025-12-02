"""
Property-Based Tests for Rate Limiting
Tests Properties 36 and 37 from design document
"""

import pytest
import time
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, g

from rate_limiter import (
    RateLimiter,
    RATE_LIMIT_TIERS,
    rate_limit,
    get_rate_limiter
)


# Test fixtures
@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def rate_limiter():
    """Create rate limiter instance for testing"""
    return RateLimiter(redis_client=None)  # Use in-memory for tests


@pytest.fixture
def mock_request():
    """Create mock Flask request"""
    mock_req = Mock()
    mock_req.headers = {}
    mock_req.remote_addr = '127.0.0.1'
    return mock_req


# Strategy for generating tier names
tier_strategy = st.sampled_from(['limited', 'free', 'basic', 'premium', 'unlimited'])


# Strategy for generating user IDs
user_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
    min_size=8,
    max_size=36
)


class TestRateLimitingProperties:
    """
    Property-based tests for rate limiting system
    
    **Feature: production-readiness, Property 36: Tier-based rate limiting**
    **Feature: production-readiness, Property 37: Rate limit response format**
    """
    
    @given(
        tier=tier_strategy,
        num_requests=st.integers(min_value=1, max_value=200)
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_36_tier_based_rate_limiting(self, tier, num_requests, rate_limiter, app, mock_request):
        """
        Property 36: Tier-based rate limiting
        
        For any user tier, API requests should be rate limited according to 
        tier-specific limits (limited, free, basic, premium, unlimited)
        
        **Validates: Requirements 9.1**
        """
        tier_config = RATE_LIMIT_TIERS[tier]
        
        with app.test_request_context():
            # Mock the request object
            with patch('rate_limiter.request', mock_request):
                # Mock g.current_user to set tier
                g.current_user = {
                    'user_id': 'test_user_123',
                    'quota_tier': tier
                }
                
                # Make requests up to the minute limit
                allowed_count = 0
                denied_count = 0
                
                for i in range(min(num_requests, tier_config.requests_per_minute + 10)):
                    is_allowed, error_response = rate_limiter.check_rate_limit()
                    
                    if is_allowed:
                        allowed_count += 1
                    else:
                        denied_count += 1
                
                # Verify tier-based limiting
                # Allowed count should not exceed tier limit
                assert allowed_count <= tier_config.requests_per_minute, \
                    f"Tier {tier}: allowed {allowed_count} requests, limit is {tier_config.requests_per_minute}"
                
                # If we made more requests than the limit, some should be denied
                if num_requests > tier_config.requests_per_minute:
                    assert denied_count > 0, \
                        f"Tier {tier}: expected denials when exceeding limit of {tier_config.requests_per_minute}"
    
    @given(
        tier=tier_strategy,
        user_id=user_id_strategy
    )
    @settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_37_rate_limit_response_format(self, tier, user_id, rate_limiter, app, mock_request):
        """
        Property 37: Rate limit response format
        
        For any rate limit exceeded, the response should be HTTP 429 with 
        Retry-After header indicating seconds to wait
        
        **Validates: Requirements 9.1, 9.2**
        """
        tier_config = RATE_LIMIT_TIERS[tier]
        
        with app.test_request_context():
            # Mock the request object
            with patch('rate_limiter.request', mock_request):
                # Mock g.current_user to set tier
                g.current_user = {
                    'user_id': user_id,
                    'quota_tier': tier
                }
                
                # Exhaust the rate limit
                for i in range(tier_config.requests_per_minute + 1):
                    is_allowed, error_response = rate_limiter.check_rate_limit()
                
                # The last request should be denied
                assert not is_allowed, "Expected rate limit to be exceeded"
                assert error_response is not None, "Expected error response when rate limited"
                
                # Verify response format (Requirement 9.2)
                assert 'error' in error_response, "Error response must contain 'error' field"
                assert error_response['error'] == 'rate_limit_exceeded', \
                    "Error field must be 'rate_limit_exceeded'"
                
                assert 'message' in error_response, "Error response must contain 'message' field"
                assert isinstance(error_response['message'], str), "Message must be a string"
                
                assert 'tier' in error_response, "Error response must contain 'tier' field"
                assert error_response['tier'] == tier, f"Tier should be {tier}"
                
                assert 'limit' in error_response, "Error response must contain 'limit' field"
                assert isinstance(error_response['limit'], int), "Limit must be an integer"
                
                assert 'window' in error_response, "Error response must contain 'window' field"
                assert error_response['window'] in ['minute', 'hour', 'day'], \
                    "Window must be 'minute', 'hour', or 'day'"
                
                # Most important: Retry-After header (Requirement 9.2)
                assert 'retry_after' in error_response, \
                    "Error response must contain 'retry_after' field for Retry-After header"
                assert isinstance(error_response['retry_after'], int), \
                    "retry_after must be an integer (seconds)"
                assert error_response['retry_after'] > 0, \
                    "retry_after must be positive"
                assert error_response['retry_after'] <= 86400, \
                    "retry_after should not exceed 24 hours"
    
    @given(
        tier1=tier_strategy,
        tier2=tier_strategy
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tier_limits_are_different(self, tier1, tier2, app, mock_request):
        """
        Verify that different tiers have different limits
        (except when comparing same tier)
        """
        assume(tier1 != tier2)  # Only test different tiers
        
        tier1_config = RATE_LIMIT_TIERS[tier1]
        tier2_config = RATE_LIMIT_TIERS[tier2]
        
        # Higher tiers should have higher or equal limits
        tier_order = ['limited', 'free', 'basic', 'premium', 'unlimited']
        tier1_index = tier_order.index(tier1)
        tier2_index = tier_order.index(tier2)
        
        if tier1_index < tier2_index:
            # tier1 is lower, so tier2 should have higher limits
            assert tier2_config.requests_per_minute >= tier1_config.requests_per_minute, \
                f"{tier2} should have >= limits than {tier1}"
        elif tier1_index > tier2_index:
            # tier1 is higher, so tier1 should have higher limits
            assert tier1_config.requests_per_minute >= tier2_config.requests_per_minute, \
                f"{tier1} should have >= limits than {tier2}"
    
    @given(
        tier=tier_strategy,
        num_users=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limits_are_per_user(self, tier, num_users, app, mock_request):
        """
        Verify that rate limits are applied per user, not globally
        """
        tier_config = RATE_LIMIT_TIERS[tier]
        rate_limiter = RateLimiter(redis_client=None)
        
        with app.test_request_context():
            with patch('rate_limiter.request', mock_request):
                # Each user should be able to make requests up to their limit
                for user_num in range(num_users):
                    g.current_user = {
                        'user_id': f'user_{user_num}',
                        'quota_tier': tier
                    }
                    
                    # Each user should be allowed at least one request
                    is_allowed, error_response = rate_limiter.check_rate_limit()
                    assert is_allowed, \
                        f"User {user_num} should be allowed at least one request"
    
    def test_rate_limit_decorator_returns_429(self, app):
        """
        Test that @rate_limit decorator returns HTTP 429 when limit exceeded
        """
        # Create a test route with rate limiting
        @app.route('/test')
        @rate_limit
        def test_route():
            return {'success': True}
        
        with app.test_client() as client:
            # Mock the rate limiter to always deny
            with patch('rate_limiter.get_rate_limiter') as mock_get_limiter:
                mock_limiter = Mock()
                mock_limiter.check_rate_limit.return_value = (False, {
                    'error': 'rate_limit_exceeded',
                    'message': 'Too many requests',
                    'tier': 'free',
                    'limit': 10,
                    'window': 'minute',
                    'retry_after': 60
                })
                mock_get_limiter.return_value = mock_limiter
                
                # Make request
                response = client.get('/test')
                
                # Verify 429 status code
                assert response.status_code == 429, \
                    "Rate limited requests should return HTTP 429"
                
                # Verify Retry-After header is present
                assert 'Retry-After' in response.headers, \
                    "Rate limited responses must include Retry-After header"
                
                # Verify Retry-After value
                retry_after = response.headers.get('Retry-After')
                assert retry_after == '60', \
                    f"Retry-After should be '60', got '{retry_after}'"
    
    @given(
        tier=tier_strategy
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_rate_limit_status_endpoint(self, tier, rate_limiter, app, mock_request):
        """
        Test that get_rate_limit_status returns correct information
        """
        tier_config = RATE_LIMIT_TIERS[tier]
        
        with app.test_request_context():
            with patch('rate_limiter.request', mock_request):
                g.current_user = {
                    'user_id': 'test_user',
                    'quota_tier': tier
                }
                
                # Get initial status
                status = rate_limiter.get_rate_limit_status()
                
                # Verify structure
                assert 'tier' in status
                assert status['tier'] == tier
                
                assert 'limits' in status
                assert 'minute' in status['limits']
                assert 'hour' in status['limits']
                assert 'day' in status['limits']
                
                # Verify minute limits
                minute_info = status['limits']['minute']
                assert minute_info['limit'] == tier_config.requests_per_minute
                assert minute_info['remaining'] <= tier_config.requests_per_minute
                assert minute_info['used'] >= 0
                assert minute_info['remaining'] + minute_info['used'] == tier_config.requests_per_minute


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
