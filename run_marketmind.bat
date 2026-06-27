@echo off
cd /d "%~dp0"
echo ==================================================
echo MARKETMIND - BOOTSTRAP RUNNER
echo ==================================================
echo.

if not exist ".venv" goto :novenv

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate

echo [INFO] Web application will be hosted on http://127.0.0.1:8050/
echo [INFO] Launching default web browser...
start http://127.0.0.1:8050/
echo.
python app.py

if %ERRORLEVEL% neq 0 goto :error
exit /b 0

:novenv
echo [ERROR] Virtual environment (.venv) not found in this folder.
echo Please create it first using 'uv venv --python 3.12'.
pause
exit /b 1

:error
echo.
echo [ERROR] Application exited with error code %ERRORLEVEL%.
pause
exit /b %ERRORLEVEL%
