"""
Alert Manager System
Implements alerting for system health and performance issues

Requirements: 8.3, 8.4
"""

import os
import time
import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages system alerts and notifications
    
    Features:
    - Configurable alert thresholds
    - Multiple notification channels (email, Slack, PagerDuty)
    - Alert deduplication
    - Alert rate limiting
    - Alert history tracking
    """
    
    def __init__(
        self,
        error_rate_threshold: float = 5.0,  # Percentage
        latency_threshold_ms: float = 1000.0,  # Milliseconds
        cpu_threshold: float = 90.0,  # Percentage
        memory_threshold: float = 90.0,  # Percentage
        disk_threshold: float = 90.0,  # Percentage
        dedup_window_seconds: int = 300,  # 5 minutes
        max_alerts_per_hour: int = 10
    ):
        """
        Initialize alert manager
        
        Args:
            error_rate_threshold: Error rate percentage to trigger alert
            latency_threshold_ms: Latency in ms to trigger alert
            cpu_threshold: CPU usage percentage to trigger alert
            memory_threshold: Memory usage percentage to trigger alert
            disk_threshold: Disk usage percentage to trigger alert
            dedup_window_seconds: Time window for alert deduplication
            max_alerts_per_hour: Maximum alerts per hour per type
        """
        self.error_rate_threshold = error_rate_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.dedup_window_seconds = dedup_window_seconds
        self.max_alerts_per_hour = max_alerts_per_hour
        
        # Alert tracking
        self.recent_alerts: Dict[str, datetime] = {}  # alert_key -> last_sent_time
        self.alert_counts: Dict[str, List[datetime]] = defaultdict(list)  # alert_key -> timestamps
        self.lock = threading.Lock()
        
        # Configuration from environment
        self.email_enabled = self._configure_email()
        self.slack_enabled = self._configure_slack()
        self.pagerduty_enabled = self._configure_pagerduty()
        
        logger.info(
            "Alert manager initialized",
            extra={
                'email_enabled': self.email_enabled,
                'slack_enabled': self.slack_enabled,
                'pagerduty_enabled': self.pagerduty_enabled,
                'error_rate_threshold': error_rate_threshold,
                'latency_threshold_ms': latency_threshold_ms
            }
        )
    
    def _configure_email(self) -> bool:
        """Configure email alerting"""
        self.smtp_host = os.getenv('SMTP_HOST')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_user = os.getenv('SMTP_USER')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.alert_email_from = os.getenv('ALERT_EMAIL_FROM', self.smtp_user)
        self.alert_email_to = os.getenv('ALERT_EMAIL_TO', '').split(',')
        
        enabled = all([self.smtp_host, self.smtp_user, self.smtp_password, self.alert_email_to])
        if enabled:
            logger.info(f"Email alerting enabled: {self.alert_email_to}")
        return enabled
    
    def _configure_slack(self) -> bool:
        """Configure Slack alerting"""
        self.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.slack_channel = os.getenv('SLACK_CHANNEL', '#alerts')
        
        enabled = bool(self.slack_webhook_url)
        if enabled:
            logger.info(f"Slack alerting enabled: {self.slack_channel}")
        return enabled
    
    def _configure_pagerduty(self) -> bool:
        """Configure PagerDuty alerting"""
        self.pagerduty_api_key = os.getenv('PAGERDUTY_API_KEY')
        self.pagerduty_service_key = os.getenv('PAGERDUTY_SERVICE_KEY')
        
        enabled = all([self.pagerduty_api_key, self.pagerduty_service_key])
        if enabled:
            logger.info("PagerDuty alerting enabled")
        return enabled
    
    def _should_send_alert(self, alert_key: str) -> bool:
        """
        Check if alert should be sent based on deduplication and rate limiting
        
        Args:
            alert_key: Unique key for the alert type
        
        Returns:
            True if alert should be sent
        """
        with self.lock:
            now = datetime.now()
            
            # Check deduplication window
            if alert_key in self.recent_alerts:
                last_sent = self.recent_alerts[alert_key]
                if (now - last_sent).total_seconds() < self.dedup_window_seconds:
                    logger.debug(f"Alert {alert_key} deduplicated (sent {(now - last_sent).total_seconds()}s ago)")
                    return False
            
            # Check rate limiting (alerts per hour)
            if alert_key in self.alert_counts:
                # Remove timestamps older than 1 hour
                one_hour_ago = now - timedelta(hours=1)
                self.alert_counts[alert_key] = [
                    ts for ts in self.alert_counts[alert_key]
                    if ts > one_hour_ago
                ]
                
                # Check if we've exceeded the limit
                if len(self.alert_counts[alert_key]) >= self.max_alerts_per_hour:
                    logger.warning(f"Alert {alert_key} rate limited ({len(self.alert_counts[alert_key])} alerts in last hour)")
                    return False
            
            # Update tracking
            self.recent_alerts[alert_key] = now
            self.alert_counts[alert_key].append(now)
            
            return True
    
    def send_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Send alert through configured channels
        
        Args:
            alert_type: Type of alert (error_rate, latency, resource, etc.)
            severity: Alert severity (critical, warning, info)
            title: Alert title
            message: Alert message
            details: Additional alert details
        """
        alert_key = f"{alert_type}:{severity}"
        
        # Check if we should send this alert
        if not self._should_send_alert(alert_key):
            return
        
        logger.warning(
            f"Sending alert: {title}",
            extra={
                'alert_type': alert_type,
                'severity': severity,
                'alert_message': message,  # Renamed to avoid conflict with LogRecord.message
                'details': details
            }
        )
        
        # Send to configured channels
        if self.email_enabled:
            self._send_email_alert(severity, title, message, details)
        
        if self.slack_enabled:
            self._send_slack_alert(severity, title, message, details)
        
        if self.pagerduty_enabled and severity == 'critical':
            self._send_pagerduty_alert(title, message, details)
    
    def _send_email_alert(
        self,
        severity: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ):
        """Send alert via email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{severity.upper()}] {title}"
            msg['From'] = self.alert_email_from
            msg['To'] = ', '.join(self.alert_email_to)
            
            # Create email body
            body = f"""
