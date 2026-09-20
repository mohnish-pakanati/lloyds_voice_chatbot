from __future__ import annotations

import argparse

try:
    from tests._common import ROOT, metric
except ModuleNotFoundError:
    from _common import ROOT, metric
from src.stt import MoonshineSTT


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe one local WAV with Moonshine.")
    parser.add_argument("--audio", default=str(ROOT / "samples" / "sample.wav"))
    args = parser.parse_args()
    with MoonshineSTT() as stt:
        result = stt.transcribe_file(args.audio)
        print(f"Transcript: {result.text}")
        print(f"Model load time: {stt.load_seconds:.3f} s")
        print(f"Transcription time: {result.transcription_seconds:.3f} s")
        print(f"Audio duration: {result.audio_duration_seconds:.3f} s")
        print(f"Real-time factor: {metric(result.real_time_factor)}")
    if not result.text:
        raise RuntimeError("Moonshine returned an empty transcript.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
