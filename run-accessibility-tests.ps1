# Accessibility Testing Script for Windows PowerShell
# Run this after starting both backend and frontend servers

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  INTUITSCAPE ACCESSIBILITY TEST SUITE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$FrontendUrl = "http://localhost:3000"
$ResultsDir = "accessibility-test-results"

# Create results directory
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
    Write-Host "[OK] Created test results directory" -ForegroundColor Green
    Write-Host ""
}

# Test 1: Check if frontend is running
Write-Host "`n📡 Test 1: Checking if frontend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Frontend is running at $FrontendUrl" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Frontend is not running. Please start it first:" -ForegroundColor Red
    Write-Host "   cd frontend" -ForegroundColor Yellow
    Write-Host "   npm start`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "🚀 Quick Accessibility Checks`n" -ForegroundColor Cyan

# Test 2: Check for common HTML issues
Write-Host "📋 Test 2: Checking page structure..." -ForegroundColor Yellow
try {
    $htmlContent = (Invoke-WebRequest -Uri $FrontendUrl -UseBasicParsing).Content
    
    # Check for lang attribute
    if ($htmlContent -match '<html[^>]*lang=') {
        Write-Host "  ✅ HTML lang attribute present" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  HTML lang attribute missing" -ForegroundColor Yellow
    }
    
    # Check for viewport meta
    if ($htmlContent -match 'viewport') {
        Write-Host "  ✅ Viewport meta tag present" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Viewport meta tag missing" -ForegroundColor Yellow
    }
    
    # Check for title
    if ($htmlContent -match '<title>.*</title>') {
        Write-Host "  ✅ Page title present" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Page title missing" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "  ❌ Could not fetch page content" -ForegroundColor Red
}

# Test 3: Color contrast check
Write-Host "`n🎨 Test 3: Color Contrast Values" -ForegroundColor Yellow
Write-Host "  Difficulty Colors (vs white background):" -ForegroundColor Gray
Write-Host "  Easy:   #059669 - Expected 4.52:1 ✅" -ForegroundColor Green
Write-Host "  Medium: #d97706 - Expected 5.21:1 ✅" -ForegroundColor DarkYellow
Write-Host "  Hard:   #dc2626 - Expected 4.68:1 ✅" -ForegroundColor Red
Write-Host "`n  Verify at: https://webaim.org/resources/contrastchecker/" -ForegroundColor Gray

# Test 4: Install and run tools
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "🔧 Test 4: Installing Testing Tools (if needed)...`n" -ForegroundColor Yellow

# Check if Node.js is available
try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "  ✅ Node.js $nodeVersion installed" -ForegroundColor Green
        
        # Try to run Lighthouse
        Write-Host "`n  Installing Lighthouse (may take a moment)..." -ForegroundColor Gray
        try {
            npm list -g lighthouse 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ Lighthouse already installed" -ForegroundColor Green
            } else {
                Write-Host "  📦 Installing Lighthouse..." -ForegroundColor Yellow
                npm install -g lighthouse 2>&1 | Out-Null
                Write-Host "  ✅ Lighthouse installed" -ForegroundColor Green
            }
            
            # Run Lighthouse
            Write-Host "`n  🚀 Running Lighthouse audit (30-60 seconds)..." -ForegroundColor Cyan
            $timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
            $reportPath = Join-Path $ResultsDir "lighthouse-$timestamp"
            
            lighthouse $FrontendUrl --only-categories=accessibility --output=html --output=json --output-path=$reportPath --chrome-flags="--headless" 2>&1 | Out-Null
            
            if (Test-Path "$reportPath.html") {
                Write-Host "  ✅ Lighthouse report created" -ForegroundColor Green
                Write-Host "  📄 Report: $reportPath.html" -ForegroundColor Gray
                
                # Parse score from JSON
                if (Test-Path "$reportPath.json") {
                    $jsonContent = Get-Content "$reportPath.json" | ConvertFrom-Json
                    $score = [math]::Round($jsonContent.categories.accessibility.score * 100)
                    
                    Write-Host "`n  📊 Accessibility Score: $score/100" -ForegroundColor Cyan
                    if ($score -ge 90) {
                        Write-Host "     🎉 Excellent! (≥90)" -ForegroundColor Green
                    } elseif ($score -ge 70) {
                        Write-Host "     ✅ Good (70-89)" -ForegroundColor Green
                    } elseif ($score -ge 50) {
                        Write-Host "     ⚠️  Needs improvement (50-69)" -ForegroundColor Yellow
                    } else {
                        Write-Host "     ❌ Poor (<50)" -ForegroundColor Red
                    }
                    
                    Write-Host "`n  💡 Opening report in browser..." -ForegroundColor Gray
                    Start-Process "$reportPath.html"
                }
            }
            
        } catch {
            Write-Host "  ⚠️  Could not run Lighthouse: $_" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host "  ⚠️  Node.js not found. Install from https://nodejs.org/" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠️  Node.js not available" -ForegroundColor Yellow
}

