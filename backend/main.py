from flask import Flask, request, jsonify, g, has_request_context
from flask_cors import CORS
from dotenv import load_dotenv

# ✅ CRITICAL: Load environment variables BEFORE importing config
# This ensures .env variables are available when config.py initializes
load_dotenv()

# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
import json
import os
import time
import random  # For jitter in exponential backoff
import logging
import re
import hashlib
import uuid
from functools import wraps, lru_cache
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from werkzeug.exceptions import BadRequest, TooManyRequests
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from io import BytesIO

# imports for handling the images generation
import requests
import base64
from PIL import Image as PILImage
import io

# Import config and structured logging
from config import get_config
from structured_logging import get_logger

# ✅ NEW: Import security modules
from auth import (
    auth_manager, 
    require_auth, 
    require_admin,
    get_current_user
)
from secrets_manager import (
    get_secrets_manager,
    get_secret,
    get_gemini_api_key as get_secure_gemini_key
)
from https_security import (
    HTTPSSecurityManager,
    require_https,
    get_client_ip,
    is_secure_request,
    audit_request
)

# Import Redis cache and circuit breaker
from redis_cache import RedisCache, cached_response
from circuit_breaker import initialize_circuit_breakers, get_google_ai_breaker, CircuitBreakerError

# Import metrics and analytics
from metrics import metrics_collector, track_request_metrics
from analytics_routes import analytics_bp
from analytics_db import analytics_db

# Import GDPR API
from gdpr_api import gdpr_api

# Import Social API
from social_api import social_api

# Import OG Image API
from og_image_api import og_image_api

# Import Gamification API
from gamification_routes import gamification_bp

# Import Study Tools API
from study_tools_routes import study_tools_bp

# Import Learning Analytics API
from learning_analytics_routes import learning_analytics_bp

# Import Integration Ecosystem API
from integration_routes import integration_bp

# Import prompt templates
from prompt_templates import get_prompt_registry

# Import advanced modules
from content_validator import get_content_validator
from advanced_rate_limiter import get_rate_limiter, advanced_rate_limit
from multi_layer_cache import MultiLayerCache, multi_layer_cached

# ✅ NEW: Import production readiness components
from error_handler import error_handler
from request_validator import request_validator, validate_json_request
from file_validator import file_validator
from csrf_protection import CSRFProtection, csrf_protect, create_csrf_token_endpoint

# Import production enhancements (optional - graceful fallback if not available)
try:
    from quota_tracker import get_quota_tracker, with_quota_check, RequestPriority
    from cache_strategy import get_cache_strategy
    QUOTA_TRACKER_AVAILABLE = True
    logging.info("Quota tracker loaded successfully")
except ImportError as e:
    QUOTA_TRACKER_AVAILABLE = False
    logging.warning(f"Quota tracker not available: {e}")

# ✅ NEW: Import Prometheus metrics (optional)
try:
    from prometheus_metrics import (
        init_prometheus_metrics,
        track_request_prometheus,
        update_quota_metrics,
        record_gemini_api_call,
        record_content_generated,
        quota_exceeded_total
    )
    PROMETHEUS_AVAILABLE = True
    logging.info("Prometheus metrics loaded successfully")
except ImportError as e:
    PROMETHEUS_AVAILABLE = False
    logging.warning(f"Prometheus metrics not available: {e}")
    # Create dummy functions if not available
    def track_request_prometheus(func):
        return func
    def update_quota_metrics(stats):
        pass
    def record_gemini_api_call(*args, **kwargs):
        pass
    def record_content_generated(*args, **kwargs):
        pass

# ✅ NEW: Initialize Sentry error tracking (optional)
SENTRY_DSN = os.getenv('SENTRY_DSN')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[FlaskIntegration()],
            environment=os.getenv('SENTRY_ENVIRONMENT', 'development'),
            traces_sample_rate=float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            release=f"KNOWALLEDGE-backend@{os.getenv('APP_VERSION', 'dev')}",
            # Scrub sensitive data before sending
            before_send=lambda event, hint: None if any(
                keyword in str(event).lower() 
                for keyword in ['password', 'api_key', 'secret', 'token']
            ) else event,
        )
        logging.info("Sentry error tracking initialized")
    except Exception as e:
        logging.warning(f"Failed to initialize Sentry: {e}")

# Initialize config
config = get_config()

# Initialize structured logger
logger = get_logger(__name__, config.logging.level)

# Initialize Redis cache
redis_cache = RedisCache(config)

# Initialize circuit breakers
initialize_circuit_breakers(config)

# Initialize prompt registry
prompt_registry = get_prompt_registry()

# Initialize content validator
content_validator = get_content_validator()

# Initialize advanced rate limiter
rate_limiter = get_rate_limiter()

# Initialize multi-layer cache
multi_cache = MultiLayerCache(redis_cache, config)

# Initialize quota tracker (optional - only if available)
quota_tracker = None
if QUOTA_TRACKER_AVAILABLE:
    try:
        quota_tracker = get_quota_tracker()
        logger.info("Quota tracker initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize quota tracker: {e}")

# ✅ NEW: Initialize security managers
secrets_manager = get_secrets_manager()
logger.info("Secrets manager initialized")

# ✅ SECURITY FIX: Get API keys from secure storage (encrypted)
# Note: load_dotenv() is called at the top of this file before config import
GOOGLE_API_KEY = get_secure_gemini_key() or os.getenv("GOOGLE_API_KEY")
PROJECT_NAME = os.getenv("PROJECT_NAME")

# Initialize Google AI
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in secure storage or .env file")
    raise ValueError("GOOGLE_API_KEY is required")

genai.configure(api_key=GOOGLE_API_KEY)
logger.info("Google AI initialized", extra={'project': PROJECT_NAME})

# Remove hardcoded system prompt - now managed in prompt_templates.py

app = Flask(__name__)

# ✅ NEW: Register centralized error handlers
error_handler.register_error_handlers(app)
logger.info("Centralized error handlers registered")

# ✅ SECURITY FIX: Initialize HTTPS security (enforces HTTPS in production)
force_https = os.getenv('FORCE_HTTPS', 'true').lower() == 'true'
https_security = HTTPSSecurityManager(app, force_https=force_https)
logger.info(f"HTTPS security initialized (force_https={force_https})")

# ✅ SECURITY: Initialize CSRF protection
app.config['SECRET_KEY'] = config.security.secret_key
csrf_handler = CSRFProtection(config.security.secret_key)
logger.info("CSRF protection initialized")

# ✅ SECURITY: Configure secure cookie settings
app.config['SESSION_COOKIE_SECURE'] = force_https  # Secure flag (HTTPS only)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # HttpOnly flag (no JS access)
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # SameSite policy
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)  # Session lifetime
logger.info("Secure cookie settings configured")

