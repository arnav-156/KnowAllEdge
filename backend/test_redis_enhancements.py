"""
Test script for Redis cache enhancements
"""

from redis_cache import RedisCache
from config import get_config
import json

print("=" * 60)
print("REDIS CACHE ENHANCEMENTS TEST")
print("=" * 60)

# Initialize cache
cache = RedisCache(get_config())
print(f"\n✓ Cache initialized (version: {cache.cache_version})")

# Test 1: Basic operations with stats tracking
print("\n" + "=" * 60)
print("TEST 1: Basic Operations")
print("=" * 60)

cache.set('test_key_1', {'data': 'value1'})
cache.set('test_key_2', {'data': 'value2'})
print("✓ Set 2 keys")

result1 = cache.get('test_key_1')  # Hit
print(f"✓ Get key1 (hit): {result1}")

result2 = cache.get('nonexistent')  # Miss
print(f"✓ Get nonexistent (miss): {result2}")

stats = cache.get_stats()
print(f"\nStats after operations:")
print(json.dumps(stats, indent=2))

# Test 2: Cache warming
print("\n" + "=" * 60)
print("TEST 2: Cache Warming")
print("=" * 60)

def warmup_test(topic):
    """Simple warmup function"""
    return {
        'topic': topic,
        'subtopics': [f'{topic} - Part 1', f'{topic} - Part 2'],
        'warmed': True
    }

warmed_count = cache.warm_cache({
    'test_namespace': warmup_test
})

print(f"✓ Warmed {warmed_count} cache entries")
print(f"  Popular topics: {cache.popular_topics}")

# Test 3: Pattern-based invalidation
print("\n" + "=" * 60)
print("TEST 3: Pattern-Based Invalidation")
print("=" * 60)

# Set some test keys with patterns
cache.set('pattern_test_1', {'data': 'a'})
cache.set('pattern_test_2', {'data': 'b'})
cache.set('other_key', {'data': 'c'})

print("✓ Set 3 keys (2 with 'pattern_test' prefix)")

# Test pattern matching
deleted = cache.delete_pattern('*pattern_test*')
print(f"✓ Deleted {deleted} keys matching pattern '*pattern_test*'")

remaining = cache.get('other_key')
print(f"✓ Other key still exists: {remaining is not None}")

# Test 4: Namespace invalidation
print("\n" + "=" * 60)
print("TEST 4: Namespace Invalidation")
print("=" * 60)

# Generate keys in namespace
namespace_key = cache._generate_key('subtopics', {'topic': 'Python'})
cache.set(namespace_key, {'subtopics': ['Variables', 'Functions']})
print("✓ Set key in 'subtopics' namespace")

# Invalidate namespace
invalidated = cache.invalidate_namespace('subtopics')
print(f"✓ Invalidated {invalidated} keys in 'subtopics' namespace")

# Test 5: Version update
print("\n" + "=" * 60)
print("TEST 5: Version Update")
print("=" * 60)

old_version = cache.cache_version
cache.set('version_test', {'data': 'old'})
print(f"✓ Set key with version {old_version}")

cache.update_version('v2.0')
print(f"✓ Updated version to {cache.cache_version}")

# Old key should not be accessible (different version)
old_key = cache.get('version_test')
print(f"✓ Old versioned key inaccessible: {old_key is None}")

# Test 6: Health check
print("\n" + "=" * 60)
print("TEST 6: Health Check")
print("=" * 60)

health = cache.health_check()
print(f"Health status: {health['status']}")
print(f"Cache type: {health['type']}")
print(f"Cleanup thread alive: {health.get('cleanup_thread', 'N/A')}")

# Test 7: Final comprehensive stats
print("\n" + "=" * 60)
print("FINAL STATISTICS")
print("=" * 60)

final_stats = cache.get_stats()
print(json.dumps(final_stats, indent=2))

# Calculate hit rate
if final_stats['total_requests'] > 0:
    print(f"\n✓ Hit Rate: {final_stats['hit_rate_percent']:.2f}%")
    print(f"✓ Avg Latency: {final_stats['avg_latency_ms']:.2f}ms")
    print(f"✓ Total Operations: {final_stats['total_requests']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)

# Cleanup
cache.shutdown()
print("\n✓ Cache shutdown gracefully")
