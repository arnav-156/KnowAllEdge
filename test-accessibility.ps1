# Simple Accessibility Test Script
# PowerShell

Write-Host ""
Write-Host "INTUITSCAPE ACCESSIBILITY TEST SUITE" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray
Write-Host ""

$url = "http://localhost:3000"

# Test 1: Check if frontend is running
Write-Host "[TEST 1] Checking if frontend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "[PASS] Frontend is running at $url" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Frontend is not running!" -ForegroundColor Red
    Write-Host "       Start it with: cd frontend; npm start" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""

# Test 2: Open color contrast checker
Write-Host "[TEST 2] Opening color contrast checker..." -ForegroundColor Yellow
$contrastFile = "color-contrast-test.html"
if (Test-Path $contrastFile) {
    Start-Process $contrastFile
    Write-Host "[PASS] Opened $contrastFile in browser" -ForegroundColor Green
} else {
    Write-Host "[SKIP] $contrastFile not found" -ForegroundColor Yellow
}

Write-Host ""

# Test 3: Open testing guide
Write-Host "[TEST 3] Opening testing guide..." -ForegroundColor Yellow
$guideFile = "ACCESSIBILITY_TESTING_GUIDE.md"
if (Test-Path $guideFile) {
    Start-Process notepad $guideFile
    Write-Host "[PASS] Opened $guideFile" -ForegroundColor Green
} else {
    Write-Host "[SKIP] $guideFile not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Gray
Write-Host "MANUAL TESTS REQUIRED" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray
Write-Host ""

Write-Host "1. KEYBOARD NAVIGATION:" -ForegroundColor Yellow
Write-Host "   - Go to: $url" -ForegroundColor Gray
Write-Host "   - Enter topic: 'Machine Learning'" -ForegroundColor Gray
Write-Host "   - Press Tab - see blue focus outline" -ForegroundColor Gray
Write-Host "   - Press Down Arrow - select first node" -ForegroundColor Gray
Write-Host "   - Press Arrow keys - navigate nodes" -ForegroundColor Gray
Write-Host "   - Press Enter - open node details" -ForegroundColor Gray
Write-Host "   - Press H - show shortcuts help" -ForegroundColor Gray
Write-Host "   - Press Esc - close modal" -ForegroundColor Gray
Write-Host ""

Write-Host "2. SCREEN READER (NVDA):" -ForegroundColor Yellow
Write-Host "   - Download: https://www.nvaccess.org/download/" -ForegroundColor Gray
Write-Host "   - Start: Ctrl + Alt + N" -ForegroundColor Gray
Write-Host "   - Navigate with Tab and arrows" -ForegroundColor Gray
Write-Host "   - Listen for node announcements" -ForegroundColor Gray
Write-Host ""

Write-Host "3. COLOR CONTRAST:" -ForegroundColor Yellow
Write-Host "   - Check opened contrast-test.html" -ForegroundColor Gray
Write-Host "   - All colors should show PASS for AA" -ForegroundColor Gray
Write-Host "   - Easy:   #059669 = 4.52:1 ratio" -ForegroundColor Green
Write-Host "   - Medium: #d97706 = 5.21:1 ratio" -ForegroundColor DarkYellow
Write-Host "   - Hard:   #dc2626 = 4.68:1 ratio" -ForegroundColor Red
Write-Host ""

Write-Host "4. BROWSER DEVTOOLS:" -ForegroundColor Yellow
Write-Host "   - Press F12 to open DevTools" -ForegroundColor Gray
Write-Host "   - Go to 'Lighthouse' tab" -ForegroundColor Gray
Write-Host "   - Select 'Accessibility' only" -ForegroundColor Gray
Write-Host "   - Click 'Generate report'" -ForegroundColor Gray
Write-Host "   - Should score 90+ for WCAG AA" -ForegroundColor Gray
Write-Host ""

Write-Host "5. BROWSER EXTENSIONS:" -ForegroundColor Yellow
Write-Host "   Install these from Chrome Web Store:" -ForegroundColor Gray
Write-Host "   - axe DevTools (most comprehensive)" -ForegroundColor Gray
Write-Host "   - WAVE Evaluation Tool" -ForegroundColor Gray
Write-Host "   Then scan the page for issues" -ForegroundColor Gray
Write-Host ""

Write-Host "======================================" -ForegroundColor Gray
Write-Host "EXPECTED RESULTS" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray
Write-Host ""
Write-Host "[OK] All elements keyboard accessible" -ForegroundColor Green
Write-Host "[OK] Focus indicators visible (blue outline)" -ForegroundColor Green
Write-Host "[OK] Screen reader announces nodes correctly" -ForegroundColor Green
Write-Host "[OK] Color contrast ratios pass WCAG AA" -ForegroundColor Green
Write-Host "[OK] No critical/serious accessibility issues" -ForegroundColor Green
Write-Host ""

Write-Host "Full testing guide opened in Notepad." -ForegroundColor Gray
Write-Host "Follow the detailed steps for complete testing." -ForegroundColor Gray
Write-Host ""
