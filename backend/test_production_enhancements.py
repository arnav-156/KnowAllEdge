"""
Comprehensive Test Suite for Production Enhancements
Tests quota tracking, caching strategy, and deployment configurations
"""

import pytest
import time
import os
from unittest.mock import Mock, patch, MagicMock
from collections import deque

# Import modules to test
from quota_tracker import (
    QuotaTracker, QuotaConfig, RequestPriority,
    get_quota_tracker, with_quota_check
)
from cache_strategy import (
    MultiLayerCache, CacheConfig, CacheEntry,
    get_cache_strategy, with_multi_layer_cache,
    add_browser_cache_headers, add_cdn_cache_headers
)


# =============================================================================
# QUOTA TRACKER TESTS
# =============================================================================

class TestQuotaTracker:
    """Test suite for Gemini API quota tracking"""
    
    def setup_method(self):
        """Reset quota tracker before each test"""
        global _quota_tracker_instance
        _quota_tracker_instance = None
    
    def test_quota_initialization(self):
        """Test quota tracker initialization with default config"""
        config = QuotaConfig()
        tracker = QuotaTracker(config)
        
        assert tracker.config.requests_per_minute == 15
        assert tracker.config.requests_per_day == 1500
        assert tracker.config.get_safe_rpm() == 12  # 15 * 0.8
        assert tracker.config.get_safe_rpd() == 1200  # 1500 * 0.8
        assert len(tracker.queues) == 4  # One queue per priority
        print("✅ Quota tracker initialization")
    
    def test_can_make_request_success(self):
        """Test request approval when quota available"""
        tracker = QuotaTracker()
        can_proceed, reason = tracker.can_make_request(estimated_tokens=1000)
        
        assert can_proceed == True
        assert reason is None
        print("✅ Request approval with available quota")
    
    def test_rpm_limit_exceeded(self):
        """Test RPM limit enforcement"""
        config = QuotaConfig(requests_per_minute=3, rpm_safety_margin=1.0)
        tracker = QuotaTracker(config)
        
        # Fill up to limit
        for _ in range(3):
            tracker.record_request(1000)
        
        # Next request should be denied
        can_proceed, reason = tracker.can_make_request(1000)
        assert can_proceed == False
        assert "RPM limit" in reason
        print("✅ RPM limit enforcement")
    
    def test_tpm_limit_exceeded(self):
        """Test TPM (tokens per minute) limit enforcement"""
        config = QuotaConfig(
            tokens_per_minute=10000,
            tpm_safety_margin=1.0
        )
        tracker = QuotaTracker(config)
        
        # Use 8000 tokens
        tracker.record_request(8000)
        
        # Try to use 3000 more (would exceed 10000)
        can_proceed, reason = tracker.can_make_request(estimated_tokens=3000)
        assert can_proceed == False
        assert "TPM limit" in reason
        print("✅ TPM limit enforcement")
    
    def test_request_recording(self):
        """Test accurate request recording"""
        tracker = QuotaTracker()
        
        assert len(tracker.requests_minute) == 0
        tracker.record_request(1500)
        assert len(tracker.requests_minute) == 1
        assert tracker.total_requests == 1
        print("✅ Request recording")
    
    def test_sliding_window_cleanup(self):
        """Test old records are cleaned from sliding windows"""
        tracker = QuotaTracker()
        
        # Add old request (70 seconds ago)
        old_time = time.time() - 70
        tracker.requests_minute.append(old_time)
        
        # Clean old records
        tracker._clean_old_records()
        
        # Old request should be removed (outside 60s window)
        assert len(tracker.requests_minute) == 0
        print("✅ Sliding window cleanup")
    
    def test_fallback_cache(self):
        """Test fallback response caching"""
        tracker = QuotaTracker()
        cache_key = "test:endpoint:args"
        response = {"data": "test_response"}
        
        # Cache response
        tracker.cache_response(cache_key, response)
        
        # Retrieve from fallback
        cached = tracker.get_fallback_response(cache_key)
        assert cached == response
        assert tracker.fallback_used_count == 1
        print("✅ Fallback cache storage and retrieval")
    
    def test_fallback_cache_expiration(self):
        """Test fallback cache expiration"""
        config = QuotaConfig(fallback_cache_ttl=1)  # 1 second TTL
        tracker = QuotaTracker(config)
        
        cache_key = "test:expired"
        tracker.cache_response(cache_key, {"data": "test"})
        
        # Wait for expiration
        time.sleep(1.5)
        
        cached = tracker.get_fallback_response(cache_key)
        assert cached is None
        print("✅ Fallback cache expiration")
    
    def test_request_queuing(self):
        """Test request queuing when quota exceeded"""
        tracker = QuotaTracker()
        
        queued = tracker.queue_request(
            priority=RequestPriority.HIGH,
            endpoint="test_endpoint",
            estimated_tokens=1000,
            user_id="user123"
        )
        
        assert queued == True
        assert len(tracker.queues[RequestPriority.HIGH]) == 1
        assert tracker.queued_requests == 1
        print("✅ Request queuing")
    
    def test_queue_priority_order(self):
        """Test requests are dequeued in priority order"""
        tracker = QuotaTracker()
        
        # Queue requests with different priorities
        tracker.queue_request(RequestPriority.LOW, "low", 1000)
        tracker.queue_request(RequestPriority.CRITICAL, "critical", 1000)
        tracker.queue_request(RequestPriority.HIGH, "high", 1000)
        
        # Get next request (should be CRITICAL)
        next_req = tracker.get_next_request()
        assert next_req.priority == RequestPriority.CRITICAL
        assert next_req.endpoint == "critical"
        print("✅ Queue priority ordering")
    
    def test_queue_full(self):
        """Test queue size limit enforcement"""
        config = QuotaConfig(max_queue_size=5)
        tracker = QuotaTracker(config)
        
        # Fill queue to limit
        for i in range(5):
            tracker.queue_request(RequestPriority.MEDIUM, f"req{i}", 1000)
        
        # Try to queue one more
        queued = tracker.queue_request(RequestPriority.MEDIUM, "overflow", 1000)
        assert queued == False
        print("✅ Queue size limit enforcement")
    
    def test_quota_stats(self):
        """Test quota statistics reporting"""
        tracker = QuotaTracker()
        tracker.record_request(1000)
        tracker.record_request(2000)
        
        stats = tracker.get_stats()
        
        assert stats['requests']['per_minute']['current'] == 2
        assert stats['tokens']['per_minute']['current'] == 3000
        assert stats['statistics']['total_requests'] == 2
        print("✅ Quota statistics reporting")
    
    def test_singleton_pattern(self):
        """Test quota tracker singleton pattern"""
        tracker1 = get_quota_tracker()
        tracker2 = get_quota_tracker()
        
        assert tracker1 is tracker2
        print("✅ Quota tracker singleton pattern")


