# WAV samples

Place an English, mono or stereo PCM WAV at `samples/sample.wav` for the standalone file-STT command. A 16 kHz mono WAV is ideal, although Moonshine's loader can handle common PCM WAV layouts.

`benchmark/` contains 30 short, human-recorded English WAVs prepared for repeatable accent coverage checks. They are 16 kHz, mono, PCM WAV files and each has an authoritative source transcript in `benchmark/manifest.json`.

For example:

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_file.py --audio .\samples\benchmark\clips\p248_003.wav
```

The automated zero-network suite does not require a checked-in recording: Pocket TTS creates `outputs/offline_input.wav` locally, and Moonshine transcribes that file while sockets are blocked.

Do not place confidential recordings in source control.
