<#
.SYNOPSIS
Build a portable Windows application bundle for IPS3608 Remote Control.

.DESCRIPTION
Creates a one-directory portable build in dist\IPS3608RemoteControl
using PyInstaller. The app bundle includes the font asset under ips3608_app/assets.
#>

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Virtual environment Python not found at $python. Create .venv first."
    exit 1
}

try {
    & $python -m PyInstaller --version > $null 2>&1
} catch {
    Write-Error "PyInstaller is not installed in the virtual environment. Run:`n    & $python -m pip install pyinstaller"
    exit 1
}

$distName = "IPS3608RemoteControl"
Remove-Item -Recurse -Force "build\$distName" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "dist\$distName" -ErrorAction SilentlyContinue
Remove-Item -Force "$distName.spec" -ErrorAction SilentlyContinue

& $python -m PyInstaller --noconfirm --clean `
    --onedir `
    --windowed `
    --name $distName `
    --add-data "ips3608_app/assets;ips3608_app/assets" `
    ips3608_remote_ui.py

Write-Host "Portable build complete: dist\$distName"