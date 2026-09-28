#!/usr/bin/env python3
"""Validate and execute the pinned Adaptive Grok Build Pro gitlink."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

VERSION = "2.0.19"
TAG = "v2.0.19"
COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"
REPOSITORY = "https://github.com/Dimkox/adaptive-grok-build-pro.git"
SUBMODULE = Path("tooling/adaptive-grok-build-pro")
SCRIPTS = {
    "grok_approve.py",
    "grok_change.py",
    "grok_deploy.py",
    "grok_doctor.py",
    "grok_review.py",
    "grok_route.py",
    "grok_status.py",
    "grok_verify.py",
}
HOOKS = {
    "post_tool_use.py",
    "pre_compact.py",
    "pre_tool_use.py",
    "session_end.py",
    "session_start.py",
    "stop_gate.py",
    "subagent_start.py",
    "subagent_stop.py",
    "user_prompt_submit.py",
}


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


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def main() -> int:
    root = _root()
    try:
        source = validate(root)
    except ToolingPinError as exc:
        print(f"Adaptive Grok pin validation failed: {exc}", file=sys.stderr)
        return 2

    invoked = Path(sys.argv[0]).name
    arguments = sys.argv[1:]
    if invoked in SCRIPTS:
        target = source / "scripts" / invoked
    elif arguments[:1] == ["--hook"] and len(arguments) >= 2 and arguments[1] in HOOKS:
        target = source / ".grok/hooks" / arguments[1]
        arguments = arguments[2:]
    elif arguments == ["--check"]:
        print(json.dumps({"version": VERSION, "tag": TAG, "commit": COMMIT}, sort_keys=True))
        return 0
    else:
        print("Adaptive Grok entrypoint is not allowed", file=sys.stderr)
        return 2
    if not target.is_file() or target.is_symlink():
        print(f"Adaptive Grok entrypoint is unavailable: {target}", file=sys.stderr)
        return 2
    os.execv(sys.executable, [sys.executable, str(target), *arguments])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
