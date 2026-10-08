# WAV samples

Place an English, mono or stereo PCM WAV at `samples/sample.wav` for the standalone file-STT command. A 16 kHz mono WAV is ideal, although Moonshine's loader can handle common PCM WAV layouts.

All 60 benchmark recordings were removed from the current repository at the user's request to reduce the size of the checked-out files. Audio under `samples/` is now ignored by Git. The original manifests, transcripts, licenses, and source attribution remain in `benchmark/` and `long_benchmark/` for reference or local regeneration.

The benchmark manifests describe the former audio sets; their WAV paths are not present in a fresh checkout. See [the longer benchmark notes](long_benchmark/README.md) for its original source and regeneration requirements. Deletion in a normal commit does not remove older audio blobs from Git history; history rewriting requires separate approval.

For example:

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_file.py --audio .\samples\sample.wav
```

The automated zero-network suite does not require a checked-in recording: Pocket TTS creates `outputs/offline_input.wav` locally, and Moonshine transcribes that file while sockets are blocked.

Do not place confidential recordings in source control.
