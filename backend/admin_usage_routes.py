"""
Admin Usage Dashboard API Routes
Provides endpoints for viewing usage statistics and costs
Validates: Requirements 9.7
"""

from flask import Blueprint, jsonify, request, g
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Dict, List

from quota_management import QuotaUsage, QuotaTracker, get_quota_tracker
from structured_logging import get_logger

logger = get_logger(__name__)

# Create blueprint
admin_usage_bp = Blueprint('admin_usage', __name__, url_prefix='/api/admin/usage')


def require_admin():
    """Decorator to require admin role"""
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Check if user is admin
            if not hasattr(g, 'current_user') or not g.current_user:
                return jsonify({'error': 'Authentication required'}), 401
            
            if g.current_user.get('role') != 'admin':
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


@admin_usage_bp.route('', methods=['GET'])
@require_admin()
def get_usage_overview():
    """
    Get usage overview for all users
    
    Query parameters:
    - period: 'daily' or 'monthly' (default: 'daily')
    - limit: Number of users to return (default: 100)
    - sort_by: 'tokens', 'cost', 'requests' (default: 'tokens')
    
    **Validates: Requirements 9.7**
    """
    try:
        # Get query parameters
        period = request.args.get('period', 'daily')
        limit = int(request.args.get('limit', 100))
        sort_by = request.args.get('sort_by', 'tokens')
        
        # Validate parameters
        if period not in ['daily', 'monthly']:
            return jsonify({'error': 'Invalid period. Must be "daily" or "monthly"'}), 400
        
        if sort_by not in ['tokens', 'cost', 'requests']:
            return jsonify({'error': 'Invalid sort_by. Must be "tokens", "cost", or "requests"'}), 400
        
        # Get database session from app context
        from flask import current_app
        db_session = current_app.config.get('db_session')
        
        if not db_session:
            return jsonify({'error': 'Database session not configured'}), 500
        
        # Calculate period bounds
        now = datetime.utcnow()
        if period == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Query usage records
        query = db_session.query(QuotaUsage).filter(
            QuotaUsage.period_type == period,
            QuotaUsage.period_start == period_start
        )
        
        # Sort by requested field
        if sort_by == 'tokens':
            query = query.order_by(desc(QuotaUsage.total_tokens))
        elif sort_by == 'cost':
            query = query.order_by(desc(QuotaUsage.total_cost))
        elif sort_by == 'requests':
            query = query.order_by(desc(QuotaUsage.total_requests))
        
        # Limit results
        usage_records = query.limit(limit).all()
        
        # Calculate totals
        total_query = db_session.query(
            func.sum(QuotaUsage.total_requests).label('total_requests'),
            func.sum(QuotaUsage.total_tokens).label('total_tokens'),
            func.sum(QuotaUsage.total_cost).label('total_cost'),
            func.count(QuotaUsage.id).label('total_users')
        ).filter(
            QuotaUsage.period_type == period,
            QuotaUsage.period_start == period_start
        ).first()
        
        return jsonify({
            'period': period,
            'period_start': period_start.isoformat(),
            'totals': {
                'users': total_query.total_users or 0,
                'requests': total_query.total_requests or 0,
                'tokens': total_query.total_tokens or 0,
                'cost': float(total_query.total_cost or 0)
            },
            'top_users': [record.to_dict() for record in usage_records],
            'sort_by': sort_by,
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting usage overview: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_usage_bp.route('/user/<user_id>', methods=['GET'])
@require_admin()
def get_user_usage(user_id: str):
    """
    Get detailed usage for a specific user
    
    **Validates: Requirements 9.7**
    """
    try:
        # Get database session
        from flask import current_app
        db_session = current_app.config.get('db_session')
        
        if not db_session:
            return jsonify({'error': 'Database session not configured'}), 500
        
        tracker = get_quota_tracker(db_session)
        
        # Get daily and monthly usage
        daily_usage = tracker.get_usage(user_id, 'daily')
        monthly_usage = tracker.get_usage(user_id, 'monthly')
        
        # Get quota warnings
        warnings = tracker.check_quota_warnings(user_id)
        
        return jsonify({
            'user_id': user_id,
            'daily': daily_usage,
            'monthly': monthly_usage,
            'warnings': warnings.get('warnings', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user usage: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_usage_bp.route('/endpoint-breakdown', methods=['GET'])
@require_admin()
def get_endpoint_breakdown():
    """
    Get usage breakdown by endpoint
    
    Query parameters:
    - period: 'daily' or 'monthly' (default: 'daily')
    
    **Validates: Requirements 9.7**
    """
    try:
        period = request.args.get('period', 'daily')
        
        if period not in ['daily', 'monthly']:
            return jsonify({'error': 'Invalid period'}), 400
        
        # Get database session
        from flask import current_app
        db_session = current_app.config.get('db_session')
        
        if not db_session:
            return jsonify({'error': 'Database session not configured'}), 500
        
        # Calculate period bounds
        now = datetime.utcnow()
        if period == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get all usage records for the period
        usage_records = db_session.query(QuotaUsage).filter(
            QuotaUsage.period_type == period,
            QuotaUsage.period_start == period_start
        ).all()
        
        # Aggregate endpoint data
        import json
        endpoint_totals = {}
        
        for record in usage_records:
            if record.endpoint_usage:
                endpoint_data = json.loads(record.endpoint_usage)
                for endpoint, stats in endpoint_data.items():
                    if endpoint not in endpoint_totals:
                        endpoint_totals[endpoint] = {
                            'requests': 0,
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'total_tokens': 0,
                            'cost': 0.0
                        }
                    
                    endpoint_totals[endpoint]['requests'] += stats.get('requests', 0)
                    endpoint_totals[endpoint]['input_tokens'] += stats.get('input_tokens', 0)
                    endpoint_totals[endpoint]['output_tokens'] += stats.get('output_tokens', 0)
                    endpoint_totals[endpoint]['total_tokens'] += stats.get('total_tokens', 0)
                    endpoint_totals[endpoint]['cost'] += stats.get('cost', 0.0)
        
        # Sort by total tokens
        sorted_endpoints = sorted(
            endpoint_totals.items(),
            key=lambda x: x[1]['total_tokens'],
            reverse=True
        )
        
        return jsonify({
            'period': period,
            'period_start': period_start.isoformat(),
            'endpoints': [
                {'endpoint': endpoint, **stats}
                for endpoint, stats in sorted_endpoints
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting endpoint breakdown: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_usage_bp.route('/export', methods=['GET'])
@require_admin()
def export_usage_data():
    """
    Export usage data as CSV
    
    Query parameters:
    - period: 'daily' or 'monthly' (default: 'daily')
    - format: 'csv' or 'json' (default: 'csv')
    
    **Validates: Requirements 9.7**
    """
    try:
        period = request.args.get('period', 'daily')
        format_type = request.args.get('format', 'csv')
        
        if period not in ['daily', 'monthly']:
            return jsonify({'error': 'Invalid period'}), 400
        
        if format_type not in ['csv', 'json']:
            return jsonify({'error': 'Invalid format'}), 400
        
        # Get database session
        from flask import current_app
        db_session = current_app.config.get('db_session')
        
        if not db_session:
            return jsonify({'error': 'Database session not configured'}), 500
        
        # Calculate period bounds
        now = datetime.utcnow()
        if period == 'daily':
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get usage records
        usage_records = db_session.query(QuotaUsage).filter(
            QuotaUsage.period_type == period,
            QuotaUsage.period_start == period_start
        ).all()
        
        if format_type == 'json':
            return jsonify({
                'period': period,
                'period_start': period_start.isoformat(),
                'records': [record.to_dict() for record in usage_records]
            }), 200
        
        else:  # CSV
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'user_id', 'period_type', 'period_start', 'total_requests',
                'total_input_tokens', 'total_output_tokens', 'total_tokens', 'total_cost'
            ])
            
            # Write data
            for record in usage_records:
                writer.writerow([
                    record.user_id,
                    record.period_type,
                    record.period_start.isoformat(),
                    record.total_requests,
                    record.total_input_tokens,
                    record.total_output_tokens,
                    record.total_tokens,
                    float(record.total_cost)
                ])
            
            output.seek(0)
            
            from flask import Response
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=usage_{period}_{now.strftime("%Y%m%d")}.csv'
                }
            )
        
    except Exception as e:
        logger.error(f"Error exporting usage data: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@admin_usage_bp.route('/trends', methods=['GET'])
@require_admin()
def get_usage_trends():
    """
    Get usage trends over time
    
    Query parameters:
    - days: Number of days to include (default: 7, max: 90)
    
    **Validates: Requirements 9.7**
    """
    try:
        days = int(request.args.get('days', 7))
        
        if days < 1 or days > 90:
            return jsonify({'error': 'Days must be between 1 and 90'}), 400
        
        # Get database session
        from flask import current_app
        db_session = current_app.config.get('db_session')
        
        if not db_session:
            return jsonify({'error': 'Database session not configured'}), 500
        
        # Calculate date range
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        
        # Query daily usage for date range
        usage_by_day = db_session.query(
            QuotaUsage.period_start,
            func.sum(QuotaUsage.total_requests).label('requests'),
            func.sum(QuotaUsage.total_tokens).label('tokens'),
            func.sum(QuotaUsage.total_cost).label('cost'),
            func.count(QuotaUsage.id).label('users')
        ).filter(
            QuotaUsage.period_type == 'daily',
            QuotaUsage.period_start >= start_date,
            QuotaUsage.period_start <= end_date
        ).group_by(QuotaUsage.period_start).order_by(QuotaUsage.period_start).all()
        
        return jsonify({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days,
            'trends': [
                {
                    'date': day.period_start.isoformat(),
                    'requests': day.requests or 0,
                    'tokens': day.tokens or 0,
                    'cost': float(day.cost or 0),
                    'users': day.users or 0
                }
                for day in usage_by_day
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting usage trends: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
