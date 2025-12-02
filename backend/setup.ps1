# Intuitscape Backend Setup Script for PowerShell
# Run this script to set up your development environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Intuitscape Backend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment already exists" -ForegroundColor Green
} else {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install requirements
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
Write-Host "This may take a few minutes..." -ForegroundColor Gray
pip install -r requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ All dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Error installing dependencies" -ForegroundColor Red
    exit 1
}

# Check if .env file exists
Write-Host ""
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: Edit .env file with your Google Cloud credentials!" -ForegroundColor Red
    Write-Host "   Required values:" -ForegroundColor Yellow
    Write-Host "   - PROJECT_NAME: Your GCP project ID" -ForegroundColor Gray
    Write-Host "   - ACCESS_TOKEN: Your GCP access token" -ForegroundColor Gray
}

# Create uploads directory
Write-Host ""
if (Test-Path "uploads") {
    Write-Host "✓ Uploads directory exists" -ForegroundColor Green
} else {
    Write-Host "Creating uploads directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "✓ Uploads directory created" -ForegroundColor Green
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your GCP credentials" -ForegroundColor White
Write-Host "   notepad .env" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run the test suite:" -ForegroundColor White
Write-Host "   python test_api.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start the development server:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Access the API:" -ForegroundColor White
Write-Host "   http://localhost:5000/api/health" -ForegroundColor Gray
Write-Host "   http://localhost:5000/api/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Documentation available in:" -ForegroundColor Yellow
Write-Host "  - README.md (API documentation)" -ForegroundColor Gray
Write-Host "  - DEPLOYMENT.md (deployment guide)" -ForegroundColor Gray
Write-Host "  - IMPROVEMENTS.md (changes log)" -ForegroundColor Gray
Write-Host ""
