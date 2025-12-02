"""
Distributed Session Management for Horizontal Scaling
Provides Redis-backed session storage for stateless application instances
"""

import os
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from flask import request, g
import redis

class DistributedSessionManager:
    """
    Redis-backed session manager for horizontal scaling
    Ensures stateless application instances can share session data
    """
    
    def __init__(self, redis_config):
        """
        Initialize distributed session manager
        
        Args:
            redis_config: RedisConfig instance with connection settings
        """
        self.enabled = redis_config.enabled
        self.session_ttl = 86400  # 24 hours
        self.redis_client = None
        self.session_prefix = "session:"
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.host,
                    port=redis_config.port,
                    db=redis_config.db,
                    password=redis_config.password,
                    decode_responses=True,
                    socket_timeout=redis_config.socket_timeout,
                    socket_connect_timeout=redis_config.socket_connect_timeout,
                    max_connections=redis_config.max_connections
                )
                # Test connection
                self.redis_client.ping()
                print(f"✅ Distributed session manager connected to Redis at {redis_config.host}:{redis_config.port}")
            except Exception as e:
                print(f"⚠️  Redis connection failed for sessions: {e}")
                print("   Falling back to in-memory sessions (NOT suitable for production!)")
                self.enabled = False
                self._fallback_sessions = {}  # Local fallback (NOT for production)
    
    def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict] = None) -> str:
        """
        Create a new session
        
        Args:
            user_id: Optional user identifier
            metadata: Additional session metadata
            
        Returns:
            Session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id or 'anonymous',
            'created_at': datetime.utcnow().isoformat(),
            'last_accessed': datetime.utcnow().isoformat(),
            'metadata': metadata or {},
            'request_count': 0
        }
        
        if self.enabled and self.redis_client:
            try:
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session_data)
                )
            except Exception as e:
                print(f"⚠️  Failed to store session in Redis: {e}")
                self._fallback_sessions[session_id] = session_data
        else:
            self._fallback_sessions[session_id] = session_data
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        if not session_id:
            return None
        
        if self.enabled and self.redis_client:
            try:
                key = f"{self.session_prefix}{session_id}"
                data = self.redis_client.get(key)
                if data:
                    session_data = json.loads(data)
                    # Update last accessed time
                    session_data['last_accessed'] = datetime.utcnow().isoformat()
                    session_data['request_count'] = session_data.get('request_count', 0) + 1
                    self.redis_client.setex(key, self.session_ttl, json.dumps(session_data))
                    return session_data
            except Exception as e:
                print(f"⚠️  Failed to retrieve session from Redis: {e}")
                # Fall back to local cache
                return self._fallback_sessions.get(session_id)
        else:
            return self._fallback_sessions.get(session_id)
        
        return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        
        # Update fields
        for key, value in updates.items():
            if key == 'metadata':
                session_data['metadata'].update(value)
            else:
                session_data[key] = value
        
        session_data['last_accessed'] = datetime.utcnow().isoformat()
        
        if self.enabled and self.redis_client:
            try:
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.setex(
                    key,
                    self.session_ttl,
                    json.dumps(session_data)
                )
                return True
            except Exception as e:
                print(f"⚠️  Failed to update session in Redis: {e}")
                self._fallback_sessions[session_id] = session_data
                return True
        else:
            self._fallback_sessions[session_id] = session_data
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        if self.enabled and self.redis_client:
            try:
                key = f"{self.session_prefix}{session_id}"
                self.redis_client.delete(key)
                return True
            except Exception as e:
                print(f"⚠️  Failed to delete session from Redis: {e}")
                if session_id in self._fallback_sessions:
                    del self._fallback_sessions[session_id]
                return False
        else:
            if session_id in self._fallback_sessions:
                del self._fallback_sessions[session_id]
            return True
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> tuple[str, Dict[str, Any]]:
        """
        Get existing session or create new one
        
        Args:
            session_id: Optional existing session ID
            
        Returns:
            Tuple of (session_id, session_data)
        """
        if session_id:
            session_data = self.get_session(session_id)
            if session_data:
                return session_id, session_data
        
        # Create new session
        new_session_id = self.create_session()
        session_data = self.get_session(new_session_id)
        return new_session_id, session_data
    
    def get_active_session_count(self) -> int:
        """
        Get count of active sessions across all instances
        
        Returns:
            Number of active sessions
        """
        if self.enabled and self.redis_client:
            try:
                keys = self.redis_client.keys(f"{self.session_prefix}*")
                return len(keys)
            except Exception as e:
                print(f"⚠️  Failed to count sessions: {e}")
                return len(self._fallback_sessions)
        else:
            return len(self._fallback_sessions)
    
    def cleanup_expired_sessions(self) -> int:
        """
        Manually cleanup expired sessions (Redis handles this automatically)
        
        Returns:
            Number of sessions cleaned up
        """
        if self.enabled and self.redis_client:
            # Redis handles TTL automatically
            return 0
        else:
            # Manual cleanup for fallback
            now = datetime.utcnow()
            expired = []
            
            for session_id, session_data in self._fallback_sessions.items():
                last_accessed = datetime.fromisoformat(session_data['last_accessed'])
                if (now - last_accessed).total_seconds() > self.session_ttl:
                    expired.append(session_id)
            
            for session_id in expired:
                del self._fallback_sessions[session_id]
            
            return len(expired)


def session_middleware(session_manager: DistributedSessionManager):
    """
    Flask middleware for automatic session management
    Attaches session to request context (g object)
    
    Args:
        session_manager: DistributedSessionManager instance
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get session ID from cookie or header
            session_id = request.cookies.get('session_id') or request.headers.get('X-Session-ID')
            
            # Get or create session
            session_id, session_data = session_manager.get_or_create_session(session_id)
            
            # Attach to request context (g object is request-scoped, safe for multi-threading)
            g.session_id = session_id
            g.session = session_data
            
            # Execute route handler
            response = f(*args, **kwargs)
            
            # Add session ID to response headers (client can store in cookie)
            if hasattr(response, 'headers'):
                response.headers['X-Session-ID'] = session_id
            
            return response
        
        return decorated_function
    return decorator


def require_session(f):
    """
    Decorator to require valid session for endpoint
    Use after @session_middleware
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'session') or not g.session:
            return jsonify({
                'success': False,
                'error': 'Valid session required'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


# Singleton instance
_session_manager_instance = None

def get_session_manager(config=None) -> DistributedSessionManager:
    """
    Get singleton session manager instance
    
    Args:
        config: Config instance (required on first call)
        
    Returns:
        DistributedSessionManager instance
    """
    global _session_manager_instance
    
    if _session_manager_instance is None:
        if config is None:
            raise ValueError("Config required for first initialization")
        _session_manager_instance = DistributedSessionManager(config.redis)
    
    return _session_manager_instance
