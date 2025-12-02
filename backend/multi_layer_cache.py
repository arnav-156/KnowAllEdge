"""
Multi-Layer Caching Strategy
Implements cache warming, versioning, and smart invalidation
"""

import json
import hashlib
import time
from typing import Optional, Any, List, Dict, Callable
from dataclasses import dataclass
from functools import wraps
from flask import request
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata"""
    data: Any
    timestamp: float
    version: str
    access_count: int = 0
    last_accessed: float = None
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp
        if self.size_bytes == 0:
            try:
                self.size_bytes = len(json.dumps(self.data))
            except:
                self.size_bytes = 1000  # Estimate


class MultiLayerCache:
    """
    Advanced caching with multiple layers and intelligent management
    """
    
    def __init__(self, redis_cache, config):
        """
        Initialize multi-layer cache
        
        Args:
            redis_cache: RedisCache instance for L2 cache
            config: Configuration object
        """
        self.redis_cache = redis_cache
        self.config = config
        
        # L1: Hot cache (most frequently accessed, in-memory)
        self.hot_cache: Dict[str, CacheEntry] = {}
        self.hot_cache_max_size = 100
        
        # L2: Redis cache (provided redis_cache instance)
        # L3: Would be CDN/browser cache (handled by HTTP headers)
        
        # Popular topics for cache warming
        self.popular_topics = [
            "Python Programming",
            "Machine Learning",
            "Web Development",
            "Data Structures",
            "Artificial Intelligence",
            "JavaScript",
            "React",
            "Database Design",
            "Computer Networks",
            "Operating Systems"
        ]
        
        # Cache statistics
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0,
            'evictions': 0,
            'warming_runs': 0
        }
        
        # Cache version (increment to invalidate all caches)
        self.cache_version = "v1.0"
        
        logger.info("Multi-layer cache initialized", extra={
            'hot_cache_size': self.hot_cache_max_size,
            'popular_topics': len(self.popular_topics),
            'cache_version': self.cache_version
        })
    
    def _generate_key(self, namespace: str, data: Dict) -> str:
        """Generate versioned cache key"""
        cache_str = f"{self.cache_version}:{namespace}:{json.dumps(data, sort_keys=True)}"
        return hashlib.sha256(cache_str.encode()).hexdigest()
    
    def _is_hot_topic(self, data: Dict) -> bool:
        """Check if this is a popular topic that should stay in hot cache"""
        topic = data.get('topic', '').lower()
        return any(pop.lower() in topic for pop in self.popular_topics)
    
    def get(self, namespace: str, data: Dict) -> Optional[Any]:
        """
        Get value from cache (checks all layers)
        
        Args:
            namespace: Cache namespace (e.g., 'subtopics', 'explanation')
            data: Request data for key generation
        
        Returns:
            Cached value or None
        """
        key = self._generate_key(namespace, data)
        current_time = time.time()
        
        # L1: Check hot cache
        if key in self.hot_cache:
            entry = self.hot_cache[key]
            
            # Check if expired
            if current_time - entry.timestamp < self.config.cache.ttl:
                entry.access_count += 1
                entry.last_accessed = current_time
                self.stats['l1_hits'] += 1
                
                logger.debug("L1 cache hit", extra={
                    'namespace': namespace,
                    'access_count': entry.access_count
                })
                
                return entry.data
            else:
                # Expired, remove from hot cache
                del self.hot_cache[key]
        
        # L2: Check Redis cache
        cached_value = self.redis_cache.get(key)
        if cached_value:
            self.stats['l2_hits'] += 1
            
            # Promote to hot cache if popular
            if self._is_hot_topic(data):
                self._promote_to_hot_cache(key, cached_value, current_time)
            
            logger.debug("L2 cache hit", extra={'namespace': namespace})
            return cached_value
        
        # Cache miss
        self.stats['misses'] += 1
        logger.debug("Cache miss", extra={'namespace': namespace})
        return None
    
    def set(
        self, 
        namespace: str, 
        data: Dict, 
        value: Any, 
        ttl: Optional[int] = None,
        promote_to_hot: bool = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            namespace: Cache namespace
            data: Request data for key generation
            value: Value to cache
            ttl: Time to live (seconds)
            promote_to_hot: Force promotion to hot cache
        
        Returns:
            Success boolean
        """
        key = self._generate_key(namespace, data)
        current_time = time.time()
        ttl = ttl or self.config.cache.ttl
        
        # Always set in L2 (Redis)
        success = self.redis_cache.set(key, value, ttl)
        
        # Promote to hot cache if popular or forced
        if promote_to_hot is True or (promote_to_hot is None and self._is_hot_topic(data)):
            self._promote_to_hot_cache(key, value, current_time)
        
        return success
    
    def _promote_to_hot_cache(self, key: str, value: Any, timestamp: float):
        """Promote entry to hot cache (L1)"""
        # Check if hot cache is full
        if len(self.hot_cache) >= self.hot_cache_max_size:
            self._evict_from_hot_cache()
        
        # Add to hot cache
        self.hot_cache[key] = CacheEntry(
            data=value,
            timestamp=timestamp,
            version=self.cache_version,
            access_count=1,
            last_accessed=timestamp
        )
        
        logger.debug("Promoted to hot cache", extra={'key': key[:16]})
    
    def _evict_from_hot_cache(self):
        """Evict least recently used entry from hot cache"""
        if not self.hot_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.hot_cache.keys(),
            key=lambda k: self.hot_cache[k].last_accessed
        )
        
        del self.hot_cache[lru_key]
        self.stats['evictions'] += 1
        
        logger.debug("Evicted from hot cache", extra={'key': lru_key[:16]})
    
    def invalidate(self, namespace: Optional[str] = None, pattern: Optional[str] = None):
        """
        Invalidate cache entries
        
        Args:
            namespace: Invalidate specific namespace
            pattern: Pattern to match (not implemented for hot cache)
        """
        if namespace:
            # Clear entries for specific namespace
            keys_to_delete = [
                k for k in self.hot_cache.keys()
                if k.startswith(f"{self.cache_version}:{namespace}:")
            ]
            for key in keys_to_delete:
                del self.hot_cache[key]
            
            logger.info("Invalidated cache namespace", extra={
                'namespace': namespace,
                'entries_cleared': len(keys_to_delete)
            })
        else:
            # Clear all
            self.hot_cache.clear()
            self.redis_cache.clear()
            logger.info("Invalidated all caches")
    
    def warm_cache(self, warmup_functions: Dict[str, Callable]):
        """
        Warm cache with popular topics
        
        Args:
            warmup_functions: Dict of {namespace: function} to generate cache data
                             Function should accept topic string and return cacheable data
        """
        logger.info("Starting cache warming", extra={
            'topics': len(self.popular_topics),
            'functions': list(warmup_functions.keys())
        })
        
        warmed_count = 0
        
        for topic in self.popular_topics:
            for namespace, warmup_func in warmup_functions.items():
                try:
                    # Generate cache data
                    data = {'topic': topic}
                    value = warmup_func(topic)
                    
                    if value:
                        # Cache with promotion to hot cache
                        self.set(
                            namespace=namespace,
                            data=data,
                            value=value,
                            promote_to_hot=True
                        )
                        warmed_count += 1
                
                except Exception as e:
                    logger.error("Cache warming error", extra={
                        'topic': topic,
                        'namespace': namespace,
                        'error': str(e)
                    })
        
        self.stats['warming_runs'] += 1
        
        logger.info("Cache warming complete", extra={
            'warmed_entries': warmed_count,
            'hot_cache_size': len(self.hot_cache)
        })
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['misses']
        hit_rate = 0.0
        if total_requests > 0:
            hit_rate = (self.stats['l1_hits'] + self.stats['l2_hits']) / total_requests
        
        return {
            'version': self.cache_version,
            'l1': {
                'size': len(self.hot_cache),
                'max_size': self.hot_cache_max_size,
                'hits': self.stats['l1_hits'],
                'evictions': self.stats['evictions']
            },
            'l2': self.redis_cache.get_stats(),
            'overall': {
                'total_requests': total_requests,
                'hit_rate': round(hit_rate, 3),
                'misses': self.stats['misses'],
                'warming_runs': self.stats['warming_runs']
            }
        }
    
    def update_version(self, new_version: str):
        """
        Update cache version (invalidates all existing caches)
        
        Args:
            new_version: New version string
        """
        old_version = self.cache_version
        self.cache_version = new_version
        
        # Clear all caches
        self.hot_cache.clear()
        self.redis_cache.clear()
        
        logger.info("Cache version updated", extra={
            'old_version': old_version,
            'new_version': new_version
        })


def multi_layer_cached(
    cache: 'MultiLayerCache',
    namespace: str,
    ttl: Optional[int] = None,
    promote_to_hot: bool = None
):
    """
    Decorator for multi-layer caching
    
    Args:
        cache: MultiLayerCache instance
        namespace: Cache namespace
        ttl: Time to live (seconds)
        promote_to_hot: Force promotion to hot cache
    """
    def multi_layer_cached_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Generate cache key from request data
            request_data = request.get_json() or {}
            
            # Try to get from cache
            cached_value = cache.get(namespace, request_data)
            if cached_value:
                return cached_value
            
            # Cache miss - execute function
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if isinstance(result, tuple):
                response, status = result if len(result) == 2 else (result[0], result[1])
                if status == 200:
                    # Extract data to cache
                    response_data = response.get_json() if hasattr(response, 'get_json') else response
                    cache.set(
                        namespace=namespace,
                        data=request_data,
                        value=response_data,
                        ttl=ttl,
                        promote_to_hot=promote_to_hot
                    )
            
            return result
        
        return wrapper
    return multi_layer_cached_decorator
