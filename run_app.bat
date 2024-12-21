@echo off
REM Change to the directory containing your Flask app
cd /d %~dp0

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python and try again.
    pause
    exit /b
)

REM Install required libraries
echo Installing required libraries...
pip install flask flask-cors flask-socketio undetected-chromedriver requests >nul 2>&1
if errorlevel 1 (
    echo Failed to install required libraries. Please check your Python environment.
    pause
    exit /b
)

REM Start the Flask app
start cmd /k python .\backend\app.py

REM Wait a moment for the server to start
timeout /t 2 >nul

REM Open the default browser to the Flask app URL
start http://127.0.0.1:5000
