"""
Standalone runner for anomaly detection property tests
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
from test_anomaly_properties import (
    test_property_35_anomaly_detection,
    test_z_score_detection_consistency,
    test_window_size_respected,
    test_iqr_detection,
    test_minimum_samples_requirement,
    test_anomaly_history_tracking,
    test_multiple_detection_methods,
    test_metric_anomaly_monitor_integration
)

print("=" * 70)
print("RUNNING ANOMALY DETECTION PROPERTY TESTS")
print("=" * 70)

print("\n1. Testing Property 35: Anomaly Detection")
print("-" * 70)
try:
    test_property_35_anomaly_detection()
    print("✅ Property 35 test PASSED")
except Exception as e:
    print(f"❌ Property 35 test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n2. Testing Z-Score Detection Consistency")
print("-" * 70)
try:
    test_z_score_detection_consistency()
    print("✅ Z-score detection test PASSED")
except Exception as e:
    print(f"❌ Z-score detection test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing Window Size Respected")
print("-" * 70)
try:
    test_window_size_respected()
    print("✅ Window size test PASSED")
except Exception as e:
    print(f"❌ Window size test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing IQR Detection")
print("-" * 70)
try:
    test_iqr_detection()
    print("✅ IQR detection test PASSED")
except Exception as e:
    print(f"❌ IQR detection test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n5. Testing Minimum Samples Requirement")
print("-" * 70)
try:
    test_minimum_samples_requirement()
    print("✅ Minimum samples test PASSED")
except Exception as e:
    print(f"❌ Minimum samples test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n6. Testing Anomaly History Tracking")
print("-" * 70)
try:
    test_anomaly_history_tracking()
    print("✅ Anomaly history test PASSED")
except Exception as e:
    print(f"❌ Anomaly history test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n7. Testing Multiple Detection Methods")
print("-" * 70)
try:
    test_multiple_detection_methods()
    print("✅ Multiple detection methods test PASSED")
except Exception as e:
    print(f"❌ Multiple detection methods test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Testing Metric Anomaly Monitor Integration")
print("-" * 70)
try:
    test_metric_anomaly_monitor_integration()
    print("✅ Monitor integration test PASSED")
except Exception as e:
    print(f"❌ Monitor integration test FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("ANOMALY DETECTION PROPERTY TESTS COMPLETE")
print("=" * 70)
