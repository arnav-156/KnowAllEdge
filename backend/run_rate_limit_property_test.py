"""
Standalone runner for rate limit property tests
Bypasses conftest.py configuration issues
"""

import sys
import os

# Set ALL required environment variables before any imports
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-32chars'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['REDIS_PASSWORD'] = 'test-redis-password-16chars'
os.environ['GOOGLE_API_KEY'] = 'test-google-api-key'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing-only-32chars'

# Run pytest programmatically
import pytest

if __name__ == '__main__':
    # Use --override-ini to ignore conftest.py
    sys.exit(pytest.main([
        'test_rate_limit_properties.py',
        '-v',
        '--tb=short',
        '-x',
        '--no-cov',
        '--override-ini=python_files=test_rate_limit_properties.py'
    ]))
