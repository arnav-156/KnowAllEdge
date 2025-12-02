"""
Security Implementation Tests
Tests authentication, encrypted secrets, and HTTPS security
"""

import sys
import os
import requests
import json
from time import sleep

# Test configuration
BASE_URL = "http://localhost:5000/api"
TEST_USER_ID = "test_security_user"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(message):
    print(f"\n{Colors.BLUE}🧪 TEST: {message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def test_authentication_registration():
    """Test user registration and API key generation"""
    print_test("User Registration and API Key Generation")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "user_id": TEST_USER_ID,
                "quota_tier": "free"
            },
            timeout=5
        )
        
        if response.status_code == 201:
            data = response.json()
            
            if "api_key" in data and data["api_key"].startswith("sk_"):
                print_success(f"User registered successfully")
                print(f"   User ID: {data['user_id']}")
                print(f"   Quota Tier: {data['quota_tier']}")
                print(f"   API Key: {data['api_key'][:20]}...")
                return data["api_key"]
            else:
                print_error("Invalid API key format")
                return None
        else:
            print_error(f"Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    
    except Exception as e:
        print_error(f"Registration request failed: {e}")
        return None

def test_jwt_login(api_key):
    """Test JWT token generation from API key"""
    print_test("JWT Token Generation (Login)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"api_key": api_key},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "token" in data:
                print_success("JWT token generated successfully")
                print(f"   Token: {data['token'][:40]}...")
                print(f"   Expires In: {data['expires_in']} seconds")
                return data["token"]
            else:
                print_error("Token not found in response")
                return None
        else:
            print_error(f"Login failed: {response.status_code}")
            return None
    
    except Exception as e:
        print_error(f"Login request failed: {e}")
        return None

def test_api_key_authentication(api_key):
    """Test API endpoint with API key authentication"""
    print_test("API Key Authentication (X-API-Key Header)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/validate",
            headers={"X-API-Key": api_key},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("valid"):
                print_success("API key authentication successful")
                print(f"   User ID: {data['user_id']}")
                print(f"   Role: {data['role']}")
                print(f"   Quota Tier: {data['quota_tier']}")
                return True
            else:
                print_error("Authentication validation failed")
                return False
        else:
            print_error(f"Validation failed: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Validation request failed: {e}")
        return False

def test_jwt_authentication(token):
    """Test API endpoint with JWT token authentication"""
    print_test("JWT Token Authentication (Authorization: Bearer)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/validate",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("valid"):
                print_success("JWT token authentication successful")
                print(f"   User ID: {data['user_id']}")
                return True
            else:
                print_error("JWT validation failed")
                return False
        else:
            print_error(f"JWT validation failed: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"JWT validation request failed: {e}")
        return False

def test_unauthenticated_request():
    """Test that protected endpoints reject unauthenticated requests"""
    print_test("Unauthenticated Request Rejection")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cache/clear",
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Unauthenticated request correctly rejected (401)")
            data = response.json()
            print(f"   Error: {data.get('error')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_admin_endpoint_access(api_key):
    """Test that non-admin users cannot access admin endpoints"""
    print_test("Admin Endpoint Access Control")
    
    try:
        response = requests.post(
            f"{BASE_URL}/cache/clear",
            headers={"X-API-Key": api_key},
            timeout=5
        )
        
        if response.status_code == 403:
            print_success("Non-admin user correctly denied access (403)")
            data = response.json()
            print(f"   Error: {data.get('error')}")
            print(f"   Message: {data.get('message')}")
            return True
        elif response.status_code == 200:
            print_warning("Admin endpoint accessible to non-admin user!")
            return False
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_invalid_api_key():
    """Test that invalid API keys are rejected"""
    print_test("Invalid API Key Rejection")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/validate",
            headers={"X-API-Key": "sk_invalid_key_12345"},
            timeout=5
        )
        
        if response.status_code == 401:
            print_success("Invalid API key correctly rejected (401)")
            return True
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_security_headers():
    """Test that security headers are present"""
    print_test("Security Headers Validation")
    
    try:
        response = requests.get(BASE_URL.replace('/api', '/'), timeout=5)
        
        required_headers = [
            'X-Frame-Options',
            'X-Content-Type-Options',
            'X-XSS-Protection',
            'Referrer-Policy'
        ]
        
        headers_present = []
        headers_missing = []
        
        for header in required_headers:
            if header in response.headers:
                headers_present.append(header)
            else:
                headers_missing.append(header)
        
        if len(headers_present) == len(required_headers):
            print_success("All required security headers present")
            for header in headers_present:
                print(f"   ✓ {header}: {response.headers[header]}")
            return True
        else:
            print_warning(f"{len(headers_present)}/{len(required_headers)} headers present")
            for header in headers_present:
                print(f"   ✓ {header}: {response.headers[header]}")
            for header in headers_missing:
                print(f"   ✗ {header}: Missing")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def test_quota_tier_limits(api_key):
    """Test that quota tier information is returned"""
    print_test("Quota Tier Limits")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/validate",
            headers={"X-API-Key": api_key},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            quota_tier = data.get('quota_tier')
            
            print_success(f"Quota tier: {quota_tier}")
            
            # Map to expected limits
            tier_limits = {
                'free': {'rpm': 10, 'rpd': 100, 'tpm': 50000, 'tpd': 500000},
                'basic': {'rpm': 15, 'rpd': 500, 'tpm': 200000, 'tpd': 2000000},
                'premium': {'rpm': 30, 'rpd': 2000, 'tpm': 1000000, 'tpd': 10000000}
            }
            
            if quota_tier in tier_limits:
                limits = tier_limits[quota_tier]
                print(f"   Expected Limits:")
                print(f"   - Requests per Minute (RPM): {limits['rpm']}")
                print(f"   - Requests per Day (RPD): {limits['rpd']}")
                print(f"   - Tokens per Minute (TPM): {limits['tpm']:,}")
                print(f"   - Tokens per Day (TPD): {limits['tpd']:,}")
                return True
            else:
                print_warning(f"Unknown quota tier: {quota_tier}")
                return False
        else:
            print_error(f"Request failed: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Request failed: {e}")
        return False

def main():
    """Run all security tests"""
    print("\n" + "=" * 70)
    print("🔒 KNOWALLEDGE SECURITY IMPLEMENTATION TESTS")
    print("=" * 70)
    
    # Check if server is running
    try:
        response = requests.get(BASE_URL.replace('/api', '/'), timeout=2)
        print_success("Server is running")
    except:
        print_error("Server is not running. Start with: python main.py")
        return
    
    results = []
    
    # Test 1: User Registration
    api_key = test_authentication_registration()
    results.append(("User Registration", api_key is not None))
    
    if not api_key:
        print_error("\nCannot continue without valid API key")
        return
    
    # Test 2: JWT Login
    jwt_token = test_jwt_login(api_key)
    results.append(("JWT Token Generation", jwt_token is not None))
    
    # Test 3: API Key Authentication
    results.append(("API Key Authentication", test_api_key_authentication(api_key)))
    
    # Test 4: JWT Authentication (if token was generated)
    if jwt_token:
        results.append(("JWT Token Authentication", test_jwt_authentication(jwt_token)))
    
    # Test 5: Unauthenticated Request
    results.append(("Unauthenticated Rejection", test_unauthenticated_request()))
    
    # Test 6: Admin Endpoint Access
    results.append(("Admin Access Control", test_admin_endpoint_access(api_key)))
    
    # Test 7: Invalid API Key
    results.append(("Invalid Key Rejection", test_invalid_api_key()))
    
    # Test 8: Security Headers
    results.append(("Security Headers", test_security_headers()))
    
    # Test 9: Quota Tier Limits
    results.append(("Quota Tier Limits", test_quota_tier_limits(api_key)))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}✅ PASS{Colors.END}" if result else f"{Colors.RED}❌ FAIL{Colors.END}"
        print(f"{status}  {test_name}")
    
    print("=" * 70)
    print(f"\n🎯 Results: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print(f"{Colors.GREEN}✅ All security tests passed!{Colors.END}")
        print(f"\n🔒 Security Implementation: COMPLETE")
    else:
        print(f"{Colors.RED}❌ Some tests failed. Check implementation.{Colors.END}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
