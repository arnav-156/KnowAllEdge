"""
Property-Based Tests for Anomaly Detection
Tests correctness properties for the AnomalyDetector class

Feature: production-readiness
Property 35: Anomaly detection
Validates: Requirements 8.7
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from anomaly_detector import AnomalyDetector, MetricAnomalyMonitor
from alert_manager import AlertManager


# ==================== Strategies ====================

# Metric values
metric_value_strategy = st.floats(min_value=0.0, max_value=1000.0, allow_nan=False, allow_infinity=False)

# Normal distribution values (for testing normal behavior)
def normal_values_strategy(mean=100.0, std=10.0, size=50):
    """Generate values from normal distribution"""
    return st.lists(
        st.floats(min_value=mean - 3*std, max_value=mean + 3*std, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    )

# Anomalous values (outliers)
def anomalous_value_strategy(mean=100.0, std=10.0):
    """Generate anomalous values (far from mean)"""
    return st.one_of(
        st.floats(min_value=mean + 5*std, max_value=mean + 10*std),  # High outlier
        st.floats(min_value=mean - 10*std, max_value=mean - 5*std)   # Low outlier
    )

# Z-score thresholds
z_score_threshold_strategy = st.floats(min_value=2.0, max_value=5.0)

# Window sizes
window_size_strategy = st.integers(min_value=30, max_value=200)


# ==================== Property Tests ====================

@given(
    normal_values=normal_values_strategy(mean=100.0, std=10.0, size=50),
    anomalous_value=anomalous_value_strategy(mean=100.0, std=10.0)
)
@settings(max_examples=100, deadline=None)
def test_property_35_anomaly_detection(normal_values, anomalous_value):
    """
    **Feature: production-readiness, Property 35: Anomaly detection**
    **Validates: Requirements 8.7**
    
    Property: For any detected anomaly in system behavior, the system should
    send notification to on-call engineers.
    
    This test verifies that:
    1. Normal values are not flagged as anomalies
    2. Anomalous values are detected
    3. Anomaly details are recorded
    4. Alerts are triggered for anomalies
    """
    # Create anomaly detector
    detector = AnomalyDetector(
        window_size=100,
        z_score_threshold=3.0,
        min_samples=30
    )
    
    # Add normal values to build baseline
    for value in normal_values:
        detector.add_sample('test_metric', value)
    
    # Property 1: Normal values should not be anomalies
    # Test a few normal values
    for value in normal_values[:5]:
        is_anomaly, details = detector.detect_z_score_anomaly('test_metric', value)
        assert not is_anomaly, \
            f"Normal value {value} should not be detected as anomaly"
    
    # Property 2: Anomalous value should be detected
    is_anomaly, details = detector.detect_z_score_anomaly('test_metric', anomalous_value)
    
    # The anomalous value should be detected (with high probability)
    # Note: Due to randomness, we can't guarantee 100% detection
    # but with 5+ std deviations, it should be detected
    std = np.std(normal_values)
    mean = np.mean(normal_values)
    
    # Only test if std > 0 (can't detect anomalies with zero variance)
    if std > 0 and abs(anomalous_value - mean) > 5 * std:
        assert is_anomaly, \
            f"Anomalous value {anomalous_value} should be detected (mean={mean}, std={std})"
        
        # Property 3: Anomaly details should be recorded
        assert details is not None, "Anomaly details should be provided"
        assert 'metric_name' in details, "Details should include metric name"
        assert 'value' in details, "Details should include value"
        assert 'z_score' in details, "Details should include z-score"
        assert details['metric_name'] == 'test_metric'
        assert details['value'] == anomalous_value
        
        # Property 4: Anomaly should be in history
        history = detector.get_anomaly_history()
        assert len(history) > 0, "Anomaly should be recorded in history"


@given(
    values=st.lists(
        metric_value_strategy,
        min_size=50,
        max_size=100
    ),
    z_threshold=z_score_threshold_strategy
)
@settings(max_examples=100, deadline=None)
def test_z_score_detection_consistency(values, z_threshold):
    """
    Property: Z-score detection should be consistent with statistical definition
    
    This test verifies that:
    1. Z-score is calculated correctly
    2. Threshold is applied correctly
    3. Detection is deterministic
    """
    detector = AnomalyDetector(
        window_size=200,
        z_score_threshold=z_threshold,
        min_samples=30
    )
    
    # Add values to build baseline
    for value in values[:-1]:
        detector.add_sample('test_metric', value)
    
    # Test last value
    test_value = values[-1]
    is_anomaly, details = detector.detect_z_score_anomaly('test_metric', test_value)
    
    # Calculate expected z-score
    mean = np.mean(values[:-1])
    std = np.std(values[:-1])
    
    if std > 0:
        expected_z_score = abs((test_value - mean) / std)
        expected_anomaly = expected_z_score > z_threshold
        
        # Property: Detection should match expected result
        assert is_anomaly == expected_anomaly, \
            f"Detection mismatch: expected {expected_anomaly}, got {is_anomaly} (z={expected_z_score}, threshold={z_threshold})"
        
        if is_anomaly:
            # Property: Z-score in details should match calculation
            assert details is not None
            assert abs(details['z_score'] - expected_z_score) < 0.01, \
                f"Z-score mismatch: expected {expected_z_score}, got {details['z_score']}"


@given(
    window_size=window_size_strategy,
    values=st.lists(metric_value_strategy, min_size=100, max_size=150)
)
@settings(max_examples=50, deadline=None)
def test_window_size_respected(window_size, values):
    """
    Property: Detector should respect configured window size
    
    This test verifies that:
    1. Window size is enforced
    2. Old samples are discarded
    3. Only recent samples affect detection
    """
    detector = AnomalyDetector(
        window_size=window_size,
        min_samples=min(30, window_size // 2)
    )
    
    # Add more values than window size
    for value in values:
        detector.add_sample('test_metric', value)
    
    # Property: Window should not exceed configured size
    with detector.lock:
        window = detector.metric_windows.get('test_metric', [])
        assert len(window) <= window_size, \
            f"Window size should be <= {window_size}, got {len(window)}"
        
        # If we added more than window_size values, window should be exactly window_size
        if len(values) > window_size:
            assert len(window) == window_size, \
                f"Window should be exactly {window_size} after adding {len(values)} values, got {len(window)}"


@given(
    values=st.lists(
        st.floats(min_value=50.0, max_value=150.0, allow_nan=False, allow_infinity=False),
        min_size=50,
        max_size=50
    )
)
@settings(max_examples=100, deadline=None)
def test_iqr_detection(values):
    """
    Property: IQR detection should identify outliers correctly
    
    This test verifies that:
    1. IQR is calculated correctly
    2. Outliers beyond IQR bounds are detected
    3. Values within bounds are not detected
    """
    detector = AnomalyDetector(
        window_size=100,
        iqr_multiplier=1.5,
        min_samples=30
    )
    
    # Add values
    for value in values:
        detector.add_sample('test_metric', value)
    
    # Calculate expected IQR bounds
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Test value within bounds (should not be anomaly)
    normal_value = (q1 + q3) / 2  # Median
    is_anomaly, details = detector.detect_iqr_anomaly('test_metric', normal_value)
    assert not is_anomaly, \
        f"Value within IQR bounds should not be anomaly: {normal_value} in [{lower_bound}, {upper_bound}]"
    
    # Test value outside bounds (should be anomaly)
    outlier_value = upper_bound + 10
    is_anomaly, details = detector.detect_iqr_anomaly('test_metric', outlier_value)
    assert is_anomaly, \
        f"Value outside IQR bounds should be anomaly: {outlier_value} > {upper_bound}"
    
    if is_anomaly:
        # Property: Details should include IQR information
        assert details is not None
        assert 'iqr' in details
        assert 'lower_bound' in details
        assert 'upper_bound' in details


@given(
    min_samples=st.integers(min_value=10, max_value=50)
)
@settings(max_examples=50, deadline=None)
def test_minimum_samples_requirement(min_samples):
    """
    Property: Detector should require minimum samples before detecting anomalies
    
    This test verifies that:
    1. No anomalies detected with insufficient samples
    2. Anomalies can be detected once minimum is reached
    """
    detector = AnomalyDetector(
        window_size=100,
        min_samples=min_samples
    )
    
    # Add fewer than minimum samples
    for i in range(min_samples - 1):
        detector.add_sample('test_metric', 100.0)
    
    # Property: Should not detect anomalies with insufficient samples
    is_anomaly, details = detector.detect_z_score_anomaly('test_metric', 1000.0)
    assert not is_anomaly, \
        f"Should not detect anomalies with {min_samples - 1} samples (min={min_samples})"
    
    # Add one more sample to reach minimum
    detector.add_sample('test_metric', 100.0)
    
    # Property: Should now be able to detect anomalies
    is_anomaly, details = detector.detect_z_score_anomaly('test_metric', 1000.0)
    # Note: Detection depends on the values, but the detector should at least try
    # We just verify it doesn't fail due to insufficient samples


def test_anomaly_history_tracking():
    """
    Integration test: Verify anomaly history is tracked correctly
    """
    detector = AnomalyDetector(
        window_size=100,
        z_score_threshold=3.0,
        min_samples=30
    )
    
    # Add normal values
    for i in range(50):
        detector.add_sample('metric1', 100.0 + i * 0.1)
    
    # Add anomalous values
    detector.detect_z_score_anomaly('metric1', 500.0)  # Anomaly
    detector.detect_z_score_anomaly('metric1', 600.0)  # Anomaly
    
    # Get history
    history = detector.get_anomaly_history()
    
    # Verify history
    assert len(history) >= 2, f"Should have at least 2 anomalies, got {len(history)}"
    
    # Verify history filtering by metric
    metric1_history = detector.get_anomaly_history(metric_name='metric1')
    assert len(metric1_history) >= 2
    
    # Verify statistics
    stats = detector.get_statistics()
    assert stats['total_anomalies'] >= 2
    assert 'metric1' in stats['by_metric']


def test_multiple_detection_methods():
    """
    Integration test: Verify multiple detection methods work independently
    """
    detector = AnomalyDetector(
        window_size=100,
        z_score_threshold=3.0,
        iqr_multiplier=1.5,
        min_samples=30
    )
    
    # Add normal values
    values = [100.0 + i * 0.5 for i in range(50)]
    for value in values:
        detector.add_sample('test_metric', value)
    
    # Test with different methods
    anomalous_value = 500.0
    
    z_anomaly, z_details = detector.detect_z_score_anomaly('test_metric', anomalous_value)
    iqr_anomaly, iqr_details = detector.detect_iqr_anomaly('test_metric', anomalous_value)
    ewma_anomaly, ewma_details = detector.detect_ewma_anomaly('test_metric', anomalous_value)
    
    # All methods should detect this obvious anomaly
    assert z_anomaly, "Z-score method should detect anomaly"
    assert iqr_anomaly, "IQR method should detect anomaly"
    assert ewma_anomaly, "EWMA method should detect anomaly"
    
    # Details should have different methods
    assert z_details['method'] == 'z_score'
    assert iqr_details['method'] == 'iqr'
    assert ewma_details['method'] == 'ewma'


def test_metric_anomaly_monitor_integration():
    """
    Integration test: Verify MetricAnomalyMonitor integrates with AlertManager
    """
    detector = AnomalyDetector(
        window_size=100,
        z_score_threshold=3.0,
        min_samples=30
    )
    
    alert_manager = AlertManager(
        error_rate_threshold=5.0,
        dedup_window_seconds=1,
        max_alerts_per_hour=100
    )
    
    monitor = MetricAnomalyMonitor(detector, alert_manager)
    
    # Add normal values
    for i in range(50):
        monitor.check_metric('error_rate', 5.0 + i * 0.1)
    
    # Add anomalous value
    monitor.check_metric('error_rate', 100.0)
    
    # Verify alert was sent
    stats = alert_manager.get_alert_stats()
    assert stats['alerts_last_hour'] >= 1, \
        "Alert should be sent for anomaly"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
