# Plain-English codebase guide

This document explains the project as if you are seeing Python for the first time.

## The 30-second explanation

This project does two jobs:

1. **Speech to text (STT):** Moonshine listens to a WAV file or microphone and produces words.
2. **Text to speech (TTS):** Pocket TTS takes words and produces a WAV file using the `alba` voice.

The round-trip test joins them together:

```text
Your voice
   -> Moonshine writes what you said
   -> Python adds "You said:"
   -> Pocket TTS speaks the answer
```

There is no chatbot intelligence or LLM yet. The Python response is deliberately just:

```python
response = "You said: " + transcript
```

## The easiest mental model

Think of the Git repository as the **instruction manual**. It contains readable source code, tests, and setup instructions.

Think of `offline_bundle` as a **sealed suitcase**. It contains:

- Python package wheels: the installers for every required Python package;
- Moonshine model files: the STT brain;
- Pocket TTS model files: the TTS brain;
- `alba.safetensors`: the selected voice;
- `manifest.json`: a packing list;
- `SHA256SUMS.txt`: tamper-detection fingerprints for the packed files.

The suitcase is large, so it is distributed as a GitHub Release ZIP rather than stored in the source-code repository.

Once the source and suitcase are on the laptop, installation and operation can happen without internet access.

## What happens from beginning to end

### A. A connected preparation machine builds the suitcase

```text
requirements-lock.txt
        +
official model sources
        |
        v
scripts/prepare_online.ps1
        |
        +-> downloads all Python wheels
        +-> downloads Moonshine files
        +-> downloads Pocket TTS files and the alba voice
        +-> tests a clean local-only package installation
        +-> writes manifest.json
        +-> writes and verifies SHA256SUMS.txt
        v
offline_bundle/
```

This is the only phase that is designed to use the internet.

### B. The enterprise laptop installs from local files

```text
offline_bundle/wheels
        |
        v
pip install --no-index
        |
        v
.venv (the project's private Python environment)
```

`--no-index` tells pip not to search PyPI. If a required package is missing from the suitcase, installation fails instead of going online.

### C. Speech recognition runs locally

```text
WAV file or microphone
        |
        v
MoonshineSTT
        |
        +-> checks that all eight required model files exist
        +-> loads them from offline_bundle/models/moonshine
        +-> blocks Python network connections
        v
transcript text
```

### D. Speech generation runs locally

```text
text + local alba voice
        |
        v
PocketTTS
        |
        +-> checks checkpoint, tokenizer, config, and voice files
        +-> rewrites the model config with absolute local paths
        +-> blocks Python network connections
        +-> generates audio on the CPU
        v
PCM16 WAV file
```

## Directory map

The source-code repository looks like this:

```text
lloyds_voice_chatbot/
|-- README.md                    How to install and run the POC
|-- requirements.txt            Three direct dependencies
|-- requirements-lock.txt       Exact versions of all dependencies
|-- .gitignore                  Files Git must not publish
|-- docs/
|   |-- CODEBASE_GUIDE.md        This beginner-friendly explanation
|   `-- DEPENDENCY_NOTES.md      Technical versions, sources, and API research
|-- scripts/                     PowerShell shortcuts for common workflows
|-- tools/                       Bundle-building and security-check utilities
|-- src/                         The actual STT/TTS application code
|-- tests/                       Small programs that prove each part works
`-- samples/README.md            How to supply an optional test recording
```

After the release ZIP is extracted, this generated directory also exists:

