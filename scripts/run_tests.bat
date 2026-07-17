@echo off
echo ==============================================================
echo  ACIRP - Keploy API Recording & Replay Tester
echo ==============================================================
echo.
echo Make sure Keploy CLI is installed (https://docs.keploy.io/docs/server/installation/)
echo.
echo 1. Record API Tests
echo 2. Replay & Assert API Tests
echo 3. Exit
echo.
set /p opt="Select an option (1-3): "

if "%opt%"=="1" (
    echo Starting Keploy Recording session...
    echo Connect to http://localhost:8000 and run actions to capture traffic.
    keploy record -c "uvicorn main:app --host 0.0.0.0 --port 8000" --config-path "./keploy.yml"
)

if "%opt%"=="2" (
    echo Starting Keploy Replay & Regression check...
    keploy test -c "uvicorn main:app --host 0.0.0.0 --port 8000" --config-path "./keploy.yml"
)

exit
