"""
Verify Google Cloud credentials and API access
Run: python verify_credentials.py
"""

import os
import sys
import re

print("=" * 60)
print("  GOOGLE CLOUD CREDENTIALS VERIFICATION")
print("=" * 60)
print()

# Manually parse .env file to avoid any caching issues
env_path = os.path.join(os.path.dirname(__file__), '.env')
env_vars = {}

print(f"📂 Loading .env from: {env_path}")
print(f"   File exists: {os.path.exists(env_path)}")
print()

# Read and parse .env file manually
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip()

PROJECT_NAME = env_vars.get("PROJECT_NAME")
ACCESS_TOKEN = env_vars.get("ACCESS_TOKEN")

# Check if values are set
print("📋 Checking .env file...")
print()

if not PROJECT_NAME or PROJECT_NAME == "your-gcp-project-id":
    print("❌ PROJECT_NAME not configured")
    print("   Current value:", PROJECT_NAME or "Not set")
    print()
    sys.exit(1)
else:
    print(f"✅ PROJECT_NAME: {PROJECT_NAME}")

if not ACCESS_TOKEN or ACCESS_TOKEN == "your-access-token":
    print("❌ ACCESS_TOKEN not configured")
    print("   Current value:", ACCESS_TOKEN[:20] + "..." if ACCESS_TOKEN else "Not set")
    print()
    sys.exit(1)
else:
    print(f"✅ ACCESS_TOKEN: {ACCESS_TOKEN[:30]}... ({len(ACCESS_TOKEN)} chars)")

print()
print("=" * 60)
print("🔍 Testing Vertex AI API Access...")
print("=" * 60)
print()

# Test Vertex AI initialization
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    
    print("✅ Vertex AI package imported successfully")
    print()
    
    # Try different regions and model names
    regions = ['us-central1', 'us-east4', 'us-west1', 'us-west4']
    model_names = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
        'gemini-1.0-pro'
    ]
    
    success = False
    working_config = {}
    
    for region in regions:
        if success:
            break
            
        print(f"🔄 Trying region: {region}")
        
        try:
            vertexai.init(project=PROJECT_NAME, location=region)
            print(f"   ✅ Initialized in {region}")
            
            for model_name in model_names:
                try:
                    print(f"   🔄 Testing model: {model_name}...")
                    model = GenerativeModel(model_name)
                    
                    # Generate a simple test response
                    response = model.generate_content("Say 'Hello!' in one word.")
                    
                    if response and response.candidates:
                        result = response.candidates[0].content.parts[0].text.strip()
                        print(f"   ✅ Model {model_name} works! Response: '{result}'")
                        working_config = {
                            'region': region,
                            'model': model_name
                        }
                        success = True
                        break
                    
                except Exception as model_error:
                    print(f"   ❌ {model_name}: {str(model_error)[:80]}")
                    continue
            
        except Exception as region_error:
            print(f"   ❌ Region {region}: {str(region_error)[:80]}")
            continue
    
    if success:
        print()
        print("=" * 60)
        print("🎉 SUCCESS! All credentials are working!")
        print("=" * 60)
        print()
        print(f"✅ Working Configuration:")
        print(f"   Region: {working_config['region']}")
        print(f"   Model: {working_config['model']}")
        print()
        print("⚠️  IMPORTANT: Update your main.py to use:")
        print(f"   vertexai.init(project=PROJECT_NAME, location='{working_config['region']}')")
        print(f"   model = GenerativeModel('{working_config['model']}')")
        print()
        print("Your backend is ready to:")
        print("  ✅ Generate subtopics")
        print("  ✅ Create presentations")
        print("  ✅ Process images")
        print("  ✅ Generate AI content")
        print()
        print("Next steps:")
        print("  1. Run: python main.py")
        print("  2. Access: http://localhost:5000/api/health")
        print("  3. Test: python test_api.py")
        print()
    else:
        print()
        print("❌ No working model/region combination found")
        print("   This might indicate:")
        print("   1. APIs not fully propagated (wait 5 minutes)")
        print("   2. Project doesn't have Gemini access")
        print("   3. Need to request access at: https://makersuite.google.com/")
        print()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print()
    print("Missing package. Install with:")
    print("  pip install google-cloud-aiplatform")
    print()
    sys.exit(1)
    
except Exception as e:
    error_message = str(e)
    print(f"❌ API Test Failed: {error_message}")
    print()
    
    # Provide helpful error messages
    if "403" in error_message or "permission" in error_message.lower():
        print("🔧 Possible fixes:")
        print("  1. Enable Vertex AI API:")
        print("     gcloud services enable aiplatform.googleapis.com")
        print()
        print("  2. Check project permissions:")
        print("     https://console.cloud.google.com/iam-admin/iam")
        print()
        
    elif "401" in error_message or "unauthorized" in error_message.lower():
        print("🔧 Token expired or invalid. Generate a new one:")
        print("  1. Run: gcloud auth application-default login")
        print("  2. Run: gcloud auth application-default print-access-token")
        print("  3. Copy the new token to .env file")
        print()
        
    elif "404" in error_message or "not found" in error_message.lower():
        print("🔧 Project not found. Verify your project ID:")
        print("  1. Run: gcloud config get-value project")
        print("  2. Update PROJECT_NAME in .env file")
        print()
        
    elif "quota" in error_message.lower():
        print("🔧 API quota exceeded. Check your quota:")
        print("  https://console.cloud.google.com/iam-admin/quotas")
        print()
        
    else:
        print("🔧 General troubleshooting:")
        print("  1. Verify project ID is correct")
        print("  2. Check if Vertex AI API is enabled")
        print("  3. Regenerate access token")
        print("  4. Check billing is enabled for project")
        print()
    
    sys.exit(1)

print("=" * 60)
