"""
Configuration Management System
Centralized configuration with environment-specific settings
✅ SECURITY: No hardcoded secrets, mandatory validation, rotation support
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import json

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

@dataclass
class RedisConfig:
    """
    ✅ SECURITY: Redis configuration with mandatory password in production
    NO default password - must be provided via environment variable
    """
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None  # ✅ NO DEFAULT - must be set via env var
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    max_connections: int = 50
    
    def __post_init__(self):
        """✅ SECURITY: Validate Redis configuration"""
        # In production, Redis password is REQUIRED if enabled
        env = os.getenv('FLASK_ENV', 'development')
        if self.enabled and env == 'production':
            if not self.password:
                redis_password = os.getenv('REDIS_PASSWORD')
                if not redis_password:
                    raise ValueError(
                        "❌ SECURITY: REDIS_PASSWORD environment variable must be set in production when Redis is enabled. "
                        "Never use default passwords."
                    )
                self.password = redis_password
            
            # Validate password strength
            if self.password and len(self.password) < 16:
                raise ValueError(
                    "❌ SECURITY: Redis password must be at least 16 characters long in production. "
                    "Use: openssl rand -base64 32"
                )
        elif self.enabled and env == 'development':
            # Development: Allow environment variable or warn
            if not self.password:
                redis_password = os.getenv('REDIS_PASSWORD')
                if redis_password:
                    self.password = redis_password
                else:
                    print("⚠️ WARNING: Redis password not set in development. Set REDIS_PASSWORD environment variable.")

@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl: int = 3600  # 1 hour
    max_size: int = 1000
    enabled: bool = True
    use_redis: bool = False  # Flag to use Redis instead of in-memory

@dataclass
class RateLimitConfig:
    """Rate limiting configuration with endpoint-specific limits"""
    max_requests: int = 100
    window_seconds: int = 3600  # 1 hour
    enabled: bool = True
    
    # ✅ ENHANCED: Endpoint-specific rate limits (different costs)
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=lambda: {
        'health': {
            'max_requests': 1000,  # High limit for health checks
            'window_seconds': 60,
            'cost_multiplier': 0.0  # Free
        },
        'subtopics': {
            'max_requests': 50,
            'window_seconds': 3600,
            'cost_multiplier': 1.0  # Standard cost
        },
        'presentation': {
            'max_requests': 30,
            'window_seconds': 3600,
            'cost_multiplier': 3.0  # 3x cost (parallel processing)
        },
        'image2topic': {
            'max_requests': 20,
            'window_seconds': 3600,
            'cost_multiplier': 2.0  # 2x cost (Vision API)
        },
        'generate_image': {
            'max_requests': 10,
            'window_seconds': 3600,
            'cost_multiplier': 10.0  # 10x cost (Imagen2)
        }
    })

@dataclass
class APIConfig:
    """API-specific configuration"""
    timeout: int = 60
    max_retries: int = 3
    max_subtopics: int = 20
    max_parallel_workers: int = 5
    min_parallel_workers: int = 2
    max_parallel_workers_limit: int = 20  # Hard limit
    dynamic_worker_scaling: bool = True  # Enable dynamic scaling based on load

@dataclass
class GeminiConfig:
    """✅ NEW: Gemini AI-specific configuration"""
    # Model selection
    default_model: str = "gemini-2.0-flash"
    fallback_model: str = "gemini-1.5-flash"
    vision_model: str = "gemini-2.0-flash"  # For image analysis
    
    # Model parameters
    temperature: float = 0.7  # 0.0-1.0, higher = more creative
    top_p: float = 0.95       # 0.0-1.0, nucleus sampling
    top_k: int = 40           # Top-k sampling
    max_output_tokens: int = 2048
    
    # Safety settings
    harm_block_threshold: str = "BLOCK_MEDIUM_AND_ABOVE"
    
    # Available models for A/B testing
    available_models: list = field(default_factory=lambda: [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-1.0-pro"
    ])
    
    # Model capabilities (for routing)
    model_capabilities: Dict[str, Dict] = field(default_factory=lambda: {
        "gemini-2.0-flash": {
            "max_tokens": 8192,
            "cost_per_1k_input": 0.00015,
            "cost_per_1k_output": 0.00060,
            "supports_vision": True,
            "speed": "fast"
        },
        "gemini-1.5-flash": {
            "max_tokens": 8192,
            "cost_per_1k_input": 0.00035,
            "cost_per_1k_output": 0.00105,
            "supports_vision": True,
            "speed": "fast"
        },
        "gemini-1.5-pro": {
            "max_tokens": 8192,
            "cost_per_1k_input": 0.00125,
            "cost_per_1k_output": 0.00375,
            "supports_vision": True,
            "speed": "medium"
        }
    })

@dataclass
class TokenBudgetConfig:
    """✅ NEW: Token budget and quota management"""
    # Daily limits
    daily_token_limit: int = 1_000_000  # 1M tokens per day
    daily_request_limit: int = 10_000
    daily_cost_limit: float = 50.0  # $50 per day
    
    # Monthly limits
    monthly_token_limit: int = 25_000_000  # 25M tokens per month
    monthly_request_limit: int = 250_000
    monthly_cost_limit: float = 1000.0  # $1000 per month
    
    # Alert thresholds (percentage of limit)
    warning_threshold: float = 0.75  # 75% usage warning
    critical_threshold: float = 0.90  # 90% usage critical alert
    
    # Cost tracking
    enable_cost_tracking: bool = True
    cost_log_file: str = "token_costs.json"
    
    # Alert settings
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None
    
    # Usage reset
    daily_reset_hour: int = 0  # Reset at midnight UTC
    
    def get_alert_thresholds(self) -> Dict[str, int]:
        """Get alert threshold values"""
        return {
            'daily_token_warning': int(self.daily_token_limit * self.warning_threshold),
            'daily_token_critical': int(self.daily_token_limit * self.critical_threshold),
            'daily_cost_warning': self.daily_cost_limit * self.warning_threshold,
            'daily_cost_critical': self.daily_cost_limit * self.critical_threshold,
            'monthly_token_warning': int(self.monthly_token_limit * self.warning_threshold),
            'monthly_token_critical': int(self.monthly_token_limit * self.critical_threshold),
        }

@dataclass
class CDNConfig:
    """✅ NEW: CDN configuration for image caching"""
    # CDN provider
    enabled: bool = False
    provider: str = "cloudflare"  # cloudflare, cloudinary, fastly
    
    # CloudFlare settings
    cloudflare_zone_id: Optional[str] = None
    cloudflare_api_token: Optional[str] = None
    cloudflare_cache_ttl: int = 86400  # 24 hours
    
    # Cloudinary settings
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    
    # Image optimization
    auto_format: bool = True  # Automatic format conversion (WebP, AVIF)
    auto_quality: bool = True  # Automatic quality optimization
    lazy_loading: bool = True
    
    # Cache settings
    cache_control_max_age: int = 86400  # 24 hours
    immutable_cache: bool = True  # Cache-Control: immutable
    
    # CDN URLs
    cdn_base_url: Optional[str] = None  # e.g., https://cdn.example.com
    
    # Image transformations
    default_transformations: Dict[str, str] = field(default_factory=lambda: {
        'thumbnail': 'w_150,h_150,c_fill',
        'medium': 'w_800,h_800,c_limit',
        'large': 'w_1920,h_1920,c_limit'
    })

@dataclass
class ConfigAuditLog:
    """
    ✅ AUDIT: Configuration audit logging
    Tracks all configuration changes and access for compliance
    """
    enabled: bool = True
    log_file: str = "config_audit.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level: str = "INFO"
    max_bytes: int = 10_485_760  # 10MB
    backup_count: int = 5
    
    # Track these config changes
    track_secrets: bool = True  # Log secret access (not values)
    track_env_vars: bool = True  # Log env var loading
    track_overrides: bool = True  # Log environment overrides
    track_validation: bool = True  # Log validation results
    
    # Audit logger instance
    _logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        """Initialize audit logger"""
        if self.enabled:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup audit logger with rotation"""
        from logging.handlers import RotatingFileHandler
        
        self._logger = logging.getLogger('config_audit')
        self._logger.setLevel(getattr(logging, self.log_level))
        
        # Don't add handlers if already exists (avoid duplicates)
        if not self._logger.handlers:
            # File handler with rotation
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            formatter = logging.Formatter(self.log_format)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            
            # Prevent propagation to root logger
            self._logger.propagate = False
    
    def log_event(self, event_type: str, message: str, details: Optional[Dict] = None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (CONFIG_LOAD, SECRET_ACCESS, VALIDATION, etc.)
            message: Human-readable message
            details: Additional details (sanitized, no secret values)
        """
        if not self.enabled or not self._logger:
            return
        
        # Build log message
        log_msg = f"[{event_type}] {message}"
        
        if details:
            # Sanitize details (never log actual secret values)
            sanitized = self._sanitize_details(details)
            log_msg += f" | Details: {sanitized}"
        
        self._logger.info(log_msg)
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Remove sensitive values from details"""
        sanitized = {}
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                sanitized[key] = '***REDACTED***' if value else None
            else:
                sanitized[key] = value
        return sanitized
    
    def log_config_load(self, environment: str, source: str):
        """Log configuration loading"""
        if self.track_env_vars:
            self.log_event(
                'CONFIG_LOAD',
                f'Configuration loaded from {source}',
                {'environment': environment, 'source': source}
            )
    
    def log_secret_access(self, secret_name: str, action: str):
        """Log secret access (not the value)"""
        if self.track_secrets:
            self.log_event(
                'SECRET_ACCESS',
                f'Secret accessed: {secret_name}',
                {'secret_name': secret_name, 'action': action}
            )
    
    def log_validation(self, validation_type: str, status: str, details: Optional[Dict] = None):
        """Log validation results"""
        if self.track_validation:
            self.log_event(
                'VALIDATION',
                f'{validation_type} validation: {status}',
                details
            )
    
    def log_override(self, config_key: str, old_value: Any, new_value: Any):
        """Log configuration overrides"""
        if self.track_overrides:
            # Sanitize values if they look like secrets
            if any(sensitive in config_key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                old_value = '***REDACTED***' if old_value else None
                new_value = '***REDACTED***' if new_value else None
            
            self.log_event(
                'CONFIG_OVERRIDE',
                f'Configuration overridden: {config_key}',
                {'key': config_key, 'old_value': old_value, 'new_value': new_value}
            )


@dataclass
class ConfigAuditLog:
    """
    ✅ AUDIT: Configuration audit logging
    Tracks all configuration changes and access for compliance
    """
    enabled: bool = True
    log_file: str = "config_audit.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level: str = "INFO"
    max_bytes: int = 10_485_760  # 10MB
    backup_count: int = 5
    
    # Track these config changes
    track_secrets: bool = True  # Log secret access (not values)
    track_env_vars: bool = True  # Log env var loading
    track_overrides: bool = True  # Log environment overrides
    track_validation: bool = True  # Log validation results
    
    # Audit logger instance
    _logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        """Initialize audit logger"""
        if self.enabled:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup audit logger with rotation"""
        from logging.handlers import RotatingFileHandler
        
        self._logger = logging.getLogger('config_audit')
        self._logger.setLevel(getattr(logging, self.log_level))
        
        # Don't add handlers if already exists (avoid duplicates)
        if not self._logger.handlers:
            # File handler with rotation
            handler = RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            formatter = logging.Formatter(self.log_format)
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            
            # Prevent propagation to root logger
            self._logger.propagate = False
    
    def log_event(self, event_type: str, message: str, details: Optional[Dict] = None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (CONFIG_LOAD, SECRET_ACCESS, VALIDATION, etc.)
            message: Human-readable message
            details: Additional details (sanitized, no secret values)
        """
        if not self.enabled or not self._logger:
            return
        
        # Build log message
        log_msg = f"[{event_type}] {message}"
        
        if details:
            # Sanitize details (never log actual secret values)
            sanitized = self._sanitize_details(details)
            log_msg += f" | Details: {sanitized}"
        
        self._logger.info(log_msg)
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Remove sensitive values from details"""
        sanitized = {}
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                sanitized[key] = '***REDACTED***' if value else None
            else:
                sanitized[key] = value
        return sanitized
    
    def log_config_load(self, environment: str, source: str):
        """Log configuration loading"""
        if self.track_env_vars:
            self.log_event(
                'CONFIG_LOAD',
                f'Configuration loaded from {source}',
                {'environment': environment, 'source': source}
            )
    
    def log_secret_access(self, secret_name: str, action: str):
        """Log secret access (not the value)"""
        if self.track_secrets:
            self.log_event(
                'SECRET_ACCESS',
                f'Secret accessed: {secret_name}',
                {'secret_name': secret_name, 'action': action}
            )
    
    def log_validation(self, validation_type: str, status: str, details: Optional[Dict] = None):
        """Log validation results"""
        if self.track_validation:
            self.log_event(
                'VALIDATION',
                f'{validation_type} validation: {status}',
                details
            )
    
    def log_override(self, config_key: str, old_value: Any, new_value: Any):
        """Log configuration overrides"""
        if self.track_overrides:
            # Sanitize values if they look like secrets
            if any(sensitive in config_key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                old_value = '***REDACTED***' if old_value else None
                new_value = '***REDACTED***' if new_value else None
            
            self.log_event(
                'CONFIG_OVERRIDE',
                f'Configuration overridden: {config_key}',
                {'key': config_key, 'old_value': old_value, 'new_value': new_value}
            )


@dataclass
class SecretRotationConfig:
    """
    ✅ SECURITY: Secret rotation configuration
    Manages automatic rotation of API keys, passwords, and tokens
    """
    # Rotation policy
    enabled: bool = True
    rotation_interval_days: int = 90  # Rotate every 90 days (industry standard)
    rotation_warning_days: int = 14  # Warn 14 days before expiration
    
    # Rotation tracking file
    rotation_file: str = "secret_rotation.json"
    
    # Secrets to track (key: secret_name, value: rotation metadata)
    tracked_secrets: Dict[str, Dict] = field(default_factory=dict)
    
    # Alert settings
    alert_on_expiry: bool = True
    alert_on_rotation: bool = True
    alert_email: Optional[str] = None
    alert_webhook: Optional[str] = None
    
    # Grace period (allow old key to work during transition)
    grace_period_hours: int = 24  # 24 hours overlap
    
    # Supported secret types
    secret_types: List[str] = field(default_factory=lambda: [
        'GOOGLE_API_KEY',
        'REDIS_PASSWORD',
        'SECRETS_MASTER_PASSWORD',
        'CLOUDFLARE_API_TOKEN',
        'CLOUDINARY_API_SECRET',
        'JWT_SECRET_KEY'
    ])
    
    def __post_init__(self):
        """Initialize rotation tracking"""
        self.load_rotation_state()
    
    def load_rotation_state(self):
        """Load rotation state from file"""
        if os.path.exists(self.rotation_file):
            try:
                with open(self.rotation_file, 'r') as f:
                    self.tracked_secrets = json.load(f)
                print(f"✅ Loaded rotation state for {len(self.tracked_secrets)} secrets")
            except Exception as e:
                print(f"⚠️ Failed to load rotation state: {e}")
                self.tracked_secrets = {}
        else:
            self.tracked_secrets = {}
    
    def save_rotation_state(self):
        """Save rotation state to file"""
        try:
            with open(self.rotation_file, 'w') as f:
                json.dump(self.tracked_secrets, f, indent=2, default=str)
            print("✅ Rotation state saved")
        except Exception as e:
            print(f"❌ Failed to save rotation state: {e}")
    
    def register_secret(self, secret_name: str, secret_value: Optional[str] = None):
        """
        Register a secret for rotation tracking
        
        Args:
            secret_name: Name of the secret (e.g., 'GOOGLE_API_KEY')
            secret_value: Current secret value (optional, for hash tracking)
        """
        if secret_name not in self.tracked_secrets:
            # Calculate hash if value provided (for change detection)
            secret_hash = None
            if secret_value:
                secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:16]
            
            self.tracked_secrets[secret_name] = {
                'registered_at': datetime.now().isoformat(),
                'last_rotated': datetime.now().isoformat(),
                'next_rotation': (datetime.now() + timedelta(days=self.rotation_interval_days)).isoformat(),
                'rotation_count': 0,
                'secret_hash': secret_hash,
                'status': 'active'
            }
            
            self.save_rotation_state()
            print(f"✅ Registered secret: {secret_name}")
        else:
            # Update hash if value provided and changed
            if secret_value:
                new_hash = hashlib.sha256(secret_value.encode()).hexdigest()[:16]
                old_hash = self.tracked_secrets[secret_name].get('secret_hash')
                
                if old_hash and new_hash != old_hash:
                    print(f"🔄 Secret changed detected: {secret_name}")
                    self.mark_rotated(secret_name)
    
    def mark_rotated(self, secret_name: str):
        """Mark a secret as rotated"""
        if secret_name in self.tracked_secrets:
            now = datetime.now()
            self.tracked_secrets[secret_name]['last_rotated'] = now.isoformat()
            self.tracked_secrets[secret_name]['next_rotation'] = (
                now + timedelta(days=self.rotation_interval_days)
            ).isoformat()
            self.tracked_secrets[secret_name]['rotation_count'] += 1
            self.tracked_secrets[secret_name]['status'] = 'active'
            
            self.save_rotation_state()
            print(f"✅ Secret rotated: {secret_name} (rotation #{self.tracked_secrets[secret_name]['rotation_count']})")
    
    def check_expiration(self, secret_name: str) -> Dict:
        """
        Check if a secret needs rotation
        
        Returns:
            dict: {
                'needs_rotation': bool,
                'days_until_expiry': int,
                'status': str  # 'active', 'warning', 'expired'
            }
        """
        if secret_name not in self.tracked_secrets:
            return {
                'needs_rotation': False,
                'days_until_expiry': None,
                'status': 'untracked'
            }
        
        metadata = self.tracked_secrets[secret_name]
        next_rotation = datetime.fromisoformat(metadata['next_rotation'])
        now = datetime.now()
        
        days_until_expiry = (next_rotation - now).days
        
        if days_until_expiry < 0:
            status = 'expired'
            needs_rotation = True
        elif days_until_expiry <= self.rotation_warning_days:
            status = 'warning'
            needs_rotation = True
        else:
            status = 'active'
            needs_rotation = False
        
        return {
            'needs_rotation': needs_rotation,
            'days_until_expiry': days_until_expiry,
            'status': status,
            'last_rotated': metadata['last_rotated'],
            'rotation_count': metadata['rotation_count']
        }
    
    def check_all_secrets(self) -> Dict[str, Dict]:
        """Check expiration status of all tracked secrets"""
        results = {}
        for secret_name in self.tracked_secrets:
            results[secret_name] = self.check_expiration(secret_name)
        return results
    
    def get_expiring_secrets(self) -> List[str]:
        """Get list of secrets that need rotation"""
        expiring = []
        for secret_name, status in self.check_all_secrets().items():
            if status['needs_rotation']:
                expiring.append(secret_name)
        return expiring
    
    def generate_rotation_report(self) -> str:
        """Generate a report of secret rotation status"""
        report = []
        report.append("=" * 60)
        report.append("SECRET ROTATION STATUS REPORT")
        report.append("=" * 60)
        report.append(f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Rotation Policy: Every {self.rotation_interval_days} days")
        report.append(f"Warning Threshold: {self.rotation_warning_days} days before expiry")
        report.append("")
        
        all_status = self.check_all_secrets()
        
        # Group by status
        expired = [k for k, v in all_status.items() if v['status'] == 'expired']
        warning = [k for k, v in all_status.items() if v['status'] == 'warning']
        active = [k for k, v in all_status.items() if v['status'] == 'active']
        
        # Expired secrets (CRITICAL)
        if expired:
            report.append("🚨 EXPIRED SECRETS (IMMEDIATE ACTION REQUIRED):")
            for secret in expired:
                status = all_status[secret]
                report.append(f"  ❌ {secret}")
                report.append(f"     Last Rotated: {status['last_rotated']}")
                report.append(f"     Days Overdue: {abs(status['days_until_expiry'])}")
                report.append(f"     Rotation Count: {status['rotation_count']}")
            report.append("")
        
        # Warning secrets
        if warning:
            report.append("⚠️ SECRETS EXPIRING SOON:")
            for secret in warning:
                status = all_status[secret]
                report.append(f"  ⚠️ {secret}")
                report.append(f"     Last Rotated: {status['last_rotated']}")
                report.append(f"     Days Until Expiry: {status['days_until_expiry']}")
                report.append(f"     Rotation Count: {status['rotation_count']}")
            report.append("")
        
        # Active secrets
        if active:
            report.append("✅ ACTIVE SECRETS:")
            for secret in active:
                status = all_status[secret]
                report.append(f"  ✅ {secret}")
                report.append(f"     Days Until Expiry: {status['days_until_expiry']}")
                report.append(f"     Rotation Count: {status['rotation_count']}")
            report.append("")
        
        report.append("=" * 60)
        report.append(f"Summary: {len(expired)} expired, {len(warning)} warning, {len(active)} active")
        report.append("=" * 60)
        
        return "\n".join(report)

@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_enabled: bool = True
    file_path: str = "app.log"
    console_enabled: bool = True

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    enabled: bool = True
    failure_threshold: int = 5  # Number of failures before opening circuit
    timeout: int = 60  # Seconds to wait before attempting reset
    success_threshold: int = 2  # Successful calls needed to close circuit
    expected_exception: type = Exception

@dataclass
class SecurityConfig:
    """
    ✅ SECURITY: Security configuration with secret validation
    Enforces strong secrets in production
    """
    cors_enabled: bool = True
    cors_origins: list = None
    max_content_length: int = 10 * 1024 * 1024  # 10MB
    allowed_upload_extensions: set = None
    
    # ✅ NEW: Secret strength requirements
    min_api_key_length: int = 32  # Minimum API key length
    min_password_length: int = 16  # Minimum password length
    require_strong_secrets: bool = True  # Enforce in production
    
    def __post_init__(self):
        if self.cors_origins is None:
            # Default to localhost only in development
            env = os.getenv('FLASK_ENV', 'development')
            if env == 'production':
                # In production, must be explicitly configured via CORS_ORIGINS env var
                # Never allow wildcard "*" - will raise error if not set
                origins_str = os.getenv('CORS_ORIGINS', '')
                if not origins_str:
                    raise ValueError(
                        "CORS_ORIGINS environment variable must be set in production. "
                        "Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
                    )
                self.cors_origins = [origin.strip() for origin in origins_str.split(',')]
                # Validate no wildcards in production
                if '*' in str(self.cors_origins):
                    raise ValueError(
                        "Wildcard '*' CORS origins are not allowed in production. "
                        "Specify exact domain origins."
                    )
            else:
                # Development: localhost only
                self.cors_origins = ["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"]
        
        # Validate CORS origins format
        for origin in self.cors_origins:
            if origin == '*':
                raise ValueError("Wildcard '*' CORS origin is not secure. Use specific domains.")
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid CORS origin format: {origin}. Must start with http:// or https://")
        
        if self.allowed_upload_extensions is None:
            self.allowed_upload_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    def validate_secret(self, secret_name: str, secret_value: Optional[str], secret_type: str = 'password') -> bool:
        """
        ✅ SECURITY: Validate secret strength
        
        Args:
            secret_name: Name of the secret (for error messages)
            secret_value: Secret value to validate
            secret_type: Type of secret ('password', 'api_key', 'token')
        
        Returns:
            bool: True if valid, raises ValueError if invalid
        """
        env = os.getenv('FLASK_ENV', 'development')
        
        # Only enforce in production if required
        if not self.require_strong_secrets and env != 'production':
            return True
        
        if not secret_value:
            if env == 'production':
                raise ValueError(f"❌ SECURITY: {secret_name} must be set in production")
            else:
                print(f"⚠️ WARNING: {secret_name} not set")
                return False
        
        # Check minimum length
        min_length = self.min_api_key_length if secret_type == 'api_key' else self.min_password_length
        
        if len(secret_value) < min_length:
            raise ValueError(
                f"❌ SECURITY: {secret_name} must be at least {min_length} characters long. "
                f"Current length: {len(secret_value)}. "
                f"Generate strong secret: openssl rand -base64 {min_length}"
            )
        
        # Check for weak patterns (production only)
        if env == 'production':
            weak_patterns = [
                'password', 'secret', 'admin', '12345', 'qwerty', 
                'test', 'demo', 'default', 'changeme'
            ]
            
            for pattern in weak_patterns:
                if pattern.lower() in secret_value.lower():
                    raise ValueError(
                        f"❌ SECURITY: {secret_name} contains weak pattern '{pattern}'. "
                        f"Use a cryptographically secure random value."
                    )
        
        return True

class Config:
    """
    ✅ SECURITY: Main configuration class with secret validation and rotation
    ✅ AUDIT: Configuration audit logging enabled
    ✅ VALIDATION: Required environment variables validated on startup
    """
    
    def __init__(self, environment: Optional[str] = None):
        self.environment = Environment(environment or os.getenv('FLASK_ENV', 'development'))
        
        # ✅ NEW: Initialize audit logging first
        self.audit_log = ConfigAuditLog()
        self.audit_log.log_config_load(self.environment.value, 'environment')
        
        # Load configurations
        self.redis = RedisConfig()
        self.cache = CacheConfig()
        self.rate_limit = RateLimitConfig()
        self.api = APIConfig()
        self.logging = LoggingConfig()
        self.security = SecurityConfig()
        self.circuit_breaker = CircuitBreakerConfig()
        
        # ✅ NEW: Enhanced configurations
        self.gemini = GeminiConfig()
        self.token_budget = TokenBudgetConfig()
        self.cdn = CDNConfig()
        self.secret_rotation = SecretRotationConfig()  # ✅ NEW: Secret rotation
        
        # Google AI (legacy, kept for compatibility)
        self.google_project_id = os.getenv('GOOGLE_CLOUD_PROJECT', '')
        self.google_location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        
        # ✅ VALIDATION: Check required environment variables FIRST
        self._validate_required_env_vars()
        
        # Load from environment variables
        self._load_from_environment()
        
        # ✅ SECURITY: Validate secrets after loading
        self._validate_secrets()
        
        # ✅ SECURITY: Register secrets for rotation tracking
        self._register_secrets()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        
        # ✅ SECURITY: Check for expiring secrets
        self._check_secret_expiration()
        
        # ✅ AUDIT: Log successful configuration load
        self.audit_log.log_event('CONFIG_INIT', 'Configuration initialized successfully', {
            'environment': self.environment.value,
            'redis_enabled': self.redis.enabled,
            'cache_enabled': self.cache.enabled,
            'cdn_enabled': self.cdn.enabled
        })
    
    def _validate_required_env_vars(self):
        """
        ✅ VALIDATION: Validate that all required environment variables are set
        Fail fast with clear error messages before app starts
        """
        env = os.getenv('FLASK_ENV', 'development')
        missing_vars = []
        optional_missing = []
        
        # Define required env vars by environment
        if env == 'production':
            # CRITICAL: Required in production
            required_vars = {
                'GOOGLE_API_KEY': 'Gemini API key for AI features',
                'SECRETS_MASTER_PASSWORD': 'Master password for encrypting secrets'
            }
            
            # Optional but recommended
            recommended_vars = {
                'REDIS_PASSWORD': 'Redis password (if Redis enabled)',
                'CORS_ORIGINS': 'Allowed CORS origins for production',
                'ALERT_EMAIL': 'Email for quota/rotation alerts',
                'ALERT_WEBHOOK': 'Webhook URL for alerts'
            }
        elif env == 'staging':
            required_vars = {
                'GOOGLE_API_KEY': 'Gemini API key for AI features'
            }
            recommended_vars = {
                'SECRETS_MASTER_PASSWORD': 'Master password for encrypting secrets'
            }
        else:  # development, testing
            required_vars = {
                'GOOGLE_API_KEY': 'Gemini API key for AI features'
            }
            recommended_vars = {}
        
        # Check required variables
        print(f"🔍 Validating required environment variables for {env}...")
        
        for var_name, description in required_vars.items():
            value = os.getenv(var_name)
            if not value:
                missing_vars.append(f"  ❌ {var_name}: {description}")
                self.audit_log.log_validation('ENV_VAR', 'FAILED', {
                    'variable': var_name,
                    'reason': 'missing'
                })
            else:
                print(f"  ✅ {var_name} is set")
                self.audit_log.log_validation('ENV_VAR', 'SUCCESS', {
                    'variable': var_name
                })
        
        # Check recommended variables (warning only)
        for var_name, description in recommended_vars.items():
            value = os.getenv(var_name)
            if not value:
                optional_missing.append(f"  ⚠️ {var_name}: {description}")
        
        # If any required vars are missing, fail fast
        if missing_vars:
            error_msg = "\n" + "=" * 70 + "\n"
            error_msg += "❌ CONFIGURATION ERROR: Missing Required Environment Variables\n"
            error_msg += "=" * 70 + "\n"
            error_msg += f"Environment: {env}\n\n"
            error_msg += "Missing required variables:\n"
            error_msg += "\n".join(missing_vars)
            error_msg += "\n\n"
            error_msg += "How to fix:\n"
            error_msg += "  1. Create a .env file in the backend directory\n"
            error_msg += "  2. Add the missing variables:\n"
            error_msg += "     GOOGLE_API_KEY=your_api_key_here\n"
            error_msg += "     SECRETS_MASTER_PASSWORD=$(openssl rand -base64 32)\n"
            error_msg += "  3. Restart the application\n"
            error_msg += "\n"
            error_msg += "Get Gemini API key: https://aistudio.google.com/apikey\n"
            error_msg += "=" * 70 + "\n"
            
            self.audit_log.log_validation('ENV_VAR_CHECK', 'CRITICAL_FAILURE', {
                'missing_count': len(missing_vars),
                'environment': env
            })
            
            raise EnvironmentError(error_msg)
        
        # Show warnings for optional vars
        if optional_missing:
            print("\n" + "=" * 70)
            print("⚠️ WARNING: Optional Environment Variables Not Set")
            print("=" * 70)
            print("\n".join(optional_missing))
            print("\nThese are optional but recommended for production.")
            print("=" * 70 + "\n")
        
        print(f"✅ All required environment variables validated for {env}\n")
        self.audit_log.log_validation('ENV_VAR_CHECK', 'SUCCESS', {
            'environment': env,
            'required_count': len(required_vars),
            'optional_missing_count': len(optional_missing)
        })
    
    def _load_from_environment(self):
        """✅ SECURITY: Load configuration from environment variables (NO defaults for secrets)"""
        self.audit_log.log_event('ENV_LOAD', 'Loading configuration from environment variables')
        
        # Gemini API Key (NO default)
        self.gemini_api_key = os.getenv('GOOGLE_API_KEY', '')
        if self.gemini_api_key:
            self.audit_log.log_secret_access('GOOGLE_API_KEY', 'loaded')
        
        # Gemini model overrides
        if os.getenv('GEMINI_MODEL'):
            old_value = self.gemini.default_model
            self.gemini.default_model = os.getenv('GEMINI_MODEL')
            self.audit_log.log_override('GEMINI_MODEL', old_value, self.gemini.default_model)
        if os.getenv('GEMINI_TEMPERATURE'):
            old_value = self.gemini.temperature
            self.gemini.temperature = float(os.getenv('GEMINI_TEMPERATURE'))
            self.audit_log.log_override('GEMINI_TEMPERATURE', old_value, self.gemini.temperature)
        
        # Token budget overrides
        if os.getenv('DAILY_TOKEN_LIMIT'):
            self.token_budget.daily_token_limit = int(os.getenv('DAILY_TOKEN_LIMIT'))
        if os.getenv('DAILY_COST_LIMIT'):
            self.token_budget.daily_cost_limit = float(os.getenv('DAILY_COST_LIMIT'))
        if os.getenv('ALERT_EMAIL'):
            self.token_budget.alert_email = os.getenv('ALERT_EMAIL')
        if os.getenv('ALERT_WEBHOOK'):
            self.token_budget.alert_webhook = os.getenv('ALERT_WEBHOOK')
        
        # CDN overrides
        if os.getenv('CDN_ENABLED'):
            self.cdn.enabled = os.getenv('CDN_ENABLED').lower() == 'true'
        if os.getenv('CDN_PROVIDER'):
            self.cdn.provider = os.getenv('CDN_PROVIDER')
        if os.getenv('CLOUDFLARE_ZONE_ID'):
            self.cdn.cloudflare_zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
        if os.getenv('CLOUDFLARE_API_TOKEN'):
            self.cdn.cloudflare_api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        if os.getenv('CLOUDINARY_CLOUD_NAME'):
            self.cdn.cloudinary_cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        if os.getenv('CDN_BASE_URL'):
            self.cdn.cdn_base_url = os.getenv('CDN_BASE_URL')
    
    def _validate_secrets(self):
        """
        ✅ SECURITY: Validate all secrets for strength and presence
        Called after _load_from_environment()
        """
        env = os.getenv('FLASK_ENV', 'development')
        
        self.audit_log.log_event('SECRET_VALIDATION', f'Starting secret validation for {env}')
        
        # Only enforce strict validation in production
        if env != 'production':
            print("⚠️ Running in non-production mode. Secret validation relaxed.")
            self.audit_log.log_validation('SECRET_STRENGTH', 'SKIPPED', {
                'reason': 'non-production environment'
            })
            return
        
        print("🔐 Validating production secrets...")
        validation_results = []
        
        # Validate Gemini API Key
        try:
            self.security.validate_secret(
                'GOOGLE_API_KEY',
                self.gemini_api_key,
                'api_key'
            )
            print("✅ GOOGLE_API_KEY validated")
            validation_results.append(('GOOGLE_API_KEY', 'SUCCESS'))
            self.audit_log.log_validation('SECRET_STRENGTH', 'SUCCESS', {
                'secret': 'GOOGLE_API_KEY',
                'type': 'api_key'
            })
        except ValueError as e:
            print(f"❌ {e}")
            validation_results.append(('GOOGLE_API_KEY', 'FAILED'))
            self.audit_log.log_validation('SECRET_STRENGTH', 'FAILED', {
                'secret': 'GOOGLE_API_KEY',
                'error': str(e)
            })
            raise
        
        # Validate Redis password (if enabled)
        if self.redis.enabled:
            try:
                self.security.validate_secret(
                    'REDIS_PASSWORD',
                    self.redis.password,
                    'password'
                )
                print("✅ REDIS_PASSWORD validated")
                validation_results.append(('REDIS_PASSWORD', 'SUCCESS'))
                self.audit_log.log_validation('SECRET_STRENGTH', 'SUCCESS', {
                    'secret': 'REDIS_PASSWORD',
                    'type': 'password'
                })
            except ValueError as e:
                print(f"❌ {e}")
                validation_results.append(('REDIS_PASSWORD', 'FAILED'))
                self.audit_log.log_validation('SECRET_STRENGTH', 'FAILED', {
                    'secret': 'REDIS_PASSWORD',
                    'error': str(e)
                })
                raise
        
        # Validate CDN secrets (if enabled)
        if self.cdn.enabled:
            if self.cdn.provider == 'cloudflare' and self.cdn.cloudflare_api_token:
                try:
                    self.security.validate_secret(
                        'CLOUDFLARE_API_TOKEN',
                        self.cdn.cloudflare_api_token,
                        'api_key'
                    )
                    print("✅ CLOUDFLARE_API_TOKEN validated")
                    validation_results.append(('CLOUDFLARE_API_TOKEN', 'SUCCESS'))
                    self.audit_log.log_validation('SECRET_STRENGTH', 'SUCCESS', {
                        'secret': 'CLOUDFLARE_API_TOKEN'
                    })
                except ValueError as e:
                    print(f"❌ {e}")
                    validation_results.append(('CLOUDFLARE_API_TOKEN', 'FAILED'))
                    self.audit_log.log_validation('SECRET_STRENGTH', 'FAILED', {
                        'secret': 'CLOUDFLARE_API_TOKEN',
                        'error': str(e)
                    })
                    raise
            
            if self.cdn.provider == 'cloudinary' and self.cdn.cloudinary_api_secret:
                try:
                    self.security.validate_secret(
                        'CLOUDINARY_API_SECRET',
                        self.cdn.cloudinary_api_secret,
                        'api_key'
                    )
                    print("✅ CLOUDINARY_API_SECRET validated")
                    validation_results.append(('CLOUDINARY_API_SECRET', 'SUCCESS'))
                    self.audit_log.log_validation('SECRET_STRENGTH', 'SUCCESS', {
                        'secret': 'CLOUDINARY_API_SECRET'
                    })
                except ValueError as e:
                    print(f"❌ {e}")
                    validation_results.append(('CLOUDINARY_API_SECRET', 'FAILED'))
                    self.audit_log.log_validation('SECRET_STRENGTH', 'FAILED', {
                        'secret': 'CLOUDINARY_API_SECRET',
                        'error': str(e)
                    })
                    raise
        
        # Validate SECRETS_MASTER_PASSWORD (from secrets_manager)
        master_password = os.getenv('SECRETS_MASTER_PASSWORD')
        if master_password:
            try:
                self.security.validate_secret(
                    'SECRETS_MASTER_PASSWORD',
                    master_password,
                    'password'
                )
                print("✅ SECRETS_MASTER_PASSWORD validated")
                validation_results.append(('SECRETS_MASTER_PASSWORD', 'SUCCESS'))
                self.audit_log.log_validation('SECRET_STRENGTH', 'SUCCESS', {
                    'secret': 'SECRETS_MASTER_PASSWORD'
                })
            except ValueError as e:
                print(f"❌ {e}")
                validation_results.append(('SECRETS_MASTER_PASSWORD', 'FAILED'))
                self.audit_log.log_validation('SECRET_STRENGTH', 'FAILED', {
                    'secret': 'SECRETS_MASTER_PASSWORD',
                    'error': str(e)
                })
                raise
        
        print("✅ All production secrets validated")
        
        # ✅ AUDIT: Log validation summary
        success_count = sum(1 for _, status in validation_results if status == 'SUCCESS')
        self.audit_log.log_event('SECRET_VALIDATION_COMPLETE', 
                                 f'Validated {success_count}/{len(validation_results)} secrets', {
            'total': len(validation_results),
            'success': success_count,
            'failed': len(validation_results) - success_count
        })
    
    def _register_secrets(self):
        """
        ✅ SECURITY: Register secrets for rotation tracking
        Called after _validate_secrets()
        """
        if not self.secret_rotation.enabled:
            self.audit_log.log_event('SECRET_ROTATION', 'Secret rotation disabled')
            return
        
        print("📋 Registering secrets for rotation tracking...")
        self.audit_log.log_event('SECRET_REGISTRATION', 'Starting secret registration for rotation')
        
        registered_count = 0
        
        # Register Gemini API Key
        if self.gemini_api_key:
            self.secret_rotation.register_secret('GOOGLE_API_KEY', self.gemini_api_key)
            self.audit_log.log_secret_access('GOOGLE_API_KEY', 'registered_for_rotation')
            registered_count += 1
        
        # Register Redis password
        if self.redis.enabled and self.redis.password:
            self.secret_rotation.register_secret('REDIS_PASSWORD', self.redis.password)
            self.audit_log.log_secret_access('REDIS_PASSWORD', 'registered_for_rotation')
            registered_count += 1
        
        # Register CDN secrets
        if self.cdn.enabled:
            if self.cdn.cloudflare_api_token:
                self.secret_rotation.register_secret('CLOUDFLARE_API_TOKEN', self.cdn.cloudflare_api_token)
                self.audit_log.log_secret_access('CLOUDFLARE_API_TOKEN', 'registered_for_rotation')
                registered_count += 1
            if self.cdn.cloudinary_api_secret:
                self.secret_rotation.register_secret('CLOUDINARY_API_SECRET', self.cdn.cloudinary_api_secret)
                self.audit_log.log_secret_access('CLOUDINARY_API_SECRET', 'registered_for_rotation')
                registered_count += 1
        
        # Register master password
        master_password = os.getenv('SECRETS_MASTER_PASSWORD')
        if master_password:
            self.secret_rotation.register_secret('SECRETS_MASTER_PASSWORD', master_password)
            self.audit_log.log_secret_access('SECRETS_MASTER_PASSWORD', 'registered_for_rotation')
            registered_count += 1
        
        print(f"✅ Registered {len(self.secret_rotation.tracked_secrets)} secrets for rotation tracking")
        
        self.audit_log.log_event('SECRET_REGISTRATION_COMPLETE', 
                                 f'Registered {registered_count} secrets', {
            'count': registered_count,
            'rotation_interval_days': self.secret_rotation.rotation_interval_days
        })
    
    def _check_secret_expiration(self):
        """
        ✅ SECURITY: Check for expiring secrets and alert
        Called at the end of __init__()
        """
        if not self.secret_rotation.enabled:
            return
        
        expiring_secrets = self.secret_rotation.get_expiring_secrets()
        
        if expiring_secrets:
            print("\n" + "=" * 60)
            print("⚠️ WARNING: SECRETS EXPIRING SOON")
            print("=" * 60)
            
            for secret_name in expiring_secrets:
                status = self.secret_rotation.check_expiration(secret_name)
                
                if status['status'] == 'expired':
                    print(f"🚨 EXPIRED: {secret_name}")
                    print(f"   Last Rotated: {status['last_rotated']}")
                    print(f"   Days Overdue: {abs(status['days_until_expiry'])}")
                else:
                    print(f"⚠️ EXPIRING: {secret_name}")
                    print(f"   Days Until Expiry: {status['days_until_expiry']}")
                    print(f"   Last Rotated: {status['last_rotated']}")
            
            print("=" * 60)
            print("Action Required: Rotate these secrets ASAP")
            print("Generate new secret: openssl rand -base64 32")
            print("=" * 60 + "\n")
            
            # Send alert if configured
            if self.secret_rotation.alert_email or self.secret_rotation.alert_webhook:
                self._send_rotation_alert(expiring_secrets)
    
    def _send_rotation_alert(self, expiring_secrets: List[str]):
        """
        ✅ SECURITY: Send alert for expiring secrets
        TODO: Integrate with email/webhook service
        """
        report = self.secret_rotation.generate_rotation_report()
        
        if self.secret_rotation.alert_email:
            print(f"📧 Would send alert to: {self.secret_rotation.alert_email}")
            # TODO: Implement email sending
            # send_email(self.secret_rotation.alert_email, "Secrets Expiring", report)
        
        if self.secret_rotation.alert_webhook:
            print(f"🔔 Would send webhook to: {self.secret_rotation.alert_webhook}")
            # TODO: Implement webhook
            # requests.post(self.secret_rotation.alert_webhook, json={'report': report})
    
    def _apply_environment_overrides(self):
        """Apply environment-specific configuration overrides"""
        self.audit_log.log_event('ENV_OVERRIDE', f'Applying {self.environment.value} overrides')
        
        if self.environment == Environment.PRODUCTION:
            self.audit_log.log_override('logging.level', self.logging.level, 'WARNING')
            self.logging.level = "WARNING"
            
            self.audit_log.log_override('cache.ttl', self.cache.ttl, 7200)
            self.cache.ttl = 7200  # 2 hours in production
            
            self.audit_log.log_override('rate_limit.max_requests', self.rate_limit.max_requests, 50)
            self.rate_limit.max_requests = 50  # Stricter in production
            
            # ✅ Production: Stricter token budgets
            self.audit_log.log_override('token_budget.daily_token_limit', 
                                       self.token_budget.daily_token_limit, 500_000)
            self.token_budget.daily_token_limit = 500_000  # More conservative
            self.token_budget.daily_cost_limit = 25.0
            self.token_budget.warning_threshold = 0.70  # Earlier warnings
            
            # ✅ Production: Enable CDN
            if self.cdn.cdn_base_url:
                self.audit_log.log_override('cdn.enabled', self.cdn.enabled, True)
                self.cdn.enabled = True
            
        elif self.environment == Environment.DEVELOPMENT:
            self.logging.level = "DEBUG"
            self.cache.enabled = True
            self.rate_limit.enabled = False  # Disable for dev
            
            # ✅ Development: Relaxed budgets
            self.token_budget.daily_token_limit = 100_000
            self.token_budget.daily_cost_limit = 10.0
            self.token_budget.enable_cost_tracking = True  # Track for analysis
            
            # ✅ Development: No CDN
            self.cdn.enabled = False
            
        elif self.environment == Environment.TESTING:
            self.cache.enabled = False
            self.rate_limit.enabled = False
            self.logging.file_enabled = False
            
            # ✅ Testing: Minimal budgets
            self.token_budget.daily_token_limit = 10_000
            self.token_budget.daily_cost_limit = 1.0
            self.token_budget.enable_cost_tracking = False
        
        self.audit_log.log_event('ENV_OVERRIDE_COMPLETE', 
                                f'Applied {self.environment.value} overrides')
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        return self.cache
    
    def get_rate_limit_config(self) -> RateLimitConfig:
        """Get rate limit configuration"""
        return self.rate_limit
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return self.api
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        return self.logging
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.security
    
    def get_gemini_config(self) -> GeminiConfig:
        """✅ NEW: Get Gemini AI configuration"""
        return self.gemini
    
    def get_token_budget_config(self) -> TokenBudgetConfig:
        """✅ NEW: Get token budget configuration"""
        return self.token_budget
    
    def get_cdn_config(self) -> CDNConfig:
        """✅ NEW: Get CDN configuration"""
        return self.cdn
    
    def get_model_for_task(self, task: str = "text") -> str:
        """✅ NEW: Get optimal model for specific task"""
        if task == "vision":
            return self.gemini.vision_model
        elif task == "fast":
            return "gemini-2.0-flash"
        elif task == "quality":
            return "gemini-1.5-pro"
        else:
            return self.gemini.default_model
    
    def get_endpoint_rate_limit(self, endpoint: str) -> Dict:
        """✅ NEW: Get rate limit for specific endpoint"""
        return self.rate_limit.endpoint_limits.get(
            endpoint,
            {
                'max_requests': self.rate_limit.max_requests,
                'window_seconds': self.rate_limit.window_seconds,
                'cost_multiplier': 1.0
            }
        )
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    def get_secret_rotation_config(self) -> SecretRotationConfig:
        """✅ NEW: Get secret rotation configuration"""
        return self.secret_rotation
    
    def get_rotation_status(self) -> Dict:
        """
        ✅ NEW: Get rotation status of all secrets
        Returns dict with rotation status for each secret
        """
        return self.secret_rotation.check_all_secrets()
    
    def generate_rotation_report(self) -> str:
        """
        ✅ NEW: Generate comprehensive rotation report
        Returns formatted string report
        """
        return self.secret_rotation.generate_rotation_report()
    
    def mark_secret_rotated(self, secret_name: str):
        """
        ✅ NEW: Mark a secret as rotated
        Call this after manually rotating a secret
        """
        self.secret_rotation.mark_rotated(secret_name)
        print(f"✅ Marked {secret_name} as rotated")
    
    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            'environment': self.environment.value,
            'cache': {
                'ttl': self.cache.ttl,
                'max_size': self.cache.max_size,
                'enabled': self.cache.enabled
            },
            'rate_limit': {
                'max_requests': self.rate_limit.max_requests,
                'window_seconds': self.rate_limit.window_seconds,
                'enabled': self.rate_limit.enabled,
                'endpoint_limits': self.rate_limit.endpoint_limits
            },
            'api': {
                'timeout': self.api.timeout,
                'max_retries': self.api.max_retries,
                'max_subtopics': self.api.max_subtopics,
                'dynamic_worker_scaling': self.api.dynamic_worker_scaling
            },
            'logging': {
                'level': self.logging.level,
                'file_enabled': self.logging.file_enabled
            },
            'gemini': {
                'default_model': self.gemini.default_model,
                'temperature': self.gemini.temperature,
                'top_p': self.gemini.top_p,
                'max_output_tokens': self.gemini.max_output_tokens
            },
            'token_budget': {
                'daily_token_limit': self.token_budget.daily_token_limit,
                'daily_cost_limit': self.token_budget.daily_cost_limit,
                'warning_threshold': self.token_budget.warning_threshold,
                'enable_cost_tracking': self.token_budget.enable_cost_tracking
            },
            'cdn': {
                'enabled': self.cdn.enabled,
                'provider': self.cdn.provider,
                'cdn_base_url': self.cdn.cdn_base_url
            }
        }

# Global config instance
config = Config()

def get_config() -> Config:
    """Get global configuration instance"""
    return config

def reload_config():
    """Reload configuration (useful for testing)"""
    global config
    config = Config()
    return config
