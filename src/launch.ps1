<#
.SYNOPSIS
    Local launch script for CrimeVision AI Forensic Analysis Platform.
.DESCRIPTION
    Activates the local Python virtual environment, verifies project dependencies,
    ensures required directories exist, and starts the Flask server at http://127.0.0.1:5000.
    Automatically launches the browser interface.
#>

[CmdletBinding()]
param(
    [int]$Port = 5000,
    [switch]$NoBrowser,
    [switch]$Debug
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "CrimeVision AI - Intelligent Multimodal Forensic Analysis Platform"

Write-Host ""
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host "         CRIMEVISION AI – MULTIMODAL FORENSIC ANALYSIS PLATFORM               " -ForegroundColor Cyan
Write-Host "===============================================================================" -ForegroundColor Cyan
Write-Host ""

# Keep source/runtime files in src while using the repository-root virtual environment.
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepositoryRoot = Split-Path -Parent $SourceRoot
Set-Location $SourceRoot
Write-Host "[1/4] Source directory context set." -ForegroundColor Gray

# Ensure required directories exist
$RequiredDirs = @("data", "uploads", "reports")
foreach ($dir in $RequiredDirs) {
    $dirPath = Join-Path $SourceRoot $dir
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
    }
}

# Verify virtual environment
$VenvPython = Join-Path $RepositoryRoot "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Repository-root virtual environment was not found." -ForegroundColor Red
    Write-Host "Please create the virtual environment using:" -ForegroundColor Yellow
    Write-Host "    python -m venv venv" -ForegroundColor Yellow
    Write-Host "    .\venv\Scripts\pip install -r src\requirements.txt" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}
Write-Host "[2/4] Python virtual environment verified." -ForegroundColor Green

# Verify or initialize .env
$EnvFile = Join-Path $SourceRoot ".env"
$EnvExample = Join-Path $SourceRoot ".env.example"
if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
    Copy-Item $EnvExample $EnvFile
    Write-Host "[INFO] Created .env from .env.example (defaults configured)." -ForegroundColor Yellow
}

# Keep debug disabled unless explicitly requested.
if ($Debug) {
    $env:FLASK_DEBUG = "1"
} else {
    $env:FLASK_DEBUG = "0"
}

$ServerUrl = "http://127.0.0.1:$Port"
Write-Host "[3/4] Preparing to launch CrimeVision AI on $ServerUrl ..." -ForegroundColor Cyan

# Open default browser after brief delay
if (-not $NoBrowser) {
    Start-Job -ScriptBlock {
        param($url)
        Start-Sleep -Seconds 2
        Start-Process $url
    } -ArgumentList $ServerUrl | Out-Null
}

Write-Host "[4/4] Starting server process (Press Ctrl+C to stop)..." -ForegroundColor Green
Write-Host "-------------------------------------------------------------------------------" -ForegroundColor Gray
Write-Host ""

try {
    & $VenvPython "app.py"
}
finally {
    Write-Host ""
    Write-Host "Server stopped." -ForegroundColor Yellow
}
