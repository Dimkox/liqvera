#!/usr/bin/env python3
"""Extract low-risk static indicators from an APK/XAPK/APKM ZIP container.

The script inventories archive entries and extracts network indicators without
writing decompiled code. URL query strings and fragments are discarded so that
embedded credentials or capability tokens are not persisted in reports.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

URL_RE = re.compile(rb"(?:https?|wss?)://[^\x00-\x20\x7f<>\"'{}|\\^`\[\]]+", re.IGNORECASE)
DOMAIN_RE = re.compile(
    rb"(?<![A-Za-z0-9_.-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    rb"[A-Za-z]{2,63}(?![A-Za-z0-9_.-])"
)
IPV4_RE = re.compile(rb"(?<![0-9.])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9.])")
SIGNATURE_SUFFIXES = (".RSA", ".DSA", ".EC", ".SF", ".MF")
NATIVE_LIBRARY_RE = re.compile(r"^lib/[^/]+/[^/]+\.so$")
DEX_RE = re.compile(r"^classes(?:\d+)?\.dex$")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_decode(value: bytes) -> str:
    return value.decode("utf-8", errors="ignore")


def _normalize_url(raw: bytes) -> str | None:
    value = _safe_decode(raw).rstrip(".,;:)]}")
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme.lower() not in {"http", "https", "ws", "wss"} or not parsed.hostname:
        return None
    host = parsed.hostname.lower().rstrip(".")
    try:
        port = parsed.port
    except ValueError:
        return None
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if port is not None:
        netloc = f"{netloc}:{port}"
    # Drop query and fragment to avoid retaining tokens or credentials.
    return urlunsplit((parsed.scheme.lower(), netloc, parsed.path or "", "", ""))


def _valid_domain(raw: bytes) -> str | None:
    domain = _safe_decode(raw).lower().rstrip(".")
    if len(domain) > 253 or ".." in domain:
        return None
    labels = domain.split(".")
    if any(not label or len(label) > 63 for label in labels):
        return None
    return domain


def _valid_ip(raw: bytes) -> str | None:
    value = _safe_decode(raw)
    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def _collect_matches(chunks: Iterable[bytes]) -> tuple[set[str], set[str], set[str]]:
    urls: set[str] = set()
    domains: set[str] = set()
    addresses: set[str] = set()
    for data in chunks:
        for match in URL_RE.findall(data):
            normalized = _normalize_url(match)
            if normalized:
                urls.add(normalized)
                hostname = urlsplit(normalized).hostname
                if hostname:
                    try:
                        addresses.add(str(ipaddress.ip_address(hostname)))
                    except ValueError:
                        domains.add(hostname.lower())
        for match in DOMAIN_RE.findall(data):
            domain = _valid_domain(match)
            if domain:
                domains.add(domain)
        for match in IPV4_RE.findall(data):
            address = _valid_ip(match)
            if address:
                addresses.add(address)
    return urls, domains, addresses


def analyze_archive(path: Path, *, max_entry_bytes: int = 16 * 1024 * 1024) -> dict[str, Any]:
    """Analyze an APK-compatible ZIP archive and return a JSON-serializable report."""
    if max_entry_bytes <= 0:
        raise ValueError("max_entry_bytes must be greater than zero")
    if not path.is_file():
        raise ValueError(f"Input file does not exist: {path}")
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Input is not a valid ZIP/APK archive: {path}")

    scanned_chunks: list[bytes] = []
    skipped: list[str] = []
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        for entry in entries:
            if entry.is_dir():
                continue
            if entry.file_size > max_entry_bytes:
                skipped.append(entry.filename)
                continue
            try:
                scanned_chunks.append(archive.read(entry))
            except (OSError, RuntimeError, zipfile.BadZipFile):
                skipped.append(entry.filename)

    urls, domains, addresses = _collect_matches(scanned_chunks)
    native_libraries = sorted(name for name in names if NATIVE_LIBRARY_RE.match(name))
    dex_files = sorted(name for name in names if DEX_RE.match(name))
    signature_entries = sorted(
        name
        for name in names
        if name.upper().startswith("META-INF/") and name.upper().endswith(SIGNATURE_SUFFIXES)
    )
    inner_packages = sorted(
        name for name in names if name.lower().endswith((".apk", ".apks", ".xapk", ".apkm"))
    )

    return {
        "schema_version": 1,
        "archive": {
            "file_name": path.name,
            "size_bytes": path.stat().st_size,
            "sha256": _sha256(path),
            "entry_count": len(names),
        },
        "scan": {
            "max_entry_bytes": max_entry_bytes,
            "scanned_entry_count": len(names) - len(skipped),
            "skipped_oversized_entries": sorted(set(skipped)),
        },
        "dex_files": dex_files,
        "native_libraries": native_libraries,
        "signature_entries": signature_entries,
        "inner_packages": inner_packages,
        "network_indicators": {
            "urls": sorted(urls),
            "domains": sorted(domains),
            "ip_addresses": sorted(addresses),
        },
        "notes": [
            "URL query strings and fragments are deliberately removed.",
            "Indicators are heuristic strings and require manual validation.",
            "No code is decompiled and no data is transmitted by this script.",
        ],
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="Path to an APK, XAPK, APKM, or ZIP archive")
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this file instead of stdout",
    )
    parser.add_argument(
        "--max-entry-bytes",
        type=int,
        default=16 * 1024 * 1024,
        help="Maximum uncompressed bytes read from any single entry (default: 16 MiB)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = analyze_archive(args.archive, max_entry_bytes=args.max_entry_bytes)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
