"""
Health Check and Readiness Endpoints
Implements /api/health and /api/ready for container orchestration
"""

from flask import jsonify
import time
import os

# Add these endpoints to main.py


def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        from redis_cache import get_redis_cache
        cache = get_redis_cache()
        if cache and cache.redis_client:
            cache.redis_client.ping()
            return True, "Redis connected"
        return False, "Redis not configured"
    except Exception as e:
        return False, f"Redis error: {str(e)}"


def check_gemini_api():
    """Check if Gemini API is accessible"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return False, "API key not configured"
        
        # Simple ping test (don't count against quota)
        genai.configure(api_key=api_key)
        return True, "Gemini API accessible"
    except Exception as e:
        return False, f"Gemini API error: {str(e)}"


def check_quota_limits():
    """Check if quota is critically high"""
    try:
        from quota_tracker import get_quota_tracker
        tracker = get_quota_tracker()
        stats = tracker.get_stats()
        
        rpm_pct = stats['requests']['per_minute']['percentage']
        rpd_pct = stats['requests']['per_day']['percentage']
        
        if rpm_pct > 90 or rpd_pct > 90:
            return False, f"Quota critical (RPM: {rpm_pct}%, RPD: {rpd_pct}%)"
        
        return True, f"Quota OK (RPM: {rpm_pct}%, RPD: {rpd_pct}%)"
    except Exception as e:
        return True, f"Quota check skipped: {str(e)}"


@app.route("/api/health", methods=['GET'])
def health_check():
    """
    Basic liveness probe
    Returns 200 if application is running (restart if fails)
    """
    return jsonify({
        "status": "healthy",
        "instance_id": os.getenv('INSTANCE_ID', 'backend-1'),
        "timestamp": time.time(),
        "version": "1.0.0"
    }), 200


@app.route("/api/ready", methods=['GET'])
def readiness_check():
    """
    Comprehensive readiness probe
    Returns 200 only if all dependencies are available (route traffic if passes)
    """
    checks = {}
    all_ready = True
    
    # Check Redis
    redis_ok, redis_msg = check_redis_connection()
    checks['redis'] = {
        'status': 'ok' if redis_ok else 'fail',
        'message': redis_msg
    }
    if not redis_ok:
        all_ready = False
    
    # Check Gemini API
    api_ok, api_msg = check_gemini_api()
    checks['gemini_api'] = {
        'status': 'ok' if api_ok else 'fail',
        'message': api_msg
    }
    if not api_ok:
        all_ready = False
    
    # Check quota limits
    quota_ok, quota_msg = check_quota_limits()
    checks['quota'] = {
        'status': 'ok' if quota_ok else 'warning',
        'message': quota_msg
    }
    # Warning only - don't mark as not ready
    
    response = {
        "ready": all_ready,
        "instance_id": os.getenv('INSTANCE_ID', 'backend-1'),
        "timestamp": time.time(),
        "checks": checks
    }
    
    status_code = 200 if all_ready else 503
    return jsonify(response), status_code


# Usage in main.py:
# Just add these two routes and the helper functions

# For Docker health check:
# HEALTHCHECK CMD curl -f http://localhost:5000/api/health || exit 1

# For Kubernetes:
# livenessProbe:
#   httpGet:
#     path: /api/health
#     port: 5000
# readinessProbe:
#   httpGet:
#     path: /api/ready
#     port: 5000
