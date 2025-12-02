"""
Multi-Layer Caching Strategy
Browser → CDN → Redis → Database
Includes cache invalidation, pre-caching, and CDN integration
"""

import time
import hashlib
import json
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass, field
from functools import wraps
from flask import request, make_response
import threading
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheConfig:
    """Configuration for multi-layer caching"""
    # Layer 1: Browser cache (Cache-Control headers)
    browser_cache_ttl: int = 300  # 5 minutes
    browser_cache_public: bool = True
    
    # Layer 2: CDN cache (CloudFlare, etc.)
    cdn_cache_ttl: int = 1800  # 30 minutes
    cdn_cache_enabled: bool = False  # Enable when CDN is configured
    cdn_bypass_header: str = 'X-CDN-Bypass'
    
    # Layer 3: Redis cache (already implemented in multi_layer_cache.py)
    redis_cache_ttl: int = 3600  # 1 hour
    
    # Layer 4: In-memory cache (hot data)
    memory_cache_ttl: int = 600  # 10 minutes
    memory_cache_max_size: int = 1000
    
    # Pre-caching configuration
    enable_precaching: bool = True
    precache_popular_threshold: int = 10  # Cache topics with 10+ requests
    precache_refresh_interval: int = 3600  # Refresh every hour
    
    # Cache invalidation
    invalidation_pattern_support: bool = True
    max_invalidation_keys: int = 100


@dataclass
class CacheEntry:
    """Represents a cached entry"""
    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float = field(default_factory=time.time)


