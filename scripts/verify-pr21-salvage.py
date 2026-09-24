#!/usr/bin/env python3
"""Verify salvage target bytes; check private source blobs when available."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml

EXPECTED_HEAD = "7fe6918690f8bc1da5826c67e3619de4126e4f54"
SCHEMA = Path(__file__).resolve().parents[1] / "architecture/schemas/salvage.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_objects_available(repository_root: Path, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        check=False,
        capture_output=True,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    return completed.returncode == 0


def _blob_sha(repository_root: Path, commit: str, path: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "blob", f"{commit}:{path}"],
        check=False,
        capture_output=True,
        env={**os.environ, "GIT_NO_LAZY_FETCH": "1"},
    )
    if completed.returncode != 0:
        return None
    payload = completed.stdout
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()


def _validate(value: Any, schema: dict[str, Any], label: str) -> None:
    kind = schema.get("type")
    if kind == "object":
        if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
            raise SystemExit(f"invalid salvage manifest: {label} must be a mapping")
        missing = set(schema.get("required", [])) - value.keys()
        if missing:
            raise SystemExit(f"invalid salvage manifest: {label} missing {', '.join(sorted(missing))}")
        properties = schema.get("properties", {})
        extra = value.keys() - properties.keys()
        if schema.get("additionalProperties") is False and extra:
            raise SystemExit(f"invalid salvage manifest: {label} has unsupported keys")
        for key, item in value.items():
            if key in properties:
                _validate(item, properties[key], f"{label}.{key}")
    elif kind == "array":
        if not isinstance(value, list) or len(value) < schema.get("minItems", 0):
            raise SystemExit(f"invalid salvage manifest: {label} must be a non-empty list")
        for index, item in enumerate(value):
            _validate(item, schema["items"], f"{label}[{index}]")
    elif kind == "string":
        if not isinstance(value, str) or len(value) < schema.get("minLength", 0):
            raise SystemExit(f"invalid salvage manifest: {label} must be a string")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise SystemExit(f"invalid salvage manifest: {label} has invalid format")
    elif kind == "integer" and type(value) is not int:
        raise SystemExit(f"invalid salvage manifest: {label} must be an integer")
    if "const" in schema and value != schema["const"]:
        raise SystemExit(f"invalid salvage manifest: {label} must be {schema['const']}")


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError, json.JSONDecodeError) as error:
        raise SystemExit(f"invalid salvage manifest: {error}") from error
    _validate(document, schema, "root")
    if document["source_head"] != EXPECTED_HEAD:
        raise SystemExit(f"invalid salvage manifest: source_head must be {EXPECTED_HEAD}")
    return document


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--require-source-objects", action="store_true")
    args = parser.parse_args()
    items = _load_manifest(Path(args.manifest))["items"]
    for row in items:
        target = args.repository_root / row["target"]
        if not target.is_file():
            raise SystemExit(f"missing rewrite target {row['target']}")
        if _sha256(target) != row["target_sha256"]:
            raise SystemExit(f"target sha256 mismatch for {row['target']}")
    source_objects_available = _source_objects_available(args.repository_root, EXPECTED_HEAD)
    if source_objects_available:
        for row in items:
            actual = _blob_sha(args.repository_root, EXPECTED_HEAD, row["source_path"])
            if actual is None:
                source_objects_available = False
                break
            if actual != row["source_blob_sha"]:
                raise SystemExit(
                    f"blob mismatch {row['source_path']}: {actual} != {row['source_blob_sha']}"
                )
    if not source_objects_available and args.require_source_objects:
        raise SystemExit("required source objects are unavailable")
    source_status = "verified" if source_objects_available else "unavailable"
    print(f"pr21 salvage passed: items={len(items)} targets=verified source_objects={source_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
