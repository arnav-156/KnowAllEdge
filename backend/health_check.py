"""
Comprehensive Health Check System
Implements detailed health checks for all system dependencies

Requirements: 8.1
"""

import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
import psutil

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    Comprehensive health check service that monitors all system dependencies
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.version = os.getenv('APP_VERSION', '1.0.0')
        self.instance_id = os.getenv('INSTANCE_ID', 'backend-1')
        self.environment = os.getenv('ENVIRONMENT', 'development')
    
    def check_database(self) -> Tuple[bool, Dict[str, Any]]:
        """Check database connectivity and health"""
        try:
            from database_manager import database_manager
            db_health = database_manager.health_check()
            
            return db_health['healthy'], {
                'status': 'healthy' if db_health['healthy'] else 'unhealthy',
                'message': db_health.get('message', 'Database connected'),
                'pool_size': db_health.get('pool_size'),
                'connections_in_use': db_health.get('connections_in_use'),
                'pool_overflow': db_health.get('pool_overflow', 0),
                'response_time_ms': db_health.get('response_time_ms', 0)
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return False, {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}',
                'error': type(e).__name__
            }
    
    def check_redis(self) -> Tuple[bool, Dict[str, Any]]:
        """Check Redis cache connectivity"""
        try:
            from redis_cache import get_redis_cache
            cache = get_redis_cache()
            
            if not cache or not cache.enabled:
                return True, {
                    'status': 'not_configured',
                    'message': 'Redis not configured (optional)'
                }
            
            # Ping Redis
            start = time.time()
            cache.redis_client.ping()
            response_time = (time.time() - start) * 1000
            
            # Get Redis info
            info = cache.redis_client.info()
            
            return True, {
                'status': 'healthy',
                'message': 'Redis connected',
                'response_time_ms': round(response_time, 2),
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', 'unknown'),
                'uptime_seconds': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Redis health check failed: {e}", exc_info=True)
            return False, {
                'status': 'unhealthy',
                'message': f'Redis error: {str(e)}',
                'error': type(e).__name__
            }
    
    def check_gemini_api(self) -> Tuple[bool, Dict[str, Any]]:
        """Check Gemini API connectivity"""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                return False, {
                    'status': 'unhealthy',
                    'message': 'API key not configured'
                }
            
            # Check circuit breaker state
            from circuit_breaker import get_google_ai_breaker
            breaker = get_google_ai_breaker()
            
            if breaker:
                breaker_state = breaker.get_state()
                if breaker_state['state'] == 'open':
                    return False, {
                        'status': 'unhealthy',
                        'message': 'Circuit breaker open',
                        'circuit_breaker': breaker_state
                    }
            
            # Simple connectivity test (minimal token usage)
            genai.configure(api_key=api_key)
            start = time.time()
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            test_response = model.generate_content(
                "Hi",
                generation_config=genai.GenerationConfig(max_output_tokens=5)
            )
            response_time = (time.time() - start) * 1000
            
            return True, {
                'status': 'healthy',
                'message': 'Gemini API accessible',
                'model': 'gemini-2.0-flash-exp',
                'response_time_ms': round(response_time, 2),
                'circuit_breaker': breaker_state if breaker else None
            }
        except Exception as e:
            logger.error(f"Gemini API health check failed: {e}", exc_info=True)
            return False, {
                'status': 'unhealthy',
                'message': f'Gemini API error: {str(e)}',
                'error': type(e).__name__
            }
    
    def check_quota_status(self) -> Tuple[bool, Dict[str, Any]]:
        """Check quota usage and limits"""
        try:
            from quota_tracker import get_quota_tracker
            tracker = get_quota_tracker()
            stats = tracker.get_stats()
            
            # Check if quota is critically high
            rpm_pct = stats['requests']['per_minute']['percentage']
            rpd_pct = stats['requests']['per_day']['percentage']
            tpm_pct = stats['tokens']['per_minute']['percentage']
            tpd_pct = stats['tokens']['per_day']['percentage']
            
            is_critical = rpm_pct > 90 or rpd_pct > 90 or tpm_pct > 90 or tpd_pct > 90
            is_warning = rpm_pct > 75 or rpd_pct > 75 or tpm_pct > 75 or tpd_pct > 75
            
            status = 'critical' if is_critical else ('warning' if is_warning else 'healthy')
            
            return not is_critical, {
                'status': status,
                'message': f'Quota {status}',
                'requests_per_minute_pct': rpm_pct,
                'requests_per_day_pct': rpd_pct,
                'tokens_per_minute_pct': tpm_pct,
                'tokens_per_day_pct': tpd_pct,
                'limits': stats.get('limits', {})
            }
        except Exception as e:
            logger.warning(f"Quota check failed: {e}")
            return True, {
                'status': 'unknown',
                'message': f'Quota check skipped: {str(e)}'
            }
    
    def check_circuit_breakers(self) -> Tuple[bool, Dict[str, Any]]:
        """Check circuit breaker states"""
        try:
            from circuit_breaker import get_google_ai_breaker
            breaker = get_google_ai_breaker()
            
            if not breaker:
                return True, {
                    'status': 'not_configured',
                    'message': 'Circuit breakers not configured'
                }
            
            breaker_state = breaker.get_state()
            is_healthy = breaker_state['state'] != 'open'
            
            return is_healthy, {
                'status': 'healthy' if is_healthy else 'unhealthy',
                'google_ai': breaker_state
            }
        except Exception as e:
            logger.warning(f"Circuit breaker check failed: {e}")
            return True, {
                'status': 'unknown',
                'message': f'Circuit breaker check skipped: {str(e)}'
            }
    
    def check_system_resources(self) -> Tuple[bool, Dict[str, Any]]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine if resources are critical
            is_critical = (
                cpu_percent > 90 or
                memory.percent > 90 or
                disk.percent > 90
            )
            
            is_warning = (
                cpu_percent > 75 or
                memory.percent > 75 or
                disk.percent > 75
            )
            
            status = 'critical' if is_critical else ('warning' if is_warning else 'healthy')
            
            return not is_critical, {
                'status': status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory.percent, 2),
                'memory_available_mb': round(memory.available / 1024 / 1024, 2),
                'disk_percent': round(disk.percent, 2),
                'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
            }
        except Exception as e:
            logger.warning(f"System resource check failed: {e}")
            return True, {
                'status': 'unknown',
                'message': f'Resource check skipped: {str(e)}'
            }
    
    def get_version_info(self) -> Dict[str, Any]:
        """Get application version information"""
        import sys
        import flask
        
        return {
            'app_version': self.version,
            'python_version': sys.version.split()[0],
            'flask_version': flask.__version__,
            'environment': self.environment,
            'instance_id': self.instance_id
        }
    
    def get_uptime_info(self) -> Dict[str, Any]:
        """Get application uptime information"""
        uptime_seconds = time.time() - self.start_time
        uptime_hours = uptime_seconds / 3600
        uptime_days = uptime_hours / 24
        
        return {
            'uptime_seconds': round(uptime_seconds, 2),
            'uptime_hours': round(uptime_hours, 2),
            'uptime_days': round(uptime_days, 2),
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'current_time': datetime.now().isoformat()
        }
    
    def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all dependencies
        
        Returns:
            Dictionary with health status and detailed checks
        """
        checks = {}
        all_healthy = True
        has_warnings = False
        
        # Check database
        db_healthy, db_info = self.check_database()
        checks['database'] = db_info
        if not db_healthy:
            all_healthy = False
        
        # Check Redis
        redis_healthy, redis_info = self.check_redis()
        checks['redis'] = redis_info
        if not redis_healthy:
            all_healthy = False
        
        # Check Gemini API
        api_healthy, api_info = self.check_gemini_api()
        checks['gemini_api'] = api_info
        if not api_healthy:
            all_healthy = False
        
        # Check quota status
        quota_healthy, quota_info = self.check_quota_status()
        checks['quota'] = quota_info
        if not quota_healthy:
            all_healthy = False
        if quota_info['status'] == 'warning':
            has_warnings = True
        
        # Check circuit breakers
        breaker_healthy, breaker_info = self.check_circuit_breakers()
        checks['circuit_breakers'] = breaker_info
        if not breaker_healthy:
            all_healthy = False
        
        # Check system resources
        resources_healthy, resources_info = self.check_system_resources()
        checks['system_resources'] = resources_info
        if not resources_healthy:
            all_healthy = False
        if resources_info['status'] == 'warning':
            has_warnings = True
        
        # Determine overall status
        if all_healthy and not has_warnings:
            overall_status = 'healthy'
        elif all_healthy and has_warnings:
            overall_status = 'healthy_with_warnings'
        else:
            overall_status = 'unhealthy'
        
        return {
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'version': self.get_version_info(),
            'uptime': self.get_uptime_info(),
            'checks': checks
        }
    
    def perform_liveness_check(self) -> Dict[str, Any]:
        """
        Simple liveness check - just confirms the app is running
        Used by Kubernetes liveness probe
        """
        return {
            'status': 'alive',
            'timestamp': datetime.now().isoformat(),
            'instance_id': self.instance_id,
            'uptime_seconds': round(time.time() - self.start_time, 2)
        }
    
    def perform_readiness_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Readiness check - confirms app can handle traffic
        Used by Kubernetes readiness probe
        
        Returns:
            Tuple of (is_ready, status_dict)
        """
        checks = {}
        is_ready = True
        
        # Check critical dependencies only
        db_healthy, db_info = self.check_database()
        checks['database'] = db_info
        if not db_healthy:
            is_ready = False
        
        api_healthy, api_info = self.check_gemini_api()
        checks['gemini_api'] = api_info
        if not api_healthy:
            is_ready = False
        
        # Check quota (don't fail readiness, just warn)
        quota_healthy, quota_info = self.check_quota_status()
        checks['quota'] = quota_info
        
        return is_ready, {
            'ready': is_ready,
            'timestamp': datetime.now().isoformat(),
            'instance_id': self.instance_id,
            'checks': checks
        }


# Global health check service instance
_health_check_service = None


def get_health_check_service() -> HealthCheckService:
    """Get or create the global health check service instance"""
    global _health_check_service
    if _health_check_service is None:
        _health_check_service = HealthCheckService()
    return _health_check_service
