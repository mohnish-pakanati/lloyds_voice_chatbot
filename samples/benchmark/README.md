# Accent benchmark clips

The 30 WAV recordings have been removed from the current checkout at the user's request. The manifest and attribution are retained. The description below documents the former set; restore or prepare the audio locally before using its file paths.

This is a compact, traceable evaluation set of 30 human-recorded English clips from the CSTR VCTK Corpus 0.92:

- 6 Indian English clips
- 18 UK clips (English regional, Scottish, Welsh, and Northern Irish)
- 6 Irish English clips

These are short sentence recordings (approximately 4–12 seconds). They have been converted from the corpus's `mic1` FLAC source files to 16 kHz, mono PCM WAV for direct use with the repository's STT command. The conversion only resamples and re-encodes audio; it does not change spoken content.

For longer continuous recordings, use [the long benchmark](../long_benchmark/README.md).

`manifest.json` is the source of truth for each clip's transcript, self-declared accent and region, duration, SHA-256 digest, and source URLs. The source corpus is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); retain its attribution when redistributing these clips.

The clips are intended for local STT/TTS evaluation, not speaker identification or voice cloning.
