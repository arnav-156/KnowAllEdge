"""
Google Gemini API Quota Tracker
Tracks API usage against quotas with fallback mechanisms and request prioritization
"""

import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
from functools import wraps
from flask import request, jsonify
import threading
from structured_logging import get_logger

logger = get_logger(__name__)


class RequestPriority(Enum):
    """Request priority levels"""
    CRITICAL = 1    # Health checks, critical operations
    HIGH = 2        # User-initiated requests
    MEDIUM = 3      # Background processing
    LOW = 4         # Batch operations


@dataclass
class QuotaConfig:
    """Configuration for Gemini API quotas"""
    # Google Gemini API free tier limits
    requests_per_minute: int = 15  # RPM limit
    requests_per_day: int = 1500   # RPD limit
    
    # Token limits (Gemini 2.0 Flash)
    tokens_per_minute: int = 1_000_000  # TPM
    tokens_per_day: int = 50_000_000    # TPD
    
    # Safety margins (use 80% of quota to prevent hitting limits)
    rpm_safety_margin: float = 0.8
    rpd_safety_margin: float = 0.8
    tpm_safety_margin: float = 0.8
    tpd_safety_margin: float = 0.8
    
    # Fallback configuration
    enable_fallback: bool = True
    fallback_cache_ttl: int = 3600  # 1 hour cache for fallback responses
    
    # Queue configuration
    max_queue_size: int = 100
    queue_timeout: int = 30  # seconds
    
    def get_safe_rpm(self) -> int:
        """Get safe RPM limit with margin"""
        return int(self.requests_per_minute * self.rpm_safety_margin)
    
    def get_safe_rpd(self) -> int:
        """Get safe RPD limit with margin"""
        return int(self.requests_per_day * self.rpd_safety_margin)
    
    def get_safe_tpm(self) -> int:
        """Get safe TPM limit with margin"""
        return int(self.tokens_per_minute * self.tpm_safety_margin)
    
    def get_safe_tpd(self) -> int:
        """Get safe TPD limit with margin"""
        return int(self.tokens_per_day * self.tpd_safety_margin)


@dataclass
class QuotaRequest:
    """Represents a queued API request"""
    priority: RequestPriority
    timestamp: float
    endpoint: str
    estimated_tokens: int
    callback: callable
    user_id: Optional[str] = None


