"""
Test script for gamification system
Run with: python test_gamification.py
"""
import requests
import json

BASE_URL = "http://localhost:5000/api/gamification"
TEST_USER_ID = "test_user_123"

def test_user_progress():
    """Test getting user progress"""
    print("\n=== Testing User Progress ===")
    response = requests.get(f"{BASE_URL}/progress?user_id={TEST_USER_ID}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_record_topic():
    """Test recording topic completion"""
    print("\n=== Testing Topic Completion ===")
    response = requests.post(
        f"{BASE_URL}/progress/topic",
        headers={"X-User-ID": TEST_USER_ID, "Content-Type": "application/json"},
        json={"topic_id": "test_topic_1", "time_spent": 300}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_record_quiz():
    """Test recording quiz completion"""
    print("\n=== Testing Quiz Completion ===")
    response = requests.post(
        f"{BASE_URL}/progress/quiz",
        headers={"X-User-ID": TEST_USER_ID, "Content-Type": "application/json"},
        json={"quiz_id": "test_quiz_1", "score": 85, "time_taken": 180}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def test_achievements():
    """Test getting achievements"""
    print("\n=== Testing Achievements ===")
    response = requests.get(f"{BASE_URL}/achievements")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total achievements: {len(data.get('achievements', []))}")
    
    # Get user achievements
    response = requests.get(f"{BASE_URL}/achievements/user?user_id={TEST_USER_ID}")
    print(f"User achievements: {response.json()}")
    return response.json()

def test_skills():
    """Test getting skills"""
    print("\n=== Testing Skills ===")
    response = requests.get(f"{BASE_URL}/skills")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total skills: {len(data.get('skills', []))}")
    
    # Get user skills
    response = requests.get(f"{BASE_URL}/skills/user?user_id={TEST_USER_ID}")
    print(f"User skills: {response.json()}")
    return response.json()

def test_challenges():
    """Test getting challenges"""
    print("\n=== Testing Challenges ===")
    response = requests.get(f"{BASE_URL}/challenges")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Total challenges: {len(data.get('challenges', []))}")
    return response.json()

def test_leaderboard():
    """Test getting leaderboard"""
    print("\n=== Testing Leaderboard ===")
    response = requests.get(f"{BASE_URL}/leaderboard?limit=10")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Leaderboard entries: {len(data.get('leaderboard', []))}")
    return response.json()

def test_stats():
    """Test getting comprehensive stats"""
    print("\n=== Testing Stats ===")
    response = requests.get(f"{BASE_URL}/stats?user_id={TEST_USER_ID}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("GAMIFICATION SYSTEM TEST SUITE")
    print("=" * 60)
    
    try:
        # Test basic progress
        test_user_progress()
        
        # Test recording activities
        test_record_topic()
        test_record_quiz()
        
        # Test achievements
        test_achievements()
        
        # Test skills
        test_skills()
        
        # Test challenges
        test_challenges()
        
        # Test leaderboard
        test_leaderboard()
        
        # Test comprehensive stats
        test_stats()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to backend")
        print("Make sure the backend is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    run_all_tests()
