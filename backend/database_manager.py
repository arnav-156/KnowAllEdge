"""
Database Manager Module

Provides secure database connections with:
- TLS/SSL encryption
- Connection pooling
- Health checks
- Automatic reconnection
"""

import os
from contextlib import contextmanager
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError, DisconnectionError
from structured_logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages database connections with security and performance features
    
    Features:
    - TLS/SSL encryption for production
    - Connection pooling with configurable limits
    - Automatic connection health checks
    - Graceful reconnection on failures
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        enable_tls: bool = None,
        echo: bool = False
    ):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection string (uses env var if not provided)
            pool_size: Number of connections to maintain in pool
            max_overflow: Maximum overflow connections beyond pool_size
            pool_timeout: Seconds to wait for connection from pool
            pool_recycle: Seconds before recycling connections
            enable_tls: Force TLS (auto-detects from env if None)
            echo: Echo SQL statements for debugging
        """
        # Get database URL from environment or parameter
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///app.db')
        
        # Determine if TLS should be enabled
        if enable_tls is None:
            # Auto-detect: enable TLS in production for PostgreSQL/MySQL
            env = os.getenv('FLASK_ENV', 'development')
            is_production = env == 'production'
            is_remote_db = 'postgresql' in self.database_url or 'mysql' in self.database_url
            self.enable_tls = is_production and is_remote_db
        else:
            self.enable_tls = enable_tls
        
        # Configure connection arguments
        connect_args = self._get_connect_args()
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=pool.QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
            echo=echo,
            connect_args=connect_args
        )
        
        # Create session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
        
        # Register event listeners
        self._register_event_listeners()
        
        logger.info(
            f"Database manager initialized",
            extra={
                'database_type': self._get_database_type(),
                'pool_size': pool_size,
                'max_overflow': max_overflow,
                'tls_enabled': self.enable_tls
            }
        )
    
    def _get_database_type(self) -> str:
        """Get database type from URL"""
        if 'postgresql' in self.database_url:
            return 'postgresql'
        elif 'mysql' in self.database_url:
            return 'mysql'
        elif 'sqlite' in self.database_url:
            return 'sqlite'
        else:
            return 'unknown'
    
    def _get_connect_args(self) -> Dict[str, Any]:
        """
        Get database-specific connection arguments
        
        Returns:
            Dictionary of connection arguments
        """
        connect_args = {}
        
        # PostgreSQL TLS configuration
        if 'postgresql' in self.database_url and self.enable_tls:
            connect_args['sslmode'] = os.getenv('DB_SSL_MODE', 'require')
            
            # Optional: SSL certificate paths
            ssl_cert = os.getenv('DB_SSL_CERT')
            ssl_key = os.getenv('DB_SSL_KEY')
            ssl_root_cert = os.getenv('DB_SSL_ROOT_CERT')
            
            if ssl_cert:
                connect_args['sslcert'] = ssl_cert
            if ssl_key:
                connect_args['sslkey'] = ssl_key
            if ssl_root_cert:
                connect_args['sslrootcert'] = ssl_root_cert
            
            logger.info(f"PostgreSQL TLS enabled with sslmode={connect_args['sslmode']}")
        
        # MySQL TLS configuration
        elif 'mysql' in self.database_url and self.enable_tls:
            connect_args['ssl'] = {
                'ssl_mode': os.getenv('DB_SSL_MODE', 'REQUIRED')
            }
            
            # Optional: SSL certificate paths
            ssl_ca = os.getenv('DB_SSL_CA')
            ssl_cert = os.getenv('DB_SSL_CERT')
            ssl_key = os.getenv('DB_SSL_KEY')
            
            if ssl_ca:
                connect_args['ssl']['ca'] = ssl_ca
            if ssl_cert:
                connect_args['ssl']['cert'] = ssl_cert
            if ssl_key:
                connect_args['ssl']['key'] = ssl_key
            
            logger.info("MySQL TLS enabled")
        
        # SQLite configuration
        elif 'sqlite' in self.database_url:
            connect_args['check_same_thread'] = False
            connect_args['timeout'] = 30
        
        return connect_args
    
    def _register_event_listeners(self):
        """Register SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log new database connections"""
            logger.debug("New database connection established")
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Log connection checkout from pool"""
            logger.debug("Connection checked out from pool")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection return to pool"""
            logger.debug("Connection returned to pool")
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session with automatic cleanup
        
        Usage:
            with db_manager.get_session() as session:
                # Use session
                session.query(...)
        
        Yields:
            SQLAlchemy session
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check database health
        
        Returns:
            Dictionary with health status
        """
        try:
            # Try to execute a simple query
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            # Get pool statistics
            pool_stats = self._get_pool_stats()
            
            return {
                'status': 'healthy',
                'database_type': self._get_database_type(),
                'tls_enabled': self.enable_tls,
                'pool': pool_stats
            }
            
        except (OperationalError, DisconnectionError) as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_type': self._get_database_type()
            }
        except Exception as e:
            logger.error(f"Database health check error: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_pool_stats(self) -> Dict[str, int]:
        """
        Get connection pool statistics (internal)
        
        Returns:
            Dictionary with pool statistics
        """
        try:
            pool = self.engine.pool
            return {
                'size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'total': pool.size() + pool.overflow()
            }
        except Exception as e:
            logger.warning(f"Failed to get pool stats: {e}")
            return {}
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics for monitoring
        
        Returns:
            Dictionary with pool statistics including:
            - pool_size: Total pool size
            - connections_in_use: Number of checked out connections
            - pool_overflow: Number of overflow connections
            - connections_available: Number of available connections
        
        Requirements: 8.2
        """
        stats = self._get_pool_stats()
        return {
            'pool_size': stats.get('size', 0),
            'connections_in_use': stats.get('checked_out', 0),
            'pool_overflow': stats.get('overflow', 0),
            'connections_available': stats.get('checked_in', 0),
            'total_connections': stats.get('total', 0)
        }
    
    def dispose(self):
        """Dispose of all connections in the pool"""
        self.engine.dispose()
        logger.info("Database connections disposed")
    
    def execute_raw(self, query: str, params: Optional[Dict] = None) -> Any:
        """
        Execute raw SQL query (use with caution!)
        
        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)
        
        Returns:
            Query result
        """
        with self.engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            conn.commit()
            return result


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(
    database_url: Optional[str] = None,
    **kwargs
) -> DatabaseManager:
    """
    Get or create global database manager instance
    
    Args:
        database_url: Database connection string
        **kwargs: Additional arguments for DatabaseManager
    
    Returns:
        DatabaseManager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url=database_url, **kwargs)
    
    return _db_manager


def dispose_database_manager():
    """Dispose of global database manager"""
    global _db_manager
    
    if _db_manager is not None:
        _db_manager.dispose()
        _db_manager = None
