from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tests._common import ROOT, metric, play_wav
except ModuleNotFoundError:
    from _common import ROOT, metric, play_wav
from src.tts import PocketTTS


DEFAULT_TEXT = (
    "Hello. This is a completely local text to speech test. "
    "No external speech service is being used."
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a WAV with local Pocket TTS.")
    parser.add_argument("--output", default=str(ROOT / "outputs" / "tts_test.wav"))
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument("--play", action="store_true")
    args = parser.parse_args()
    tts = PocketTTS()
    result = tts.synthesize(args.text, args.output)
    print(f"Model + voice load time: {tts.load_seconds:.3f} s")
    print(f"Generation time: {result.generation_seconds:.3f} s")
    print(f"Generated audio duration: {result.audio_duration_seconds:.3f} s")
    print(f"Real-time factor: {metric(result.real_time_factor)}")
    print(f"Output path: {result.output_path}")
    if not Path(result.output_path).is_file() or Path(result.output_path).stat().st_size <= 44:
        raise RuntimeError("Pocket TTS did not produce a valid non-empty WAV.")
    if args.play:
        play_wav(result.output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
