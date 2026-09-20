"""Local-only wrapper around Kyutai Pocket TTS 3.1.0."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml

from src import config
from src.errors import OfflineModelMissingError
from src.offline import network_blocked


@dataclass(frozen=True)
class SynthesisResult:
    output_path: Path
    audio_duration_seconds: float
    generation_seconds: float

    @property
    def real_time_factor(self) -> float | None:
        if self.audio_duration_seconds <= 0:
            return None
        return self.generation_seconds / self.audio_duration_seconds


class PocketTTS:
    """Pocket TTS using an explicit local checkpoint, tokenizer, and voice state."""

    def __init__(
        self,
        model_dir: str | Path | None = None,
        voice_file: str | Path | None = None,
    ):
        config.apply_offline_environment()
        self.model_dir = Path(model_dir or config.POCKET_TTS_MODEL_DIR).resolve()
        self.voice_file = Path(voice_file or config.POCKET_TTS_VOICE_FILE).resolve()
        self.model_file = self.model_dir / "model.safetensors"
        self.tokenizer_file = self.model_dir / "tokenizer.model"
        self.upstream_config = self.model_dir / "upstream-english_2026-04.yaml"
        self.load_seconds = 0.0
        self._model = None
        self._voice_state = None
        self._validate_assets()
        self._load()

    def _validate_assets(self) -> None:
        required = {
            "Pocket TTS checkpoint": self.model_file,
            "Pocket TTS tokenizer": self.tokenizer_file,
            "Pocket TTS upstream config": self.upstream_config,
            "Pocket TTS local voice state": self.voice_file,
        }
        missing = [f"{label}: {path}" for label, path in required.items() if not path.is_file()]
        if missing:
            raise OfflineModelMissingError(
                "Pocket TTS assets are missing from the offline bundle:\n- "
                + "\n- ".join(missing)
            )

    def _write_runtime_config(self) -> Path:
        with self.upstream_config.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
        data["weights_path"] = str(self.model_file)
        data["weights_path_without_voice_cloning"] = None
        data["flow_lm"]["lookup_table"]["tokenizer_path"] = str(self.tokenizer_file)
        data["flow_lm"]["weights_path"] = None
        data["mimi"]["weights_path"] = None
        config.RUNTIME_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        path = config.RUNTIME_CONFIG_DIR / "pocket-tts-english_2026-04.local.yaml"
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
        return path

    def _load(self) -> None:
        from pocket_tts import TTSModel

        runtime_config = self._write_runtime_config()
        started = time.perf_counter()
        with network_blocked(config.OFFLINE_MODE):
            self._model = TTSModel.load_model(config=runtime_config)
            # The selected official checkpoint intentionally omits voice cloning.
            self._model.has_voice_cloning = False
            self._voice_state = self._model.get_state_for_audio_prompt(self.voice_file)
        self.load_seconds = time.perf_counter() - started

    @property
    def sample_rate(self) -> int:
        return int(self._model.sample_rate)

    def synthesize(self, text: str, output_path: str | Path) -> SynthesisResult:
        import scipy.io.wavfile

        if not text.strip():
            raise ValueError("Text for speech synthesis must not be empty.")
        destination = Path(output_path).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        with network_blocked(config.OFFLINE_MODE):
            audio = self._model.generate_audio(self._voice_state, text)
        elapsed = time.perf_counter() - started
        values = audio.detach().cpu().numpy().reshape(-1)
        # The official API returns float PCM. Persist standard signed PCM16 so
        # Moonshine's WAV loader and Windows media tools accept the same file.
        pcm16 = (np.clip(values, -1.0, 1.0) * 32767.0).astype(np.int16)
        scipy.io.wavfile.write(destination, self.sample_rate, pcm16)
        duration = pcm16.size / float(self.sample_rate)
        return SynthesisResult(destination, duration, elapsed)
