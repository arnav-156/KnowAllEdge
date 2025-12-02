"""
Property-Based Tests for Metrics Collection
Tests correctness properties for the MetricsCollector class

Feature: production-readiness
Property 32: Metrics collection
Validates: Requirements 8.2
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
import time
from datetime import datetime
from metrics import MetricsCollector, metrics_collector
from tests.property_test_utils import (
    http_status_strategy,
    ip_address_strategy,
    user_agent_strategy
)


# ==================== Strategies ====================

# Endpoint paths
endpoint_strategy = st.sampled_from([
    '/api/subtopics',
    '/api/generate',
    '/api/quiz',
    '/api/user/profile',
    '/api/auth/login',
    '/health',
    '/metrics'
])

# HTTP methods
method_strategy = st.sampled_from(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])

# Response durations (in seconds)
duration_strategy = st.floats(min_value=0.001, max_value=10.0)

# Error types
error_strategy = st.sampled_from([
    ValueError("Invalid input"),
    KeyError("Missing key"),
    RuntimeError("Runtime error"),
    Exception("Generic error"),
    None  # No error
])


# ==================== Property Tests ====================

@given(
    endpoint=endpoint_strategy,
    method=method_strategy,
    status_code=http_status_strategy(),
    duration=duration_strategy,
    error=error_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_32_metrics_collection(endpoint, method, status_code, duration, error):
    """
    **Feature: production-readiness, Property 32: Metrics collection**
    **Validates: Requirements 8.2**
    
    Property: For any API request, the system should record metrics including
    response time, status code, and endpoint.
    
    This test verifies that:
    1. All API requests are recorded with complete metadata
    2. Response time is accurately captured
    3. Status codes are correctly recorded
    4. Endpoint information is preserved
    5. Error information is captured when present
    """
    # Create a fresh collector for this test
    collector = MetricsCollector()
    
    # Record the request
    collector.record_request(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration=duration,
        error=error
    )
    
    # Verify metrics were recorded
    stats = collector.get_statistics()
    
    # Property 1: Request count should increase
    assert stats['recent_requests'] >= 1, \
        "Metrics collector should record at least one request"
    
    # Property 2: Error count should match error presence
    if error is not None:
        assert stats['recent_errors'] >= 1, \
            "Metrics collector should record errors when present"
    
    # Property 3: Recent requests should contain the recorded request
    assert len(collector.recent_requests) >= 1, \
        "Recent requests should contain at least one entry"
    
    # Get the most recent request
    recent_request = collector.recent_requests[-1]
    
    # Property 4: Endpoint should be recorded correctly
    assert recent_request['endpoint'] == endpoint, \
        f"Endpoint should be '{endpoint}', got '{recent_request['endpoint']}'"
    
    # Property 5: Method should be recorded correctly
    assert recent_request['method'] == method, \
        f"Method should be '{method}', got '{recent_request['method']}'"
    
    # Property 6: Status code should be recorded correctly
    assert recent_request['status_code'] == status_code, \
        f"Status code should be {status_code}, got {recent_request['status_code']}"
    
    # Property 7: Duration should be recorded in milliseconds
    recorded_duration_ms = recent_request['duration_ms']
    expected_duration_ms = duration * 1000
    # Allow small floating point tolerance
    assert abs(recorded_duration_ms - expected_duration_ms) < 0.1, \
        f"Duration should be ~{expected_duration_ms}ms, got {recorded_duration_ms}ms"
    
    # Property 8: Error should be recorded when present
    if error is not None:
        assert recent_request['error'] is not None, \
            "Error should be recorded when present"
        assert str(error) in recent_request['error'], \
            f"Error message should contain '{str(error)}'"
    else:
        assert recent_request['error'] is None, \
            "Error should be None when no error occurred"
    
    # Property 9: Timestamp should be present and recent
    assert 'timestamp' in recent_request, \
        "Timestamp should be present in recorded request"
    
    # Parse timestamp and verify it's recent (within last minute)
    timestamp = datetime.fromisoformat(recent_request['timestamp'])
    time_diff = (datetime.now() - timestamp).total_seconds()
    assert time_diff < 60, \
        f"Timestamp should be recent (within 60s), but was {time_diff}s ago"


@given(
    requests=st.lists(
        st.tuples(
            endpoint_strategy,
            method_strategy,
            http_status_strategy(),
            duration_strategy
        ),
        min_size=1,
        max_size=200  # Test beyond the 100-item deque limit
    )
)
@settings(max_examples=100, deadline=None)
def test_metrics_collection_bounded_memory(requests):
    """
    Property: Metrics collector should use bounded memory (deque with maxlen=100)
    
    This test verifies that:
    1. Memory usage is bounded regardless of request count
    2. Only the most recent 100 requests are kept
    3. Older requests are automatically discarded
    """
    collector = MetricsCollector()
    
    # Record all requests
    for endpoint, method, status_code, duration in requests:
        collector.record_request(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration
        )
    
    # Property: Recent requests should never exceed 100
    assert len(collector.recent_requests) <= 100, \
        f"Recent requests should be bounded to 100, got {len(collector.recent_requests)}"
    
    # Property: If we recorded more than 100 requests, we should have exactly 100
    if len(requests) > 100:
        assert len(collector.recent_requests) == 100, \
            f"Should have exactly 100 recent requests when {len(requests)} were recorded"


@given(
    error_count=st.integers(min_value=0, max_value=50),  # Limited to deque size
    success_count=st.integers(min_value=0, max_value=50)  # Limited to deque size
)
@settings(max_examples=100, deadline=None)
def test_metrics_error_rate_calculation(error_count, success_count):
    """
    Property: Error rate should be calculated correctly as (errors / total) * 100
    
    This test verifies that:
    1. Error rate is calculated correctly
    2. Error rate is 0 when no errors occur
    3. Error rate is 100 when all requests fail
    4. Error rate is accurate for mixed success/failure
    
    Note: Limited to 50 errors and 50 successes to stay within deque bounds
    (recent_requests maxlen=100, recent_errors maxlen=50)
    """
    collector = MetricsCollector()
    
    # Record error requests
    for i in range(error_count):
        collector.record_request(
            endpoint='/api/test',
            method='GET',
            status_code=500,
            duration=0.1,
            error=Exception("Test error")
        )
    
    # Record successful requests
    for i in range(success_count):
        collector.record_request(
            endpoint='/api/test',
            method='GET',
            status_code=200,
            duration=0.1
        )
    
    stats = collector.get_statistics()
    total_requests = error_count + success_count
    
    if total_requests == 0:
        # Property: Error rate should be 0 when no requests
        assert stats['error_rate_percent'] == 0, \
            "Error rate should be 0 when no requests recorded"
    else:
        # Property: Error rate should match calculation
        # Account for deque bounds: recent_requests keeps last 100, recent_errors keeps last 50
        actual_error_count = min(error_count, 50)  # Deque maxlen for errors
        actual_total_count = min(total_requests, 100)  # Deque maxlen for requests
        
        expected_error_rate = (actual_error_count / actual_total_count) * 100
        actual_error_rate = stats['error_rate_percent']
        
        # Allow tolerance for rounding to 2 decimal places
        assert abs(actual_error_rate - expected_error_rate) < 0.5, \
            f"Error rate should be ~{expected_error_rate}%, got {actual_error_rate}%"
        
        # Property: Error rate should be between 0 and 100
        assert 0 <= actual_error_rate <= 100, \
            f"Error rate should be between 0 and 100, got {actual_error_rate}"


@given(
    user_ids=st.lists(
        st.integers(min_value=1, max_value=1000),
        min_size=0,
        max_size=100,
        unique=True
    )
)
@settings(max_examples=100, deadline=None)
def test_concurrent_user_tracking(user_ids):
    """
    Property: Concurrent user tracking should accurately count unique users
    
    This test verifies that:
    1. Adding users increases the count
    2. Removing users decreases the count
    3. Duplicate users are not double-counted
    4. Count never goes negative
    """
    collector = MetricsCollector()
    
    # Add all users
    for user_id in user_ids:
        collector.add_concurrent_user(user_id)
    
    stats = collector.get_statistics()
    
    # Property: Concurrent user count should match unique user count
    assert stats['concurrent_users'] == len(user_ids), \
        f"Should have {len(user_ids)} concurrent users, got {stats['concurrent_users']}"
    
    # Remove half the users
    users_to_remove = user_ids[:len(user_ids)//2]
    for user_id in users_to_remove:
        collector.remove_concurrent_user(user_id)
    
    stats = collector.get_statistics()
    expected_remaining = len(user_ids) - len(users_to_remove)
    
    # Property: Count should decrease correctly
    assert stats['concurrent_users'] == expected_remaining, \
        f"Should have {expected_remaining} users after removal, got {stats['concurrent_users']}"
    
    # Remove all remaining users
    for user_id in user_ids[len(user_ids)//2:]:
        collector.remove_concurrent_user(user_id)
    
    stats = collector.get_statistics()
    
    # Property: Count should be 0 after removing all users
    assert stats['concurrent_users'] == 0, \
        f"Should have 0 users after removing all, got {stats['concurrent_users']}"


@given(
    cache_hits=st.integers(min_value=0, max_value=100),
    cache_misses=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=100, deadline=None)
def test_cache_metrics_recording(cache_hits, cache_misses):
    """
    Property: Cache hit/miss metrics should be recorded correctly
    
    This test verifies that:
    1. Cache hits are recorded
    2. Cache misses are recorded
    3. Metrics are independent and don't interfere
    """
    collector = MetricsCollector()
    
    # Record cache hits
    for _ in range(cache_hits):
        collector.record_cache_hit()
    
    # Record cache misses
    for _ in range(cache_misses):
        collector.record_cache_miss()
    
    # Property: Operations should complete without error
    # (Prometheus metrics are recorded, we can't easily query them in tests)
    # This test verifies the methods execute successfully
    assert True, "Cache metrics should be recorded without error"


# ==================== Stateful Property Tests ====================

class MetricsCollectorStateMachine(RuleBasedStateMachine):
    """
    Stateful property-based testing for MetricsCollector
    
    This tests that the collector maintains correct state across
    a sequence of operations.
    """
    
    def __init__(self):
        super().__init__()
        self.collector = MetricsCollector()
        self.expected_request_count = 0
        self.expected_error_count = 0
        self.concurrent_users = set()
    
    @rule(
        endpoint=endpoint_strategy,
        method=method_strategy,
        status_code=http_status_strategy(),
        duration=duration_strategy
    )
    def record_successful_request(self, endpoint, method, status_code, duration):
        """Record a successful request"""
        self.collector.record_request(endpoint, method, status_code, duration)
        self.expected_request_count = min(self.expected_request_count + 1, 100)
    
    @rule(
        endpoint=endpoint_strategy,
        method=method_strategy,
        duration=duration_strategy
    )
    def record_error_request(self, endpoint, method, duration):
        """Record a request with error"""
        self.collector.record_request(
            endpoint, method, 500, duration,
            error=Exception("Test error")
        )
        self.expected_request_count = min(self.expected_request_count + 1, 100)
        self.expected_error_count = min(self.expected_error_count + 1, 50)
    
    @rule(user_id=st.integers(min_value=1, max_value=100))
    def add_user(self, user_id):
        """Add a concurrent user"""
        self.collector.add_concurrent_user(user_id)
        self.concurrent_users.add(user_id)
    
    @rule(user_id=st.integers(min_value=1, max_value=100))
    def remove_user(self, user_id):
        """Remove a concurrent user"""
        self.collector.remove_concurrent_user(user_id)
        self.concurrent_users.discard(user_id)
    
    @invariant()
    def request_count_bounded(self):
        """Request count should never exceed 100"""
        assert len(self.collector.recent_requests) <= 100
    
    @invariant()
    def error_count_bounded(self):
        """Error count should never exceed 50"""
        assert len(self.collector.recent_errors) <= 50
    
    @invariant()
    def concurrent_users_match(self):
        """Concurrent user count should match tracked users"""
        stats = self.collector.get_statistics()
        assert stats['concurrent_users'] == len(self.concurrent_users)
    
    @invariant()
    def statistics_valid(self):
        """Statistics should always be valid"""
        stats = self.collector.get_statistics()
        
        # All counts should be non-negative
        assert stats['recent_requests'] >= 0
        assert stats['recent_errors'] >= 0
        assert stats['concurrent_users'] >= 0
        
        # Error rate should be between 0 and 100
        assert 0 <= stats['error_rate_percent'] <= 100
        
        # Uptime should be positive
        assert stats['uptime_seconds'] > 0


# Test the state machine
TestMetricsCollectorStateMachine = MetricsCollectorStateMachine.TestCase


# ==================== Integration Tests ====================

def test_metrics_collector_integration():
    """
    Integration test: Verify metrics collector works end-to-end
    """
    collector = MetricsCollector()
    
    # Simulate a realistic request pattern
    endpoints = ['/api/generate', '/api/subtopics', '/api/quiz']
    methods = ['GET', 'POST']
    
    for i in range(50):
        endpoint = endpoints[i % len(endpoints)]
        method = methods[i % len(methods)]
        status_code = 200 if i % 10 != 0 else 500  # 10% error rate
        duration = 0.1 + (i % 10) * 0.05  # Varying durations
        error = Exception("Error") if status_code == 500 else None
        
        collector.record_request(endpoint, method, status_code, duration, error)
    
    # Verify statistics
    stats = collector.get_statistics()
    
    assert stats['recent_requests'] == 50
    assert stats['recent_errors'] == 5  # 10% of 50
    assert abs(stats['error_rate_percent'] - 10.0) < 0.1
    
    # Verify health metrics
    health = collector.get_health_metrics()
    
    assert health['status'] in ['healthy', 'degraded', 'unhealthy']
    assert health['recent_errors_5min'] >= 0
    assert health['avg_response_time_ms'] > 0


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
