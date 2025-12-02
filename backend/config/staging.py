"""
Staging Environment Configuration
For pre-production testing with production-like settings
"""

import os
from typing import Dict, Any

class StagingConfig:
    """Staging environment configuration"""
    
    # Environment
    ENV = 'staging'
    DEBUG = False
    TESTING = False
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in staging")
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable must be set in staging")
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'connect_args': {
            'sslmode': 'require',
            'connect_timeout': 10,
        }
    }
    
    # Redis
    REDIS_ENABLED = True
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    if not REDIS_PASSWORD:
        raise ValueError("REDIS_PASSWORD environment variable must be set in staging")
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable must be set in staging")
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable must be set in staging")
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_ALGORITHM = 'HS256'
    
    # CORS
    CORS_ORIGINS = [
        'https://staging.KNOWALLEDGE.com',
        'https://staging-app.KNOWALLEDGE.com',
    ]
    CORS_ALLOW_CREDENTIALS = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_STORAGE_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # Quota Management (production-like limits)
    QUOTA_FREE_RPM = 10
    QUOTA_FREE_RPD = 100
    QUOTA_FREE_TPM = 50000
    QUOTA_BASIC_RPM = 30
    QUOTA_BASIC_RPD = 500
    QUOTA_BASIC_TPM = 200000
    QUOTA_PREMIUM_RPM = 100
    QUOTA_PREMIUM_RPD = 2000
    QUOTA_PREMIUM_TPM = 1000000
    
    # Caching
    CACHE_ENABLED = True
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 3600  # 1 hour
    CACHE_KEY_PREFIX = 'KNOWALLEDGE_staging:'
    CACHE_REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/staging.log'
    LOG_MAX_BYTES = 52428800  # 50MB
    LOG_BACKUP_COUNT = 10
    LOG_JSON_FORMAT = True
    
    # Security
    HTTPS_REQUIRED = True
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    }
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = '/app/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'json'}
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION = Exception
    
    # Monitoring
    METRICS_ENABLED = True
    PROMETHEUS_METRICS_PORT = 9090
    SENTRY_DSN = os.getenv('SENTRY_DSN')
    SENTRY_ENVIRONMENT = 'staging'
    SENTRY_TRACES_SAMPLE_RATE = 0.5
    
    # Health Checks
    HEALTH_CHECK_TIMEOUT = 5
    HEALTH_CHECK_INTERVAL = 30
    
    # Feature Flags
    FEATURES = {
        'gamification': True,
        'analytics': True,
        'study_tools': True,
        'learning_analytics': True,
        'integrations': True,
        'social_features': True,
    }
    
    # Backup
    BACKUP_ENABLED = True
    BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = 7
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
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
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        # Validate password strength
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        
        if len(cls.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        
        if len(cls.REDIS_PASSWORD) < 16:
            raise ValueError("REDIS_PASSWORD must be at least 16 characters")
        
        return True
