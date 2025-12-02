"""
Structured Logging Module
Provides JSON-formatted logging with context and request tracking

✅ SECURITY FIX: Integrated log sanitization to prevent PII leakage
"""

import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
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
    Wrapper around Python's logging module for structured logging
    """
    
    def __init__(self, name: str, level: str = 'INFO'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Add console handler with structured formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
    
    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add contextual information to log"""
        context = extra or {}
        
        if has_request_context():
            context['request_id'] = getattr(g, 'request_id', None)
            context['endpoint'] = request.endpoint
        
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

def get_logger(name: str, level: str = 'INFO') -> StructuredLogger:
    """
    Get or create a structured logger
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name, level)
