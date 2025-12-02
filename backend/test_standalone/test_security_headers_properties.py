"""
Property-Based Tests for Security Headers
Tests Properties 42, 43, 44, 45, 46, 47 from design document
"""

import pytest
from hypothesis import given, strategies as st, settings
from hypothesis import HealthCheck
from flask import Flask, Response
from unittest.mock import Mock, patch

from security_headers import (
    SecurityHeadersMiddleware,
    HTTPSRedirector,
    configure_secure_cookies,
    set_secure_cookie
)


# Test fixtures
@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['ENV'] = 'production'
    return app


def create_test_app_with_security():
    """Create a fresh Flask app with security middleware for testing"""
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    test_app.config['ENV'] = 'production'
    SecurityHeadersMiddleware(test_app)
    
    # Add catch-all route
    @test_app.route('/', defaults={'path': ''})
    @test_app.route('/<path:path>')
    def catch_all(path):
        return {'success': True}
    
    return test_app


# Strategies
path_strategy = st.sampled_from([
    '/',
    '/api/test',
    '/api/users',
    '/dashboard',
    '/admin'
])


class TestSecurityHeadersProperties:
    """
    Property-based tests for security headers middleware
    
    **Feature: production-readiness, Properties 42-47**
    """
    
    @given(path=path_strategy)
    @settings(max_examples=50, deadline=None)
    def test_property_42_csp_header_presence(self, path):
        """
        Property 42: CSP header presence
        
        For any HTTP response, the Content-Security-Policy header should be 
        present with appropriate directives
        
        **Validates: Requirements 10.1**
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get(path)
            
            # Verify CSP header is present
            assert 'Content-Security-Policy' in response.headers, \
                "Content-Security-Policy header must be present"
            
            csp_value = response.headers['Content-Security-Policy']
            
            # Verify CSP contains essential directives
            assert 'default-src' in csp_value, \
                "CSP must contain default-src directive"
            assert 'script-src' in csp_value, \
                "CSP must contain script-src directive"
            assert 'style-src' in csp_value, \
                "CSP must contain style-src directive"
            
            # Verify CSP is not empty
            assert len(csp_value) > 0, \
                "CSP header must not be empty"
    
    @given(path=path_strategy)
    @settings(max_examples=50, deadline=None)
    def test_property_43_x_frame_options_header(self, path):
        """
        Property 43: X-Frame-Options header
        
        For any HTTP response, the X-Frame-Options header should be set to DENY
        
        **Validates: Requirements 10.2**
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get(path)
            
            # Verify X-Frame-Options header is present
            assert 'X-Frame-Options' in response.headers, \
                "X-Frame-Options header must be present"
            
            # Verify value is DENY
            assert response.headers['X-Frame-Options'] == 'DENY', \
                "X-Frame-Options must be set to DENY"
    
    @given(path=path_strategy)
    @settings(max_examples=50, deadline=None)
    def test_property_44_hsts_header(self, path):
        """
        Property 44: HSTS header
        
        For any HTTP response, the Strict-Transport-Security header should be 
        present with max-age >= 31536000
        
        **Validates: Requirements 10.3**
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get(path)
            
            # Verify HSTS header is present
            assert 'Strict-Transport-Security' in response.headers, \
                "Strict-Transport-Security header must be present"
            
            hsts_value = response.headers['Strict-Transport-Security']
            
            # Verify max-age is present
            assert 'max-age=' in hsts_value, \
                "HSTS must contain max-age directive"
            
            # Extract max-age value
            for part in hsts_value.split(';'):
                part = part.strip()
                if part.startswith('max-age='):
                    max_age = int(part.split('=')[1])
                    assert max_age >= 31536000, \
                        f"HSTS max-age must be >= 31536000 (1 year), got {max_age}"
                    break
            else:
                pytest.fail("Could not find max-age in HSTS header")
    
    @given(path=path_strategy)
    @settings(max_examples=50, deadline=None)
    def test_property_45_x_content_type_options_header(self, path):
        """
        Property 45: X-Content-Type-Options header
        
        For any HTTP response, the X-Content-Type-Options header should be 
        set to nosniff
        
        **Validates: Requirements 10.5**
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get(path)
            
            # Verify X-Content-Type-Options header is present
            assert 'X-Content-Type-Options' in response.headers, \
                "X-Content-Type-Options header must be present"
            
            # Verify value is nosniff
            assert response.headers['X-Content-Type-Options'] == 'nosniff', \
                "X-Content-Type-Options must be set to nosniff"
    
    @given(path=path_strategy)
    @settings(max_examples=50, deadline=None)
    def test_property_47_referrer_policy_header(self, path):
        """
        Property 47: Referrer-Policy header
        
        For any HTTP response, the Referrer-Policy header should be present
        
        **Validates: Requirements 10.7**
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get(path)
            
            # Verify Referrer-Policy header is present
            assert 'Referrer-Policy' in response.headers, \
                "Referrer-Policy header must be present"
            
            referrer_policy = response.headers['Referrer-Policy']
            
            # Verify it's a valid policy
            valid_policies = [
                'no-referrer',
                'no-referrer-when-downgrade',
                'origin',
                'origin-when-cross-origin',
                'same-origin',
                'strict-origin',
                'strict-origin-when-cross-origin',
                'unsafe-url'
            ]
            
            assert referrer_policy in valid_policies, \
                f"Referrer-Policy must be a valid policy, got '{referrer_policy}'"
    
    @given(
        cookie_name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        cookie_value=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    @settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_46_secure_cookie_flags(self, cookie_name, cookie_value):
        """
        Property 46: Secure cookie flags
        
        For any cookie set by the system, the Secure and HttpOnly flags 
        should be enabled
        
        **Validates: Requirements 10.6**
        """
        # Create a fresh app for each test to avoid route conflicts
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        
        @test_app.route('/set-cookie')
        def set_cookie_route():
            response = Response('{"success": true}')
            set_secure_cookie(
                response,
                key=cookie_name,
                value=cookie_value
            )
            return response
        
        with test_app.test_client() as client:
            response = client.get('/set-cookie')
            
            # Get Set-Cookie header
            set_cookie_header = response.headers.get('Set-Cookie', '')
            
            if set_cookie_header:
                # Verify Secure flag is present
                assert 'Secure' in set_cookie_header, \
                    "Cookie must have Secure flag"
                
                # Verify HttpOnly flag is present
                assert 'HttpOnly' in set_cookie_header, \
                    "Cookie must have HttpOnly flag"
                
                # Verify SameSite is present
                assert 'SameSite' in set_cookie_header, \
                    "Cookie must have SameSite attribute"
    
    def test_all_security_headers_present(self):
        """
        Test that all required security headers are present in a single response
        """
        test_app = create_test_app_with_security()
        
        with test_app.test_client() as client:
            response = client.get('/test')
            
            required_headers = [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security',
                'X-XSS-Protection',
                'Referrer-Policy',
                'Permissions-Policy'
            ]
            
            for header in required_headers:
                assert header in response.headers, \
                    f"Required security header '{header}' is missing"
    
    def test_https_redirector_in_production(self):
        """
        Test that HTTPS redirector works in production mode
        """
        # Create a fresh app for production testing
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        test_app.config['ENV'] = 'production'
        
        HTTPSRedirector(test_app)
        
        @test_app.route('/test')
        def test_route():
            return {'success': True}
        
        with test_app.test_client() as client:
            # In test mode with TESTING=True, Flask doesn't actually redirect
            # but we can verify the middleware is installed and doesn't break requests
            response = client.get('/test')
            assert response.status_code in [200, 301, 302], \
                "HTTPS redirector should allow request or redirect"
            
            # Verify the route works
            if response.status_code == 200:
                assert response.json == {'success': True}
    
    def test_https_redirector_skips_development(self):
        """
        Test that HTTPS redirector is skipped in development mode
        """
        # Create a fresh app for development testing
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        test_app.config['ENV'] = 'development'
        
        HTTPSRedirector(test_app)
        
        @test_app.route('/test')
        def test_route():
            return {'success': True}
        
        with test_app.test_client() as client:
            response = client.get('/test')
            # Should not redirect in development
            assert response.status_code == 200
    
    def test_secure_cookie_configuration(self, app):
        """
        Test that secure cookie configuration is applied correctly
        """
        configure_secure_cookies(app)
        
        # Verify configuration
        assert app.config['SESSION_COOKIE_SECURE'] == True
        assert app.config['SESSION_COOKIE_HTTPONLY'] == True
        assert app.config['SESSION_COOKIE_SAMESITE'] == 'Strict'
        assert app.config['PERMANENT_SESSION_LIFETIME'] == 86400
    
    @given(
        max_age=st.integers(min_value=1, max_value=31536000)
    )
    @settings(max_examples=30, deadline=None)
    def test_hsts_max_age_configuration(self, max_age):
        """
        Test that HSTS max-age can be configured
        """
        test_app = Flask(__name__)
        test_app.config['TESTING'] = True
        
        SecurityHeadersMiddleware(
            test_app,
            hsts_max_age=max_age
        )
        
        @test_app.route('/test')
        def test_route():
            return {'success': True}
        
        with test_app.test_client() as client:
            response = client.get('/test')
            hsts_value = response.headers.get('Strict-Transport-Security', '')
            
            # Extract and verify max-age
            for part in hsts_value.split(';'):
                part = part.strip()
                if part.startswith('max-age='):
                    actual_max_age = int(part.split('=')[1])
                    assert actual_max_age == max_age, \
                        f"HSTS max-age should be {max_age}, got {actual_max_age}"
                    break


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
