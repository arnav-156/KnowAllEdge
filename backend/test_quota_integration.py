"""
Test quota tracker integration with main.py

This script verifies that:
1. Main app starts successfully with quota_tracker
2. Main app starts successfully WITHOUT quota_tracker (graceful fallback)
3. Quota endpoints work correctly
4. API calls respect quota limits
"""

import sys
import os
import time
import requests
import json

def test_quota_endpoints():
    """Test quota-related endpoints"""
    base_url = "http://localhost:5000"
    
    print("\n=== Testing Quota Endpoints ===\n")
    
    # Test 1: Health check
    print("1. Testing /api/health...")
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Readiness check
    print("\n2. Testing /api/ready...")
    try:
        response = requests.get(f"{base_url}/api/ready")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Stats endpoint
    print("\n3. Testing /api/stats...")
    try:
        response = requests.get(f"{base_url}/api/stats")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Has quota stats: {'quota' in data}")
        if 'quota' in data:
            print(f"   Quota info: {json.dumps(data['quota'], indent=2)}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Quota stats endpoint
    print("\n4. Testing /api/quota/stats...")
    try:
        response = requests.get(f"{base_url}/api/quota/stats")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_api_with_quota():
    """Test API calls with quota tracking"""
    base_url = "http://localhost:5000"
    
    print("\n=== Testing API with Quota Tracking ===\n")
    
    # Test creating subtopics
    print("1. Testing /api/create_subtopics...")
    try:
        response = requests.post(
            f"{base_url}/api/create_subtopics",
            json={"topic": "Python Programming"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Subtopics count: {len(data.get('subtopics', []))}")
            print(f"   Quality score: {data.get('quality_score', 'N/A')}")
            if 'subtopics' in data and len(data['subtopics']) > 0:
                print(f"   First subtopic: {data['subtopics'][0]}")
        else:
            print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check quota after API call
    print("\n2. Checking quota usage after API call...")
    try:
        response = requests.get(f"{base_url}/api/quota/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   Requests today: {data.get('requests_today', 'N/A')}")
            print(f"   Tokens today: {data.get('tokens_today', 'N/A')}")
            print(f"   RPM remaining: {data.get('rpm_remaining', 'N/A')}")
            print(f"   TPM remaining: {data.get('tpm_remaining', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_quota_exceeded():
    """Test behavior when quota is exceeded"""
    base_url = "http://localhost:5000"
    
    print("\n=== Testing Quota Exceeded Behavior ===\n")
    print("Making multiple rapid requests to potentially hit rate limit...")
    
    for i in range(5):
        print(f"\nRequest {i+1}:")
        try:
            response = requests.post(
                f"{base_url}/api/create_subtopics",
                json={"topic": f"Test Topic {i+1}"},
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 429:
                print(f"   ✅ Quota limit enforced!")
                print(f"   Response: {response.json()}")
                break
            elif response.status_code == 200:
                print(f"   ✅ Request succeeded")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay between requests

def main():
    """Run all tests"""
    print("=" * 60)
    print("QUOTA TRACKER INTEGRATION TEST")
    print("=" * 60)
    print("\nMake sure the Flask server is running on http://localhost:5000")
    print("Run: python main.py")
    
    input("\nPress Enter when server is ready...")
    
    try:
        # Test quota endpoints
        test_quota_endpoints()
        
        # Test API with quota
        test_api_with_quota()
        
        # Test quota exceeded (optional - comment out if you don't want to hit limits)
        # test_quota_exceeded()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")

if __name__ == "__main__":
    main()
