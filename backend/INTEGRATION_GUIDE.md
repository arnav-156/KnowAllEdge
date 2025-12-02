# Integration Guide for New Production Components

## Overview
This guide explains how to integrate the newly implemented production readiness components into the main application.

## Components to Integrate

### 1. Error Handler

#### Import in main.py
Add to imports section:
```python
from error_handler import error_handler
```

#### Register Error Handlers
Add after Flask app initialization:
```python
# Register centralized error handlers
error_handler.register_error_handlers(app)
```

#### Usage in Routes
```python
from error_handler import error_handler

@app.route('/api/example', methods=['POST'])
def example_endpoint():
    try:
        # Your logic here
        pass
    except ValueError as e:
        response, status = error_handler.handle_validation_error([str(e)])
        return jsonify(response), status
    except Exception as e:
        response, status = error_handler.handle_exception(e)
        return jsonify(response), status
```

### 2. Request Validator

#### Import in main.py
Add to imports section:
```python
from request_validator import request_validator, validate_json_request
```

#### Apply to Routes
```python
@app.route('/api/generate', methods=['POST'])
@validate_json_request()  # Validates JSON content-type and body
@require_auth()
def generate_content():
    data = request.get_json()
    
    # Validate topic
    topic_result = request_validator.validate_topic(data.get('topic', ''))
    if not topic_result.is_valid:
        response, status = error_handler.handle_validation_error(topic_result.errors)
        return jsonify(response), status
    
    topic = topic_result.sanitized_value
    
    # Continue with logic...
```

#### Validate Arrays
```python
# Validate array fields
subtopics = data.get('subtopics', [])
array_result = request_validator.validate_array(subtopics, 'subtopics')
if not array_result.is_valid:
    response, status = error_handler.handle_validation_error(array_result.errors)
    return jsonify(response), status
```

### 3. File Validator

#### Import in main.py
Add to imports section:
```python
from file_validator import file_validator
```

#### Apply to File Upload Routes
```python
@app.route('/api/upload', methods=['POST'])
@require_auth()
def upload_file():
    if 'file' not in request.files:
        response, status = error_handler.handle_validation_error(['No file provided'])
        return jsonify(response), status
    
    file = request.files['file']
    
    # Validate file
    validation_result = file_validator.validate_file(file, file.filename)
    
    if not validation_result.is_valid:
        response, status = error_handler.handle_validation_error(validation_result.errors)
        return jsonify(response), status
    
    # Use safe filename
    safe_filename = validation_result.safe_filename
    
    # Save file securely
    file.save(os.path.join(UPLOAD_FOLDER, safe_filename))
    
    return jsonify({
        'success': True,
        'filename': safe_filename,
        'size': validation_result.file_size,
        'mime_type': validation_result.mime_type
    })
```

## Complete Integration Example

Here's a complete example of an endpoint using all new components:

```python
from flask import Flask, request, jsonify, g
from error_handler import error_handler
from request_validator import request_validator, validate_json_request
from auth import require_auth, get_current_user

@app.route('/api/content/generate', methods=['POST'])
@validate_json_request()  # Step 1: Validate JSON
@require_auth()           # Step 2: Authenticate user
def generate_content():
    """
    Generate content with full validation and error handling
    """
    try:
        # Get JSON data (already validated by decorator)
        data = request.get_json()
        
        # Validate topic
        topic_result = request_validator.validate_topic(data.get('topic', ''))
        if not topic_result.is_valid:
            response, status = error_handler.handle_validation_error(topic_result.errors)
            return jsonify(response), status
        
        topic = topic_result.sanitized_value
        
        # Validate subtopics array (if provided)
        if 'subtopics' in data:
            subtopics_result = request_validator.validate_array(
                data['subtopics'], 
                'subtopics'
            )
            if not subtopics_result.is_valid:
                response, status = error_handler.handle_validation_error(
                    subtopics_result.errors
                )
                return jsonify(response), status
            
            subtopics = subtopics_result.sanitized_value
        else:
            subtopics = []
        
        # Get authenticated user
        user = get_current_user()
        
        # Your business logic here
        result = generate_content_logic(topic, subtopics, user)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except ValueError as e:
        # Handle validation errors
        response, status = error_handler.handle_validation_error([str(e)])
        return jsonify(response), status
        
    except Exception as e:
        # Handle unexpected errors
        response, status = error_handler.handle_exception(e)
        return jsonify(response), status
```

