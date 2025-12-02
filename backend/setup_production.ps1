# Quick Setup Script for Final Production Integration
# Run this in PowerShell from the backend directory

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IntuitScape Backend - Production Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Python
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Step 2: Install dependencies
Write-Host ""
Write-Host "[2/6] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

try {
    python -m pip install -r ../requirements.txt --quiet
    Write-Host "  ✓ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    Write-Host "  Try manually: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Step 3: Check Redis (optional but recommended)
Write-Host ""
Write-Host "[3/6] Checking Redis installation..." -ForegroundColor Yellow
$redisRunning = $false
try {
    $redisTest = redis-cli ping 2>&1
    if ($redisTest -eq "PONG") {
        $redisRunning = $true
        Write-Host "  ✓ Redis is running" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Redis not found (optional)" -ForegroundColor Yellow
    Write-Host "    Redis enables distributed caching" -ForegroundColor Gray
    Write-Host "    Download: https://github.com/microsoftarchive/redis/releases" -ForegroundColor Gray
}

# Step 4: Check environment variables
Write-Host ""
Write-Host "[4/6] Checking environment configuration..." -ForegroundColor Yellow

$envFile = ".env"
if (Test-Path $envFile) {
    Write-Host "  ✓ .env file found" -ForegroundColor Green
    
    # Check for required keys
    $envContent = Get-Content $envFile
    $hasGeminiKey = $envContent | Where-Object { $_ -like "GEMINI_API_KEY=*" -and $_ -notlike "GEMINI_API_KEY=your_*" }
    
    if ($hasGeminiKey) {
        Write-Host "  ✓ GEMINI_API_KEY is configured" -ForegroundColor Green
    } else {
        Write-Host "  ✗ GEMINI_API_KEY not configured in .env" -ForegroundColor Red
        Write-Host "    Please add your API key to .env file" -ForegroundColor Yellow
        Write-Host "    Get your key from: https://makersuite.google.com/app/apikey" -ForegroundColor Gray
    }
} else {
    Write-Host "  ⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "    Creating template .env file..." -ForegroundColor Gray
    
    $envTemplate = @"
# Google Gemini API Configuration
GEMINI_API_KEY=your_api_key_here

# Redis Configuration (optional)
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true

# Security
SECRET_KEY=$(New-Guid)
"@
    Set-Content -Path $envFile -Value $envTemplate
    Write-Host "  ✓ Created .env template - please configure API key" -ForegroundColor Green
}

# Step 5: Verify modules
Write-Host ""
Write-Host "[5/6] Verifying production modules..." -ForegroundColor Yellow

$modules = @(
    "quota_tracker.py",
    "cache_strategy.py",
    "prometheus_metrics.py",
    "redis_cache.py",
    "circuit_breaker.py",
    "content_validator.py",
    "advanced_rate_limiter.py",
    "multi_layer_cache.py"
)

$allModulesPresent = $true
foreach ($module in $modules) {
    if (Test-Path $module) {
        Write-Host "  ✓ $module" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $module (missing)" -ForegroundColor Red
        $allModulesPresent = $false
    }
}

if ($allModulesPresent) {
    Write-Host ""
    Write-Host "  ✓ All production modules present" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  ⚠ Some modules missing - app will run with graceful fallback" -ForegroundColor Yellow
}

# Step 6: Summary
Write-Host ""
Write-Host "[6/6] Setup Summary" -ForegroundColor Yellow
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Quota Tracking:       " -NoNewline
if (Test-Path "quota_tracker.py") {
    Write-Host "✓ Available" -ForegroundColor Green
} else {
    Write-Host "✗ Not available" -ForegroundColor Red
}

Write-Host "  Redis Caching:        " -NoNewline
if ($redisRunning) {
    Write-Host "✓ Running" -ForegroundColor Green
} else {
    Write-Host "⚠ Not running (optional)" -ForegroundColor Yellow
}

Write-Host "  Prometheus Metrics:   " -NoNewline
if (Test-Path "prometheus_metrics.py") {
    Write-Host "✓ Available" -ForegroundColor Green
} else {
    Write-Host "✗ Not available" -ForegroundColor Red
}

Write-Host "  Gemini API Key:       " -NoNewline
if ($hasGeminiKey) {
    Write-Host "✓ Configured" -ForegroundColor Green
} else {
    Write-Host "✗ Not configured" -ForegroundColor Red
}

Write-Host ""
Write-Host "  ========================================" -ForegroundColor Cyan
Write-Host ""

# Final instructions
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""

if (-not $hasGeminiKey) {
    Write-Host "  1. Configure your GEMINI_API_KEY in .env file" -ForegroundColor Yellow
    Write-Host "     Get your key from: https://makersuite.google.com/app/apikey" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "  2. Start the backend server:" -ForegroundColor Yellow
Write-Host "     python main.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "  3. Verify the server is running:" -ForegroundColor Yellow
Write-Host "     curl http://localhost:5000/api/health" -ForegroundColor Cyan
Write-Host ""

Write-Host "  4. Check production features:" -ForegroundColor Yellow
Write-Host "     curl http://localhost:5000/api/ready" -ForegroundColor Cyan
Write-Host "     curl http://localhost:5000/api/quota/stats" -ForegroundColor Cyan
Write-Host "     curl http://localhost:5000/metrics" -ForegroundColor Cyan
Write-Host ""

Write-Host "  5. Run integration tests:" -ForegroundColor Yellow
Write-Host "     python test_quota_integration.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "For more information, see:" -ForegroundColor Gray
Write-Host "  - FINAL_INTEGRATION_COMPLETE.md" -ForegroundColor Gray
Write-Host "  - QUOTA_INTEGRATION_QUICKSTART.md" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup complete! 🎉" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
