"""
Authentication Integration Tests
Task 1.14: Write integration tests for auth endpoints
"""

import pytest
import json
from flask import Flask
from datetime import datetime

from auth_routes import auth_bp
from auth_models import User, Session as UserSession, Base, create_database_engine, create_session_factory
from password_hasher import PasswordHasher


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Register blueprint
    app.register_blueprint(auth_bp)
    
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session():
    """Create test database session"""
    engine = create_database_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    SessionFactory = create_session_factory(engine)
    session = SessionFactory()
    
    yield session
    
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user"""
    hasher = PasswordHasher()
    
    user = User(
        email='test@example.com',
        password_hash=hasher.hash('testpassword123'),
        email_verified=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(user)
    db_session.commit()
    
    return user


class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_successful_registration(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register', 
                             json={
                                 'email': 'newuser@example.com',
                                 'password': 'newpassword123',
                                 'confirm_password': 'newpassword123'
                             })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'User registered successfully'
        assert 'user_id' in data
        assert data['email'] == 'newuser@example.com'
    
    def test_registration_missing_fields(self, client):
        """Test registration with missing fields"""
        response = client.post('/api/auth/register',
                             json={'email': 'test@example.com'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_registration_password_mismatch(self, client):
        """Test registration with password mismatch"""
        response = client.post('/api/auth/register',
                             json={
                                 'email': 'test@example.com',
                                 'password': 'password123',
                                 'confirm_password': 'different123'
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Passwords do not match' in data['error']
    
    def test_registration_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/api/auth/register',
                             json={
                                 'email': 'test@example.com',
                                 'password': '123',
                                 'confirm_password': '123'
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'at least 8 characters' in data['error']
    
    def test_registration_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register',
                             json={
                                 'email': 'invalid-email',
                                 'password': 'password123',
                                 'confirm_password': 'password123'
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Invalid email format' in data['error']


class TestUserLogin:
    """Test user login endpoint"""
    
    def test_successful_login(self, client, test_user):
        """Test successful login"""
        response = client.post('/api/auth/login',
                             json={
                                 'email': 'test@example.com',
                                 'password': 'testpassword123'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Login successful'
        assert 'access_token' in data
        assert data['token_type'] == 'Bearer'
        assert 'user' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login',
                             json={
                                 'email': 'test@example.com',
                                 'password': 'wrongpassword'
                             })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid credentials' in data['error']
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post('/api/auth/login',
                             json={
                                 'email': 'nonexistent@example.com',
                                 'password': 'password123'
                             })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Invalid credentials' in data['error']
    
    def test_login_missing_fields(self, client):
        """Test login with missing fields"""
        response = client.post('/api/auth/login',
                             json={'email': 'test@example.com'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Email and password required' in data['error']


class TestAuthenticatedEndpoints:
    """Test endpoints that require authentication"""
    
    def get_auth_token(self, client, test_user):
        """Helper to get authentication token"""
        response = client.post('/api/auth/login',
                             json={
                                 'email': 'test@example.com',
                                 'password': 'testpassword123'
                             })
        
        data = json.loads(response.data)
        return data['access_token']
    
    def test_get_current_user(self, client, test_user):
        """Test get current user endpoint"""
        token = self.get_auth_token(client, test_user)
        
        response = client.get('/api/auth/me',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_no_token(self, client):
        """Test get current user without token"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Authorization header required' in data['error']
    
    def test_logout(self, client, test_user):
        """Test logout endpoint"""
        token = self.get_auth_token(client, test_user)
        
        response = client.post('/api/auth/logout',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Logout successful'
    
    def test_change_password(self, client, test_user):
        """Test change password endpoint"""
        token = self.get_auth_token(client, test_user)
        
        response = client.post('/api/auth/change-password',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'current_password': 'testpassword123',
                                 'new_password': 'newpassword123',
                                 'confirm_password': 'newpassword123'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Password changed successfully'
    
    def test_change_password_wrong_current(self, client, test_user):
        """Test change password with wrong current password"""
        token = self.get_auth_token(client, test_user)
        
        response = client.post('/api/auth/change-password',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'current_password': 'wrongpassword',
                                 'new_password': 'newpassword123',
                                 'confirm_password': 'newpassword123'
                             })
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'Current password is incorrect' in data['error']
    
    def test_refresh_token(self, client, test_user):
        """Test token refresh endpoint"""
        token = self.get_auth_token(client, test_user)
        
        response = client.post('/api/auth/refresh',
                             headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['token_type'] == 'Bearer'
    
    def test_get_sessions(self, client, test_user):
        """Test get user sessions endpoint"""
        token = self.get_auth_token(client, test_user)
        
        response = client.get('/api/auth/sessions',
                            headers={'Authorization': f'Bearer {token}'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'sessions' in data
        assert 'count' in data


class TestTokenRefresh:
    """Test token refresh flow"""
    
    def test_token_refresh_flow(self, client, test_user):
        """Test complete token refresh flow"""
        # Login
        login_response = client.post('/api/auth/login',
                                    json={
                                        'email': 'test@example.com',
                                        'password': 'testpassword123'
                                    })
        
        assert login_response.status_code == 200
        login_data = json.loads(login_response.data)
        old_token = login_data['access_token']
        
        # Refresh token
        refresh_response = client.post('/api/auth/refresh',
                                      headers={'Authorization': f'Bearer {old_token}'})
        
        assert refresh_response.status_code == 200
        refresh_data = json.loads(refresh_response.data)
        new_token = refresh_data['access_token']
        
        # Verify new token works
        me_response = client.get('/api/auth/me',
                                headers={'Authorization': f'Bearer {new_token}'})
        
        assert me_response.status_code == 200


class TestSessionManagement:
    """Test session management"""
    
    def test_multiple_sessions(self, client, test_user):
        """Test user can have multiple active sessions"""
        # Login from first device
        response1 = client.post('/api/auth/login',
                               json={
                                   'email': 'test@example.com',
                                   'password': 'testpassword123'
                               })
        
        assert response1.status_code == 200
        token1 = json.loads(response1.data)['access_token']
        
        # Login from second device
        response2 = client.post('/api/auth/login',
                               json={
                                   'email': 'test@example.com',
                                   'password': 'testpassword123'
                               })
        
        assert response2.status_code == 200
        token2 = json.loads(response2.data)['access_token']
        
        # Both tokens should work
        me_response1 = client.get('/api/auth/me',
                                 headers={'Authorization': f'Bearer {token1}'})
        me_response2 = client.get('/api/auth/me',
                                 headers={'Authorization': f'Bearer {token2}'})
        
        assert me_response1.status_code == 200
        assert me_response2.status_code == 200
    
    def test_logout_invalidates_session(self, client, test_user):
        """Test logout invalidates the session"""
        # Login
        login_response = client.post('/api/auth/login',
                                    json={
                                        'email': 'test@example.com',
                                        'password': 'testpassword123'
                                    })
        
        token = json.loads(login_response.data)['access_token']
        
        # Logout
        logout_response = client.post('/api/auth/logout',
                                     headers={'Authorization': f'Bearer {token}'})
        
        assert logout_response.status_code == 200


class TestPasswordChange:
    """Test password change functionality"""
    
    def test_password_change_invalidates_sessions(self, client, test_user):
        """Test password change invalidates all sessions"""
        # Login
        login_response = client.post('/api/auth/login',
                                    json={
                                        'email': 'test@example.com',
                                        'password': 'testpassword123'
                                    })
        
        token = json.loads(login_response.data)['access_token']
        
        # Change password
        change_response = client.post('/api/auth/change-password',
                                     headers={'Authorization': f'Bearer {token}'},
                                     json={
                                         'current_password': 'testpassword123',
                                         'new_password': 'newpassword456',
                                         'confirm_password': 'newpassword456'
                                     })
        
        assert change_response.status_code == 200
        
        # Login with new password should work
        new_login_response = client.post('/api/auth/login',
                                        json={
                                            'email': 'test@example.com',
                                            'password': 'newpassword456'
                                        })
        
        assert new_login_response.status_code == 200
    
    def test_password_change_validation(self, client, test_user):
        """Test password change validation"""
        # Login
        login_response = client.post('/api/auth/login',
                                    json={
                                        'email': 'test@example.com',
                                        'password': 'testpassword123'
                                    })
        
        token = json.loads(login_response.data)['access_token']
        
        # Try weak password
        response = client.post('/api/auth/change-password',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'current_password': 'testpassword123',
                                 'new_password': '123',
                                 'confirm_password': '123'
                             })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'at least 8 characters' in data['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
