"""
Authentication Database Models
SQLAlchemy models for User and Session management
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, DateTime, Integer, Boolean, ForeignKey,
    Enum as SQLEnum, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum

Base = declarative_base()


class UserRole(enum.Enum):
    """User role enumeration"""
    USER = 'user'
    ADMIN = 'admin'


class QuotaTier(enum.Enum):
    """Quota tier enumeration"""
    LIMITED = 'limited'  # Anonymous/guest
    FREE = 'free'        # Free registered
    BASIC = 'basic'      # Basic paid
    PREMIUM = 'premium'  # Premium paid
    UNLIMITED = 'unlimited'  # Admin


class User(Base):
    """
    User model for authentication and authorization
    
    Stores user credentials, roles, and metadata
    """
    __tablename__ = 'users'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Authorization fields
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    quota_tier = Column(SQLEnum(QuotaTier), default=QuotaTier.FREE, nullable=False)
    
    # API key (hashed)
    api_key_hash = Column(String(64), unique=True, nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    account_locked_until = Column(DateTime, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String(64), nullable=True)
    password_reset_token = Column(String(64), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # GDPR compliance fields
    consent_given_at = Column(DateTime, nullable=True)
    data_export_requested_at = Column(DateTime, nullable=True)
    deletion_requested_at = Column(DateTime, nullable=True)
    
    # Relationships
    sessions = relationship('Session', back_populates='user', cascade='all, delete-orphan')
    audit_logs = relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_api_key_hash', 'api_key_hash'),
        Index('idx_user_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive fields)"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.value,
            'quota_tier': self.quota_tier.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'email_verified': self.email_verified
        }


class Session(Base):
    """
    Session model for JWT token management
    
    Tracks active user sessions with metadata
    """
    __tablename__ = 'sessions'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to user
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Token (hashed for security)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(255), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_token_hash', 'token_hash'),
        Index('idx_session_expires_at', 'expires_at'),
        Index('idx_session_is_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'device_type': self.device_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active
        }
    
    def is_expired(self):
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired()


class AuditLog(Base):
    """
    Audit log model for GDPR compliance
    
    Tracks all access to personal data
    """
    __tablename__ = 'audit_logs'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Foreign key to user (nullable for system events)
    user_id = Column(String(36), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # login, logout, data_access, etc.
    event_category = Column(
        SQLEnum('auth', 'data_access', 'data_modification', 'admin', name='event_category_enum'),
        nullable=False
    )
    resource_type = Column(String(50), nullable=True)  # user, session, data, etc.
    resource_id = Column(String(255), nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(36), nullable=True, index=True)
    
    # Event data (JSON stored as string)
    event_data = Column(String, nullable=True)  # JSON string
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_created_at', 'created_at'),
        Index('idx_audit_request_id', 'request_id'),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type={self.event_type}, user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Database initialization functions
def get_database_url():
    """Get database URL from environment or use default SQLite"""
    import os
    return os.getenv('DATABASE_URL', 'sqlite:///auth.db')


def create_database_engine(database_url=None, echo=False):
    """
    Create SQLAlchemy engine
    
    Args:
        database_url: Database connection string
        echo: Whether to echo SQL statements (for debugging)
    
    Returns:
        SQLAlchemy engine
    """
    if database_url is None:
        database_url = get_database_url()
    
    # Create engine with appropriate settings
    engine = create_engine(
        database_url,
        echo=echo,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
    )
    
    return engine


def create_session_factory(engine):
    """
    Create SQLAlchemy session factory
    
    Args:
        engine: SQLAlchemy engine
    
    Returns:
        Session factory
    """
    return sessionmaker(bind=engine)


def init_database(engine=None):
    """
    Initialize database tables
    
    Args:
        engine: SQLAlchemy engine (creates new one if not provided)
    """
    if engine is None:
        engine = create_database_engine()
    
    # Create all tables
    Base.metadata.create_all(engine)
    print("✅ Database tables created successfully")


def drop_database(engine=None):
    """
    Drop all database tables (use with caution!)
    
    Args:
        engine: SQLAlchemy engine (creates new one if not provided)
    """
    if engine is None:
        engine = create_database_engine()
    
    # Drop all tables
    Base.metadata.drop_all(engine)
    print("⚠️ Database tables dropped")


if __name__ == '__main__':
    # Initialize database when run directly
    print("Initializing authentication database...")
    init_database()
    print("Database initialization complete!")
