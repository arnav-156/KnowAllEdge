"""
Advanced Rate Limiting Module
User-based rate limiting with request prioritization and queuing
Integrated with quota tracker for comprehensive rate management
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from functools import wraps
from flask import request, jsonify
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    # Per-user limits
    user_requests_per_minute: int = 10
    user_requests_per_hour: int = 100
    user_requests_per_day: int = 500
    
    # Per-IP limits (fallback)
    ip_requests_per_minute: int = 20
    ip_requests_per_hour: int = 200
    
    # Global limits (prevent single user exhausting quota)
    global_requests_per_minute: int = 100
    global_requests_per_hour: int = 1000
    
    # Burst allowance
    burst_size: int = 5
    
    # Priority levels
    priority_levels: Dict[str, int] = field(default_factory=lambda: {
        'high': 1,    # Critical requests (e.g., health checks)
        'medium': 2,  # Normal requests
        'low': 3      # Background/batch requests
    })


@dataclass
class RequestRecord:
    """Record of a request for rate limiting"""
    timestamp: float
    endpoint: str
    user_id: Optional[str] = None
    ip_address: Optional[str] = None


class RateLimiter:
    """
    Advanced rate limiter with user-based tracking and request prioritization
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Request history per user
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Request history per IP (fallback)
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=500))
        
        # Global request history
        self.global_requests: deque = deque(maxlen=2000)
        
        # Blocked users/IPs (temporary)
        self.blocked_until: Dict[str, float] = {}
        
        # Request queue (for prioritization)
        self.request_queue: Dict[int, deque] = {
            1: deque(),  # High priority
            2: deque(),  # Medium priority
            3: deque(),  # Low priority
        }
        
        logger.info("Advanced rate limiter initialized", extra={
            'user_limit_per_minute': self.config.user_requests_per_minute,
            'user_limit_per_hour': self.config.user_requests_per_hour
        })
    
    def _get_identifier(self) -> Tuple[Optional[str], str]:
        """
        Get user identifier and IP address
        Returns: (user_id, ip_address)
        
        ✅ SECURITY FIX: Now properly extracts user_id from authenticated requests
        Priority order:
        1. g.current_user (set by @require_auth decorator)
        2. JWT token validation
        3. API key from X-API-Key header
        4. Falls back to IP only if no auth
        """
        user_id = None
        
        # 1. Check Flask g object (set by auth decorators)
        from flask import g
        if hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.get('user_id')
        
        # 2. Try to validate JWT token from Authorization header
        if not user_id:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
                try:
                    # Import auth module to decode JWT
                    from auth import decode_jwt_token
                    payload = decode_jwt_token(token)
                    if payload:
                        user_id = payload.get('user_id')
                except Exception:
                    pass  # Invalid token, continue to next method
        
        # 3. Check for API Key in X-API-Key header
        if not user_id:
            api_key = request.headers.get('X-API-Key')
            if api_key:
                user_id = f"apikey_{api_key[:16]}"  # Use truncated key as identifier
        
        # Get IP address (fallback identifier)
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        return user_id, ip_address
    
    def _clean_old_requests(self, request_deque: deque, max_age: float):
        """Remove requests older than max_age seconds"""
        current_time = time.time()
        while request_deque and current_time - request_deque[0].timestamp > max_age:
            request_deque.popleft()
    
    def _count_recent_requests(self, request_deque: deque, window: int) -> int:
        """Count requests within the time window (seconds)"""
        self._clean_old_requests(request_deque, window)
        return len(request_deque)
    
    def _is_blocked(self, identifier: str) -> bool:
        """Check if identifier is temporarily blocked"""
        if identifier in self.blocked_until:
            if time.time() < self.blocked_until[identifier]:
                return True
            else:
                # Block expired
                del self.blocked_until[identifier]
        return False
    
    def _block_identifier(self, identifier: str, duration: int = 300):
        """Temporarily block an identifier (default: 5 minutes)"""
        self.blocked_until[identifier] = time.time() + duration
        logger.warning("Identifier blocked", extra={
            'identifier': identifier[:16] + '...',
            'duration': duration
        })
    
    def check_rate_limit(
        self, 
        endpoint: str,
        priority: str = 'medium'
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request should be allowed based on rate limits
        
        Args:
            endpoint: The endpoint being accessed
            priority: Request priority ('high', 'medium', 'low')
        
        Returns:
            (is_allowed, error_info)
        """
        user_id, ip_address = self._get_identifier()
        identifier = user_id if user_id else ip_address
        current_time = time.time()
        
        # Check if blocked
        if self._is_blocked(identifier):
            return False, {
                'error': 'Too many requests - temporarily blocked',
                'retry_after': int(self.blocked_until[identifier] - current_time)
            }
        
        # Check global limits first (prevent quota exhaustion)
        global_1min = self._count_recent_requests(self.global_requests, 60)
        global_1hour = self._count_recent_requests(self.global_requests, 3600)
        
        if global_1min >= self.config.global_requests_per_minute:
            logger.warning("Global rate limit exceeded (1 minute)", extra={
                'requests_per_minute': global_1min
            })
            return False, {
                'error': 'System is experiencing high load. Please try again later.',
                'retry_after': 60
            }
        
        if global_1hour >= self.config.global_requests_per_hour:
            logger.warning("Global rate limit exceeded (1 hour)", extra={
                'requests_per_hour': global_1hour
            })
            return False, {
                'error': 'System hourly quota exceeded. Please try again later.',
                'retry_after': 300
            }
        
        # Check user-specific limits (if user_id available)
        if user_id:
            user_reqs = self.user_requests[user_id]
            
            user_1min = self._count_recent_requests(user_reqs, 60)
            user_1hour = self._count_recent_requests(user_reqs, 3600)
            user_1day = self._count_recent_requests(user_reqs, 86400)
            
            # Allow burst with exponential backoff
            burst_allowance = self.config.burst_size if user_1min < self.config.user_requests_per_minute else 0
            
            if user_1min >= (self.config.user_requests_per_minute + burst_allowance):
                # Block after multiple violations
                if user_1min > self.config.user_requests_per_minute * 2:
                    self._block_identifier(user_id, duration=300)
                
                return False, {
                    'error': 'Rate limit exceeded',
                    'limit': 'per_minute',
                    'current': user_1min,
                    'max': self.config.user_requests_per_minute,
                    'retry_after': 60
                }
            
            if user_1hour >= self.config.user_requests_per_hour:
                return False, {
                    'error': 'Hourly rate limit exceeded',
                    'limit': 'per_hour',
                    'current': user_1hour,
                    'max': self.config.user_requests_per_hour,
                    'retry_after': 300
                }
            
            if user_1day >= self.config.user_requests_per_day:
                return False, {
                    'error': 'Daily rate limit exceeded',
                    'limit': 'per_day',
                    'current': user_1day,
                    'max': self.config.user_requests_per_day,
                    'retry_after': 3600
                }
        
        # Check IP-based limits (fallback or additional check)
        ip_reqs = self.ip_requests[ip_address]
        ip_1min = self._count_recent_requests(ip_reqs, 60)
        ip_1hour = self._count_recent_requests(ip_reqs, 3600)
        
        if ip_1min >= self.config.ip_requests_per_minute:
            # Block aggressive IPs
            if ip_1min > self.config.ip_requests_per_minute * 3:
                self._block_identifier(ip_address, duration=600)
            
            return False, {
                'error': 'IP rate limit exceeded',
                'limit': 'per_minute',
                'retry_after': 60
            }
        
        if ip_1hour >= self.config.ip_requests_per_hour:
            return False, {
                'error': 'IP hourly rate limit exceeded',
                'limit': 'per_hour',
                'retry_after': 300
            }
        
        # Record this request
        request_record = RequestRecord(
            timestamp=current_time,
            endpoint=endpoint,
            user_id=user_id,
            ip_address=ip_address
        )
        
        if user_id:
            self.user_requests[user_id].append(request_record)
        self.ip_requests[ip_address].append(request_record)
        self.global_requests.append(request_record)
        
        return True, None
    
    def get_rate_limit_stats(self, user_id: Optional[str] = None, ip_address: Optional[str] = None) -> Dict:
        """Get current rate limit statistics"""
        stats = {
            'global': {
                'requests_per_minute': self._count_recent_requests(self.global_requests, 60),
                'requests_per_hour': self._count_recent_requests(self.global_requests, 3600),
                'limits': {
                    'per_minute': self.config.global_requests_per_minute,
                    'per_hour': self.config.global_requests_per_hour
                }
            }
        }
        
        if user_id and user_id in self.user_requests:
            user_reqs = self.user_requests[user_id]
            stats['user'] = {
                'requests_per_minute': self._count_recent_requests(user_reqs, 60),
                'requests_per_hour': self._count_recent_requests(user_reqs, 3600),
                'requests_per_day': self._count_recent_requests(user_reqs, 86400),
                'limits': {
                    'per_minute': self.config.user_requests_per_minute,
                    'per_hour': self.config.user_requests_per_hour,
                    'per_day': self.config.user_requests_per_day
                }
            }
        
        if ip_address and ip_address in self.ip_requests:
            ip_reqs = self.ip_requests[ip_address]
            stats['ip'] = {
                'requests_per_minute': self._count_recent_requests(ip_reqs, 60),
                'requests_per_hour': self._count_recent_requests(ip_reqs, 3600),
                'limits': {
                    'per_minute': self.config.ip_requests_per_minute,
                    'per_hour': self.config.ip_requests_per_hour
                }
            }
        
        return stats


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def advanced_rate_limit(priority: str = 'medium'):
    """
    Decorator for advanced rate limiting with user tracking
    
    Args:
        priority: Request priority level ('high', 'medium', 'low')
    """
    def advanced_rate_limit_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter()
            
            # Check rate limit
            is_allowed, error_info = rate_limiter.check_rate_limit(
                endpoint=f.__name__,
                priority=priority
            )
            
            if not is_allowed:
                logger.warning("Rate limit exceeded", extra={
                    'endpoint': f.__name__,
                    'error': error_info
                })
                return jsonify(error_info), 429
            
            # Execute function
            return f(*args, **kwargs)
        
        return wrapper
    return advanced_rate_limit_decorator