# =============================================================================
# CACHE STRATEGY TESTS
# =============================================================================

class TestCacheStrategy:
    """Test suite for multi-layer caching strategy"""
    
    def setup_method(self):
        """Reset cache before each test"""
        global _cache_instance
        _cache_instance = None
    
    def test_cache_initialization(self):
        """Test cache initialization with default config"""
        config = CacheConfig()
        cache = MultiLayerCache(config)
        
        assert cache.config.browser_cache_ttl == 300
        assert cache.config.cdn_cache_ttl == 1800
        assert cache.config.memory_cache_max_size == 1000
        assert len(cache.memory_cache) == 0
        print("✅ Cache initialization")
    
    def test_memory_cache_set_get(self):
        """Test memory cache storage and retrieval"""
        cache = MultiLayerCache()
        key = "test:key:123"
        value = {"data": "test_value"}
        
        cache.set_in_memory(key, value, ttl=60)
        retrieved = cache.get_from_memory(key)
        
        assert retrieved == value
        print("✅ Memory cache set/get")
    
    def test_memory_cache_expiration(self):
        """Test memory cache TTL expiration"""
        cache = MultiLayerCache()
        key = "test:expired"
        
        cache.set_in_memory(key, "value", ttl=1)
        time.sleep(1.5)
        
        retrieved = cache.get_from_memory(key)
        assert retrieved is None
        print("✅ Memory cache expiration")
    
    def test_memory_cache_lru_eviction(self):
        """Test LRU eviction when cache size exceeds limit"""
        config = CacheConfig(memory_cache_max_size=3)
        cache = MultiLayerCache(config)
        
        # Add 5 items (should evict 2 oldest)
        for i in range(5):
            cache.set_in_memory(f"key{i}", f"value{i}")
            time.sleep(0.1)  # Ensure different timestamps
        
        # Oldest items should be evicted
        assert cache.get_from_memory("key0") is None
        assert cache.get_from_memory("key1") is None
        assert cache.get_from_memory("key4") is not None
        print("✅ LRU eviction")
    
    def test_cache_key_generation(self):
        """Test cache key generation from arguments"""
        cache = MultiLayerCache()
        
        key1 = cache._generate_cache_key("prefix", "arg1", "arg2", kwarg1="val1")
        key2 = cache._generate_cache_key("prefix", "arg1", "arg2", kwarg1="val1")
        key3 = cache._generate_cache_key("prefix", "arg1", "arg2", kwarg1="val2")
        
        assert key1 == key2  # Same arguments
        assert key1 != key3  # Different kwargs
        print("✅ Cache key generation")
    
    def test_cache_promotion(self):
        """Test cache promotion (Redis hit promotes to memory)"""
        mock_redis = Mock()
        mock_redis.get.return_value = {"data": "from_redis"}
        
        cache = MultiLayerCache(redis_cache=mock_redis)
        key = "test:promotion"
        
        # Get from Redis (should promote to memory)
        value = cache.get(key)
        
        assert value == {"data": "from_redis"}
        assert cache.get_from_memory(key) == {"data": "from_redis"}
        print("✅ Cache promotion")
    
    def test_cache_invalidation(self):
        """Test cache invalidation across layers"""
        mock_redis = Mock()
        cache = MultiLayerCache(redis_cache=mock_redis)
        
        key = "test:invalidate"
        cache.set_in_memory(key, "value")
        
        # Invalidate
        cache.invalidate(key)
        
        assert cache.get_from_memory(key) is None
        mock_redis.delete.assert_called_once_with(key)
        print("✅ Cache invalidation")
    
    def test_pattern_invalidation(self):
        """Test pattern-based cache invalidation"""
        cache = MultiLayerCache()
        
        # Add keys with pattern
        cache.set_in_memory("topic:python", "value1")
        cache.set_in_memory("topic:java", "value2")
        cache.set_in_memory("user:123", "value3")
        
        # Invalidate pattern
        cache.invalidate_pattern("topic:*")
        
        assert cache.get_from_memory("topic:python") is None
        assert cache.get_from_memory("topic:java") is None
        assert cache.get_from_memory("user:123") is not None
        print("✅ Pattern invalidation")
    
    def test_popular_topic_tracking(self):
        """Test tracking of popular topics for pre-caching"""
        cache = MultiLayerCache()
        
        # Access same topic multiple times
        for _ in range(12):
            cache.track_access("python_basics")
        
        popular = cache.get_popular_topics(10)
        assert len(popular) > 0
        assert popular[0][0] == "python_basics"
        assert popular[0][1] == 12
        print("✅ Popular topic tracking")
    
    def test_cache_stats(self):
        """Test cache statistics reporting"""
        cache = MultiLayerCache()
        
        cache.set_in_memory("key1", "value1")
        cache.set_in_memory("key2", "value2")
        cache.get_from_memory("key1")  # Hit
        
        stats = cache.get_stats()
        
        assert stats['memory']['size'] == 2
        assert stats['memory']['total_hits'] == 1
        print("✅ Cache statistics")
    
    def test_browser_cache_headers(self):
        """Test browser cache header generation"""
        from flask import Flask, Response
        
        app = Flask(__name__)
        with app.app_context():
            response = Response("test")
            response = add_browser_cache_headers(response, ttl=300, public=True)
            
            assert 'Cache-Control' in response.headers
            assert 'max-age=300' in response.headers['Cache-Control']
            assert 'ETag' in response.headers
        print("✅ Browser cache headers")
    
    def test_cdn_cache_headers(self):
        """Test CDN cache header generation"""
        from flask import Flask, Response
        
        app = Flask(__name__)
        with app.app_context():
            response = Response("test")
            response = add_cdn_cache_headers(response, ttl=1800)
            
            assert 'Cache-Control' in response.headers
            assert 'CDN-Cache-Control' in response.headers
            assert 'Vary' in response.headers
        print("✅ CDN cache headers")


