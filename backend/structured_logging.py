"""
Structured Logging Module
Provides JSON-formatted logging with context and request tracking
Task 3.3: Implement structured logging with JSON format, rotation, and context

✅ SECURITY FIX: Integrated log sanitization to prevent PII leakage
"""

import logging
import json
import sys
import time
import inspect
from datetime import datetime
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import has_request_context, g, request

# ✅ SECURITY: Import sanitization module
try:
    from log_sanitizer import sanitize_log_data
    LOG_SANITIZATION_ENABLED = True
except ImportError:
    LOG_SANITIZATION_ENABLED = False
    print("WARNING: log_sanitizer not available, sensitive data may be logged")

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format
    
    ✅ SECURITY: Automatically sanitizes sensitive data before logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add request context if available
        if has_request_context():
            log_data['request'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
                'request_id': getattr(g, 'request_id', None),
            }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add custom fields from extra
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # ✅ SECURITY: Sanitize log data before outputting
        if LOG_SANITIZATION_ENABLED:
            log_data = sanitize_log_data(log_data)
        
        return json.dumps(log_data)

class StructuredLogger:
    """
    Enhanced wrapper around Python's logging module for structured logging
    Includes log rotation, performance tracking, and specialized logging methods
    """
    
    def __init__(self, name: str, level: str = 'INFO', 
                 log_file: Optional[str] = None,
                 max_bytes: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add console handler with structured formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        # Add file handler with rotation if log_file specified
        if log_file:
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
        
        # Context storage for thread-local context
        self._context = {}
        
        # Performance tracking
        self._start_times = {}
    
    def add_context(self, **kwargs):
        """Add persistent context that will be included in all log messages"""
        self._context.update(kwargs)
    
    def remove_context(self, *keys):
        """Remove context keys"""
        for key in keys:
            self._context.pop(key, None)
    
    def clear_context(self):
        """Clear all persistent context"""
        self._context.clear()
    
    def start_timer(self, operation: str):
        """Start timing an operation"""
        self._start_times[operation] = time.time()
    
    def end_timer(self, operation: str, **kwargs):
        """End timing and log duration"""
        if operation in self._start_times:
            duration = time.time() - self._start_times[operation]
            del self._start_times[operation]
            self.info(f"Operation completed: {operation}", 
                     extra={
                         'operation': operation,
                         'duration_ms': duration * 1000,
                         **kwargs
                     })
            return duration
        return None
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration_ms: float, user_id: str = None, **kwargs):
        """Log HTTP request with standardized format"""
        self.info("HTTP request", 
                 extra={
                     'request_method': method,
                     'request_path': path,
                     'status_code': status_code,
                     'duration_ms': duration_ms,
                     'user_id': user_id,
                     **kwargs
                 })
    
    def log_database_query(self, query_type: str, table: str, 
                          duration_ms: float, rows_affected: int = None, **kwargs):
        """Log database query with performance metrics"""
        self.info("Database query",
                 extra={
                     'query_type': query_type,
                     'table': table,
                     'duration_ms': duration_ms,
                     'rows_affected': rows_affected,
                     **kwargs
                 })
    
    def log_security_event(self, event_type: str, severity: str, 
                          user_id: str = None, ip_address: str = None, **kwargs):
        """Log security-related events"""
        self.warning(f"Security event: {event_type}",
                    extra={
                        'event_type': event_type,
                        'severity': severity,
                        'user_id': user_id,
                        'ip_address': ip_address,
                        **kwargs
                    })
    
    def log_business_event(self, event_name: str, user_id: str = None, **kwargs):
        """Log business events for analytics"""
        self.info(f"Business event: {event_name}",
                 extra={
                     'event_name': event_name,
                     'user_id': user_id,
                     **kwargs
                 })
    
    def log_external_api_call(self, service: str, endpoint: str, 
                             duration_ms: float, status_code: int = None, **kwargs):
        """Log external API calls"""
        self.info(f"External API call: {service}",
                 extra={
                     'service': service,
                     'endpoint': endpoint,
                     'duration_ms': duration_ms,
                     'status_code': status_code,
                     **kwargs
                 })
    
    def log_cache_operation(self, operation: str, key: str, hit: bool = None, **kwargs):
        """Log cache operations"""
        self.debug(f"Cache {operation}",
                  extra={
                      'cache_operation': operation,
                      'cache_key': key,
                      'cache_hit': hit,
                      **kwargs
                  })
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add contextual information to log"""
        context = {**self._context}
        
        if extra:
            context.update(extra)
        
        if has_request_context():
            context['request_id'] = getattr(g, 'request_id', None)
            context['endpoint'] = request.endpoint
            context['user_id'] = getattr(g, 'user_id', None)
        
        # Add caller information
        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            context['caller_module'] = caller_frame.f_globals.get('__name__', 'unknown')
            context['caller_function'] = caller_frame.f_code.co_name
            context['caller_line'] = caller_frame.f_lineno
        
        return {'extra_fields': context}
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self.logger.debug(message, extra=self._add_context(extra))
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self.logger.info(message, extra=self._add_context(extra))
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self.logger.warning(message, extra=self._add_context(extra))
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, extra=self._add_context(extra), exc_info=exc_info)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log critical message"""
        self.logger.critical(message, extra=self._add_context(extra), exc_info=exc_info)

def get_logger(name: str, level: str = 'INFO', 
               log_file: Optional[str] = None,
               max_bytes: int = 10 * 1024 * 1024,
               backup_count: int = 5) -> StructuredLogger:
    """
    Get or create a structured logger with optional file rotation
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file for rotation
        max_bytes: Maximum size of log file before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)
    
    Returns:
        StructuredLogger instance
    
    Example:
        # Console only
        logger = get_logger(__name__)
        
        # With file rotation
        logger = get_logger(__name__, log_file='app.log', max_bytes=5*1024*1024, backup_count=3)
    """
    return StructuredLogger(name, level, log_file, max_bytes, backup_count)


def configure_root_logger(level: str = 'INFO', log_file: Optional[str] = None):
    """
    Configure the root logger for the entire application
    
    Args:
        level: Log level for root logger
        log_file: Optional path to log file
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
