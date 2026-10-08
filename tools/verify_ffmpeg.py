"""Verify optional offline FFmpeg wheels and a real audio conversion, without models."""
from __future__ import annotations

import array
import hashlib
import math
import os
from pathlib import Path
import subprocess
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
WHEELHOUSE = ROOT / "vendor" / "ffmpeg" / "wheels"
HASHES = {
    "ffmpeg_python-0.2.0-py3-none-any.whl": "ac441a0404e053f8b6a1113a77c0f452f1cfc62f6344a769475ffdc0f56c23c5",
    "future-1.0.0-py3-none-any.whl": "929292d34f5872e70396626ef385ec22355a1fae8ad29e1a734c3e43f9fbc216",
    "imageio_ffmpeg-0.6.0-py3-none-win_amd64.whl": "02fa47c83703c37df6bfe4896aab339013f62bf02c5ebf2dce6da56af04ffc0a",
}


def main() -> None:
    if os.name != "nt":
        raise RuntimeError("This wheel set contains a Windows x64 executable.")
    for filename, expected in HASHES.items():
        path = WHEELHOUSE / filename
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise RuntimeError(f"Wheel checksum mismatch: {filename}")
    print("Wheel checksums: PASS (3 unmodified PyPI wheels)")

    try:
        import ffmpeg
        import imageio_ffmpeg
    except ImportError as error:
        raise RuntimeError("Install vendor/ffmpeg/requirements.txt from its local wheels first.") from error
    if not hasattr(ffmpeg, "input"):
        raise RuntimeError("Wrong ffmpeg module installed; this tool needs ffmpeg-python.")
    # Test the bundled executable, not an unrelated PATH/Conda/environment override.
    executable = Path(imageio_ffmpeg.__file__).resolve().parent / "binaries" / "ffmpeg-win-x86_64-v7.1.exe"
    flags = subprocess.CREATE_NO_WINDOW
    version = subprocess.run([str(executable), "-version"], check=True, capture_output=True, text=True, timeout=20, creationflags=flags)
    print(version.stdout.splitlines()[0])
    with tempfile.TemporaryDirectory(prefix="lloyds-ffmpeg-check-") as temporary:
        source = Path(temporary) / "input.wav"
        target = Path(temporary) / "output.wav"
        # A generated, one-second test signal; no person's recording or STT/TTS model.
        samples = array.array("h")
        for index in range(44100):
            value = round(8000 * math.sin(2 * math.pi * 440 * index / 44100))
            samples.extend((value, value))
        with wave.open(str(source), "wb") as audio:
            audio.setparams((2, 2, 44100, 0, "NONE", "not compressed"))
            audio.writeframes(samples.tobytes())
        stream = ffmpeg.input(str(source)).output(str(target), ac=1, ar=16000, acodec="pcm_s16le")
        command = ffmpeg.compile(stream, cmd=str(executable), overwrite_output=True)
        subprocess.run(command, check=True, capture_output=True, timeout=20, creationflags=flags)
        with wave.open(str(target), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getnframes()) != (1, 2, 16000, 16000):
                raise RuntimeError("Conversion produced an unexpected WAV format or duration.")
            converted = array.array("h", audio.readframes(audio.getnframes()))
        if max(abs(value) for value in converted) < 1000:
            raise RuntimeError("Conversion unexpectedly produced silent audio.")
    print("Audio conversion: PASS (44.1 kHz stereo -> 16 kHz mono PCM16)")
    print("No models loaded; verification subprocesses terminated and temporary test audio removed.")


if __name__ == "__main__":
    main()
