[CmdletBinding()]
param(
    [switch]$IncludeMicrophone,
    [switch]$PlayAudio
)

$ErrorActionPreference = 'Stop'
$RepoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$Python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) {
    throw 'The offline virtual environment does not exist. Run .\scripts\install_offline.ps1 first.'
}

$env:PIP_NO_INDEX = '1'
$env:HF_HUB_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
$env:DO_NOT_TRACK = '1'
$env:OFFLINE_MODE = '1'
$env:VOICE_POC_ROOT = $RepoRoot
$env:PYTHONPATH = $RepoRoot

& $Python (Join-Path $RepoRoot 'tools\verify_checksums.py') --bundle-dir (Join-Path $RepoRoot 'offline_bundle')
if ($LASTEXITCODE -ne 0) { throw 'Checksum validation failed.' }
& $Python (Join-Path $RepoRoot 'tools\verify_no_network.py') --run-suite
if ($LASTEXITCODE -ne 0) { throw 'Offline inference suite failed.' }

if ($IncludeMicrophone) {
    & $Python (Join-Path $RepoRoot 'tests\test_stt_microphone.py')
    if ($LASTEXITCODE -ne 0) { throw 'Microphone STT test failed.' }
    $roundtripArgs = @((Join-Path $RepoRoot 'tests\test_roundtrip.py'), '--mode', 'microphone')
    if ($PlayAudio) { $roundtripArgs += '--play' }
    & $Python @roundtripArgs
    if ($LASTEXITCODE -ne 0) { throw 'Microphone round-trip test failed.' }
}

