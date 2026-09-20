from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tests._common import ROOT, play_wav
except ModuleNotFoundError:
    from _common import ROOT, play_wav
from src.stt import MoonshineSTT
from src.tts import PocketTTS


def run_file_roundtrip(input_path: Path | None, play: bool) -> Path:
    tts = PocketTTS()
    if input_path is None:
        input_path = ROOT / "outputs" / "roundtrip_input.wav"
        tts.synthesize("Hello, can you hear me?", input_path)
    with MoonshineSTT() as stt:
        transcription = stt.transcribe_file(input_path)
    if not transcription.text:
        raise RuntimeError("Moonshine returned an empty round-trip transcript.")
    response = "You said: " + transcription.text
    output = ROOT / "outputs" / "roundtrip.wav"
    tts.synthesize(response, output)
    print(f"Transcript: {transcription.text}")
    print(f"Response: {response}")
    print(f"Output: {output}")
    if play:
        play_wav(output)
    return output


def run_microphone_roundtrip(seconds: float, play: bool) -> Path:
    with MoonshineSTT() as stt:
        transcription = stt.transcribe_microphone(seconds)
    if not transcription.text:
        raise RuntimeError("Moonshine returned an empty microphone transcript.")
    response = "You said: " + transcription.text
    output = ROOT / "outputs" / "roundtrip.wav"
    PocketTTS().synthesize(response, output)
    print(f"Transcript: {transcription.text}")
    print(f"Response: {response}")
    print(f"Output: {output}")
    if play:
        play_wav(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Local Moonshine to Pocket TTS round trip.")
    parser.add_argument("--mode", choices=("file", "microphone"), default="file")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--play", action="store_true")
    args = parser.parse_args()
    if args.mode == "microphone":
        run_microphone_roundtrip(args.seconds, args.play)
    else:
        run_file_roundtrip(args.input.resolve() if args.input else None, args.play)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
