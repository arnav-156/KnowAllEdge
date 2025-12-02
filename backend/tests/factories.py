"""
Test Data Factories
Provides factory classes for generating test data
Requirements: 6.4 - Create test fixtures and factories
"""

from datetime import datetime, timedelta
from faker import Faker
import random
import hashlib

fake = Faker()


class UserFactory:
    """Factory for creating test users"""
    
    @staticmethod
    def create(
        email=None,
        password='test_password_123',
        role='user',
        quota_tier='free',
        **kwargs
    ):
        """Create a test user"""
        from auth_models import User
        
        return User(
            id=kwargs.get('id', random.randint(1, 1000000)),
            email=email or fake.email(),
            password_hash=kwargs.get('password_hash', f'$2b$12${fake.sha256()[:50]}'),
            role=role,
            quota_tier=quota_tier,
            created_at=kwargs.get('created_at', datetime.utcnow()),
            updated_at=kwargs.get('updated_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_batch(count=5, **kwargs):
        """Create multiple test users"""
        return [UserFactory.create(**kwargs) for _ in range(count)]
    
    @staticmethod
    def create_admin(**kwargs):
        """Create an admin user"""
        return UserFactory.create(role='admin', quota_tier='premium', **kwargs)


class SessionFactory:
    """Factory for creating test sessions"""
    
    @staticmethod
    def create(
        user_id=None,
        token=None,
        expires_in_hours=24,
        **kwargs
    ):
        """Create a test session"""
        from auth_models import Session
        
        if token is None:
            token = fake.sha256()
        
        return Session(
            id=kwargs.get('id', random.randint(1, 1000000)),
            user_id=user_id or random.randint(1, 1000),
            token_hash=hashlib.sha256(token.encode()).hexdigest(),
            expires_at=kwargs.get('expires_at', datetime.utcnow() + timedelta(hours=expires_in_hours)),
            ip_address=kwargs.get('ip_address', fake.ipv4()),
            user_agent=kwargs.get('user_agent', fake.user_agent()),
            created_at=kwargs.get('created_at', datetime.utcnow())
        )
    
    @staticmethod
    def create_expired(**kwargs):
        """Create an expired session"""
        return SessionFactory.create(
            expires_at=datetime.utcnow() - timedelta(hours=1),
            **kwargs
        )


class APIKeyFactory:
    """Factory for creating test API keys"""
    
    @staticmethod
    def create(
        user_id=None,
        key=None,
        prefix='sk_',
        **kwargs
    ):
        """Create a test API key"""
        from auth_models import APIKey
        
        if key is None:
            key = f"{prefix}{fake.sha256()[:32]}"
        
        return APIKey(
            id=kwargs.get('id', random.randint(1, 1000000)),
            user_id=user_id or random.randint(1, 1000),
            key_hash=hashlib.sha256(key.encode()).hexdigest(),
            key_prefix=prefix,
            name=kwargs.get('name', f'Test API Key {random.randint(1, 100)}'),
            created_at=kwargs.get('created_at', datetime.utcnow()),
            last_used_at=kwargs.get('last_used_at')
        )


class RequestFactory:
    """Factory for creating test HTTP requests"""
    
    @staticmethod
    def create(
        method='GET',
        path='/api/test',
        headers=None,
        json_data=None,
        **kwargs
    ):
        """Create a mock request"""
        from unittest.mock import Mock
        
        request = Mock()
        request.method = method
        request.path = path
        request.headers = headers or {}
        request.json = json_data or {}
        request.args = kwargs.get('args', {})
        request.form = kwargs.get('form', {})
        request.remote_addr = kwargs.get('remote_addr', fake.ipv4())
        request.user_agent = kwargs.get('user_agent', fake.user_agent())
        
        return request
    
    @staticmethod
    def create_authenticated(token=None, **kwargs):
        """Create an authenticated request"""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token or fake.sha256()}'
        kwargs['headers'] = headers
        return RequestFactory.create(**kwargs)


class ValidationErrorFactory:
    """Factory for creating test validation errors"""
    
    @staticmethod
    def create(field='test_field', message='Invalid value', **kwargs):
        """Create a validation error"""
        return {
            'field': field,
            'message': message,
            'code': kwargs.get('code', 'VALIDATION_ERROR'),
            'details': kwargs.get('details', {})
        }


class TopicFactory:
    """Factory for creating test topics"""
    
    @staticmethod
    def create(length=None):
        """Create a test topic"""
        if length:
            return fake.text(max_nb_chars=length)[:length]
        return fake.sentence(nb_words=random.randint(2, 5)).rstrip('.')
    
    @staticmethod
    def create_batch(count=5):
        """Create multiple topics"""
        return [TopicFactory.create() for _ in range(count)]


class SubtopicsFactory:
    """Factory for creating test subtopics"""
    
    @staticmethod
    def create(count=None):
        """Create a list of subtopics"""
        count = count or random.randint(3, 10)
        return [fake.sentence(nb_words=random.randint(2, 4)).rstrip('.') for _ in range(count)]


class FileFactory:
    """Factory for creating test file objects"""
    
    @staticmethod
    def create(
        filename=None,
        content=b'test content',
        content_type='image/jpeg',
        size=None
    ):
        """Create a test file"""
        from io import BytesIO
        
        if filename is None:
            ext = content_type.split('/')[-1]
            filename = f'test_{fake.uuid4()}.{ext}'
        
        if size:
            content = b'x' * size
        
        file = BytesIO(content)
        file.name = filename
        file.content_type = content_type
        file.seek(0)
        
        return file
    
    @staticmethod
    def create_image(size=1024):
        """Create a test image file"""
        return FileFactory.create(
            filename='test.jpg',
            content=b'x' * size,
            content_type='image/jpeg',
            size=size
        )
    
    @staticmethod
    def create_oversized(max_size=10*1024*1024):
        """Create an oversized file"""
        return FileFactory.create(
            size=max_size + 1024
        )


class DatabaseFactory:
    """Factory for database-related test data"""
    
    @staticmethod
    def create_connection_string(
        host='localhost',
        port=5432,
        database='test_db',
        user='test_user',
        password='test_pass'
    ):
        """Create a test database connection string"""
        return f'postgresql://{user}:{password}@{host}:{port}/{database}'


class CleanupManager:
    """Manager for cleaning up test data"""
    
    def __init__(self):
        self.cleanup_functions = []
    
    def register(self, cleanup_fn):
        """Register a cleanup function"""
        self.cleanup_functions.append(cleanup_fn)
    
    def cleanup(self):
        """Execute all cleanup functions"""
        for fn in reversed(self.cleanup_functions):
            try:
                fn()
            except Exception as e:
                print(f"Cleanup error: {e}")
        self.cleanup_functions.clear()


# Global cleanup manager
cleanup_manager = CleanupManager()
