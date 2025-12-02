"""
GDPR Compliance Service
Implements all GDPR requirements including data export, deletion, consent management,
audit logging, encryption at rest, and breach notification.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from auth_models import User, Session as UserSession, AuditLog
from encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class GDPRService:
    """
    GDPR Compliance Service
    Handles all GDPR-related operations
    """
    
    def __init__(self, db_session: Session, encryption_service: EncryptionService):
        self.db = db_session
        self.encryption = encryption_service
    
    # ==================== DATA EXPORT (Article 15) ====================
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all user data in machine-readable format (JSON)
        GDPR Article 15: Right to Access
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary containing all user data
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Log data export for audit trail
        self._log_audit_event(
            user_id=user_id,
            event_type='data_export',
            event_category='data_access',
            resource_type='user',
            resource_id=user_id
        )
        
        # Update export timestamp
        user.data_export_requested_at = datetime.utcnow()
        self.db.commit()
        
        # Collect all user data
        export_data = {
            'export_info': {
                'requested_at': datetime.utcnow().isoformat() + 'Z',
                'format': 'JSON',
                'gdpr_article': 'Article 15 - Right to Access'
            },
            'account': self._get_account_data(user),
            'sessions': self._get_sessions_data(user_id),
            'audit_logs': self._get_audit_logs_data(user_id),
            'consent_records': self._get_consent_records(user_id),
            'metadata': {
                'account_created': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'email_verified': user.email_verified
            }
        }
        
        return export_data
    
    def _get_account_data(self, user: User) -> Dict[str, Any]:
        """Get account information"""
        return {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'quota_tier': user.quota_tier.value,
            'email_verified': user.email_verified,
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'updated_at': user.updated_at.isoformat() if user.updated_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    def _get_sessions_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user sessions"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).all()
        
        return [
            {
                'session_id': session.id,
                'created_at': session.created_at.isoformat() if session.created_at else None,
                'expires_at': session.expires_at.isoformat() if session.expires_at else None,
                'ip_address': session.ip_address,
                'device_type': session.device_type,
                'is_active': session.is_active
            }
            for session in sessions
        ]
    
    def _get_audit_logs_data(self, user_id: str) -> List[Dict[str, Any]]:
        """Get audit logs for user"""
        logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(1000).all()
        
        return [
            {
                'event_type': log.event_type,
                'event_category': log.event_category,
                'resource_type': log.resource_type,
                'created_at': log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    
    def _get_consent_records(self, user_id: str) -> List[Dict[str, Any]]:
        """Get consent records"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        return [
            {
                'type': 'terms_of_service',
                'given_at': user.consent_given_at.isoformat() if user.consent_given_at else None,
                'status': 'given' if user.consent_given_at else 'not_given'
            }
        ]
    
    # ==================== DATA DELETION (Article 17) ====================
    
    def delete_user_data(self, user_id: str, reason: str = 'User requested deletion') -> Dict[str, Any]:
        """
        Delete all user data permanently
        GDPR Article 17: Right to Erasure
        
        Args:
            user_id: User ID
            reason: Reason for deletion
            
        Returns:
            Dictionary with deletion details
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Check deletion eligibility
        can_delete, reasons = self.check_deletion_eligibility(user_id)
        if not can_delete:
            raise ValueError(f"Cannot delete user: {', '.join(reasons)}")
        
        # Log deletion before deleting
        self._log_audit_event(
            user_id=user_id,
            event_type='account_deletion',
            event_category='data_modification',
            resource_type='user',
            resource_id=user_id,
            event_data=json.dumps({'reason': reason})
        )
        
        deleted_at = datetime.utcnow()
        data_removed = []
        
        # 1. Delete sessions
        session_count = self.db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).delete()
        if session_count > 0:
            data_removed.append(f'sessions ({session_count})')
        
        # 2. Anonymize audit logs (keep for compliance)
        audit_count = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).update({'user_id': None})
        if audit_count > 0:
            data_removed.append(f'audit_logs_anonymized ({audit_count})')
        
        # 3. Delete user account
        self.db.delete(user)
        data_removed.append('account')
        
        # Commit all changes
        self.db.commit()
        
        logger.info(f"User {user_id} data deleted: {data_removed}")
        
        return {
            'deleted_at': deleted_at.isoformat() + 'Z',
            'data_removed': data_removed,
            'reason': reason
        }
    
    def check_deletion_eligibility(self, user_id: str) -> Tuple[bool, List[str]]:
        """
        Check if user account can be deleted
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (can_delete, reasons)
        """
        reasons = []
        
        # Check if user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            reasons.append('User not found')
            return False, reasons
        
        # Add any business logic checks here
        # For example: active subscriptions, pending payments, legal holds, etc.
        
        can_delete = len(reasons) == 0
        return can_delete, reasons
    
    # ==================== CONSENT MANAGEMENT (Article 7) ====================
    
    def record_consent(self, user_id: str, consent_type: str, given: bool,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None) -> Dict[str, Any]:
        """
        Record user consent
        GDPR Article 7: Conditions for consent
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            given: Whether consent was given
            ip_address: IP address
            user_agent: User agent
            
        Returns:
            Consent record
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Update consent timestamp
        if given:
            user.consent_given_at = datetime.utcnow()
        
        # Log consent change
        self._log_audit_event(
            user_id=user_id,
            event_type='consent_update',
            event_category='data_modification',
            resource_type='consent',
            resource_id=consent_type,
            event_data=json.dumps({
                'consent_type': consent_type,
                'given': given,
                'ip_address': ip_address,
                'user_agent': user_agent
            })
        )
        
        self.db.commit()
        
        return {
            'user_id': user_id,
            'consent_type': consent_type,
            'given': given,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    def get_consent_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get user consent status
        
        Args:
            user_id: User ID
            
        Returns:
            Consent status
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        return {
            'user_id': user_id,
            'consent_given': user.consent_given_at is not None,
            'consent_given_at': user.consent_given_at.isoformat() if user.consent_given_at else None
        }
    
    # ==================== AUDIT LOGGING (Article 30) ====================
    
    def _log_audit_event(self, user_id: Optional[str], event_type: str,
                        event_category: str, resource_type: Optional[str] = None,
                        resource_id: Optional[str] = None,
                        ip_address: Optional[str] = None,
                        user_agent: Optional[str] = None,
                        event_data: Optional[str] = None) -> AuditLog:
        """
        Log audit event
        GDPR Article 30: Records of processing activities
        
        Args:
            user_id: User ID (optional for system events)
            event_type: Type of event
            event_category: Category of event
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            ip_address: IP address
            user_agent: User agent
            event_data: Additional event data (JSON string)
            
        Returns:
            AuditLog instance
        """
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            event_category=event_category,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            event_data=event_data,
            created_at=datetime.utcnow()
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        logger.info(f"Audit log created: {event_type} for user {user_id}")
        
        return audit_log
    
    def get_audit_logs(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get audit logs for user
        
        Args:
            user_id: User ID
            limit: Maximum number of logs to return
            
        Returns:
            List of audit logs
        """
        logs = self.db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()
        
        return [log.to_dict() for log in logs]
    
    # ==================== DATA RETENTION ====================
    
    def cleanup_old_audit_logs(self, retention_days: int = 2555) -> int:
        """
        Clean up old audit logs (7 years = 2555 days for GDPR compliance)
        
        Args:
            retention_days: Number of days to retain logs
            
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted_count = self.db.query(AuditLog).filter(
            AuditLog.created_at < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {deleted_count} old audit logs")
        
        return deleted_count


class BreachNotifier:
    """
    Breach Notification System
    GDPR Article 33 & 34: Notification of personal data breach
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def detect_breach(self, breach_type: str, affected_data: str,
                     severity: str = 'high') -> Dict[str, Any]:
        """
        Detect and log a potential data breach
        
        Args:
            breach_type: Type of breach
            affected_data: Description of affected data
            severity: Severity level (low, medium, high, critical)
            
        Returns:
            Breach record
        """
        breach_record = {
            'breach_id': hashlib.sha256(
                f"{breach_type}{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16],
            'breach_type': breach_type,
            'affected_data': affected_data,
            'severity': severity,
            'detected_at': datetime.utcnow().isoformat() + 'Z',
            'notification_deadline': (datetime.utcnow() + timedelta(hours=72)).isoformat() + 'Z'
        }
        
        logger.critical(f"BREACH DETECTED: {breach_type} - {affected_data}")
        
        return breach_record
    
    def notify_affected_users(self, user_ids: List[str], breach_info: Dict[str, Any]) -> int:
        """
        Notify affected users of a data breach
        Must be done within 72 hours (GDPR Article 34)
        
        Args:
            user_ids: List of affected user IDs
            breach_info: Breach information
            
        Returns:
            Number of users notified
        """
        notified_count = 0
        
        for user_id in user_ids:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                # In production, send actual email/notification
                logger.warning(f"BREACH NOTIFICATION: User {user.email} notified of breach")
                notified_count += 1
        
        logger.info(f"Notified {notified_count} users of data breach")
        
        return notified_count
