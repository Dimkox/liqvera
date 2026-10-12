"""Bind release artifacts to a clean Liqvera source commit."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


class ConformanceError(RuntimeError):
    """An artifact cannot be built or its source identity is ambiguous."""


def require_clean_exact_head(source_sha: str, root: Path) -> None:
    if not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ConformanceError("source_sha must be a 40-character hex SHA")
    head = _git(root, "rev-parse", "HEAD")
    if head != source_sha:
        raise ConformanceError(f"HEAD {head} does not match source_sha {source_sha}")
    if _git(root, "status", "--porcelain"):
        raise ConformanceError("working tree is dirty")


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=False, capture_output=True, text=True,
    )
    if result.returncode:
        raise ConformanceError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()
