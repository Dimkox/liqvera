"""Durable SQLite state and immutable artifact reads for the local demo only."""

from __future__ import annotations

import hashlib
import os
import re
import sqlite3
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from uuid import UUID

_MIGRATION = Path(__file__).resolve().parents[2] / "migrations" / "001_local_demo.sql"
_CAPABILITY = re.compile(r"[0-9a-f]{64}\Z")


class LocalDemoError(ValueError):
    """Stable local API rejection with an HTTP status for the demo adapter."""

    def __init__(self, code: str, status: int = 400) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


def capability_digest(capability: str) -> str:
    """Hash the exact 256-bit browser capability; never persist its bearer value."""

    if type(capability) is not str or _CAPABILITY.fullmatch(capability) is None:
        raise LocalDemoError("INVALID_CAPABILITY", 401)
    return hashlib.sha256(capability.encode("ascii")).hexdigest()


class LocalDemoStore:
    """One on-disk demo ledger and its store-selected artifact directory."""

    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        if not isinstance(database_path, Path) or not isinstance(artifact_root, Path):
            raise TypeError("database_path and artifact_root must be Paths")
        self.database_path = database_path
        self.artifact_root = artifact_root
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        if self.database_path.is_symlink() or self.artifact_root.is_symlink():
            raise ValueError("local demo store paths must not be symlinks")
        with self.connect() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                connection.executescript(_MIGRATION.read_text(encoding="utf-8"))
            elif version != 1:
                raise RuntimeError(f"unsupported local demo ledger version: {version}")

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            yield connection
        finally:
            connection.close()

    def read_artifact(self, report_id: UUID, filename: str, expected_sha256: str) -> bytes:
        """Read an allowlisted immutable file and check its committed digest."""

        if type(report_id) is not UUID or filename not in {"report.json", "evidence.zip"}:
            raise LocalDemoError("ARTIFACT_NOT_FOUND", 404)
        path = self.artifact_root / str(report_id) / filename
        directory = path.parent
        try:
            directory_mode = directory.lstat().st_mode
        except OSError as error:
            raise LocalDemoError("ARTIFACT_UNAVAILABLE", 500) from error
        if not stat.S_ISDIR(directory_mode) or directory.is_symlink():
            raise LocalDemoError("ARTIFACT_UNAVAILABLE", 500)
        try:
            descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        except OSError as error:
            raise LocalDemoError("ARTIFACT_UNAVAILABLE", 500) from error
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise LocalDemoError("ARTIFACT_UNAVAILABLE", 500)
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                payload = stream.read()
        except OSError as error:
            raise LocalDemoError("ARTIFACT_UNAVAILABLE", 500) from error
        finally:
            os.close(descriptor)
        if hashlib.sha256(payload).hexdigest() != expected_sha256:
            raise LocalDemoError("ARTIFACT_DIGEST_MISMATCH", 500)
        return payload
