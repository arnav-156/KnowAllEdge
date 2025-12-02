"""
Production Environment Configuration
Strict security, performance optimization, and comprehensive monitoring
"""

import os
from typing import Dict, Any

class ProductionConfig:
    """Production environment configuration"""
    
    # Environment
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("❌ CRITICAL: SECRET_KEY environment variable must be set in production")
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("❌ CRITICAL: DATABASE_URL environment variable must be set in production")
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 40
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_use_lifo': True,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10,
            'application_name': 'KNOWALLEDGE_production',
        }
    }
    
    # Redis (required in production)
    REDIS_ENABLED = True
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    if not REDIS_PASSWORD:
        raise ValueError("❌ CRITICAL: REDIS_PASSWORD environment variable must be set in production")
    REDIS_SSL = os.getenv('REDIS_SSL', 'true').lower() == 'true'
    REDIS_SSL_CERT_REQS = 'required' if REDIS_SSL else None
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("❌ CRITICAL: GOOGLE_API_KEY environment variable must be set in production")
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("❌ CRITICAL: JWT_SECRET_KEY environment variable must be set in production")
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
    JWT_ALGORITHM = 'HS256'
    
    # CORS (strict whitelist)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://KNOWALLEDGE.com,https://app.KNOWALLEDGE.com').split(',')
    CORS_ALLOW_CREDENTIALS = True
    CORS_MAX_AGE = 3600
    
    # Rate Limiting (strict)
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_STORAGE_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    RATE_LIMIT_STRATEGY = 'fixed-window-elastic-expiry'
    
    # Quota Management (production limits)
    QUOTA_FREE_RPM = 10
    QUOTA_FREE_RPD = 100
    QUOTA_FREE_TPM = 50000
    QUOTA_BASIC_RPM = 30
    QUOTA_BASIC_RPD = 500
    QUOTA_BASIC_TPM = 200000
    QUOTA_PREMIUM_RPM = 100
    QUOTA_PREMIUM_RPD = 2000
    QUOTA_PREMIUM_TPM = 1000000
    QUOTA_ADMIN_RPM = 1000
    QUOTA_ADMIN_RPD = 100000
    QUOTA_ADMIN_TPM = 10000000
    
    # Caching (aggressive)
    CACHE_ENABLED = True
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    CACHE_KEY_PREFIX = 'KNOWALLEDGE_prod:'
    CACHE_REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # Multi-layer caching
    CACHE_L1_ENABLED = True  # In-memory cache
    CACHE_L1_SIZE = 1000
    CACHE_L1_TTL = 300  # 5 minutes
    CACHE_L2_ENABLED = True  # Redis cache
    CACHE_L2_TTL = 3600  # 1 hour
    
    # Logging (structured JSON)
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = 'json'
    LOG_FILE = '/var/log/KNOWALLEDGE/production.log'
    LOG_MAX_BYTES = 104857600  # 100MB
    LOG_BACKUP_COUNT = 30
    LOG_JSON_FORMAT = True
    LOG_SANITIZE_SENSITIVE = True
    
    # Security (maximum)
    HTTPS_REQUIRED = True
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Security Headers (strict)
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://generativelanguage.googleapis.com; frame-ancestors 'none';",
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
    }
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = '/app/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'json'}
    FILE_SCAN_ENABLED = True
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION = Exception
    CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS = 3
    
    # Monitoring (comprehensive)
    METRICS_ENABLED = True
    PROMETHEUS_METRICS_PORT = 9090
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT = 'production'
    SENTRY_TRACES_SAMPLE_RATE = 0.1  # Sample 10% of transactions
    SENTRY_PROFILES_SAMPLE_RATE = 0.1
    
    # APM (Application Performance Monitoring)
    APM_ENABLED = os.getenv('APM_ENABLED', 'false').lower() == 'true'
    APM_SERVICE_NAME = 'KNOWALLEDGE-backend'
    APM_SERVER_URL = os.getenv('APM_SERVER_URL')
    
    # Health Checks
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 30
    READINESS_CHECK_TIMEOUT = 10
    
    # Feature Flags
    FEATURES = {
        'gamification': True,
        'analytics': True,
        'study_tools': True,
        'learning_analytics': True,
        'integrations': True,
        'social_features': True,
    }
    
    # Backup (automated)
    BACKUP_ENABLED = True
    BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = 30
    BACKUP_S3_BUCKET = os.getenv('BACKUP_S3_BUCKET')
    BACKUP_ENCRYPTION_ENABLED = True
    
    # GDPR Compliance
    GDPR_ENABLED = True
    DATA_RETENTION_DAYS = 365
    AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years
    
    # Performance
    WORKER_PROCESSES = int(os.getenv('WORKER_PROCESSES', 4))
    WORKER_THREADS = int(os.getenv('WORKER_THREADS', 2))
    WORKER_TIMEOUT = 120
    WORKER_GRACEFUL_TIMEOUT = 30
    WORKER_MAX_REQUESTS = 1000
    WORKER_MAX_REQUESTS_JITTER = 50
    
    # CDN
    CDN_ENABLED = os.getenv('CDN_ENABLED', 'false').lower() == 'true'
    CDN_URL = os.getenv('CDN_URL')
    STATIC_URL = CDN_URL if CDN_ENABLED else '/static'
    
    # Email (for notifications)
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@KNOWALLEDGE.com')
    
    # Alerting
    ALERT_EMAIL = os.getenv('ALERT_EMAIL')
    ALERT_SLACK_WEBHOOK = os.getenv('ALERT_SLACK_WEBHOOK')
    ALERT_PAGERDUTY_KEY = os.getenv('ALERT_PAGERDUTY_KEY')
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        config = {}
        for key, value in cls.__dict__.items():
            if not key.startswith('_') and not callable(value):
                # Sanitize sensitive values
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                    config[key] = '***REDACTED***'
                else:
                    config[key] = value
        return config
    
    @classmethod
    def validate(cls) -> bool:
        """Validate production configuration"""
        required_vars = [
            'SECRET_KEY',
            'DATABASE_URL',
            'REDIS_PASSWORD',
            'GOOGLE_API_KEY',
            'JWT_SECRET_KEY',
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(cls, var, None):
                missing.append(var)
        
        if missing:
            raise ValueError(f"❌ CRITICAL: Missing required configuration: {', '.join(missing)}")
        
        # Validate password strength (minimum 32 characters)
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("❌ CRITICAL: SECRET_KEY must be at least 32 characters in production")
        
        if len(cls.JWT_SECRET_KEY) < 32:
            raise ValueError("❌ CRITICAL: JWT_SECRET_KEY must be at least 32 characters in production")
        
        if len(cls.REDIS_PASSWORD) < 16:
            raise ValueError("❌ CRITICAL: REDIS_PASSWORD must be at least 16 characters in production")
        
        # Validate HTTPS
        if not cls.HTTPS_REQUIRED:
            raise ValueError("❌ CRITICAL: HTTPS must be required in production")
        
        # Validate CORS origins
        if not cls.CORS_ORIGINS or 'localhost' in str(cls.CORS_ORIGINS):
            raise ValueError("❌ CRITICAL: CORS_ORIGINS must not include localhost in production")
        
        return True
