[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Bundle = Join-Path $RepoRoot 'offline_bundle'
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = 'py'
    & $Python -3.11 (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir $Bundle
} else {
    & $Python (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir $Bundle
}
if ($LASTEXITCODE -ne 0) { throw 'Bundle verification failed.' }