## Testing the Integration

### 1. Test Error Handling
```bash
# Test 400 error
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: text/plain" \
  -d "invalid"

# Expected: Validation error with request_id and timestamp
```

### 2. Test Authentication
```bash
# Test without auth
curl -X GET http://localhost:5000/api/protected

# Expected: 401 Unauthorized

# Test with API key
curl -X GET http://localhost:5000/api/protected \
  -H "X-API-Key: sk_your_api_key"

# Expected: Success
```

### 3. Test Input Validation
```bash
# Test with invalid topic (too long)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_your_api_key" \
  -d '{"topic": "'$(python -c 'print("a"*600)')'"}'

# Expected: Validation error about topic length
```

### 4. Test File Upload
```bash
# Test with invalid file type
curl -X POST http://localhost:5000/api/upload \
  -H "X-API-Key: sk_your_api_key" \
  -F "file=@malicious.exe"

# Expected: Validation error about file extension
```

## Property Tests

Run the property tests to verify implementations:

```bash
cd backend

# Test authentication
pytest test_auth_properties.py -v

# Test validation
pytest test_validation_properties.py -v

# Test error handling
pytest test_error_handling_properties.py -v

# Test password hashing
pytest test_password_properties.py -v

# Run all property tests
pytest test_*_properties.py -v
```

## Monitoring Integration

### Add Request ID Tracking
```python
@app.before_request
def before_request():
    # Generate request ID
    g.request_id = error_handler.generate_request_id()
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'user_id': getattr(g, 'user_id', 'anonymous')
        }
    )

@app.after_request
def after_request(response):
    # Add request ID to response headers
    response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
    
    # Log response
    logger.info(
        f"Request completed",
        extra={
            'request_id': g.request_id,
            'status_code': response.status_code,
            'duration_ms': getattr(g, 'request_duration', 0)
        }
    )
    
    return response
```

## Configuration

### Environment Variables
Add to `.env`:
```bash
# Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRATION_HOURS=24
ADMIN_API_KEY=sk_admin_your_admin_key
ADMIN_EMAIL=admin@KNOWALLEDGE.com

# Validation
MAX_TOPIC_LENGTH=500
MAX_ARRAY_LENGTH=100
MAX_FILE_SIZE=10485760  # 10 MB

# Error Handling
DOCS_BASE_URL=https://docs.KNOWALLEDGE.com/errors
```

## Checklist

- [ ] Import error_handler in main.py
- [ ] Register error handlers with Flask app
- [ ] Import request_validator in main.py
- [ ] Apply @validate_json_request() to POST endpoints
- [ ] Add topic validation to content generation endpoints
- [ ] Add array validation where applicable
- [ ] Import file_validator for file upload endpoints
- [ ] Add file validation to upload endpoints
- [ ] Add request ID tracking in before_request
- [ ] Add request ID to response headers in after_request
- [ ] Test all endpoints with invalid inputs
- [ ] Run property tests
- [ ] Update API documentation with error responses
- [ ] Configure environment variables

## Next Steps

1. **Integrate components** - Follow this guide to integrate all new components
2. **Run tests** - Verify all property tests pass
3. **Test endpoints** - Test all API endpoints with various inputs
4. **Update documentation** - Document new error responses and validation rules
5. **Monitor logs** - Check that structured logging works correctly
6. **Continue implementation** - Move on to Phase 4 (Database Security)

## Troubleshooting

### Import Errors
If you get import errors, ensure all files are in the backend directory:
- `error_handler.py`
- `request_validator.py`
- `file_validator.py`
- `test_auth_properties.py`
- `test_validation_properties.py`
- `test_error_handling_properties.py`

### Dependency Errors
Install required packages:
```bash
pip install hypothesis pytest bcrypt pyjwt python-magic werkzeug
```

### Test Failures
If tests fail, check:
1. All imports are correct
2. Environment variables are set
3. Dependencies are installed
4. Python version is 3.8+

## Support

For issues or questions:
1. Check the implementation files for inline documentation
2. Review the property tests for usage examples
3. Check logs for detailed error messages
4. Refer to PRODUCTION_TASKS_IMPLEMENTATION_SUMMARY.md
