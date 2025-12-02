# Quick Start: Run Gemini Translation

## Get API Key
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host "  Step 1: Get Your Free Gemini API Key" -ForegroundColor Yellow
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host ""
Write-Host "Visit: https://makersuite.google.com/app/apikey" -ForegroundColor Green
Write-Host "Click 'Create API Key' and copy it" -ForegroundColor Green
Write-Host ""
Write-Host "Then set it with:" -ForegroundColor White
Write-Host '$env:GEMINI_API_KEY="your-api-key-here"' -ForegroundColor Yellow
Write-Host ""

# Check if API key is set
if (-not $env:GEMINI_API_KEY) {
    Write-Host "ERROR: GEMINI_API_KEY not set!" -ForegroundColor Red
    Write-Host "Set it with: " -NoNewline
    Write-Host '$env:GEMINI_API_KEY="your-key"' -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ API Key found!" -ForegroundColor Green
Write-Host ""

## Install dependencies
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host "  Step 2: Installing Dependencies" -ForegroundColor Yellow
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host ""

python -m pip install -r translation-requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Dependencies installed!" -ForegroundColor Green
Write-Host ""

## Run translation
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host "  Step 3: Running Translation (5-10 minutes)" -ForegroundColor Yellow
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host ""

python translate_with_gemini.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Translation failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host "  ✅ TRANSLATION COMPLETE!" -ForegroundColor Green
Write-Host "==================================================="  -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. cd frontend" -ForegroundColor White
Write-Host "2. npm run dev" -ForegroundColor White
Write-Host "3. Test language selector in navbar!" -ForegroundColor White
Write-Host ""
Write-Host "🎉 Your app now speaks 6 languages!" -ForegroundColor Green