class QuotaTracker:
    """
    Tracks Gemini API quota usage with intelligent fallback and prioritization
    """
    
    def __init__(self, config: Optional[QuotaConfig] = None):
        self.config = config or QuotaConfig()
        
        # Request tracking (sliding window)
        self.requests_minute: deque = deque(maxlen=200)  # Last minute
        self.requests_day: deque = deque(maxlen=10000)   # Last 24 hours
        
        # Token tracking
        self.tokens_minute: deque = deque(maxlen=200)
        self.tokens_day: deque = deque(maxlen=10000)
        
        # Priority queue (separate queue per priority level)
        self.queues: Dict[RequestPriority, deque] = {
            RequestPriority.CRITICAL: deque(),
            RequestPriority.HIGH: deque(),
            RequestPriority.MEDIUM: deque(),
            RequestPriority.LOW: deque(),
        }
        
        # Fallback cache
        self.fallback_cache: Dict[str, Tuple[any, float]] = {}  # key -> (response, timestamp)
        
        # Statistics
        self.total_requests = 0
        self.quota_exceeded_count = 0
        self.fallback_used_count = 0
        self.queued_requests = 0
        
        # Thread safety
        self.lock = threading.Lock()
        
        logger.info("Quota tracker initialized", extra={
            'rpm_limit': self.config.requests_per_minute,
            'rpd_limit': self.config.requests_per_day,
            'safe_rpm': self.config.get_safe_rpm(),
            'safe_rpd': self.config.get_safe_rpd()
        })
    
    def _clean_old_records(self):
        """Remove records outside sliding windows"""
        current_time = time.time()
        
        # Clean minute window (60 seconds)
        minute_ago = current_time - 60
        while self.requests_minute and self.requests_minute[0] < minute_ago:
            self.requests_minute.popleft()
        while self.tokens_minute and self.tokens_minute[0][0] < minute_ago:
            self.tokens_minute.popleft()
        
        # Clean day window (24 hours)
        day_ago = current_time - 86400
        while self.requests_day and self.requests_day[0] < day_ago:
            self.requests_day.popleft()
        while self.tokens_day and self.tokens_day[0][0] < day_ago:
            self.tokens_day.popleft()
    
    def can_make_request(self, estimated_tokens: int = 1000) -> Tuple[bool, Optional[str]]:
        """
        Check if request can be made without exceeding quota
        Returns: (can_proceed, reason_if_denied)
        """
        with self.lock:
            self._clean_old_records()
            
            # Check RPM
            rpm_count = len(self.requests_minute)
            if rpm_count >= self.config.get_safe_rpm():
                logger.warning("RPM limit reached", extra={
                    'current': rpm_count,
                    'limit': self.config.get_safe_rpm()
                })
                return False, f"RPM limit reached ({rpm_count}/{self.config.get_safe_rpm()})"
            
            # Check RPD
            rpd_count = len(self.requests_day)
            if rpd_count >= self.config.get_safe_rpd():
                logger.warning("RPD limit reached", extra={
                    'current': rpd_count,
                    'limit': self.config.get_safe_rpd()
                })
                return False, f"RPD limit reached ({rpd_count}/{self.config.get_safe_rpd()})"
            
            # Check TPM
            tpm_count = sum(tokens for _, tokens in self.tokens_minute)
            if tpm_count + estimated_tokens > self.config.get_safe_tpm():
                logger.warning("TPM limit reached", extra={
                    'current': tpm_count,
                    'estimated': estimated_tokens,
                    'limit': self.config.get_safe_tpm()
                })
                return False, f"TPM limit reached ({tpm_count}/{self.config.get_safe_tpm()})"
            
            # Check TPD
            tpd_count = sum(tokens for _, tokens in self.tokens_day)
            if tpd_count + estimated_tokens > self.config.get_safe_tpd():
                logger.warning("TPD limit reached", extra={
                    'current': tpd_count,
                    'estimated': estimated_tokens,
                    'limit': self.config.get_safe_tpd()
                })
                return False, f"TPD limit reached ({tpd_count}/{self.config.get_safe_tpd()})"
            
            return True, None
    
    def record_request(self, actual_tokens: int):
        """Record a successful API request"""
        with self.lock:
            current_time = time.time()
            self.requests_minute.append(current_time)
            self.requests_day.append(current_time)
            self.tokens_minute.append((current_time, actual_tokens))
            self.tokens_day.append((current_time, actual_tokens))
            self.total_requests += 1
            
            logger.debug("Request recorded", extra={
                'tokens': actual_tokens,
                'rpm': len(self.requests_minute),
                'rpd': len(self.requests_day)
            })
    
    def get_fallback_response(self, cache_key: str) -> Optional[any]:
        """Get cached response as fallback"""
        if not self.config.enable_fallback:
            return None
        
        if cache_key not in self.fallback_cache:
            return None
        
        response, timestamp = self.fallback_cache[cache_key]
        
        # Check if cache is still valid
        if time.time() - timestamp > self.config.fallback_cache_ttl:
            del self.fallback_cache[cache_key]
            return None
        
        self.fallback_used_count += 1
        logger.info("Using fallback response", extra={'cache_key': cache_key})
        return response
    
    def cache_response(self, cache_key: str, response: any):
        """Cache response for potential fallback use"""
        if self.config.enable_fallback:
            self.fallback_cache[cache_key] = (response, time.time())
    
    def queue_request(self, priority: RequestPriority, endpoint: str, 
                     estimated_tokens: int, user_id: Optional[str] = None) -> bool:
        """
        Queue a request when quota is exceeded
        Returns: True if queued successfully, False if queue is full
        """
        with self.lock:
            # Check total queue size
            total_queued = sum(len(q) for q in self.queues.values())
            if total_queued >= self.config.max_queue_size:
                logger.warning("Request queue full", extra={
                    'queue_size': total_queued,
                    'max_size': self.config.max_queue_size
                })
                return False
            
            # Add to appropriate priority queue
            req = QuotaRequest(
                priority=priority,
                timestamp=time.time(),
                endpoint=endpoint,
                estimated_tokens=estimated_tokens,
                user_id=user_id,
                callback=None
            )
            self.queues[priority].append(req)
            self.queued_requests += 1
            
            logger.info("Request queued", extra={
                'priority': priority.name,
                'endpoint': endpoint,
                'queue_size': len(self.queues[priority])
            })
            return True
    
    def get_next_request(self) -> Optional[QuotaRequest]:
        """Get next request from queue (highest priority first)"""
        with self.lock:
            for priority in [RequestPriority.CRITICAL, RequestPriority.HIGH, 
                           RequestPriority.MEDIUM, RequestPriority.LOW]:
                if self.queues[priority]:
                    return self.queues[priority].popleft()
            return None
    
    def get_stats(self) -> Dict:
        """Get current quota usage statistics"""
        with self.lock:
            self._clean_old_records()
            
            rpm_count = len(self.requests_minute)
            rpd_count = len(self.requests_day)
            tpm_count = sum(tokens for _, tokens in self.tokens_minute)
            tpd_count = sum(tokens for _, tokens in self.tokens_day)
            
            return {
                'requests': {
                    'per_minute': {
                        'current': rpm_count,
                        'limit': self.config.get_safe_rpm(),
                        'percentage': round((rpm_count / self.config.get_safe_rpm()) * 100, 2)
                    },
                    'per_day': {
                        'current': rpd_count,
                        'limit': self.config.get_safe_rpd(),
                        'percentage': round((rpd_count / self.config.get_safe_rpd()) * 100, 2)
                    }
                },
                'tokens': {
                    'per_minute': {
                        'current': tpm_count,
                        'limit': self.config.get_safe_tpm(),
                        'percentage': round((tpm_count / self.config.get_safe_tpm()) * 100, 2)
                    },
                    'per_day': {
                        'current': tpd_count,
                        'limit': self.config.get_safe_tpd(),
                        'percentage': round((tpd_count / self.config.get_safe_tpd()) * 100, 2)
                    }
                },
                'statistics': {
                    'total_requests': self.total_requests,
                    'quota_exceeded': self.quota_exceeded_count,
                    'fallback_used': self.fallback_used_count,
                    'queued_requests': self.queued_requests,
                    'current_queue_size': sum(len(q) for q in self.queues.values())
                },
                'queue': {
                    priority.name: len(queue) 
                    for priority, queue in self.queues.items()
                }
            }


