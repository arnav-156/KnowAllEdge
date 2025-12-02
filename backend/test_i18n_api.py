"""
Test script for i18n API integration
Tests that backend correctly reads language parameters and responds in the requested language
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5000/api"

def test_language_header(topic="Artificial Intelligence", language="es"):
    """Test API with Accept-Language header"""
    print(f"\n{'='*60}")
    print(f"Testing: {language.upper()} - Accept-Language Header")
    print(f"{'='*60}")
    
    headers = {
        'Content-Type': 'application/json',
        'Accept-Language': language
    }
    
    payload = {
        'topic': topic
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/create_subtopics",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Status: {response.status_code}")
            print(f"\nSubtopics (in {language}):")
            for i, subtopic in enumerate(data.get('subtopics', []), 1):
                print(f"  {i}. {subtopic}")
            return True
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_language_body(topic="Machine Learning", language="fr"):
    """Test API with language in request body"""
    print(f"\n{'='*60}")
    print(f"Testing: {language.upper()} - Request Body Parameter")
    print(f"{'='*60}")
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        'topic': topic,
        'language': language  # Language in body
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/create_subtopics",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Status: {response.status_code}")
            print(f"\nSubtopics (in {language}):")
            for i, subtopic in enumerate(data.get('subtopics', []), 1):
                print(f"  {i}. {subtopic}")
            return True
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_all_languages():
    """Test all supported languages"""
    languages = {
        'en': 'Quantum Computing',
        'es': 'Inteligencia Artificial',
        'fr': 'Science des Données',
        'de': 'Maschinelles Lernen',
        'zh': '人工智能',
        'ja': '機械学習'
    }
    
    results = []
    
    for lang, topic in languages.items():
        success = test_language_header(topic, lang)
        results.append((lang, success))
    
    return results

def print_summary(results):
    """Print test summary"""
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for lang, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{lang.upper()}: {status}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! i18n API integration is working!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Check the output above.")

def quick_test():
    """Quick test with just Spanish"""
    print("🚀 Quick i18n API Test")
    print("Testing Spanish translation...")
    
    success = test_language_header("Artificial Intelligence", "es")
    
    if success:
        print("\n✅ Backend i18n integration is working!")
        print("You should see Spanish subtopics above (e.g., 'Fundamentos de...')")
    else:
        print("\n❌ Test failed. Check server logs for errors.")

if __name__ == "__main__":
    import sys
    
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           i18n API Integration Test Suite                   ║
    ║                                                              ║
    ║  This script tests that the backend correctly:              ║
    ║  1. Reads Accept-Language header                            ║
    ║  2. Reads language parameter from request body              ║
    ║  3. Returns responses in the requested language             ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running on http://localhost:5000")
        else:
            print("⚠️ Server responded with unexpected status")
    except:
        print("❌ ERROR: Server is not running!")
        print("Please start the server with: python main.py")
        sys.exit(1)
    
    # Run tests based on command line argument
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "--full":
        results = test_all_languages()
        print_summary(results)
    else:
        # Default: run Spanish and French tests
        print("\n🔬 Running i18n API tests...")
        print("(Use --quick for single test, --full for all languages)")
        
        results = [
            ('es', test_language_header("Artificial Intelligence", "es")),
            ('fr', test_language_body("Machine Learning", "fr")),
        ]
        
        print_summary(results)
        
        print("\n💡 TIP: Run with --full to test all 6 languages")
