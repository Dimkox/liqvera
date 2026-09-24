"""Canonical JSON and member hashing for frozen packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from mee_readonly_analyzer.frozen_package.types import (
    FrozenPackageError,
    FrozenPackageErrorCode,
)


def canonical_json_bytes(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "ascii"
    )


def decode_canonical_json(payload: bytes) -> object:
    if not payload.endswith(b"\n"):
        raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_NON_CANONICAL)
    try:
        return json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenPackageError(FrozenPackageErrorCode.MANIFEST_NON_CANONICAL) from error


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def hash_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require_relative_member(path: str) -> PurePosixPath:
    relative = PurePosixPath(path)
    if (
        not path
        or relative.is_absolute()
        or ".." in relative.parts
        or relative.as_posix() != path
        or path.endswith("/")
    ):
        raise FrozenPackageError(FrozenPackageErrorCode.PATH_INVALID)
    return relative


def scan_regular_files(root: Path) -> set[str]:
    found: set[str] = set()
    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            raise FrozenPackageError(FrozenPackageErrorCode.SYMLINK_FORBIDDEN)
        if item.is_dir():
            continue
        if not item.is_file():
            raise FrozenPackageError(FrozenPackageErrorCode.PATH_INVALID)
        found.add(relative)
    return found
