@echo off
echo.
echo ============================================================
echo   INTUITSCAPE ACCESSIBILITY QUICK CHECK
echo ============================================================
echo.

:: Check if frontend is running
echo [TEST] Checking if frontend is running...
curl -s -o nul -w "%%{http_code}" http://localhost:3000 > temp.txt
set /p STATUS=<temp.txt
del temp.txt

if "%STATUS%"=="200" (
    echo [PASS] Frontend is running at http://localhost:3000
) else (
    echo [FAIL] Frontend is not running!
    echo        Start it with: cd frontend ^&^& npm start
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   OPENING TEST FILES
echo ============================================================
echo.

:: Open color contrast checker
if exist "color-contrast-test.html" (
    echo [OK] Opening color contrast checker...
    start "" "color-contrast-test.html"
) else (
    echo [SKIP] color-contrast-test.html not found
)

:: Open testing guide
if exist "ACCESSIBILITY_TESTING_GUIDE.md" (
    echo [OK] Opening testing guide...
    start notepad "ACCESSIBILITY_TESTING_GUIDE.md"
) else (
    echo [SKIP] Testing guide not found
)

:: Open quick reference
if exist "ACCESSIBILITY_QUICK_REFERENCE.md" (
    echo [OK] Opening quick reference...
    start notepad "ACCESSIBILITY_QUICK_REFERENCE.md"
) else (
    echo [SKIP] Quick reference not found
)

echo.
echo ============================================================
echo   MANUAL TESTS REQUIRED
echo ============================================================
echo.
echo 1. KEYBOARD NAVIGATION:
echo    - Go to http://localhost:3000
echo    - Enter a topic (e.g., "Machine Learning")
echo    - Press Tab - should see blue focus outline
echo    - Press Down Arrow - select first node
echo    - Press Arrow keys (up/down/left/right) - navigate
echo    - Press Enter - open node details
echo    - Press H - show keyboard shortcuts
echo    - Press Esc - close modal
echo.
echo 2. BROWSER DEVTOOLS (F12):
echo    - Open Lighthouse tab
echo    - Select "Accessibility" only
echo    - Click "Generate report"
echo    - Should score 90+ (WCAG AA compliant)
echo.
echo 3. INSTALL BROWSER EXTENSIONS:
echo    Chrome Web Store:
echo    - axe DevTools
echo    - WAVE Evaluation Tool
echo    Then scan the page
echo.
echo 4. COLOR CONTRAST:
echo    - Check opened HTML file
echo    - All three colors pass WCAG AA
echo    - Easy: #059669 (4.52:1)
echo    - Medium: #d97706 (5.21:1)
echo    - Hard: #dc2626 (4.68:1)
echo.
echo 5. SCREEN READER (Optional):
echo    - Download NVDA: https://www.nvaccess.org/download/
echo    - Start with Ctrl+Alt+N
echo    - Navigate with Tab and arrows
echo.
echo ============================================================
echo   EXPECTED RESULTS
echo ============================================================
echo.
echo [OK] All elements keyboard accessible
echo [OK] Focus indicators visible
echo [OK] Screen reader announces correctly
echo [OK] Color contrast passes WCAG AA
echo [OK] Lighthouse score 90+
echo.
echo Full testing instructions are now open in Notepad.
echo Follow the detailed guide for complete testing.
echo.
pause
