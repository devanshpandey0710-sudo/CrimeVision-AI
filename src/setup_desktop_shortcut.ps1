# setup_desktop_shortcut.ps1
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$desktop = [System.Environment]::GetFolderPath('Desktop')

# 1. Direct Batch launcher on Desktop
$srcBat = Join-Path $projectRoot 'desktop_launcher.bat'
$destBat = Join-Path $desktop 'Launch CrimeVision AI.bat'
$destLnk = Join-Path $desktop 'CrimeVision AI.lnk'
if ((Test-Path -LiteralPath $destBat) -or (Test-Path -LiteralPath $destLnk)) {
    throw 'A desktop launcher or shortcut already exists. Move or rename the existing file before running this helper.'
}
Copy-Item -Path $srcBat -Destination $destBat
Write-Host "Created Desktop Batch Launcher: $destBat" -ForegroundColor Green

# 2. Windows Shortcut (.lnk) on Desktop
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($destLnk)
$fso = New-Object -ComObject Scripting.FileSystemObject
$shortDir = $fso.GetFolder($projectRoot).ShortPath
$shortcut.TargetPath = Join-Path $shortDir 'launch.bat'
$shortcut.WorkingDirectory = $shortDir
$shortcut.Description = 'CrimeVision AI - Intelligent Multimodal Forensic Analysis Platform'
$shortcut.Save()
Write-Host "Created Desktop Shortcut: $destLnk (target: $($shortcut.TargetPath))" -ForegroundColor Green
