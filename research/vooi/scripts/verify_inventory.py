#!/usr/bin/env python3
"""Offline integrity checks for the VOOI research inventory."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED_RESULTS = {"not_verified"}
ALLOWED_WEB_STATUS = {
    "live",
    "live_legacy",
    "shut_down_migration_only",
    "live_bearer_auth",
}


class InventoryError(ValueError):
    """Raised when the checked inventory violates its local contract."""


def _check_url(value: str, where: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme != "https":
        raise InventoryError(f"{where}: URL must use https: {value!r}")
    if not parsed.hostname:
        raise InventoryError(f"{where}: URL has no host: {value!r}")
    if parsed.username or parsed.password:
        raise InventoryError(f"{where}: credentials are forbidden in URLs")
    lowered = value.lower()
    forbidden_fragments = ("access_token=", "api_key=", "apikey=", "secret=", "authorization=")
    if any(fragment in lowered for fragment in forbidden_fragments):
        raise InventoryError(f"{where}: secret-like query parameter is forbidden")


def validate_inventory(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise InventoryError("schema_version must be 1")
    snapshot = data.get("snapshot_at")
    if not isinstance(snapshot, str) or not snapshot.endswith("Z"):
        raise InventoryError("snapshot_at must be an ISO-8601 UTC string ending in Z")

    ids: set[str] = set()
    for section in ("web_clients", "programmatic_clients"):
        items = data.get(section)
        if not isinstance(items, list) or not items:
            raise InventoryError(f"{section} must be a non-empty list")
        for index, item in enumerate(items):
            item_id = item.get("id")
            where = f"{section}[{index}]"
            if not isinstance(item_id, str) or not item_id:
                raise InventoryError(f"{where}: missing id")
            if item_id in ids:
                raise InventoryError(f"{where}: duplicate id {item_id!r}")
            ids.add(item_id)

    for index, item in enumerate(data["web_clients"]):
        where = f"web_clients[{index}]"
        _check_url(item["url"], f"{where}.url")
        if item.get("status") not in ALLOWED_WEB_STATUS:
            raise InventoryError(f"{where}: unsupported status {item.get('status')!r}")
        for evidence_index, url in enumerate(item.get("evidence", [])):
            _check_url(url, f"{where}.evidence[{evidence_index}]")

    for index, item in enumerate(data["programmatic_clients"]):
        where = f"programmatic_clients[{index}]"
        _check_url(item["repo"], f"{where}.repo")
        commit = item.get("commit", "")
        if not SHA40_RE.fullmatch(commit):
            raise InventoryError(f"{where}: commit must be a 40-character lowercase SHA")
        if item.get("default_branch") != "main":
            raise InventoryError(f"{where}: expected pinned default_branch=main")

    for index, item in enumerate(data.get("official_non_client_repositories", [])):
        _check_url(item["repo"], f"official_non_client_repositories[{index}].repo")

    for index, item in enumerate(data.get("negative_findings", [])):
        if item.get("result") not in ALLOWED_RESULTS:
            raise InventoryError(f"negative_findings[{index}]: unsupported result")

    return data


def validate_api_csv_files(paths: list[Path]) -> int:
    if not paths:
        raise InventoryError("API surface CSV set is empty")

    required = {
        "method",
        "path",
        "schema_auth",
        "risk_class",
        "multi_exchange_engine_policy",
        "notes",
        "source",
    }
    seen: set[tuple[str, str]] = set()
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    total = 0

    for path in paths:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if set(reader.fieldnames or ()) != required:
                raise InventoryError(
                    f"{path}: API CSV columns differ from expected: "
                    f"{set(reader.fieldnames or ())!r}"
                )
            rows = list(reader)

        if not rows:
            raise InventoryError(f"{path}: API surface CSV is empty")

        for line_number, row in enumerate(rows, start=2):
            method = row["method"]
            path_value = row["path"]
            if method not in valid_methods:
                raise InventoryError(
                    f"{path} line {line_number}: invalid method {method!r}"
                )
            if not path_value.startswith("/") or "://" in path_value:
                raise InventoryError(
                    f"{path} line {line_number}: invalid relative path"
                )
            key = (method, path_value)
            if key in seen:
                raise InventoryError(
                    f"{path} line {line_number}: duplicate {method} {path_value}"
                )
            seen.add(key)
            if not row["source"].startswith("vooi-app/"):
                raise InventoryError(
                    f"{path} line {line_number}: source is not pinned"
                )
        total += len(rows)

    return total


def validate_api_csv(path: Path) -> int:
    """Backward-compatible validation for one CSV file."""
    return validate_api_csv_files([path])


def main() -> int:
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--inventory",
        type=Path,
        default=base / "clients.lock.json",
        help="Path to clients.lock.json",
    )
    parser.add_argument(
        "--api-dir",
        type=Path,
        default=base / "data",
        help="Directory containing api-surface-*.csv",
    )
    args = parser.parse_args()

    try:
        data = validate_inventory(args.inventory)
        endpoint_count = validate_api_csv_files(
            sorted(args.api_dir.glob("api-surface-*.csv"))
        )
    except (OSError, json.JSONDecodeError, InventoryError) as exc:
        print(f"VOOI inventory verification failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "snapshot_at": data["snapshot_at"],
                "web_clients": len(data["web_clients"]),
                "programmatic_clients": len(data["programmatic_clients"]),
                "api_rows": endpoint_count,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
