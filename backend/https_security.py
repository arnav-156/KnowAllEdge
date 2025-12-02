"""
HTTPS Security Module
Enforces HTTPS and adds security headers
"""

from functools import wraps
from flask import request, redirect, make_response
from structured_logging import get_logger

logger = get_logger(__name__)


class HTTPSSecurityManager:
    """
    Manages HTTPS enforcement and security headers
    
    Features:
    - HTTPS redirect
    - Strict Transport Security (HSTS)
    - Content Security Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - X-XSS-Protection
    """
    
    def __init__(self, app=None, force_https: bool = True):
        """
        Initialize HTTPS security manager
        
        Args:
            app: Flask app instance
            force_https: If True, redirects HTTP to HTTPS
        """
        self.force_https = force_https
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize Flask app with security settings
        
        Args:
            app: Flask app instance
        """
        self.app = app
        
        # Register before_request handler for HTTPS redirect
        app.before_request(self._enforce_https)
        
        # Register after_request handler for security headers
        app.after_request(self._add_security_headers)
        
        logger.info("HTTPS security manager initialized")
    
    def _enforce_https(self):
        """Enforce HTTPS by redirecting HTTP requests"""
        # Skip HTTPS enforcement in development
        if not self.force_https:
            return
        
        # Skip for localhost (development)
        if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
            return
        
        # Check if request is HTTPS
        if request.scheme != 'https':
            # Redirect to HTTPS
            url = request.url.replace('http://', 'https://', 1)
            logger.info(f"Redirecting to HTTPS: {url}")
            return redirect(url, code=301)
    
    def _add_security_headers(self, response):
        """
        Add security headers to response
        
        Args:
            response: Flask response object
        
        Returns:
            Modified response with security headers
        """
        # Strict Transport Security (HSTS)
        # Forces HTTPS for 1 year, includes subdomains
        if self.force_https:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy (CSP)
        # Prevents XSS attacks by restricting resource loading
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://generativelanguage.googleapis.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # X-Frame-Options
        # Prevents clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection
        # Enables browser XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer-Policy
        # Controls referrer information
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy (formerly Feature-Policy)
        # Controls browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), payment=()'
        )
        
        # X-Permitted-Cross-Domain-Policies
        # Restricts Adobe Flash/PDF cross-domain access
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
        
        return response


def require_https():
    """
    Decorator to enforce HTTPS on specific routes
    
    Usage:
        @app.route('/api/sensitive')
        @require_https()
        def sensitive_endpoint():
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip for localhost (development)
            if request.host.startswith('localhost') or request.host.startswith('127.0.0.1'):
                return func(*args, **kwargs)
            
            # Check if request is HTTPS
            if request.scheme != 'https':
                # Return error
                return {
                    "error": "HTTPS Required",
                    "message": "This endpoint requires HTTPS"
                }, 426  # 426 Upgrade Required
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def get_client_ip() -> str:
    """
    Get client IP address (handles proxies)
    
    Returns:
        Client IP address
    """
    # Check for X-Forwarded-For header (behind proxy/load balancer)
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    
    # Check for X-Real-IP header (nginx)
    if request.headers.get('X-Real-IP'):
        return request.headers['X-Real-IP']
    
    # Use remote address
    return request.remote_addr or 'unknown'


def is_secure_request() -> bool:
    """Check if current request is secure (HTTPS)"""
    return request.scheme == 'https' or request.is_secure


def add_cors_headers(response, origins: list = None):
    """
    Add CORS headers to response
    
    Args:
        response: Flask response object
        origins: Allowed origins (None = use default)
    
    Returns:
        Modified response with CORS headers
    """
    if origins is None:
        # Default allowed origins (update for production)
        origins = [
            'http://localhost:5173',
            'http://localhost:3000',
            'https://KNOWALLEDGE.com',  # Add your production domain
        ]
    
    origin = request.headers.get('Origin')
    
    if origin in origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = (
            'Content-Type, Authorization, X-API-Key, X-Request-ID'
        )
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    
    return response


def validate_content_type(allowed_types: list = None):
    """
    Decorator to validate Content-Type header
    
    Args:
        allowed_types: List of allowed MIME types
    
    Usage:
        @app.route('/api/upload')
        @validate_content_type(['application/json', 'multipart/form-data'])
        def upload_endpoint():
            pass
    """
    if allowed_types is None:
        allowed_types = ['application/json']
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            content_type = request.headers.get('Content-Type', '')
            
            # Extract base content type (ignore charset)
            base_type = content_type.split(';')[0].strip()
            
            if base_type not in allowed_types:
                return {
                    "error": "Invalid Content-Type",
                    "message": f"Expected one of: {', '.join(allowed_types)}",
                    "received": base_type
                }, 415  # 415 Unsupported Media Type
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_by_ip(max_requests: int = 100, window_seconds: int = 60):
    """
    Simple IP-based rate limiting decorator
    
    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
    
    Usage:
        @app.route('/api/endpoint')
        @rate_limit_by_ip(max_requests=10, window_seconds=60)
        def endpoint():
            pass
    """
    from collections import defaultdict
    from time import time
    
    # In-memory storage (use Redis in production)
    request_counts = defaultdict(list)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_ip = get_client_ip()
            current_time = time()
            
            # Clean old requests
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip]
                if current_time - req_time < window_seconds
            ]
            
            # Check rate limit
            if len(request_counts[client_ip]) >= max_requests:
                return {
                    "error": "Rate Limit Exceeded",
                    "message": f"Maximum {max_requests} requests per {window_seconds} seconds",
                    "retry_after": window_seconds
                }, 429  # 429 Too Many Requests
            
            # Record request
            request_counts[client_ip].append(current_time)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Security audit utilities
def audit_request():
    """Log security-relevant request information"""
    logger.info(
        "Request audit",
        extra={
            'ip': get_client_ip(),
            'method': request.method,
            'path': request.path,
            'user_agent': request.headers.get('User-Agent'),
            'referer': request.headers.get('Referer'),
            'is_secure': is_secure_request()
        }
    )


def check_security_headers(response) -> dict:
    """
    Check if response has security headers
    
    Args:
        response: Flask response object
    
    Returns:
        Dictionary of header presence
    """
    required_headers = [
        'Strict-Transport-Security',
        'Content-Security-Policy',
        'X-Frame-Options',
        'X-Content-Type-Options',
        'X-XSS-Protection'
    ]
    
    return {
        header: header in response.headers
        for header in required_headers
    }
