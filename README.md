# Fully offline Windows voice POC

This repository packages and runs an English voice loop using the official Moonshine Voice STT and Kyutai Pocket TTS implementations. Runtime is local-only: no DNS, internet, PyPI, Hugging Face, GitHub, cloud speech service, telemetry, model download, update check, or license check is required.

Target: Windows 11 x64, CPython 3.11, CPU inference. The default STT is Moonshine Medium Streaming; `small` is available during bundle preparation. TTS is Pocket TTS 3.1.0 `english_2026-04` with the official precomputed `alba` voice. See [dependency notes](docs/DEPENDENCY_NOTES.md) for verified APIs and asset provenance.

## A. PREPARE BUNDLE ON INTERNET MACHINE

Use an internet-connected Windows x64 machine with 64-bit Python 3.11. Start in the repository root:

```powershell
py -3.11 --version
.\scripts\prepare_online.ps1 -MoonshineModel medium
```

For the lighter STT model:

```powershell
.\scripts\prepare_online.ps1 -MoonshineModel small
```

The script creates a temporary Python 3.11 environment, downloads a complete Windows wheelhouse, installs and checks it from that wheelhouse, downloads the exact official model assets, writes `offline_bundle/manifest.json`, generates SHA-256 checksums, and verifies the finished bundle. It builds in a staging directory and replaces `offline_bundle` only after verification. Use `-Force` when intentionally replacing an existing generated bundle.

No SSL verification is disabled. If the connected preparation machine cannot reach PyPI, `download.moonshine.ai`, or Hugging Face through the organization's supported network configuration, prepare the bundle on another approved connected machine.

## B. TRANSFER

Transfer the complete repository directory, including `offline_bundle`, using an organization-approved file-transfer mechanism. Do not bypass enterprise security controls. Preserve filenames and directory structure; the offline laptop will reject modified or missing files through SHA-256 verification.

## C. INSTALL ON OFFLINE LAPTOP

From PowerShell in the transferred repository root:

```powershell
.\scripts\verify_bundle.ps1
.\scripts\install_offline.ps1
```

Installation requires 64-bit Python 3.11, creates `.venv`, and runs pip with both `--no-index` and `--find-links=offline_bundle\wheels`. It sets Hugging Face offline/telemetry flags and does not initialize a downloader. To recreate an existing environment:

```powershell
.\scripts\install_offline.ps1 -Recreate
```

If corporate PowerShell policy blocks unsigned scripts, use the organization's approved script-signing or execution process; do not weaken corporate policy.

## D. TEST STT

Place a non-confidential English WAV at `samples\sample.wav`, then run:

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_file.py --audio .\samples\sample.wav
```

For the default microphone:

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_microphone.py --seconds 5
```

The commands print transcript, load/inference time, audio duration, and real-time factor.

## E. TEST TTS

```powershell
.\.venv\Scripts\python.exe .\tests\test_tts.py
```

The output is `outputs\tts_test.wav`. Add `--play` to play it through the default Windows output device.

## F. TEST STT + TTS ROUNDTRIP

Interactive microphone to Moonshine to Python to Pocket TTS to speaker:

```powershell
.\.venv\Scripts\python.exe .\tests\test_roundtrip.py --mode microphone --play
```

Non-interactive file round trip (the input is synthesized locally when `--input` is omitted):

```powershell
.\.venv\Scripts\python.exe .\tests\test_roundtrip.py --mode file
```

The response is exactly `You said: ` plus Moonshine's transcript and is written to `outputs\roundtrip.wav`.

## G. PROVE ZERO-INTERNET OPERATION

1. Disable Wi-Fi.
2. Disconnect Ethernet and VPN where appropriate under organization policy.
3. Run:

```powershell
.\scripts\run_all_tests.ps1
```

4. Expected result:

```text
OFFLINE STT: PASS
OFFLINE TTS: PASS
OFFLINE ROUNDTRIP: PASS
NETWORK ATTEMPTS: 0
```

The suite verifies bundle hashes, activates Hugging Face offline mode, blocks common Python socket/DNS connection paths, initializes both models from explicit local files, performs both inference paths, and completes a file-based round trip. For device acceptance too, run:

```powershell
.\scripts\run_all_tests.ps1 -IncludeMicrophone -PlayAudio
```

Physical/logical network disconnection is the definitive validation because Python monkey-patching cannot observe networking initiated entirely inside arbitrary native libraries.

## Repository layout

```text
voice_poc/
|-- README.md
|-- requirements.txt
|-- requirements-lock.txt
|-- docs/DEPENDENCY_NOTES.md
|-- scripts/
|   |-- prepare_online.ps1
|   |-- install_offline.ps1
|   |-- verify_bundle.ps1
|   `-- run_all_tests.ps1
|-- tools/
|   |-- download_models.py
|   |-- verify_checksums.py
|   `-- verify_no_network.py
|-- src/
|   |-- config.py
|   |-- offline.py
|   |-- stt/moonshine_stt.py
|   `-- tts/pocket_tts.py
|-- tests/
|   |-- test_stt_file.py
|   |-- test_stt_microphone.py
|   |-- test_tts.py
|   |-- test_roundtrip.py
|   `-- test_offline.py
|-- samples/README.md
`-- offline_bundle/
    |-- wheels/
    |-- models/moonshine/
    |-- models/pocket_tts/
    |-- voices/pocket_tts/
    |-- manifest.json          (generated)
    `-- SHA256SUMS.txt         (generated)
```

## Troubleshooting

- **Wrong Python version:** `py -3.11 --version` must report Python 3.11, and it must be 64-bit. Install Python only through an approved enterprise software channel.
- **Missing wheels:** rerun online preparation. A clean offline install must not fetch a missing dependency. `pip install` will fail because `PIP_NO_INDEX=1` is intentional.
- **Wrong wheel architecture:** prepare on Windows x64 with 64-bit Python 3.11. Do not prepare this Windows bundle on macOS or Linux.
- **Missing Moonshine files:** the error names the exact local directory. Re-transfer the complete bundle and run `scripts\verify_bundle.ps1`.
- **Missing Pocket TTS model/tokenizer:** verify `offline_bundle\models\pocket_tts` and checksums. There is no download fallback.
- **Missing voice asset:** verify `offline_bundle\voices\pocket_tts\alba.safetensors`. A bare voice name is never passed at runtime.
- **Microphone permission denied:** enable desktop microphone access under Windows Settings according to organization policy and confirm the intended default input device.
- **Audio device unavailable:** select/enable a Windows default input/output device. File STT/TTS tests do not require playback hardware.
- **Torch attempts a download:** this project passes only a local Pocket TTS YAML whose checkpoint and tokenizer values are absolute local paths. Confirm that the generated runtime YAML under `outputs\.runtime` contains no `hf://` or `https://` value. Keep `HF_HUB_OFFLINE=1`.
- **Hugging Face attempts a download:** check that `OFFLINE_MODE=1` and `HF_HUB_OFFLINE=1` are not being overridden, and do not replace the local voice path with `alba` or an `hf://` URL.
- **Checksum mismatch:** do not install. Re-transfer the bundle or rebuild it on the approved connected preparation machine.

## Scope and limitations

- English, one user, low concurrency, CPU only.
- Pocket TTS voice cloning is intentionally unavailable; the official no-voice-cloning checkpoint and built-in `alba` state avoid gated asset and runtime credential requirements.
- No LLM, server, API, Docker, FastAPI service, RAG, or production infrastructure is included.
- Intel Arc/NPU/OpenVINO optimization is deferred until the CPU baseline passes on the target laptop.

