"""Fail-closed validation for the pinned Adaptive Grok Build Pro gitlink."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

VERSION = "2.0.19"
TAG = "v2.0.19"
COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"
REPOSITORY = "https://github.com/Dimkox/adaptive-grok-build-pro.git"
SUBMODULE = Path("tooling/adaptive-grok-build-pro")
EXECUTABLE_ROOTS = (Path(".grok-stack"), Path("scripts"), Path(".grok/hooks"))
IMPORTABLE_SUFFIXES = {".py", ".pyc", ".pyo", ".pyd", ".so"}


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


def _run_bytes(root: Path, *args: str, cwd: Path | None = None) -> bytes:
    completed = subprocess.run(
        list(args),
        cwd=cwd or root,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        detail = completed.stderr.decode(errors="replace").strip()
        detail = detail or completed.stdout.decode(errors="replace").strip()
        raise ToolingPinError(detail or "command failed")
    return completed.stdout


def _verify_index_flags(source: Path) -> None:
    records = _run_bytes(source, "git", "ls-files", "-v", "-z").split(b"\0")
    for record in records:
        if not record:
            continue
        if len(record) < 3 or record[1:2] != b" " or record[:1] != b"H":
            path = record[2:].decode(errors="replace") if len(record) > 2 else "?"
            raise ToolingPinError(
                f"Adaptive Grok index has forbidden optimization/state flags: {path}"
            )


def _blob_oid(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


def _verify_head_tree(source: Path) -> None:
    if _run(source, "git", "rev-parse", "--show-object-format") != "sha1":
        raise ToolingPinError("Adaptive Grok repository uses an unexpected object format")
    records = _run_bytes(
        source, "git", "ls-tree", "-r", "-z", "--full-tree", "HEAD"
    ).split(b"\0")
    for record in records:
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            raw_mode, raw_kind, raw_oid = metadata.split(b" ", 2)
            mode = raw_mode.decode("ascii")
            kind = raw_kind.decode("ascii")
            expected_oid = raw_oid.decode("ascii")
            relative = Path(os.fsdecode(raw_path))
        except (ValueError, UnicodeError) as exc:
            raise ToolingPinError("Adaptive Grok HEAD tree is malformed") from exc
        if relative.is_absolute() or ".." in relative.parts:
            raise ToolingPinError("Adaptive Grok HEAD contains an unsafe path")
        candidate = source / relative
        try:
            attributes = candidate.lstat()
        except OSError as exc:
            raise ToolingPinError(f"Adaptive Grok tracked path is unavailable: {relative}") from exc
        if kind != "blob":
            raise ToolingPinError(
                f"Adaptive Grok contains an unsupported tracked object: {relative}"
            )
        if mode == "120000":
            if not stat.S_ISLNK(attributes.st_mode):
                raise ToolingPinError(f"Adaptive Grok tracked mode differs from HEAD: {relative}")
            data = os.fsencode(os.readlink(candidate))
        elif mode in {"100644", "100755"}:
            if not stat.S_ISREG(attributes.st_mode):
                raise ToolingPinError(f"Adaptive Grok tracked mode differs from HEAD: {relative}")
            executable = bool(attributes.st_mode & 0o111)
            if executable != (mode == "100755"):
                raise ToolingPinError(f"Adaptive Grok tracked mode differs from HEAD: {relative}")
            try:
                data = candidate.read_bytes()
            except OSError as exc:
                raise ToolingPinError(
                    f"Adaptive Grok tracked path is unreadable: {relative}"
                ) from exc
        else:
            raise ToolingPinError(f"Adaptive Grok has an unsupported mode: {relative}")
        if _blob_oid(data) != expected_oid:
            raise ToolingPinError(f"Adaptive Grok tracked bytes differ from HEAD: {relative}")


def _verify_no_ignored_imports(source: Path) -> None:
    records = _run_bytes(
        source,
        "git",
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
        "--",
        *(str(path) for path in EXECUTABLE_ROOTS),
    ).split(b"\0")
    for record in records:
        if not record:
            continue
        relative = Path(os.fsdecode(record))
        if relative.suffix.casefold() in IMPORTABLE_SUFFIXES:
            raise ToolingPinError(
                f"Adaptive Grok executable roots contain ignored importable code: {relative}"
            )


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
    _verify_index_flags(source)
    _verify_head_tree(source)
    if _run(root, "git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"):
        raise ToolingPinError("Adaptive Grok checkout is modified")
    _verify_no_ignored_imports(source)
    if _run(root, "git", "-C", str(source), "rev-parse", f"{TAG}^{{}}") != COMMIT:
        raise ToolingPinError("Adaptive Grok tag does not resolve to the locked commit")
    try:
        actual_version = (source / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ToolingPinError("Adaptive Grok VERSION is unavailable") from exc
    if actual_version != VERSION:
        raise ToolingPinError("Adaptive Grok VERSION does not match the lock")
    return source
