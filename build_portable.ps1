<#
.SYNOPSIS
Build a portable Windows application bundle for FNIRSI IPS3608 Remote Control.

.DESCRIPTION
Creates a one-directory portable build in dist\FNIRSI-IPS3608 using PyInstaller,
driven by IPS3608RemoteControl.spec (single source of truth for the build:
output name, bundled font asset under ips3608_app/assets, windowed mode).
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

& $python -m PyInstaller --noconfirm --clean IPS3608RemoteControl.spec
if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
}

Write-Host "Portable build complete: dist\FNIRSI-IPS3608"