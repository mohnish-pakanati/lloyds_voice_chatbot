#!/usr/bin/env python3
"""Generate or verify the complete offline bundle SHA-256 inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


CHECKSUM_NAME = "SHA256SUMS.txt"


def files_to_hash(bundle: Path) -> list[Path]:
    return sorted(
        path
        for path in bundle.rglob("*")
        if path.is_file() and path.name not in {CHECKSUM_NAME, ".gitkeep"}
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate(bundle: Path) -> None:
    entries = [
        f"{sha256(path)}  {path.relative_to(bundle).as_posix()}"
        for path in files_to_hash(bundle)
    ]
    if not entries:
        raise RuntimeError(f"Refusing to generate an empty checksum file for {bundle}")
    (bundle / CHECKSUM_NAME).write_text("\n".join(entries) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} SHA-256 entries.")


def parse_checksum_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"Checksum file is missing: {path}")
    entries: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        parts = raw.split("  ", 1)
        if len(parts) != 2 or len(parts[0]) != 64:
            raise ValueError(f"Malformed checksum line {line_number}: {raw!r}")
        entries[parts[1]] = parts[0].lower()
    return entries


def validate_manifest(bundle: Path) -> None:
    path = bundle / "manifest.json"
    if not path.is_file():
        raise FileNotFoundError(f"Bundle manifest is missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("bundle_format") != 1:
        raise ValueError("Unsupported or missing bundle_format in manifest.json")
    for name in ("moonshine", "pocket_tts"):
        for entry in data["models"][name]["files"]:
            artifact = bundle / entry["path"]
            if not artifact.is_file() or artifact.stat().st_size != entry["size"]:
                raise ValueError(f"Manifest artifact missing or wrong size: {artifact}")
    voice = data["voices"]["pocket_tts"]
    voice_path = bundle / voice["path"]
    if not voice_path.is_file() or voice_path.stat().st_size != voice["size"]:
        raise ValueError(f"Manifest voice artifact missing or wrong size: {voice_path}")
    if not data.get("wheels"):
        raise ValueError("Manifest contains no wheels.")


def verify(bundle: Path) -> None:
    expected = parse_checksum_file(bundle / CHECKSUM_NAME)
    actual_paths = {
        path.relative_to(bundle).as_posix(): path for path in files_to_hash(bundle)
    }
    missing_from_sums = sorted(set(actual_paths) - set(expected))
    absent_files = sorted(set(expected) - set(actual_paths))
    if missing_from_sums:
        raise ValueError(f"Files not covered by checksums: {missing_from_sums}")
    if absent_files:
        raise ValueError(f"Checksum entries refer to missing files: {absent_files}")
    failures = []
    for relative, path in actual_paths.items():
        actual = sha256(path)
        if actual != expected[relative]:
            failures.append(relative)
    if failures:
        raise ValueError(f"SHA-256 mismatch: {failures}")
    validate_manifest(bundle)
    print(f"BUNDLE CHECKSUMS: PASS ({len(expected)} files)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args()
    bundle = args.bundle_dir.resolve()
    if args.generate:
        generate(bundle)
    else:
        verify(bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

