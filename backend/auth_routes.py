"""
Authentication API Routes
Implements user registration, login, logout, token refresh, and user info endpoints
Task 1.13: Create authentication API endpoints
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from auth_models import User, Session as UserSession, UserRole, QuotaTier, create_database_engine, create_session_factory
from password_hasher import PasswordHasher
from auth import JWTHandler
from error_handler import ErrorResponse

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize services
_db_session_factory = None
_password_hasher = None
_jwt_handler = None


def init_auth_routes(app):
    """Initialize auth routes with app context"""
    global _db_session_factory, _password_hasher, _jwt_handler
    
    engine = create_database_engine()
    _db_session_factory = create_session_factory(engine)
    _password_hasher = PasswordHasher()
    _jwt_handler = JWTHandler()
    
    app.register_blueprint(auth_bp)


def get_db_session() -> Session:
    """Get database session"""
    if not hasattr(g, 'db_session'):
        g.db_session = _db_session_factory()
    return g.db_session


# ==================== REGISTRATION ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    POST /api/auth/register
    """
    try:
        data = request.get_json()
        
        # Validate input
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            error = ErrorResponse(
                error_code='VALIDATION_ERROR',
                message='Email and password are required',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 400
        
        db = get_db_session()
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            error = ErrorResponse(
                error_code='USER_EXISTS',
                message='User with this email already exists',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 409
        
        # Hash password
        password_hash = _password_hasher.hash(password)
        
        # Create user
        user = User(
            email=email,
            password_hash=password_hash,
            role=UserRole.USER,
            quota_tier=QuotaTier.FREE,
            email_verified=False
        )
        
        db.add(user)
        db.commit()
        
        logger.info(f"User registered: {email}")
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        error = ErrorResponse(
            error_code='REGISTRATION_ERROR',
            message='Failed to register user',
            details={'error': str(e)},
            timestamp=datetime.utcnow().isoformat()
        )
        return jsonify(error.to_dict()), 500


# ==================== LOGIN ====================

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    POST /api/auth/login
    """
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            error = ErrorResponse(
                error_code='VALIDATION_ERROR',
                message='Email and password are required',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 400
        
        db = get_db_session()
        
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            error = ErrorResponse(
                error_code='INVALID_CREDENTIALS',
                message='Invalid email or password',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        # Verify password
        if not _password_hasher.verify(password, user.password_hash):
            error = ErrorResponse(
                error_code='INVALID_CREDENTIALS',
                message='Invalid email or password',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        # Generate JWT token
        token = _jwt_handler.generate(
            user_id=user.id,
            role=user.role.value,
            quota_tier=user.quota_tier.value
        )
        
        # Create session
        session = UserSession(
            user_id=user.id,
            token_hash=_jwt_handler.hash_token(token),
            expires_at=datetime.utcnow() + timedelta(hours=24),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        db.add(session)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info(f"User logged in: {email}")
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict(),
            'expires_in': 86400  # 24 hours
        }), 200
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        error = ErrorResponse(
            error_code='LOGIN_ERROR',
            message='Failed to login',
            details={'error': str(e)},
            timestamp=datetime.utcnow().isoformat()
        )
        return jsonify(error.to_dict()), 500


# ==================== LOGOUT ====================

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    User logout endpoint
    POST /api/auth/logout
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            error = ErrorResponse(
                error_code='MISSING_TOKEN',
                message='Authorization token required',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        token = auth_header.split(' ')[1]
        token_hash = _jwt_handler.hash_token(token)
        
        db = get_db_session()
        
        # Find and revoke session
        session = db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoke_reason = 'User logout'
            db.commit()
        
        logger.info(f"User logged out")
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        error = ErrorResponse(
            error_code='LOGOUT_ERROR',
            message='Failed to logout',
            timestamp=datetime.utcnow().isoformat()
        )
        return jsonify(error.to_dict()), 500


# ==================== TOKEN REFRESH ====================

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Token refresh endpoint
    POST /api/auth/refresh
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            error = ErrorResponse(
                error_code='MISSING_TOKEN',
                message='Authorization token required',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        token = auth_header.split(' ')[1]
        
        # Validate token
        payload = _jwt_handler.validate(token)
        if not payload:
            error = ErrorResponse(
                error_code='INVALID_TOKEN',
                message='Invalid or expired token',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        user_id = payload.get('user_id')
        
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            error = ErrorResponse(
                error_code='USER_NOT_FOUND',
                message='User not found',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 404
        
        # Generate new token
        new_token = _jwt_handler.generate(
            user_id=user.id,
            role=user.role.value,
            quota_tier=user.quota_tier.value
        )
        
        logger.info(f"Token refreshed for user: {user.email}")
        
        return jsonify({
            'message': 'Token refreshed successfully',
            'token': new_token,
            'expires_in': 86400
        }), 200
        
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        error = ErrorResponse(
            error_code='REFRESH_ERROR',
            message='Failed to refresh token',
            timestamp=datetime.utcnow().isoformat()
        )
        return jsonify(error.to_dict()), 500


# ==================== GET CURRENT USER ====================

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Get current user info
    GET /api/auth/me
    """
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            error = ErrorResponse(
                error_code='MISSING_TOKEN',
                message='Authorization token required',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        token = auth_header.split(' ')[1]
        
        # Validate token
        payload = _jwt_handler.validate(token)
        if not payload:
            error = ErrorResponse(
                error_code='INVALID_TOKEN',
                message='Invalid or expired token',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 401
        
        user_id = payload.get('user_id')
        
        db = get_db_session()
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            error = ErrorResponse(
                error_code='USER_NOT_FOUND',
                message='User not found',
                timestamp=datetime.utcnow().isoformat()
            )
            return jsonify(error.to_dict()), 404
        
        return jsonify({
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        error = ErrorResponse(
            error_code='USER_INFO_ERROR',
            message='Failed to get user info',
            timestamp=datetime.utcnow().isoformat()
        )
        return jsonify(error.to_dict()), 500


__all__ = ['auth_bp', 'init_auth_routes']
