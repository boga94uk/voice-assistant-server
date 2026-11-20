@echo off
setlocal enabledelayedexpansion

echo ============================================
echo Voice Assistant Server Export Tool
echo ============================================
echo.

set OUTPUT_FILE=export_server.txt
set PROJECT_ROOT=%~dp0

:: Clear previous export
if exist "%OUTPUT_FILE%" del "%OUTPUT_FILE%"

:: Header
echo ============================================ >> "%OUTPUT_FILE%"
echo Voice Assistant Server Project Export >> "%OUTPUT_FILE%"
echo Generated: %DATE% %TIME% >> "%OUTPUT_FILE%"
echo ============================================ >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

:: Project Structure
echo [PROJECT STRUCTURE] >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
tree /F /A >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

:: Configuration Files
echo ============================================ >> "%OUTPUT_FILE%"
echo [requirements.txt] >> "%OUTPUT_FILE%"
echo ============================================ >> "%OUTPUT_FILE%"
type requirements.txt >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo ============================================ >> "%OUTPUT_FILE%"
echo [start_server.bat] >> "%OUTPUT_FILE%"
echo ============================================ >> "%OUTPUT_FILE%"
type start_server.bat >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

:: Documentation Files
echo ============================================ >> "%OUTPUT_FILE%"
echo [DOCUMENTATION FILES] >> "%OUTPUT_FILE%"
echo ============================================ >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

for %%f in (*.md *.txt) do (
    if not "%%f"=="export_server.txt" (
        echo ============================================ >> "%OUTPUT_FILE%"
        echo [%%f] >> "%OUTPUT_FILE%"
        echo ============================================ >> "%OUTPUT_FILE%"
        type "%%f" >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
    )
)

:: Config Files
if exist "config" (
    echo ============================================ >> "%OUTPUT_FILE%"
    echo [CONFIG FILES] >> "%OUTPUT_FILE%"
    echo ============================================ >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
    
    for /R config %%f in (*.json *.yaml *.yml *.ini *.env *.py) do (
        echo ============================================ >> "%OUTPUT_FILE%"
        echo [%%~nxf - %%f] >> "%OUTPUT_FILE%"
        echo ============================================ >> "%OUTPUT_FILE%"
        type "%%f" >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
    )
)

:: Source Files
if exist "src" (
    echo ============================================ >> "%OUTPUT_FILE%"
    echo [SOURCE FILES] >> "%OUTPUT_FILE%"
    echo ============================================ >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
    
    for /R src %%f in (*.py) do (
        echo ============================================ >> "%OUTPUT_FILE%"
        echo [%%~nxf - %%f] >> "%OUTPUT_FILE%"
        echo ============================================ >> "%OUTPUT_FILE%"
        type "%%f" >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
    )
)

:: Test Files
if exist "tests" (
    echo ============================================ >> "%OUTPUT_FILE%"
    echo [TEST FILES] >> "%OUTPUT_FILE%"
    echo ============================================ >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
    
    for /R tests %%f in (*.py) do (
        echo ============================================ >> "%OUTPUT_FILE%"
        echo [%%~nxf - %%f] >> "%OUTPUT_FILE%"
        echo ============================================ >> "%OUTPUT_FILE%"
        type "%%f" >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
        echo. >> "%OUTPUT_FILE%"
    )
)

:: Test Scripts in Root
if exist "test_deployment.py" (
    echo ============================================ >> "%OUTPUT_FILE%"
    echo [test_deployment.py] >> "%OUTPUT_FILE%"
    echo ============================================ >> "%OUTPUT_FILE%"
    type test_deployment.py >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

if exist "test_env.py" (
    echo ============================================ >> "%OUTPUT_FILE%"
    echo [test_env.py] >> "%OUTPUT_FILE%"
    echo ============================================ >> "%OUTPUT_FILE%"
    type test_env.py >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
    echo. >> "%OUTPUT_FILE%"
)

echo.
echo ============================================
echo Export Complete!
echo Output: %OUTPUT_FILE%
echo.
echo File size:
for %%A in ("%OUTPUT_FILE%") do echo %%~zA bytes
echo ============================================
echo.
pause
