"""
Quick verification script to check if environment is set up correctly
Run: python verify_setup.py
"""

import sys
import os

print("=" * 60)
print("  KNOWALLEDGE BACKEND - ENVIRONMENT VERIFICATION")
print("=" * 60)
print()

# Check Python version
print("✓ Python Version:", sys.version.split()[0])
print()

# Check if we're in a virtual environment
in_venv = sys.prefix != sys.base_prefix
print(f"{'✓' if in_venv else '✗'} Virtual Environment:", "Active" if in_venv else "NOT Active")
if not in_venv:
    print("  ⚠️  Warning: Virtual environment not detected!")
print()

# Check required packages
required_packages = {
    'flask': 'Flask',
    'flask_cors': 'Flask-Cors',
    'dotenv': 'python-dotenv',
    'langchain_core': 'langchain-core',
    'langchain_google_vertexai': 'langchain-google-vertexai',
    'vertexai': 'google-cloud-aiplatform',
    'PIL': 'Pillow',
    'requests': 'requests'
}

print("Checking required packages:")
missing_packages = []
for module, package_name in required_packages.items():
    try:
        __import__(module)
        print(f"  ✓ {package_name}")
    except ImportError:
        print(f"  ✗ {package_name} - MISSING")
        missing_packages.append(package_name)
print()

# Check .env file
print("Checking configuration:")
if os.path.exists('.env'):
    print("  ✓ .env file exists")
    
    # Check if credentials are set
    from dotenv import load_dotenv
    load_dotenv()
    
    project_name = os.getenv('PROJECT_NAME')
    access_token = os.getenv('ACCESS_TOKEN')
    
    if project_name and project_name != 'your-gcp-project-id':
        print(f"  ✓ PROJECT_NAME configured: {project_name}")
    else:
        print("  ⚠️  PROJECT_NAME not configured")
    
    if access_token and access_token != 'your-access-token':
        print("  ✓ ACCESS_TOKEN configured (length: {} chars)".format(len(access_token)))
    else:
        print("  ⚠️  ACCESS_TOKEN not configured")
else:
    print("  ✗ .env file NOT found")
    print("    Run: copy .env.example .env")
print()

# Check uploads directory
print("Checking directories:")
if os.path.exists('uploads'):
    print("  ✓ uploads/ directory exists")
else:
    print("  ✗ uploads/ directory missing")
    print("    Creating now...")
    os.makedirs('uploads', exist_ok=True)
    print("  ✓ uploads/ directory created")
print()

# Check main.py
print("Checking application files:")
if os.path.exists('main.py'):
    print("  ✓ main.py found")
else:
    print("  ✗ main.py NOT found")
print()

# Summary
print("=" * 60)
if missing_packages:
    print("⚠️  SETUP INCOMPLETE")
    print()
    print("Missing packages:")
    for pkg in missing_packages:
        print(f"  - {pkg}")
    print()
    print("Install with: pip install -r requirements.txt")
elif not os.path.exists('.env'):
    print("⚠️  CONFIGURATION REQUIRED")
    print()
    print("Create .env file: copy .env.example .env")
    print("Then edit it with your GCP credentials")
elif os.getenv('PROJECT_NAME') == 'your-gcp-project-id':
    print("⚠️  CREDENTIALS REQUIRED")
    print()
    print("Edit .env file with your Google Cloud credentials:")
    print("  - PROJECT_NAME: Your GCP project ID")
    print("  - ACCESS_TOKEN: Your GCP access token")
    print()
    print("Get access token:")
    print("  gcloud auth application-default print-access-token")
else:
    print("✅ SETUP COMPLETE!")
    print()
    print("Your environment is ready to run!")
    print()
    print("Next steps:")
    print("  1. Start server: python main.py")
    print("  2. Test API: python test_api.py")
    print("  3. Access: http://localhost:5000/api/health")
print("=" * 60)
