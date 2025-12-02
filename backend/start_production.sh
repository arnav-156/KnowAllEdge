#!/bin/bash
# Production startup script for KnowAllEdge API
# CRITICAL FIX: Proper production server startup

set -e  # Exit on error

echo "=========================================="
echo "🚀 KnowAllEdge API - Production Startup"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
else
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

echo "✅ Virtual environment activated"

# Install/upgrade production dependencies
echo "📦 Installing production dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn gevent  # Production server

echo "✅ Dependencies installed"

# Check environment variables
if [ -f ".env" ]; then
    echo "✅ .env file found"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠️  No .env file found. Using environment variables..."
fi

# Initialize database
echo "🗄️  Initializing database..."
python -c "from database import init_database; init_database()"

echo "✅ Database initialized"

# Set default environment variables if not set
export PORT=${PORT:-5000}
export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-120}
export LOG_LEVEL=${LOG_LEVEL:-info}

echo "=========================================="
echo "📊 Configuration:"
echo "   Port: $PORT"
echo "   Workers: $GUNICORN_WORKERS"
echo "   Timeout: ${GUNICORN_TIMEOUT}s"
echo "   Log Level: $LOG_LEVEL"
echo "=========================================="

# Start gunicorn
echo "🚀 Starting Gunicorn..."
exec gunicorn \
    --config gunicorn_config.py \
    --bind 0.0.0.0:$PORT \
    --workers $GUNICORN_WORKERS \
    --timeout $GUNICORN_TIMEOUT \
    --log-level $LOG_LEVEL \
    wsgi:application