# =============================================================================
# RUN ALL TESTS
# =============================================================================

def run_all_tests():
    """Run all test suites"""
    print("\n" + "="*80)
    print("PRODUCTION ENHANCEMENTS TEST SUITE")
    print("="*80 + "\n")
    
    # Quota Tracker Tests
    print("📊 QUOTA TRACKER TESTS")
    print("-"*80)
    test_quota = TestQuotaTracker()
    test_quota.setup_method()
    test_quota.test_quota_initialization()
    test_quota.test_can_make_request_success()
    test_quota.test_rpm_limit_exceeded()
    test_quota.test_tpm_limit_exceeded()
    test_quota.test_request_recording()
    test_quota.test_sliding_window_cleanup()
    test_quota.test_fallback_cache()
    test_quota.test_fallback_cache_expiration()
    test_quota.test_request_queuing()
    test_quota.test_queue_priority_order()
    test_quota.test_queue_full()
    test_quota.test_quota_stats()
    test_quota.test_singleton_pattern()
    print("\n✅ QUOTA TRACKER: All tests passed (13/13)\n")
    
    # Cache Strategy Tests
    print("💾 CACHE STRATEGY TESTS")
    print("-"*80)
    test_cache = TestCacheStrategy()
    test_cache.setup_method()
    test_cache.test_cache_initialization()
    test_cache.test_memory_cache_set_get()
    test_cache.test_memory_cache_expiration()
    test_cache.test_memory_cache_lru_eviction()
    test_cache.test_cache_key_generation()
    test_cache.test_cache_promotion()
    test_cache.test_cache_invalidation()
    test_cache.test_pattern_invalidation()
    test_cache.test_popular_topic_tracking()
    test_cache.test_cache_stats()
    test_cache.test_browser_cache_headers()
    test_cache.test_cdn_cache_headers()
    print("\n✅ CACHE STRATEGY: All tests passed (12/12)\n")
    
    print("="*80)
    print("✅ ALL TESTS PASSED (25/25)")
    print("="*80)
    print("\nTest Summary:")
    print(f"  • Quota Tracker:   13 tests ✅")
    print(f"  • Cache Strategy:  12 tests ✅")
    print(f"  • Total:           25 tests ✅")
    print()


if __name__ == "__main__":
    run_all_tests()
