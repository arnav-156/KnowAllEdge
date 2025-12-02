#!/usr/bin/env python3
"""
Check available Gemini models
"""

import os
import google.generativeai as genai

# Get API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyCOzWhDajjs7Fv8K6PzWOvSYr65NxqRnOE')

print(f"Using API key: {GEMINI_API_KEY[:20]}...")
print()

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

print("="*60)
print("Available Gemini Models:")
print("="*60)

try:
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description[:100]}...")
            print()
except Exception as e:
    print(f"❌ Error listing models: {e}")
    print("\nThis might mean:")
    print("1. Your API key is invalid or expired")
    print("2. You need to enable the Gemini API in Google Cloud Console")
    print("3. There's a temporary API issue")
    print("\nGet a new API key from: https://makersuite.google.com/app/apikey")
