# WAV samples

Place an English, mono or stereo PCM WAV at `samples/sample.wav` for the standalone file-STT command. A 16 kHz mono WAV is ideal, although Moonshine's loader can handle common PCM WAV layouts.

The automated zero-network suite does not require a checked-in recording: Pocket TTS creates `outputs/offline_input.wav` locally, and Moonshine transcribes that file while sockets are blocked.

Do not place confidential recordings in source control.

