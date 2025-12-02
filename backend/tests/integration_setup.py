"""
Integration Test Environment Setup
Configures test database, Redis, and mocks for integration testing
Requirements: 6.5 - Set up integration test environment
"""

import os
import pytest
from unittest.mock import Mock, patch
import redis


class TestDatabaseManager:
    """Manages test database setup and teardown"""
    
    def __init__(self):
        self.db_url = os.getenv('TEST_DATABASE_URL', 'sqlite:///:memory:')
        self.engine = None
        self.session = None
    
    def setup(self):
        """Set up test database"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        self.engine = create_engine(self.db_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create all tables
        # Base.metadata.create_all(self.engine)
        
        return self.session
    
    def teardown(self):
        """Tear down test database"""
        if self.session:
            self.session.close()
        if self.engine:
            # Drop all tables
            # Base.metadata.drop_all(self.engine)
            self.engine.dispose()
    
    def clear_all_tables(self):
        """Clear all data from tables"""
        if self.session:
            # Delete all records from all tables
            # for table in reversed(Base.metadata.sorted_tables):
            #     self.session.execute(table.delete())
            self.session.commit()


class TestRedisManager:
    """Manages test Redis instance"""
    
    def __init__(self):
        self.redis_url = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/15')
        self.client = None
        self.use_mock = os.getenv('USE_MOCK_REDIS', 'true').lower() == 'true'
    
    def setup(self):
        """Set up test Redis"""
        if self.use_mock:
            # Use mock Redis for tests
            self.client = MockRedis()
        else:
            # Use real Redis (test database 15)
            try:
                self.client = redis.StrictRedis.from_url(
                    self.redis_url,
                    decode_responses=True
                )
                # Test connection
                self.client.ping()
            except redis.ConnectionError:
                print("Warning: Could not connect to Redis, using mock")
                self.client = MockRedis()
        
        return self.client
    
    def teardown(self):
        """Tear down test Redis"""
        if self.client and not self.use_mock:
            # Clear test database
            self.client.flushdb()
            self.client.close()
    
    def clear(self):
        """Clear all Redis data"""
        if self.client:
            if self.use_mock:
                self.client.data.clear()
            else:
                self.client.flushdb()


class MockRedis:
    """Mock Redis client for testing"""
    
    def __init__(self):
        self.data = {}
        self.expiry = {}
    
    def get(self, key):
        """Get value"""
        if key in self.expiry:
            import time
            if time.time() > self.expiry[key]:
                del self.data[key]
                del self.expiry[key]
                return None
        return self.data.get(key)
    
    def set(self, key, value, ex=None):
        """Set value"""
        self.data[key] = value
        if ex:
            import time
            self.expiry[key] = time.time() + ex
        return True
    
    def delete(self, *keys):
        """Delete keys"""
        count = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                count += 1
            if key in self.expiry:
                del self.expiry[key]
        return count
    
    def exists(self, key):
        """Check if key exists"""
        return key in self.data
    
    def flushdb(self):
        """Clear all data"""
        self.data.clear()
        self.expiry.clear()
    
    def ping(self):
        """Ping"""
        return True


class MockGeminiAPI:
    """Mock Google Gemini API for testing"""
    
    def __init__(self):
        self.call_count = 0
        self.responses = []
        self.default_response = {
            'explanation': 'Test explanation',
            'real_world_application': 'Test application',
            'youtube_search_query': 'test query'
        }
    
    def generate_content(self, prompt, **kwargs):
        """Mock generate_content"""
        self.call_count += 1
        
        # Return queued response or default
        if self.responses:
            response_data = self.responses.pop(0)
        else:
            response_data = self.default_response
        
        # Create mock response
        response = Mock()
        response.text = str(response_data) if isinstance(response_data, dict) else response_data
        response.usage_metadata = Mock()
        response.usage_metadata.total_token_count = 1500
        
        return response
    
    def queue_response(self, response):
        """Queue a response for next call"""
        self.responses.append(response)
    
    def reset(self):
        """Reset mock state"""
        self.call_count = 0
        self.responses.clear()


class IntegrationTestEnvironment:
    """Complete integration test environment"""
    
    def __init__(self):
        self.db_manager = TestDatabaseManager()
        self.redis_manager = TestRedisManager()
        self.gemini_mock = MockGeminiAPI()
        self.patches = []
    
    def setup(self):
        """Set up complete test environment"""
        # Setup database
        db_session = self.db_manager.setup()
        
        # Setup Redis
        redis_client = self.redis_manager.setup()
        
        # Mock Gemini API
        gemini_patch = patch('google.generativeai.GenerativeModel')
        mock_model = gemini_patch.start()
        mock_model.return_value.generate_content = self.gemini_mock.generate_content
        self.patches.append(gemini_patch)
        
        return {
            'db_session': db_session,
            'redis_client': redis_client,
            'gemini_mock': self.gemini_mock
        }
    
    def teardown(self):
        """Tear down test environment"""
        # Stop all patches
        for p in self.patches:
            p.stop()
        self.patches.clear()
        
        # Teardown Redis
        self.redis_manager.teardown()
        
        # Teardown database
        self.db_manager.teardown()
    
    def reset(self):
        """Reset environment between tests"""
        self.db_manager.clear_all_tables()
        self.redis_manager.clear()
        self.gemini_mock.reset()


# Pytest fixtures for integration tests

@pytest.fixture(scope='session')
def integration_env():
    """Session-scoped integration environment"""
    env = IntegrationTestEnvironment()
    env.setup()
    yield env
    env.teardown()


@pytest.fixture(scope='function')
def clean_integration_env(integration_env):
    """Function-scoped clean environment"""
    integration_env.reset()
    yield integration_env


@pytest.fixture
def test_db(integration_env):
    """Test database session"""
    return integration_env.db_manager.session


@pytest.fixture
def test_redis(integration_env):
    """Test Redis client"""
    return integration_env.redis_manager.client


@pytest.fixture
def mock_gemini(integration_env):
    """Mock Gemini API"""
    return integration_env.gemini_mock


# Helper functions

def create_test_app():
    """Create Flask app for integration testing"""
    from main import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def seed_test_data(db_session):
    """Seed database with test data"""
    from tests.factories import UserFactory, SessionFactory
    
    # Create test users
    users = UserFactory.create_batch(5)
    for user in users:
        db_session.add(user)
    
    # Create test sessions
    for user in users:
        session = SessionFactory.create(user_id=user.id)
        db_session.add(session)
    
    db_session.commit()
    return users
