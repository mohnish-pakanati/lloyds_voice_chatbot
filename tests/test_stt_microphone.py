from __future__ import annotations

import argparse

try:
    from tests._common import metric
except ModuleNotFoundError:
    from _common import metric
from src.stt import MoonshineSTT


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture and transcribe the default microphone.")
    parser.add_argument("--seconds", type=float, default=5.0)
    args = parser.parse_args()
    print("Speak clearly after recording starts.")
    with MoonshineSTT() as stt:
        result = stt.transcribe_microphone(args.seconds)
        print(f"Transcript: {result.text}")
        print(f"Model load time: {stt.load_seconds:.3f} s")
        print(f"Transcription time: {result.transcription_seconds:.3f} s")
        print(f"Audio duration: {result.audio_duration_seconds:.3f} s")
        print(f"Real-time factor: {metric(result.real_time_factor)}")
    if not result.text:
        raise RuntimeError("No speech was recognized. Check the microphone and try again.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
