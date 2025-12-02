"""
Log Sanitization Module
=======================

✅ SECURITY FIX: Remove sensitive data from logs to prevent PII leakage

Sanitizes:
- API keys and tokens
- Email addresses
- Passwords and secrets
- Credit card numbers
- IP addresses (partial)
- User-generated content (truncated)

Usage:
    from log_sanitizer import sanitize_log_data
    
    safe_data = sanitize_log_data({
        'user_email': 'test@example.com',
        'api_key': 'secret_key_12345',
        'topic': 'Machine Learning'
    })
    logger.info("User action", extra=safe_data)
"""

import re
from typing import Any, Dict, List, Union
from copy import deepcopy

# Regex patterns for sensitive data
PATTERNS = {
    'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    'api_key': re.compile(r'\b[A-Za-z0-9_-]{20,}\b'),
    'jwt': re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'),
    'credit_card': re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'ipv4': re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
    'password': re.compile(r'(?:password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE),
}

# Sensitive field names (case-insensitive)
SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth', 'credential', 'private_key', 'privatekey',
    'access_token', 'refresh_token', 'session_id', 'cookie', 'csrf',
    'master_password', 'encryption_key', 'api_secret'
}

# Fields that may contain PII (truncate but don't fully redact)
PII_FIELDS = {
    'email', 'name', 'username', 'user', 'phone', 'address',
    'city', 'state', 'zip', 'postal', 'ssn', 'license'
}

# User-generated content fields (truncate to prevent log bloat)
USER_CONTENT_FIELDS = {
    'topic', 'subtopic', 'query', 'search', 'message', 'content',
    'description', 'text', 'body', 'comment'
}

# Maximum length for user content in logs
MAX_CONTENT_LENGTH = 100


def sanitize_string(value: str, field_name: str = '') -> str:
    """
    Sanitize a string value
    
    Args:
        value: String to sanitize
        field_name: Field name for context-aware sanitization
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return value
    
    field_lower = field_name.lower()
    
    # Full redaction for sensitive fields
    if field_lower in SENSITIVE_FIELDS:
        return '[REDACTED]'
    
    # Partial redaction for PII
    if field_lower in PII_FIELDS:
        if '@' in value:  # Email
            parts = value.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                # Show first 2 chars of username, redact rest
                return f"{username[:2]}***@{domain}"
        return '[PII_REDACTED]'
    
    # Truncate user content
    if field_lower in USER_CONTENT_FIELDS:
        if len(value) > MAX_CONTENT_LENGTH:
            return value[:MAX_CONTENT_LENGTH] + '...[truncated]'
    
    # Apply regex patterns
    sanitized = value
    
    # Emails: partial redaction
    sanitized = PATTERNS['email'].sub(
        lambda m: f"{m.group(0)[:3]}***@{m.group(0).split('@')[1]}" if '@' in m.group(0) else '[EMAIL]',
        sanitized
    )
    
    # API keys: show first/last 4 chars
    def redact_key(match):
        key = match.group(0)
        if len(key) >= 12:
            return f"{key[:4]}...{key[-4:]}"
        return '[API_KEY]'
    sanitized = PATTERNS['api_key'].sub(redact_key, sanitized)
    
    # JWTs: full redaction
    sanitized = PATTERNS['jwt'].sub('[JWT_TOKEN]', sanitized)
    
    # Credit cards: show last 4 digits
    def redact_cc(match):
        cc = match.group(0).replace('-', '').replace(' ', '')
        return f"****-****-****-{cc[-4:]}"
    sanitized = PATTERNS['credit_card'].sub(redact_cc, sanitized)
    
    # SSN: full redaction
    sanitized = PATTERNS['ssn'].sub('[SSN]', sanitized)
    
    # Phone: show area code only
    sanitized = PATTERNS['phone'].sub(lambda m: f"{m.group(0)[:3]}-***-****", sanitized)
    
    # IP: show first 2 octets
    def redact_ip(match):
        ip = match.group(0)
        parts = ip.split('.')
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.*.*"
        return ip
    sanitized = PATTERNS['ipv4'].sub(redact_ip, sanitized)
    
    # Passwords in strings
    sanitized = PATTERNS['password'].sub(lambda m: f"{m.group(0).split('=')[0]}=[REDACTED]", sanitized)
    
    return sanitized


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary
    
    Args:
        data: Dictionary to sanitize
    
    Returns:
        Sanitized dictionary (new object)
    """
    sanitized = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Handle nested structures
        if isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = sanitize_list(value, key)
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value, key)
        else:
            # Numbers, booleans, None - pass through
            sanitized[key] = value
    
    return sanitized


def sanitize_list(data: List[Any], field_name: str = '') -> List[Any]:
    """
    Recursively sanitize list
    
    Args:
        data: List to sanitize
        field_name: Field name for context
    
    Returns:
        Sanitized list (new object)
    """
    sanitized = []
    
    for item in data:
        if isinstance(item, dict):
            sanitized.append(sanitize_dict(item))
        elif isinstance(item, list):
            sanitized.append(sanitize_list(item, field_name))
        elif isinstance(item, str):
            sanitized.append(sanitize_string(item, field_name))
        else:
            sanitized.append(item)
    
    return sanitized


def sanitize_log_data(data: Union[Dict, List, str, Any]) -> Union[Dict, List, str, Any]:
    """
    Main sanitization function - sanitize any data structure
    
    Args:
        data: Data to sanitize (dict, list, string, or primitive)
    
    Returns:
        Sanitized copy of data
    
    Examples:
        >>> sanitize_log_data({'email': 'test@example.com', 'topic': 'ML'})
        {'email': 'te***@example.com', 'topic': 'ML'}
        
        >>> sanitize_log_data({'api_key': 'sk_test_1234567890abcdef'})
        {'api_key': 'sk_t...cdef'}
        
        >>> sanitize_log_data({'password': 'secret123'})
        {'password': '[REDACTED]'}
    """
    # Don't modify the original object
    if isinstance(data, dict):
        return sanitize_dict(deepcopy(data))
    elif isinstance(data, list):
        return sanitize_list(deepcopy(data))
    elif isinstance(data, str):
        return sanitize_string(data)
    else:
        # Primitive types (int, float, bool, None)
        return data


def create_safe_extra(**kwargs) -> Dict[str, Any]:
    """
    Convenience function for creating safe logging extras
    
    Usage:
        logger.info("User action", extra=create_safe_extra(
            user_email='test@example.com',
            topic='Machine Learning',
            api_key='secret_key'
        ))
    
    Returns:
        Sanitized dictionary safe for logging
    """
    return sanitize_log_data(kwargs)


# Testing examples
if __name__ == '__main__':
    # Test data
    test_data = {
        'user_email': 'john.doe@example.com',
        'api_key': 'sk_live_1234567890abcdefghij',
        'password': 'SuperSecret123!',
        'topic': 'Machine Learning and Deep Learning with Python',
        'credit_card': '4532-1234-5678-9010',
        'ip_address': '192.168.1.100',
        'jwt_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
        'nested': {
            'secret_token': 'very_secret_token_12345',
            'user': 'jane_smith'
        }
    }
    
    print("Original data:")
    print(test_data)
    print("\nSanitized data:")
    print(sanitize_log_data(test_data))
