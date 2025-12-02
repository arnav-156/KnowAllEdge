"""
Production Rate Limiter with Redis Backend
Implements sliding window algorithm with tier-based limits
Complies with Requirements 9.1, 9.2
"""

import time
import hashlib
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from functools import wraps
from flask import request, jsonify, g
import json

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitTier:
    """Rate limit configuration for a specific tier"""
    name: str
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    
    def __repr__(self):
        return f"<RateLimitTier {self.name}: {self.requests_per_minute}rpm, {self.requests_per_hour}rph, {self.requests_per_day}rpd>"


# Tier-based rate limits (Requirements 9.1)
RATE_LIMIT_TIERS = {
    'limited': RateLimitTier('limited', 5, 20, 50),          # Anonymous/guest
    'free': RateLimitTier('free', 10, 100, 500),             # Free registered
    'basic': RateLimitTier('basic', 30, 500, 2000),          # Basic paid
    'premium': RateLimitTier('premium', 100, 2000, 10000),   # Premium paid
    'unlimited': RateLimitTier('unlimited', 1000, 50000, 1000000)  # Admin
}


class RateLimiter:
    """
    Production-grade rate limiter with Redis backend
    
    Features:
    - Sliding window algorithm for accurate rate limiting
    - Tier-based limits (limited, free, basic, premium, unlimited)
    - Redis backend for distributed rate limiting
    - Fallback to in-memory for development
    - Automatic cleanup of expired entries
    
    Validates: Requirements 9.1, 9.2
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize rate limiter
        
        Args:
            redis_client: Redis client instance (optional, will use in-memory if None)
        """
        self.redis_client = redis_client
        self.memory_store: Dict[str, list] = {}  # Fallback in-memory store
        
        if self.redis_client:
            try:
                self.redis_client.ping()
                logger.info("Rate limiter initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
                self.redis_client = None
        else:
            logger.info("Rate limiter initialized with in-memory backend")
    
    def _get_redis_key(self, identifier: str, window: str) -> str:
        """
        Generate Redis key for rate limiting
        
        Args:
            identifier: User ID or IP address
            window: Time window ('minute', 'hour', 'day')
        
        Returns:
            Redis key string
        """
        return f"rate_limit:{identifier}:{window}"
    
    def _get_user_tier(self) -> str:
        """
        Get user's quota tier from request context
        
        Returns:
            Tier name ('limited', 'free', 'basic', 'premium', 'unlimited')
        """
        # Check Flask g object for authenticated user
        if hasattr(g, 'current_user') and g.current_user:
            tier = g.current_user.get('quota_tier', 'free')
            return tier
        
        # Check for API key (indicates at least free tier)
        if request.headers.get('X-API-Key'):
            return 'free'
        
        # Check for JWT token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return 'free'
        
        # Anonymous user
        return 'limited'
    
    def _get_identifier(self) -> str:
        """
        Get unique identifier for rate limiting
        
        Priority:
        1. User ID from authenticated request
        2. API key
        3. IP address
        
        Returns:
            Unique identifier string
        """
        # Try to get user ID from Flask g object
        if hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.get('user_id')
            if user_id:
                return f"user:{user_id}"
        
        # Try to get API key
        api_key = request.headers.get('X-API-Key')
        if api_key:
            # Hash API key for privacy
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
            return f"apikey:{key_hash}"
        
        # Fall back to IP address
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        
        return f"ip:{ip_address}"
    
    def _sliding_window_check(
        self,
        identifier: str,
        window_seconds: int,
        limit: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window algorithm
        
        Args:
            identifier: Unique identifier for the requester
            window_seconds: Time window in seconds
            limit: Maximum requests allowed in window
        
        Returns:
            Tuple of (is_allowed, current_count, retry_after_seconds)
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if self.redis_client:
            # Redis-based sliding window
            window_name = f"{window_seconds}s"
            key = self._get_redis_key(identifier, window_name)
            
            try:
                # Remove expired entries
                self.redis_client.zremrangebyscore(key, 0, window_start)
                
                # Count requests in current window
                current_count = self.redis_client.zcard(key)
                
                if current_count >= limit:
                    # Get oldest request timestamp to calculate retry_after
                    oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                    if oldest:
                        oldest_timestamp = oldest[0][1]
                        retry_after = int(oldest_timestamp + window_seconds - current_time) + 1
                    else:
                        retry_after = window_seconds
                    
                    return False, current_count, retry_after
                
                # Add current request
                request_id = f"{current_time}:{id(request)}"
                self.redis_client.zadd(key, {request_id: current_time})
                
                # Set expiration on key
                self.redis_client.expire(key, window_seconds + 10)
                
                return True, current_count + 1, 0
                
            except Exception as e:
                logger.error(f"Redis error in rate limiting: {e}")
                # Fall through to in-memory fallback
        
        # In-memory fallback
        key = f"{identifier}:{window_seconds}s"
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remove expired entries
        self.memory_store[key] = [
            ts for ts in self.memory_store[key]
            if ts > window_start
        ]
        
        current_count = len(self.memory_store[key])
        
        if current_count >= limit:
            # Calculate retry_after
            oldest_timestamp = min(self.memory_store[key])
            retry_after = int(oldest_timestamp + window_seconds - current_time) + 1
            return False, current_count, retry_after
        
        # Add current request
        self.memory_store[key].append(current_time)
        
        return True, current_count + 1, 0
    
    def check_rate_limit(self) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request should be allowed based on rate limits
        
        Returns:
            Tuple of (is_allowed, error_response_dict)
            
        Validates: Requirements 9.1, 9.2
        """
        identifier = self._get_identifier()
        tier_name = self._get_user_tier()
        tier = RATE_LIMIT_TIERS.get(tier_name, RATE_LIMIT_TIERS['limited'])
        
        # Check minute limit
        allowed, count, retry_after = self._sliding_window_check(
            identifier, 60, tier.requests_per_minute
        )
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded (minute)",
                extra={
                    'identifier': identifier[:20],
                    'tier': tier_name,
                    'count': count,
                    'limit': tier.requests_per_minute
                }
            )
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded: {count}/{tier.requests_per_minute} requests per minute',
                'tier': tier_name,
                'limit': tier.requests_per_minute,
                'window': 'minute',
                'retry_after': retry_after
            }
        
        # Check hour limit
        allowed, count, retry_after = self._sliding_window_check(
            identifier, 3600, tier.requests_per_hour
        )
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded (hour)",
                extra={
                    'identifier': identifier[:20],
                    'tier': tier_name,
                    'count': count,
                    'limit': tier.requests_per_hour
                }
            )
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded: {count}/{tier.requests_per_hour} requests per hour',
                'tier': tier_name,
                'limit': tier.requests_per_hour,
                'window': 'hour',
                'retry_after': retry_after
            }
        
        # Check day limit
        allowed, count, retry_after = self._sliding_window_check(
            identifier, 86400, tier.requests_per_day
        )
        
        if not allowed:
            logger.warning(
                "Rate limit exceeded (day)",
                extra={
                    'identifier': identifier[:20],
                    'tier': tier_name,
                    'count': count,
                    'limit': tier.requests_per_day
                }
            )
            return False, {
                'error': 'rate_limit_exceeded',
                'message': f'Rate limit exceeded: {count}/{tier.requests_per_day} requests per day',
                'tier': tier_name,
                'limit': tier.requests_per_day,
                'window': 'day',
                'retry_after': retry_after
            }
        
        return True, None
    
    def get_rate_limit_status(self) -> Dict:
        """
        Get current rate limit status for the requester
        
        Returns:
            Dictionary with current usage and limits
        """
        identifier = self._get_identifier()
        tier_name = self._get_user_tier()
        tier = RATE_LIMIT_TIERS.get(tier_name, RATE_LIMIT_TIERS['limited'])
        
        current_time = time.time()
        
        def get_count(window_seconds: int) -> int:
            """Get current request count for window"""
            window_start = current_time - window_seconds
            
            if self.redis_client:
                window_name = f"{window_seconds}s"
                key = self._get_redis_key(identifier, window_name)
                try:
                    self.redis_client.zremrangebyscore(key, 0, window_start)
                    return self.redis_client.zcard(key)
                except Exception:
                    pass
            
            # In-memory fallback
            key = f"{identifier}:{window_seconds}s"
            if key in self.memory_store:
                self.memory_store[key] = [
                    ts for ts in self.memory_store[key]
                    if ts > window_start
                ]
                return len(self.memory_store[key])
            
            return 0
        
        return {
            'tier': tier_name,
            'limits': {
                'minute': {
                    'limit': tier.requests_per_minute,
                    'remaining': max(0, tier.requests_per_minute - get_count(60)),
                    'used': get_count(60)
                },
                'hour': {
                    'limit': tier.requests_per_hour,
                    'remaining': max(0, tier.requests_per_hour - get_count(3600)),
                    'used': get_count(3600)
                },
                'day': {
                    'limit': tier.requests_per_day,
                    'remaining': max(0, tier.requests_per_day - get_count(86400)),
                    'used': get_count(86400)
                }
            }
        }


# Global rate limiter instance
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter(redis_client: Optional[redis.Redis] = None) -> RateLimiter:
    """
    Get or create global rate limiter instance
    
    Args:
        redis_client: Redis client (only used on first call)
    
    Returns:
        RateLimiter instance
    """
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter(redis_client)
    return _rate_limiter_instance


def rate_limit(f):
    """
    Decorator to apply rate limiting to Flask routes
    
    Usage:
        @app.route('/api/endpoint')
        @rate_limit
        def my_endpoint():
            return {'data': 'value'}
    
    Validates: Requirements 9.1, 9.2
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        limiter = get_rate_limiter()
        
        # Check rate limit
        allowed, error_response = limiter.check_rate_limit()
        
        if not allowed:
            # Return 429 with Retry-After header (Requirement 9.2)
            response = jsonify(error_response)
            response.status_code = 429
            response.headers['Retry-After'] = str(error_response.get('retry_after', 60))
            return response
        
        # Execute the route function
        return f(*args, **kwargs)
    
    return decorated_function
