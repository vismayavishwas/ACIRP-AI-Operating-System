@echo off
echo ====================================================
echo ACIRP Frontend Setup: Installing Web dependencies
echo ====================================================
cd /d "%~dp0"

echo [1/2] Running npm install...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: npm install failed. Please check that Node.js and npm are installed on your machine.
    pause
    exit /b %errorlevel%
)

echo ====================================================
echo [2/2] Setup Completed Successfully!
echo To run the frontend dev server, execute:
echo    npm run dev
echo ====================================================
pause
