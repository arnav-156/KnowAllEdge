"""
Authentication Database Manager

Handles database connections, sessions, and CRUD operations for auth models
"""

import os
from contextlib import contextmanager
from typing import Optional, List
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from auth_models import (
    User, Session as SessionModel, AuditLog,
    UserRole, QuotaTier,
    create_database_engine, create_session_factory, init_database
)
from structured_logging import get_logger

logger = get_logger(__name__)


class AuthDatabase:
    """
    Authentication database manager
    
    Provides high-level interface for auth operations
    """
    
    def __init__(self, database_url=None):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection string (uses env var if not provided)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///auth.db')
        self.engine = create_database_engine(self.database_url)
        self.SessionFactory = create_session_factory(self.engine)
        
        # Initialize database tables
        init_database(self.engine)
        
        logger.info(f"Auth database initialized: {self.database_url}")
    
    @contextmanager
    def get_session(self):
        """
        Get database session with automatic cleanup
        
        Usage:
            with auth_db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    # User operations
    
    def create_user(self, email: str, password_hash: str, role: UserRole = UserRole.USER,
                   quota_tier: QuotaTier = QuotaTier.FREE, **kwargs) -> Optional[dict]:
        """
        Create a new user
        
        Args:
            email: User email
            password_hash: Hashed password
            role: User role
            quota_tier: Quota tier
            **kwargs: Additional user fields
        
        Returns:
            Created user dict or None if failed
        """
        try:
            with self.get_session() as session:
                user = User(
                    email=email,
                    password_hash=password_hash,
                    role=role,
                    quota_tier=quota_tier,
                    **kwargs
                )
                session.add(user)
                session.flush()  # Get the ID
                
                # Convert to dict before session closes
                user_dict = user.to_dict()
                user_dict['password_hash'] = user.password_hash  # Include for internal use
                
                logger.info(f"User created: {user.id} ({email})")
                return user_dict
        except IntegrityError as e:
            logger.warning(f"User creation failed (duplicate email?): {email}")
            return None
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Get user by email"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.email == email).first()
                if user:
                    user_dict = user.to_dict()
                    user_dict['password_hash'] = user.password_hash  # Include for auth
                    return user_dict
                return None
        except Exception as e:
            logger.error(f"Failed to get user by email: {e}")
            return None
    
    def get_user_by_api_key_hash(self, api_key_hash: str) -> Optional[dict]:
        """Get user by API key hash"""
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.api_key_hash == api_key_hash).first()
                return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"Failed to get user by API key: {e}")
            return None
    
    def update_user(self, user_id: str, **kwargs) -> bool:
        """
        Update user fields
        
        Args:
            user_id: User ID
            **kwargs: Fields to update
        
        Returns:
            True if successful
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                
                user.updated_at = datetime.utcnow()
                logger.info(f"User updated: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user (cascades to sessions and audit logs)
        
        Args:
            user_id: User ID
        
        Returns:
            True if successful
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                session.delete(user)
                logger.info(f"User deleted: {user_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False
    
    def record_login_attempt(self, user_id: str, success: bool) -> bool:
        """
        Record login attempt and handle account locking
        
        Args:
            user_id: User ID
            success: Whether login was successful
        
        Returns:
            True if successful
        """
        try:
            with self.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False
                
                if success:
                    user.failed_login_attempts = 0
                    user.last_login = datetime.utcnow()
                    user.account_locked_until = None
                else:
                    user.failed_login_attempts += 1
                    
                    # Lock account after 5 failed attempts
                    if user.failed_login_attempts >= 5:
                        user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
                        logger.warning(f"Account locked due to failed attempts: {user_id}")
                
                return True
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            return False
    
    # Session operations
    
    def create_session(self, user_id: str, token_hash: str, expires_at: datetime,
                      ip_address: str = None, user_agent: str = None, **kwargs) -> Optional[dict]:
        """
        Create a new session
        
        Args:
            user_id: User ID
            token_hash: Hashed JWT token
            expires_at: Session expiration time
            ip_address: Client IP address
            user_agent: Client user agent
            **kwargs: Additional session fields
        
        Returns:
            Created session dict or None if failed
        """
        try:
            with self.get_session() as session:
                session_model = SessionModel(
                    user_id=user_id,
                    token_hash=token_hash,
                    expires_at=expires_at,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    **kwargs
                )
                session.add(session_model)
                session.flush()
                
                session_dict = session_model.to_dict()
                logger.info(f"Session created: {session_model.id} for user {user_id}")
                return session_dict
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None
    
    def get_session_by_token_hash(self, token_hash: str) -> Optional[dict]:
        """Get session by token hash"""
        try:
            with self.get_session() as session:
                session_model = session.query(SessionModel).filter(
                    SessionModel.token_hash == token_hash
                ).first()
                return session_model.to_dict() if session_model else None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def get_user_sessions(self, user_id: str, active_only: bool = True) -> List[dict]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            active_only: Only return active sessions
        
        Returns:
            List of session dicts
        """
        try:
            with self.get_session() as session:
                query = session.query(SessionModel).filter(SessionModel.user_id == user_id)
                
                if active_only:
                    query = query.filter(
                        SessionModel.is_active == True,
                        SessionModel.expires_at > datetime.utcnow()
                    )
                
                return [s.to_dict() for s in query.all()]
        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []
    
    def revoke_session(self, session_id: str, reason: str = None) -> bool:
        """
        Revoke a session
        
        Args:
            session_id: Session ID
            reason: Revocation reason
        
        Returns:
            True if successful
        """
        try:
            with self.get_session() as session:
                session_model = session.query(SessionModel).filter(
                    SessionModel.id == session_id
                ).first()
                
                if not session_model:
                    return False
                
                session_model.is_active = False
                session_model.revoked_at = datetime.utcnow()
                session_model.revoke_reason = reason
                
                logger.info(f"Session revoked: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to revoke session: {e}")
            return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions deleted
        """
        try:
            with self.get_session() as session:
                count = session.query(SessionModel).filter(
                    SessionModel.expires_at < datetime.utcnow()
                ).delete()
                
                logger.info(f"Cleaned up {count} expired sessions")
                return count
        except Exception as e:
            logger.error(f"Failed to cleanup sessions: {e}")
            return 0
    
    # Audit log operations
    
    def create_audit_log(self, event_type: str, event_category: str,
                        user_id: str = None, resource_type: str = None,
                        resource_id: str = None, ip_address: str = None,
                        user_agent: str = None, request_id: str = None,
                        event_data: str = None) -> Optional[dict]:
        """
        Create an audit log entry
        
        Args:
            event_type: Type of event (login, logout, data_access, etc.)
            event_category: Category (auth, data_access, data_modification, admin)
            user_id: User ID (optional for system events)
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            ip_address: Client IP
            user_agent: Client user agent
            request_id: Request ID for tracing
            event_data: Additional event data (JSON string)
        
        Returns:
            Created audit log dict or None if failed
        """
        try:
            with self.get_session() as session:
                audit_log = AuditLog(
                    event_type=event_type,
                    event_category=event_category,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    request_id=request_id,
                    event_data=event_data
                )
                session.add(audit_log)
                session.flush()
                
                return audit_log.to_dict()
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None
    
    def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[dict]:
        """
        Get audit logs for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of logs to return
        
        Returns:
            List of audit log dicts
        """
        try:
            with self.get_session() as session:
                logs = session.query(AuditLog).filter(
                    AuditLog.user_id == user_id
                ).order_by(AuditLog.created_at.desc()).limit(limit).all()
                return [log.to_dict() for log in logs]
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []


# Global database instance
auth_db = AuthDatabase()


if __name__ == '__main__':
    # Test database operations
    print("Testing auth database...")
    
    # Create test user
    user = auth_db.create_user(
        email='test@example.com',
        password_hash='$2b$12$test_hash',
        role=UserRole.USER,
        quota_tier=QuotaTier.FREE
    )
    
    if user:
        print(f"✅ Created user: {user}")
        
        # Create test session
        session = auth_db.create_session(
            user_id=user['id'],
            token_hash='test_token_hash',
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address='127.0.0.1'
        )
        
        if session:
            print(f"✅ Created session: {session}")
        
        # Create audit log
        audit = auth_db.create_audit_log(
            event_type='login',
            event_category='auth',
            user_id=user['id'],
            ip_address='127.0.0.1'
        )
        
        if audit:
            print(f"✅ Created audit log: {audit}")
        
        # Test retrieval
        retrieved_user = auth_db.get_user_by_email('test@example.com')
        print(f"✅ Retrieved user: {retrieved_user['email']}")
        
        # Test session retrieval
        sessions = auth_db.get_user_sessions(user['id'])
        print(f"✅ Found {len(sessions)} active session(s)")
        
        # Test audit log retrieval
        logs = auth_db.get_user_audit_logs(user['id'])
        print(f"✅ Found {len(logs)} audit log(s)")
    
    print("\n✅ Database test complete! All operations working correctly.")
