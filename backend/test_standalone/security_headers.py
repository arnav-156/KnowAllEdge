"""
Security Headers Middleware
Adds comprehensive security headers to all HTTP responses
Validates: Requirements 10.1, 10.2, 10.3, 10.5, 10.7
"""

from flask import Flask, request, Response
from functools import wraps
from typing import Dict, Optional
import secrets

from structured_logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware:
    """
    Flask middleware to add security headers to all responses
    
    Features:
    - Content-Security-Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security (HSTS)
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    
    Validates: Requirements 10.1, 10.2, 10.3, 10.5, 10.7
    """
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        csp_policy: Optional[Dict[str, str]] = None,
        enable_hsts: bool = True,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False
    ):
        """
        Initialize security headers middleware
        
        Args:
            app: Flask application instance
            csp_policy: Custom CSP policy directives
            enable_hsts: Enable HSTS header
            hsts_max_age: HSTS max-age in seconds
            hsts_include_subdomains: Include subdomains in HSTS
            hsts_preload: Enable HSTS preload
        """
        self.csp_policy = csp_policy or self._default_csp_policy()
        self.enable_hsts = enable_hsts
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        if app:
            self.init_app(app)
    
    def _default_csp_policy(self) -> Dict[str, str]:
        """
        Get default Content Security Policy
        
        Returns:
            Dictionary of CSP directives
        """
        return {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com",
            'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com",
            'font-src': "'self' https://fonts.gstatic.com",
            'img-src': "'self' data: https: blob:",
            'connect-src': "'self' https://generativelanguage.googleapis.com",
            'frame-ancestors': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'",
            'upgrade-insecure-requests': ''
        }
    
    def _build_csp_header(self, nonce: Optional[str] = None) -> str:
        """
        Build CSP header value from policy directives
        
        Args:
            nonce: Optional nonce for inline scripts
        
        Returns:
            CSP header value string
        """
        policy_parts = []
        
        for directive, value in self.csp_policy.items():
            if value:
                # Add nonce to script-src if provided
                if directive == 'script-src' and nonce:
                    value = f"{value} 'nonce-{nonce}'"
                policy_parts.append(f"{directive} {value}")
            else:
                # Directive with no value (e.g., upgrade-insecure-requests)
                policy_parts.append(directive)
        
        return '; '.join(policy_parts)
    
    def _build_hsts_header(self) -> str:
        """
        Build HSTS header value
        
        Returns:
            HSTS header value string
        """
        parts = [f"max-age={self.hsts_max_age}"]
        
        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")
        
        if self.hsts_preload:
            parts.append("preload")
        
        return "; ".join(parts)
    
    def init_app(self, app: Flask):
        """
        Initialize middleware with Flask app
        
        Args:
            app: Flask application instance
        """
        @app.after_request
        def add_security_headers(response: Response) -> Response:
            """Add security headers to response"""
            
            # Generate nonce for CSP (can be used in templates)
            nonce = secrets.token_urlsafe(16)
            response.headers['X-CSP-Nonce'] = nonce
            
            # Content-Security-Policy (Requirement 10.1)
            csp_value = self._build_csp_header(nonce)
            response.headers['Content-Security-Policy'] = csp_value
            
            # X-Frame-Options (Requirement 10.2)
            response.headers['X-Frame-Options'] = 'DENY'
            
            # X-Content-Type-Options (Requirement 10.5)
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Strict-Transport-Security (Requirement 10.3)
            if self.enable_hsts:
                response.headers['Strict-Transport-Security'] = self._build_hsts_header()
            
            # X-XSS-Protection (legacy, but still useful)
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Referrer-Policy (Requirement 10.7)
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy (formerly Feature-Policy)
            response.headers['Permissions-Policy'] = (
                'geolocation=(), '
                'microphone=(), '
                'camera=(), '
                'payment=(), '
                'usb=(), '
                'magnetometer=(), '
                'gyroscope=(), '
                'accelerometer=()'
            )
            
            # Additional security headers
            response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
            response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
            response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
            response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'
            
            return response
        
        logger.info("Security headers middleware initialized")


