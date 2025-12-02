"""
Prometheus Metrics Exporter for KNOWALLEDGE Backend

Provides Prometheus-compatible metrics for monitoring:
- API request metrics (counter, histogram)
- Quota usage metrics (gauge)
- Cache performance metrics (counter)
- Circuit breaker metrics (gauge)
- Error rate metrics (counter)
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)

# ==================== REQUEST METRICS ====================

# Total API requests
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Request duration histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

# Active requests gauge
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# ==================== QUOTA METRICS ====================

# Quota usage gauges
quota_requests_current_minute = Gauge(
    'quota_requests_current_minute',
    'Current requests in the current minute'
)

quota_requests_today = Gauge(
    'quota_requests_today',
    'Total requests today'
)

quota_tokens_current_minute = Gauge(
    'quota_tokens_current_minute',
    'Current tokens used in the current minute'
)

quota_tokens_today = Gauge(
    'quota_tokens_today',
    'Total tokens used today'
)

# Quota limits
quota_rpm_limit = Gauge(
    'quota_rpm_limit',
    'Requests per minute limit'
)

quota_tpm_limit = Gauge(
    'quota_tpm_limit',
    'Tokens per minute limit'
)

# Quota remaining
quota_rpm_remaining = Gauge(
    'quota_rpm_remaining',
    'Remaining requests this minute'
)

quota_tpm_remaining = Gauge(
    'quota_tpm_remaining',
    'Remaining tokens this minute'
)

# Quota exceeded counter
quota_exceeded_total = Counter(
    'quota_exceeded_total',
    'Total number of times quota was exceeded',
    ['limit_type']  # rpm, rpd, tpm, tpd
)

# ==================== CACHE METRICS ====================

# Cache operations
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['operation', 'result']  # operation: get/set/delete, result: hit/miss/success/failure
)

# Cache hit rate
cache_hit_rate = Gauge(
    'cache_hit_rate',
    'Cache hit rate percentage'
)

# Cache size
cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Current cache size in bytes',
    ['layer']  # memory, redis, cdn
)

# Cache items count
cache_items_count = Gauge(
    'cache_items_count',
    'Number of items in cache',
    ['layer']
)

# ==================== CIRCUIT BREAKER METRICS ====================

# Circuit breaker state
circuit_breaker_state = Gauge(
    'circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

# Circuit breaker failures
circuit_breaker_failures_total = Counter(
    'circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['service']
)

# Circuit breaker successes
circuit_breaker_successes_total = Counter(
    'circuit_breaker_successes_total',
    'Total circuit breaker successes',
    ['service']
)

# ==================== DATABASE METRICS ====================

# Database connection pool size
db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size'
)

# Database connections in use
db_connections_in_use = Gauge(
    'db_connections_in_use',
    'Number of database connections currently in use'
)

# Database pool overflow
db_pool_overflow = Gauge(
    'db_pool_overflow',
    'Number of connections in overflow'
)

# Database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],  # select, insert, update, delete
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

# Database errors
db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type']
)

# ==================== ERROR METRICS ====================

# Application errors
application_errors_total = Counter(
    'application_errors_total',
    'Total application errors',
    ['endpoint', 'error_type']
)

# Validation failures
validation_failures_total = Counter(
    'validation_failures_total',
    'Total validation failures',
    ['validator', 'issue_type']
)

# ==================== API METRICS ====================

# Gemini API calls
gemini_api_calls_total = Counter(
    'gemini_api_calls_total',
    'Total Gemini API calls',
    ['endpoint', 'model', 'status']
)

# Gemini API duration
gemini_api_duration_seconds = Histogram(
    'gemini_api_duration_seconds',
    'Gemini API call duration in seconds',
    ['endpoint', 'model'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
)

# Gemini API tokens
gemini_api_tokens_total = Counter(
    'gemini_api_tokens_total',
    'Total tokens used in Gemini API calls',
    ['endpoint', 'model']
)

# ==================== BUSINESS METRICS ====================

# Subtopics generated
subtopics_generated_total = Counter(
    'subtopics_generated_total',
    'Total subtopics generated'
)

# Explanations generated
explanations_generated_total = Counter(
    'explanations_generated_total',
    'Total explanations generated'
)

# Images generated
images_generated_total = Counter(
    'images_generated_total',
    'Total images generated',
    ['source']  # dalle, imagen, upload
)

# Quality scores
content_quality_score = Histogram(
    'content_quality_score',
    'Content quality scores',
    ['content_type'],  # subtopic, explanation, topic
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# ==================== SYSTEM METRICS ====================

# Application info
app_info = Info('app', 'Application information')
app_info.info({
    'name': 'KNOWALLEDGE_backend',
    'version': '1.0.0',
    'python_version': '3.9+'
})

# ==================== HELPER FUNCTIONS ====================

def track_request_prometheus(func):
    """
    Decorator to track request metrics in Prometheus format
    
    Usage:
        @app.route('/api/endpoint')
        @track_request_prometheus
        def endpoint():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from flask import request
        
        method = request.method
        endpoint = request.endpoint or 'unknown'
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        start_time = time.time()
        status = 500  # Default to error
        error = None
        
        try:
            response = func(*args, **kwargs)
            
            # Extract status code from response
            if isinstance(response, tuple):
                status = response[1] if len(response) > 1 else 200
            else:
                status = 200
            
            return response
            
        except Exception as e:
            error = e
            logger.error(f"Error in {endpoint}: {str(e)}", exc_info=True)
            raise
            
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            http_requests_in_progress.labels(
                method=method,
                endpoint=endpoint
            ).dec()
            
            if error:
                error_type = type(error).__name__
                application_errors_total.labels(
                    endpoint=endpoint,
                    error_type=error_type
                ).inc()
    
    return wrapper


