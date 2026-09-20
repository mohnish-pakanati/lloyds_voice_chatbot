#!/usr/bin/env python3
"""Download official model assets on the connected preparation machine only."""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.resources
import json
import os
import platform
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml
from huggingface_hub import hf_hub_download


POCKET_REPO = "kyutai/pocket-tts-without-voice-cloning"
POCKET_REVISION = "d29db7978e464fb90cb3359ee0c69a273b9142cc"
POCKET_LANGUAGE = "english_2026-04"
POCKET_FILES = {
    "model": f"languages/{POCKET_LANGUAGE}/model.safetensors",
    "tokenizer": f"languages/{POCKET_LANGUAGE}/tokenizer.model",
    "voice": f"languages/{POCKET_LANGUAGE}/embeddings/alba.safetensors",
}


def _copy_file(source: str | Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(source), destination)
    if not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError(f"Downloaded artifact is missing or empty: {destination}")


def download_moonshine(bundle: Path, selection: str) -> dict:
    from moonshine_voice import ModelArch
    from moonshine_voice.download import find_model_info, get_model_for_language

    arch = (
        ModelArch.MEDIUM_STREAMING
        if selection == "medium"
        else ModelArch.SMALL_STREAMING
    )
    destination = (
        bundle / "models" / "moonshine" / f"{selection}-streaming-en"
    )
    with tempfile.TemporaryDirectory(prefix="voice-poc-moonshine-") as cache:
        source, resolved_arch = get_model_for_language(
            "en", wanted_model_arch=arch, cache_root=Path(cache)
        )
        if resolved_arch != arch:
            raise RuntimeError(
                f"Moonshine returned {resolved_arch!r}; expected {arch!r}."
            )
        shutil.copytree(source, destination, dirs_exist_ok=False)

    model_info = find_model_info("en", arch)
    files = [
        {
            "path": path.relative_to(bundle).as_posix(),
            "size": path.stat().st_size,
        }
        for path in sorted(destination.rglob("*"))
        if path.is_file()
    ]
    if not files:
        raise RuntimeError("Moonshine downloader returned an empty model directory.")
    return {
        "package": "moonshine-voice",
        "architecture": f"{selection}-streaming",
        "language": "en",
        "source": model_info["download_url"],
        "runtime_backend": "Moonshine native library / ONNX Runtime CPU",
        "files": files,
    }


def download_pocket_tts(bundle: Path) -> tuple[dict, dict]:
    model_dir = bundle / "models" / "pocket_tts"
    voice_dir = bundle / "voices" / "pocket_tts"
    model_dir.mkdir(parents=True, exist_ok=False)
    voice_dir.mkdir(parents=True, exist_ok=False)

    with tempfile.TemporaryDirectory(prefix="voice-poc-hf-") as cache:
        downloaded = {
            key: hf_hub_download(
                repo_id=POCKET_REPO,
                filename=filename,
                revision=POCKET_REVISION,
                cache_dir=cache,
            )
            for key, filename in POCKET_FILES.items()
        }
        _copy_file(downloaded["model"], model_dir / "model.safetensors")
        _copy_file(downloaded["tokenizer"], model_dir / "tokenizer.model")
        _copy_file(downloaded["voice"], voice_dir / "alba.safetensors")

    upstream_resource = importlib.resources.files("pocket_tts").joinpath(
        "config", f"{POCKET_LANGUAGE}.yaml"
    )
    with importlib.resources.as_file(upstream_resource) as upstream_path:
        _copy_file(upstream_path, model_dir / f"upstream-{POCKET_LANGUAGE}.yaml")

    # This template is informational. Runtime code writes an equivalent YAML
    # with absolute local paths so it remains reliable from any working directory.
    with (model_dir / f"upstream-{POCKET_LANGUAGE}.yaml").open(
        "r", encoding="utf-8"
    ) as handle:
        local_config = yaml.safe_load(handle)
    local_config["weights_path"] = "model.safetensors"
    local_config["weights_path_without_voice_cloning"] = None
    local_config["flow_lm"]["lookup_table"]["tokenizer_path"] = "tokenizer.model"
    with (model_dir / "local-config-template.yaml").open(
        "w", encoding="utf-8", newline="\n"
    ) as handle:
        yaml.safe_dump(local_config, handle, sort_keys=False)

    model_files = [
        {
            "path": path.relative_to(bundle).as_posix(),
            "size": path.stat().st_size,
        }
        for path in sorted(model_dir.rglob("*"))
        if path.is_file()
    ]
    voice_path = voice_dir / "alba.safetensors"
    model_entry = {
        "package": "pocket-tts",
        "model": POCKET_LANGUAGE,
        "variant": "official no-voice-cloning checkpoint",
        "repository": POCKET_REPO,
        "revision": POCKET_REVISION,
        "runtime_backend": "PyTorch CPU",
        "files": model_files,
    }
    voice_entry = {
        "name": "alba",
        "format": "precomputed Pocket TTS model state",
        "repository": POCKET_REPO,
        "revision": POCKET_REVISION,
        "source_path": POCKET_FILES["voice"],
        "path": voice_path.relative_to(bundle).as_posix(),
        "size": voice_path.stat().st_size,
    }
    return model_entry, voice_entry


def installed_packages() -> dict[str, str]:
    names = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name")
        if name:
            names[name] = distribution.version
    return dict(sorted(names.items(), key=lambda item: item[0].lower()))


def wheel_inventory(bundle: Path) -> list[dict]:
    wheels = bundle / "wheels"
    entries = [
        {
            "path": path.relative_to(bundle).as_posix(),
            "size": path.stat().st_size,
        }
        for path in sorted(wheels.glob("*.whl"))
    ]
    if not entries:
        raise RuntimeError(f"No wheels were found in {wheels}")
    return entries


def write_manifest(bundle: Path, moonshine: dict, pocket: dict, voice: dict) -> None:
    manifest = {
        "bundle_format": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "preparation": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "operating_system": platform.platform(),
            "machine": platform.machine(),
        },
        "packages": installed_packages(),
        "wheels": wheel_inventory(bundle),
        "models": {"moonshine": moonshine, "pocket_tts": pocket},
        "voices": {"pocket_tts": voice},
        "runtime": {
            "python": "3.11.x, Windows x64",
            "language": "en",
            "device": "CPU",
            "offline_mode": True,
            "environment": {
                "PIP_NO_INDEX": "1",
                "HF_HUB_OFFLINE": "1",
                "HF_HUB_DISABLE_TELEMETRY": "1",
                "DO_NOT_TRACK": "1",
            },
            "network_fallbacks": False,
        },
    }
    with (bundle / "manifest.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True, type=Path)
    parser.add_argument("--moonshine-model", choices=("medium", "small"), default="medium")
    args = parser.parse_args()
    bundle = args.bundle_dir.resolve()
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError(f"Python 3.11 is required; found {platform.python_version()}")
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        raise RuntimeError("HF_HUB_OFFLINE=1 is set on the online preparation machine.")

    (bundle / "models" / "moonshine").mkdir(parents=True, exist_ok=True)
    (bundle / "voices").mkdir(parents=True, exist_ok=True)
    moonshine = download_moonshine(bundle, args.moonshine_model)
    pocket, voice = download_pocket_tts(bundle)
    write_manifest(bundle, moonshine, pocket, voice)
    print(f"Model assets and manifest created in {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
