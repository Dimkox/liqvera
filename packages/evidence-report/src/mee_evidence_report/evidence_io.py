"""Bounded immutable bytes and strict JSON at the canonical F3 boundary."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

MAX_BUNDLE_BYTES = 10 * 1024 * 1024
MAX_MEMBER_BYTES = 4 * 1024 * 1024
MAX_MEMBERS = 32


class EvidenceRejected(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result = {}
        for key, value in items:
            if key in result:
                raise EvidenceRejected("INVALID_DATASET")
            result[key] = value
        return result

    def forbidden(value: str) -> object:
        raise EvidenceRejected("INVALID_DATASET")

    try:
        result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                            parse_float=forbidden, parse_constant=forbidden)
        _strings(result)
        return result
    except (UnicodeError, ValueError, RecursionError) as error:
        raise EvidenceRejected("INVALID_DATASET") from error


def _strings(value: object) -> None:
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            raise EvidenceRejected("INVALID_DATASET")
        value.encode("utf-8")
    elif type(value) is dict:
        for key, child in value.items():
            _strings(key)
            _strings(child)
    elif type(value) is list:
        for child in value:
            _strings(child)


def object_keys(value: object, keys: set[str]) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise EvidenceRejected("INVALID_DATASET")
    return value


def integer(value: object, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EvidenceRejected("INVALID_DATASET")
    return value


def identifier(value: object) -> str:
    try:
        if type(value) is not str or str(UUID(value)) != value:
            raise ValueError()
    except (ValueError, AttributeError) as error:
        raise EvidenceRejected("INVALID_INPUT") from error
    return value


def safe_member(name: object) -> str:
    if (type(name) is not str or len(name) > 180
            or re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*(/[A-Za-z0-9_-][A-Za-z0-9_.-]*)*", name) is None):
        raise EvidenceRejected("INVALID_DATASET")
    return name


def timestamp_ms(value: object) -> int:
    if type(value) is not str or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z", value
    ) is None:
        raise EvidenceRejected("INVALID_DATASET")
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
        delta = instant - datetime(1970, 1, 1, tzinfo=UTC)
        return (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
    except ValueError as error:
        raise EvidenceRejected("INVALID_DATASET") from error


def read_tree(root: Path) -> dict[str, bytes]:
    """Read each file once through no-follow directory descriptors, with bounds."""
    result: dict[str, bytes] = {}
    total = 0

    def visit(fd: int, prefix: str = "") -> None:
        nonlocal total
        names = sorted(os.listdir(fd))
        if len(names) > MAX_MEMBERS:
            raise EvidenceRejected("INVALID_DATASET")
        for name in names:
            relative = safe_member(prefix + name)
            metadata = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISDIR(metadata.st_mode):
                if relative.count("/") >= 2:
                    raise EvidenceRejected("INVALID_DATASET")
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if not os.listdir(child):
                        raise EvidenceRejected("INVALID_DATASET")
                    visit(child, relative + "/")
                finally:
                    os.close(child)
            elif stat.S_ISREG(metadata.st_mode):
                if len(result) >= MAX_MEMBERS or metadata.st_size > MAX_MEMBER_BYTES:
                    raise EvidenceRejected("INVALID_DATASET")
                child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                with os.fdopen(child, "rb") as stream:
                    before = os.fstat(stream.fileno())
                    if not stat.S_ISREG(before.st_mode):
                        raise EvidenceRejected("INVALID_DATASET")
                    raw = stream.read(MAX_MEMBER_BYTES + 1)
                    after = os.fstat(stream.fileno())
                if (before.st_ino != metadata.st_ino or before.st_dev != metadata.st_dev
                        or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
                        or len(raw) != after.st_size or len(raw) > MAX_MEMBER_BYTES):
                    raise EvidenceRejected("INVALID_DATASET")
                total += len(raw)
                if total > MAX_BUNDLE_BYTES:
                    raise EvidenceRejected("INVALID_DATASET")
                result[relative] = raw
            else:
                raise EvidenceRejected("INVALID_DATASET")
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            visit(fd)
        finally:
            os.close(fd)
    except OSError as error:
        raise EvidenceRejected("INVALID_DATASET") from error
    return result
