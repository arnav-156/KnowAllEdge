"""
Centralized Error Handling Module

Provides consistent error handling and responses across the application
"""

import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from flask import jsonify, request
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class ErrorResponse:
    """Standardized error response format"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class ErrorHandler:
    """
    Centralized error handling for the application
    
    Handles:
    - General exceptions
    - Validation errors
    - Database errors
    - Rate limit errors
    - Authentication errors
    """
    
    # Documentation base URL
    DOCS_BASE_URL = "https://docs.KNOWALLEDGE.com/errors"
    
    def __init__(self):
        logger.info("ErrorHandler initialized")
    
    def generate_request_id(self) -> str:
        """Generate unique request ID"""
        return str(uuid.uuid4())
    
    def handle_exception(self, error: Exception, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle general exceptions
        
        Args:
            error: Exception object
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        # Log the error with full traceback
        logger.error(
            f"Unhandled exception",
            extra={
                'request_id': request_id,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc(),
                'path': request.path if request else None,
                'method': request.method if request else None
            }
        )
        
        # Create error response
        error_response = ErrorResponse(
            error_code='INTERNAL_SERVER_ERROR',
            message='An internal server error occurred',
            details={
                'error_type': type(error).__name__
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/internal-server-error"
        )
        
        return error_response.to_dict(), 500
    
    def handle_validation_error(self, errors: list, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle validation errors
        
        Args:
            errors: List of validation error messages
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        logger.warning(
            f"Validation error",
            extra={
                'request_id': request_id,
                'errors': errors,
                'path': request.path if request else None
            }
        )
        
        error_response = ErrorResponse(
            error_code='VALIDATION_ERROR',
            message='Request validation failed',
            details={
                'validation_errors': errors
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/validation-error"
        )
        
        return error_response.to_dict(), 400
    
    def handle_database_error(self, error: Exception, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle database errors
        
        Args:
            error: Database exception
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        logger.error(
            f"Database error",
            extra={
                'request_id': request_id,
                'error_type': type(error).__name__,
                'error_message': str(error),
                'traceback': traceback.format_exc()
            }
        )
        
        error_response = ErrorResponse(
            error_code='DATABASE_ERROR',
            message='A database error occurred',
            details={
                'error_type': type(error).__name__
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/database-error"
        )
        
        return error_response.to_dict(), 500
    
    def handle_rate_limit_error(self, retry_after: int, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle rate limit errors
        
        Args:
            retry_after: Seconds until rate limit resets
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        logger.warning(
            f"Rate limit exceeded",
            extra={
                'request_id': request_id,
                'retry_after': retry_after,
                'path': request.path if request else None
            }
        )
        
        error_response = ErrorResponse(
            error_code='RATE_LIMIT_EXCEEDED',
            message='Rate limit exceeded',
            details={
                'retry_after': retry_after,
                'retry_after_human': f"{retry_after} seconds"
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/rate-limit-exceeded"
        )
        
        return error_response.to_dict(), 429
    
    def handle_authentication_error(self, message: str = None, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle authentication errors
        
        Args:
            message: Optional custom error message
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        logger.warning(
            f"Authentication error",
            extra={
                'request_id': request_id,
                'message': message,
                'path': request.path if request else None
            }
        )
        
        error_response = ErrorResponse(
            error_code='AUTHENTICATION_ERROR',
            message=message or 'Authentication required',
            details={
                'hint': 'Provide valid credentials via X-API-Key or Authorization header'
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/authentication-error"
        )
        
        return error_response.to_dict(), 401
    
    def handle_authorization_error(self, message: str = None, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle authorization errors
        
        Args:
            message: Optional custom error message
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        logger.warning(
            f"Authorization error",
            extra={
                'request_id': request_id,
                'message': message,
                'path': request.path if request else None
            }
        )
        
        error_response = ErrorResponse(
            error_code='AUTHORIZATION_ERROR',
            message=message or 'Insufficient permissions',
            details={
                'hint': 'You do not have permission to access this resource'
            },
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/authorization-error"
        )
        
        return error_response.to_dict(), 403
    
    def handle_not_found_error(self, resource: str = None, request_id: Optional[str] = None) -> Tuple[Dict, int]:
        """
        Handle not found errors
        
        Args:
            resource: Optional resource name
            request_id: Optional request ID
        
        Returns:
            Tuple of (response_dict, status_code)
        """
        if request_id is None:
            request_id = self.generate_request_id()
        
        message = f"{resource} not found" if resource else "Resource not found"
        
        logger.info(
            f"Not found",
            extra={
                'request_id': request_id,
                'resource': resource,
                'path': request.path if request else None
            }
        )
        
        error_response = ErrorResponse(
            error_code='NOT_FOUND',
            message=message,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            documentation_url=f"{self.DOCS_BASE_URL}/not-found"
        )
        
        return error_response.to_dict(), 404
    
    def register_error_handlers(self, app):
        """
        Register error handlers with Flask app
        
        Args:
            app: Flask application instance
        """
        @app.errorhandler(400)
        def handle_400(error):
            response, status = self.handle_validation_error([str(error)])
            return jsonify(response), status
        
        @app.errorhandler(401)
        def handle_401(error):
            response, status = self.handle_authentication_error(str(error))
            return jsonify(response), status
        
        @app.errorhandler(403)
        def handle_403(error):
            response, status = self.handle_authorization_error(str(error))
            return jsonify(response), status
        
        @app.errorhandler(404)
        def handle_404(error):
            response, status = self.handle_not_found_error()
            return jsonify(response), status
        
        @app.errorhandler(429)
        def handle_429(error):
            response, status = self.handle_rate_limit_error(60)
            return jsonify(response), status
        
        @app.errorhandler(500)
        def handle_500(error):
            response, status = self.handle_exception(error)
            return jsonify(response), status
        
        @app.errorhandler(Exception)
        def handle_generic_exception(error):
            response, status = self.handle_exception(error)
            return jsonify(response), status
        
        logger.info("Error handlers registered with Flask app")


# Global error handler instance
error_handler = ErrorHandler()
