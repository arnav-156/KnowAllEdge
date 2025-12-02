"""
Request Signing Module
======================

✅ SECURITY FIX: HMAC signature verification for API requests
Prevents man-in-the-middle attacks by ensuring request integrity

Usage:
    from request_signing import require_signature
    
    @app.route('/api/sensitive')
    @require_signature
    def sensitive_endpoint():
        return jsonify({"data": "protected"})

Client-side signing (JavaScript example):
    const signature = await generateSignature(apiKey, method, path, timestamp, body);
    headers: {
        'X-API-Key': apiKey,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
"""

import hmac
import hashlib
import time
from functools import wraps
from flask import request, jsonify, current_app
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Signature validity window (5 minutes)
SIGNATURE_VALIDITY_WINDOW = 300


def generate_signature(api_key: str, method: str, path: str, timestamp: str, body: str = "") -> str:
    """
    Generate HMAC-SHA256 signature for request
    
    Args:
        api_key: User's API key (used as signing key)
        method: HTTP method (GET, POST, etc)
        path: Request path (/api/create_subtopics)
        timestamp: Unix timestamp (seconds)
        body: Request body (empty string for GET)
    
    Returns:
        Hex-encoded signature string
    """
    # Construct signing string
    signing_string = f"{method}:{path}:{timestamp}:{body}"
    
    # Generate HMAC signature
    signature = hmac.new(
        api_key.encode('utf-8'),
        signing_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(api_key: str, signature: str, method: str, path: str, timestamp: str, body: str = "") -> Tuple[bool, Optional[str]]:
    """
    Verify request signature
    
    Returns:
        (is_valid, error_message)
    """
    # Check timestamp freshness (prevent replay attacks)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - request_time) > SIGNATURE_VALIDITY_WINDOW:
            return False, "Signature expired (timestamp too old or too far in future)"
    except ValueError:
        return False, "Invalid timestamp format"
    
    # Generate expected signature
    expected_signature = generate_signature(api_key, method, path, timestamp, body)
    
    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        return False, "Invalid signature"
    
    return True, None


def require_signature(f):
    """
    Decorator to require HMAC signature on endpoints
    
    Usage:
        @app.route('/api/endpoint')
        @require_signature
        def my_endpoint():
            return jsonify({"data": "protected"})
    
    Required headers:
        X-API-Key: User's API key
        X-Timestamp: Unix timestamp (seconds)
        X-Signature: HMAC-SHA256 signature
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract required headers
        api_key = request.headers.get('X-API-Key')
        timestamp = request.headers.get('X-Timestamp')
        signature = request.headers.get('X-Signature')
        
        # Validate presence
        if not all([api_key, timestamp, signature]):
            logger.warning("Request missing signature headers", extra={
                'path': request.path,
                'has_api_key': bool(api_key),
                'has_timestamp': bool(timestamp),
                'has_signature': bool(signature)
            })
            return jsonify({
                "error": "signature_required",
                "message": "Request must include X-API-Key, X-Timestamp, and X-Signature headers"
            }), 401
        
        # Get request body
        body = ""
        if request.method in ['POST', 'PUT', 'PATCH']:
            body = request.get_data(as_text=True)
        
        # Verify signature
        is_valid, error_msg = verify_signature(
            api_key=api_key,
            signature=signature,
            method=request.method,
            path=request.path,
            timestamp=timestamp,
            body=body
        )
        
        if not is_valid:
            logger.warning("Invalid request signature", extra={
                'path': request.path,
                'error': error_msg
            })
            return jsonify({
                "error": "invalid_signature",
                "message": error_msg
            }), 401
        
        # Signature valid - proceed with request
        return f(*args, **kwargs)
    
    return decorated_function


def optional_signature(f):
    """
    Decorator that verifies signature if provided, but doesn't require it
    Useful for backwards compatibility during rollout
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        signature = request.headers.get('X-Signature')
        
        # If signature provided, verify it
        if signature:
            api_key = request.headers.get('X-API-Key')
            timestamp = request.headers.get('X-Timestamp')
            
            if not all([api_key, timestamp]):
                return jsonify({
                    "error": "incomplete_signature",
                    "message": "X-API-Key and X-Timestamp required when X-Signature is provided"
                }), 401
            
            body = ""
            if request.method in ['POST', 'PUT', 'PATCH']:
                body = request.get_data(as_text=True)
            
            is_valid, error_msg = verify_signature(
                api_key=api_key,
                signature=signature,
                method=request.method,
                path=request.path,
                timestamp=timestamp,
                body=body
            )
            
            if not is_valid:
                logger.warning("Invalid optional signature", extra={
                    'path': request.path,
                    'error': error_msg
                })
                return jsonify({
                    "error": "invalid_signature",
                    "message": error_msg
                }), 401
        
        # No signature or valid signature - proceed
        return f(*args, **kwargs)
    
    return decorated_function


# Client-side JavaScript helper (include in frontend documentation)
CLIENT_SIDE_EXAMPLE = """
// JavaScript helper for generating signatures
async function generateSignature(apiKey, method, path, timestamp, body = '') {
    const signingString = `${method}:${path}:${timestamp}:${body}`;
    
    // Convert API key and signing string to Uint8Array
    const encoder = new TextEncoder();
    const keyData = encoder.encode(apiKey);
    const messageData = encoder.encode(signingString);
    
    // Import key for HMAC
    const key = await crypto.subtle.importKey(
        'raw',
        keyData,
        { name: 'HMAC', hash: 'SHA-256' },
        false,
        ['sign']
    );
    
    // Generate signature
    const signature = await crypto.subtle.sign('HMAC', key, messageData);
    
    // Convert to hex string
    return Array.from(new Uint8Array(signature))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
}

// Example usage in API client
async function signedRequest(method, path, body = null) {
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const bodyString = body ? JSON.stringify(body) : '';
    
    const signature = await generateSignature(
        API_KEY,
        method,
        path,
        timestamp,
        bodyString
    );
    
    const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
        'X-Timestamp': timestamp,
        'X-Signature': signature
    };
    
    const response = await fetch(`${BASE_URL}${path}`, {
        method,
        headers,
        body: body ? bodyString : undefined
    });
    
    return response.json();
}
"""
