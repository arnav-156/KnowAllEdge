# Backend Test Suite

## Overview
Comprehensive test suite for production readiness validation.

## Test Structure

```
backend/
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration
├── test_*.py                # Test files
└── tests/
    ├── unit/                # Unit tests
    ├── integration/         # Integration tests
    ├── property/            # Property-based tests
    └── fixtures/            # Additional test fixtures
```

## Running Tests

### All Tests
```bash
pytest
```

### Specific Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests
pytest -m integration

# Property-based tests
pytest -m property

# Security tests
pytest -m security

# Authentication tests
pytest -m auth
```

### With Coverage
```bash
# Generate coverage report
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Parallel Execution
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### Specific Test File
```bash
pytest test_auth_properties.py
```

### Specific Test Function
```bash
pytest test_auth_properties.py::test_password_hashing_consistency
```

## Test Markers

Tests are categorized using markers:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.property` - Property-based tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.validation` - Input validation tests
- `@pytest.mark.security` - Security tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.api` - API endpoint tests

## Writing Tests

### Unit Test Example
```python
import pytest

@pytest.mark.unit
def test_password_hashing(password_hasher):
    password = "test_password"
    hashed = password_hasher.hash(password)
    assert password_hasher.verify(password, hashed)
```

### Property-Based Test Example
```python
from hypothesis import given, strategies as st
import pytest

@pytest.mark.property
@given(password=st.text(min_size=8, max_size=100))
def test_password_hashing_consistency(password_hasher, password):
    hashed = password_hasher.hash(password)
    assert password_hasher.verify(password, hashed)
```

### Integration Test Example
```python
import pytest

@pytest.mark.integration
def test_auth_endpoint(client):
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    assert response.status_code == 200
```

## Fixtures

Common fixtures available in `conftest.py`:

### Configuration
- `test_config` - Test configuration
- `app` - Flask app instance
- `client` - Flask test client
- `app_context` - Flask application context
- `request_context` - Flask request context

### Database
- `db_session` - Database session
- `clean_database` - Clean database before test

### Authentication
- `password_hasher` - PasswordHasher instance
- `sample_user` - Sample user object
- `admin_user` - Admin user object
- `sample_session` - Sample session object
- `sample_api_key` - Sample API key object
- `valid_jwt_token` - Valid JWT token
- `expired_jwt_token` - Expired JWT token

### Requests
- `mock_request` - Mock Flask request
- `authenticated_request` - Authenticated mock request

### Validation
- `valid_topic` - Valid topic string
- `invalid_topic_too_long` - Invalid topic (too long)
- `invalid_topic_special_chars` - Invalid topic (special chars)
- `valid_subtopics` - Valid subtopics array
- `invalid_subtopics_too_many` - Invalid subtopics (too many)

### Files
- `valid_image_file` - Valid image file
- `invalid_file_type` - Invalid file type
- `oversized_file` - Oversized file

### Mocks
- `mock_gemini_api` - Mock Gemini API
- `mock_redis` - Mock Redis client

## Coverage Requirements

- Minimum coverage: 80%
- Target coverage: 90%+
- Critical paths: 100%

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **Arrange-Act-Assert**: Follow AAA pattern
4. **Mock External Services**: Don't call real APIs in tests
5. **Fast Tests**: Keep unit tests fast (<1s each)
6. **Property Tests**: Use Hypothesis for edge cases
7. **Fixtures**: Reuse fixtures for common setup
8. **Markers**: Tag tests appropriately

## Continuous Integration

Tests run automatically on:
- Every commit (unit tests)
- Pull requests (all tests)
- Pre-deployment (full suite + security)

## Troubleshooting

### Tests Failing Locally
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Show print statements
pytest -s
```

### Coverage Issues
```bash
# See which lines are not covered
pytest --cov=. --cov-report=term-missing
```

### Slow Tests
```bash
# Find slowest tests
pytest --durations=10
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
