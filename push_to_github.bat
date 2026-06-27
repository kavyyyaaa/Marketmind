@echo off
cd /d "%~dp0"
echo ==================================================
echo MARKETMIND - GITHUB PUSH BOOTSTRAPPER
echo ==================================================
echo.

echo [INFO] Checking if git is installed...
git --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in your system PATH.
    echo Please download and install Git from: https://git-scm.com/
    echo.
    echo Once installed, open Git Bash in this folder:
    echo   C:\Users\vanda\.gemini\antigravity\scratch\marketmind-ai
    echo.
    echo And run these copy-pasteable commands:
    echo --------------------------------------------------
    echo   git init
    echo   git config user.name "kavyyyaaa"
    echo   git config user.email "kavyyyaaa@users.noreply.github.com"
    echo   git add .
    echo   git commit -m "feat: migrate to Flask REST API + premium HTML/CSS/JS frontend"
    echo   git remote add origin https://github.com/kavyyyaaa/Marketmind.git
    echo   git branch -M main
    echo   git push -f -u origin main
    echo --------------------------------------------------
    echo.
    pause
    exit /b 1
)

echo [INFO] Initializing local Git repository...
if not exist ".git" (
    git init
)

echo [INFO] Staging all files...
git add .

echo [INFO] Configuring local Git identity...
git config user.name "kavyyyaaa"
git config user.email "kavyyyaaa@users.noreply.github.com"

echo [INFO] Committing changes...
git commit -m "feat: migrate to Flask REST API + premium HTML/CSS/JS frontend"

echo [INFO] Linking to GitHub repository...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/kavyyyaaa/Marketmind.git

echo [INFO] Renaming default branch to main...
git branch -M main

echo [INFO] Pushing changes to GitHub (force-push to overwrite default README)...
echo *Note: A GitHub authentication window will pop up if you are not signed in.*
git push -f -u origin main

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Pushing failed. If it was an authentication issue, try running:
    echo   git push -u origin main
    echo manually in Git Bash.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==================================================
echo SUCCESS! Your codebase has been pushed to GitHub!
echo View it here: https://github.com/kavyyyaaa/Marketmind
echo ==================================================
pause
exit /b 0