Alert: {title}
Severity: {severity.upper()}
Time: {datetime.now().isoformat()}

Message:
{message}

Details:
{self._format_details(details)}

---
KnowAllEdge Monitoring System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent to {self.alert_email_to}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)
    
    def _send_slack_alert(
        self,
        severity: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ):
        """Send alert via Slack webhook"""
        try:
            # Color based on severity
            color_map = {
                'critical': '#FF0000',
                'warning': '#FFA500',
                'info': '#0000FF'
            }
            color = color_map.get(severity, '#808080')
            
            # Create Slack message
            payload = {
                'channel': self.slack_channel,
                'username': 'KnowAllEdge Monitor',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color,
                    'title': f"[{severity.upper()}] {title}",
                    'text': message,
                    'fields': self._format_slack_fields(details),
                    'footer': 'KnowAllEdge Monitoring',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("Slack alert sent")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=True)
    
    def _send_pagerduty_alert(
        self,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]]
    ):
        """Send alert via PagerDuty"""
        try:
            payload = {
                'routing_key': self.pagerduty_service_key,
                'event_action': 'trigger',
                'payload': {
                    'summary': title,
                    'severity': 'critical',
                    'source': 'KNOWALLEDGE-backend',
                    'custom_details': details or {}
                }
            }
            
            response = requests.post(
                'https://events.pagerduty.com/v2/enqueue',
                json=payload,
                headers={
                    'Authorization': f'Token token={self.pagerduty_api_key}',
                    'Content-Type': 'application/json'
                },
                timeout=10
            )
            response.raise_for_status()
            
            logger.info("PagerDuty alert sent")
            
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}", exc_info=True)
    
    def _format_details(self, details: Optional[Dict[str, Any]]) -> str:
        """Format details dictionary for email"""
        if not details:
            return "No additional details"
        
        lines = []
        for key, value in details.items():
            lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
    
    def _format_slack_fields(self, details: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format details dictionary for Slack fields"""
        if not details:
            return []
        
        fields = []
        for key, value in details.items():
            fields.append({
                'title': key.replace('_', ' ').title(),
                'value': str(value),
                'short': True
            })
        return fields
    
    def check_error_rate(self, error_rate: float, total_requests: int):
        """
        Check error rate and send alert if threshold exceeded
        
        Args:
            error_rate: Current error rate percentage
            total_requests: Total number of requests
        
        Requirements: 8.3
        """
        if error_rate > self.error_rate_threshold:
            self.send_alert(
                alert_type='error_rate',
                severity='critical' if error_rate > self.error_rate_threshold * 2 else 'warning',
                title='High Error Rate Detected',
                message=f'Error rate is {error_rate:.2f}%, exceeding threshold of {self.error_rate_threshold}%',
                details={
                    'error_rate': f'{error_rate:.2f}%',
                    'threshold': f'{self.error_rate_threshold}%',
                    'total_requests': total_requests
                }
            )
    
    def check_latency(self, avg_latency_ms: float, p95_latency_ms: float, p99_latency_ms: float):
        """
        Check latency and send alert if threshold exceeded
        
        Args:
            avg_latency_ms: Average latency in milliseconds
            p95_latency_ms: 95th percentile latency
            p99_latency_ms: 99th percentile latency
        
        Requirements: 8.4
        """
        if p99_latency_ms > self.latency_threshold_ms:
            self.send_alert(
                alert_type='latency',
                severity='critical' if p99_latency_ms > self.latency_threshold_ms * 2 else 'warning',
                title='High Latency Detected',
                message=f'P99 latency is {p99_latency_ms:.2f}ms, exceeding threshold of {self.latency_threshold_ms}ms',
                details={
                    'avg_latency_ms': f'{avg_latency_ms:.2f}',
                    'p95_latency_ms': f'{p95_latency_ms:.2f}',
                    'p99_latency_ms': f'{p99_latency_ms:.2f}',
                    'threshold_ms': self.latency_threshold_ms
                }
            )
    
    def check_system_resources(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """
        Check system resources and send alert if thresholds exceeded
        
        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            disk_percent: Disk usage percentage
        """
        if cpu_percent > self.cpu_threshold:
            self.send_alert(
                alert_type='cpu',
                severity='critical',
                title='High CPU Usage',
                message=f'CPU usage is {cpu_percent:.2f}%, exceeding threshold of {self.cpu_threshold}%',
                details={'cpu_percent': f'{cpu_percent:.2f}%', 'threshold': f'{self.cpu_threshold}%'}
            )
        
        if memory_percent > self.memory_threshold:
            self.send_alert(
                alert_type='memory',
                severity='critical',
                title='High Memory Usage',
                message=f'Memory usage is {memory_percent:.2f}%, exceeding threshold of {self.memory_threshold}%',
                details={'memory_percent': f'{memory_percent:.2f}%', 'threshold': f'{self.memory_threshold}%'}
            )
        
        if disk_percent > self.disk_threshold:
            self.send_alert(
                alert_type='disk',
                severity='critical',
                title='High Disk Usage',
                message=f'Disk usage is {disk_percent:.2f}%, exceeding threshold of {self.disk_threshold}%',
                details={'disk_percent': f'{disk_percent:.2f}%', 'threshold': f'{self.disk_threshold}%'}
            )
    
    def check_quota_exceeded(self, user_id: str, quota_type: str, usage: int, limit: int):
        """
        Send alert when quota is exceeded
        
        Args:
            user_id: User ID
            quota_type: Type of quota (rpm, rpd, tpm, tpd)
            usage: Current usage
            limit: Quota limit
        """
        self.send_alert(
            alert_type='quota',
            severity='warning',
            title='Quota Exceeded',
            message=f'User {user_id} exceeded {quota_type} quota',
            details={
                'user_id': user_id,
                'quota_type': quota_type,
                'usage': usage,
                'limit': limit,
                'percentage': f'{(usage / limit * 100):.2f}%'
            }
        )
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        with self.lock:
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)
            
            # Count alerts in last hour
            alerts_last_hour = sum(
                len([ts for ts in timestamps if ts > one_hour_ago])
                for timestamps in self.alert_counts.values()
            )
            
            return {
                'alerts_last_hour': alerts_last_hour,
                'unique_alert_types': len(self.alert_counts),
                'email_enabled': self.email_enabled,
                'slack_enabled': self.slack_enabled,
                'pagerduty_enabled': self.pagerduty_enabled,
                'thresholds': {
                    'error_rate': self.error_rate_threshold,
                    'latency_ms': self.latency_threshold_ms,
                    'cpu': self.cpu_threshold,
                    'memory': self.memory_threshold,
                    'disk': self.disk_threshold
                }
            }


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager(**kwargs) -> AlertManager:
    """Get or create global alert manager instance"""
    global _alert_manager
    
    if _alert_manager is None:
        _alert_manager = AlertManager(**kwargs)
    
    return _alert_manager
