"""
Authentication and Authorization Module
JWT-based authentication with API key management
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from typing import Optional, Dict, Tuple
from dataclasses import dataclass
from structured_logging import get_logger

logger = get_logger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_urlsafe(32))
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24
API_KEY_HEADER = 'X-API-Key'
AUTH_HEADER = 'Authorization'


@dataclass
class User:
    """User model"""
    user_id: str
    email: Optional[str] = None
    role: str = 'user'  # user, admin
    api_key_hash: Optional[str] = None
    quota_tier: str = 'free'  # free, basic, premium
    created_at: Optional[datetime] = None
    metadata: Optional[Dict] = None


class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self):
        self.api_keys = {}  # In-memory store (use database in production)
        self.users = {}     # In-memory store (use database in production)
        
        # Load or create admin API key
        self._initialize_admin_key()
    
    def _initialize_admin_key(self):
        """Initialize admin API key from environment or generate new one"""
        admin_key = os.getenv('ADMIN_API_KEY')
        
        if not admin_key:
            admin_key = f"sk_admin_{secrets.token_urlsafe(32)}"
            logger.warning(
                f"No ADMIN_API_KEY found. Generated new admin key: {admin_key}\n"
                f"SAVE THIS KEY! Add to .env: ADMIN_API_KEY={admin_key}"
            )
        
        admin_key_hash = self._hash_api_key(admin_key)
        
        # Create admin user
        admin_user = User(
            user_id='admin',
            email=os.getenv('ADMIN_EMAIL', 'admin@KNOWALLEDGE.local'),
            role='admin',
            api_key_hash=admin_key_hash,
            quota_tier='unlimited',
            created_at=datetime.now(),
            metadata={'is_system_admin': True}
        )
        
        self.users['admin'] = admin_user
        self.api_keys[admin_key_hash] = admin_user
        
        logger.info("Admin user initialized")
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def generate_api_key(self, user_id: str, role: str = 'user', quota_tier: str = 'free') -> str:
        """
        Generate new API key for user
        
        Args:
            user_id: Unique user identifier
            role: User role (user, admin)
            quota_tier: Quota tier (free, basic, premium, unlimited)
        
        Returns:
            API key string (starts with sk_)
        """
        # Generate secure API key
        api_key = f"sk_{secrets.token_urlsafe(32)}"
        api_key_hash = self._hash_api_key(api_key)
        
        # Create user
        user = User(
            user_id=user_id,
            role=role,
            api_key_hash=api_key_hash,
            quota_tier=quota_tier,
            created_at=datetime.now()
        )
        
        self.users[user_id] = user
        self.api_keys[api_key_hash] = user
        
        logger.info(f"Generated API key for user: {user_id}")
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[User]]:
        """
        Validate API key
        
        Args:
            api_key: API key to validate
        
        Returns:
            Tuple of (is_valid, user)
        """
        if not api_key:
            return False, None
        
        api_key_hash = self._hash_api_key(api_key)
        user = self.api_keys.get(api_key_hash)
        
        if user:
            logger.debug(f"Valid API key for user: {user.user_id}")
            return True, user
        
        logger.warning("Invalid API key attempted")
        return False, None
    
    def generate_jwt_token(self, user: User, expires_in_hours: int = JWT_EXPIRATION_HOURS) -> str:
        """
        Generate JWT token for user
        
        Args:
            user: User object
            expires_in_hours: Token expiration time
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user.user_id,
            'role': user.role,
            'quota_tier': user.quota_tier,
            'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        logger.info(f"Generated JWT token for user: {user.user_id}")
        
        return token
    
    def validate_jwt_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate JWT token
        
        Args:
            token: JWT token to validate
        
        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return True, payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None
    
    def get_user_from_request(self, request_obj) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Extract and validate user from request
        
        Supports two authentication methods:
        1. API Key (X-API-Key header)
        2. JWT Token (Authorization: Bearer <token>)
        
        Args:
            request_obj: Flask request object
        
        Returns:
            Tuple of (is_authenticated, user, error_message)
        """
        # Method 1: API Key authentication
        api_key = request_obj.headers.get(API_KEY_HEADER)
        if api_key:
            is_valid, user = self.validate_api_key(api_key)
            if is_valid:
                return True, user, None
            return False, None, "Invalid API key"
        
        # Method 2: JWT Token authentication
        auth_header = request_obj.headers.get(AUTH_HEADER)
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            is_valid, payload = self.validate_jwt_token(token)
            
            if is_valid:
                user_id = payload.get('user_id')
                user = self.users.get(user_id)
                
                if user:
                    return True, user, None
                return False, None, "User not found"
            
            return False, None, "Invalid or expired token"
        
        return False, None, "No authentication credentials provided"
    
    def require_role(self, required_role: str):
        """
        Decorator to require specific role
        
        Args:
            required_role: Required role (user, admin)
        """
        def require_role_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                user = getattr(g, 'user', None)
                
                if not user:
                    return jsonify({
                        "error": "Unauthorized",
                        "message": "Authentication required"
                    }), 401
                
                if user.role != required_role and user.role != 'admin':
                    return jsonify({
                        "error": "Forbidden",
                        "message": f"Role '{required_role}' required"
                    }), 403
                
                return func(*args, **kwargs)
            
            return wrapper
        return require_role_decorator


# Global auth manager instance
auth_manager = AuthManager()


def require_auth(optional: bool = False):
    """
    Authentication decorator for routes
    
    Args:
        optional: If True, doesn't reject unauthenticated requests
                 but still sets g.user if credentials provided
    
    Usage:
        @app.route('/api/endpoint')
        @require_auth()
        def endpoint():
            user = g.user  # Access authenticated user
    """
    def require_auth_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_authenticated, user, error = auth_manager.get_user_from_request(request)
            
            if is_authenticated:
                # Store user in Flask g object
                g.user = user
                g.user_id = user.user_id
                g.user_role = user.role
                g.quota_tier = user.quota_tier
                
                logger.debug(f"Authenticated request from user: {user.user_id}")
                
                return func(*args, **kwargs)
            
            # If authentication failed
            if optional:
                # Set guest user context
                g.user = None
                g.user_id = 'anonymous'
                g.user_role = 'guest'
                g.quota_tier = 'limited'
                
                return func(*args, **kwargs)
            
            # Authentication required but failed
            logger.warning(f"Unauthorized access attempt: {error}")
            
            return jsonify({
                "error": "Unauthorized",
                "message": error or "Authentication required",
                "hint": "Provide X-API-Key header or Authorization: Bearer <token>"
            }), 401
        
        return wrapper
    return require_auth_decorator


def require_admin():
    """
    Decorator to require admin role
    
    Usage:
        @app.route('/api/admin/endpoint')
        @require_auth()
        @require_admin()
        def admin_endpoint():
            pass
    """
    def require_admin_decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'user', None)
            
            if not user:
                return jsonify({
                    "error": "Unauthorized",
                    "message": "Authentication required"
                }), 401
            
            if user.role != 'admin':
                return jsonify({
                    "error": "Forbidden",
                    "message": "Admin role required"
                }), 403
            
            return func(*args, **kwargs)
        
        return wrapper
    return require_admin_decorator


def get_current_user() -> Optional[User]:
    """Get currently authenticated user from Flask g object"""
    return getattr(g, 'user', None)


def get_user_quota_tier() -> str:
    """Get current user's quota tier"""
    return getattr(g, 'quota_tier', 'limited')


# Quota tier limits
QUOTA_LIMITS = {
    'limited': {  # Anonymous/guest users
        'rpm': 5,
        'rpd': 50,
        'tpm': 10000,
        'tpd': 100000
    },
    'free': {  # Free registered users
        'rpm': 10,
        'rpd': 100,
        'tpm': 50000,
        'tpd': 500000
    },
    'basic': {  # Basic paid users
        'rpm': 15,
        'rpd': 500,
        'tpm': 200000,
        'tpd': 2000000
    },
    'premium': {  # Premium paid users
        'rpm': 30,
        'rpd': 2000,
        'tpm': 1000000,
        'tpd': 10000000
    },
    'unlimited': {  # Admin users
        'rpm': 1000,
        'rpd': 100000,
        'tpm': 10000000,
        'tpd': 100000000
    }
}


def get_user_quota_limits() -> Dict[str, int]:
    """Get quota limits for current user's tier"""
    tier = get_user_quota_tier()
    return QUOTA_LIMITS.get(tier, QUOTA_LIMITS['limited'])