def update_quota_metrics(quota_stats: dict):
    """
    Update Prometheus quota metrics from quota_tracker stats
    
    Args:
        quota_stats: Dictionary from quota_tracker.get_stats()
    """
    try:
        # Current usage
        current_min = quota_stats.get('current_minute', {})
        current_day = quota_stats.get('current_day', {})
        
        quota_requests_current_minute.set(current_min.get('requests', 0))
        quota_requests_today.set(current_day.get('requests', 0))
        quota_tokens_current_minute.set(current_min.get('tokens', 0))
        quota_tokens_today.set(current_day.get('tokens', 0))
        
        # Limits
        limits = quota_stats.get('limits', {})
        quota_rpm_limit.set(limits.get('rpm', 0))
        quota_tpm_limit.set(limits.get('tpm', 0))
        
        # Remaining
        remaining = quota_stats.get('remaining', {})
        quota_rpm_remaining.set(remaining.get('rpm', 0))
        quota_tpm_remaining.set(remaining.get('tpm', 0))
        
    except Exception as e:
        logger.warning(f"Failed to update quota metrics: {e}")


def update_cache_metrics(cache_stats: dict):
    """
    Update Prometheus cache metrics from cache stats
    
    Args:
        cache_stats: Dictionary from multi_cache.get_stats()
    """
    try:
        # Hit rate
        hit_rate = cache_stats.get('hit_rate', 0.0)
        cache_hit_rate.set(hit_rate)
        
        # Layer-specific stats
        layers = cache_stats.get('layers', {})
        for layer_name, layer_stats in layers.items():
            hits = layer_stats.get('hits', 0)
            misses = layer_stats.get('misses', 0)
            size = layer_stats.get('size', 0)
            
            cache_items_count.labels(layer=layer_name).set(hits + misses)
            
    except Exception as e:
        logger.warning(f"Failed to update cache metrics: {e}")


def update_database_metrics(db_stats: dict):
    """
    Update Prometheus database metrics from database manager stats
    
    Args:
        db_stats: Dictionary from database_manager.get_pool_stats()
    """
    try:
        # Pool metrics
        db_pool_size.set(db_stats.get('pool_size', 0))
        db_connections_in_use.set(db_stats.get('connections_in_use', 0))
        db_pool_overflow.set(db_stats.get('pool_overflow', 0))
        
    except Exception as e:
        logger.warning(f"Failed to update database metrics: {e}")


