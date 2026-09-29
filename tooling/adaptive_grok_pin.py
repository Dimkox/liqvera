"""Fail-closed validation for the pinned Adaptive Grok Build Pro gitlink."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import NamedTuple

VERSION = "2.0.19"
TAG = "v2.0.19"
COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"
REPOSITORY = "https://github.com/Dimkox/adaptive-grok-build-pro.git"
SUBMODULE = Path("tooling/adaptive-grok-build-pro")
EXECUTABLE_ROOTS = (Path(".grok-stack"), Path("scripts"), Path(".grok/hooks"))
IMPORTABLE_SUFFIXES = {".py", ".pyc", ".pyo", ".pyd", ".so"}
TRUSTED_PREFIXES = (
    Path(".agents/skills"),
    Path(".grok/agents"),
    Path(".grok/hooks"),
    Path(".grok/skills"),
    Path(".grok-stack/adaptive_grok"),
    Path(".grok-stack/config"),
    Path(".grok-stack/templates"),
)
TRUSTED_FILES = frozenset(
    {
        Path(".grok/config.toml"),
        Path(".grok/hooks.json"),
        Path("schemas/change-spec-v1.schema.json"),
        Path("schemas/change-spec.schema.json"),
        Path("AGENTS.md"),
        Path("VERSION"),
    }
)
TRUSTED_SCRIPT_NAMES = frozenset(
    {
        "grok_approve.py",
        "grok_change.py",
        "grok_deploy.py",
        "grok_doctor.py",
        "grok_review.py",
        "grok_route.py",
        "grok_status.py",
        "grok_verify.py",
    }
)
TRUST_TREE_PATHS = (*TRUSTED_PREFIXES, *sorted(TRUSTED_FILES), Path("scripts"))
REQUIRED_TRUSTED_FILES = frozenset(
    {
        Path(".agents/skills/adaptive-delivery/SKILL.md"),
        Path(".grok/agents/security_reviewer.md"),
        Path(".grok/hooks/pre_tool_use.py"),
        Path(".grok/skills/adaptive-delivery/SKILL.md"),
        Path(".grok-stack/adaptive_grok/python_test_runner.py"),
        Path(".grok-stack/adaptive_grok/verification.py"),
        Path(".grok-stack/config/policy.json"),
        Path(".grok-stack/config/routing.json"),
        Path(".grok-stack/templates/change/change-spec.yaml"),
        Path("scripts/grok_verify.py"),
        Path("schemas/change-spec-v1.schema.json"),
        Path("schemas/change-spec.schema.json"),
        Path("AGENTS.md"),
        Path("VERSION"),
    }
)
MAX_TRUSTED_FILES = 256
MAX_TRUSTED_BYTES = 2_000_000


class ToolingPinError(RuntimeError):
    """The external tooling checkout does not match the Liqvera lock."""


class TrustEntry(NamedTuple):
    """One immutable blob in the runtime/instruction trust closure."""

    relative: Path
    mode: str
    oid: str
    size: int


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


def _is_trusted_path(relative: Path) -> bool:
    if relative in TRUSTED_FILES:
        return True
    if relative.parent == Path("scripts"):
        return relative.name in TRUSTED_SCRIPT_NAMES
    return any(relative.is_relative_to(prefix) for prefix in TRUSTED_PREFIXES)


def _trust_closure_manifest(source: Path) -> tuple[TrustEntry, ...]:
    if _run(source, "git", "rev-parse", "--show-object-format") != "sha1":
        raise ToolingPinError("Adaptive Grok repository uses an unexpected object format")
    records = _run_bytes(
        source,
        "git",
        "ls-tree",
        "-r",
        "-l",
        "-z",
        "--full-tree",
        "HEAD",
        "--",
        *(str(path) for path in TRUST_TREE_PATHS),
    ).split(b"\0")
    entries: list[TrustEntry] = []
    for record in records:
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            raw_mode, raw_kind, raw_oid, raw_size = metadata.split()
            mode = raw_mode.decode("ascii")
            kind = raw_kind.decode("ascii")
            expected_oid = raw_oid.decode("ascii")
            size = int(raw_size)
            relative = Path(os.fsdecode(raw_path))
        except (TypeError, ValueError, UnicodeError) as exc:
            raise ToolingPinError("Adaptive Grok HEAD tree is malformed") from exc
        if relative.is_absolute() or ".." in relative.parts:
            raise ToolingPinError("Adaptive Grok HEAD contains an unsafe path")
        if not _is_trusted_path(relative):
            continue
        if kind != "blob":
            raise ToolingPinError(
                f"Adaptive Grok contains an unsupported tracked object: {relative}"
            )
        if mode not in {"100644", "100755", "120000"}:
            raise ToolingPinError(f"Adaptive Grok has an unsupported mode: {relative}")
        entries.append(TrustEntry(relative, mode, expected_oid, size))
    manifest = tuple(sorted(entries, key=lambda entry: entry.relative.as_posix()))
    present = {entry.relative for entry in manifest}
    missing = REQUIRED_TRUSTED_FILES - present
    if missing:
        paths = ", ".join(sorted(str(path) for path in missing))
        raise ToolingPinError(f"Adaptive Grok trust closure is incomplete: {paths}")
    total_bytes = sum(entry.size for entry in manifest)
    if len(manifest) > MAX_TRUSTED_FILES or total_bytes > MAX_TRUSTED_BYTES:
        raise ToolingPinError(
            "Adaptive Grok trust closure exceeds its file/byte safety bound"
        )
    return manifest


def _read_tracked_bytes(source: Path, entry: TrustEntry) -> bytes:
    candidate = source / entry.relative
    try:
        attributes = candidate.lstat()
    except OSError as exc:
        raise ToolingPinError(
            f"Adaptive Grok tracked path is unavailable: {entry.relative}"
        ) from exc
    if entry.mode == "120000":
        if not stat.S_ISLNK(attributes.st_mode):
            raise ToolingPinError(
                f"Adaptive Grok tracked mode differs from HEAD: {entry.relative}"
            )
        return os.fsencode(os.readlink(candidate))
    if not stat.S_ISREG(attributes.st_mode):
        raise ToolingPinError(
            f"Adaptive Grok tracked mode differs from HEAD: {entry.relative}"
        )
    executable = bool(attributes.st_mode & 0o111)
    if executable != (entry.mode == "100755"):
        raise ToolingPinError(
            f"Adaptive Grok tracked mode differs from HEAD: {entry.relative}"
        )
    try:
        return candidate.read_bytes()
    except OSError as exc:
        raise ToolingPinError(
            f"Adaptive Grok tracked path is unreadable: {entry.relative}"
        ) from exc


def _verify_trust_closure(source: Path) -> None:
    for entry in _trust_closure_manifest(source):
        data = _read_tracked_bytes(source, entry)
        if len(data) != entry.size or _blob_oid(data) != entry.oid:
            raise ToolingPinError(
                f"Adaptive Grok tracked bytes differ from HEAD: {entry.relative}"
            )


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
    _verify_trust_closure(source)
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