class MultiLayerCache:
    """
    Multi-layer caching system with browser, CDN, Redis, and memory layers
    """
    
    def __init__(self, config: Optional[CacheConfig] = None, redis_cache=None):
        self.config = config or CacheConfig()
        self.redis_cache = redis_cache  # External Redis cache instance
        
        # In-memory cache (Layer 4 - hot data)
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_lock = threading.Lock()
        
        # Popular topics tracking
        self.access_counts: Dict[str, int] = {}
        self.popular_topics: List[str] = []
        
        # CDN configuration
        self.cdn_headers = {
            'Cache-Control': f'public, max-age={self.config.cdn_cache_ttl}',
            'CDN-Cache-Control': f'max-age={self.config.cdn_cache_ttl}'
        }
        
        logger.info("Multi-layer cache initialized", extra={
            'browser_ttl': self.config.browser_cache_ttl,
            'cdn_enabled': self.config.cdn_cache_enabled,
            'redis_ttl': self.config.redis_cache_ttl,
            'memory_ttl': self.config.memory_cache_ttl
        })
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _clean_memory_cache(self):
        """Remove expired entries and enforce size limit"""
        current_time = time.time()
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if current_time - entry.timestamp > entry.ttl
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Enforce size limit (LRU eviction)
        if len(self.memory_cache) > self.config.memory_cache_max_size:
            # Sort by last access time and remove oldest
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1].last_access
            )
            remove_count = len(self.memory_cache) - self.config.memory_cache_max_size
            for key, _ in sorted_entries[:remove_count]:
                del self.memory_cache[key]
                logger.debug("Evicted cache entry (LRU)", extra={'key': key})
    
    def get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache (Layer 4)"""
        with self.cache_lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                
                # Check expiration
                if time.time() - entry.timestamp > entry.ttl:
                    del self.memory_cache[key]
                    return None
                
                # Update access statistics
                entry.access_count += 1
                entry.last_access = time.time()
                
                logger.debug("Memory cache hit", extra={'key': key})
                return entry.value
            
            return None
    
    def set_in_memory(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in memory cache (Layer 4)"""
        with self.cache_lock:
            self._clean_memory_cache()
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl or self.config.memory_cache_ttl
            )
            self.memory_cache[key] = entry
            logger.debug("Memory cache set", extra={'key': key, 'ttl': entry.ttl})
    
    def get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache (Layer 3)"""
        if self.redis_cache:
            try:
                result = self.redis_cache.get(key)
                if result:
                    logger.debug("Redis cache hit", extra={'key': key})
                return result
            except Exception as e:
                logger.error("Redis cache get failed", extra={'error': str(e)})
        return None
    
    def set_in_redis(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis cache (Layer 3)"""
        if self.redis_cache:
            try:
                self.redis_cache.set(key, value, ttl or self.config.redis_cache_ttl)
                logger.debug("Redis cache set", extra={'key': key})
            except Exception as e:
                logger.error("Redis cache set failed", extra={'error': str(e)})
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache hierarchy (memory → Redis)
        Implements cache promotion (lower hit promotes to upper layers)
        """
        # Layer 4: Memory cache
        value = self.get_from_memory(key)
        if value is not None:
            return value
        
        # Layer 3: Redis cache
        value = self.get_from_redis(key)
        if value is not None:
            # Promote to memory cache
            self.set_in_memory(key, value)
            return value
        
        logger.debug("Cache miss", extra={'key': key})
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in all cache layers"""
        self.set_in_memory(key, value, ttl)
        self.set_in_redis(key, value, ttl)
    
    def invalidate(self, key: str):
        """Invalidate cache entry across all layers"""
        # Memory cache
        with self.cache_lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
                logger.debug("Memory cache invalidated", extra={'key': key})
        
        # Redis cache
        if self.redis_cache:
            try:
                self.redis_cache.delete(key)
                logger.debug("Redis cache invalidated", extra={'key': key})
            except Exception as e:
                logger.error("Redis cache invalidation failed", extra={'error': str(e)})
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern (e.g., 'topic:*')"""
        if not self.config.invalidation_pattern_support:
            logger.warning("Pattern invalidation disabled")
            return
        
        count = 0
        
        # Memory cache
        with self.cache_lock:
            matching_keys = [
                key for key in self.memory_cache.keys()
                if self._pattern_matches(pattern, key)
            ]
            for key in matching_keys[:self.config.max_invalidation_keys]:
                del self.memory_cache[key]
                count += 1
        
        # Redis cache
        if self.redis_cache:
            try:
                # Redis SCAN with pattern matching
                redis_count = self.redis_cache.delete_pattern(pattern)
                count += redis_count
            except Exception as e:
                logger.error("Redis pattern invalidation failed", extra={'error': str(e)})
        
        logger.info("Pattern invalidation complete", extra={
            'pattern': pattern,
            'count': count
        })
    
    def _pattern_matches(self, pattern: str, key: str) -> bool:
        """Check if key matches wildcard pattern"""
        if '*' not in pattern:
            return pattern == key
        
        # Simple wildcard matching
        parts = pattern.split('*')
        if len(parts) == 2:
            return key.startswith(parts[0]) and key.endswith(parts[1])
        return False
    
    def track_access(self, topic: str):
        """Track topic access for pre-caching popular items"""
        if not self.config.enable_precaching:
            return
        
        with self.cache_lock:
            self.access_counts[topic] = self.access_counts.get(topic, 0) + 1
            
            # Update popular topics list
            if self.access_counts[topic] >= self.config.precache_popular_threshold:
                if topic not in self.popular_topics:
                    self.popular_topics.append(topic)
                    logger.info("Topic marked as popular", extra={
                        'topic': topic,
                        'access_count': self.access_counts[topic]
                    })
    
    def get_popular_topics(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular topics for pre-caching"""
        with self.cache_lock:
            sorted_topics = sorted(
                self.access_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_topics[:limit]
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.cache_lock:
            memory_hits = sum(entry.access_count for entry in self.memory_cache.values())
            
            stats = {
                'memory': {
                    'size': len(self.memory_cache),
                    'max_size': self.config.memory_cache_max_size,
                    'usage_percent': round(
                        (len(self.memory_cache) / self.config.memory_cache_max_size) * 100, 2
                    ),
                    'total_hits': memory_hits
                },
                'popular_topics': {
                    'count': len(self.popular_topics),
                    'top_10': self.get_popular_topics(10)
                },
                'config': {
                    'browser_ttl': self.config.browser_cache_ttl,
                    'cdn_enabled': self.config.cdn_cache_enabled,
                    'redis_ttl': self.config.redis_cache_ttl,
                    'memory_ttl': self.config.memory_cache_ttl
                }
            }
            
            # Add Redis stats if available
            if self.redis_cache:
                try:
                    redis_stats = self.redis_cache.get_stats()
                    stats['redis'] = redis_stats
                except:
                    pass
            
            return stats


def add_browser_cache_headers(response, ttl: Optional[int] = None, public: bool = True):
    """Add browser cache headers to response (Layer 1)"""
    ttl = ttl or 300  # Default 5 minutes
    
    cache_control = f"{'public' if public else 'private'}, max-age={ttl}"
    response.headers['Cache-Control'] = cache_control
    response.headers['Expires'] = time.strftime(
        '%a, %d %b %Y %H:%M:%S GMT',
        time.gmtime(time.time() + ttl)
    )
    
    # ETag for conditional requests
    if response.data:
        etag = hashlib.md5(response.data).hexdigest()
        response.headers['ETag'] = f'"{etag}"'
    
    return response


def add_cdn_cache_headers(response, ttl: Optional[int] = None):
    """Add CDN cache headers to response (Layer 2)"""
    ttl = ttl or 1800  # Default 30 minutes
    
    # CloudFlare-specific headers
    response.headers['Cache-Control'] = f'public, max-age={ttl}'
    response.headers['CDN-Cache-Control'] = f'max-age={ttl}'
    response.headers['Cloudflare-CDN-Cache-Control'] = f'max-age={ttl}'
    
    # Vary header for proper caching
    response.headers['Vary'] = 'Accept-Encoding, Accept-Language'
    
    return response


def check_cdn_bypass() -> bool:
    """Check if CDN should be bypassed"""
    return request.headers.get('X-CDN-Bypass') == 'true'


def with_multi_layer_cache(
    cache_key_prefix: str,
    ttl: Optional[int] = None,
    browser_cache: bool = True,
    cdn_cache: bool = False,
    track_popularity: bool = True
):
    """
    Decorator for multi-layer caching
    
    Args:
        cache_key_prefix: Prefix for cache key generation
        ttl: Cache TTL (seconds)
        browser_cache: Enable browser caching (Layer 1)
        cdn_cache: Enable CDN caching (Layer 2)
        track_popularity: Track access for pre-caching
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache = kwargs.get('cache')  # MultiLayerCache instance
            if not cache:
                # Execute without caching
                return f(*args, **kwargs)
            
            cache_key = cache._generate_cache_key(cache_key_prefix, *args, **kwargs)
            
            # Check cache hierarchy
            if not check_cdn_bypass():
                cached_value = cache.get(cache_key)
                if cached_value is not None:
                    response = make_response(cached_value)
                    
                    # Add cache headers
                    if browser_cache:
                        add_browser_cache_headers(response, ttl)
                    if cdn_cache and cache.config.cdn_cache_enabled:
                        add_cdn_cache_headers(response, ttl)
                    
                    response.headers['X-Cache'] = 'HIT'
                    return response
            
            # Cache miss - execute function
            result = f(*args, **kwargs)
            
            # Store in cache
            if result:
                cache.set(cache_key, result, ttl)
                
                # Track popularity
                if track_popularity and 'topic' in kwargs:
                    cache.track_access(kwargs['topic'])
            
            # Add cache headers to response
            response = make_response(result)
            if browser_cache:
                add_browser_cache_headers(response, ttl)
            if cdn_cache and cache.config.cdn_cache_enabled:
                add_cdn_cache_headers(response, ttl)
            
            response.headers['X-Cache'] = 'MISS'
            return response
        
        return wrapper
    return decorator


# Global cache instance
_cache_instance = None
_cache_lock = threading.Lock()


def get_cache_strategy(config: Optional[CacheConfig] = None, redis_cache=None) -> MultiLayerCache:
    """Get or create cache strategy singleton"""
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = MultiLayerCache(config, redis_cache)
    return _cache_instance
