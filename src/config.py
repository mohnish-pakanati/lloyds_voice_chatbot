"""Central, repository-relative configuration for the offline POC."""

from __future__ import annotations

import os
from pathlib import Path

from src.errors import OfflineConfigurationError, OfflineModelMissingError


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


REPOSITORY_ROOT = Path(
    os.environ.get("VOICE_POC_ROOT", Path(__file__).resolve().parents[1])
).resolve()
OFFLINE_BUNDLE_DIR = Path(
    os.environ.get("OFFLINE_BUNDLE_DIR", REPOSITORY_ROOT / "offline_bundle")
).resolve()

LANGUAGE = "en"
OFFLINE_MODE = _env_bool("OFFLINE_MODE", True)

MOONSHINE_MODEL = os.environ.get("MOONSHINE_MODEL", "medium").strip().lower()
_MOONSHINE_VARIANTS = {
    "medium": "medium-streaming-en",
    "medium-streaming": "medium-streaming-en",
    "small": "small-streaming-en",
    "small-streaming": "small-streaming-en",
}
if MOONSHINE_MODEL not in _MOONSHINE_VARIANTS:
    raise OfflineConfigurationError(
        "MOONSHINE_MODEL must be 'medium' or 'small' "
        f"(received {MOONSHINE_MODEL!r})."
    )

MOONSHINE_MODEL_DIR = OFFLINE_BUNDLE_DIR / "models" / "moonshine" / _MOONSHINE_VARIANTS[MOONSHINE_MODEL]
POCKET_TTS_MODEL_DIR = OFFLINE_BUNDLE_DIR / "models" / "pocket_tts"
POCKET_TTS_VOICE_DIR = OFFLINE_BUNDLE_DIR / "voices" / "pocket_tts"
POCKET_TTS_UPSTREAM_CONFIG = POCKET_TTS_MODEL_DIR / "upstream-english_2026-04.yaml"
POCKET_TTS_MODEL_FILE = POCKET_TTS_MODEL_DIR / "model.safetensors"
POCKET_TTS_TOKENIZER_FILE = POCKET_TTS_MODEL_DIR / "tokenizer.model"
POCKET_TTS_VOICE = os.environ.get("POCKET_TTS_VOICE", "alba")
POCKET_TTS_VOICE_FILE = POCKET_TTS_VOICE_DIR / f"{POCKET_TTS_VOICE}.safetensors"

OUTPUT_DIR = REPOSITORY_ROOT / "outputs"
RUNTIME_CONFIG_DIR = OUTPUT_DIR / ".runtime"


def apply_offline_environment() -> None:
    """Disable supported package network behavior and telemetry."""

    if not OFFLINE_MODE:
        return
    values = {
        "PIP_NO_INDEX": "1",
        "HF_HUB_OFFLINE": "1",
        "HF_HUB_DISABLE_TELEMETRY": "1",
        "DO_NOT_TRACK": "1",
    }
    for key, value in values.items():
        os.environ[key] = value


def require_local_file(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise OfflineModelMissingError(
            f"{label} is missing from the offline bundle: {resolved}"
        )
    return resolved


def require_local_directory(path: Path, label: str) -> Path:
    resolved = path.resolve()
    if not resolved.is_dir():
        raise OfflineModelMissingError(
            f"{label} directory is missing from the offline bundle: {resolved}"
        )
    return resolved


apply_offline_environment()

