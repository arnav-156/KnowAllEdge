@echo off
echo ============================================================
echo   Google Gemini Translation Setup
echo ============================================================
echo.

REM Prompt for API key if not set
if "%GEMINI_API_KEY%"=="" (
    echo GEMINI_API_KEY not found in environment.
    echo.
    set /p GEMINI_API_KEY="Enter your Gemini API key: "
)

echo.
echo Using API key: %GEMINI_API_KEY:~0,20%...
echo.
echo ============================================================
echo   Running Translation Script
echo ============================================================
echo.

python translate_with_gemini.py

pause
