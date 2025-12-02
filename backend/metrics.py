"""
Backend Analytics and Metrics Middleware
Tracks API performance, errors, and usage metrics using Prometheus

✅ FIXED: Uses existing prometheus_metrics.py to avoid duplicate metric registration
"""

from flask import request, g
from functools import wraps
import time
from datetime import datetime, timedelta
from collections import deque
import threading

# ✅ Import existing Prometheus metrics (avoids duplicate registration)
try:
    from prometheus_metrics import (
        http_requests_total as REQUEST_COUNT,
        http_request_duration_seconds as REQUEST_DURATION,
        http_requests_in_progress as REQUEST_IN_PROGRESS,
        cache_operations_total as CACHE_OPERATIONS,
        application_errors_total as ERROR_COUNT,
        gemini_api_calls_total as GEMINI_API_CALLS,
        gemini_api_tokens_total as GEMINI_TOKENS,
        gemini_api_duration_seconds as GEMINI_API_DURATION
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Fallback if prometheus_metrics not available
    PROMETHEUS_AVAILABLE = False
    print("⚠️ Warning: prometheus_metrics not available, metrics will not be tracked")

class MetricsCollector:
    """
    Collects and stores application metrics using Prometheus
    
    ✅ FIXED: No more memory leaks - using Prometheus counters/histograms
    ✅ FIXED: Thread-safe without lock contention
    ✅ FIXED: Metrics persist across restarts (Prometheus scrapes)
    ✅ FIXED: Uses existing prometheus_metrics.py (no duplicate registration)
    """
    
    def __init__(self):
        # ✅ Use fixed-size ring buffer instead of unbounded list
        self.recent_requests = deque(maxlen=100)  # Only keep last 100 for health checks
        self.recent_errors = deque(maxlen=50)     # Only keep last 50 errors
        
        self.start_time = datetime.now()
        self.lock = threading.Lock()  # Only for ring buffer access
        
        # Track concurrent users (set is thread-safe for add/remove)
        self.concurrent_users = set()
        self.user_lock = threading.Lock()
    
    def record_request(self, endpoint, method, status_code, duration, error=None):
        """
        Record a request with its metrics
        
        ✅ FIXED: Uses Prometheus metrics (no memory leak)
        ✅ FIXED: Only keeps 100 recent requests for health checks
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        # Update Prometheus metrics (no memory leak)
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        if error:
            error_type = type(error).__name__
            ERROR_COUNT.labels(endpoint=endpoint, error_type=error_type).inc()
        
        # Only keep recent requests for health checks (fixed-size ring buffer)
        with self.lock:
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'endpoint': endpoint,
                'method': method,
                'status_code': status_code,
                'duration_ms': duration * 1000,
                'error': str(error) if error else None
            }
            
            self.recent_requests.append(request_data)
            
            if error:
                self.recent_errors.append(request_data)
    
    def record_cache_hit(self):
        """Record a cache hit"""
        if PROMETHEUS_AVAILABLE:
            CACHE_OPERATIONS.labels(operation='get', result='hit').inc()
    
    def record_cache_miss(self):
        """Record a cache miss"""
        if PROMETHEUS_AVAILABLE:
            CACHE_OPERATIONS.labels(operation='get', result='miss').inc()
    
    def record_cache_set(self):
        """Record a cache set operation"""
        if PROMETHEUS_AVAILABLE:
            CACHE_OPERATIONS.labels(operation='set', result='success').inc()
    
    def add_concurrent_user(self, user_id):
        """Add a concurrent user"""
        with self.user_lock:
            self.concurrent_users.add(user_id)
    
    def remove_concurrent_user(self, user_id):
        """Remove a concurrent user"""
        with self.user_lock:
            self.concurrent_users.discard(user_id)
    
    def record_gemini_api_call(self, endpoint, model, tokens_used, duration, status='success'):
        """
        Record Gemini API usage
        
        Args:
            endpoint: API endpoint (e.g., '/api/generate')
            model: Model name (e.g., 'gemini-1.5-flash')
            tokens_used: Total tokens (prompt + completion)
            duration: API call duration in seconds
            status: 'success' or 'failure'
        """
        if not PROMETHEUS_AVAILABLE:
            return
            
        GEMINI_TOKENS.labels(endpoint=endpoint, model=model).inc(tokens_used)
        GEMINI_API_CALLS.labels(endpoint=endpoint, model=model, status=status).inc()
        GEMINI_API_DURATION.labels(endpoint=endpoint, model=model).observe(duration)
    
    
    def get_statistics(self):
        """
        Get comprehensive statistics
        
        ✅ FIXED: No more O(n log n) percentile calculations on every call
        Prometheus handles aggregation efficiently
        """
        with self.lock:
            total_requests = len(self.recent_requests)
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Calculate error rate from recent requests only
            error_count = len(self.recent_errors)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            with self.user_lock:
                concurrent_users = len(self.concurrent_users)
            
            return {
                'uptime_seconds': uptime,
                'uptime_formatted': str(timedelta(seconds=int(uptime))),
                'recent_requests': total_requests,  # Last 100 only
                'recent_errors': error_count,
                'error_rate_percent': round(error_rate, 2),
                'concurrent_users': concurrent_users,
                'note': 'Full metrics available at /metrics endpoint (Prometheus format)'
            }
    
    def get_health_metrics(self):
        """Get health check metrics"""
        with self.lock:
            # Only check last 50 errors (fixed-size deque)
            recent_errors_5min = [
                e for e in self.recent_errors
                if datetime.fromisoformat(e['timestamp']) > datetime.now() - timedelta(minutes=5)
            ]
            
            # Calculate avg response time from recent requests
            recent_times = [r['duration_ms'] for r in self.recent_requests]
            avg_response_time = sum(recent_times) / len(recent_times) if recent_times else 0
            
            # Determine health status
            if len(recent_errors_5min) > 10:
                status = 'unhealthy'
            elif avg_response_time > 5000:  # 5 seconds
                status = 'degraded'
            else:
                status = 'healthy'
            
            with self.user_lock:
                concurrent_users = len(self.concurrent_users)
            
            return {
                'status': status,
                'recent_errors_5min': len(recent_errors_5min),
                'avg_response_time_ms': round(avg_response_time, 2),
                'concurrent_users': concurrent_users
            }
    
    def reset_metrics(self):
        """Reset recent metrics (Prometheus counters cannot be reset)"""
        with self.lock:
            self.recent_requests.clear()
            self.recent_errors.clear()
            self.start_time = datetime.now()

# Global metrics collector instance
metrics_collector = MetricsCollector()

def track_request_metrics(f):
    """
    Decorator to track request metrics
    
    ✅ FIXED: Uses Prometheus REQUEST_IN_PROGRESS gauge
    ✅ FIXED: No lock contention issues
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Generate request ID
        request_id = f"{int(time.time() * 1000)}-{id(request)}"
        g.request_id = request_id
        g.start_time = time.time()
        
        # Track concurrent user
        user_id = request.remote_addr
        metrics_collector.add_concurrent_user(user_id)
        
        # Track request in progress
        if PROMETHEUS_AVAILABLE:
            REQUEST_IN_PROGRESS.labels(method=request.method, endpoint=request.path).inc()
        
        try:
            response = f(*args, **kwargs)
            
            # Record successful request
            duration = time.time() - g.start_time
            status_code = response[1] if isinstance(response, tuple) else 200
            
            metrics_collector.record_request(
                endpoint=request.path,
                method=request.method,
                status_code=status_code,
                duration=duration
            )
            
            # Add performance headers
            if isinstance(response, tuple):
                data, code, headers = response if len(response) == 3 else (*response, {})
            else:
                data, code, headers = response, 200, {}
            
            headers['X-Request-ID'] = request_id
            headers['X-Response-Time'] = f"{duration * 1000:.2f}ms"
            
            return data, code, headers
            
        except Exception as error:
            # Record failed request
            duration = time.time() - g.start_time
            metrics_collector.record_request(
                endpoint=request.path,
                method=request.method,
                status_code=500,
                duration=duration,
                error=error
            )
            raise
        
        finally:
            # Remove concurrent user and request in progress
            metrics_collector.remove_concurrent_user(user_id)
            if PROMETHEUS_AVAILABLE:
                REQUEST_IN_PROGRESS.labels(method=request.method, endpoint=request.path).dec()
    
    return decorated_function

def get_metrics_summary():
    """Get formatted metrics summary"""
    return metrics_collector.get_statistics()

def get_health_status():
    """Get health status"""
    return metrics_collector.get_health_metrics()

def record_cache_event(hit=True):
    """Record cache hit or miss"""
    if hit:
        metrics_collector.record_cache_hit()
    else:
        metrics_collector.record_cache_miss()

def record_gemini_usage(endpoint, model, tokens, duration, status='success'):
    """
    Record Gemini API usage and cost
    
    Example:
        record_gemini_usage('/api/generate', 'gemini-1.5-flash', 1500, 2.5)
    """
    metrics_collector.record_gemini_api_call(endpoint, model, tokens, duration, status)
