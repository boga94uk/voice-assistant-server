@echo off
REM Server Diagnostics Script
echo ========================================
echo   Voice Assistant Server Diagnostics
echo ========================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)

REM Check if .env exists
echo [1/5] Checking configuration...
if not exist "config\.env" (
    echo   [FAIL] config\.env not found!
    echo   Please copy config\.env.example to config\.env and add your API keys
) else (
    echo   [OK] config\.env exists
)
echo.

REM Check Python version
echo [2/5] Checking Python...
python --version
echo.

REM Check if OpenAI package is installed
echo [3/5] Checking OpenAI package...
python -c "import openai; print(f'  [OK] OpenAI package version: {openai.__version__}')" 2>nul
if errorlevel 1 (
    echo   [FAIL] OpenAI package not installed
    echo   Run: pip install openai
)
echo.

REM Check if API key is set (without revealing it)
echo [4/5] Checking API key...
python -c "import os; from dotenv import load_dotenv; load_dotenv('config/.env'); key=os.getenv('OPENAI_API_KEY'); print('  [OK] API key is set (' + str(len(key)) + ' chars)') if key and key != 'sk-your-key-here' else print('  [FAIL] API key not configured or using default')" 2>nul
if errorlevel 1 (
    echo   [FAIL] Cannot check API key
)
echo.

REM Test OpenAI connection
echo [5/5] Testing OpenAI API connection...
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv('config/.env'); client = OpenAI(api_key=os.getenv('OPENAI_API_KEY')); models = client.models.list(); print('  [OK] OpenAI API is accessible')" 2>nul
if errorlevel 1 (
    echo   [FAIL] Cannot connect to OpenAI API
    echo   Possible issues:
    echo   - Invalid API key
    echo   - Network connectivity issue  
    echo   - OpenAI API service down
    echo   - Rate limit exceeded
)
echo.

REM Check if server is running
echo ========================================
echo Checking if server is running...
netstat -ano | findstr ":8080" >nul
if errorlevel 1 (
    echo [INFO] Server is NOT running on port 8080
    echo Run start_server.bat to start the server
) else (
    echo [INFO] Server IS running on port 8080
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8080"') do (
        echo Process ID: %%a
        goto :found
    )
    :found
)
echo.

echo ========================================
echo Diagnostics Complete
echo ========================================
echo.
echo If transcription is failing, check:
echo 1. Edit config\.env and verify OPENAI_API_KEY is valid
echo 2. Check your OpenAI account for quota/billing issues
echo 3. Restart the server: start_server.bat
echo.
pause