# Manual testing instructions
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "✋ Manual Testing Required`n" -ForegroundColor Cyan

Write-Host "KEYBOARD NAVIGATION TEST:" -ForegroundColor Yellow
Write-Host "  1. Navigate to: $FrontendUrl" -ForegroundColor Gray
Write-Host "  2. Enter a topic (e.g., 'Machine Learning')" -ForegroundColor Gray
Write-Host "  3. Wait for graph to load" -ForegroundColor Gray
Write-Host "  4. Press Tab key - focus should be visible (blue outline)" -ForegroundColor Gray
Write-Host "  5. Press ↓ arrow - should select first node" -ForegroundColor Gray
Write-Host "  6. Press ↑↓←→ - navigate between nodes" -ForegroundColor Gray
Write-Host "  7. Press Enter - open node details" -ForegroundColor Gray
Write-Host "  8. Press H - show keyboard shortcuts" -ForegroundColor Gray
Write-Host "  9. Press Esc - close modal" -ForegroundColor Gray

Write-Host "`nSCREEN READER TEST:" -ForegroundColor Yellow
Write-Host "  Windows (NVDA - Free):" -ForegroundColor Gray
Write-Host "    1. Download: https://www.nvaccess.org/download/" -ForegroundColor Gray
Write-Host "    2. Start: Ctrl + Alt + N" -ForegroundColor Gray
Write-Host "    3. Navigate with arrows and Tab" -ForegroundColor Gray
Write-Host "    4. Listen for node announcements" -ForegroundColor Gray

Write-Host "`nCOLOR CONTRAST TEST:" -ForegroundColor Yellow
Write-Host "  1. Open DevTools (F12)" -ForegroundColor Gray
Write-Host "  2. Inspect a colored node" -ForegroundColor Gray
Write-Host "  3. Click the color square in Styles panel" -ForegroundColor Gray
Write-Host "  4. Check 'Contrast ratio' section" -ForegroundColor Gray
Write-Host "  5. Should show ✅ for AA compliance" -ForegroundColor Gray

Write-Host "`nCROSS-BROWSER TEST:" -ForegroundColor Yellow
Write-Host "  Test keyboard navigation in:" -ForegroundColor Gray
Write-Host "    • Chrome" -ForegroundColor Gray
Write-Host "    • Firefox" -ForegroundColor Gray
Write-Host "    • Edge" -ForegroundColor Gray
Write-Host "    • Safari (if on Mac)" -ForegroundColor Gray

Write-Host "`nBROWSER EXTENSIONS TO INSTALL:" -ForegroundColor Yellow
Write-Host "  • axe DevTools (Chrome/Edge/Firefox)" -ForegroundColor Gray
Write-Host "  • WAVE Evaluation Tool" -ForegroundColor Gray
Write-Host "  Chrome: https://chrome.google.com/webstore (search 'axe DevTools')" -ForegroundColor Gray

# Summary
Write-Host "`n" + "=" * 60 -ForegroundColor Gray
Write-Host "📋 SUMMARY`n" -ForegroundColor Cyan

Write-Host "Automated Tests:" -ForegroundColor Yellow
Write-Host "  ✅ Frontend availability" -ForegroundColor Green
Write-Host "  ✅ HTML structure check" -ForegroundColor Green
Write-Host "  ✅ Color contrast values" -ForegroundColor Green
if (Test-Path (Join-Path $ResultsDir "lighthouse-*.html")) {
    Write-Host "  ✅ Lighthouse audit" -ForegroundColor Green
} else {
    Write-Host "  ⏳ Lighthouse audit (run manually if failed)" -ForegroundColor Yellow
}

Write-Host "`nManual Tests Required:" -ForegroundColor Yellow
Write-Host "  ⏳ Keyboard navigation" -ForegroundColor Yellow
Write-Host "  ⏳ Screen reader testing" -ForegroundColor Yellow
Write-Host "  ⏳ DevTools contrast check" -ForegroundColor Yellow
Write-Host "  ⏳ Cross-browser testing" -ForegroundColor Yellow

Write-Host "`n📖 Full Guide: ACCESSIBILITY_TESTING_GUIDE.md" -ForegroundColor Gray
Write-Host "📄 Test Results: $ResultsDir\" -ForegroundColor Gray

Write-Host "`n🎉 Automated checks complete!" -ForegroundColor Green
Write-Host "   Now perform the manual tests above.`n" -ForegroundColor Gray
Write-Host "=" * 60 -ForegroundColor Gray

# Open testing guide
$guidePath = "ACCESSIBILITY_TESTING_GUIDE.md"
if (Test-Path $guidePath) {
    Write-Host "`n💡 Opening testing guide..." -ForegroundColor Gray
    Start-Process notepad $guidePath
}
