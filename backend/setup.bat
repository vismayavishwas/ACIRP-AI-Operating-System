@echo off
echo ====================================================
echo ACIRP Backend Setup: Creating Environment & Installing
echo ====================================================
cd /d "%~dp0"

echo [1/4] Creating virtual environment (venv)...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Python not found or failed to create venv. Please ensure Python is installed and in your PATH.
    pause
    exit /b %errorlevel%
)

echo [2/4] Activating venv and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [3/4] Installing requirements...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install packages from requirements.txt.
    pause
    exit /b %errorlevel%
)

echo [4/4] Installing Playwright Chromium browser...
playwright install chromium
if %errorlevel% neq 0 (
    echo WARNING: Playwright browser installation failed. Local web automation may fail, but mock API integration will still work.
)

echo ====================================================
echo Setup Completed Successfully!
echo To activate the environment in the future, run:
echo    backend\venv\Scripts\activate
echo To start the backend server, run:
echo    python main.py
echo ====================================================
pause
