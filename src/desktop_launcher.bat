@echo off
chcp 65001 >nul 2>&1
title CrimeVision AI - Forensic Analysis Platform
color 0B

echo ===============================================================================
echo               CRIMEVISION AI - FORENSIC ANALYSIS PLATFORM
echo ===============================================================================
echo.

rem ── Strategy 1: Use the directory where THIS script lives ──────────────────
set "PROJECT_DIR=%~dp0"
rem Strip trailing backslash
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

rem Verify app.py exists in that location
if not exist "%PROJECT_DIR%\app.py" set "PROJECT_DIR="

rem ── Strategy 2: Search Desktop for any folder containing app.py ───────────
if "%PROJECT_DIR%"=="" (
    for /d %%D in ("%USERPROFILE%\Desktop\*CrimeVision*") do (
        if exist "%%D\src\app.py" set "PROJECT_DIR=%%D\src"
    )
)

if "%PROJECT_DIR%"=="" (
    echo [ERROR] Could not locate CrimeVision AI project folder.
    echo Please run this launcher from inside the project folder.
    pause
    exit /b 1
)

echo [1/4] Located project directory:
echo       %PROJECT_DIR%
cd /d "%PROJECT_DIR%"
if errorlevel 1 (
    echo [ERROR] Failed to switch to: %PROJECT_DIR%
    pause
    exit /b 1
)

echo.
echo [2/4] Verifying required folders and configuration...
if not exist "data"    mkdir data
if not exist "uploads" mkdir uploads
if not exist "reports" mkdir reports

if not exist ".env" (
    if exist ".env.example" (
        echo      Copying .env.example to .env
        copy .env.example .env >nul
    )
)

echo.
echo [3/4] Verifying Python virtual environment...
if not exist "..\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at:
    echo         repository-root venv\Scripts\python.exe
    echo.
    echo To create it, run:
    echo   python -m venv venv
    echo   venv\Scripts\pip install -r src\requirements.txt
    pause
    exit /b 1
)

echo.
echo [4/4] Starting CrimeVision AI on http://127.0.0.1:5000 ...
echo       (The browser will open automatically in 2 seconds)
echo.
echo Press Ctrl+C to stop the server.
echo ===============================================================================
echo.

rem Open browser after a short delay
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

set "FLASK_DEBUG=0"
..\venv\Scripts\python.exe app.py

if errorlevel 1 (
    echo.
    echo ===============================================================================
    echo [ERROR] Application exited with an error. See output above.
    echo ===============================================================================
    pause
)
