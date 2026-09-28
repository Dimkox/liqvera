"""Fail-closed validation for the pinned Adaptive Grok Build Pro gitlink."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

VERSION = "2.0.19"
TAG = "v2.0.19"
COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"
REPOSITORY = "https://github.com/Dimkox/adaptive-grok-build-pro.git"
SUBMODULE = Path("tooling/adaptive-grok-build-pro")


class ToolingPinError(RuntimeError):
    """The external tooling checkout does not match the Liqvera lock."""


def _run(root: Path, *args: str, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        list(args),
        cwd=cwd or root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip() or "command failed"
        raise ToolingPinError(detail)
    return completed.stdout.strip()


def validate(root: Path) -> Path:
    lock_path = root / "tooling/tooling-lock.json"
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        pin = lock["adaptive_grok_build_pro"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ToolingPinError("tooling lock is missing or invalid") from exc
    expected = {
        "version": VERSION,
        "tag": TAG,
        "commit": COMMIT,
        "repository": REPOSITORY,
        "release_asset_sha256": (
            "4176a872acdca873e840855d0b2c9e379cf8f796c9de69e5560b3e2bf85634b9"
        ),
    }
    if pin != expected:
        raise ToolingPinError("Adaptive Grok lock does not match the trusted Liqvera pin")

    source = root / SUBMODULE
    if not source.is_dir():
        raise ToolingPinError(
            "Adaptive Grok submodule is missing; run: git submodule update --init --recursive"
        )
    index = _run(root, "git", "ls-files", "-s", "--", str(SUBMODULE)).split()
    if len(index) < 2 or index[0] != "160000" or index[1] != COMMIT:
        raise ToolingPinError("Adaptive Grok gitlink does not match the locked commit")
    if _run(root, "git", "-C", str(source), "rev-parse", "HEAD") != COMMIT:
        raise ToolingPinError("Adaptive Grok checkout is not at the locked commit")
    if _run(root, "git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"):
        raise ToolingPinError("Adaptive Grok checkout is modified")
    if _run(root, "git", "-C", str(source), "rev-parse", f"{TAG}^{{}}") != COMMIT:
        raise ToolingPinError("Adaptive Grok tag does not resolve to the locked commit")
    try:
        actual_version = (source / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ToolingPinError("Adaptive Grok VERSION is unavailable") from exc
    if actual_version != VERSION:
        raise ToolingPinError("Adaptive Grok VERSION does not match the lock")
    return source
