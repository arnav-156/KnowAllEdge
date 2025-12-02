"""
Configuration Package
Provides environment-specific configurations
"""

import os
from typing import Any

from .development import DevelopmentConfig
from .staging import StagingConfig
from .production import ProductionConfig


def get_config(env: str = None) -> Any:
    """
    Get configuration based on environment
    
    Args:
        env: Environment name (development, staging, production)
             If None, reads from FLASK_ENV or defaults to development
    
    Returns:
        Configuration class for the specified environment
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    env = env.lower()
    
    config_map = {
        'development': DevelopmentConfig,
        'dev': DevelopmentConfig,
        'staging': StagingConfig,
        'stage': StagingConfig,
        'production': ProductionConfig,
        'prod': ProductionConfig,
    }
    
    config_class = config_map.get(env)
    
    if not config_class:
        raise ValueError(
            f"Invalid environment: {env}. "
            f"Must be one of: {', '.join(config_map.keys())}"
        )
    
    # Validate configuration
    try:
        config_class.validate()
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        raise
    
    return config_class


def load_config(app, env: str = None):
    """
    Load configuration into Flask app
    
    Args:
        app: Flask application instance
        env: Environment name (optional)
    """
    config_class = get_config(env)
    
    # Load configuration from class
    app.config.from_object(config_class)
    
    # Log configuration loaded
    print(f"✅ Configuration loaded: {config_class.ENV}")
    
    return app


__all__ = [
    'DevelopmentConfig',
    'StagingConfig',
    'ProductionConfig',
    'get_config',
    'load_config',
]
