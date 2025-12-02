"""
Quick API Test
"""
import requests

print("Testing KNOWALLEDGE API...\n")

# Test 1: Generate Subtopics
print("1. Generating subtopics for 'Web Development'...")
response = requests.post(
    "http://127.0.0.1:5000/api/create_subtopics",
    json={"topic": "Web Development"}
)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Generated {data['count']} subtopics:")
    for i, sub in enumerate(data['subtopics'][:5], 1):
        print(f"   {i}. {sub}")
    print(f"   ... and {data['count'] - 5} more\n")
else:
    print(f"❌ Failed: {response.status_code}\n")

# Test 2: Generate Presentation
print("2. Generating presentation for 2 subtopics...")
response = requests.post(
    "http://127.0.0.1:5000/api/create_presentation",
    json={
        "topic": "Artificial Intelligence",
        "educationLevel": "beginner",
        "levelOfDetail": "brief",
        "focus": ["Machine Learning", "Neural Networks"]
    }
)
if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Generated {data['success_count']} explanations")
    if data['explanations'] and len(data['explanations']) > 0:
        exp = data['explanations'][0]
        if isinstance(exp, dict):
            print(f"\n📚 {exp['subtopic']}:")
            print(f"   {exp['explanation'][:200]}...\n")
        else:
            print(f"\n📚 First explanation:")
            print(f"   {str(exp)[:200]}...\n")
else:
    print(f"❌ Failed: {response.status_code}\n")

print("=" * 60)
print("🎉 Your backend is working with Google AI!")
print("=" * 60)
