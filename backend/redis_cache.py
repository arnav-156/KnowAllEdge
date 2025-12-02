"""
Redis Cache Implementation
Thread-safe caching with Redis backend
Enhanced with pattern invalidation, cache warming, and comprehensive stats
"""

import json
import hashlib
from typing import Optional, Any, List, Dict, Callable
from functools import wraps
import time
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Warning: redis-py not installed. Using in-memory cache fallback.")

from structured_logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Redis-based cache with fallback to in-memory cache
    
    Features:
    - Pattern-based invalidation with versioning
    - Automatic memory cleanup with background thread
    - Cache warming for popular topics
    - Comprehensive statistics with hit rate and latency tracking
    """
    
    def __init__(self, config):
        """Initialize Redis cache or fallback to in-memory"""
        self.config = config
        self.redis_client = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.cache_version = "v1.0"  # Version for invalidation strategy
        
        # Enhanced statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'invalidations': 0,
            'total_latency_ms': 0.0,
            'operations': 0
        }
        
        # Popular topics for cache warming (Top 100)
        self.popular_topics = [
            # Programming Languages (20)
            "Python Programming",
            "JavaScript",
            "Java Programming",
            "C++ Programming",
            "C Programming",
            "C# Programming",
            "Go Programming",
            "Rust Programming",
            "TypeScript",
            "PHP Programming",
            "Ruby Programming",
            "Swift Programming",
            "Kotlin Programming",
            "R Programming",
            "MATLAB",
            "SQL Programming",
            "Scala Programming",
            "Perl Programming",
            "Dart Programming",
            "Assembly Language",
            
            # Web Development (15)
            "Web Development",
            "Frontend Development",
            "Backend Development",
            "Full Stack Development",
            "React",
            "Angular",
            "Vue.js",
            "Node.js",
            "Django",
            "Flask",
            "Spring Boot",
            "ASP.NET",
            "REST API",
            "GraphQL",
            "Web Security",
            
            # Data Science & AI (15)
            "Machine Learning",
            "Artificial Intelligence",
            "Deep Learning",
            "Neural Networks",
            "Natural Language Processing",
            "Computer Vision",
            "Data Science",
            "Data Analytics",
            "Big Data",
            "TensorFlow",
            "PyTorch",
            "Keras",
            "Scikit-learn",
            "Pandas",
            "NumPy",
            
            # Computer Science Fundamentals (15)
            "Data Structures",
            "Algorithms",
            "Operating Systems",
            "Computer Networks",
            "Database Management",
            "Computer Architecture",
            "Compiler Design",
            "Theory of Computation",
            "Discrete Mathematics",
            "Linear Algebra",
            "Probability and Statistics",
            "Calculus",
            "Software Engineering",
            "Design Patterns",
            "Object Oriented Programming",
            
            # Mobile & Cloud (10)
            "Android Development",
            "iOS Development",
            "React Native",
            "Flutter",
            "Cloud Computing",
            "AWS",
            "Azure",
            "Google Cloud",
            "Docker",
            "Kubernetes",
            
            # DevOps & Tools (10)
            "DevOps",
            "Git Version Control",
            "CI/CD",
            "Jenkins",
            "Linux Administration",
            "Shell Scripting",
            "Ansible",
            "Terraform",
            "Monitoring and Logging",
            "Microservices",
            
            # Security & Blockchain (10)
            "Cybersecurity",
            "Ethical Hacking",
            "Cryptography",
            "Network Security",
            "Blockchain",
            "Smart Contracts",
            "Penetration Testing",
            "Security Testing",
            "OAuth and Authentication",
            "GDPR and Compliance",
            
            # Emerging Technologies (5)
            "Internet of Things",
            "Edge Computing",
            "Quantum Computing",
            "Augmented Reality",
            "Virtual Reality"
        ]
        
        # Start cleanup thread for memory cache
        self.cleanup_thread = None
        self._stop_cleanup = threading.Event()
        
        if config.redis.enabled and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=config.redis.host,
                    port=config.redis.port,
                    db=config.redis.db,
                    password=config.redis.password,
                    socket_timeout=config.redis.socket_timeout,
                    socket_connect_timeout=config.redis.socket_connect_timeout,
                    max_connections=config.redis.max_connections,
                    decode_responses=True  # Return strings instead of bytes
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully", extra={
                    'host': config.redis.host,
                    'port': config.redis.port,
                    'version': self.cache_version
                })
            except Exception as e:
                logger.warning("Redis connection failed, using in-memory cache", extra={
                    'error': str(e)
                })
                self.redis_client = None
        else:
            logger.info("Using in-memory cache (Redis disabled or unavailable)")
        
        # Start background cleanup for memory cache
        if not self.redis_client:
            self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background thread for memory cache cleanup"""
        def cleanup_worker():
            while not self._stop_cleanup.is_set():
                try:
                    self._clean_memory_cache()
                    # Run every 60 seconds
                    self._stop_cleanup.wait(60)
                except Exception as e:
                    logger.error("Cleanup thread error", extra={'error': str(e)})
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        logger.info("Memory cache cleanup thread started")
    
    def _generate_key(self, endpoint: str, data: dict) -> str:
        """Generate versioned cache key from endpoint and data"""
        cache_str = f"{self.cache_version}:{endpoint}:{json.dumps(data, sort_keys=True)}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with latency tracking"""
        start_time = time.time()
        
        try:
            if self.redis_client:
                # Get from Redis
                value = self.redis_client.get(key)
                if value:
                    self.stats['hits'] += 1
                    self._track_latency(start_time)
                    return json.loads(value)
                else:
                    self.stats['misses'] += 1
            else:
                # Get from memory cache
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    if time.time() - entry['timestamp'] < self.config.cache.ttl:
                        self.stats['hits'] += 1
                        self._track_latency(start_time)
                        return entry['data']
                    else:
                        # Expired, remove it
                        del self.memory_cache[key]
                        self.stats['misses'] += 1
                else:
                    self.stats['misses'] += 1
            
            return None
        except Exception as e:
            logger.error("Cache get error", extra={'key': key, 'error': str(e)})
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL and latency tracking"""
        start_time = time.time()
        
        try:
            ttl = ttl or self.config.cache.ttl
            
            if self.redis_client:
                # Set in Redis with expiration
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
            else:
                # Set in memory cache
                self.memory_cache[key] = {
                    'data': value,
                    'timestamp': time.time()
                }
                # Note: Cleanup is now handled by background thread
            
            self.stats['sets'] += 1
            self._track_latency(start_time)
            return True
        except Exception as e:
            logger.error("Cache set error", extra={'key': key, 'error': str(e)})
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            
            self.stats['deletes'] += 1
            return True
        except Exception as e:
            logger.error("Cache delete error", extra={'key': key, 'error': str(e)})
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern (HIGH priority fix)
        
        Args:
            pattern: Pattern to match (e.g., "v1.0:subtopics:*")
        
        Returns:
            Number of keys deleted
        """
        deleted_count = 0
        
        try:
            if self.redis_client:
                # Use SCAN for safe pattern matching in production
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(cursor, match=pattern, count=100)
                    if keys:
                        deleted_count += self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Memory cache pattern matching
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if self._matches_pattern(k, pattern)
                ]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                deleted_count = len(keys_to_delete)
            
            self.stats['invalidations'] += deleted_count
            logger.info("Pattern-based deletion", extra={
                'pattern': pattern,
                'deleted': deleted_count
            })
            
            return deleted_count
        except Exception as e:
            logger.error("Pattern delete error", extra={
                'pattern': pattern,
                'error': str(e)
            })
            return 0
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple wildcard pattern matching for memory cache"""
        if '*' not in pattern:
            return key == pattern
        
        # Convert wildcard pattern to regex-like matching
        parts = pattern.split('*')
        pos = 0
        for part in parts:
            if not part:
                continue
            idx = key.find(part, pos)
            if idx == -1:
                return False
            pos = idx + len(part)
        
        return True
    
    def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidate all entries in a namespace (HIGH priority fix)
        
        Args:
            namespace: Namespace to invalidate (e.g., "subtopics")
        
        Returns:
            Number of keys invalidated
        """
        pattern = f"{self.cache_version}:{namespace}:*"
        return self.delete_pattern(pattern)
    
    def invalidate_version(self, old_version: str) -> int:
        """
        Invalidate all entries with specific version
        
        Args:
            old_version: Version to invalidate
        
        Returns:
            Number of keys invalidated
        """
        pattern = f"{old_version}:*"
        return self.delete_pattern(pattern)
    
    def update_version(self, new_version: str) -> None:
        """
        Update cache version (invalidates all existing caches)
        
        Args:
            new_version: New version string
        """
        old_version = self.cache_version
        
        # Delete old version entries
        self.invalidate_version(old_version)
        
        # Update version
        self.cache_version = new_version
        
        logger.info("Cache version updated", extra={
            'old_version': old_version,
            'new_version': new_version
        })
    
    def clear(self) -> bool:
        """Clear all cache entries"""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
            else:
                self.memory_cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error("Cache clear error", extra={'error': str(e)})
            return False
    
    def _clean_memory_cache(self):
        """Remove expired entries from memory cache (MEDIUM priority fix)"""
        if not self.memory_cache:
            return
        
        current_time = time.time()
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if current_time - v['timestamp'] > self.config.cache.ttl
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Also enforce max size by removing oldest entries
        if len(self.memory_cache) > self.config.cache.max_size:
            # Sort by timestamp and remove oldest
            sorted_keys = sorted(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]['timestamp']
            )
            
            num_to_remove = len(self.memory_cache) - self.config.cache.max_size
            for key in sorted_keys[:num_to_remove]:
                del self.memory_cache[key]
        
        if expired_keys:
            logger.debug("Memory cache cleaned", extra={
                'expired': len(expired_keys),
                'current_size': len(self.memory_cache)
            })
    
    def warm_cache(self, warmup_functions: Dict[str, Callable]) -> int:
        """
        Warm cache with popular topics (MEDIUM priority fix)
        
        Args:
            warmup_functions: Dict of {namespace: function} to generate cache data
                             Function should accept topic string and return cacheable data
        
        Returns:
            Number of entries warmed
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
                    key = self._generate_key(namespace, data)
                    
                    # Skip if already cached
                    if self.get(key):
                        continue
                    
                    # Generate value
                    value = warmup_func(topic)
                    
                    if value:
                        # Cache with default TTL
                        self.set(key, value)
                        warmed_count += 1
                
                except Exception as e:
                    logger.error("Cache warming error", extra={
                        'topic': topic,
                        'namespace': namespace,
                        'error': str(e)
                    })
        
        logger.info("Cache warming complete", extra={
            'warmed_entries': warmed_count,
            'cache_size': len(self.memory_cache) if not self.redis_client else 'redis'
        })
        
        return warmed_count
    
    def _track_latency(self, start_time: float):
        """Track operation latency (LOW priority fix)"""
        latency_ms = (time.time() - start_time) * 1000
        self.stats['total_latency_ms'] += latency_ms
        self.stats['operations'] += 1
    
    def get_stats(self) -> dict:
        """Get comprehensive cache statistics (LOW priority fix)"""
        try:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = 0.0
            avg_latency_ms = 0.0
            
            if total_requests > 0:
                hit_rate = (self.stats['hits'] / total_requests) * 100
            
            if self.stats['operations'] > 0:
                avg_latency_ms = self.stats['total_latency_ms'] / self.stats['operations']
            
            if self.redis_client:
                try:
                    info = self.redis_client.info('stats')
                    memory_info = self.redis_client.info('memory')
                    
                    return {
                        'type': 'redis',
                        'version': self.cache_version,
                        'hits': self.stats['hits'],
                        'misses': self.stats['misses'],
                        'hit_rate_percent': round(hit_rate, 2),
                        'total_requests': total_requests,
                        'sets': self.stats['sets'],
                        'deletes': self.stats['deletes'],
                        'invalidations': self.stats['invalidations'],
                        'avg_latency_ms': round(avg_latency_ms, 2),
                        'keys': self.redis_client.dbsize(),
                        'memory_used_mb': round(memory_info.get('used_memory', 0) / 1024 / 1024, 2),
                        'redis_stats': {
                            'keyspace_hits': info.get('keyspace_hits', 0),
                            'keyspace_misses': info.get('keyspace_misses', 0),
                            'evicted_keys': info.get('evicted_keys', 0)
                        }
                    }
                except Exception as e:
                    logger.error("Redis stats error", extra={'error': str(e)})
                    # Fallback to basic stats
                    return {
                        'type': 'redis',
                        'version': self.cache_version,
                        'hits': self.stats['hits'],
                        'misses': self.stats['misses'],
                        'hit_rate_percent': round(hit_rate, 2),
                        'error': str(e)
                    }
            else:
                return {
                    'type': 'memory',
                    'version': self.cache_version,
                    'hits': self.stats['hits'],
                    'misses': self.stats['misses'],
                    'hit_rate_percent': round(hit_rate, 2),
                    'total_requests': total_requests,
                    'sets': self.stats['sets'],
                    'deletes': self.stats['deletes'],
                    'invalidations': self.stats['invalidations'],
                    'avg_latency_ms': round(avg_latency_ms, 2),
                    'keys': len(self.memory_cache),
                    'max_size': self.config.cache.max_size,
                    'cleanup_thread_alive': self.cleanup_thread.is_alive() if self.cleanup_thread else False
                }
        except Exception as e:
            logger.error("Cache stats error", extra={'error': str(e)})
            return {'error': str(e)}
    
    def health_check(self) -> dict:
        """Check cache health"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return {
                    'status': 'healthy',
                    'type': 'redis',
                    'connected': True,
                    'version': self.cache_version
                }
            else:
                return {
                    'status': 'healthy',
                    'type': 'memory',
                    'connected': True,
                    'version': self.cache_version,
                    'cleanup_thread': self.cleanup_thread.is_alive() if self.cleanup_thread else False
                }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connected': False
            }
    
    def shutdown(self):
        """Gracefully shutdown cache (cleanup threads)"""
        if self.cleanup_thread:
            self._stop_cleanup.set()
            self.cleanup_thread.join(timeout=2)
            logger.info("Cache cleanup thread stopped")
        
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error("Error closing Redis", extra={'error': str(e)})


def cached_response(cache: RedisCache, ttl: Optional[int] = None):
    """Decorator for caching API responses using RedisCache"""
    def cached_response_decorator_redis(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from flask import request
            
            # Generate cache key
            request_data = request.get_json() or {}
            cache_key = cache._generate_key(f.__name__, request_data)
            
            # Try to get from cache
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info("Cache hit", extra={'endpoint': f.__name__, 'key': cache_key[:16]})
                return cached_data
            
            # Cache miss - execute function
            logger.info("Cache miss", extra={'endpoint': f.__name__, 'key': cache_key[:16]})
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if isinstance(result, tuple):
                response, status = result if len(result) == 2 else (result[0], result[1])
                if status == 200:
                    cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return cached_response_decorator_redis

