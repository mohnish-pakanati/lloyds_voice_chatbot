"""Prepare continuous EdAcc turns, without loading models or a full corpus into RAM.

Online dependencies: requests, pyarrow, numpy, scipy, soundfile.
Only small metadata columns and individually selected recordings are downloaded.
For build, place the official corpus test/text, test/segments and test/company.ctm
in --cache as test__text, test__segments and test__company.ctm respectively.
The existing checked-in recordings can be verified without these source files.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import math
import re
import time
import wave
from collections import Counter
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATASET = "edinburghcstr/edacc"
REVISION = "d9ae7bd344f0562b766ec93ee5ce8f2f9568ce66"
SOURCE = "https://doi.org/10.7488/ds/7914"
LICENSE_URL = "https://datashare.ed.ac.uk/server/api/core/bitstreams/bc7c247e-ae85-41cc-91a8-a1af06f4da29/content"
GROUPS = {"Southern British English": "uk_english", "Irish English": "irish_english", "Indian English": "indian_english"}
QUOTAS = {"uk_english": 12, "irish_english": 12, "indian_english": 6}
SESSION = requests.Session()


def get(url, **kwargs):
    for attempt in range(6):
        response = SESSION.get(url, timeout=(20, 40), **kwargs)
        if response.status_code in (429, 500, 502, 503, 504):
            response.close()
            time.sleep(min(5 * (attempt + 1), 30))
            continue
        response.raise_for_status()
        return response
    raise RuntimeError(f"Repeated download failure: {url}")


class RangeFile(io.RawIOBase):
    """Bounded HTTP reads let PyArrow skip large embedded audio columns."""
    def __init__(self, url, size):
        self.url, self.size, self.position = url, size, 0
        self.windows = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else (self.position if whence == 1 else self.size) + offset
        return self.position

    def read(self, count=-1):
        count = min(count if count >= 0 else self.size, self.size - self.position)
        if count <= 0:
            return b""
        start, end = self.position, self.position + count - 1
        for cached_start, data in self.windows:
            if cached_start <= start and end < cached_start + len(data):
                result = data[start - cached_start:end + 1 - cached_start]
                self.position += len(result)
                return result
        with get(self.url, stream=True, headers={"Range": f"bytes={start}-{end}"}, params={"range_request": f"{start}-{end}"}) as response:
            if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {start}-{end}/"):
                raise RuntimeError("Server did not honor bounded HTTP range request")
            data = response.content
        if len(data) != count:
            raise RuntimeError("Incomplete range response")
        self.position += len(data)
        return data


def catalog(cache):
    import pyarrow.parquet as pq

    rows, offsets = [], Counter()
    with get(f"https://huggingface.co/api/datasets/{DATASET}/tree/{REVISION}/data") as response:
        files = response.json()
    for item in files:
        path = item["path"]
        if not path.endswith(".parquet"):
            continue
        split = "validation" if "validation-" in path else "test"
        with RangeFile(f"https://huggingface.co/datasets/{DATASET}/resolve/{REVISION}/{path}", item["size"]) as source:
            parquet = pq.ParquetFile(source, pre_buffer=False)
            # Metadata columns are adjacent in every row group. Fetch one small
            # span per group and serve individual column reads from that span.
            for group_index in range(parquet.metadata.num_row_groups):
                columns = [parquet.metadata.row_group(group_index).column(i) for i in range(6)]
                starts = [min(c.data_page_offset, c.dictionary_page_offset) if c.has_dictionary_page else c.data_page_offset for c in columns]
                start = min(starts)
                end = max(s + c.total_compressed_size for s, c in zip(starts, columns))
                source.seek(start)
                source.windows.append((start, source.read(end - start)))
            for index, row in enumerate(parquet.read(columns=["speaker", "text", "accent", "raw_accent", "gender", "l1"], use_threads=False).to_pylist()):
                row.update(split=split, row_index=offsets[split] + index)
                if row["accent"] in GROUPS and len(row["text"]) >= 280:
                    row["accent_group"] = GROUPS[row["accent"]]
                    rows.append(row)
            offsets[split] += parquet.metadata.num_rows
        (cache / "catalog.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Scanned {path}; {len(rows)} long-turn candidates", flush=True)
    print("Candidates:", dict(Counter(row["accent"] for row in rows)), flush=True)


def build(cache, output):
    import soundfile as sf
    from scipy.signal import resample_poly

    (output / "clips").mkdir(parents=True, exist_ok=True)
    (output / "transcripts").mkdir(exist_ok=True)
    rows = [row for row in json.loads((cache / "catalog.json").read_text(encoding="utf-8")) if row["accent"] in GROUPS]
    rows.sort(key=lambda row: len(row["text"]), reverse=True)
    # The available long Indian turns are concentrated in one speaker.
    # Fall back to non-overlapping second excerpts only after trying all turns.
    rows += [dict(row, part=2) for row in rows if row["accent_group"] == "indian_english" and len(row["text"]) > 1600]
    source_text = {}
    required = [cache / f"test__{name}" for name in ("text", "segments", "company.ctm")]
    if not all(path.exists() for path in required):
        raise RuntimeError("Build needs the official test/text, test/segments and test/company.ctm annotations in --cache. See the module docstring; verify needs no source download.")
    for line in (cache / "test__text").read_text(encoding="utf-8").splitlines():
        identifier, text = line.split(maxsplit=1)
        source_text[" ".join(text.upper().split())] = identifier
    segments = {}
    for line in (cache / "test__segments").read_text(encoding="utf-8").splitlines():
        identifier, recording, start, end = line.split()
        segments[identifier] = (recording, float(start), float(end))
    timed_words = {}
    for line in (cache / "test__company.ctm").read_text(encoding="utf-8").splitlines():
        recording, channel, start, duration, word, *rest = line.split()
        timed_words.setdefault(recording, []).append((float(start), float(start) + float(duration), word.upper()))
    selected, counts, speakers = [], Counter(), Counter()
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        selected = json.loads(manifest_path.read_text(encoding="utf-8"))["clips"]
        counts.update(row["accent_group"] for row in selected)
        speakers.update(row["speaker_id"] for row in selected)
    selected_ids = {r["id"] for r in selected}
    for row in rows:
        group = row["accent_group"]
        identifier = f"edacc_{row['split']}_{row['row_index']:05d}" + ("_part02" if row.get("part") == 2 else "")
        if counts[group] >= QUOTAS[group] or speakers[row["speaker"]] >= (6 if group == "indian_english" else 4) or identifier in selected_ids:
            continue
        with get("https://datasets-server.huggingface.co/rows", params={"dataset": DATASET, "config": "default", "split": row["split"], "offset": row["row_index"], "length": 1}) as response:
            view = response.json()["rows"][0]["row"]
        if view["speaker"] != row["speaker"] or view["text"] != row["text"]:
            raise RuntimeError("Dataset viewer differs from pinned metadata")
        audio_url = view["audio"][0]["src"]
        print(f"Checking {row['split']} row {row['row_index']}: {row['accent']}", flush=True)
        with get(audio_url, headers={"Range": "bytes=0-99"}) as response:
            header = response.content
        if len(header) != 100:
            raise RuntimeError("Unexpected WAV header range")
        with wave.open(io.BytesIO(header)) as audio:
            sr, channels, width, frames = audio.getframerate(), audio.getnchannels(), audio.getsampwidth(), audio.getnframes()
            offset = audio._file.tell() + 8
        # WAV source turns can exceed two minutes. Read only the desired PCM
        # byte range, rather than downloading or decoding a whole conversation.
        source_duration = frames / sr
        raw = row["text"]
        start_seconds = 0
        end_seconds = source_duration
        alignment = None
        if source_duration > 120:
            if row["split"] != "test":
                continue
            source_id = source_text.get(" ".join(raw.upper().split()))
            if not source_id:
                raise RuntimeError("No original transcript match for timed excerpt")
            recording, segment_start, segment_end = segments[source_id]
            if abs(segment_end - segment_start - source_duration) > 0.1:
                raise RuntimeError("Original segment duration differs from viewer WAV")
            words = [w for w in timed_words[recording] if segment_start <= w[0] < segment_end]
            reference_tokens = raw.split()
            matcher = difflib.SequenceMatcher(None, [w[2] for w in words], reference_tokens, autojunk=False)
            # company.ctm is an ASR hypothesis, NOT the reference transcript.
            # Use its timings only; retain the human reference, including
            # fillers and corrections that the hypothesis omitted or mistook.
            lower = 90 if row.get("part") == 2 else 0
            upper = lower + 89.9
            anchors = [(block.a + j, block.b + j) for block in matcher.get_matching_blocks() if block.size >= 6 for j in range(block.size) if words[block.a + j][0] >= segment_start + lower and words[block.a + j][1] <= segment_start + upper]
            if not anchors:
                continue
            hypothesis_index, reference_index = anchors[-1]
            reference_start = 0
            if lower:
                hypothesis_start, reference_start = anchors[0]
                start_seconds = words[hypothesis_start][0] - segment_start - 0.025
                if hypothesis_start:
                    start_seconds = max(start_seconds, words[hypothesis_start - 1][1] - segment_start)
            end_seconds = words[hypothesis_index][1] - segment_start + 0.025
            if hypothesis_index + 1 < len(words):
                end_seconds = min(end_seconds, words[hypothesis_index + 1][0] - segment_start)
            raw = " ".join(reference_tokens[reference_start:reference_index + 1])
            alignment = {"source_utterance": source_id, "source_recording": recording, "source_recording_start_seconds": segment_start, "word_timing_source": "Official test/company.ctm ASR hypothesis; timing anchors matched to the original human reference (not ASR-generated reference text)", "reference_word_start_index": reference_start, "reference_word_count": reference_index + 1 - reference_start, "excerpt_start_seconds_in_turn": start_seconds, "excerpt_end_seconds_in_turn": end_seconds}
        if not 30 <= end_seconds - start_seconds <= 120:
            continue
        start_frame = round(start_seconds * sr)
        selected_frames = min(frames, round(end_seconds * sr)) - start_frame
        offset += start_frame * channels * width
        byte_end = offset + selected_frames * channels * width - 1
        with get(audio_url, headers={"Range": f"bytes={offset}-{byte_end}"}) as response:
            pcm = response.content
            if response.status_code != 206 or not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-{byte_end}/") or len(pcm) != selected_frames * channels * width:
                raise RuntimeError("Incomplete or incorrect WAV PCM range")
        wav = io.BytesIO()
        with wave.open(wav, "wb") as audio:
            audio.setparams((channels, width, sr, 0, "NONE", "not compressed"))
            audio.writeframes(pcm)
        data, sr = sf.read(io.BytesIO(wav.getvalue()), dtype="float32", always_2d=True)
        del pcm, wav
        data = data.mean(axis=1)
        if sr != 16000:
            factor = math.gcd(sr, 16000)
            data = resample_poly(data, 16000 // factor, sr // factor)
        path = output / "clips" / f"{identifier}.wav"
        sf.write(str(path), data, 16000, subtype="PCM_16")
        del data
        transcript = " ".join(re.sub(r"<[^>]+>", " ", raw).split())
        (output / "transcripts" / f"{identifier}.txt").write_text(transcript + "\n", encoding="utf-8")
        info = sf.info(str(path))
        selected.append({"id": identifier, "audio_file": f"clips/{identifier}.wav", "transcript_file": f"transcripts/{identifier}.txt", "speaker_id": row["speaker"], "accent": row["accent"], "region": row["raw_accent"], "accent_group": group, "transcript": transcript, "transcript_raw": raw, "duration_seconds": round(info.duration, 6), "sample_rate_hz": 16000, "channels": 1, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "source_dataset": DATASET, "source_revision": REVISION, "source_split": row["split"], "source_row_index": row["row_index"], "source_audio": audio_url.split("?")[0], "source_page": f"https://huggingface.co/datasets/{DATASET}/viewer/default/{row['split']}?row={row['row_index']}", "source_gender": row["gender"], "source_l1": row["l1"], "construction": "full continuous source turn; no concatenation, looping, time stretching, padding, or generated speech"})
        selected[-1]["source_turn_duration_seconds"] = source_duration
        if alignment:
            selected[-1]["construction"] = "continuous word-aligned excerpt; no concatenation, looping, time stretching, padding, or generated speech"
            selected[-1]["excerpt_alignment"] = alignment
        counts[group] += 1
        speakers[row["speaker"]] += 1
        manifest = {"dataset": "EdAcc continuous long-turn benchmark subset", "license": "CC-BY-SA-4.0", "license_url": "https://creativecommons.org/licenses/by-sa/4.0/", "source_corpus": SOURCE, "source_repository": f"https://huggingface.co/datasets/{DATASET}/tree/{REVISION}", "attribution": "Ramon Sanabria, Nikolay Bogoychev, Nina Markl, Andrea Carmantini, Ondrej Klejch and Peter Bell. The Edinburgh International Accents of English Corpus, ICASSP 2023. University of Edinburgh.", "conversion": "Viewer WAV decoded and resampled to 16 kHz mono PCM16 WAV. Full continuous source turns or continuous word-aligned excerpts retained. Excerpts use official test/company.ctm timings and retain their alignment metadata. Non-speech angle-bracket annotations omitted from scoring transcript; raw retained in transcript_raw.", "clips": selected}
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Selected {identifier}: {group}, {info.duration:.1f}s, {row['speaker']}; {dict(counts)}", flush=True)
        if dict(counts) == QUOTAS:
            break
    with get(LICENSE_URL) as response:
        (output / "LICENSE-CC-BY-SA-4.0.txt").write_bytes(response.content)
    if dict(counts) != QUOTAS:
        raise RuntimeError(f"Insufficient samples: {dict(counts)}; requested {QUOTAS}")
    verify(output)


def verify(output):
    import wave

    rows = json.loads((output / "manifest.json").read_text(encoding="utf-8"))["clips"]
    assert Counter(row["accent_group"] for row in rows) == Counter(QUOTAS), "Incorrect accent counts"
    assert len({row["id"] for row in rows}) == 30, "Missing or duplicate IDs"
    assert {f"clips/{p.name}" for p in (output / "clips").glob("*.wav")} == {r["audio_file"] for r in rows}, "Audio files differ from manifest"
    assert {f"transcripts/{p.name}" for p in (output / "transcripts").glob("*.txt")} == {r["transcript_file"] for r in rows}, "Transcript files differ from manifest"
    intervals = {}
    for row in rows:
        path = output / row["audio_file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"], f"Checksum mismatch: {path}"
        with wave.open(str(path)) as audio:
            duration = audio.getnframes() / audio.getframerate()
            assert (audio.getframerate(), audio.getnchannels(), audio.getsampwidth()) == (16000, 1, 2), f"Invalid WAV: {path}"
        assert 30 <= duration <= 120 and abs(duration - row["duration_seconds"]) <= 0.000001, f"Duration mismatch: {path}"
        assert (output / row["transcript_file"]).read_text(encoding="utf-8").strip() == row["transcript"], f"Transcript mismatch: {path}"
        assert GROUPS[row["accent"]] == row["accent_group"], f"Incorrect accent: {path}"
        alignment = row.get("excerpt_alignment", {})
        start = alignment.get("excerpt_start_seconds_in_turn", 0)
        end = alignment.get("excerpt_end_seconds_in_turn", row["source_turn_duration_seconds"])
        assert abs(end - start - duration) <= 0.0001, f"Incorrect excerpt timing: {path}"
        key = (row["source_split"], row["source_row_index"])
        for previous_start, previous_end in intervals.get(key, []):
            assert end <= previous_start or start >= previous_end, f"Overlapping excerpts: {path}"
        intervals.setdefault(key, []).append((start, end))
    print(f"Verified {len(rows)} clips; {sum(r['duration_seconds'] for r in rows) / 60:.1f} minutes; {min(r['duration_seconds'] for r in rows):.1f}–{max(r['duration_seconds'] for r in rows):.1f}s; {len({r['speaker_id'] for r in rows})} speakers", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["catalog", "build", "verify"])
    parser.add_argument("--cache", type=Path, default=ROOT / ".sample-prep-edacc-20261008")
    parser.add_argument("--output", type=Path, default=ROOT / "samples" / "long_benchmark")
    args = parser.parse_args()
    if args.stage == "verify":
        verify(args.output)
    else:
        args.cache.mkdir(parents=True, exist_ok=True)
        catalog(args.cache) if args.stage == "catalog" else build(args.cache, args.output)


if __name__ == "__main__":
    try:
        main()
    finally:
        SESSION.close()
