"""
Centralized Logging Configuration
Configures log aggregation and shipping for ELK/Loki stacks

Requirements: 8.6
"""

import os
import logging
import logging.handlers
import json
from typing import Dict, Any, Optional
from datetime import datetime


class CentralizedLoggingConfig:
    """
    Configures centralized logging with support for:
    - ELK Stack (Elasticsearch, Logstash, Kibana)
    - Loki (Grafana Loki)
    - File-based logging with rotation
    - JSON structured logging
    """
    
    def __init__(
        self,
        app_name: str = 'KNOWALLEDGE-backend',
        environment: str = None,
        log_level: str = None,
        enable_elk: bool = False,
        enable_loki: bool = False,
        enable_file_logging: bool = True
    ):
        """
        Initialize centralized logging configuration
        
        Args:
            app_name: Application name for log identification
            environment: Environment (development, staging, production)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_elk: Enable ELK stack integration
            enable_loki: Enable Loki integration
            enable_file_logging: Enable file-based logging
        """
        self.app_name = app_name
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
        self.enable_elk = enable_elk or os.getenv('ENABLE_ELK', 'false').lower() == 'true'
        self.enable_loki = enable_loki or os.getenv('ENABLE_LOKI', 'false').lower() == 'true'
        self.enable_file_logging = enable_file_logging
        
        # ELK configuration
        self.logstash_host = os.getenv('LOGSTASH_HOST', 'localhost')
        self.logstash_port = int(os.getenv('LOGSTASH_PORT', '5000'))
        
        # Loki configuration
        self.loki_url = os.getenv('LOKI_URL', 'http://localhost:3100')
        
        # File logging configuration
        self.log_dir = os.getenv('LOG_DIR', 'logs')
        self.log_file = os.path.join(self.log_dir, f'{app_name}.log')
        self.max_bytes = int(os.getenv('LOG_MAX_BYTES', str(10 * 1024 * 1024)))  # 10MB
        self.backup_count = int(os.getenv('LOG_BACKUP_COUNT', '10'))
        
        # Log retention (days)
        self.retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
        
        self.logger = logging.getLogger()
    
    def configure(self):
        """Configure all logging handlers"""
        # Set log level
        self.logger.setLevel(getattr(logging, self.log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add console handler (always enabled)
        self._add_console_handler()
        
        # Add file handler if enabled
        if self.enable_file_logging:
            self._add_file_handler()
        
        # Add ELK handler if enabled
        if self.enable_elk:
            self._add_elk_handler()
        
        # Add Loki handler if enabled
        if self.enable_loki:
            self._add_loki_handler()
        
        logging.info(
            f"Centralized logging configured",
            extra={
                'app_name': self.app_name,
                'environment': self.environment,
                'log_level': self.log_level,
                'elk_enabled': self.enable_elk,
                'loki_enabled': self.enable_loki,
                'file_logging_enabled': self.enable_file_logging
            }
        )
    
    def _add_console_handler(self):
        """Add console handler with JSON formatting"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(JSONFormatter(self.app_name, self.environment))
        self.logger.addHandler(console_handler)
    
    def _add_file_handler(self):
        """Add rotating file handler"""
        try:
            # Create log directory if it doesn't exist
            os.makedirs(self.log_dir, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=self.max_bytes,
                backupCount=self.backup_count
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter(self.app_name, self.environment))
            self.logger.addHandler(file_handler)
            
            logging.info(f"File logging enabled: {self.log_file}")
            
        except Exception as e:
            logging.error(f"Failed to configure file logging: {e}")
    
    def _add_elk_handler(self):
        """Add Logstash handler for ELK stack"""
        try:
            from logstash_async.handler import AsynchronousLogstashHandler
            
            elk_handler = AsynchronousLogstashHandler(
                self.logstash_host,
                self.logstash_port,
                database_path=None  # In-memory queue
            )
            elk_handler.setLevel(logging.INFO)
            self.logger.addHandler(elk_handler)
            
            logging.info(f"ELK logging enabled: {self.logstash_host}:{self.logstash_port}")
            
        except ImportError:
            logging.warning("logstash-async not installed. Install with: pip install python-logstash-async")
        except Exception as e:
            logging.error(f"Failed to configure ELK logging: {e}")
    
    def _add_loki_handler(self):
        """Add Loki handler for Grafana Loki"""
        try:
            from logging_loki import LokiHandler
            
            loki_handler = LokiHandler(
                url=f"{self.loki_url}/loki/api/v1/push",
                tags={"application": self.app_name, "environment": self.environment},
                version="1"
            )
            loki_handler.setLevel(logging.INFO)
            self.logger.addHandler(loki_handler)
            
            logging.info(f"Loki logging enabled: {self.loki_url}")
            
        except ImportError:
            logging.warning("python-logging-loki not installed. Install with: pip install python-logging-loki")
        except Exception as e:
            logging.error(f"Failed to configure Loki logging: {e}")
    
    def create_dashboard_config(self) -> Dict[str, Any]:
        """
        Create dashboard configuration for log visualization
        
        Returns:
            Dictionary with dashboard configuration
        """
        return {
            'elk_dashboard': {
                'enabled': self.enable_elk,
                'kibana_url': os.getenv('KIBANA_URL', 'http://localhost:5601'),
                'index_pattern': f'{self.app_name}-*',
                'retention_days': self.retention_days
            },
            'loki_dashboard': {
                'enabled': self.enable_loki,
                'grafana_url': os.getenv('GRAFANA_URL', 'http://localhost:3000'),
                'datasource': 'Loki',
                'labels': {
                    'application': self.app_name,
                    'environment': self.environment
                }
            },
            'log_retention': {
                'retention_days': self.retention_days,
                'cleanup_enabled': True,
                'cleanup_schedule': '0 2 * * *'  # Daily at 2 AM
            }
        }


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    
    Outputs logs in JSON format with consistent fields:
    - timestamp
    - level
    - logger
    - message
    - context (extra fields)
    """
    
    def __init__(self, app_name: str, environment: str):
        super().__init__()
        self.app_name = app_name
        self.environment = environment
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'application': self.app_name,
            'environment': self.environment
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'levelno', 'lineno', 'module', 'msecs',
                              'message', 'pathname', 'process', 'processName',
                              'relativeCreated', 'thread', 'threadName', 'exc_info',
                              'exc_text', 'stack_info']:
                    log_data[key] = value
        
        return json.dumps(log_data)


def setup_centralized_logging(
    app_name: str = 'KNOWALLEDGE-backend',
    **kwargs
) -> CentralizedLoggingConfig:
    """
    Setup centralized logging
    
    Args:
        app_name: Application name
        **kwargs: Additional configuration options
    
    Returns:
        CentralizedLoggingConfig instance
    
    Requirements: 8.6
    """
    config = CentralizedLoggingConfig(app_name=app_name, **kwargs)
    config.configure()
    return config


def get_log_shipping_config() -> Dict[str, Any]:
    """
    Get log shipping configuration for external tools
    
    Returns:
        Dictionary with log shipping configuration
    """
    return {
        'filebeat': {
            'enabled': os.getenv('ENABLE_FILEBEAT', 'false').lower() == 'true',
            'config_path': '/etc/filebeat/filebeat.yml',
            'log_paths': [
                '/var/log/KNOWALLEDGE/*.log',
                '/var/log/KNOWALLEDGE/app.log'
            ],
            'output': {
                'elasticsearch': {
                    'hosts': [os.getenv('ELASTICSEARCH_HOST', 'localhost:9200')],
                    'index': 'KNOWALLEDGE-%{+yyyy.MM.dd}'
                }
            }
        },
        'promtail': {
            'enabled': os.getenv('ENABLE_PROMTAIL', 'false').lower() == 'true',
            'config_path': '/etc/promtail/promtail.yml',
            'positions_file': '/tmp/positions.yaml',
            'clients': [{
                'url': os.getenv('LOKI_URL', 'http://localhost:3100') + '/loki/api/v1/push'
            }],
            'scrape_configs': [{
                'job_name': 'KNOWALLEDGE',
                'static_configs': [{
                    'targets': ['localhost'],
                    'labels': {
                        'job': 'KNOWALLEDGE-backend',
                        'environment': os.getenv('ENVIRONMENT', 'development'),
                        '__path__': '/var/log/KNOWALLEDGE/*.log'
                    }
                }]
            }]
        },
        'fluentd': {
            'enabled': os.getenv('ENABLE_FLUENTD', 'false').lower() == 'true',
            'config_path': '/etc/fluent/fluent.conf',
            'source': {
                'type': 'tail',
                'path': '/var/log/KNOWALLEDGE/*.log',
                'pos_file': '/var/log/td-agent/KNOWALLEDGE.pos',
                'tag': 'KNOWALLEDGE.backend'
            },
            'match': {
                'type': 'elasticsearch',
                'host': os.getenv('ELASTICSEARCH_HOST', 'localhost'),
                'port': int(os.getenv('ELASTICSEARCH_PORT', '9200')),
                'index_name': 'KNOWALLEDGE',
                'type_name': 'logs'
            }
        }
    }


# Example Filebeat configuration
FILEBEAT_CONFIG_EXAMPLE = """
# /etc/filebeat/filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/KNOWALLEDGE/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "KNOWALLEDGE-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"

setup.ilm.enabled: true
setup.ilm.rollover_alias: "KNOWALLEDGE"
setup.ilm.pattern: "{now/d}-000001"
"""

# Example Promtail configuration
PROMTAIL_CONFIG_EXAMPLE = """
# /etc/promtail/promtail.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: KNOWALLEDGE
    static_configs:
      - targets:
          - localhost
        labels:
          job: KNOWALLEDGE-backend
          environment: production
          __path__: /var/log/KNOWALLEDGE/*.log
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339
"""

# Example Grafana Loki dashboard query
LOKI_DASHBOARD_QUERIES = {
    'error_logs': '{application="KNOWALLEDGE-backend", level="ERROR"}',
    'warning_logs': '{application="KNOWALLEDGE-backend", level="WARNING"}',
    'api_requests': '{application="KNOWALLEDGE-backend"} |= "API request"',
    'slow_queries': '{application="KNOWALLEDGE-backend"} |= "slow query" | json | duration > 1000',
    'user_actions': '{application="KNOWALLEDGE-backend"} |= "user_id" | json'
}
