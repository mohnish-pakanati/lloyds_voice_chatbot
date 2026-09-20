from __future__ import annotations

try:
    from tests._common import ROOT
except ModuleNotFoundError:
    from _common import ROOT
from src.stt import MoonshineSTT
from src.tts import PocketTTS


def run_offline_suite() -> None:
    outputs = ROOT / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    stt = MoonshineSTT()
    print("OFFLINE STT INITIALIZATION: PASS")

    tts = PocketTTS()
    print("OFFLINE TTS INITIALIZATION: PASS")
    seed = tts.synthesize("Hello, can you hear me?", outputs / "offline_input.wav")
    if not seed.output_path.is_file() or seed.audio_duration_seconds <= 0:
        raise RuntimeError("Pocket TTS offline inference produced no audio.")
    print("OFFLINE TTS: PASS")

    try:
        transcription = stt.transcribe_file(seed.output_path)
    finally:
        stt.close()
    if not transcription.text:
        raise RuntimeError("Moonshine offline transcription returned empty text.")
    print("OFFLINE STT: PASS")

    response = "You said: " + transcription.text
    roundtrip = tts.synthesize(response, outputs / "offline_roundtrip.wav")
    if not roundtrip.output_path.is_file() or roundtrip.audio_duration_seconds <= 0:
        raise RuntimeError("Offline round trip produced no audio.")
    print("OFFLINE ROUNDTRIP: PASS")


if __name__ == "__main__":
    run_offline_suite()