```text
offline_bundle/
|-- wheels/                      Local Python installers
|-- models/moonshine/            Local Moonshine model
|-- models/pocket_tts/           Local Pocket TTS model and tokenizer
|-- voices/pocket_tts/           Local alba voice state
|-- manifest.json                Bundle contents and provenance
`-- SHA256SUMS.txt               SHA-256 fingerprint for every packed file
```

`.venv/`, `offline_bundle/`, and `outputs/` are intentionally not committed to Git. They are installed, extracted, or generated locally.

## Every maintained file, in plain English

### Files at the top level

| File | Plain-English job |
|---|---|
| `README.md` | The operator's manual: download, install, test, and troubleshooting commands. |
| `requirements.txt` | The short shopping list: Moonshine Voice, Pocket TTS, and PyYAML. |
| `requirements-lock.txt` | The exact shopping receipt. It pins every direct and indirect package version so another machine gets the same set. |
| `.gitignore` | Prevents generated environments, downloaded models, output audio, caches, and other local files from entering the repository. |

### `docs/`

| File | Plain-English job |
|---|---|
| `CODEBASE_GUIDE.md` | Explains the project without assuming programming knowledge. |
| `docs/DEPENDENCY_NOTES.md` | Records the official projects, exact models, versions, download sources, runtime backends, and local-loading behavior. This is the technical audit trail. |

### `src/`: the application itself

| File | Plain-English job |
|---|---|
| `src/config.py` | The project's address book and offline switches. It calculates all paths from the repository root, selects medium/small Moonshine, selects `alba`, and sets offline/telemetry environment variables. |
| `src/errors.py` | Gives important failures clear names, such as “model file missing,” “unsafe offline configuration,” and “network blocked.” |
| `src/offline.py` | The Python-level network bouncer. While protected work is running, it intercepts DNS lookups and common socket connections, records attempts, and rejects them. |
| `src/stt/moonshine_stt.py` | The Moonshine adapter. It validates local assets, loads the streaming English model, records microphone audio when requested, transcribes samples/files, and reports timings. |
| `src/tts/pocket_tts.py` | The Pocket TTS adapter. It validates the model/tokenizer/config/voice, points the model at local files, generates audio, and writes a standard WAV. |
| `src/__init__.py` | Marks `src` as a Python package. It contains no business logic. |
| `src/stt/__init__.py` | Makes the STT classes easy to import. |
| `src/tts/__init__.py` | Makes the TTS classes easy to import. |

The two main application objects are:

```python
from src.stt import MoonshineSTT
from src.tts import PocketTTS

with MoonshineSTT() as stt:
    result = stt.transcribe_file("recording.wav")

