# Dependency notes

Research date: 2026-09-20. Only the current official project repositories, documentation, package metadata, and model repositories were treated as authoritative.

## Moonshine Voice

| Field | Selected value |
|---|---|
| Package | `moonshine-voice==0.1.5` |
| Repository | <https://github.com/moonshine-ai/moonshine> |
| Package release | <https://pypi.org/project/moonshine-voice/0.1.5/> |
| Model | English Medium Streaming by default; English Small Streaming optional |
| Current Python API | `moonshine_voice.Transcriber(model_path=..., model_arch=ModelArch.MEDIUM_STREAMING)` and `transcribe_without_streaming()` |
| Model source | `https://download.moonshine.ai/model/...`; resolved by the package's current native dependency manifest |
| Selected Medium revision | `medium-streaming-en/quantized_26_08_21` |
| Medium required files | `adapter.ort`, `cross_kv.ort`, `decoder_kv.ort`, `encoder.ort`, `frontend.model.ort`, `frontend.weights.ort`, `streaming_config.json`, `tokenizer.bin` |
| Runtime backend | Moonshine native Windows library with its packaged ONNX Runtime, CPU |
| Local behavior | The low-level `Transcriber` accepts a directory directly and performs no download. The high-level `get_model_for_language()` downloads and caches, so it is used only by `tools/download_models.py` on the online machine. |

Moonshine's default cache is managed with `platformdirs`; a custom cache can be passed to `get_model_for_language(..., cache_root=...)`. This project does not depend on that cache at runtime. Preparation copies the returned model directory into the bundle and runtime passes that exact local directory to `Transcriber`.

The current streaming APIs use the `ModelArch.SMALL_STREAMING` and `ModelArch.MEDIUM_STREAMING` enum members. Older `moonshine-onnx`, Transformers pipeline, and legacy `DialogFlow` examples are not used.

## Kyutai Pocket TTS

| Field | Selected value |
|---|---|
| Package | `pocket-tts==3.1.0` |
| Repository | <https://github.com/kyutai-labs/pocket-tts> |
| Package release | <https://pypi.org/project/pocket-tts/3.1.0/> |
| Model | `english_2026-04`, official no-voice-cloning checkpoint |
| Model repository | <https://huggingface.co/kyutai/pocket-tts-without-voice-cloning> |
| Pinned model revision | `d29db7978e464fb90cb3359ee0c69a273b9142cc` |
| Model files | `languages/english_2026-04/model.safetensors` (219,029,196 bytes), `languages/english_2026-04/tokenizer.model` (59,339 bytes) |
| Voice | `alba` precomputed state, `languages/english_2026-04/embeddings/alba.safetensors` (6,194,424 bytes) |
| Current Python API | `TTSModel.load_model(config=<local yaml>)`, `get_state_for_audio_prompt(<local safetensors>)`, `generate_audio(...)` |
| Runtime backend | PyTorch CPU, 24 kHz mono output |
| Local behavior | Pocket TTS resolves `https://` and `hf://` values through `download_if_necessary()`. This project rewrites the packaged upstream YAML at runtime so every asset value is an absolute local filesystem path. The voice is passed as a `Path`, never as a predefined voice name or URL. |

The full voice-cloning checkpoint in `kyutai/pocket-tts` is gated and requires accepting publisher terms before downloading. That is incompatible with an unattended, credential-free bundle preparation flow. The selected official `pocket-tts-without-voice-cloning` checkpoint is not gated and is specifically paired with published precomputed voices. Voice cloning is outside this POC; synthesis with the built-in `alba` state remains supported.

Pocket TTS 3.1.0's packaged `english.yaml` maps the `english` alias to `english_2026-04`. Its source configuration pins the no-voice-cloning assets to the revision above. The project copies the exact package YAML into the model directory for traceability.

## Offline flags and enforcement

Relevant flags used at runtime:

- `PIP_NO_INDEX=1` prevents pip index access.
- `HF_HUB_OFFLINE=1` prevents Hugging Face Hub HTTP lookups.
- `HF_HUB_DISABLE_TELEMETRY=1` disables Hub telemetry.
- `DO_NOT_TRACK=1` is honored by Hugging Face ecosystem libraries.
- `OFFLINE_MODE=1` enables this project's socket guard.

Transformers is not in the runtime dependency set, so `TRANSFORMERS_OFFLINE` is deliberately not required. Moonshine's direct `Transcriber` path does not use its downloader or cache at runtime. Pocket TTS receives only ordinary local paths.

`hf-xet==1.5.2` is pinned and included because `huggingface-hub==1.32.0` declares it for supported Windows architectures. Runtime inference never invokes Xet or the Hub because all Pocket TTS assets are explicit local files and Hub offline mode is enforced.

The Python guard blocks `socket.create_connection`, `socket.socket.connect`, `socket.socket.connect_ex`, and DNS resolution through `socket.getaddrinfo`. It catches Python-level accidental networking. The definitive system-level proof remains running the full suite with Wi-Fi and Ethernet disconnected.

## CPU and Intel hardware

The first POC intentionally uses CPU inference. The Windows PyTorch wheel is CPU-capable and does not pull NVIDIA CUDA runtime wheels. Moonshine uses its packaged native CPU runtime. Intel Arc/NPU, OpenVINO, and ONNX export are potential later experiments, not prerequisites for this acceptance build.
