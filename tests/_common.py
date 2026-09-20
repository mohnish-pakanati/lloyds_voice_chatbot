from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def metric(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def play_wav(path: Path) -> None:
    import scipy.io.wavfile
    import sounddevice as sd

    sample_rate, audio = scipy.io.wavfile.read(path)
    sd.play(audio, sample_rate)
    sd.wait()

