@echo off
REM Voice Assistant Server Startup Script
REM Double-click this file to start the server

echo ========================================
echo   Voice Assistant Server
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Check if .env exists
if not exist "config\.env" (
    echo.
    echo WARNING: config\.env not found!
    echo Copying from config\.env.example...
    copy config\.env.example config\.env
    echo.
    echo IMPORTANT: Edit config\.env and add your API keys!
    echo Then restart this script.
    pause
    exit /b 1
)

REM Kill any existing server instances
echo.
echo Checking for existing server instances...

REM Use PowerShell to find and kill processes on port 8080
powershell -Command "$procs = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique; if ($procs) { $procs | ForEach-Object { Write-Host 'Stopping server process (PID: '$_')'; Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }"

REM Also kill any Python processes with 'Voice Assistant Server' in window title
taskkill /FI "WINDOWTITLE eq Voice Assistant Server*" /F >nul 2>&1

REM Wait for cleanup to complete
echo Waiting for cleanup...
timeout /t 3 /nobreak > nul

REM Start the server and tunnel
echo.
echo ========================================
echo Starting server and Cloudflare tunnel...
echo ========================================
echo.
echo Local Admin Panel: http://localhost:8080
echo Public URL: https://your-server.example.com
echo.
echo Starting Flask server in background...

REM Start Flask server in background
start "Voice Assistant Server" /min python src\server.py

REM Wait for server to initialize
timeout /t 3 /nobreak > nul

REM Check if cloudflared is installed
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: cloudflared not found in PATH
    echo Trying alternative path...
    set CLOUDFLARED="C:\Program Files (x86)\cloudflared\cloudflared.exe"
) else (
    set CLOUDFLARED=cloudflared
)

REM Start Cloudflare tunnel
echo.
echo Starting Cloudflare tunnel...
echo Tunnel: YOUR_TUNNEL_NAME
echo Domain: your-server.example.com
echo.
echo Press Ctrl+C to stop both server and tunnel
echo ========================================
echo.

%CLOUDFLARED% tunnel run YOUR_TUNNEL_NAME

REM If tunnel stops, cleanup
echo.
echo Tunnel stopped. Closing server...
taskkill /FI "WINDOWTITLE eq Voice Assistant Server*" /F >nul 2>&1
pause
