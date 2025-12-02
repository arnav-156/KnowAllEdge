"""
WSGI entry point for production servers
CRITICAL FIX: Production WSGI application entry point

Usage:
    gunicorn --config gunicorn_config.py wsgi:application
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
"""
import os
import sys

# Ensure the backend directory is in the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application
from main import app

# This is what gunicorn/uwsgi will import
application = app

# For direct execution (testing)
if __name__ == "__main__":
    print("=" * 60)
    print("⚠️  WARNING: Running with Flask development server")
    print("   For production, use: gunicorn wsgi:application")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