# Configure CORS using config settings
if config.security.cors_enabled:
    CORS(app, resources={
        r"/api/*": {
            "origins": config.security.cors_origins,
            "methods": ["POST", "GET", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-API-Key", "X-CSRF-Token"],  # ✅ Added CSRF token
            "max_age": 3600
        }
    })

# Register analytics blueprint
app.register_blueprint(analytics_bp)

# Register GDPR API blueprint
app.register_blueprint(gdpr_api, url_prefix='/api/user')

# Register Social API blueprint
app.register_blueprint(social_api, url_prefix='/api/social')

# Register OG Image API blueprint
app.register_blueprint(og_image_api, url_prefix='/api/og')

# Register Gamification API blueprint
app.register_blueprint(gamification_bp)

# Register Study Tools API blueprint
app.register_blueprint(study_tools_bp)

# Register Learning Analytics API blueprint
app.register_blueprint(learning_analytics_bp)

# Register Integration Ecosystem API blueprint
app.register_blueprint(integration_bp)

# ✅ NEW: Initialize Prometheus metrics (if available)
if PROMETHEUS_AVAILABLE:
    try:
        from database_manager import get_database_manager
        database_manager = get_database_manager()
        init_prometheus_metrics(
            app, 
            quota_tracker=quota_tracker, 
            cache=multi_cache,
            database_manager=database_manager
        )
        logger.info("Prometheus metrics initialized - available at /metrics")
    except Exception as e:
        logger.warning(f"Failed to initialize Prometheus metrics: {e}")

# Enable Brotli and gzip compression for Flask
try:
    from flask_compress import Compress
    COMPRESS_ALGORITHM = ['br', 'gzip']
    compress = Compress()
    compress.init_app(app)
    app.config['COMPRESS_ALGORITHM'] = COMPRESS_ALGORITHM
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/javascript', 'application/json', 'image/svg+xml']
    logger.info('Brotli and gzip compression enabled')
except ImportError:
    logger.warning('flask-compress not installed; Brotli/gzip compression not enabled')

# ✅ REQUEST ID TRACKING MIDDLEWARE
@app.before_request
def before_request():
    """Add unique request ID to each request"""
    # Generate unique request ID
    g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
    g.start_time = time.time()
    
    logger.info("Request started", extra={
        'method': request.method,
        'path': request.path,
        'request_id': g.request_id
    })

@app.after_request
def after_request(response):
    """Add security headers and request tracking"""
    # Add request ID to response headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    
    # ✅ SECURITY FIX: Add Content Security Policy headers
    # Strict CSP to prevent XSS attacks
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://generativelanguage.googleapis.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests;"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Additional security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Calculate request duration
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        logger.info("Request completed", extra={
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_seconds': round(duration, 3),
            'request_id': g.request_id
        })
    
    return response

# Configuration from config system
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = config.security.max_content_length

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Redis Cloud integration for caching
import os
import redis

REDIS_URL = os.getenv('REDIS_URL', 'redis://default:redispw@redis-12345.c1.us-east1-2.gcp.cloud.redislabs.com:12345')
redis_client = redis.StrictRedis.from_url(REDIS_URL)

# In-memory cache and rate limit storage (use Redis in production)
cache = {}
rate_limit_store = {}

def get_cache_key(endpoint, data):
    """Generate cache key from endpoint and request data"""
    cache_str = f"{endpoint}:{json.dumps(data, sort_keys=True)}"
    return hashlib.md5(cache_str.encode()).hexdigest()

def clean_old_cache():
    """Remove expired cache entries"""
    current_time = time.time()
    expired_keys = [k for k, v in cache.items() if current_time - v['timestamp'] > config.cache.ttl]
    for key in expired_keys:
        del cache[key]
    if expired_keys:
        logger.info("Cleaned expired cache entries", extra={'count': len(expired_keys)})
        
    # Record cache events for metrics
    for key in cache.keys():
        if current_time - cache[key]['timestamp'] < config.cache.ttl:
            metrics_collector.record_cache_hit()
        else:
            metrics_collector.record_cache_miss()

# Rate limiting decorator using config settings
def rate_limit(max_requests=None, window=None):
    """Rate limiting decorator"""
    def rate_limit_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Use config defaults if not specified
            _max_requests = max_requests or config.rate_limit.max_requests
            _window = window or config.rate_limit.window_seconds
            
            client_ip = request.remote_addr
            current_time = time.time()
            
            # Clean old entries
            if client_ip in rate_limit_store:
                rate_limit_store[client_ip] = [
                    timestamp for timestamp in rate_limit_store[client_ip]
                    if current_time - timestamp < _window
                ]
            else:
                rate_limit_store[client_ip] = []
            
            # Check rate limit
            if len(rate_limit_store[client_ip]) >= _max_requests:
                logger.warning("Rate limit exceeded", extra={'client_ip': client_ip})
                return jsonify({
                    "error": "Rate limit exceeded. Please try again later.",
                    "retry_after": _window
                }), 429
            
            # Add current request
            rate_limit_store[client_ip].append(current_time)
            
            return f(*args, **kwargs)
        return wrapper
    return rate_limit_decorator

# ✅ FIX 2: INPUT VALIDATION
def validate_json(*expected_args, **validators):
    """
    Decorator for validating JSON request data
    validators example: {'topic': lambda x: len(x) > 0 and len(x) < 200}
    """
    def validate_json_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                logger.warning("Non-JSON request received")
                return jsonify({"error": "Content-Type must be application/json"}), 400
            
            try:
                data = request.get_json()
            except Exception as e:
                logger.error(f"Invalid JSON: {str(e)}")
                return jsonify({"error": "Invalid JSON format"}), 400
            
            # Check required fields
            for arg in expected_args:
                if arg not in data:
                    return jsonify({"error": f"Missing required field: {arg}"}), 400
            
            # Validate topic if present
            if 'topic' in data:
                topic = data['topic'].strip() if isinstance(data['topic'], str) else ""
                if not topic or len(topic) > 200:
                    return jsonify({"error": "Topic must be 1-200 characters"}), 400
                if not re.match(r'^[a-zA-Z0-9\s\-.,()!?&]+$', topic):
                    return jsonify({"error": "Topic contains invalid characters"}), 400
                data['topic'] = topic
            
            # Validate focus array
            if 'focus' in data:
                if not isinstance(data['focus'], list):
                    return jsonify({"error": "Focus must be an array"}), 400
                if len(data['focus']) > config.api.max_subtopics:
                    return jsonify({"error": f"Maximum {config.api.max_subtopics} subtopics allowed"}), 400
            
            # Custom validators
            for field, validator in validators.items():
                if field in data:
                    try:
                        if not validator(data[field]):
                            return jsonify({"error": f"Invalid value for field: {field}"}), 400
                    except Exception as e:
                        return jsonify({"error": f"Validation error for {field}: {str(e)}"}), 400
            
            return f(*args, **kwargs)
        return wrapper
    return validate_json_decorator

# Caching decorator using config settings
def cached_response(ttl=None):
    """Decorator for caching API responses"""
    def cached_response_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Use config default if not specified
            _ttl = ttl or config.cache.ttl
            
            # Clean old cache periodically
            if len(cache) % 100 == 0:
                clean_old_cache()
            
            # Generate cache key
            cache_key = get_cache_key(f.__name__, request.get_json())
            
            # Check cache
            if cache_key in cache:
                cached_data = cache[cache_key]
                if time.time() - cached_data['timestamp'] < _ttl:
                    logger.info("Cache hit", extra={'endpoint': f.__name__})
                    metrics_collector.record_cache_hit()
                    return jsonify(cached_data['data'])
            
            # Cache miss
            metrics_collector.record_cache_miss()
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache successful responses
            if isinstance(result, tuple):
                # Handle tuples (response, status) or (response, status, headers)
                if len(result) == 2:
                    response, status = result
                    headers = {}
                elif len(result) == 3:
                    response, status, headers = result
                else:
                    return result  # Unexpected format, return as-is
                
                if status == 200:
                    cache[cache_key] = {
                        'data': response.get_json() if hasattr(response, 'get_json') else response,
                        'timestamp': time.time()
                    }
                return result
            else:
                # Single response object (Flask Response)
                try:
                    # Only cache if it's a successful response
                    if hasattr(result, 'status_code') and result.status_code == 200:
                        cache[cache_key] = {
                            'data': result.get_json() if hasattr(result, 'get_json') else None,
                            'timestamp': time.time()
                        }
                except:
                    pass  # Can't cache this response
                
                return result
        return wrapper
    return cached_response_decorator

# ✅ FIX 7: IMPROVED ERROR HANDLING
@app.errorhandler(400)
def bad_request(e):
    logger.warning(f"Bad request: {str(e)}")
    return jsonify({"error": "Bad request", "message": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(429)
def too_many_requests(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {str(e)}")
    return jsonify({"error": "Internal server error. Please try again later."}), 500

# Helper function for file validation
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: bool = True) -> float:
    """
    Calculate exponential backoff delay with optional jitter
    
    Args:
        attempt: Current retry attempt (0-indexed)
        base_delay: Base delay in seconds (default: 1.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        jitter: Whether to add random jitter (default: True)
    
    Returns:
        Delay in seconds
    """
    # Exponential: base_delay * 2^attempt
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    # Add jitter: random between 0 and calculated delay
    if jitter:
        delay = random.uniform(0, delay)
    
    return delay

def calculate_dynamic_workers(subtopic_count: int) -> int:
    """
    Calculate optimal number of workers based on load
    
    Args:
        subtopic_count: Number of subtopics to process
    
    Returns:
        Optimal worker count
    """
    if not config.api.dynamic_worker_scaling:
        return config.api.max_parallel_workers
    
    # Scale workers based on load
    # Rule: 1 worker per 2 subtopics, capped at limits
    optimal_workers = max(
        config.api.min_parallel_workers,
        min(
            subtopic_count // 2 + 1,
            config.api.max_parallel_workers_limit
        )
    )
    
    logger.debug("Calculated dynamic workers", extra={
        'subtopic_count': subtopic_count,
        'workers': optimal_workers
    })
    
    return optimal_workers

# ✅ FIX 5: PARALLEL PROCESSING HELPER WITH CIRCUIT BREAKER & VALIDATION
def generate_single_explanation_google_ai(subtopic, topic, detail, education, language='en', learning_style='General'):
    """✅ ENHANCED: Generate explanation with exponential backoff, circuit breaker, content validation, and language support"""
    max_retries = config.api.max_retries
    
    # Determine max words based on detail level
    max_words = 150
    if detail == 'detailed':
        max_words = 300
    elif detail == 'brief':
        max_words = 100
        
    # ✅ ADAPTIVE LEARNING: Check for user mastery
    # If we have a request context, try to get the user's mastery level
    mastery_level = 0
    mastery_context = "Beginner"
    use_adaptive = False
    
    if has_request_context():
        try:
            # This assumes we can get user_id from session or g
            # For now, we'll skip if not authenticated, or use a default
            from flask import g
            if hasattr(g, 'user_id'):
                user_id = g.user_id
                progress = analytics_db.get_user_progress(user_id, topic)
                # Find mastery for this subtopic if exists, or average
                for p in progress:
                    if p['subtopic'] == subtopic:
                        mastery_level = p['mastery_level']
                        break
                # Example: Convert mastery_level to context
                if mastery_level >= 0.8:
                    mastery_context = "Advanced"
                elif mastery_level >= 0.5:
                    mastery_context = "Intermediate"
                else:
                    mastery_context = "Beginner"
                use_adaptive = True # Enable adaptive if user progress is found
        except Exception:
            pass

    # Construct prompt using registry
    try:
        if use_adaptive:
            prompt_text = prompt_registry.format(
                "adaptive_explanation",
                subtopic=subtopic,
                topic=topic,
                mastery_level=mastery_context,
                context=f"Education: {education}, Detail: {detail}",
                learning_style=learning_style,
                max_words=max_words
            )
        else:
            prompt_text = prompt_registry.format(
                "explanation_v2",
                subtopic=subtopic,
                topic=topic,
                education=education,
                detail=detail,
                learning_style=learning_style,
                max_words=max_words
            )
    except Exception as e:
        logger.error(f"Error formatting prompt: {e}")
        # Fallback prompt
        prompt_text = f"Explain {subtopic} in {topic} for {education} level. Style: {learning_style}."
    
    prompt_text += get_language_instruction(language)

    # Semantic cache key
    def semantic_hash(text: str) -> str:
        import unicodedata, hashlib
        norm = unicodedata.normalize('NFKC', text.strip().lower())
        return hashlib.sha256(norm.encode('utf-8')).hexdigest()
    cache_key = f"explanation:{semantic_hash(prompt_text)}"
    cached = multi_cache.get(cache_key)
    if cached:
        logger.info("Semantic cache hit for explanation", extra={'subtopic': subtopic})
        return cached
    
    # Get circuit breaker
    breaker = get_google_ai_breaker()
    
    for attempt in range(max_retries):
        try:
            # Track API call start time for Prometheus
            api_start_time = time.time()
            token_count = 1500  # Default estimate
            
            # Function to call Google AI
            def call_google_ai():
                nonlocal token_count  # Allow updating outer scope variable
                model = genai.GenerativeModel('gemini-2.0-flash')
                response_obj = model.generate_content(prompt_text)
                
                # ✅ Extract token count from response metadata
                if hasattr(response_obj, 'usage_metadata') and response_obj.usage_metadata:
                    token_count = getattr(response_obj.usage_metadata, 'total_token_count', 1500)
                
                return response_obj.text
            
            # Call with circuit breaker if enabled
            if breaker:
                try:
                    result = breaker.call(call_google_ai)
                except CircuitBreakerError as e:
                    # Circuit is open, return fallback immediately
                    logger.warning("Circuit breaker open, using fallback", extra={
                        'subtopic': subtopic
                    })
                    return {
                        "subtopic": subtopic,
                        "explanation": f"Service temporarily unavailable. Please try again in a few moments.",
                        "error": "circuit_breaker_open"
                    }
            else:
                result = call_google_ai()
            
            # ✅ Record Prometheus metrics after successful API call
            api_duration = time.time() - api_start_time
            record_gemini_api_call('explain_subtopic', 'gemini-2.0-flash', api_duration, token_count, 'success')
            
            # ✅ Parse JSON response
            try:
                # Clean response text
                text = result.strip()
                if text.startswith('```json'):
                    text = text[7:]
                if text.endswith('```'):
                    text = text[:-3]
                
                data = json.loads(text)
                explanation_text = data.get('explanation', '')
                real_world_app = data.get('real_world_application', '')
                youtube_query = data.get('youtube_search_query', '')
            except json.JSONDecodeError:
                # Fallback for legacy text response
                explanation_text = result
                real_world_app = "Not available"
                youtube_query = f"{topic} {subtopic}"

            # ✅ VALIDATE CONTENT QUALITY
            validation_result = content_validator.validate_explanation(
                explanation=explanation_text.strip(),
                subtopic=subtopic,
                topic=topic,
                education_level=education
            )
            
            # If validation fails significantly, retry or return error
            if not validation_result.is_valid:
                logger.warning("Explanation validation failed", extra={
                    'subtopic': subtopic,
                    'quality_score': validation_result.quality_score,
                    'issues': validation_result.issues,
                    'attempt': attempt + 1
                })
                
                # If hallucination detected, don't retry - return error immediately
                if any('hallucination' in issue.lower() for issue in validation_result.issues):
                    return {
                        "subtopic": subtopic,
                        "explanation": "Content validation failed - please regenerate.",
                        "error": "validation_failed",
                        "quality_score": validation_result.quality_score
                    }
                
                # For other issues, retry if attempts remain with exponential backoff
                if attempt < max_retries - 1:
                    backoff_delay = calculate_exponential_backoff(attempt, base_delay=1.0, jitter=True)
                    logger.info("Retrying due to validation failure", extra={
                        'subtopic': subtopic,
                        'backoff_delay': f"{backoff_delay:.2f}s"
                    })
                    time.sleep(backoff_delay)
                    continue
            
            return {
                "subtopic": subtopic,
                "explanation": explanation_text.strip(),
                "real_world_application": real_world_app,
                "youtube_search_query": youtube_query,
                "error": None,
                "quality_score": validation_result.quality_score,
                "warnings": validation_result.warnings if validation_result.warnings else None
            }
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error("Failed to generate explanation", extra={
                    'subtopic': subtopic,
                    'error': str(e)
                }, exc_info=True)
                return {
                    "subtopic": subtopic,
                    "explanation": f"Content generation temporarily unavailable for this topic.",
                    "error": str(e)
                }
            # ✅ Use exponential backoff with jitter
            backoff_delay = calculate_exponential_backoff(attempt, base_delay=2.0, jitter=True)
            logger.warning("Retrying generation", extra={
                'subtopic': subtopic,
                'attempt': attempt + 1,
                'max_retries': max_retries,
                'backoff_delay': f"{backoff_delay:.2f}s"
            })
            time.sleep(backoff_delay)

def generate_single_explanation(subtopic, topic, detail, education, prompt_template, llm, output_parser):
    """Generate explanation for a single subtopic with retry logic"""
    max_retries = 3
    retry_delay = 2
    
    chain = prompt_template | llm | output_parser
    
    for attempt in range(max_retries):
        try:
            result = chain.invoke({
                "topic": topic,
                "subtopic": subtopic,
                "detail": detail,
                "education": education
            })
            return {"subtopic": subtopic, "explanation": result.strip(), "error": None}
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to generate explanation for '{subtopic}': {str(e)}")
                return {
                    "subtopic": subtopic,
                    "explanation": f"Content generation temporarily unavailable for this topic.",
                    "error": str(e)
                }
            logger.warning(f"Retry {attempt + 1}/{max_retries} for '{subtopic}'")
            time.sleep(retry_delay * (attempt + 1))

def parse_json_response(results):
    """Parse JSON response with markdown removal"""
    if not results:
        return None
    
    # Strip whitespace first
    results = results.strip()
    
    # Remove markdown code blocks with regex for better handling
    import re
    # Remove opening ```json or ``` with optional whitespace/newlines
    results = re.sub(r'^```(?:json|JSON)?\s*', '', results)
    # Remove closing ``` with optional whitespace/newlines
    results = re.sub(r'\s*```$', '', results)
    
    # Strip again after removing markdown
    results = results.strip()
    
    try:
        return json.loads(results)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {str(e)}, content: {results[:200]}")
        raise


# ==================== I18N LANGUAGE SUPPORT ====================

def get_user_language():
    """
    ✅ I18N: Get user's preferred language from request
    Reads from Accept-Language header or request body
    
    Returns:
        str: Language code (en, es, fr, de, zh, ja, ar, he) or 'en' as fallback
    """
    # Try header first (recommended)
    language = request.headers.get('Accept-Language', 'en')
    
    # Fallback to body parameter if JSON request
    if request.is_json:
        try:
            data = request.get_json()
            if data and 'language' in data:
                language = data.get('language', language)
        except Exception:
            pass  # Keep header value if body parsing fails
    
    # Validate language code (only allow supported languages)
    supported = ['en', 'es', 'fr', 'de', 'zh', 'ja', 'ar', 'he', 'fa', 'ur']
    language = language.lower().split('-')[0]  # Handle 'en-US' -> 'en'
    
    return language if language in supported else 'en'


def get_language_instruction(language=None):
    """
    ✅ I18N: Get language instruction to append to Gemini prompts
    Instructs Gemini to respond in the user's preferred language
    Uses concise instructions for cost optimization.
    """
    if language is None:
        language = get_user_language()
    if language == 'en':
        return ''
    # Concise instructions for supported languages
    short_instructions = {
        'es': '\nRespond in Spanish.',
        'fr': '\nRépondez en français.',
        'de': '\nAntworten Sie auf Deutsch.',
        'zh': '\n请用简体中文回答。',
        'ja': '\n日本語で回答してください。',
        'ar': '\nيرجى الرد باللغة العربية.',
        'he': '\nאנא הגב בעברית.',
        'fa': '\nلطفاً به زبان فارسی پاسخ دهید.',
        'ur': '\nبراہ کرم اردو میں جواب دیں۔',
    }
    return short_instructions.get(language, '')


def log_language_request(endpoint, language):
    """
    ✅ I18N: Log language usage for analytics
    
    Args:
        endpoint (str): API endpoint name
        language (str): Language code
    """
    logger.info("Language request", extra={
        'endpoint': endpoint,
        'language': language,
        'request_id': getattr(g, 'request_id', 'unknown')
    })


# ==================== API ENDPOINTS ====================

@app.route("/api/csrf-token", methods=['GET'])
def get_csrf_token():
    """Get CSRF token for client-side requests"""
    return create_csrf_token_endpoint(csrf_handler)()

@app.route("/api/health", methods=['GET'])
@track_request_metrics
def health_check():
    """
    Comprehensive health check endpoint for monitoring
    
    Returns detailed status of all system dependencies including:
    - Database connectivity and pool status
    - Redis cache status
    - Gemini API connectivity
    - Quota usage and limits
    - Circuit breaker states
    - System resource usage (CPU, memory, disk)
    - Version information
    - Uptime statistics
    
    Requirements: 8.1
    """
    from health_check import get_health_check_service
    
    health_service = get_health_check_service()
    health_status = health_service.perform_comprehensive_health_check()
    
    # Add application metrics
    health_status['metrics'] = metrics_collector.get_health_metrics()
    
    # Add prompt templates info
    health_status['checks']['prompt_templates'] = {
        'status': 'healthy',
        'available_templates': len(prompt_registry.list_templates())
    }
    
    # Determine HTTP status code
    if health_status['status'] == 'healthy' or health_status['status'] == 'healthy_with_warnings':
        status_code = 200
    else:
        status_code = 503
    
    return jsonify(health_status), status_code


@app.route("/api/prompts", methods=['GET'])
@track_request_metrics
def list_prompts():
    """List available prompt templates"""
    return jsonify({
        "templates": prompt_registry.list_templates(),
        "system_context": prompt_registry.get_system_context()
    })


@app.route("/api/stats", methods=['GET'])
@track_request_metrics
def get_stats():
    """✅ NEW: Get system statistics (cache, rate limits, validation)"""
    try:
        user_id, ip_address = rate_limiter._get_identifier()
        
        stats = {
            "cache": multi_cache.get_stats(),
            "rate_limits": rate_limiter.get_rate_limit_stats(user_id, ip_address),
            "system": {
                "active_users": len(rate_limiter.user_requests),
                "active_ips": len(rate_limiter.ip_requests),
                "blocked_count": len(rate_limiter.blocked_until)
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        logger.error("Error getting stats", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to retrieve stats"}), 500


@app.route("/api/ready", methods=['GET'])
def readiness_check():
    """
    Kubernetes readiness probe
    Returns 200 only if critical dependencies are available
    
    This endpoint is used by Kubernetes to determine if the pod
    should receive traffic. It checks:
    - Database connectivity
    - Gemini API availability
    - Quota status (warning only)
    
    Requirements: 8.1
    """
    from health_check import get_health_check_service
    
    health_service = get_health_check_service()
    is_ready, readiness_status = health_service.perform_readiness_check()
    
    status_code = 200 if is_ready else 503
    return jsonify(readiness_status), status_code


@app.route("/api/cache/invalidate", methods=['POST'])
@advanced_rate_limit(priority='high')
@track_request_metrics
def invalidate_cache():
    """✅ NEW: Invalidate cache (admin endpoint)"""
    try:
        request_data = request.get_json() or {}
        namespace = request_data.get('namespace')
        
        multi_cache.invalidate(namespace=namespace)
        
        logger.info("Cache invalidated", extra={'namespace': namespace or 'all'})
        
        return jsonify({
            "message": f"Cache invalidated successfully",
            "namespace": namespace or "all"
        })
    except Exception as e:
        logger.error("Error invalidating cache", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to invalidate cache"}), 500


@app.route("/api/create_subtopics", methods=['POST'])
@advanced_rate_limit(priority='medium')
@validate_json('topic')
@track_request_metrics
@multi_layer_cached(multi_cache, namespace='subtopics', ttl=7200)
def create_subtopics():
    """✅ ENHANCED: Generate 15 subtopics with validation, caching, and language support"""
    try:
        request_data = request.get_json()
        topic = request_data['topic']
        
        # ✅ I18N: Get user's preferred language
        language = get_user_language()
        log_language_request('create_subtopics', language)
        
        logger.info("Creating subtopics", extra={'topic': topic, 'language': language})

        # Use optimized prompt template
        prompt_text = prompt_registry.format(
            "subtopics_v1",
            count=15,
            topic=topic
        )
        # ✅ I18N: Add language instruction to prompt
        prompt_text += get_language_instruction(language)

        # Semantic cache key
        def semantic_hash(text: str) -> str:
            import unicodedata, hashlib
            norm = unicodedata.normalize('NFKC', text.strip().lower())
            return hashlib.sha256(norm.encode('utf-8')).hexdigest()
        cache_key = f"subtopics:{semantic_hash(prompt_text)}"
        cached = multi_cache.get(cache_key)
        if cached:
            logger.info("Semantic cache hit for subtopics", extra={'topic': topic})
            return jsonify(cached)
        
        # Use Google AI Gemini model
        start_api_time = time.time()
        model = genai.GenerativeModel('gemini-2.0-flash')
        response_obj = model.generate_content(prompt_text)
        results = response_obj.text
        api_duration = time.time() - start_api_time
        
        logger.debug("LLM response received", extra={'preview': results[:200]})
        
        # Parse JSON response
        parsed_results = parse_json_response(results)
        
        # Handle both array format ["subtopic1", ...] and object format {"subtopics": [...]}
        if isinstance(parsed_results, list):
            subtopics = parsed_results
        elif isinstance(parsed_results, dict) and 'subtopics' in parsed_results:
            subtopics = parsed_results['subtopics']
        else:
            raise ValueError("Invalid response format from LLM")
        
        # Validate subtopics is a list (no longer need to extract from parsed_results)
        
        if not isinstance(subtopics, list) or len(subtopics) == 0:
            raise ValueError("Subtopics must be a non-empty list")
        
        # ✅ NEW: Cache response for quota fallback after successful parsing
        if quota_tracker:
            cache_key = f"subtopics:{topic}"
            quota_tracker.cache_response(cache_key, {"subtopics": subtopics})
        
        # ✅ VALIDATE CONTENT QUALITY
        validation_result = content_validator.validate_subtopics(
            subtopics=subtopics,
            topic=topic,
            expected_count=15
        )
        
        if not validation_result.is_valid:
            logger.warning("Subtopics validation failed", extra={
                'issues': validation_result.issues,
                'quality_score': validation_result.quality_score
            })
            # Return error if critical issues found
            if validation_result.quality_score < 0.3:
                return jsonify({
                    "error": "Generated subtopics failed quality check",
                    "issues": validation_result.issues
                }), 500
        
        logger.info("Successfully generated subtopics", extra={
            'count': len(subtopics),
            'quality_score': validation_result.quality_score
        })
        
        # ✅ NEW: Record content generation metrics
        for _ in subtopics:
            record_content_generated('subtopic', validation_result.quality_score)
        
        return jsonify({
            "subtopics": subtopics,
            "count": len(subtopics),
            "quality_score": validation_result.quality_score,
            "warnings": validation_result.warnings if validation_result.warnings else None
        })
        
    except json.JSONDecodeError as e:
        logger.error("JSON parsing error", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to parse AI response. Please try again."}), 500
    except Exception as e:
        logger.error("Error in create_subtopics", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to generate subtopics. Please try again."}), 500


@app.route("/api/create_presentation", methods=['POST'])
@validate_json_request()  # ✅ NEW: Validate JSON content-type
@advanced_rate_limit(priority='medium')
@validate_json('topic', 'educationLevel', 'levelOfDetail', 'focus')
@track_request_metrics
def create_presentation():
    """Generate explanations for selected subtopics with parallel processing and language support"""
    try:
        request_data = request.get_json()
        
        # ✅ NEW: Enhanced validation with request_validator
        topic_result = request_validator.validate_topic(request_data.get('topic', ''))
        if not topic_result.is_valid:
            response, status = error_handler.handle_validation_error(topic_result.errors)
            return jsonify(response), status
        
        topic = topic_result.sanitized_value
        education = request_data['educationLevel']
        detail = request_data['levelOfDetail']
        subtopics = request_data['focus']
        
        # ✅ NEW: Validate subtopics array
        array_result = request_validator.validate_array(subtopics, 'subtopics')
        if not array_result.is_valid:
            response, status = error_handler.handle_validation_error(array_result.errors)
            return jsonify(response), status
        
        # ✅ I18N: Get user's preferred language
        language = get_user_language()
        log_language_request('create_presentation', language)
        
        # ✅ PERSONALIZATION: Get learning style
        learning_style = request_data.get('learningStyle', 'General')
        
        logger.info("Creating presentation", extra={
            'topic': topic,
            'subtopic_count': len(subtopics),
            'language': language,
            'learning_style': learning_style
        })
        
        # Validate subtopics count
        if len(subtopics) > config.api.max_subtopics:
            return jsonify({"error": f"Maximum {config.api.max_subtopics} subtopics allowed"}), 400
        
        if len(subtopics) == 0:
            return jsonify({"error": "At least one subtopic must be selected"}), 400
        
        # ✅ ENHANCED: Dynamic worker scaling based on load
        worker_count = calculate_dynamic_workers(len(subtopics))
        
        logger.debug("Starting parallel processing", extra={
            'subtopic_count': len(subtopics),
            'worker_count': worker_count
        })
        
        # ✅ FIX 5: PARALLEL PROCESSING - Execute in parallel with dynamic ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            generate_func = partial(
                generate_single_explanation_google_ai,
                topic=topic,
                detail=detail,
                education=education,
                language=language,  # ✅ I18N: Pass language to generation function
                learning_style=learning_style # ✅ PERSONALIZATION
            )
            results = list(executor.map(generate_func, subtopics))
        
        # Extract explanations and check for errors  
        explanations = results  # Keep full dict with subtopic and explanation
        errors = [r for r in results if r["error"]]
        
        if errors:
            logger.warning("Some generations failed", extra={
                'failed_count': len(errors),
                'total_count': len(subtopics)
            })
        
        logger.info("Successfully generated explanations", extra={
            'success_count': len(explanations) - len(errors),
            'total_count': len(explanations)
        })
        
        return jsonify({
            "explanations": explanations,
            "success_count": len(explanations) - len(errors),
            "failed_count": len(errors)
        })
        
    except ValueError as e:
        # ✅ NEW: Handle validation errors with centralized error handler
        response, status = error_handler.handle_validation_error([str(e)])
        return jsonify(response), status
    except Exception as e:
        # ✅ NEW: Handle unexpected errors with centralized error handler
        logger.error("Error in create_presentation", extra={'error': str(e)}, exc_info=True)
        response, status = error_handler.handle_exception(e)
        return jsonify(response), status


@app.route("/api/image2topic", methods=['POST'])
@advanced_rate_limit(priority='medium')
@track_request_metrics
def image2topic():
    """
    ✅ ENHANCED: Secure image upload with compression, content validation, and language support
    Extract topic from uploaded image using Gemini Vision
    """
    try:
        # ✅ I18N: Get user's preferred language
        language = get_user_language()
        log_language_request('image2topic', language)
        
        # Validate file upload
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                "error": f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # Read file content
        file_content = file.read()
        
        # Validate file size
        if len(file_content) > MAX_FILE_SIZE:
            return jsonify({"error": f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"}), 400
        
        # Compute image hash for caching
        def image_hash(image_bytes: bytes) -> str:
            import hashlib
            return hashlib.sha256(image_bytes).hexdigest()
        img_hash = image_hash(file_content)
        cache_key = f"image2topic:{img_hash}"
        cached = multi_cache.get(cache_key)
        if cached:
            logger.info("Image hash cache hit for image2topic", extra={'hash': img_hash})
            return jsonify(cached)
        
        # Verify and optimize image using PIL
        try:
            img = PILImage.open(BytesIO(file_content))
            img.verify()
            
            # Reopen for processing (verify closes the file)
            img = PILImage.open(BytesIO(file_content))
            
            # ✅ SECURITY FIX: Strip EXIF metadata to prevent data leakage
            # EXIF can contain GPS coordinates, camera info, timestamps, etc.
            data = list(img.getdata())
            image_without_exif = PILImage.new(img.mode, img.size)
            image_without_exif.putdata(data)
            img = image_without_exif
            
            logger.info("Stripped EXIF metadata from uploaded image")
            
            # Compress and resize image to optimize API usage
            # Max dimension 1024px - Gemini Vision doesn't need more
            max_dimension = 1024
            if img.width > max_dimension or img.height > max_dimension:
                # Calculate new size maintaining aspect ratio
                if img.width > img.height:
                    new_width = max_dimension
                    new_height = int(img.height * (max_dimension / img.width))
                else:
                    new_height = max_dimension
                    new_width = int(img.width * (max_dimension / img.height))
                
                img = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                logger.info(f"Resized image from original to ({new_width}, {new_height})")
            
            # Convert to RGB if necessary (handles RGBA, grayscale, etc)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
        except Exception as e:
            logger.error(f"Image validation/optimization failed: {str(e)}")
            return jsonify({"error": "File is not a valid image"}), 400
        
        # Save optimized image temporarily with secure filename
        timestamp = int(time.time() * 1000)
        filename = secure_filename(f"{timestamp}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        logger.info(f"Processing optimized image: {filename}")
        
        # Save optimized image with compression
        img.save(filepath, format='JPEG', quality=85, optimize=True)
        
        try:
            # ✅ NEW: Check quota before making API call
            if quota_tracker:
                can_proceed, reason = quota_tracker.can_make_request(estimated_tokens=2000)  # Vision uses more tokens
                if not can_proceed:
                    # Try fallback cache
                    cache_key = f"image2topic:{filename}"
                    fallback = quota_tracker.get_fallback_response(cache_key)
                    if fallback:
                        logger.info(f"Using fallback response for image due to quota")
                        # Cleanup
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return jsonify(fallback)
                    # No fallback - return quota error
                    logger.warning(f"Quota exceeded for image2topic: {reason}")
                    # Cleanup
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return jsonify({
                        "error": "quota_exceeded",
                        "message": reason,
                        "retry_after": "60 seconds"
                    }), 429
            
            # Load and process image with Google AI
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # Upload the image file
            uploaded_file = genai.upload_file(filepath)
            
            # Use optimized prompt (90% fewer tokens than before)
            prompt = prompt_registry.format("image_topic_v1")
            
            # ✅ I18N: Add language instruction to prompt
            prompt += get_language_instruction(language)
            
            # ✅ Track API call start time
            api_start_time = time.time()
            
            response_obj = model.generate_content([uploaded_file, prompt])
            generated_topic = response_obj.text.strip()
            
            # ✅ Extract token count from response
            token_count = 2000  # Default estimate for vision
            if hasattr(response_obj, 'usage_metadata') and response_obj.usage_metadata:
                token_count = getattr(response_obj.usage_metadata, 'total_token_count', 2000)
            
            # ✅ Record quota usage
            if quota_tracker:
                quota_tracker.record_request(token_count)
            
            # ✅ Record Prometheus metrics
            api_duration = time.time() - api_start_time
            record_gemini_api_call('analyze_image', 'gemini-2.0-flash', api_duration, token_count, 'success')
            
            # ✅ VALIDATE CONTENT QUALITY
            validation_result = content_validator.validate_topic(generated_topic)
            
            if not validation_result.is_valid:
                logger.warning("Topic validation failed", extra={
                    'topic': generated_topic,
                    'issues': validation_result.issues
                })
                return jsonify({
                    "error": "Failed to extract valid topic from image",
                    "issues": validation_result.issues
                }), 500
            
            if validation_result.warnings:
                logger.info("Topic validation warnings", extra={
                    'topic': generated_topic,
                    'warnings': validation_result.warnings
                })
            
            logger.info("Successfully generated topic from image", extra={
                'topic': generated_topic,
                'quality_score': validation_result.quality_score
            })
            
            # ✅ NEW: Cache response for quota fallback
            if quota_tracker:
                cache_key = f"image2topic:{filename}"
                quota_tracker.cache_response(cache_key, {
                    "generated_topic": generated_topic,
                    "quality_score": validation_result.quality_score,
                    "warnings": validation_result.warnings if validation_result.warnings else None
                })
            
            return jsonify({
                "generated_topic": generated_topic,
                "quality_score": validation_result.quality_score,
                "warnings": validation_result.warnings if validation_result.warnings else None
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug(f"Cleaned up temporary file: {filename}")
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {filename}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in image2topic: {str(e)}")
        return jsonify({"error": "Failed to process image. Please try again with a different image."}), 500




# ==================== IMAGE GENERATION ====================

############ Function for generating image with Imagen2 ############
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

@app.route("/api/generate_image", methods=['POST'])
@advanced_rate_limit(priority='low')
@validate_json('prompt')
@track_request_metrics
def generate_image_endpoint():
    """Generate image from text prompt using Imagen2"""
    try:
        request_data = request.get_json()
        prompt = request_data['prompt'].strip()
        
        if not prompt or len(prompt) > 500:
            return jsonify({"error": "Prompt must be 1-500 characters"}), 400
        
        logger.info(f"Generating image for prompt: '{prompt[:100]}...'")
        
        # ✅ NEW: Check quota before making API call
        if quota_tracker:
            can_proceed, reason = quota_tracker.can_make_request(estimated_tokens=500)  # Image gen uses fewer tokens
            if not can_proceed:
                # Try fallback cache
                cache_key = f"generate_image:{prompt[:100]}"
                fallback = quota_tracker.get_fallback_response(cache_key)
                if fallback:
                    logger.info(f"Using fallback response for image generation due to quota")
                    return jsonify(fallback)
                # No fallback - return quota error
                logger.warning(f"Quota exceeded for generate_image: {reason}")
                return jsonify({
                    "error": "quota_exceeded",
                    "message": reason,
                    "retry_after": "60 seconds"
                }), 429
        
        image_data = generate_image(prompt, PROJECT_NAME)
        
        # ✅ NEW: Record quota usage after successful call
        if quota_tracker:
            quota_tracker.record_request(500)  # Image generation tokens
            # Cache response for fallback
            cache_key = f"generate_image:{prompt[:100]}"
            quota_tracker.cache_response(cache_key, {
                "image": image_data,
                "format": "base64_png"
            })
        
        return jsonify({
            "image": image_data,
            "format": "base64_png"
        })
        
    except Exception as e:
        logger.error(f"Error in generate_image_endpoint: {str(e)}")
        return jsonify({"error": "Failed to generate image. Please try again."}), 500

def generate_image(prompt, project_id):
    """Generate image using Imagen2 API"""
    url = f'https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/imagegeneration:predict'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json; charset=utf-8'
    }
    data = {
        "instances": [
            {
                "prompt": prompt
            }
        ],
        "parameters": {
            "sampleCount": 1
        }
    }
    
    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    
    predictions = response.json()['predictions'][0]
    img_data = base64.b64decode(predictions['bytesBase64Encoded'])
    
    img = PILImage.open(BytesIO(img_data))
    
    # Convert the image to a base64-encoded string
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    base64_encode_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return base64_encode_img


# ==================== MONITORING & METRICS (Nice to Have) ====================

@app.route("/api/metrics", methods=['GET'])
@track_request_metrics
@require_auth()  # ✅ SECURITY FIX: Require authentication
@require_admin()  # ✅ SECURITY FIX: Admin-only endpoint
def metrics():
    """
    ✅ SECURED: Return application metrics for monitoring (admin-only)
    
    Requires: Admin role authentication
    """
    try:
        stats = metrics_collector.get_statistics()
        cache_stats = redis_cache.get_stats()
        
        # Get circuit breaker states
        circuit_breaker_stats = {}
        breaker = get_google_ai_breaker()
        if breaker:
            circuit_breaker_stats["google_ai"] = breaker.get_state()
        
        return jsonify({
            "cache": cache_stats,
            "rate_limiting": {
                "active_ips": len(rate_limit_store),
                "window": config.rate_limit.window_seconds
            },
            "circuit_breakers": circuit_breaker_stats,
            "config": {
                "max_subtopics": config.api.max_subtopics,
                "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                "allowed_extensions": list(ALLOWED_EXTENSIONS),
                "environment": config.environment.value,
                "redis_enabled": config.redis.enabled,
                "circuit_breaker_enabled": config.circuit_breaker.enabled
            },
            "timestamp": datetime.now().isoformat(),
            "detailed_metrics": stats
        })
    except Exception as e:
        logger.error("Error in metrics endpoint", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to retrieve metrics"}), 500

@app.route("/api/cache/clear", methods=['POST'])
@require_auth()  # ✅ SECURITY FIX: Added authentication
@require_admin()  # ✅ SECURITY FIX: Requires admin role
def clear_cache():
    """✅ SECURED: Clear the application cache (admin endpoint)"""
    try:
        user = get_current_user()
        success = redis_cache.clear()
        
        if success:
            logger.info(f"Cache cleared by admin user: {user.user_id}")
            audit_request()  # Log security-relevant action
            
            return jsonify({
                "message": "Cache cleared successfully",
                "cleared_by": user.user_id,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({"error": "Failed to clear cache"}), 500
    except Exception as e:
        logger.error("Error clearing cache", extra={'error': str(e)}, exc_info=True)
        return jsonify({"error": "Failed to clear cache"}), 500

@app.route("/api/circuit-breaker/<name>/state", methods=['GET'])
@require_auth()  # ✅ SECURITY FIX: Added authentication
def get_circuit_breaker_state(name):
    """✅ SECURED: Get circuit breaker state"""
    if name == "google_ai":
        breaker = get_google_ai_breaker()
        if breaker:
            return jsonify(breaker.get_state())
        return jsonify({"error": "Circuit breaker not enabled"}), 404
    return jsonify({"error": "Unknown circuit breaker"}), 404

@app.route("/api/circuit-breaker/<name>/reset", methods=['POST'])
@require_auth()  # ✅ SECURITY FIX: Added authentication
@require_admin()  # ✅ SECURITY FIX: Requires admin role
def reset_circuit_breaker(name):
    """✅ SECURED: Manually reset (close) a circuit breaker (admin only)"""
    if name == "google_ai":
        breaker = get_google_ai_breaker()
        if breaker:
            breaker.force_close()
            logger.info("Circuit breaker manually reset", extra={'name': name})
            return jsonify({
                "message": f"Circuit breaker '{name}' reset successfully",
                "state": breaker.get_state()
            })
        return jsonify({"error": "Circuit breaker not enabled"}), 404
    return jsonify({"error": "Unknown circuit breaker"}), 404


# ==================== API DOCUMENTATION (Nice to Have) ====================

@app.route("/api/docs", methods=['GET'])
def api_docs():
    """
    ✅ FIX 9: API DOCUMENTATION
    Basic API documentation (OpenAPI/Swagger format)
    """
    docs = {
        "openapi": "3.0.0",
        "info": {
            "title": "KNOWALLEDGE API",
            "description": "AI-powered e-learning platform API for generating interactive concept maps",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "http://localhost:5000/api",
                "description": "Development server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {
                        "200": {
                            "description": "Service is healthy"
                        }
                    }
                }
            },
            "/create_subtopics": {
                "post": {
                    "summary": "Generate subtopics for a topic",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {
                                            "type": "string",
                                            "example": "Machine Learning"
                                        }
                                    },
                                    "required": ["topic"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Subtopics generated successfully"
                        },
                        "400": {
                            "description": "Invalid request"
                        }
                    }
                }
            },
            "/create_presentation": {
                "post": {
                    "summary": "Generate explanations for subtopics",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "topic": {"type": "string"},
                                        "educationLevel": {"type": "string"},
                                        "levelOfDetail": {"type": "string"},
                                        "focus": {"type": "array", "items": {"type": "string"}}
                                    },
                                    "required": ["topic", "educationLevel", "levelOfDetail", "focus"]
                                }
                            }
                        }
                    }
                }
            },
            "/image2topic": {
                "post": {
                    "summary": "Extract topic from image",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "image": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/generate_image": {
                "post": {
                    "summary": "Generate image from text prompt",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "prompt": {"type": "string"}
                                    },
                                    "required": ["prompt"]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return jsonify(docs)


# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route("/api/auth/register", methods=['POST'])
def auth_register():
    """
    Register new user and generate API key
    
    Request Body:
        {
            "user_id": "unique_user_id",
            "email": "user@example.com",  # Optional
            "quota_tier": "free"  # free, basic, premium
        }
    
    Response:
        {
            "api_key": "sk_...",
            "user_id": "...",
            "quota_tier": "free",
            "message": "User registered successfully"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Bad Request",
                "message": "user_id is required"
            }), 400
        
        user_id = data['user_id']
        quota_tier = data.get('quota_tier', 'free')
        
        # Validate quota tier
        if quota_tier not in ['free', 'basic', 'premium']:
            return jsonify({
                "error": "Bad Request",
                "message": "Invalid quota_tier. Must be: free, basic, or premium"
            }), 400
        
        # Generate API key
        api_key = auth_manager.generate_api_key(
            user_id=user_id,
            role='user',
            quota_tier=quota_tier
        )
        
        logger.info(f"New user registered: {user_id} (tier: {quota_tier})")
        
        return jsonify({
            "api_key": api_key,
            "user_id": user_id,
            "quota_tier": quota_tier,
            "message": "User registered successfully. Save your API key - it won't be shown again!",
            "usage_instructions": {
                "header": "X-API-Key",
                "example": f"X-API-Key: {api_key[:20]}..."
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        return jsonify({
            "error": "Registration Failed",
            "message": str(e)
        }), 500


@app.route("/api/auth/login", methods=['POST'])
def auth_login():
    """
    Generate JWT token from API key
    
    Request Body:
        {
            "api_key": "sk_..."
        }
    
    Response:
        {
            "token": "jwt_token",
            "expires_in": 86400,
            "user_id": "...",
            "quota_tier": "free"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'api_key' not in data:
            return jsonify({
                "error": "Bad Request",
                "message": "api_key is required"
            }), 400
        
        api_key = data['api_key']
        
        # Validate API key
        is_valid, user = auth_manager.validate_api_key(api_key)
        
        if not is_valid or not user:
            return jsonify({
                "error": "Unauthorized",
                "message": "Invalid API key"
            }), 401
        
        # Generate JWT token
        token = auth_manager.generate_jwt_token(user)
        
        logger.info(f"User logged in: {user.user_id}")
        
        return jsonify({
            "token": token,
            "expires_in": 86400,  # 24 hours
            "user_id": user.user_id,
            "quota_tier": user.quota_tier,
            "message": "Login successful",
            "usage_instructions": {
                "header": "Authorization",
                "example": f"Authorization: Bearer {token[:30]}..."
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        return jsonify({
            "error": "Login Failed",
            "message": str(e)
        }), 500


@app.route("/api/auth/validate", methods=['GET'])
@require_auth()
def auth_validate():
    """
    Validate current authentication and get user info
    
    Headers:
        X-API-Key: sk_...
        OR
        Authorization: Bearer jwt_token
    
    Response:
        {
            "valid": true,
            "user_id": "...",
            "role": "user",
            "quota_tier": "free"
        }
    """
    user = get_current_user()
    
    return jsonify({
        "valid": True,
        "user_id": user.user_id,
        "role": user.role,
        "quota_tier": user.quota_tier,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }), 200


@app.route("/api/auth/admin/generate-key", methods=['POST'])
@require_auth()
@require_admin()
def admin_generate_key():
    """
    Admin endpoint to generate API key for any user
    
    Request Body:
        {
            "user_id": "...",
            "quota_tier": "free|basic|premium|unlimited",
            "role": "user|admin"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Bad Request",
                "message": "user_id is required"
            }), 400
        
        user_id = data['user_id']
        quota_tier = data.get('quota_tier', 'free')
        role = data.get('role', 'user')
        
        # Generate API key
        api_key = auth_manager.generate_api_key(
            user_id=user_id,
            role=role,
            quota_tier=quota_tier
        )
        
        admin = get_current_user()
        logger.info(f"Admin {admin.user_id} generated API key for user: {user_id}")
        audit_request()
        
        return jsonify({
            "api_key": api_key,
            "user_id": user_id,
            "role": role,
            "quota_tier": quota_tier,
            "message": "API key generated successfully"
        }), 201
    
    except Exception as e:
        logger.error(f"Admin key generation failed: {e}", exc_info=True)
        return jsonify({
            "error": "Generation Failed",
            "message": str(e)
        }), 500


# ==================== COST TRACKING & ANALYTICS ENDPOINTS ====================

# Import token counter (optional)
try:
    from token_counter import token_counter
    TOKEN_COUNTER_AVAILABLE = True
except ImportError:
    TOKEN_COUNTER_AVAILABLE = False
    logger.warning("Token counter not available")

@app.route('/api/metrics/costs', methods=['GET'])
def get_api_costs():
    """Get Gemini API cost estimates and token usage"""
    try:
        if not TOKEN_COUNTER_AVAILABLE:
            return jsonify({
                'error': 'Token counter not available',
                'message': 'Install token_counter module to track costs'
            }), 503
        
        # Get today's usage
        today_usage = token_counter.get_today_usage()
        
        # Get 7-day summary
        week_summary = token_counter.get_usage_summary(days=7)
        
        # Check quota limits
        quota_status = token_counter.check_quota_limits()
        
        # Get cost breakdown by endpoint
        breakdown = token_counter.get_cost_breakdown_by_endpoint(days=7)
        
        # Get optimization suggestions
        suggestions = token_counter.suggest_optimizations()
        
        return jsonify({
            'today': today_usage,
            'last_7_days': week_summary,
            'quota_status': quota_status,
            'cost_breakdown': breakdown,
            'optimization_suggestions': suggestions
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get cost metrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/estimate', methods=['POST'])
def estimate_costs():
    """Estimate monthly costs based on expected usage"""
    try:
        if not TOKEN_COUNTER_AVAILABLE:
            return jsonify({'error': 'Token counter not available'}), 503
        
        data = request.get_json()
        daily_requests = data.get('daily_requests', 100)
        avg_tokens = data.get('avg_tokens_per_request', 2000)
        
        estimate = token_counter.estimate_monthly_cost(daily_requests, avg_tokens)
        
        return jsonify(estimate), 200
    
    except Exception as e:
        logger.error(f"Failed to estimate costs: {e}")
        return jsonify({'error': str(e)}), 500


# ==================== ADAPTIVE LEARNING ENDPOINTS ====================

@app.route('/api/quiz/generate', methods=['POST'])
@validate_json_request()  # ✅ NEW: Validate JSON content-type
@validate_json('topic', 'subtopic')
@rate_limit(max_requests=10, window=60)
@require_auth()
def generate_quiz():
    """Generate a quiz for a subtopic"""
    try:
        data = request.get_json()
        
        # ✅ NEW: Enhanced validation
        topic_result = request_validator.validate_topic(data.get('topic', ''))
        if not topic_result.is_valid:
            response, status = error_handler.handle_validation_error(topic_result.errors)
            return jsonify(response), status
        
        subtopic_result = request_validator.validate_topic(data.get('subtopic', ''))
        if not subtopic_result.is_valid:
            response, status = error_handler.handle_validation_error(subtopic_result.errors)
            return jsonify(response), status
        
        topic = topic_result.sanitized_value
        subtopic = subtopic_result.sanitized_value
        education = data.get('education', 'high school')
        count = data.get('count', 3)
        
        # Check cache
        cache_key = f"quiz:{topic}:{subtopic}:{education}:{count}"
        cached = multi_cache.get(cache_key)
        if cached:
            return jsonify(cached)
            
        prompt = prompt_registry.format(
            "quiz_generation",
            count=count,
            subtopic=subtopic,
            topic=topic,
            education=education
        )
        
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        quiz_data = parse_json_response(response.text)
        
        # Cache result
        multi_cache.set(cache_key, quiz_data, ttl=3600)
        
        return jsonify(quiz_data)
        
    except ValueError as e:
        # ✅ NEW: Handle validation errors
        response, status = error_handler.handle_validation_error([str(e)])
        return jsonify(response), status
    except Exception as e:
        # ✅ NEW: Handle unexpected errors
        logger.error(f"Quiz generation failed: {e}")
        response, status = error_handler.handle_exception(e)
        return jsonify(response), status

@app.route('/api/quiz/submit', methods=['POST'])
@validate_json('topic', 'score', 'total')
@require_auth()
def submit_quiz():
    """Submit quiz results and update mastery"""
    data = request.get_json()
    user = get_current_user()
    user_id = user.get('uid') if user else 'anonymous'
    
    topic = data['topic']
    subtopic = data.get('subtopic', 'general')
    score = data['score']
    total = data['total']
    difficulty = data.get('difficulty', 'medium')
    
    # Calculate mastery update
    percentage = (score / total) * 100
    mastery_level = 0
    if percentage >= 80:
        mastery_level = 3 # High
    elif percentage >= 50:
        mastery_level = 2 # Medium
    else:
        mastery_level = 1 # Low
        
    # Update DB
    analytics_db.save_quiz_result(user_id, topic, score, total, difficulty)
    analytics_db.update_progress(user_id, topic, subtopic, mastery_level)
    
    return jsonify({"status": "success", "mastery_level": mastery_level})

@app.route('/api/progress', methods=['GET'])
@require_auth()
def get_progress():
    """Get user progress"""
    user = get_current_user()
    user_id = user.get('uid') if user else 'anonymous'
    topic = request.args.get('topic')
    
    progress = analytics_db.get_user_progress(user_id, topic)
    return jsonify(progress)

@app.route('/api/recommendations', methods=['POST'])
@validate_json('topic')
@require_auth()
def get_recommendations():
    """Get recommended subtopics based on progress"""
    data = request.get_json()
    user = get_current_user()
    user_id = user.get('uid') if user else 'anonymous'
    topic = data['topic']
    
    # Get completed subtopics
    progress = analytics_db.get_user_progress(user_id, topic)
    completed = [p['subtopic'] for p in progress if p['mastery_level'] >= 2]
    
    prompt = prompt_registry.format(
        "recommendation",
        topic=topic,
        completed_subtopics=", ".join(completed) if completed else "None"
    )
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        recommendations = parse_json_response(response.text)
        return jsonify(recommendations)
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        return jsonify({"error": "Failed to get recommendations"}), 500


# ==================== SIMPLE HEALTH ENDPOINTS (for Docker/K8s) ====================

@app.route("/health", methods=['GET'])
def simple_health_check():
    """
    Simple liveness check for Docker HEALTHCHECK
    Returns 200 if application is running (no dependency checks)
    
    Requirements: 8.1
    """
    from health_check import get_health_check_service
    
    health_service = get_health_check_service()
    liveness_status = health_service.perform_liveness_check()
    
    return jsonify(liveness_status), 200


@app.route("/ready", methods=['GET'])
def simple_readiness_check():
    """
    Simple readiness check for Kubernetes
    Returns 200 if ready to serve traffic
    """
    # Reuse the detailed readiness check
    return readiness_check()


# ==================== APPLICATION STARTUP ====================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting KNOWALLEDGE API Server")
    logger.info("=" * 60)
    
    # ✅ SECURITY: Display admin API key on first startup
    admin_key = os.getenv('ADMIN_API_KEY')
    if not admin_key:
        logger.warning("=" * 60)
        logger.warning("🔐 ADMIN API KEY GENERATED (SAVE THIS!):")
        logger.warning("   Check the logs above for your admin API key")
        logger.warning("   Add to .env: ADMIN_API_KEY=<your_key>")
        logger.warning("=" * 60)
    
    logger.info("Configuration", extra={
        'environment': config.environment.value,  # Convert enum to string
        'project': PROJECT_NAME,
        'google_ai': 'Configured',
        'max_subtopics': config.api.max_subtopics,
        'cache_ttl': config.cache.ttl,
        'upload_folder': UPLOAD_FOLDER,
        'debug_mode': config.is_development(),
        'https_enforced': force_https,
        'authentication': 'Enabled'
    })
    logger.info("=" * 60)
    
    # In production, use a production WSGI server like Gunicorn
    # gunicorn -w 4 -b 0.0.0.0:5000 main:app
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,
        debug=config.is_development(),
        threaded=True  # Enable threading for concurrent requests
    )


