[CmdletBinding()]
param(
    [ValidateSet('medium', 'small')]
    [string]$MoonshineModel = 'medium',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Bundle = Join-Path $RepoRoot 'offline_bundle'
$LockFile = Join-Path $RepoRoot 'requirements-lock.txt'
$Build = Join-Path $RepoRoot ('.bundle-build-' + [guid]::NewGuid().ToString('N'))
$PrepVenv = Join-Path ([System.IO.Path]::GetTempPath()) ('voice-poc-prep-' + [guid]::NewGuid().ToString('N'))

function Assert-Python311 {
    $version = & py -3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne '3.11') {
        throw 'Python 3.11 x64 is required on the online preparation machine.'
    }
    $bits = & py -3.11 -c "import struct; print(struct.calcsize('P') * 8)"
    if ($bits.Trim() -ne '64') { throw '64-bit Python is required.' }
}

try {
    Assert-Python311
    if (-not (Test-Path -LiteralPath $LockFile)) { throw "Missing lock file: $LockFile" }

    $existing = @()
    if (Test-Path -LiteralPath $Bundle) {
        $existing = @(Get-ChildItem -LiteralPath $Bundle -Recurse -File | Where-Object Name -ne '.gitkeep')
    }
    if ($existing.Count -gt 0 -and -not $Force) {
        throw 'offline_bundle already contains generated files. Re-run with -Force to replace it after a successful new build.'
    }

    New-Item -ItemType Directory -Force -Path (Join-Path $Build 'wheels') | Out-Null
    & py -3.11 -m venv $PrepVenv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the preparation virtual environment.' }
    $Python = Join-Path $PrepVenv 'Scripts\python.exe'

    & $Python -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw 'Failed to prepare pip tooling.' }

    & $Python -m pip download --only-binary=:all: --dest (Join-Path $Build 'wheels') --requirement $LockFile
    if ($LASTEXITCODE -ne 0) { throw 'Wheel download failed. The bundle was not replaced.' }

    $env:PIP_NO_INDEX = '1'
    & $Python -m pip install --no-index --find-links (Join-Path $Build 'wheels') --requirement $LockFile
    if ($LASTEXITCODE -ne 0) { throw 'Local wheel installation verification failed.' }
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'The resolved wheel set has dependency conflicts.' }
    Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue

    & $Python (Join-Path $RepoRoot 'tools\download_models.py') --bundle-dir $Build --moonshine-model $MoonshineModel
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed. The bundle was not replaced.' }

    & $Python (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir $Build --generate
    & $Python (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir $Build
    if ($LASTEXITCODE -ne 0) { throw 'New bundle verification failed. The bundle was not replaced.' }

    $resolvedBuild = [System.IO.Path]::GetFullPath($Build)
    if (-not $resolvedBuild.StartsWith($RepoRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Unsafe build path: $resolvedBuild"
    }
    if (Test-Path -LiteralPath $Bundle) {
        Remove-Item -LiteralPath $Bundle -Recurse -Force
    }
    Move-Item -LiteralPath $Build -Destination $Bundle
    Write-Host "Offline bundle ready: $Bundle"
}
finally {
    Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $PrepVenv) {
        Remove-Item -LiteralPath $PrepVenv -Recurse -Force
    }
    if (Test-Path -LiteralPath $Build) {
        $resolvedBuild = [System.IO.Path]::GetFullPath($Build)
        if ($resolvedBuild.StartsWith($RepoRoot + [System.IO.Path]::DirectorySeparatorChar)) {
            Remove-Item -LiteralPath $Build -Recurse -Force
        }
    }
}

