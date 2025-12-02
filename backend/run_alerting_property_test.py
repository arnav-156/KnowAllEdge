"""
Standalone runner for alerting property tests
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
from test_alerting_properties import (
    test_property_33_error_rate_alerting,
    test_property_34_performance_alerting,
    test_resource_alerting,
    test_alert_deduplication,
    test_alert_rate_limiting,
    test_threshold_configuration,
    test_alert_stats_accuracy,
    test_multiple_alert_types_independent
)

print("=" * 70)
print("RUNNING ALERTING PROPERTY TESTS")
print("=" * 70)

print("\n1. Testing Property 33: Error Rate Alerting")
print("-" * 70)
try:
    test_property_33_error_rate_alerting()
    print("✅ Property 33 test PASSED")
except Exception as e:
    print(f"❌ Property 33 test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Property 34: Performance Alerting")
print("-" * 70)
try:
    test_property_34_performance_alerting()
    print("✅ Property 34 test PASSED")
except Exception as e:
    print(f"❌ Property 34 test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing Resource Alerting")
print("-" * 70)
try:
    test_resource_alerting()
    print("✅ Resource alerting test PASSED")
except Exception as e:
    print(f"❌ Resource alerting test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing Alert Deduplication")
print("-" * 70)
try:
    test_alert_deduplication()
    print("✅ Alert deduplication test PASSED")
except Exception as e:
    print(f"❌ Alert deduplication test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing Alert Rate Limiting")
print("-" * 70)
try:
    test_alert_rate_limiting()
    print("✅ Alert rate limiting test PASSED")
except Exception as e:
    print(f"❌ Alert rate limiting test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Testing Threshold Configuration")
print("-" * 70)
try:
    test_threshold_configuration()
    print("✅ Threshold configuration test PASSED")
except Exception as e:
    print(f"❌ Threshold configuration test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n7. Testing Alert Stats Accuracy")
print("-" * 70)
try:
    test_alert_stats_accuracy()
    print("✅ Alert stats accuracy test PASSED")
except Exception as e:
    print(f"❌ Alert stats accuracy test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Testing Multiple Alert Types Independence")
print("-" * 70)
try:
    test_multiple_alert_types_independent()
    print("✅ Multiple alert types test PASSED")
except Exception as e:
    print(f"❌ Multiple alert types test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ALERTING PROPERTY TESTS COMPLETE")
print("=" * 70)
