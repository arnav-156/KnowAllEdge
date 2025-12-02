"""
Standalone runner for metrics property tests
Bypasses conftest.py to avoid config issues
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set minimal environment
os.environ['FLASK_ENV'] = 'development'

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import test functions directly
from test_metrics_properties import (
    test_property_32_metrics_collection,
    test_metrics_collection_bounded_memory,
    test_metrics_error_rate_calculation,
    test_concurrent_user_tracking,
    test_cache_metrics_recording,
    test_metrics_collector_integration
)

from hypothesis import given, settings

print("=" * 70)
print("RUNNING METRICS PROPERTY TESTS")
print("=" * 70)

print("\n1. Testing Property 32: Metrics Collection")
print("-" * 70)
try:
    # Run the property test with a few examples
    test_property_32_metrics_collection()
    print("✅ Property 32 test PASSED")
except Exception as e:
    print(f"❌ Property 32 test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Bounded Memory")
print("-" * 70)
try:
    test_metrics_collection_bounded_memory()
    print("✅ Bounded memory test PASSED")
except Exception as e:
    print(f"❌ Bounded memory test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing Error Rate Calculation")
print("-" * 70)
try:
    test_metrics_error_rate_calculation()
    print("✅ Error rate calculation test PASSED")
except Exception as e:
    print(f"❌ Error rate calculation test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing Concurrent User Tracking")
print("-" * 70)
try:
    test_concurrent_user_tracking()
    print("✅ Concurrent user tracking test PASSED")
except Exception as e:
    print(f"❌ Concurrent user tracking test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing Cache Metrics Recording")
print("-" * 70)
try:
    test_cache_metrics_recording()
    print("✅ Cache metrics recording test PASSED")
except Exception as e:
    print(f"❌ Cache metrics recording test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Testing Integration")
print("-" * 70)
try:
    test_metrics_collector_integration()
    print("✅ Integration test PASSED")
except Exception as e:
    print(f"❌ Integration test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("METRICS PROPERTY TESTS COMPLETE")
print("=" * 70)
