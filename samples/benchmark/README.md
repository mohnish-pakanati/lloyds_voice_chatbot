# Accent benchmark clips

This is a compact, traceable evaluation set of 30 human-recorded English clips from the CSTR VCTK Corpus 0.92:

- 6 Indian English clips
- 18 UK clips (English regional, Scottish, Welsh, and Northern Irish)
- 6 Irish English clips

All files are under five seconds, far below the two-minute limit. They have been converted from the corpus's `mic1` FLAC source files to 16 kHz, mono PCM WAV for direct use with the repository's STT command. The conversion only resamples and re-encodes audio; it does not change spoken content.

`manifest.json` is the source of truth for each clip's transcript, self-declared accent and region, duration, SHA-256 digest, and source URLs. The source corpus is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); retain its attribution when redistributing these clips.

The clips are intended for local STT/TTS evaluation, not speaker identification or voice cloning.
