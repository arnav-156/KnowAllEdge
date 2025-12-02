"""
Test script for KNOWALLEDGE API endpoints
Run with: python test_api.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health check endpoint"""
    print("\n🧪 Testing Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200

def test_create_subtopics():
    """Test subtopics generation"""
    print("\n🧪 Testing Create Subtopics...")
    data = {"topic": "Python Programming"}
    response = requests.post(f"{BASE_URL}/create_subtopics", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Generated {result.get('count', 0)} subtopics")
    print(f"First 3: {result.get('subtopics', [])[:3]}")
    assert response.status_code == 200
    assert 'subtopics' in result
    return result['subtopics'][:2]  # Return first 2 for next test

def test_create_presentation(subtopics):
    """Test presentation generation"""
    print("\n🧪 Testing Create Presentation...")
    data = {
        "topic": "Python Programming",
        "educationLevel": "undergradLevel",
        "levelOfDetail": "mediumDetail",
        "focus": subtopics
    }
    response = requests.post(f"{BASE_URL}/create_presentation", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success_count', 0)}/{len(subtopics)}")
    print(f"First explanation (100 chars): {result.get('explanations', [''])[0][:100]}...")
    assert response.status_code == 200

def test_image2topic():
    """Test image to topic extraction (requires image file)"""
    print("\n🧪 Testing Image to Topic...")
    print("⚠️  Skipped: Requires actual image file")
    # Uncomment and provide image path to test:
    # with open('test_image.jpg', 'rb') as f:
    #     files = {'image': f}
    #     response = requests.post(f"{BASE_URL}/image2topic", files=files)
    #     print(f"Status: {response.status_code}")
    #     print(f"Response: {response.json()}")

def test_metrics():
    """Test metrics endpoint"""
    print("\n🧪 Testing Metrics...")
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200

def test_api_docs():
    """Test API documentation"""
    print("\n🧪 Testing API Documentation...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {response.status_code}")
    docs = response.json()
    print(f"API Version: {docs.get('info', {}).get('version', 'N/A')}")
    print(f"Endpoints: {len(docs.get('paths', {}))}")
    assert response.status_code == 200

def test_caching():
    """Test caching functionality"""
    print("\n🧪 Testing Caching...")
    data = {"topic": "Caching Test Topic"}
    
    # First request
    start = time.time()
    response1 = requests.post(f"{BASE_URL}/create_subtopics", json=data)
    time1 = time.time() - start
    
    # Second request (should be cached)
    start = time.time()
    response2 = requests.post(f"{BASE_URL}/create_subtopics", json=data)
    time2 = time.time() - start
    
    print(f"First request: {time1:.2f}s")
    print(f"Second request (cached): {time2:.2f}s")
    print(f"Speed improvement: {time1/time2:.1f}x faster")
    
    assert response1.json() == response2.json()
    assert time2 < time1

def test_input_validation():
    """Test input validation"""
    print("\n🧪 Testing Input Validation...")
    
    # Missing field
    response = requests.post(f"{BASE_URL}/create_subtopics", json={})
    print(f"Missing field: {response.status_code} - {response.json().get('error')}")
    assert response.status_code == 400
    
    # Invalid characters
    response = requests.post(f"{BASE_URL}/create_subtopics", json={"topic": "<script>alert('xss')</script>"})
    print(f"Invalid chars: {response.status_code} - {response.json().get('error')}")
    assert response.status_code == 400
    
    # Too long
    response = requests.post(f"{BASE_URL}/create_subtopics", json={"topic": "A" * 300})
    print(f"Too long: {response.status_code} - {response.json().get('error')}")
    assert response.status_code == 400
    
    print("✅ All validation tests passed!")

def test_rate_limiting():
    """Test rate limiting (makes many requests)"""
    print("\n🧪 Testing Rate Limiting...")
    print("⚠️  Skipped: Would make too many requests")
    # Uncomment to test (will hit rate limits):
    # for i in range(60):
    #     response = requests.get(f"{BASE_URL}/health")
    #     if response.status_code == 429:
    #         print(f"Rate limit hit after {i} requests")
    #         break

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🚀 KNOWALLEDGE API TEST SUITE")
    print("=" * 60)
    
    try:
        test_health()
        subtopics = test_create_subtopics()
        test_create_presentation(subtopics)
        test_image2topic()
        test_metrics()
        test_api_docs()
        test_caching()
        test_input_validation()
        test_rate_limiting()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API. Is the server running?")
        print("Start server with: python main.py")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    run_all_tests()
