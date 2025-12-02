# Production startup script for KnowAllEdge API (Windows)
# CRITICAL FIX: Proper production server startup for Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "🚀 KnowAllEdge API - Production Startup" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

# Check if virtual environment exists
if (-not (Test-Path "venv") -and -not (Test-Path ".venv")) {
    Write-Host "⚠️  No virtual environment found. Creating one..." -ForegroundColor Yellow
    python -m venv venv
    .\venv\Scripts\Activate.ps1
} else {
    if (Test-Path "venv") {
        .\venv\Scripts\Activate.ps1
    } else {
        .\.venv\Scripts\Activate.ps1
    }
}

Write-Host "✅ Virtual environment activated" -ForegroundColor Green

# Install/upgrade production dependencies
Write-Host "📦 Installing production dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn gevent

Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Load environment variables from .env
if (Test-Path ".env") {
    Write-Host "✅ .env file found" -ForegroundColor Green
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
} else {
    Write-Host "⚠️  No .env file found. Using environment variables..." -ForegroundColor Yellow
}

# Initialize database
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
python -c "from database import init_database; init_database()"

Write-Host "✅ Database initialized" -ForegroundColor Green

# Set default environment variables if not set
if (-not $env:PORT) { $env:PORT = "5000" }
if (-not $env:GUNICORN_WORKERS) { $env:GUNICORN_WORKERS = "4" }
if (-not $env:GUNICORN_TIMEOUT) { $env:GUNICORN_TIMEOUT = "120" }
if (-not $env:LOG_LEVEL) { $env:LOG_LEVEL = "info" }

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "📊 Configuration:" -ForegroundColor Green
Write-Host "   Port: $env:PORT"
Write-Host "   Workers: $env:GUNICORN_WORKERS"
Write-Host "   Timeout: $($env:GUNICORN_TIMEOUT)s"
Write-Host "   Log Level: $env:LOG_LEVEL"
Write-Host "==========================================" -ForegroundColor Cyan

# Start gunicorn
Write-Host "🚀 Starting Gunicorn..." -ForegroundColor Green
gunicorn `
    --config gunicorn_config.py `
    --bind "0.0.0.0:$env:PORT" `
    --workers $env:GUNICORN_WORKERS `
    --timeout $env:GUNICORN_TIMEOUT `
    --log-level $env:LOG_LEVEL `
    wsgi:application
