# Longer English accent recordings

The 30 WAV recordings have been removed from the current checkout at the user's request. The transcripts, manifest, license, and preparation tool remain. The description below documents the former set; audio examples and verification require local regeneration first. Regenerated recordings are ignored by Git.

30 real conversational recordings, each 30–120 seconds, with a predominance of English and Irish accents:

The originally prepared set ranges from **36.4 to 118.9 seconds**, totaling **34.1 minutes** across **9 speakers** (4 UK English, 4 Irish, 1 Indian-group speaker).

| Group | Recordings | Corpus accent label |
| --- | ---: | --- |
| UK English | 12 | Southern British English |
| Irish English | 12 | Irish English |
| Indian English | 6 | Indian English |

These are continuous speech turns or continuous excerpts, not stitched sentences, repeated audio, silence-padded recordings, or synthetic speech. The older short VCTK sentence set remains in `../benchmark/`.

## Files and use

- `clips/`: 16 kHz, mono, 16-bit PCM WAV files, suitable for the existing file-STT command.
- `transcripts/`: one reference `.txt` file per recording.
- `manifest.json`: transcripts, raw annotations, speaker/accent labels, durations, SHA-256 checksums, source links/revision, and excerpt timing details.
- `LICENSE-CC-BY-SA-4.0.txt`: the source corpus's full redistribution license.

For example, on the Lloyds laptop after regenerating the audio locally:

```powershell
.\.venv\Scripts\python.exe .\tests\test_stt_file.py --audio .\samples\long_benchmark\clips\edacc_test_03314.wav
```

Compare the output against `transcripts/edacc_test_03314.txt`. Normalize case, punctuation, and non-speech annotations consistently before calculating WER/CER; do not silently remove meaningful words or normalize away recognition errors. Report accent-specific results and word-weighted overall WER. Check long-utterance truncation, pauses, and latency as well as recognition accuracy.

These audio/reference pairs evaluate STT. Their text can supply TTS prompts, but naturalness and intelligibility of generated speech still need separate listening evaluation; these recordings alone do not measure TTS quality.

## Source, transformations, and limits

Source: [The Edinburgh International Accents of English Corpus (EdAcc)](https://doi.org/10.7488/ds/7914), the current replacement record with the corrected CC BY-SA license. Individual turns come from the [authors' dataset](https://huggingface.co/datasets/edinburghcstr/edacc/tree/d9ae7bd344f0562b766ec93ee5ce8f2f9568ce66), pinned to revision `d9ae7bd344f0562b766ec93ee5ce8f2f9568ce66`. Every clip links to its source row in the manifest.

Audio was decoded from the viewer WAV and resampled to 16 kHz PCM16. Turns within the duration limit are retained whole. Longer test turns are shortened near 90 seconds using word-timing anchors from the official `test/company.ctm`, aligned to matching spans of the original human reference. The company CTM is an ASR hypothesis: **its recognized words are not used as the reference transcript**. Excerpt references retain the corresponding span of the human transcript, including fillers. `_part02` files are non-overlapping second excerpts from the same source turn. Timing boundaries are alignment-based, not manually audited. Excerpts and original turn durations are explicitly identified in the manifest.

Angle-bracket non-speech annotations are removed from the scoring text; the raw text is retained. These are conversational video-call recordings and may contain background noise, hesitations, and overlapping speakers. The accent label identifies the primary speaker, not necessarily every voice audible in the clip. Multiple clips share speakers/conversations, so this small set is a smoke/regression test, not evidence of production readiness or accent fairness. Keep evaluation audio out of model training and check for pretraining overlap when interpreting scores.

The six longer Indian-group clips share one speaker, `EDACC-C34-A`, whom the corpus standardizes as **Indian English**; their self-described accent is **“Indian / Pakistani accent”**. Both labels are preserved. This is limited South Asian coverage, not six independent Indian speakers. Accent groups follow the corpus's standardized linguistic labels, not nationality or first-language assumptions.

## Attribution and license

Ramon Sanabria, Nikolay Bogoychev, Nina Markl, Andrea Carmantini, Ondrej Klejch and Peter Bell. *The Edinburgh International Accents of English Corpus*, ICASSP 2023. University of Edinburgh.

The recordings, transcripts, and this adapted subset are distributed under [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Preserve attribution, identify changes, and follow ShareAlike when redistributing adaptations. This data license is separate from the project's software license. Do not use the recordings for speaker impersonation or voice cloning.

## Data checks and rebuilding

Verify locally regenerated samples without loading any speech models:

```powershell
.\.venv\Scripts\python.exe .\tools\prepare_long_samples.py verify
```

Preparation dependencies are `requests`, `pyarrow`, `numpy`, `scipy`, and `soundfile`; these are not added to the offline runtime requirements. To rebuild, use `catalog` followed by `build`. The build also requires the official corpus's `test/text`, `test/segments`, and `test/company.ctm` files, placed in the chosen `--cache` directory under the names `test__text`, `test__segments`, and `test__company.ctm`. Preparation downloads only metadata and selected WAV byte ranges; it does not load STT/TTS models or retain the full corpus. Temporary preparation files are ignored by Git and can be deleted after delivery; they are not needed for using or verifying the samples.
