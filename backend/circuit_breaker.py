"""
Circuit Breaker Pattern Implementation
Prevents cascade failures for external API calls
Enhanced with separate breakers per service and metrics export
"""

import time
from enum import Enum
from functools import wraps
from typing import Callable, Optional, Any, Dict
from threading import Lock

from structured_logging import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit is open, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit is open"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        success_threshold: int = 2,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before attempting reset (OPEN -> HALF_OPEN)
            success_threshold: Successful calls needed to close circuit
            expected_exception: Exception type to catch
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self.expected_exception = expected_exception
        self.name = name
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.lock = Lock()
        
        # ✅ NEW: Metrics tracking for monitoring
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'rejected_calls': 0,
            'state_transitions': {
                'closed_to_open': 0,
                'open_to_half_open': 0,
                'half_open_to_closed': 0,
                'half_open_to_open': 0
            },
            'last_state_change': None,
            'uptime_start': time.time()
        }
        
        logger.info("Circuit breaker initialized", extra={
            'name': name,
            'failure_threshold': failure_threshold,
            'timeout': timeout
        })
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        # Track total calls
        self.metrics['total_calls'] += 1
        
        with self.lock:
            # Check if we should attempt reset
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._transition_state(CircuitState.HALF_OPEN)
                    self.success_count = 0
                    logger.info("Circuit breaker entering HALF_OPEN state", extra={
                        'name': self.name
                    })
                else:
                    # Circuit is open, fail fast
                    self.metrics['rejected_calls'] += 1
                    logger.warning("Circuit breaker is OPEN, request rejected", extra={
                        'name': self.name,
                        'failure_count': self.failure_count
                    })
                    raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
        
        # Attempt to execute function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        return time.time() - self.last_failure_time >= self.timeout
    
    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            self.metrics['successful_calls'] += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._reset()
                    self._transition_state(CircuitState.CLOSED)
                    logger.info("Circuit breaker CLOSED after successful recovery", extra={
                        'name': self.name,
                        'success_count': self.success_count
                    })
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success in CLOSED state
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.metrics['failed_calls'] += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failure during recovery, open circuit again
                self._transition_state(CircuitState.OPEN)
                logger.warning("Circuit breaker reopened during recovery", extra={
                    'name': self.name
                })
            elif self.failure_count >= self.failure_threshold:
                # Too many failures, open circuit
                self._transition_state(CircuitState.OPEN)
                logger.error("Circuit breaker OPENED due to failures", extra={
                    'name': self.name,
                    'failure_count': self.failure_count,
                    'threshold': self.failure_threshold
                })
    
    def _reset(self):
        """Reset circuit breaker to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
    
    def _transition_state(self, new_state: CircuitState):
        """Track state transitions for metrics"""
        old_state = self.state
        self.state = new_state
        self.metrics['last_state_change'] = time.time()
        
        # Track specific transitions
        transition_key = f"{old_state.value}_to_{new_state.value}"
        if transition_key in self.metrics['state_transitions']:
            self.metrics['state_transitions'][transition_key] += 1
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'last_failure_time': self.last_failure_time
        }
    
    def get_metrics(self) -> dict:
        """✅ NEW: Export comprehensive metrics for monitoring"""
        with self.lock:
            uptime = time.time() - self.metrics['uptime_start']
            total_calls = self.metrics['total_calls']
            
            # Calculate derived metrics
            success_rate = 0.0
            if total_calls > 0:
                success_rate = (self.metrics['successful_calls'] / total_calls) * 100
            
            failure_rate = 0.0
            if total_calls > 0:
                failure_rate = (self.metrics['failed_calls'] / total_calls) * 100
            
            rejection_rate = 0.0
            if total_calls > 0:
                rejection_rate = (self.metrics['rejected_calls'] / total_calls) * 100
            
            return {
                'name': self.name,
                'state': self.state.value,
                'uptime_seconds': round(uptime, 2),
                
                # Call metrics
                'total_calls': total_calls,
                'successful_calls': self.metrics['successful_calls'],
                'failed_calls': self.metrics['failed_calls'],
                'rejected_calls': self.metrics['rejected_calls'],
                
                # Rates
                'success_rate_percent': round(success_rate, 2),
                'failure_rate_percent': round(failure_rate, 2),
                'rejection_rate_percent': round(rejection_rate, 2),
                
                # Current state
                'current_failure_count': self.failure_count,
                'current_success_count': self.success_count,
                'failure_threshold': self.failure_threshold,
                'success_threshold': self.success_threshold,
                
                # State transitions
                'state_transitions': self.metrics['state_transitions'].copy(),
                'last_state_change': self.metrics['last_state_change'],
                
                # Health indicators
                'is_healthy': self.state == CircuitState.CLOSED,
                'is_degraded': self.state == CircuitState.HALF_OPEN,
                'is_failing': self.state == CircuitState.OPEN
            }
    
    def export_prometheus_metrics(self) -> str:
        """✅ NEW: Export metrics in Prometheus format"""
        metrics = self.get_metrics()
        name = self.name.replace('-', '_').replace(' ', '_')
        
        lines = [
            f'# HELP circuit_breaker_state Current state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)',
            f'# TYPE circuit_breaker_state gauge',
            f'circuit_breaker_state{{name="{self.name}"}} {0 if self.state == CircuitState.CLOSED else 1 if self.state == CircuitState.HALF_OPEN else 2}',
            '',
            f'# HELP circuit_breaker_calls_total Total number of calls',
            f'# TYPE circuit_breaker_calls_total counter',
            f'circuit_breaker_calls_total{{name="{self.name}",result="success"}} {metrics["successful_calls"]}',
            f'circuit_breaker_calls_total{{name="{self.name}",result="failure"}} {metrics["failed_calls"]}',
            f'circuit_breaker_calls_total{{name="{self.name}",result="rejected"}} {metrics["rejected_calls"]}',
            '',
            f'# HELP circuit_breaker_success_rate Success rate percentage',
            f'# TYPE circuit_breaker_success_rate gauge',
            f'circuit_breaker_success_rate{{name="{self.name}"}} {metrics["success_rate_percent"]}',
            '',
            f'# HELP circuit_breaker_state_transitions_total State transitions count',
            f'# TYPE circuit_breaker_state_transitions_total counter'
        ]
        
        for transition, count in metrics['state_transitions'].items():
            lines.append(f'circuit_breaker_state_transitions_total{{name="{self.name}",transition="{transition}"}} {count}')
        
        return '\n'.join(lines)
    
    def force_open(self):
        """Manually open the circuit (for testing/maintenance)"""
        with self.lock:
            self._transition_state(CircuitState.OPEN)
            logger.warning("Circuit breaker manually opened", extra={'name': self.name})
    
    def force_close(self):
        """Manually close the circuit (for testing/maintenance)"""
        with self.lock:
            self._reset()
            self._transition_state(CircuitState.CLOSED)
            logger.info("Circuit breaker manually closed", extra={'name': self.name})


def circuit_breaker(breaker: CircuitBreaker):
    """Decorator to protect functions with circuit breaker"""
    def circuit_breaker_decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return circuit_breaker_decorator


# ✅ ENHANCED: Separate circuit breakers for different Google AI services
google_ai_text_breaker = None      # Text generation (subtopics, explanation)
google_ai_vision_breaker = None    # Vision API (image2topic)
google_ai_imagen_breaker = None    # Image generation (generate_image)

# Legacy breaker for backward compatibility
google_ai_breaker = None


def initialize_circuit_breakers(config):
    """Initialize separate circuit breakers for each Google AI service"""
    global google_ai_text_breaker, google_ai_vision_breaker, google_ai_imagen_breaker, google_ai_breaker
    
    if config.circuit_breaker.enabled:
        # Separate breaker for text generation (most common, more lenient)
        google_ai_text_breaker = CircuitBreaker(
            failure_threshold=config.circuit_breaker.failure_threshold,
            timeout=config.circuit_breaker.timeout,
            success_threshold=config.circuit_breaker.success_threshold,
            expected_exception=Exception,
            name="google_ai_text_generation"
        )
        
        # Separate breaker for vision API (different failure patterns)
        google_ai_vision_breaker = CircuitBreaker(
            failure_threshold=max(3, config.circuit_breaker.failure_threshold - 2),  # More sensitive
            timeout=config.circuit_breaker.timeout,
            success_threshold=config.circuit_breaker.success_threshold,
            expected_exception=Exception,
            name="google_ai_vision"
        )
        
        # Separate breaker for image generation (can be slow, different thresholds)
        google_ai_imagen_breaker = CircuitBreaker(
            failure_threshold=max(3, config.circuit_breaker.failure_threshold - 2),
            timeout=config.circuit_breaker.timeout * 2,  # Longer recovery time
            success_threshold=config.circuit_breaker.success_threshold,
            expected_exception=Exception,
            name="google_ai_imagen"
        )
        
        # Legacy breaker for backward compatibility (points to text breaker)
        google_ai_breaker = google_ai_text_breaker
        
        logger.info("Separate circuit breakers initialized", extra={
            'text_breaker': google_ai_text_breaker.name,
            'vision_breaker': google_ai_vision_breaker.name,
            'imagen_breaker': google_ai_imagen_breaker.name
        })
    else:
        logger.info("Circuit breakers disabled")


def get_google_ai_breaker() -> Optional[CircuitBreaker]:
    """Get Google AI circuit breaker (legacy - returns text breaker)"""
    return google_ai_breaker


def get_text_generation_breaker() -> Optional[CircuitBreaker]:
    """✅ NEW: Get text generation circuit breaker"""
    return google_ai_text_breaker


def get_vision_api_breaker() -> Optional[CircuitBreaker]:
    """✅ NEW: Get vision API circuit breaker"""
    return google_ai_vision_breaker


def get_imagen_breaker() -> Optional[CircuitBreaker]:
    """✅ NEW: Get Imagen circuit breaker"""
    return google_ai_imagen_breaker


def get_all_breakers() -> Dict[str, CircuitBreaker]:
    """✅ NEW: Get all circuit breakers for monitoring"""
    breakers = {}
    if google_ai_text_breaker:
        breakers['text_generation'] = google_ai_text_breaker
    if google_ai_vision_breaker:
        breakers['vision'] = google_ai_vision_breaker
    if google_ai_imagen_breaker:
        breakers['imagen'] = google_ai_imagen_breaker
    return breakers


def get_all_metrics() -> Dict[str, dict]:
    """✅ NEW: Get metrics from all circuit breakers"""
    metrics = {}
    for name, breaker in get_all_breakers().items():
        metrics[name] = breaker.get_metrics()
    return metrics


def export_all_prometheus_metrics() -> str:
    """✅ NEW: Export all circuit breaker metrics in Prometheus format"""
    lines = []
    for breaker in get_all_breakers().values():
        lines.append(breaker.export_prometheus_metrics())
        lines.append('')  # Blank line between breakers
    return '\n'.join(lines)
