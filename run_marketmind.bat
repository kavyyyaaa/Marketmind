@echo off
cd /d "%~dp0"
echo ==================================================
echo MARKETMIND - SMART BOOTSTRAP RUNNER
echo ==================================================
echo.

:: 1. Check if we have a working virtual environment already
set VENV_OK=0
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import flask, pandas, sklearn, xgboost" >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set VENV_OK=1
    )
)

if "%VENV_OK%"=="1" (
    echo [INFO] Virtual environment is healthy. Starting dashboard...
    goto :startapp
)

:: 2. If .venv is missing or broken, check if global Python is installed to rebuild it
echo [INFO] Testing system Python configuration...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed on this computer or not in system PATH.
    echo Please install Python [3.11 or 3.12] from python.org or the Microsoft Store.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: 3. Rebuild virtual environment
echo [INFO] Rebuilding virtual environment...
if exist ".venv" (
    echo [INFO] Removing broken environment...
    rmdir /s /q .venv >nul 2>&1
)

echo [INFO] Creating new virtual environment...
python -m venv .venv
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [INFO] Installing required dependencies - this may take a few minutes...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [INFO] Environment successfully configured!
echo.

:startapp
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
