"""
Validation Decorators
Decorators to add validation to API endpoints
Task 2.11: Add validation decorators to all API endpoints
"""

from functools import wraps
from flask import request, jsonify
import logging
from typing import Dict, Any, List, Optional, Callable

from request_validator import RequestValidator
from structured_logging import get_logger

logger = get_logger(__name__)
validator = RequestValidator()


def validate_json(required_fields: List[str] = None, 
                 optional_fields: List[str] = None,
                 max_size: int = 1024 * 1024):
    """
    Validate JSON request body
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        max_size: Maximum JSON size in bytes
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check content type
            if not request.is_json:
                logger.warning("Invalid content type", 
                             content_type=request.content_type,
                             endpoint=request.endpoint)
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            # Check content length
            if request.content_length and request.content_length > max_size:
                logger.warning("Request too large", 
                             content_length=request.content_length,
                             max_size=max_size,
                             endpoint=request.endpoint)
                return jsonify({'error': 'Request body too large'}), 413
            
            try:
                data = request.get_json()
                if data is None:
                    return jsonify({'error': 'Invalid JSON'}), 400
                
                # Validate required fields
                if required_fields:
                    missing_fields = []
                    for field in required_fields:
                        if field not in data or data[field] is None:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        logger.warning("Missing required fields",
                                     missing_fields=missing_fields,
                                     endpoint=request.endpoint)
                        return jsonify({
                            'error': 'Missing required fields',
                            'missing_fields': missing_fields
                        }), 400
                
                # Check for unexpected fields
                allowed_fields = set(required_fields or []) | set(optional_fields or [])
                if allowed_fields:
                    unexpected_fields = set(data.keys()) - allowed_fields
                    if unexpected_fields:
                        logger.warning("Unexpected fields",
                                     unexpected_fields=list(unexpected_fields),
                                     endpoint=request.endpoint)
                        return jsonify({
                            'error': 'Unexpected fields',
                            'unexpected_fields': list(unexpected_fields)
                        }), 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error("JSON validation error", error=str(e), endpoint=request.endpoint)
                return jsonify({'error': 'Invalid JSON format'}), 400
        
        return decorated
    return decorator


def validate_query_params(allowed_params: List[str] = None,
                         required_params: List[str] = None):
    """
    Validate query parameters
    
    Args:
        allowed_params: List of allowed parameter names
        required_params: List of required parameter names
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check required parameters
            if required_params:
                missing_params = []
                for param in required_params:
                    if param not in request.args:
                        missing_params.append(param)
                
                if missing_params:
                    logger.warning("Missing required query parameters",
                                 missing_params=missing_params,
                                 endpoint=request.endpoint)
                    return jsonify({
                        'error': 'Missing required query parameters',
                        'missing_params': missing_params
                    }), 400
            
            # Check for unexpected parameters
            if allowed_params:
                unexpected_params = set(request.args.keys()) - set(allowed_params)
                if unexpected_params:
                    logger.warning("Unexpected query parameters",
                                 unexpected_params=list(unexpected_params),
                                 endpoint=request.endpoint)
                    return jsonify({
                        'error': 'Unexpected query parameters',
                        'unexpected_params': list(unexpected_params)
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def validate_email_field(field_name: str = 'email'):
    """
    Validate email field in JSON request
    
    Args:
        field_name: Name of the email field
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data and field_name in data:
                email = data[field_name]
                if not validator.validate_email(email):
                    logger.warning("Invalid email format",
                                 email=email[:20] + '...' if len(email) > 20 else email,
                                 endpoint=request.endpoint)
                    return jsonify({'error': f'Invalid {field_name} format'}), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def validate_string_length(field_name: str, min_length: int = 0, max_length: int = 1000):
    """
    Validate string field length
    
    Args:
        field_name: Name of the string field
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data and field_name in data:
                value = data[field_name]
                if isinstance(value, str):
                    if len(value) < min_length:
                        return jsonify({
                            'error': f'{field_name} must be at least {min_length} characters'
                        }), 400
                    
                    if len(value) > max_length:
                        return jsonify({
                            'error': f'{field_name} must be at most {max_length} characters'
                        }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def validate_integer_range(field_name: str, min_value: int = None, max_value: int = None):
    """
    Validate integer field range
    
    Args:
        field_name: Name of the integer field
        min_value: Minimum allowed value
        max_value: Maximum allowed value
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data and field_name in data:
                value = data[field_name]
                
                # Check if it's an integer
                if not isinstance(value, int):
                    try:
                        value = int(value)
                        data[field_name] = value  # Update the value
                    except (ValueError, TypeError):
                        return jsonify({
                            'error': f'{field_name} must be an integer'
                        }), 400
                
                # Check range
                if min_value is not None and value < min_value:
                    return jsonify({
                        'error': f'{field_name} must be at least {min_value}'
                    }), 400
                
                if max_value is not None and value > max_value:
                    return jsonify({
                        'error': f'{field_name} must be at most {max_value}'
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def validate_array_field(field_name: str, max_items: int = 100, item_type: type = None):
    """
    Validate array field
    
    Args:
        field_name: Name of the array field
        max_items: Maximum number of items allowed
        item_type: Expected type of array items
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data and field_name in data:
                value = data[field_name]
                
                # Check if it's a list
                if not isinstance(value, list):
                    return jsonify({
                        'error': f'{field_name} must be an array'
                    }), 400
                
                # Check length
                if len(value) > max_items:
                    return jsonify({
                        'error': f'{field_name} can have at most {max_items} items'
                    }), 400
                
                # Check item types
                if item_type:
                    for i, item in enumerate(value):
                        if not isinstance(item, item_type):
                            return jsonify({
                                'error': f'{field_name}[{i}] must be of type {item_type.__name__}'
                            }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def sanitize_input():
    """
    Sanitize input data to prevent XSS and other attacks
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if data:
                # Sanitize string values
                sanitized_data = {}
                for key, value in data.items():
                    if isinstance(value, str):
                        # Basic XSS prevention
                        sanitized_value = validator.sanitize_input(value)
                        sanitized_data[key] = sanitized_value
                    else:
                        sanitized_data[key] = value
                
                # Replace request data with sanitized version
                request._cached_json = (sanitized_data, sanitized_data)
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def validate_file_upload(allowed_extensions: List[str] = None,
                        max_size: int = 10 * 1024 * 1024,  # 10MB
                        required: bool = True):
    """
    Validate file upload
    
    Args:
        allowed_extensions: List of allowed file extensions
        max_size: Maximum file size in bytes
        required: Whether file is required
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if file is present
            if 'file' not in request.files:
                if required:
                    return jsonify({'error': 'No file uploaded'}), 400
                else:
                    return f(*args, **kwargs)
            
            file = request.files['file']
            
            # Check if file is selected
            if file.filename == '':
                if required:
                    return jsonify({'error': 'No file selected'}), 400
                else:
                    return f(*args, **kwargs)
            
            # Validate file
            validation_result = validator.validate_file_upload(file, allowed_extensions, max_size)
            
            if not validation_result.is_valid:
                logger.warning("File upload validation failed",
                             filename=file.filename,
                             errors=validation_result.errors,
                             endpoint=request.endpoint)
                return jsonify({
                    'error': 'File validation failed',
                    'details': validation_result.errors
                }), 400
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def rate_limit_endpoint(limit: int = 100, window: int = 3600):
    """
    Apply rate limiting to endpoint
    
    Args:
        limit: Number of requests allowed
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            from rate_limiter import RateLimiter
            
            rate_limiter = RateLimiter()
            client_ip = request.remote_addr
            endpoint = request.endpoint
            
            key = f"{endpoint}:{client_ip}"
            
            if not rate_limiter.is_allowed(key, limit=limit, window=window):
                logger.warning("Rate limit exceeded",
                             client_ip=client_ip,
                             endpoint=endpoint,
                             limit=limit,
                             window=window)
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': window
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator


# Composite decorators for common use cases
def validate_auth_request():
    """Validate authentication request (login/register)"""
    return validate_json(
        required_fields=['email', 'password'],
        max_size=1024  # 1KB
    )


def validate_user_registration():
    """Validate user registration request"""
    def decorator(f):
        @validate_json(required_fields=['email', 'password', 'confirm_password'])
        @validate_email_field('email')
        @validate_string_length('password', min_length=8, max_length=128)
        @sanitize_input()
        @rate_limit_endpoint(limit=5, window=3600)  # 5 registrations per hour
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_content_request():
    """Validate content generation request"""
    def decorator(f):
        @validate_json(required_fields=['topic'], optional_fields=['difficulty', 'format'])
        @validate_string_length('topic', min_length=3, max_length=200)
        @sanitize_input()
        @rate_limit_endpoint(limit=50, window=3600)  # 50 requests per hour
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated
    return decorator


__all__ = [
    'validate_json',
    'validate_query_params', 
    'validate_email_field',
    'validate_string_length',
    'validate_integer_range',
    'validate_array_field',
    'sanitize_input',
    'validate_file_upload',
    'rate_limit_endpoint',
    'validate_auth_request',
    'validate_user_registration',
    'validate_content_request'
]
