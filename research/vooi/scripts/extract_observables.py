#!/usr/bin/env python3
"""Statically extract non-secret observables from acquired VOOI sources."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

MAX_FILE_BYTES = 8 * 1024 * 1024
TEXT_SUFFIXES = {
    ".c",
    ".conf",
    ".css",
    ".env",
    ".example",
    ".go",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "node_modules",
    "target",
    "vendor",
}
URL_RE = re.compile(r"""(?P<url>(?:https?|wss?)://[^\s"'`<>\\)]+)""")
API_PATH_RE = re.compile(
    r"""(?P<path>/(?:broker(?:-statistics)?|deposit|exchange|extended|funding-strategies|kinetiq|mcp|time|transfer|user(?:-exchange)?|withdraw)(?:/[A-Za-z0-9_.:{}-]+)*)"""
)
ENV_RE_LIST = [
    re.compile(r"""(?:os\.(?:getenv|environ\.get)|getenv)\(\s*["'](?P<name>[A-Z][A-Z0-9_]{2,})["']"""),
    re.compile(r"""process\.env\.(?P<name>[A-Z][A-Z0-9_]{2,})"""),
    re.compile(r"""^\s*(?:export\s+)?(?P<name>[A-Z][A-Z0-9_]{2,})\s*=""", re.MULTILINE),
]
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
SECRET_QUERY_PARTS = ("token", "key", "secret", "auth", "signature", "session", "password")


class ExtractionError(RuntimeError):
    """Raised when local extraction cannot proceed safely."""


def is_text_candidate(path: Path) -> bool:
    if any(part in SKIP_PARTS for part in path.parts):
        return False
    name = path.name.lower()
    if name in {".env.example", "dockerfile", "makefile"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def redact_url(raw: str) -> str:
    raw = raw.rstrip(".,;:")
    parsed = urlsplit(raw)
    if parsed.username or parsed.password:
        netloc = parsed.hostname or ""
        if parsed.port:
            netloc += f":{parsed.port}"
    else:
        netloc = parsed.netloc

    redacted_query: list[tuple[str, str]] = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if any(fragment in lowered for fragment in SECRET_QUERY_PARTS):
            value = "<redacted>"
        redacted_query.append((key, value))
    return urlunsplit(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            urlencode(redacted_query, doseq=True),
            "",
        )
    )


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def relative_display(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def scan_file(path: Path, root: Path) -> dict[str, list[dict[str, object]]]:
    size = path.stat().st_size
    if size > MAX_FILE_BYTES:
        return {"skipped": [{"path": relative_display(path, root), "reason": "too_large", "size": size}]}

    raw = path.read_bytes()
    if b"\x00" in raw:
        return {"skipped": [{"path": relative_display(path, root), "reason": "binary"}]}
    text = raw.decode("utf-8", errors="replace")
    text = BEARER_RE.sub("Bearer <redacted>", text)
    display = relative_display(path, root)

    urls: list[dict[str, object]] = []
    for match in URL_RE.finditer(text):
        urls.append(
            {
                "value": redact_url(match.group("url")),
                "path": display,
                "line": line_number(text, match.start()),
            }
        )

    api_paths: list[dict[str, object]] = []
    for match in API_PATH_RE.finditer(text):
        api_paths.append(
            {
                "value": match.group("path"),
                "path": display,
                "line": line_number(text, match.start()),
            }
        )

    env_names: list[dict[str, object]] = []
    for regex in ENV_RE_LIST:
        for match in regex.finditer(text):
            env_names.append(
                {
                    "value": match.group("name"),
                    "path": display,
                    "line": line_number(text, match.start()),
                }
            )

    return {"urls": urls, "api_paths": api_paths, "env_names": env_names}


def deduplicate(items: list[dict[str, object]]) -> list[dict[str, object]]:
    seen: set[tuple[object, ...]] = set()
    output: list[dict[str, object]] = []
    for item in sorted(items, key=lambda value: (str(value.get("value")), str(value.get("path")), int(value.get("line", 0)))):
        key = (item.get("value"), item.get("path"), item.get("line"), item.get("reason"))
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def scan_roots(roots: list[Path]) -> dict[str, object]:
    result: dict[str, list[dict[str, object]]] = {
        "urls": [],
        "api_paths": [],
        "env_names": [],
        "skipped": [],
    }
    file_count = 0
    for root in roots:
        if not root.exists():
            raise ExtractionError(f"input does not exist: {root}")
        candidates = [root] if root.is_file() else root.rglob("*")
        for path in candidates:
            if not path.is_file() or not is_text_candidate(path):
                continue
            file_count += 1
            scanned = scan_file(path, root if root.is_dir() else root.parent)
            for key, values in scanned.items():
                result[key].extend(values)

    return {
        "schema_version": 1,
        "static_only": True,
        "secret_values_collected": False,
        "files_scanned": file_count,
        "urls": deduplicate(result["urls"]),
        "api_paths": deduplicate(result["api_paths"]),
        "env_names": deduplicate(result["env_names"]),
        "skipped": deduplicate(result["skipped"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", type=Path, help="Files or directories to scan")
    parser.add_argument("-o", "--output", type=Path, help="Write JSON here; stdout otherwise")
    args = parser.parse_args()
    try:
        result = scan_roots(args.roots)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(payload, encoding="utf-8")
        else:
            sys.stdout.write(payload)
    except (OSError, ExtractionError) as exc:
        print(f"static extraction failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
