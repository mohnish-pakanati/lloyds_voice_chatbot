"""Local-only wrapper around the current Moonshine Voice Python API."""

from __future__ import annotations

import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from src import config
from src.errors import OfflineModelMissingError
from src.offline import network_blocked


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    audio_duration_seconds: float
    transcription_seconds: float

    @property
    def real_time_factor(self) -> float | None:
        if self.audio_duration_seconds <= 0:
            return None
        return self.transcription_seconds / self.audio_duration_seconds


class MoonshineSTT:
    """Moonshine Medium/Small Streaming loaded directly from a local directory."""

    _REQUIRED_FILES = {
        "adapter.ort",
        "cross_kv.ort",
        "decoder_kv.ort",
        "encoder.ort",
        "frontend.model.ort",
        "frontend.weights.ort",
        "streaming_config.json",
        "tokenizer.bin",
    }

    def __init__(self, model_dir: str | Path | None = None, model: str | None = None):
        config.apply_offline_environment()
        self.model_name = (model or config.MOONSHINE_MODEL).strip().lower()
        self.model_dir = Path(model_dir or config.MOONSHINE_MODEL_DIR).resolve()
        self.load_seconds = 0.0
        self._transcriber = None
        self._validate_assets()
        self._load()

    def _validate_assets(self) -> None:
        if not self.model_dir.is_dir():
            raise OfflineModelMissingError(
                "Moonshine model files are missing from " f"{self.model_dir}"
            )
        missing = sorted(
            name for name in self._REQUIRED_FILES if not (self.model_dir / name).is_file()
        )
        if missing:
            raise OfflineModelMissingError(
                f"Moonshine model directory {self.model_dir} is incomplete; "
                f"missing: {', '.join(missing)}"
            )

    def _load(self) -> None:
        from moonshine_voice import ModelArch, Transcriber

        arch_by_name = {
            "medium": ModelArch.MEDIUM_STREAMING,
            "medium-streaming": ModelArch.MEDIUM_STREAMING,
            "small": ModelArch.SMALL_STREAMING,
            "small-streaming": ModelArch.SMALL_STREAMING,
        }
        if self.model_name not in arch_by_name:
            raise ValueError("Moonshine model must be 'medium' or 'small'.")
        started = time.perf_counter()
        with network_blocked(config.OFFLINE_MODE):
            self._transcriber = Transcriber(
                model_path=str(self.model_dir), model_arch=arch_by_name[self.model_name]
            )
        self.load_seconds = time.perf_counter() - started

    def transcribe_samples(
        self, audio: Iterable[float] | np.ndarray, sample_rate: int
    ) -> TranscriptionResult:
        samples = np.asarray(audio, dtype=np.float32).reshape(-1)
        duration = float(samples.size) / float(sample_rate) if sample_rate else 0.0
        started = time.perf_counter()
        with network_blocked(config.OFFLINE_MODE):
            transcript = self._transcriber.transcribe_without_streaming(
                samples.tolist(), sample_rate=int(sample_rate)
            )
        elapsed = time.perf_counter() - started
        text = " ".join(
            line.text.strip() for line in transcript.lines if line.text and line.text.strip()
        ).strip()
        return TranscriptionResult(text, duration, elapsed)

    def transcribe_file(self, audio_path: str | Path) -> TranscriptionResult:
        from moonshine_voice import load_wav_file

        path = Path(audio_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Input WAV does not exist: {path}")
        audio, sample_rate = load_wav_file(str(path))
        return self.transcribe_samples(audio, sample_rate)

    def transcribe_microphone(
        self, duration_seconds: float = 5.0, sample_rate: int = 16000
    ) -> TranscriptionResult:
        import sounddevice as sd

        print(f"Recording {duration_seconds:.1f} seconds from the default microphone...")
        recording = sd.rec(
            int(duration_seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        return self.transcribe_samples(recording[:, 0], sample_rate)

    @staticmethod
    def wav_duration(audio_path: str | Path) -> float:
        with wave.open(str(audio_path), "rb") as wav_file:
            return wav_file.getnframes() / float(wav_file.getframerate())

    def close(self) -> None:
        if self._transcriber is not None:
            self._transcriber.close()
            self._transcriber = None

    def __enter__(self) -> "MoonshineSTT":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

