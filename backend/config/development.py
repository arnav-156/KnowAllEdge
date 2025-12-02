"""
Development Environment Configuration
For local development with relaxed security and verbose logging
"""

import os
from typing import Dict, Any

class DevelopmentConfig:
    """Development environment configuration"""
    
    # Environment
    ENV = 'development'
    DEBUG = True
    TESTING = False
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://KNOWALLEDGE_user:dev_password@localhost:5432/KNOWALLEDGE_dev'
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True  # Log SQL queries in development
    SQLALCHEMY_POOL_SIZE = 5
    SQLALCHEMY_MAX_OVERFLOW = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    
    # Redis
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'false').lower() == 'true'
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    JWT_ALGORITHM = 'HS256'
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:8080', 'http://localhost:5173']
    CORS_ALLOW_CREDENTIALS = True
    
    # Rate Limiting (relaxed for development)
    RATE_LIMIT_ENABLED = False
    RATE_LIMIT_STORAGE_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}' if REDIS_ENABLED else 'memory://'
    
    # Quota Management (generous for development)
    QUOTA_FREE_RPM = 100
    QUOTA_FREE_RPD = 10000
    QUOTA_FREE_TPM = 1000000
    QUOTA_BASIC_RPM = 300
    QUOTA_BASIC_RPD = 30000
    QUOTA_BASIC_TPM = 3000000
    QUOTA_PREMIUM_RPM = 1000
    QUOTA_PREMIUM_RPD = 100000
    QUOTA_PREMIUM_TPM = 10000000
    
    # Caching
    CACHE_ENABLED = True
    CACHE_TYPE = 'redis' if REDIS_ENABLED else 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_PREFIX = 'KNOWALLEDGE_dev:'
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'logs/development.log'
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 3
    
    # Security (relaxed for development)
    HTTPS_REQUIRED = False
    CSRF_ENABLED = True
    CSRF_TIME_LIMIT = None
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'json'}
    
    # Circuit Breaker
    CIRCUIT_BREAKER_ENABLED = True
    CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION = Exception
    
    # Monitoring
    METRICS_ENABLED = True
    PROMETHEUS_METRICS_PORT = 9090
    
    # Feature Flags
    FEATURES = {
        'gamification': True,
        'analytics': True,
        'study_tools': True,
        'learning_analytics': True,
        'integrations': True,
        'social_features': True,
    }
    
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
        # In development, we're more lenient
        if not cls.GOOGLE_API_KEY:
            print("⚠️ WARNING: GOOGLE_API_KEY not set. Some features will not work.")
        
        return True