# Global instance
_quota_tracker_instance = None
_quota_tracker_lock = threading.Lock()


def get_quota_tracker(config: Optional[QuotaConfig] = None) -> QuotaTracker:
    """Get or create quota tracker singleton"""
    global _quota_tracker_instance
    if _quota_tracker_instance is None:
        with _quota_tracker_lock:
            if _quota_tracker_instance is None:
                _quota_tracker_instance = QuotaTracker(config)
    return _quota_tracker_instance


def with_quota_check(priority: RequestPriority = RequestPriority.HIGH, 
                     estimated_tokens: int = 1000):
    """
    Decorator to check quota before making API request
    Implements fallback and queuing when quota is exceeded
    """
    def with_quota_check_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            tracker = get_quota_tracker()
            
            # Check if request can proceed
            can_proceed, reason = tracker.can_make_request(estimated_tokens)
            
            if can_proceed:
                # Execute request
                try:
                    result = f(*args, **kwargs)
                    
                    # Record successful request
                    # Extract actual token count from result if available
                    actual_tokens = estimated_tokens
                    if isinstance(result, dict) and 'usage_metadata' in result:
                        actual_tokens = result['usage_metadata'].get('total_token_count', estimated_tokens)
                    
                    tracker.record_request(actual_tokens)
                    
                    # Cache response for potential fallback
                    cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                    tracker.cache_response(cache_key, result)
                    
                    return result
                    
                except Exception as e:
                    logger.error("API request failed", extra={'error': str(e)}, exc_info=True)
                    
                    # Try fallback
                    cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                    fallback = tracker.get_fallback_response(cache_key)
                    if fallback:
                        return fallback
                    raise
            
            else:
                # Quota exceeded - try fallback first
                cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
                fallback = tracker.get_fallback_response(cache_key)
                if fallback:
                    return fallback
                
                # No fallback - queue request
                tracker.quota_exceeded_count += 1
                user_id = kwargs.get('user_id') or (hasattr(request, 'cookies') and request.cookies.get('session_id'))
                
                queued = tracker.queue_request(
                    priority=priority,
                    endpoint=f.__name__,
                    estimated_tokens=estimated_tokens,
                    user_id=user_id
                )
                
                if queued:
                    return jsonify({
                        'error': 'quota_exceeded',
                        'message': f'API quota exceeded: {reason}. Request queued.',
                        'queued': True,
                        'priority': priority.name
                    }), 429
                else:
                    return jsonify({
                        'error': 'quota_exceeded',
                        'message': f'API quota exceeded: {reason}. Queue full.',
                        'queued': False
                    }), 429
        
        return decorated_function
    return with_quota_check_decorator

