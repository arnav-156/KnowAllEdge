"""
CSRF Protection Module
Provides CSRF token generation and validation for Flask
Requirements: 5.3 - Implement CSRF protection
"""

import secrets
import hmac
import hashlib
from functools import wraps
from flask import request, jsonify, session
from typing import Optional, Tuple


class CSRFProtection:
    """CSRF protection handler"""
    
    def __init__(self, secret_key: str):
        """
        Initialize CSRF protection
        
        Args:
            secret_key: Secret key for HMAC signing
        """
        self.secret_key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self.token_length = 32
        self.header_name = 'X-CSRF-Token'
        self.session_key = 'csrf_token'
    
    def generate_token(self) -> str:
        """
        Generate a new CSRF token
        
        Returns:
            CSRF token string
        """
        # Generate random token
        token = secrets.token_hex(self.token_length)
        
        # Sign token with HMAC
        signature = hmac.new(
            self.secret_key,
            token.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine token and signature
        return f"{token}.{signature}"
    
    def validate_token(self, token: str) -> bool:
        """
        Validate a CSRF token
        
        Args:
            token: CSRF token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        if not token:
            return False
        
        try:
            # Split token and signature
            parts = token.split('.')
            if len(parts) != 2:
                return False
            
            token_value, signature = parts
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key,
                token_value.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Use constant-time comparison
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            print(f"CSRF validation error: {e}")
            return False
    
    def get_token_from_request(self) -> Optional[str]:
        """
        Extract CSRF token from request
        
        Returns:
            CSRF token or None if not found
        """
        # Check header first
        token = request.headers.get(self.header_name)
        if token:
            return token
        
        # Check form data
        token = request.form.get('csrf_token')
        if token:
            return token
        
        # Check JSON body
        if request.is_json:
            data = request.get_json(silent=True)
            if data and 'csrf_token' in data:
                return data['csrf_token']
        
        return None
    
    def get_session_token(self) -> Optional[str]:
        """
        Get CSRF token from session
        
        Returns:
            CSRF token or None if not found
        """
        return session.get(self.session_key)
    
    def set_session_token(self, token: str) -> None:
        """
        Store CSRF token in session
        
        Args:
            token: CSRF token to store
        """
        session[self.session_key] = token
    
    def clear_session_token(self) -> None:
        """Clear CSRF token from session"""
        session.pop(self.session_key, None)
    
    def requires_csrf_protection(self, method: str) -> bool:
        """
        Check if HTTP method requires CSRF protection
        
        Args:
            method: HTTP method
            
        Returns:
            True if method requires CSRF protection
        """
        safe_methods = ['GET', 'HEAD', 'OPTIONS', 'TRACE']
        return method.upper() not in safe_methods


def csrf_protect(csrf_handler: CSRFProtection):
    """
    Decorator to protect routes with CSRF validation
    
    Args:
        csrf_handler: CSRFProtection instance
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip CSRF check for safe methods
            if not csrf_handler.requires_csrf_protection(request.method):
                return f(*args, **kwargs)
            
            # Get token from request
            request_token = csrf_handler.get_token_from_request()
            
            # Get token from session
            session_token = csrf_handler.get_session_token()
            
            # Validate tokens
            if not request_token:
                return jsonify({
                    'error': 'CSRF token missing',
                    'error_code': 'CSRF_TOKEN_MISSING',
                    'message': 'CSRF token is required for this request'
                }), 403
            
            if not session_token:
                return jsonify({
                    'error': 'CSRF session invalid',
                    'error_code': 'CSRF_SESSION_INVALID',
                    'message': 'CSRF session token not found'
                }), 403
            
            if not csrf_handler.validate_token(request_token):
                return jsonify({
                    'error': 'Invalid CSRF token',
                    'error_code': 'CSRF_TOKEN_INVALID',
                    'message': 'CSRF token validation failed'
                }), 403
            
            # Verify tokens match
            if not hmac.compare_digest(request_token, session_token):
                return jsonify({
                    'error': 'CSRF token mismatch',
                    'error_code': 'CSRF_TOKEN_MISMATCH',
                    'message': 'CSRF token does not match session'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def create_csrf_token_endpoint(csrf_handler: CSRFProtection):
    """
    Create endpoint to generate and return CSRF token
    
    Args:
        csrf_handler: CSRFProtection instance
        
    Returns:
        Flask route function
    """
    def get_csrf_token():
        """Generate and return CSRF token"""
        # Generate new token
        token = csrf_handler.generate_token()
        
        # Store in session
        csrf_handler.set_session_token(token)
        
        return jsonify({
            'csrf_token': token,
            'header_name': csrf_handler.header_name
        }), 200
    
    return get_csrf_token