tts = PocketTTS()
tts.synthesize("Hello", "answer.wav")
```

`TranscriptionResult` holds the transcript, audio duration, transcription time, and real-time factor. `SynthesisResult` holds the output path, generated duration, generation time, and real-time factor.

### `tests/`: runnable proofs

These are named “tests,” but they are also simple demonstration programs.

| File | Plain-English job |
|---|---|
| `tests/test_stt_file.py` | Loads Moonshine and transcribes one local WAV. Prints the text and timing measurements. |
| `tests/test_stt_microphone.py` | Records the default microphone for a chosen number of seconds, then transcribes it. |
| `tests/test_tts.py` | Speaks a known sentence, saves `outputs/tts_test.wav`, prints timings, and optionally plays it. |
| `tests/test_roundtrip.py` | Joins STT and TTS. It accepts a file or microphone, creates `"You said: ..."`, writes `outputs/roundtrip.wav`, and optionally plays it. |
| `tests/test_offline.py` | Runs the automatic local-only proof: initialize STT/TTS, generate speech, transcribe it, and generate the response. |
| `tests/_common.py` | Shared helper code for displaying timing values and playing WAV files. |
| `tests/__init__.py` | Marks the test directory as a Python package. |

The automatic offline test creates its own audio with Pocket TTS and feeds that WAV to Moonshine. That makes it repeatable and avoids storing a person's recording in Git.

### `tools/`: packaging and verification utilities

| File | Plain-English job |
|---|---|
| `tools/download_models.py` | Runs only on the connected preparation machine. Downloads the official pinned models and `alba` voice, copies them into controlled folders, and writes the manifest. |
| `tools/verify_checksums.py` | Creates or checks the bundle's SHA-256 fingerprints. It also checks that the manifest's model and voice files exist with the expected sizes. |
| `tools/verify_no_network.py` | First proves that the network blocker can catch a connection. It can then run STT and TTS while sockets are blocked and require zero attempted connections. |

### `scripts/`: PowerShell shortcuts

The Python files do the detailed work. These scripts arrange the commands in the correct order.

| File | Plain-English job |
|---|---|
| `scripts/prepare_online.ps1` | Builds a fresh suitcase on a connected Windows machine. It downloads wheels, proves they install locally, downloads models, creates checksums, and replaces the old bundle only after success. |
| `scripts/install_offline.ps1` | Checks Python 3.11 x64, verifies the suitcase, creates `.venv`, enables offline flags, and installs only from local wheels. |
| `scripts/verify_bundle.ps1` | A short wrapper around the checksum verifier. |
| `scripts/run_all_tests.ps1` | Rechecks the bundle, runs the socket-blocked offline suite, and can optionally add microphone and playback tests. |

Lloyds may block unsigned PowerShell scripts. That does not mean the Python application is broken. The README provides equivalent commands that can be typed directly without changing corporate execution policy.

### `samples/`

| File | Plain-English job |
|---|---|
| `samples/README.md` | Explains how to add `samples/sample.wav` for the standalone file test and warns not to commit confidential recordings. |

## How offline operation is enforced

“Offline” is protected and tested in several layers:

1. **Local package installation:** pip uses `--no-index` and `offline_bundle/wheels`. It cannot fill a missing dependency from PyPI.
2. **Offline environment flags:** Hugging Face offline mode and telemetry opt-out variables are set before models load.
3. **Explicit local paths:** both wrappers point at files inside `offline_bundle`; they do not pass public model names to a runtime downloader.
4. **Fail-closed asset checks:** a missing model or voice produces `OfflineModelMissingError`. There is no cloud fallback.
5. **Python socket blocker:** model loading and inference reject DNS and common outbound socket calls.
6. **Automated evidence:** the suite must finish with `NETWORK ATTEMPTS: 0`.
7. **System-level evidence:** the final acceptance test is run with Wi-Fi, Ethernet, and VPN disconnected as permitted by policy.

Important limits:

- The Python socket blocker watches common Python networking paths. It is useful evidence, but it is not a whole-machine firewall or packet capture.
- A checksum proves that files match the prepared bundle. It does not prove that a file is safe. Lloyds should still perform malware scanning, dependency vulnerability review, license review, code signing, and application allow-listing under its normal controls.
- The release ZIP is public. No Lloyds data, recordings, credentials, internal hostnames, or confidential configuration should ever be added to it.

## Why runtime configuration is created in `outputs/.runtime`

Pocket TTS ships a general configuration file. That file was designed to locate assets in several environments.

At startup, `PocketTTS` reads that template and writes a tiny local copy containing absolute paths to this laptop's checkpoint and tokenizer. Pocket TTS therefore knows exactly which local files to open regardless of the current working directory.

This generated file is temporary runtime plumbing, so it belongs in `outputs/.runtime`, not in source control.

## What to change later

| Future goal | Start here |
|---|---|
| Change default model, voice, path, or offline flag | `src/config.py` |
| Change how Moonshine receives or transcribes audio | `src/stt/moonshine_stt.py` |
| Change how Pocket TTS generates or saves audio | `src/tts/pocket_tts.py` |
| Change the spoken response | `tests/test_roundtrip.py` now; later move conversation logic into a new application module |
| Add another offline test | `tests/` |
| Change bundle contents or model revision | `tools/download_models.py`, then rebuild and re-verify the release bundle |
| Change package versions | `requirements.txt` and `requirements-lock.txt`, then rebuild and test the entire bundle |
| Change setup instructions | `README.md` |

## Things not to change casually

- Do not remove `--no-index` from offline installation commands.
- Do not replace local paths with Hugging Face model names at runtime.
- Do not add “download if missing” behavior.
- Do not weaken TLS or certificate checking on the online preparation machine.
- Do not edit a model, wheel, voice, manifest, or checksum inside a released bundle. Rebuild the bundle and issue new checksums instead.
- Do not commit `.venv`, `offline_bundle`, `outputs`, recordings, credentials, or Lloyds information.
- Do not claim the project is secure solely because `NETWORK ATTEMPTS: 0` appears. Keep the normal enterprise review controls too.

## Small glossary

| Term | Meaning |
|---|---|
| STT | Speech to text: audio becomes written words. |
| TTS | Text to speech: written words become audio. |
| Model | Learned numeric data that performs speech recognition or generation. It is the “brain,” not ordinary Python code. |
| Wheel (`.whl`) | A ready-made local installer for one Python package. |
| Virtual environment (`.venv`) | A private Python installation area for this project, kept separate from the rest of the laptop. |
| Checkpoint (`.safetensors`) | A file containing a model's learned numbers. |
| Tokenizer | Converts text into the smaller units a model understands. |
| PCM16 WAV | A common uncompressed audio format that Windows and Moonshine can read. |
| SHA-256 | A digital fingerprint. Any changed byte creates a different fingerprint. |
| Manifest | A packing list describing the bundle and its contents. |
| Real-time factor | Processing time divided by audio duration. Below `1.0` is faster than real time; above `1.0` is slower. |

## Five things to remember

1. The repository is the **instruction manual**; the release ZIP is the **offline suitcase**.
2. Moonshine turns local audio into text; Pocket TTS turns text into local audio.
3. Missing local files cause a clear failure. Nothing silently falls back to the cloud.
4. Checksums prove the suitcase was not changed; socket blocking and disconnected-network tests provide offline evidence.
5. The current response is only `"You said: ..."`. A real conversational brain can be added later, but it must follow the same local-only security rules.
