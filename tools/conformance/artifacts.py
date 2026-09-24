"""Inspect Stage A package trees for forbidden Go inputs."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path


def match_relative(relative: str, pattern: str) -> bool:
    normalized = relative.replace("\\", "/")
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return normalized == prefix.rstrip("/") or normalized.startswith(prefix)
    return fnmatch(normalized, pattern) or fnmatch(Path(normalized).name, pattern)


def scan(
    roots: tuple[Path, ...], forbid_paths: tuple[str, ...], forbid_binary: str | None
) -> list[str]:
    hits: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            for pattern in forbid_paths:
                if match_relative(relative, pattern):
                    hits.append(f"{root.as_posix()}/{relative}")
            if forbid_binary and path.name == forbid_binary:
                hits.append(f"{root.as_posix()}/{relative}")
            if path.suffix == ".go" or path.name in {"go.mod", "go.sum"}:
                hits.append(f"{root.as_posix()}/{relative}")
    return sorted(set(hits))
