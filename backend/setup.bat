@echo off
REM Intuitscape Backend Setup Script for Windows CMD
REM Run this script to set up your development environment

echo ========================================
echo   Intuitscape Backend Setup
echo ========================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
) else (
    echo [OK] Python found
)

REM Check if virtual environment exists
if exist "venv" (
    echo [OK] Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

REM Install requirements
echo.
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
) else (
    echo [OK] All dependencies installed successfully
)

REM Check if .env file exists
echo.
if exist ".env" (
    echo [OK] .env file found
) else (
    echo Creating .env file from template...
    copy .env.example .env >nul
    echo [OK] .env file created
    echo.
    echo [WARNING] IMPORTANT: Edit .env file with your Google Cloud credentials!
    echo    Required values:
    echo    - PROJECT_NAME: Your GCP project ID
    echo    - ACCESS_TOKEN: Your GCP access token
)

REM Create uploads directory
echo.
if exist "uploads" (
    echo [OK] Uploads directory exists
) else (
    echo Creating uploads directory...
    mkdir uploads
    echo [OK] Uploads directory created
)

REM Summary
echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Edit .env file with your GCP credentials
echo    notepad .env
echo.
echo 2. Run the test suite:
echo    python test_api.py
echo.
echo 3. Start the development server:
echo    python main.py
echo.
echo 4. Access the API:
echo    http://localhost:5000/api/health
echo    http://localhost:5000/api/docs
echo.
echo Documentation available in:
echo   - README.md (API documentation)
echo   - DEPLOYMENT.md (deployment guide)
echo   - IMPROVEMENTS.md (changes log)
echo.
pause
