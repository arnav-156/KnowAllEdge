"""
Standalone GDPR Test Runner
Runs GDPR tests without conftest dependencies
"""

import sys
import os

# Set environment variables before importing anything
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['REDIS_PASSWORD'] = 'test-redis-password'
os.environ['GOOGLE_API_KEY'] = 'test-google-api-key'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing'

# Run pytest
import pytest

if __name__ == '__main__':
    # Run property tests
    print("=" * 80)
    print("Running GDPR Property Tests")
    print("=" * 80)
    
    exit_code = pytest.main([
        'test_gdpr_properties.py',
        '-v',
        '--tb=short',
        '-p', 'no:warnings',
        '--no-header',
        '-x'  # Stop on first failure
    ])
    
    if exit_code == 0:
        print("\n" + "=" * 80)
        print("Running GDPR Integration Tests")
        print("=" * 80)
        
        exit_code = pytest.main([
            'test_gdpr_integration.py',
            '-v',
            '--tb=short',
            '-p', 'no:warnings',
            '--no-header',
            '-x'  # Stop on first failure
        ])
    
    sys.exit(exit_code)
