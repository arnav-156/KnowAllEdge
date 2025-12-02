"""
Anomaly Detection System
Detects anomalies in system behavior using statistical methods

Requirements: 8.7
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """
    Detects anomalies in system metrics using statistical methods
    
    Methods:
    - Z-score detection (standard deviations from mean)
    - Moving average detection
    - Exponential weighted moving average (EWMA)
    - Interquartile range (IQR) detection
    """
    
    def __init__(
        self,
        window_size: int = 100,
        z_score_threshold: float = 3.0,
        iqr_multiplier: float = 1.5,
        ewma_alpha: float = 0.3,
        min_samples: int = 30
    ):
        """
        Initialize anomaly detector
        
        Args:
            window_size: Number of samples to keep in sliding window
            z_score_threshold: Number of standard deviations for anomaly
            iqr_multiplier: Multiplier for IQR method
            ewma_alpha: Smoothing factor for EWMA (0-1)
            min_samples: Minimum samples before detecting anomalies
        """
        self.window_size = window_size
        self.z_score_threshold = z_score_threshold
        self.iqr_multiplier = iqr_multiplier
        self.ewma_alpha = ewma_alpha
        self.min_samples = min_samples
        
        # Metric windows (metric_name -> deque of values)
        self.metric_windows: Dict[str, deque] = {}
        self.lock = threading.Lock()
        
        # Anomaly history
        self.anomaly_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        
        logger.info(
            "Anomaly detector initialized",
            extra={
                'window_size': window_size,
                'z_score_threshold': z_score_threshold,
                'min_samples': min_samples
            }
        )
    
    def add_sample(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """
        Add a sample to the metric window
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        with self.lock:
            if metric_name not in self.metric_windows:
                self.metric_windows[metric_name] = deque(maxlen=self.window_size)
            
            self.metric_windows[metric_name].append({
                'value': value,
                'timestamp': timestamp or datetime.now()
            })
    
    def detect_z_score_anomaly(self, metric_name: str, value: float) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect anomaly using Z-score method
        
        Args:
            metric_name: Name of the metric
            value: Current value to check
        
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        """
        with self.lock:
            if metric_name not in self.metric_windows:
                return False, None
            
            window = self.metric_windows[metric_name]
            
            # Need minimum samples
            if len(window) < self.min_samples:
                return False, None
            
            # Calculate statistics
            values = [sample['value'] for sample in window]
            mean = np.mean(values)
            std = np.std(values)
            
            # Avoid division by zero
            if std == 0:
                return False, None
            
            # Calculate Z-score
            z_score = abs((value - mean) / std)
            
            is_anomaly = z_score > self.z_score_threshold
            
            if is_anomaly:
                details = {
                    'method': 'z_score',
                    'metric_name': metric_name,
                    'value': value,
                    'mean': mean,
                    'std': std,
                    'z_score': z_score,
                    'threshold': self.z_score_threshold,
                    'timestamp': datetime.now().isoformat()
                }
                self._record_anomaly(details)
                return True, details
            
            return False, None
    
    def detect_iqr_anomaly(self, metric_name: str, value: float) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect anomaly using Interquartile Range (IQR) method
        
        Args:
            metric_name: Name of the metric
            value: Current value to check
        
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        """
        with self.lock:
            if metric_name not in self.metric_windows:
                return False, None
            
            window = self.metric_windows[metric_name]
            
            # Need minimum samples
            if len(window) < self.min_samples:
                return False, None
            
            # Calculate IQR
            values = [sample['value'] for sample in window]
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            
            # Calculate bounds
            lower_bound = q1 - (self.iqr_multiplier * iqr)
            upper_bound = q3 + (self.iqr_multiplier * iqr)
            
            is_anomaly = value < lower_bound or value > upper_bound
            
            if is_anomaly:
                details = {
                    'method': 'iqr',
                    'metric_name': metric_name,
                    'value': value,
                    'q1': q1,
                    'q3': q3,
                    'iqr': iqr,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound,
                    'timestamp': datetime.now().isoformat()
                }
                self._record_anomaly(details)
                return True, details
            
            return False, None
    
    def detect_ewma_anomaly(
        self,
        metric_name: str,
        value: float,
        threshold_multiplier: float = 3.0
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect anomaly using Exponential Weighted Moving Average (EWMA)
        
        Args:
            metric_name: Name of the metric
            value: Current value to check
            threshold_multiplier: Multiplier for standard deviation threshold
        
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        """
        with self.lock:
            if metric_name not in self.metric_windows:
                return False, None
            
            window = self.metric_windows[metric_name]
            
            # Need minimum samples
            if len(window) < self.min_samples:
                return False, None
            
            # Calculate EWMA
            values = [sample['value'] for sample in window]
            ewma = self._calculate_ewma(values)
            
            # Calculate standard deviation of residuals
            residuals = [v - e for v, e in zip(values, ewma)]
            std_residual = np.std(residuals)
            
            # Check if current value is anomalous
            expected = ewma[-1]
            deviation = abs(value - expected)
            threshold = threshold_multiplier * std_residual
            
            is_anomaly = deviation > threshold
            
            if is_anomaly:
                details = {
                    'method': 'ewma',
                    'metric_name': metric_name,
                    'value': value,
                    'expected': expected,
                    'deviation': deviation,
                    'threshold': threshold,
                    'std_residual': std_residual,
                    'timestamp': datetime.now().isoformat()
                }
                self._record_anomaly(details)
                return True, details
            
            return False, None
    
    def _calculate_ewma(self, values: List[float]) -> List[float]:
        """Calculate Exponential Weighted Moving Average"""
        ewma = [values[0]]
        for value in values[1:]:
            ewma.append(self.ewma_alpha * value + (1 - self.ewma_alpha) * ewma[-1])
        return ewma
    
    def detect_anomaly(
        self,
        metric_name: str,
        value: float,
        method: str = 'z_score'
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Detect anomaly using specified method
        
        Args:
            metric_name: Name of the metric
            value: Current value to check
            method: Detection method ('z_score', 'iqr', 'ewma', 'all')
        
        Returns:
            Tuple of (is_anomaly, anomaly_details)
        
        Requirements: 8.7
        """
        # Add sample to window
        self.add_sample(metric_name, value)
        
        # Detect using specified method
        if method == 'z_score':
            return self.detect_z_score_anomaly(metric_name, value)
        elif method == 'iqr':
            return self.detect_iqr_anomaly(metric_name, value)
        elif method == 'ewma':
            return self.detect_ewma_anomaly(metric_name, value)
        elif method == 'all':
            # Use all methods and return if any detect anomaly
            z_anomaly, z_details = self.detect_z_score_anomaly(metric_name, value)
            iqr_anomaly, iqr_details = self.detect_iqr_anomaly(metric_name, value)
            ewma_anomaly, ewma_details = self.detect_ewma_anomaly(metric_name, value)
            
            if z_anomaly or iqr_anomaly or ewma_anomaly:
                # Combine details
                combined_details = {
                    'method': 'combined',
                    'metric_name': metric_name,
                    'value': value,
                    'z_score': z_details if z_anomaly else None,
                    'iqr': iqr_details if iqr_anomaly else None,
                    'ewma': ewma_details if ewma_anomaly else None,
                    'timestamp': datetime.now().isoformat()
                }
                return True, combined_details
            
            return False, None
        else:
            raise ValueError(f"Unknown detection method: {method}")
    
    def _record_anomaly(self, details: Dict[str, Any]):
        """Record anomaly in history"""
        self.anomaly_history.append(details)
        
        # Trim history if too large
        if len(self.anomaly_history) > self.max_history:
            self.anomaly_history = self.anomaly_history[-self.max_history:]
        
        logger.warning(
            f"Anomaly detected: {details['metric_name']}",
            extra=details
        )
    
    def get_anomaly_history(
        self,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get anomaly history
        
        Args:
            metric_name: Filter by metric name (optional)
            since: Filter by timestamp (optional)
            limit: Maximum number of anomalies to return
        
        Returns:
            List of anomaly details
        """
        with self.lock:
            history = self.anomaly_history.copy()
        
        # Filter by metric name
        if metric_name:
            history = [a for a in history if a['metric_name'] == metric_name]
        
        # Filter by timestamp
        if since:
            history = [
                a for a in history
                if datetime.fromisoformat(a['timestamp']) > since
            ]
        
        # Limit results
        return history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""
        with self.lock:
            total_anomalies = len(self.anomaly_history)
            
            # Count by metric
            by_metric = {}
            for anomaly in self.anomaly_history:
                metric = anomaly['metric_name']
                by_metric[metric] = by_metric.get(metric, 0) + 1
            
            # Count by method
            by_method = {}
            for anomaly in self.anomaly_history:
                method = anomaly['method']
                by_method[method] = by_method.get(method, 0) + 1
            
            # Recent anomalies (last hour)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_anomalies = [
                a for a in self.anomaly_history
                if datetime.fromisoformat(a['timestamp']) > one_hour_ago
            ]
            
            return {
                'total_anomalies': total_anomalies,
                'recent_anomalies_1h': len(recent_anomalies),
                'by_metric': by_metric,
                'by_method': by_method,
                'tracked_metrics': list(self.metric_windows.keys()),
                'window_size': self.window_size,
                'min_samples': self.min_samples
            }
    
    def reset_metric(self, metric_name: str):
        """Reset metric window"""
        with self.lock:
            if metric_name in self.metric_windows:
                del self.metric_windows[metric_name]
    
    def reset_all(self):
        """Reset all metrics and history"""
        with self.lock:
            self.metric_windows.clear()
            self.anomaly_history.clear()


class MetricAnomalyMonitor:
    """
    Monitors specific metrics for anomalies and triggers alerts
    """
    
    def __init__(self, detector: AnomalyDetector, alert_manager=None):
        """
        Initialize metric anomaly monitor
        
        Args:
            detector: AnomalyDetector instance
            alert_manager: Optional AlertManager for sending alerts
        """
        self.detector = detector
        self.alert_manager = alert_manager
        
        # Metrics to monitor
        self.monitored_metrics = {
            'error_rate': {'method': 'z_score', 'severity': 'critical'},
            'latency_p99': {'method': 'ewma', 'severity': 'warning'},
            'cpu_percent': {'method': 'iqr', 'severity': 'warning'},
            'memory_percent': {'method': 'iqr', 'severity': 'warning'},
            'request_rate': {'method': 'z_score', 'severity': 'info'}
        }
    
    def check_metric(self, metric_name: str, value: float):
        """
        Check metric for anomalies and send alert if detected
        
        Args:
            metric_name: Name of the metric
            value: Current value
        """
        if metric_name not in self.monitored_metrics:
            return
        
        config = self.monitored_metrics[metric_name]
        method = config['method']
        severity = config['severity']
        
        is_anomaly, details = self.detector.detect_anomaly(metric_name, value, method)
        
        if is_anomaly and self.alert_manager:
            self.alert_manager.send_alert(
                alert_type='anomaly',
                severity=severity,
                title=f'Anomaly Detected: {metric_name}',
                message=f'Unusual behavior detected in {metric_name}',
                details=details
            )
    
    def add_monitored_metric(self, metric_name: str, method: str = 'z_score', severity: str = 'warning'):
        """Add a metric to monitor"""
        self.monitored_metrics[metric_name] = {
            'method': method,
            'severity': severity
        }
    
    def remove_monitored_metric(self, metric_name: str):
        """Remove a metric from monitoring"""
        if metric_name in self.monitored_metrics:
            del self.monitored_metrics[metric_name]


# Global anomaly detector instance
_anomaly_detector: Optional[AnomalyDetector] = None


def get_anomaly_detector(**kwargs) -> AnomalyDetector:
    """Get or create global anomaly detector instance"""
    global _anomaly_detector
    
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetector(**kwargs)
    
    return _anomaly_detector