def update_circuit_breaker_metrics(breaker_name: str, state: str, failures: int = 0, successes: int = 0):
    """
    Update circuit breaker metrics
    
    Args:
        breaker_name: Name of the circuit breaker
        state: Current state (closed, open, half_open)
        failures: Number of failures (optional)
        successes: Number of successes (optional)
    """
    try:
        # Map state to numeric value
        state_map = {'closed': 0, 'open': 1, 'half_open': 2}
        state_value = state_map.get(state.lower(), 0)
        
        circuit_breaker_state.labels(service=breaker_name).set(state_value)
        
        if failures > 0:
            circuit_breaker_failures_total.labels(service=breaker_name).inc(failures)
        
        if successes > 0:
            circuit_breaker_successes_total.labels(service=breaker_name).inc(successes)
            
    except Exception as e:
        logger.warning(f"Failed to update circuit breaker metrics: {e}")


def record_gemini_api_call(endpoint: str, model: str, duration: float, tokens: int, status: str = 'success'):
    """
    Record a Gemini API call
    
    Args:
        endpoint: API endpoint name
        model: Model name (gemini-2.0-flash, etc.)
        duration: Call duration in seconds
        tokens: Number of tokens used
        status: Call status (success, failure, quota_exceeded)
    """
    try:
        gemini_api_calls_total.labels(
            endpoint=endpoint,
            model=model,
            status=status
        ).inc()
        
        gemini_api_duration_seconds.labels(
            endpoint=endpoint,
            model=model
        ).observe(duration)
        
        gemini_api_tokens_total.labels(
            endpoint=endpoint,
            model=model
        ).inc(tokens)
        
    except Exception as e:
        logger.warning(f"Failed to record Gemini API call: {e}")


def record_content_generated(content_type: str, quality_score: float = None):
    """
    Record content generation
    
    Args:
        content_type: Type of content (subtopic, explanation, image)
        quality_score: Optional quality score (0.0-1.0)
    """
    try:
        if content_type == 'subtopic':
            subtopics_generated_total.inc()
        elif content_type == 'explanation':
            explanations_generated_total.inc()
        elif content_type == 'image':
            images_generated_total.labels(source='generated').inc()
        
        if quality_score is not None:
            content_quality_score.labels(content_type=content_type).observe(quality_score)
            
    except Exception as e:
        logger.warning(f"Failed to record content generation: {e}")


def get_prometheus_metrics() -> Response:
    """
    Generate Prometheus metrics response
    
    Returns:
        Flask Response with Prometheus metrics
    """
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


# ==================== INITIALIZATION ====================

def init_prometheus_metrics(app, quota_tracker=None, cache=None, database_manager=None):
    """
    Initialize Prometheus metrics with Flask app
    
    Args:
        app: Flask application
        quota_tracker: Optional quota tracker instance
        cache: Optional cache instance
        database_manager: Optional database manager instance
    
    Requirements: 8.2
    """
    logger.info("Initializing Prometheus metrics")
    
    # Add metrics endpoint
    @app.route('/metrics', methods=['GET'])
    def metrics_endpoint():
        """
        Prometheus metrics endpoint
        
        Exposes metrics in Prometheus format including:
        - Request count, latency, errors
        - Database pool usage
        - Cache hit ratio
        - Quota usage
        - Circuit breaker states
        
        Requirements: 8.2
        """
        try:
            # Update quota metrics if available
            if quota_tracker:
                try:
                    quota_stats = quota_tracker.get_stats()
                    update_quota_metrics(quota_stats)
                except Exception as e:
                    logger.warning(f"Failed to update quota metrics: {e}")
            
            # Update cache metrics if available
            if cache:
                try:
                    cache_stats = cache.get_stats()
                    update_cache_metrics(cache_stats)
                except Exception as e:
                    logger.warning(f"Failed to update cache metrics: {e}")
            
            # Update database metrics if available
            if database_manager:
                try:
                    db_stats = database_manager.get_pool_stats()
                    update_database_metrics(db_stats)
                except Exception as e:
                    logger.warning(f"Failed to update database metrics: {e}")
            
            return get_prometheus_metrics()
            
        except Exception as e:
            logger.error(f"Error generating Prometheus metrics: {e}")
            return Response("Error generating metrics", status=500)
    
    logger.info("Prometheus metrics initialized successfully")
    logger.info("Metrics available at /metrics endpoint")
