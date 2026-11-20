@echo off
REM Run tests from project root

echo.
echo ====================================
echo   Voice Assistant Test Runner
echo ====================================
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found. Using system Python.
)

echo.
echo Running routing architecture tests...
echo ------------------------------------
python -m tests.test_routing

echo.
echo.
echo ====================================
echo   Test Run Complete
echo ====================================
echo.

pause
