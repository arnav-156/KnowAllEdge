"""
Database initialization and connection management
CRITICAL FIX: Proper database connection with pooling and health checks
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool, NullPool
from contextlib import contextmanager
import os
import logging

from config import get_config
from structured_logging import get_logger

logger = get_logger(__name__)
config = get_config()

# Database URL from environment with fallback to SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./knowalledge.db')

# Determine if using SQLite (no pooling needed)
is_sqlite = DATABASE_URL.startswith('sqlite')

# Create engine with appropriate configuration
if is_sqlite:
    # SQLite doesn't support connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},  # Allow multi-threading
        echo=config.is_development(),
    )
    logger.info("Database engine created (SQLite - no pooling)")
else:
    # PostgreSQL/MySQL with connection pooling
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=10,  # Number of connections to keep open
        max_overflow=20,  # Max connections beyond pool_size
        pool_timeout=30,  # Timeout for getting connection
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Test connections before using
        echo=config.is_development(),
    )
    logger.info("Database engine created with connection pooling")

# Create session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

def init_database():
    """
    Initialize database tables
    Returns True if successful, False otherwise
    """
    try:
        # Import all models to ensure they're registered
        from auth_models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database tables created successfully", extra={
            'database_url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else 'sqlite'
        })
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        return False

def get_db():
    """
    Dependency for getting database session
    Use with FastAPI Depends or Flask teardown
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context():
    """
    Context manager for database sessions
    Automatically commits on success, rolls back on error
    
    Usage:
        with get_db_context() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def check_database_health():
    """
    Check if database is accessible
    Returns True if healthy, False otherwise
    """
    try:
        with get_db_context() as db:
            # Simple query to test connection
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

def get_database_stats():
    """
    Get database connection pool statistics
    Returns dict with pool info or None if not applicable
    """
    if is_sqlite:
        return {"type": "sqlite", "pooling": False}
    
    try:
        pool = engine.pool
        return {
            "type": "pooled",
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow()
        }
    except Exception as e:
        logger.warning(f"Could not get pool stats: {e}")
        return None

# Event listeners for connection management
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Called when a new DB connection is created"""
    logger.debug("New database connection established")

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Called when a connection is retrieved from the pool"""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Called when a connection is returned to the pool"""
    logger.debug("Connection returned to pool")

# Cleanup function
def close_database():
    """Close all database connections"""
    try:
        SessionLocal.remove()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

__all__ = [
    'engine',
    'SessionLocal',
    'init_database',
    'get_db',
    'get_db_context',
    'check_database_health',
    'get_database_stats',
    'close_database'
]
