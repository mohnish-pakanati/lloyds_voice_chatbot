[CmdletBinding()]
param([switch]$Recreate)

$ErrorActionPreference = 'Stop'
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Bundle = Join-Path $RepoRoot 'offline_bundle'
$Venv = Join-Path $RepoRoot '.venv'
$Wheels = Join-Path $Bundle 'wheels'
$LockFile = Join-Path $RepoRoot 'requirements-lock.txt'

$version = & py -3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne '3.11') {
    throw 'Python 3.11 x64 is required. Install it through your organization-approved process.'
}
$bits = & py -3.11 -c "import struct; print(struct.calcsize('P') * 8)"
if ($bits.Trim() -ne '64') { throw '64-bit Python is required.' }

& py -3.11 (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir $Bundle
if ($LASTEXITCODE -ne 0) { throw 'Bundle checksum verification failed. Installation stopped.' }

if ($Recreate -and (Test-Path -LiteralPath $Venv)) {
    $resolvedVenv = [System.IO.Path]::GetFullPath($Venv)
    if (-not $resolvedVenv.StartsWith($RepoRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Unsafe virtual environment path: $resolvedVenv"
    }
    Remove-Item -LiteralPath $Venv -Recurse -Force
}
if (-not (Test-Path -LiteralPath $Venv)) {
    & py -3.11 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv.' }
}

$Python = Join-Path $Venv 'Scripts\python.exe'
$env:PIP_NO_INDEX = '1'
$env:HF_HUB_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:DO_NOT_TRACK = '1'
$env:OFFLINE_MODE = '1'
$env:VOICE_POC_ROOT = $RepoRoot

& $Python -m pip install --no-index --find-links $Wheels --requirement $LockFile
if ($LASTEXITCODE -ne 0) { throw 'Offline package installation failed. No index was contacted.' }
& $Python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Installed package dependency check failed.' }
& $Python -c "from src import config; print('Moonshine:', config.MOONSHINE_MODEL_DIR); print('Pocket TTS:', config.POCKET_TTS_MODEL_DIR); print('Voice:', config.POCKET_TTS_VOICE_FILE)"
if ($LASTEXITCODE -ne 0) { throw 'Offline configuration smoke check failed.' }

Write-Host 'OFFLINE INSTALL: PASS'
Write-Host 'Run .\scripts\run_all_tests.ps1 after disconnecting all network interfaces.'

