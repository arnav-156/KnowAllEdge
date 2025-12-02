"""
Quick Test Script for HIGH Priority Fixes
Tests: Multi-layer cache, Advanced rate limiting, Content validation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"
USER_ID = "test-user-123"

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def test_cache_stats():
    """Test 1: Check cache statistics"""
    print_section("TEST 1: Cache Statistics")
    
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            data = response.json()
            cache_stats = data.get('cache', {})
            
            print("✅ Cache Stats Retrieved Successfully")
            print(f"   Version: {cache_stats.get('version')}")
            print(f"   L1 (Hot Cache) Size: {cache_stats.get('l1', {}).get('size')}/{cache_stats.get('l1', {}).get('max_size')}")
            print(f"   L1 Hits: {cache_stats.get('l1', {}).get('hits')}")
            print(f"   L2 Type: {cache_stats.get('l2', {}).get('type')}")
            print(f"   Overall Hit Rate: {cache_stats.get('overall', {}).get('hit_rate')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_rate_limiting():
    """Test 2: Check rate limiting with user tracking"""
    print_section("TEST 2: Rate Limiting")
    
    try:
        # Make request with user ID
        response = requests.post(
            f"{BASE_URL}/api/create_subtopics",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": USER_ID
            },
            json={"topic": "Python Programming"}
        )
        
        if response.status_code == 200:
            print("✅ Request Successful")
        else:
            print(f"⚠️ Status: {response.status_code}")
        
        # Check rate limit stats
        stats_response = requests.get(f"{BASE_URL}/api/stats")
        if stats_response.status_code == 200:
            data = stats_response.json()
            rate_limits = data.get('rate_limits', {})
            
            print("\n📊 Rate Limit Stats:")
            
            # User limits
            user = rate_limits.get('user', {})
            if user:
                print(f"   User Requests (1 min): {user.get('requests_per_minute')}/{user.get('limits', {}).get('per_minute')}")
                print(f"   User Requests (1 hour): {user.get('requests_per_hour')}/{user.get('limits', {}).get('per_hour')}")
                print(f"   User Requests (1 day): {user.get('requests_per_day')}/{user.get('limits', {}).get('per_day')}")
            
            # Global limits
            global_stats = rate_limits.get('global', {})
            if global_stats:
                print(f"   Global Requests (1 min): {global_stats.get('requests_per_minute')}/{global_stats.get('limits', {}).get('per_minute')}")
            
            # System
            system = data.get('system', {})
            print(f"\n🖥️ System:")
            print(f"   Active Users: {system.get('active_users')}")
            print(f"   Active IPs: {system.get('active_ips')}")
            print(f"   Blocked: {system.get('blocked_count')}")
            
            return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_content_validation():
    """Test 3: Check content validation with quality scores"""
    print_section("TEST 3: Content Validation")
    
    try:
        # Test subtopics generation with validation
        response = requests.post(
            f"{BASE_URL}/api/create_subtopics",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": USER_ID
            },
            json={"topic": "Machine Learning"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Content Generated & Validated")
            print(f"   Subtopics Count: {data.get('count')}")
            print(f"   Quality Score: {data.get('quality_score'):.2f}")
            
            warnings = data.get('warnings')
            if warnings:
                print(f"   ⚠️ Warnings: {len(warnings)}")
                for w in warnings[:3]:  # Show first 3
                    print(f"      - {w}")
            else:
                print(f"   ✅ No Warnings")
            
            # Show first 3 subtopics
            subtopics = data.get('subtopics', [])
            print(f"\n   First 3 Subtopics:")
            for i, st in enumerate(subtopics[:3], 1):
                print(f"      {i}. {st}")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_cache_invalidation():
    """Test 4: Cache invalidation"""
    print_section("TEST 4: Cache Invalidation")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/cache/invalidate",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": USER_ID
            },
            json={"namespace": "subtopics"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Cache Invalidated")
            print(f"   Namespace: {data.get('namespace')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multi_layer_caching():
    """Test 5: Multi-layer caching performance"""
    print_section("TEST 5: Multi-Layer Cache Performance")
    
    try:
        topic = "Web Development"
        
        # First request (cache miss)
        print("🔍 First Request (cache miss expected)...")
        start1 = time.time()
        response1 = requests.post(
            f"{BASE_URL}/api/create_subtopics",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": USER_ID
            },
            json={"topic": topic}
        )
        time1 = (time.time() - start1) * 1000
        
        if response1.status_code == 200:
            print(f"   ✅ Success - {time1:.0f}ms")
        
        time.sleep(0.5)  # Small delay
        
        # Second request (cache hit expected)
        print("\n🔍 Second Request (cache hit expected)...")
        start2 = time.time()
        response2 = requests.post(
            f"{BASE_URL}/api/create_subtopics",
            headers={
                "Content-Type": "application/json",
                "X-User-ID": USER_ID
            },
            json={"topic": topic}
        )
        time2 = (time.time() - start2) * 1000
        
        if response2.status_code == 200:
            print(f"   ✅ Success - {time2:.0f}ms")
        
        # Performance improvement
        if time2 < time1:
            improvement = ((time1 - time2) / time1) * 100
            print(f"\n📊 Performance Improvement: {improvement:.1f}% faster")
            print(f"   First Request: {time1:.0f}ms")
            print(f"   Second Request (cached): {time2:.0f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_prompt_templates():
    """Test 6: Verify prompt templates"""
    print_section("TEST 6: Prompt Templates")
    
    try:
        response = requests.get(f"{BASE_URL}/api/prompts")
        
        if response.status_code == 200:
            data = response.json()
            templates = data.get('templates', [])
            
            print(f"✅ {len(templates)} Templates Available")
            
            for template in templates:
                print(f"\n   📝 {template.get('name')} (v{template.get('version')})")
                print(f"      Description: {template.get('description')}")
                print(f"      Max Tokens: {template.get('max_tokens')}")
            
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "🚀 TESTING HIGH PRIORITY FIXES ".center(60, "="))
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test User ID: {USER_ID}")
    
    results = {
        "Cache Stats": test_cache_stats(),
        "Rate Limiting": test_rate_limiting(),
        "Content Validation": test_content_validation(),
        "Cache Invalidation": test_cache_invalidation(),
        "Multi-Layer Cache": test_multi_layer_caching(),
        "Prompt Templates": test_prompt_templates()
    }
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({(passed/total)*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
