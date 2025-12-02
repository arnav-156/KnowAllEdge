"""
Request Validation Module

Comprehensive input validation and sanitization for API requests
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from flask import request
from structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of validation operation"""
    is_valid: bool
    errors: List[str]
    sanitized_value: Optional[Any] = None
    
    def __bool__(self):
        return self.is_valid


class RequestValidator:
    """
    Validates and sanitizes API request inputs
    
    Provides validation for:
    - Content-Type headers
    - Topic strings
    - Array lengths
    - File uploads
    - Special characters
    """
    
    # Configuration
    MAX_TOPIC_LENGTH = 500
    MAX_ARRAY_LENGTH = 100
    MAX_STRING_LENGTH = 10000
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    ALLOWED_FILE_EXTENSIONS = {
        'txt', 'pdf', 'doc', 'docx', 'md', 'json', 'csv',
        'jpg', 'jpeg', 'png', 'gif', 'webp'
    }
    
    # Safe character whitelist (alphanumeric + common punctuation)
    SAFE_CHARS_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?()\'\"]+$')
    
    # Dangerous patterns to reject
    DANGEROUS_PATTERNS = [
        re.compile(r'<script', re.IGNORECASE),  # XSS
        re.compile(r'javascript:', re.IGNORECASE),  # XSS
        re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
        re.compile(r'(union|select|insert|update|delete|drop|create|alter)\s', re.IGNORECASE),  # SQL
        re.compile(r'\.\./'),  # Path traversal
        re.compile(r'[<>]'),  # HTML tags
    ]
    
    def __init__(self):
        logger.info("RequestValidator initialized")
    
    def validate_json(self, request_obj=None) -> ValidationResult:
        """
        Validate that request has JSON content type and valid JSON body
        
        Args:
            request_obj: Flask request object (uses global request if None)
        
        Returns:
            ValidationResult with validation status
        """
        if request_obj is None:
            request_obj = request
        
        errors = []
        
        # Check Content-Type header
        content_type = request_obj.headers.get('Content-Type', '')
        
        if 'application/json' not in content_type:
            errors.append(f"Invalid Content-Type: expected 'application/json', got '{content_type}'")
            logger.warning(f"Invalid Content-Type: {content_type}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Try to parse JSON
        try:
            json_data = request_obj.get_json(force=True)
            
            if json_data is None:
                errors.append("Request body is empty or invalid JSON")
                return ValidationResult(is_valid=False, errors=errors)
            
            logger.debug("Valid JSON request")
            return ValidationResult(
                is_valid=True,
                errors=[],
                sanitized_value=json_data
            )
            
        except Exception as e:
            errors.append(f"Invalid JSON: {str(e)}")
            logger.warning(f"JSON parsing error: {e}")
            return ValidationResult(is_valid=False, errors=errors)
    
    def validate_topic(self, topic: str) -> ValidationResult:
        """
        Validate topic string
        
        Args:
            topic: Topic string to validate
        
        Returns:
            ValidationResult with validation status and sanitized topic
        """
        errors = []
        
        # Check if topic exists
        if not topic:
            errors.append("Topic is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check type
        if not isinstance(topic, str):
            errors.append(f"Topic must be a string, got {type(topic).__name__}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check length
        if len(topic) > self.MAX_TOPIC_LENGTH:
            errors.append(f"Topic exceeds maximum length of {self.MAX_TOPIC_LENGTH} characters")
            logger.warning(f"Topic too long: {len(topic)} characters")
            return ValidationResult(is_valid=False, errors=errors)
        
        if len(topic) < 1:
            errors.append("Topic cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(topic):
                errors.append(f"Topic contains potentially dangerous content")
                logger.warning(f"Dangerous pattern detected in topic: {pattern.pattern}")
                return ValidationResult(is_valid=False, errors=errors)
        
        # Sanitize: strip whitespace
        sanitized_topic = topic.strip()
        
        logger.debug(f"Valid topic: {sanitized_topic[:50]}...")
        return ValidationResult(
            is_valid=True,
            errors=[],
            sanitized_value=sanitized_topic
        )
    
    def validate_array(self, array: List[Any], field_name: str = "array") -> ValidationResult:
        """
        Validate array length
        
        Args:
            array: Array to validate
            field_name: Name of field for error messages
        
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        # Check if array exists
        if array is None:
            errors.append(f"{field_name} is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check type
        if not isinstance(array, (list, tuple)):
            errors.append(f"{field_name} must be an array, got {type(array).__name__}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check length
        if len(array) > self.MAX_ARRAY_LENGTH:
            errors.append(f"{field_name} exceeds maximum length of {self.MAX_ARRAY_LENGTH} items")
            logger.warning(f"Array too long: {len(array)} items")
            return ValidationResult(is_valid=False, errors=errors)
        
        if len(array) < 1:
            errors.append(f"{field_name} cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)
        
        logger.debug(f"Valid array: {len(array)} items")
        return ValidationResult(
            is_valid=True,
            errors=[],
            sanitized_value=array
        )
    
    def validate_string(self, value: str, field_name: str = "field", 
                       min_length: int = 1, max_length: Optional[int] = None) -> ValidationResult:
        """
        Validate string field
        
        Args:
            value: String to validate
            field_name: Name of field for error messages
            min_length: Minimum length
            max_length: Maximum length (uses MAX_STRING_LENGTH if None)
        
        Returns:
            ValidationResult with validation status and sanitized string
        """
        errors = []
        
        if max_length is None:
            max_length = self.MAX_STRING_LENGTH
        
        # Check if value exists
        if value is None:
            errors.append(f"{field_name} is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check type
        if not isinstance(value, str):
            errors.append(f"{field_name} must be a string, got {type(value).__name__}")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check length
        if len(value) < min_length:
            errors.append(f"{field_name} must be at least {min_length} characters")
            return ValidationResult(is_valid=False, errors=errors)
        
        if len(value) > max_length:
            errors.append(f"{field_name} exceeds maximum length of {max_length} characters")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.search(value):
                errors.append(f"{field_name} contains potentially dangerous content")
                logger.warning(f"Dangerous pattern detected in {field_name}")
                return ValidationResult(is_valid=False, errors=errors)
        
        # Sanitize
        sanitized_value = value.strip()
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            sanitized_value=sanitized_value
        )
    
    def validate_special_characters(self, value: str, field_name: str = "field") -> ValidationResult:
        """
        Validate that string contains only safe characters
        
        Args:
            value: String to validate
            field_name: Name of field for error messages
        
        Returns:
            ValidationResult with validation status
        """
        errors = []
        
        if not value:
            errors.append(f"{field_name} is required")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check for safe characters only
        if not self.SAFE_CHARS_PATTERN.match(value):
            errors.append(f"{field_name} contains invalid characters")
            logger.warning(f"Invalid characters in {field_name}")
            return ValidationResult(is_valid=False, errors=errors)
        
        return ValidationResult(
            is_valid=True,
            errors=[],
            sanitized_value=value.strip()
        )
    
    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML content (basic implementation)
        
        Args:
            html: HTML string to sanitize
        
        Returns:
            Sanitized HTML string
        """
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove event handlers
        html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s*on\w+\s*=\s*\S+', '', html, flags=re.IGNORECASE)
        
        # Remove javascript: URLs
        html = re.sub(r'javascript:', '', html, flags=re.IGNORECASE)
        
        return html
    
    def escape_sql(self, value: str) -> str:
        """
        Escape SQL special characters (use parameterized queries instead!)
        
        Args:
            value: String to escape
        
        Returns:
            Escaped string
        """
        # This is a basic implementation - ALWAYS use parameterized queries!
        if not isinstance(value, str):
            return value
        
        # Escape single quotes
        value = value.replace("'", "''")
        
        # Escape backslashes
        value = value.replace("\\", "\\\\")
        
        return value


# Global validator instance
request_validator = RequestValidator()


# Decorator for route validation
def validate_json_request():
    """
    Decorator to validate JSON requests
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_json_request()
        def endpoint():
            data = request.get_json()
    """
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = request_validator.validate_json()
            
            if not result.is_valid:
                from flask import jsonify
                return jsonify({
                    "error": "Validation Error",
                    "message": "Invalid request format",
                    "details": result.errors
                }), 400
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
