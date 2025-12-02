"""
Database Connection Pool Optimizer
Optimizes database connection pooling for performance
"""

import time
import threading
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event, pool
from sqlalchemy.pool import QueuePool, NullPool
import logging

logger = logging.getLogger(__name__)


class ConnectionPoolOptimizer:
    """
    Optimizes database connection pooling based on load
    """
    
    def __init__(self, database_url: str, initial_pool_size: int = 5,
                 max_overflow: int = 10, pool_timeout: int = 30):
        """
        Initialize connection pool optimizer
        
        Args:
            database_url: Database connection URL
            initial_pool_size: Initial pool size
            max_overflow: Maximum overflow connections
            pool_timeout: Connection timeout in seconds
        """
        self.database_url = database_url
        self.initial_pool_size = initial_pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        
        # Metrics
        self.metrics = {
            'connections_created': 0,
            'connections_closed': 0,
            'connections_recycled': 0,
            'checkout_count': 0,
            'checkin_count': 0,
            'overflow_count': 0,
            'pool_size': initial_pool_size,
            'active_connections': 0,
            'idle_connections': 0
        }
        
        self.engine = None
        self._lock = threading.Lock()
    
    def create_optimized_engine(self, **kwargs):
        """
        Create optimized database engine
        
        Returns:
            SQLAlchemy engine
        """
        # Default pool configuration
        pool_config = {
            'poolclass': QueuePool,
            'pool_size': self.initial_pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': 3600,  # Recycle connections after 1 hour
            'pool_pre_ping': True,  # Verify connections before using
            'echo_pool': False
        }
        
        # Merge with custom kwargs
        pool_config.update(kwargs)
        
        # Create engine
        self.engine = create_engine(self.database_url, **pool_config)
        
        # Register event listeners
        self._register_event_listeners()
        
        logger.info(f"Created optimized connection pool: size={self.initial_pool_size}, overflow={self.max_overflow}")
        
        return self.engine
    
    def _register_event_listeners(self):
        """Register event listeners for pool monitoring"""
        
        @event.listens_for(self.engine, 'connect')
        def receive_connect(dbapi_conn, connection_record):
            """Track connection creation"""
            with self._lock:
                self.metrics['connections_created'] += 1
                self.metrics['active_connections'] += 1
        
        @event.listens_for(self.engine, 'close')
        def receive_close(dbapi_conn, connection_record):
            """Track connection closure"""
            with self._lock:
                self.metrics['connections_closed'] += 1
                self.metrics['active_connections'] -= 1
        
        @event.listens_for(self.engine, 'checkout')
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkout"""
            with self._lock:
                self.metrics['checkout_count'] += 1
        
        @event.listens_for(self.engine, 'checkin')
        def receive_checkin(dbapi_conn, connection_record):
            """Track connection checkin"""
            with self._lock:
                self.metrics['checkin_count'] += 1
    
    def get_pool_status(self) -> Dict[str, any]:
        """
        Get current pool status
        
        Returns:
            Pool status dictionary
        """
        if not self.engine:
            return {'error': 'Engine not initialized'}
        
        pool = self.engine.pool
        
        status = {
            'pool_size': pool.size(),
            'checked_out': pool.checkedout(),
            'overflow': pool.overflow(),
            'checked_in': pool.checkedin() if hasattr(pool, 'checkedin') else 0,
            'metrics': self.metrics.copy(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Calculate utilization
        total_capacity = self.initial_pool_size + self.max_overflow
        utilization = (status['checked_out'] / total_capacity) * 100 if total_capacity > 0 else 0
        status['utilization_percent'] = round(utilization, 2)
        
        return status
    
    def optimize_pool_size(self, target_utilization: float = 0.7) -> Dict[str, any]:
        """
        Optimize pool size based on usage patterns
        
        Args:
            target_utilization: Target utilization (0-1)
            
        Returns:
            Optimization result
        """
        status = self.get_pool_status()
        
        if 'error' in status:
            return status
        
        current_utilization = status['utilization_percent'] / 100
        
        # Calculate recommended pool size
        if current_utilization > target_utilization:
            # Increase pool size
            recommended_size = int(self.initial_pool_size * 1.5)
            action = 'increase'
        elif current_utilization < target_utilization * 0.5:
            # Decrease pool size
            recommended_size = max(2, int(self.initial_pool_size * 0.75))
            action = 'decrease'
        else:
            # Keep current size
            recommended_size = self.initial_pool_size
            action = 'maintain'
        
        return {
            'current_pool_size': self.initial_pool_size,
            'recommended_pool_size': recommended_size,
            'current_utilization': current_utilization,
            'target_utilization': target_utilization,
            'action': action,
            'status': status
        }
    
    def monitor_pool_health(self) -> Dict[str, any]:
        """
        Monitor pool health and detect issues
        
        Returns:
            Health report
        """
        status = self.get_pool_status()
        
        if 'error' in status:
            return {'healthy': False, 'error': status['error']}
        
        issues = []
        warnings = []
        
        # Check for high utilization
        if status['utilization_percent'] > 90:
            issues.append('Pool utilization above 90%')
        elif status['utilization_percent'] > 75:
            warnings.append('Pool utilization above 75%')
        
        # Check for overflow usage
        if status['overflow'] > 0:
            warnings.append(f'Using {status["overflow"]} overflow connections')
        
        # Check for connection leaks
        checkout_count = self.metrics['checkout_count']
        checkin_count = self.metrics['checkin_count']
        if checkout_count > checkin_count + 10:
            issues.append(f'Possible connection leak: {checkout_count - checkin_count} connections not returned')
        
        # Determine health status
        if issues:
            health_status = 'unhealthy'
        elif warnings:
            health_status = 'warning'
        else:
            health_status = 'healthy'
        
        return {
            'healthy': health_status == 'healthy',
            'status': health_status,
            'issues': issues,
            'warnings': warnings,
            'pool_status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_connection_stats(self) -> Dict[str, any]:
        """
        Get detailed connection statistics
        
        Returns:
            Connection statistics
        """
        metrics = self.metrics.copy()
        
        # Calculate rates
        total_checkouts = metrics['checkout_count']
        total_checkins = metrics['checkin_count']
        
        stats = {
            'total_connections_created': metrics['connections_created'],
            'total_connections_closed': metrics['connections_closed'],
            'total_checkouts': total_checkouts,
            'total_checkins': total_checkins,
            'active_connections': metrics['active_connections'],
            'connection_reuse_rate': (total_checkins / total_checkouts * 100) if total_checkouts > 0 else 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return stats
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.metrics = {
                'connections_created': 0,
                'connections_closed': 0,
                'connections_recycled': 0,
                'checkout_count': 0,
                'checkin_count': 0,
                'overflow_count': 0,
                'pool_size': self.initial_pool_size,
                'active_connections': 0,
                'idle_connections': 0
            }
        
        logger.info("Connection pool metrics reset")
    
    def dispose_pool(self):
        """Dispose of the connection pool"""
        if self.engine:
            self.engine.dispose()
            logger.info("Connection pool disposed")


class ConnectionPoolMonitor:
    """
    Monitors connection pool over time
    """
    
    def __init__(self, optimizer: ConnectionPoolOptimizer, interval: int = 60):
        """
        Initialize monitor
        
        Args:
            optimizer: ConnectionPoolOptimizer instance
            interval: Monitoring interval in seconds
        """
        self.optimizer = optimizer
        self.interval = interval
        self.running = False
        self.thread = None
        self.history = []
        self.max_history = 1000
    
    def start(self):
        """Start monitoring"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info(f"Connection pool monitoring started (interval={self.interval}s)")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Connection pool monitoring stopped")
    
    def _monitor_loop(self):
        """Monitoring loop"""
        while self.running:
            try:
                # Get pool status
                status = self.optimizer.get_pool_status()
                
                # Add to history
                self.history.append({
                    'timestamp': datetime.utcnow(),
                    'status': status
                })
                
                # Trim history
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]
                
                # Check health
                health = self.optimizer.monitor_pool_health()
                if not health['healthy']:
                    logger.warning(f"Pool health issues: {health['issues']}")
                
            except Exception as e:
                logger.error(f"Error in pool monitoring: {e}")
            
            # Sleep
            time.sleep(self.interval)
    
    def get_history(self, minutes: int = 60) -> List[Dict[str, any]]:
        """
        Get monitoring history
        
        Args:
            minutes: Number of minutes of history to return
            
        Returns:
            List of historical status records
        """
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            record for record in self.history
            if record['timestamp'] > cutoff
        ]
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get summary statistics
        
        Returns:
            Summary statistics
        """
        if not self.history:
            return {'error': 'No history available'}
        
        recent = self.get_history(minutes=60)
        
        if not recent:
            return {'error': 'No recent history'}
        
        # Calculate averages
        avg_utilization = sum(r['status']['utilization_percent'] for r in recent) / len(recent)
        avg_checked_out = sum(r['status']['checked_out'] for r in recent) / len(recent)
        max_checked_out = max(r['status']['checked_out'] for r in recent)
        
        return {
            'period_minutes': 60,
            'samples': len(recent),
            'avg_utilization_percent': round(avg_utilization, 2),
            'avg_checked_out': round(avg_checked_out, 2),
            'max_checked_out': max_checked_out,
            'current_status': recent[-1]['status'] if recent else None
        }
