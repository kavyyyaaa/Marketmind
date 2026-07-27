@echo off
cd /d "%~dp0"
echo ==================================================
echo MARKETMIND - SMART BOOTSTRAP RUNNER
echo ==================================================
echo.

:: 1. Check if Python is installed on the system
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed on this computer or not in system PATH.
    echo Please install Python (3.11 or 3.12) from python.org or the Microsoft Store.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 2. Check if .venv is working
echo [INFO] Testing virtual environment...
set REBUILD_VENV=0

if not exist ".venv" (
    echo [INFO] No virtual environment found. Setting up...
    set REBUILD_VENV=1
) else (
    :: Run a test import to see if the environment is active and has dependencies
    .venv\Scripts\python.exe -c "import flask, pandas, sklearn, xgboost" >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] The virtual environment (.venv) is broken or missing dependencies.
        echo (This happens when copying python projects between different computers).
        echo Rebuilding .venv for this computer...
        set REBUILD_VENV=1
    )
)

if "%REBUILD_VENV%"=="1" (
    :: Clean up old broken venv folder if it exists
    if exist ".venv" (
        echo [INFO] Removing old environment...
        rmdir /s /q .venv >nul 2>&1
    )
    
    echo [INFO] Creating new virtual environment...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    echo [INFO] Installing required dependencies (this may take a few minutes)...
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [INFO] Environment successfully configured!
    echo.
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

echo [INFO] Web application will be hosted on http://127.0.0.1:8050/
echo [INFO] Launching default web browser...
start http://127.0.0.1:8050/
echo.
python app.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)
exit /b 0
