"""
Pytest Configuration and Shared Fixtures
Requirements: 6.1, 6.4 - Configure pytest and create test fixtures
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import application modules
from config import get_config
from password_hasher import PasswordHasher
from auth_models import User, Session, APIKey


# ==================== Configuration Fixtures ====================

@pytest.fixture(scope='session')
def test_config():
    """Get test configuration"""
    os.environ['ENVIRONMENT'] = 'test'
    config = get_config()
    return config


@pytest.fixture(scope='session')
def app(test_config):
    """Create Flask app for testing"""
    from main import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create Flask application context"""
    with app.app_context():
        yield app


@pytest.fixture
def request_context(app):
    """Create Flask request context"""
    with app.test_request_context():
        yield


# ==================== Database Fixtures ====================

@pytest.fixture(scope='function')
def db_session():
    """Create database session for testing"""
    # This would connect to test database
    # For now, return a mock
    session = MagicMock()
    yield session
    # Cleanup
    session.rollback()
    session.close()


@pytest.fixture
def clean_database(db_session):
    """Clean database before each test"""
    # Clear all tables
    # This is a placeholder - implement based on your database setup
    yield
    # Cleanup after test


# ==================== Authentication Fixtures ====================

@pytest.fixture
def password_hasher():
    """Create PasswordHasher instance"""
    return PasswordHasher()


@pytest.fixture
def sample_user():
    """Create sample user for testing"""
    return User(
        id=1,
        email='test@example.com',
        password_hash='$2b$12$test_hash',
        role='user',
        quota_tier='free',
        created_at=datetime.utcnow()
    )


@pytest.fixture
def admin_user():
    """Create admin user for testing"""
    return User(
        id=2,
        email='admin@example.com',
        password_hash='$2b$12$admin_hash',
        role='admin',
        quota_tier='premium',
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_session(sample_user):
    """Create sample session for testing"""
    return Session(
        id=1,
        user_id=sample_user.id,
        token_hash='test_token_hash',
        expires_at=datetime.utcnow() + timedelta(hours=24),
        ip_address='127.0.0.1',
        user_agent='pytest',
        created_at=datetime.utcnow()
    )


@pytest.fixture
def sample_api_key(sample_user):
    """Create sample API key for testing"""
    return APIKey(
        id=1,
        user_id=sample_user.id,
        key_hash='test_key_hash',
        key_prefix='sk_test',
        name='Test API Key',
        created_at=datetime.utcnow(),
        last_used_at=None
    )


@pytest.fixture
def valid_jwt_token():
    """Create valid JWT token for testing"""
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token'


@pytest.fixture
def expired_jwt_token():
    """Create expired JWT token for testing"""
    return 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token'


# ==================== Request Fixtures ====================

@pytest.fixture
def mock_request():
    """Create mock Flask request"""
    request = Mock()
    request.method = 'GET'
    request.path = '/api/test'
    request.headers = {}
    request.json = {}
    request.args = {}
    request.form = {}
    return request


@pytest.fixture
def authenticated_request(mock_request, valid_jwt_token):
    """Create authenticated mock request"""
    mock_request.headers['Authorization'] = f'Bearer {valid_jwt_token}'
    return mock_request


# ==================== Validation Fixtures ====================

@pytest.fixture
def valid_topic():
    """Valid topic string for testing"""
    return 'Machine Learning Basics'


@pytest.fixture
def invalid_topic_too_long():
    """Invalid topic (too long) for testing"""
    return 'A' * 201


@pytest.fixture
def invalid_topic_special_chars():
    """Invalid topic (special characters) for testing"""
    return '<script>alert("xss")</script>'


@pytest.fixture
def valid_subtopics():
    """Valid subtopics array for testing"""
    return ['Neural Networks', 'Deep Learning', 'Supervised Learning']


@pytest.fixture
def invalid_subtopics_too_many():
    """Invalid subtopics (too many) for testing"""
    return [f'Topic {i}' for i in range(21)]


# ==================== File Upload Fixtures ====================

@pytest.fixture
def valid_image_file():
    """Create valid image file for testing"""
    from io import BytesIO
    file = BytesIO(b'fake image content')
    file.name = 'test.jpg'
    file.content_type = 'image/jpeg'
    return file


@pytest.fixture
def invalid_file_type():
    """Create invalid file type for testing"""
    from io import BytesIO
    file = BytesIO(b'fake executable content')
    file.name = 'malware.exe'
    file.content_type = 'application/x-msdownload'
    return file


@pytest.fixture
def oversized_file():
    """Create oversized file for testing"""
    from io import BytesIO
    # Create 11MB file (over 10MB limit)
    file = BytesIO(b'x' * (11 * 1024 * 1024))
    file.name = 'large.jpg'
    file.content_type = 'image/jpeg'
    return file


# ==================== Error Fixtures ====================

@pytest.fixture
def sample_validation_error():
    """Sample validation error for testing"""
    return {
        'error_code': 'VALIDATION_ERROR',
        'message': 'Invalid input',
        'details': {'field': 'topic', 'issue': 'too long'}
    }


@pytest.fixture
def sample_auth_error():
    """Sample authentication error for testing"""
    return {
        'error_code': 'AUTH_REQUIRED',
        'message': 'Authentication required',
        'details': {}
    }


# ==================== Mock External Services ====================

@pytest.fixture
def mock_gemini_api():
    """Mock Google Gemini API"""
    mock = Mock()
    mock.generate_content.return_value.text = '{"explanation": "Test explanation"}'
    return mock


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = Mock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    return mock


# ==================== Hypothesis Strategies ====================

@pytest.fixture
def hypothesis_settings():
    """Configure Hypothesis for property-based testing"""
    from hypothesis import settings, Verbosity
    return settings(
        max_examples=100,
        verbosity=Verbosity.verbose,
        deadline=None
    )


# ==================== Cleanup Fixtures ====================

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables after each test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear caches before each test"""
    # Clear any in-memory caches
    yield
    # Cleanup after test


# ==================== Pytest Hooks ====================

def pytest_configure(config):
    """Configure pytest"""
    # Set test environment
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['TESTING'] = 'true'


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    # Add markers automatically based on test location
    for item in items:
        if 'test_auth' in item.nodeid:
            item.add_marker(pytest.mark.auth)
        if 'test_validation' in item.nodeid:
            item.add_marker(pytest.mark.validation)
        if 'property' in item.nodeid:
            item.add_marker(pytest.mark.property)
        if 'integration' in item.nodeid:
            item.add_marker(pytest.mark.integration)


def pytest_report_header(config):
    """Add custom header to pytest report"""
    return [
        "Production Readiness Test Suite",
        f"Environment: {os.getenv('ENVIRONMENT', 'test')}",
        f"Python: {sys.version.split()[0]}"
    ]
