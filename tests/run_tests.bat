@echo off
REM Run all Voice Assistant Server tests

echo.
echo ============================================
echo Voice Assistant Server - Test Suite
echo ============================================
echo.

REM Activate virtual environment if it exists
if exist "..\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call ..\venv\Scripts\activate.bat
)

REM Run tests
python run_all_tests.py

echo.
pause
