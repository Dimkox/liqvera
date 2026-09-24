#!/usr/bin/env python3
"""Verify salvage target bytes; check private source blobs when available."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

EXPECTED_HEAD = "7fe6918690f8bc1da5826c67e3619de4126e4f54"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_objects_available(repository_root: Path, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _blob_sha(repository_root: Path, commit: str, path: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", f"{commit}:{path}"],
        check=False,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise SystemExit(f"missing blob {commit}:{path}\n{completed.stderr}")
    return completed.stdout.strip()


def _parse_items(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    in_items = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("source_head:"):
            continue
        if line == "items:":
            in_items = True
            continue
        if line == "rejected:":
            if current:
                items.append(current)
                current = None
            break
        if not in_items:
            continue
        stripped = line.lstrip()
        if stripped.startswith("- "):
            if current:
                items.append(current)
            current = {}
            key, value = stripped[2:].split(":", 1)
            current[key.strip()] = value.strip()
        elif line.startswith(" ") and current is not None:
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        items.append(current)
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--repository-root", type=Path, default=Path("."))
    parser.add_argument("--require-source-objects", action="store_true")
    args = parser.parse_args()
    text = Path(args.manifest).read_text(encoding="utf-8")
    if "source_pr: 21" not in text:
        raise SystemExit("source_pr must be 21")
    if EXPECTED_HEAD not in text:
        raise SystemExit(f"source_head must be {EXPECTED_HEAD}")
    items = _parse_items(text)
    if not items:
        raise SystemExit("salvage items are required")
    for row in items:
        if len(row["source_blob_sha"]) != 40:
            raise SystemExit(f"invalid blob sha for {row['source_path']}")
        if not row["target"].startswith("packages/readonly-analyzer/"):
            raise SystemExit(f"target outside analyzer tree: {row['target']}")
        target = args.repository_root / row["target"]
        if not target.is_file():
            raise SystemExit(f"missing rewrite target {row['target']}")
        if _sha256(target) != row.get("target_sha256"):
            raise SystemExit(f"target sha256 mismatch for {row['target']}")
        if not row.get("rule", "").strip():
            raise SystemExit(f"missing rewrite rule for {row['source_path']}")
    source_objects_available = _source_objects_available(args.repository_root, EXPECTED_HEAD)
    if not source_objects_available and args.require_source_objects:
        raise SystemExit("required source objects are unavailable")
    if source_objects_available:
        for row in items:
            actual = _blob_sha(args.repository_root, EXPECTED_HEAD, row["source_path"])
            if actual != row["source_blob_sha"]:
                raise SystemExit(
                    f"blob mismatch {row['source_path']}: {actual} != {row['source_blob_sha']}"
                )
    source_status = "verified" if source_objects_available else "unavailable"
    print(f"pr21 salvage passed: items={len(items)} targets=verified source_objects={source_status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
