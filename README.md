# Offline voice chatbot for Windows

This is a fully local English voice proof of concept:

```text
Microphone -> Moonshine STT -> Python -> Pocket TTS -> Speaker
```

It uses:

- Python 3.11 on Windows x64
- Moonshine Voice 0.1.5, Medium Streaming English
- Pocket TTS 3.1.0, `english_2026-04`
- the built-in `alba` voice
- CPU inference; CUDA is not required

At runtime it needs no internet, DNS, PyPI, Hugging Face, GitHub, API key, cloud speech service, telemetry, model download, update check, or license check.

## Important: code and bundle are separate

The Git repository contains source code and tests.

The large wheels and model files are distributed as one verified ZIP in the [v1.0.0 offline bundle release](https://github.com/mohnish-pakanati/lloyds_voice_chatbot/releases/tag/v1.0.0-offline-bundle).

Do not use Git LFS for the bundle on the Lloyds laptop. Download the release ZIP through the browser or use an organization-approved transfer method.

## Lloyds laptop: simple setup without PowerShell scripts

Use these instructions when `.ps1` files are blocked by corporate policy. Type each command directly into PowerShell. Do not change or bypass the execution policy.

### 1. Get the source code

For a clean checkout:

```powershell
git clone https://github.com/mohnish-pakanati/lloyds_voice_chatbot.git lloyds_voice_chatbot_clean
cd lloyds_voice_chatbot_clean
```

If you already have a working checkout:

```powershell
git pull origin main
```

### 2. Download the offline bundle

Download this file in the browser:

[offline_bundle-windows-py311.zip](https://github.com/mohnish-pakanati/lloyds_voice_chatbot/releases/download/v1.0.0-offline-bundle/offline_bundle-windows-py311.zip)

Expected ZIP SHA-256:

```text
18543EB81F19E16C6FD712560CE2E328DCFC287E999E7C75831B8DB9D89FD179
```

### 3. Verify and extract the ZIP

```powershell
Get-FileHash "$env:USERPROFILE\Downloads\offline_bundle-windows-py311.zip" -Algorithm SHA256
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\offline_bundle-windows-py311.zip" -DestinationPath . -Force
```

The calculated SHA-256 must exactly match the value above.

Verify all files inside the extracted bundle:

```powershell
py -3.11 .\tools\verify_checksums.py --bundle-dir .\offline_bundle
```

Expected result:

```text
BUNDLE CHECKSUMS: PASS (67 files)
```

This means every required wheel, model and voice file exists and matches the prepared bundle.

### 4. Create the Python environment

```powershell
py -3.11 --version
py -3.11 -m venv .venv
```

Python must report version 3.11.x and must be 64-bit.

### 5. Enable offline mode

```powershell
$env:PIP_NO_INDEX="1"
$env:HF_HUB_OFFLINE="1"
$env:HF_HUB_DISABLE_TELEMETRY="1"
$env:DO_NOT_TRACK="1"
$env:OFFLINE_MODE="1"
$env:VOICE_POC_ROOT=(Get-Location).Path
$env:PYTHONPATH=(Get-Location).Path
```

These variables apply to the current PowerShell window. Set them again after opening a new window.

### 6. Install only from the local bundle

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .\offline_bundle\wheels --requirement .\requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
```

Expected final line:

```text
No broken requirements found.
```

`--no-index` prevents pip from contacting PyPI.

### 7. Run the automated offline test

```powershell
.\.venv\Scripts\python.exe .\tools\verify_no_network.py --run-suite
```

Expected result:

```text
OFFLINE STT INITIALIZATION: PASS
OFFLINE TTS INITIALIZATION: PASS
OFFLINE TTS: PASS
OFFLINE STT: PASS
OFFLINE ROUNDTRIP: PASS
NETWORK ATTEMPTS: 0
```

### 8. Test the speaker

```powershell
.\.venv\Scripts\python.exe .\tests\test_tts.py --play
```

### 9. Test the microphone

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_microphone.py --seconds 5
```

### 10. Test the complete voice loop

```powershell
.\.venv\Scripts\python.exe .\tests\test_roundtrip.py --mode microphone --play
```

Say: `Hello, can you hear me?`

The system should reply: `You said: Hello, can you hear me?`

## Final zero-internet proof

After installation:

1. Disable Wi-Fi.
2. Disconnect Ethernet and VPN where appropriate under Lloyds policy.
3. Open PowerShell in the repository.
4. Set the offline environment variables from step 5 again.
5. Run:

```powershell
.\.venv\Scripts\python.exe .\tools\verify_no_network.py --run-suite
```

All tests must pass with `NETWORK ATTEMPTS: 0`.

## Standard setup when PowerShell scripts are allowed

After placing the extracted `offline_bundle` in the repository root:

```powershell
.\scripts\verify_bundle.ps1
.\scripts\install_offline.ps1
.\scripts\run_all_tests.ps1
```

For microphone and playback testing:

```powershell
.\scripts\run_all_tests.ps1 -IncludeMicrophone -PlayAudio
```

## Build a new bundle on an internet-connected machine

Only use this when intentionally rebuilding the bundle:

```powershell
.\scripts\prepare_online.ps1 -MoonshineModel medium -Force
```

The preparation script downloads the exact Windows wheels and model assets, validates a clean offline installation, writes the manifest, and generates checksums. It never disables SSL verification.

## What the checks prove

- ZIP SHA-256 proves the downloaded archive is byte-for-byte identical.
- `verify_checksums.py` proves all 67 internal files are present and unchanged.
- `verify_no_network.py` blocks common Python network calls during initialization and inference.
- Physically disconnecting networking is the final system-level offline proof.

Checksums prove file integrity. They do not replace Lloyds malware scanning, vulnerability review, license review, code signing, or application allow-listing.

## Common problems

- **PowerShell says scripts are disabled:** use the typed commands above or ask Lloyds IT to sign and approve the `.ps1` files. Do not bypass policy.
- **Git LFS authorization error:** do not use LFS. Download the release ZIP in a browser.
- **Checksum file is missing:** the release ZIP was not extracted into the repository root.
- **Checksum mismatch:** stop. Download or transfer the bundle again.
- **Python is not 3.11:** use an organization-approved Python 3.11 x64 installation.
- **Microphone denied:** enable desktop microphone access through the approved Windows policy.
- **No audio:** select a working Windows input/output device.

Technical API and model provenance details are in [docs/DEPENDENCY_NOTES.md](docs/DEPENDENCY_NOTES.md).
