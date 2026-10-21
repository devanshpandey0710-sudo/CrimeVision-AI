@echo off
title CrimeVision AI – Intelligent Multimodal Forensic Analysis Platform
color 0B

echo ===============================================================================
echo               CRIMEVISION AI - FORENSIC ANALYSIS PLATFORM
echo ===============================================================================
echo.

echo [1/4] Setting directory context...
cd /d "%~dp0"

echo [2/4] Verifying required folders...
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "reports" mkdir reports

if not exist ".env" (
    if exist ".env.example" (
        echo [INFO] Creating .env from .env.example...
        copy .env.example .env >nul
    )
)

echo [3/4] Checking Python virtual environment...
if not exist "..\venv\Scripts\python.exe" (
    echo [ERROR] Repository-root virtual environment was not found.
    echo Please create the virtual environment first:
    echo     python -m venv venv
    echo     .\venv\Scripts\pip install -r src\requirements.txt
    echo.
    pause
    exit /b 1
)

echo [4/4] Starting CrimeVision AI on http://127.0.0.1:5000 ...
echo.
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

set "FLASK_DEBUG=0"
..\venv\Scripts\python.exe app.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with an error.
    pause
)
