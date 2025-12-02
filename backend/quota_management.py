"""
Production Quota Management System
Tracks daily and monthly token usage with cost calculation
Complies with Requirements 9.3, 9.6
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Numeric, Index, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session as DBSession
from flask import g

from structured_logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()


@dataclass
class CostConfig:
    """Cost configuration for API usage"""
    # Gemini 2.0 Flash pricing (per 1M tokens)
    input_token_cost: float = 0.075  # $0.075 per 1M input tokens
    output_token_cost: float = 0.30  # $0.30 per 1M output tokens
    
    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Cost in USD
        """
        input_cost = (input_tokens / 1_000_000) * self.input_token_cost
        output_cost = (output_tokens / 1_000_000) * self.output_token_cost
        return input_cost + output_cost


class QuotaUsage(Base):
    """
    Database model for quota usage tracking
    
    Validates: Requirements 9.3, 9.6
    """
    __tablename__ = 'quota_usage'
    
    # Primary key
    id = Column(String(36), primary_key=True)
    
    # User identification
    user_id = Column(String(36), nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    period_type = Column(String(10), nullable=False)  # 'daily' or 'monthly'
    
    # Usage metrics
    total_requests = Column(Integer, default=0, nullable=False)
    total_input_tokens = Column(BigInteger, default=0, nullable=False)
    total_output_tokens = Column(BigInteger, default=0, nullable=False)
    total_tokens = Column(BigInteger, default=0, nullable=False)
    
    # Cost tracking (Requirement 9.6)
    total_cost = Column(Numeric(10, 4), default=0, nullable=False)
    
    # Per-endpoint breakdown (stored as JSON string)
    endpoint_usage = Column(String, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_quota_user_period', 'user_id', 'period_type', 'period_start'),
        Index('idx_quota_period_start', 'period_start'),
    )
    
    def __repr__(self):
        return f"<QuotaUsage(user_id={self.user_id}, period={self.period_type}, tokens={self.total_tokens})>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'period_type': self.period_type,
            'total_requests': self.total_requests,
            'total_input_tokens': self.total_input_tokens,
            'total_output_tokens': self.total_output_tokens,
            'total_tokens': self.total_tokens,
            'total_cost': float(self.total_cost) if self.total_cost else 0.0,
            'endpoint_usage': self.endpoint_usage
        }


@dataclass
class QuotaLimits:
    """Quota limits for different tiers"""
    tier: str
    daily_tokens: int
    monthly_tokens: int
    
    def __repr__(self):
        return f"<QuotaLimits {self.tier}: {self.daily_tokens} daily, {self.monthly_tokens} monthly>"


# Tier-based quota limits (Requirements 9.4, 9.5)
QUOTA_LIMITS = {
    'limited': QuotaLimits('limited', 10_000, 100_000),           # Anonymous/guest
    'free': QuotaLimits('free', 50_000, 500_000),                 # Free registered
    'basic': QuotaLimits('basic', 200_000, 2_000_000),            # Basic paid
    'premium': QuotaLimits('premium', 1_000_000, 10_000_000),     # Premium paid
    'unlimited': QuotaLimits('unlimited', 100_000_000, 1_000_000_000)  # Admin
}