class HTTPSRedirector:
    """
    Middleware to redirect HTTP requests to HTTPS
    
    Validates: Requirement 10.4
    """
    
    def __init__(
        self,
        app: Optional[Flask] = None,
        permanent: bool = True,
        skip_paths: Optional[list] = None
    ):
        """
        Initialize HTTPS redirector
        
        Args:
            app: Flask application instance
            permanent: Use 301 (permanent) vs 302 (temporary) redirect
            skip_paths: List of paths to skip HTTPS redirect (e.g., health checks)
        """
        self.permanent = permanent
        self.skip_paths = skip_paths or ['/health', '/metrics']
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """
        Initialize middleware with Flask app
        
        Args:
            app: Flask application instance
        """
        @app.before_request
        def redirect_to_https():
            """Redirect HTTP to HTTPS in production"""
            
            # Skip in development
            if app.config.get('ENV') == 'development':
                return None
            
            # Skip for certain paths
            if request.path in self.skip_paths:
                return None
            
            # Check if request is already HTTPS
            if request.is_secure:
                return None
            
            # Check X-Forwarded-Proto header (for load balancers)
            if request.headers.get('X-Forwarded-Proto', 'http') == 'https':
                return None
            
            # Redirect to HTTPS
            url = request.url.replace('http://', 'https://', 1)
            code = 301 if self.permanent else 302
            
            logger.info(
                "Redirecting HTTP to HTTPS",
                extra={
                    'original_url': request.url,
                    'redirect_url': url,
                    'code': code
                }
            )
            
            from flask import redirect
            return redirect(url, code=code)
        
        logger.info("HTTPS redirector middleware initialized")


def configure_secure_cookies(app: Flask):
    """
    Configure secure cookie settings
    
    Validates: Requirement 10.6
    
    Args:
        app: Flask application instance
    """
    # Set secure cookie defaults
    app.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Not accessible via JavaScript
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # CSRF protection
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
    
    # Remember me cookie settings
    app.config['REMEMBER_COOKIE_SECURE'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Strict'
    
    logger.info("Secure cookie configuration applied")


def set_secure_cookie(
    response: Response,
    key: str,
    value: str,
    max_age: Optional[int] = None,
    httponly: bool = True,
    secure: bool = True,
    samesite: str = 'Strict'
) -> Response:
    """
    Set a cookie with secure flags
    
    Validates: Requirement 10.6
    
    Args:
        response: Flask response object
        key: Cookie name
        value: Cookie value
        max_age: Cookie max age in seconds
        httponly: Set HttpOnly flag
        secure: Set Secure flag
        samesite: SameSite policy ('Strict', 'Lax', or 'None')
    
    Returns:
        Modified response object
    """
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        secure=secure,
        httponly=httponly,
        samesite=samesite
    )
    
    return response


def init_security_middleware(app: Flask, config: Optional[Dict] = None):
    """
    Initialize all security middleware
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    config = config or {}
    
    # Initialize security headers
    csp_policy = config.get('csp_policy')
    enable_hsts = config.get('enable_hsts', True)
    hsts_max_age = config.get('hsts_max_age', 31536000)
    hsts_include_subdomains = config.get('hsts_include_subdomains', True)
    hsts_preload = config.get('hsts_preload', False)
    
    SecurityHeadersMiddleware(
        app=app,
        csp_policy=csp_policy,
        enable_hsts=enable_hsts,
        hsts_max_age=hsts_max_age,
        hsts_include_subdomains=hsts_include_subdomains,
        hsts_preload=hsts_preload
    )
    
    # Initialize HTTPS redirector (only in production)
    if app.config.get('ENV') != 'development':
        skip_paths = config.get('https_skip_paths', ['/health', '/metrics'])
        HTTPSRedirector(app=app, skip_paths=skip_paths)
    
    # Configure secure cookies
    configure_secure_cookies(app)
    
    logger.info("All security middleware initialized")


# Decorator for routes that need custom CSP
def custom_csp(**directives):
    """
    Decorator to set custom CSP for specific routes
    
    Usage:
        @app.route('/special')
        @custom_csp(script_src="'self' 'unsafe-inline'")
        def special_route():
            return render_template('special.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Build custom CSP
            policy_parts = []
            for directive, value in directives.items():
                directive_name = directive.replace('_', '-')
                policy_parts.append(f"{directive_name} {value}")
            
            if policy_parts:
                csp = '; '.join(policy_parts)
                if isinstance(response, Response):
                    response.headers['Content-Security-Policy'] = csp
            
            return response
        return decorated_function
    return decorator
