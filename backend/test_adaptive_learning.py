"""
Test script for KNOWALLEDGE Adaptive Learning API endpoints
Run with: python test_adaptive_learning.py
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_quiz_generation():
    """Test quiz generation endpoint"""
    print("\n🧪 Testing Quiz Generation...")
    data = {
        "topic": "Python Programming",
        "subtopic": "Variables",
        "education": "beginner",
        "count": 2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/quiz/generate", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Generated {len(result)} questions")
            if len(result) > 0:
                print(f"First question: {result[0].get('question')}")
        elif response.status_code == 401:
            print("⚠️ Auth required. Skipping actual test logic.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

def test_quiz_submission():
    """Test quiz submission endpoint"""
    print("\n🧪 Testing Quiz Submission...")
    data = {
        "topic": "Python Programming",
        "subtopic": "Variables",
        "score": 2,
        "total": 2,
        "difficulty": "beginner"
    }
    try:
        response = requests.post(f"{BASE_URL}/quiz/submit", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Mastery Level: {result.get('mastery_level')}")
        elif response.status_code == 401:
            print("⚠️ Auth required.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

def test_progress():
    """Test progress endpoint"""
    print("\n🧪 Testing Progress Tracking...")
    try:
        response = requests.get(f"{BASE_URL}/progress?topic=Python Programming")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Progress entries: {len(result)}")
        elif response.status_code == 401:
            print("⚠️ Auth required.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

def test_recommendations():
    """Test recommendations endpoint"""
    print("\n🧪 Testing Recommendations...")
    data = {"topic": "Python Programming"}
    try:
        response = requests.post(f"{BASE_URL}/recommendations", json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Recommendations: {len(result)}")
            if len(result) > 0:
                print(f"First recommendation: {result[0].get('subtopic')}")
        elif response.status_code == 401:
            print("⚠️ Auth required.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 ADAPTIVE LEARNING API TEST SUITE")
    print("=" * 60)
    try:
        test_quiz_generation()
        test_quiz_submission()
        test_progress()
        test_recommendations()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API. Is the server running?")
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