class QuotaTracker:
    """
    Production quota tracker with database persistence
    
    Features:
    - Track daily and monthly token usage
    - Calculate costs per request
    - Store usage in database
    - Per-endpoint breakdown
    - Quota warnings at 75% and 90%
    - Quota enforcement
    
    Validates: Requirements 9.3, 9.4, 9.5, 9.6
    """
    
    def __init__(self, db_session: DBSession, cost_config: Optional[CostConfig] = None):
        """
        Initialize quota tracker
        
        Args:
            db_session: SQLAlchemy database session
            cost_config: Cost configuration (optional)
        """
        self.db_session = db_session
        self.cost_config = cost_config or CostConfig()
        
        logger.info("Quota tracker initialized")
    
    def _get_user_id(self) -> Optional[str]:
        """
        Get user ID from request context
        
        Returns:
            User ID or None if not authenticated
        """
        # Check Flask g object for authenticated user
        if hasattr(g, 'current_user') and g.current_user:
            return g.current_user.get('user_id')
        
        return None
    
    def _get_period_bounds(self, period_type: str) -> Tuple[datetime, datetime]:
        """
        Get start and end datetime for period
        
        Args:
            period_type: 'daily' or 'monthly'
        
        Returns:
            Tuple of (period_start, period_end)
        """
        now = datetime.utcnow()
        
        if period_type == 'daily':
            # Start of current day
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # End of current day
            period_end = period_start + timedelta(days=1)
        elif period_type == 'monthly':
            # Start of current month
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Start of next month
            if now.month == 12:
                period_end = period_start.replace(year=now.year + 1, month=1)
            else:
                period_end = period_start.replace(month=now.month + 1)
        else:
            raise ValueError(f"Invalid period_type: {period_type}")
        
        return period_start, period_end
    
    def _get_or_create_usage_record(
        self,
        user_id: str,
        period_type: str
    ) -> QuotaUsage:
        """
        Get or create usage record for user and period
        
        Args:
            user_id: User ID
            period_type: 'daily' or 'monthly'
        
        Returns:
            QuotaUsage record
        """
        period_start, period_end = self._get_period_bounds(period_type)
        
        # Try to find existing record
        usage = self.db_session.query(QuotaUsage).filter(
            QuotaUsage.user_id == user_id,
            QuotaUsage.period_type == period_type,
            QuotaUsage.period_start == period_start
        ).first()
        
        if not usage:
            # Create new record
            import uuid
            usage = QuotaUsage(
                id=str(uuid.uuid4()),
                user_id=user_id,
                period_start=period_start,
                period_end=period_end,
                period_type=period_type,
                total_requests=0,
                total_input_tokens=0,
                total_output_tokens=0,
                total_tokens=0,
                total_cost=0,
                endpoint_usage='{}'
            )
            self.db_session.add(usage)
            self.db_session.flush()
        
        return usage
    
    def track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        endpoint: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Track API usage and calculate cost
        
        Args:
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            endpoint: API endpoint name
            user_id: User ID (optional, will try to get from context)
        
        Returns:
            Dictionary with usage and cost information
            
        Validates: Requirements 9.3, 9.6
        """
        # Get user ID
        if user_id is None:
            user_id = self._get_user_id()
        
        if user_id is None:
            logger.warning("Cannot track usage: no user ID available")
            return {
                'tracked': False,
                'reason': 'no_user_id'
            }
        
        # Calculate cost (Requirement 9.6)
        cost = self.cost_config.calculate_cost(input_tokens, output_tokens)
        total_tokens = input_tokens + output_tokens
        
        try:
            # Update daily usage
            daily_usage = self._get_or_create_usage_record(user_id, 'daily')
            daily_usage.total_requests += 1
            daily_usage.total_input_tokens += input_tokens
            daily_usage.total_output_tokens += output_tokens
            daily_usage.total_tokens += total_tokens
            daily_usage.total_cost = float(daily_usage.total_cost) + cost
            
            # Update monthly usage
            monthly_usage = self._get_or_create_usage_record(user_id, 'monthly')
            monthly_usage.total_requests += 1
            monthly_usage.total_input_tokens += input_tokens
            monthly_usage.total_output_tokens += output_tokens
            monthly_usage.total_tokens += total_tokens
            monthly_usage.total_cost = float(monthly_usage.total_cost) + cost
            
            # Update per-endpoint breakdown
            import json
            for usage_record in [daily_usage, monthly_usage]:
                endpoint_data = json.loads(usage_record.endpoint_usage or '{}')
                if endpoint not in endpoint_data:
                    endpoint_data[endpoint] = {
                        'requests': 0,
                        'input_tokens': 0,
                        'output_tokens': 0,
                        'total_tokens': 0,
                        'cost': 0.0
                    }
                
                endpoint_data[endpoint]['requests'] += 1
                endpoint_data[endpoint]['input_tokens'] += input_tokens
                endpoint_data[endpoint]['output_tokens'] += output_tokens
                endpoint_data[endpoint]['total_tokens'] += total_tokens
                endpoint_data[endpoint]['cost'] += cost
                
                usage_record.endpoint_usage = json.dumps(endpoint_data)
            
            # Commit changes
            self.db_session.commit()
            
            logger.info(
                "Usage tracked",
                extra={
                    'user_id': user_id,
                    'endpoint': endpoint,
                    'tokens': total_tokens,
                    'cost': f"${cost:.4f}"
                }
            )
            
            return {
                'tracked': True,
                'user_id': user_id,
                'endpoint': endpoint,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost': cost,
                'daily_total': daily_usage.total_tokens,
                'monthly_total': monthly_usage.total_tokens,
                'daily_cost': float(daily_usage.total_cost),
                'monthly_cost': float(monthly_usage.total_cost)
            }
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}", exc_info=True)
            self.db_session.rollback()
            return {
                'tracked': False,
                'reason': 'database_error',
                'error': str(e)
            }
    
    def get_usage(
        self,
        user_id: Optional[str] = None,
        period_type: str = 'daily'
    ) -> Optional[Dict]:
        """
        Get current usage for user
        
        Args:
            user_id: User ID (optional, will try to get from context)
            period_type: 'daily' or 'monthly'
        
        Returns:
            Usage dictionary or None if not found
        """
        # Get user ID
        if user_id is None:
            user_id = self._get_user_id()
        
        if user_id is None:
            return None
        
        try:
            period_start, period_end = self._get_period_bounds(period_type)
            
            usage = self.db_session.query(QuotaUsage).filter(
                QuotaUsage.user_id == user_id,
                QuotaUsage.period_type == period_type,
                QuotaUsage.period_start == period_start
            ).first()
            
            if usage:
                return usage.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting usage: {e}", exc_info=True)
            return None
    
    def get_all_usage(self, user_id: Optional[str] = None) -> Dict:
        """
        Get both daily and monthly usage for user
        
        Args:
            user_id: User ID (optional, will try to get from context)
        
        Returns:
            Dictionary with daily and monthly usage
        """
        return {
            'daily': self.get_usage(user_id, 'daily'),
            'monthly': self.get_usage(user_id, 'monthly')
        }
    
    def _get_user_tier(self) -> str:
        """
        Get user's quota tier from request context
        
        Returns:
            Tier name
        """
        from flask import g
        if hasattr(g, 'current_user') and g.current_user:
            return g.current_user.get('quota_tier', 'free')
        return 'limited'
    
    def check_quota_warnings(
        self,
        user_id: Optional[str] = None,
        tier: Optional[str] = None
    ) -> Dict:
        """
        Check if user should receive quota warnings
        
        Sends warnings at 75% and 90% usage
        
        Args:
            user_id: User ID (optional, will try to get from context)
            tier: User tier (optional, will try to get from context)
        
        Returns:
            Dictionary with warning information
            
        Validates: Requirements 9.4
        """
        if user_id is None:
            user_id = self._get_user_id()
        
        if user_id is None:
            return {'warnings': []}
        
        if tier is None:
            tier = self._get_user_tier()
        
        limits = QUOTA_LIMITS.get(tier, QUOTA_LIMITS['limited'])
        
        # Get current usage
        daily_usage = self.get_usage(user_id, 'daily')
        monthly_usage = self.get_usage(user_id, 'monthly')
        
        warnings = []
        
        # Check daily quota
        if daily_usage:
            daily_tokens = daily_usage['total_tokens']
            daily_percentage = (daily_tokens / limits.daily_tokens) * 100
            
            if daily_percentage >= 90:
                warnings.append({
                    'level': 'critical',
                    'period': 'daily',
                    'usage': daily_tokens,
                    'limit': limits.daily_tokens,
                    'percentage': round(daily_percentage, 2),
                    'message': f'Daily quota at {daily_percentage:.1f}% ({daily_tokens}/{limits.daily_tokens} tokens)'
                })
            elif daily_percentage >= 75:
                warnings.append({
                    'level': 'warning',
                    'period': 'daily',
                    'usage': daily_tokens,
                    'limit': limits.daily_tokens,
                    'percentage': round(daily_percentage, 2),
                    'message': f'Daily quota at {daily_percentage:.1f}% ({daily_tokens}/{limits.daily_tokens} tokens)'
                })
        
        # Check monthly quota
        if monthly_usage:
            monthly_tokens = monthly_usage['total_tokens']
            monthly_percentage = (monthly_tokens / limits.monthly_tokens) * 100
            
            if monthly_percentage >= 90:
                warnings.append({
                    'level': 'critical',
                    'period': 'monthly',
                    'usage': monthly_tokens,
                    'limit': limits.monthly_tokens,
                    'percentage': round(monthly_percentage, 2),
                    'message': f'Monthly quota at {monthly_percentage:.1f}% ({monthly_tokens}/{limits.monthly_tokens} tokens)'
                })
            elif monthly_percentage >= 75:
                warnings.append({
                    'level': 'warning',
                    'period': 'monthly',
                    'usage': monthly_tokens,
                    'limit': limits.monthly_tokens,
                    'percentage': round(monthly_percentage, 2),
                    'message': f'Monthly quota at {monthly_percentage:.1f}% ({monthly_tokens}/{limits.monthly_tokens} tokens)'
                })
        
        if warnings:
            logger.warning(
                "Quota warnings triggered",
                extra={
                    'user_id': user_id,
                    'tier': tier,
                    'warnings': warnings
                }
            )
        
        return {
            'user_id': user_id,
            'tier': tier,
            'warnings': warnings
        }
    
    def check_quota_enforcement(
        self,
        estimated_tokens: int,
        user_id: Optional[str] = None,
        tier: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if request should be allowed based on quota limits
        
        Args:
            estimated_tokens: Estimated tokens for the request
            user_id: User ID (optional, will try to get from context)
            tier: User tier (optional, will try to get from context)
        
        Returns:
            Tuple of (is_allowed, error_response_dict)
            
        Validates: Requirements 9.5
        """
        if user_id is None:
            user_id = self._get_user_id()
        
        if user_id is None:
            # Allow anonymous requests (they'll be rate limited separately)
            return True, None
        
        if tier is None:
            tier = self._get_user_tier()
        
        limits = QUOTA_LIMITS.get(tier, QUOTA_LIMITS['limited'])
        
        # Get current usage
        daily_usage = self.get_usage(user_id, 'daily')
        monthly_usage = self.get_usage(user_id, 'monthly')
        
        daily_tokens = daily_usage['total_tokens'] if daily_usage else 0
        monthly_tokens = monthly_usage['total_tokens'] if monthly_usage else 0
        
        # Check if adding estimated tokens would exceed limits
        if daily_tokens + estimated_tokens > limits.daily_tokens:
            # Calculate reset time (start of next day)
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            reset_seconds = int((tomorrow - now).total_seconds())
            
            logger.warning(
                "Daily quota exceeded",
                extra={
                    'user_id': user_id,
                    'tier': tier,
                    'current': daily_tokens,
                    'limit': limits.daily_tokens
                }
            )
            
            return False, {
                'error': 'quota_exceeded',
                'message': f'Daily quota exceeded: {daily_tokens}/{limits.daily_tokens} tokens used',
                'period': 'daily',
                'tier': tier,
                'usage': daily_tokens,
                'limit': limits.daily_tokens,
                'reset_in_seconds': reset_seconds
            }
        
        if monthly_tokens + estimated_tokens > limits.monthly_tokens:
            # Calculate reset time (start of next month)
            from datetime import datetime
            now = datetime.utcnow()
            if now.month == 12:
                next_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                next_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            reset_seconds = int((next_month - now).total_seconds())
            
            logger.warning(
                "Monthly quota exceeded",
                extra={
                    'user_id': user_id,
                    'tier': tier,
                    'current': monthly_tokens,
                    'limit': limits.monthly_tokens
                }
            )
            
            return False, {
                'error': 'quota_exceeded',
                'message': f'Monthly quota exceeded: {monthly_tokens}/{limits.monthly_tokens} tokens used',
                'period': 'monthly',
                'tier': tier,
                'usage': monthly_tokens,
                'limit': limits.monthly_tokens,
                'reset_in_seconds': reset_seconds
            }
        
        return True, None


# Global quota tracker instance
_quota_tracker_instance: Optional[QuotaTracker] = None


def get_quota_tracker(db_session: DBSession) -> QuotaTracker:
    """
    Get or create global quota tracker instance
    
    Args:
        db_session: SQLAlchemy database session
    
    Returns:
        QuotaTracker instance
    """
    global _quota_tracker_instance
    if _quota_tracker_instance is None:
        _quota_tracker_instance = QuotaTracker(db_session)
    return _quota_tracker_instance


def init_quota_database(database_url: str = 'sqlite:///quota.db'):
    """
    Initialize quota database tables
    
    Args:
        database_url: Database connection string
    """
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    logger.info(f"Quota database initialized: {database_url}")
    return engine


if __name__ == '__main__':
    # Initialize database when run directly
    print("Initializing quota database...")
    init_quota_database()
    print("✅ Quota database initialized!")
