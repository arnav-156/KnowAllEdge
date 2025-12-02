"""
Test Google AI Studio API Key with Gemini
"""

import os
import google.generativeai as genai

print("=" * 60)
print("  TESTING GOOGLE AI STUDIO API (GEMINI)")
print("=" * 60)
print()

# Manually parse .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
env_vars = {}

with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()

GOOGLE_API_KEY = env_vars.get("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    print("❌ GOOGLE_API_KEY not found in .env file")
    exit(1)

print(f"✅ API Key found: {GOOGLE_API_KEY[:20]}...")
print()

# Configure the API
genai.configure(api_key=GOOGLE_API_KEY)

# Test 1: List available models
print("🔍 Listing available Gemini models...")
try:
    models = genai.list_models()
    gemini_models = [m for m in models if 'gemini' in m.name.lower()]
    
    if gemini_models:
        print(f"✅ Found {len(gemini_models)} Gemini models:")
        for model in gemini_models:
            print(f"   - {model.name}")
    else:
        print("⚠️  No Gemini models found")
except Exception as e:
    print(f"❌ Error listing models: {str(e)}")
    exit(1)

print()

# Test 2: Generate content with Gemini Flash (new model)
print("🔍 Testing Gemini 2.0 Flash text generation...")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say 'Hello from Gemini!' in one sentence.")
    
    print(f"✅ Gemini Flash Response:")
    print(f"   {response.text}")
    print()
    
except Exception as e:
    print(f"❌ Error with Gemini Flash: {str(e)}")
    exit(1)

# Test 3: Test with a real question
print("🔍 Testing with educational content generation...")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = "Generate 3 subtopics for learning Python programming (just list the topics, no explanations)"
    response = model.generate_content(prompt)
    
    print(f"✅ Educational Content Test:")
    print(f"   {response.text}")
    print()
    
except Exception as e:
    print(f"❌ Error with educational test: {str(e)}")
    exit(1)

print("=" * 60)
print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("🎉 Your Google AI API is working!")
print("📝 You can now use Gemini models in your backend")
print()
print("Next steps:")
print("  1. Update main.py to use google-generativeai instead of Vertex AI")
print("  2. Start the Flask server: python main.py")
print("  3. Test the API endpoints")
