#!/usr/bin/env python3
"""Offline integrity checks for the perp-cli research inventory."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


class InventoryError(ValueError):
    pass


def check_url(value: str, where: str) -> None:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise InventoryError(f"{where}: URL must be absolute https: {value!r}")
    if parsed.username or parsed.password:
        raise InventoryError(f"{where}: credentials are forbidden in URLs")
    lowered = value.lower()
    forbidden = ("access_token=", "api_key=", "apikey=", "secret=", "authorization=")
    if any(fragment in lowered for fragment in forbidden):
        raise InventoryError(f"{where}: secret-like query parameter is forbidden")


def validate_inventory(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise InventoryError("schema_version must be 1")
    snapshot = data.get("snapshot_at")
    if not isinstance(snapshot, str) or not snapshot.endswith("Z"):
        raise InventoryError("snapshot_at must be UTC ISO-8601 ending in Z")

    ids: set[str] = set()
    for section in ("official_components", "third_party_surfaces"):
        items = data.get(section)
        if not isinstance(items, list) or not items:
            raise InventoryError(f"{section} must be a non-empty list")
        for i, item in enumerate(items):
            item_id = item.get("id")
            where = f"{section}[{i}]"
            if not isinstance(item_id, str) or not item_id:
                raise InventoryError(f"{where}: missing id")
            if item_id in ids:
                raise InventoryError(f"{where}: duplicate id {item_id!r}")
            ids.add(item_id)

            for key in ("repo", "url", "registry_metadata"):
                if item.get(key):
                    check_url(item[key], f"{where}.{key}")

            if item.get("commit") and not SHA40_RE.fullmatch(item["commit"]):
                raise InventoryError(f"{where}.commit must be lowercase 40-char SHA")
            if item.get("version") and not SEMVER_RE.fullmatch(item["version"]):
                raise InventoryError(f"{where}.version is not semver")
            if item.get("observed_version") and not SEMVER_RE.fullmatch(item["observed_version"]):
                raise InventoryError(f"{where}.observed_version is not semver")

    official = {item["id"]: item for item in data["official_components"]}
    expected_bins = {
        "perp-cli-bin": ("perp", "dist/index.js"),
        "perp-mcp-bin": ("perp-mcp", "dist/mcp-server.js"),
        "perp-guardrail-bin": ("perp-guardrail", "dist/guardrail/perp-guardrail.js"),
    }
    for item_id, (name, target) in expected_bins.items():
        item = official.get(item_id)
        if not item or item.get("name") != name or item.get("target") != target:
            raise InventoryError(f"{item_id}: bin contract drift")

    exchanges = data.get("supported_exchanges")
    if not isinstance(exchanges, list) or len(exchanges) != 4:
        raise InventoryError("supported_exchanges must contain exactly 4 built-ins")
    ex_ids = {item["id"] for item in exchanges}
    if ex_ids != {"pacifica", "hyperliquid", "lighter", "aster"}:
        raise InventoryError(f"unexpected exchange set: {sorted(ex_ids)!r}")
    for i, item in enumerate(exchanges):
        if item.get("public_api"):
            check_url(item["public_api"], f"supported_exchanges[{i}].public_api")

    collisions = data.get("unrelated_name_collisions")
    if not isinstance(collisions, list) or not collisions:
        raise InventoryError("unrelated_name_collisions must document @perp/cli collision")
    for i, item in enumerate(collisions):
        check_url(item["url"], f"unrelated_name_collisions[{i}].url")

    for i, item in enumerate(data.get("negative_findings", [])):
        if item.get("result") != "not_verified":
            raise InventoryError(f"negative_findings[{i}]: unsupported result")

    return data


def validate_csv(path: Path, required: list[str]) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != required:
            raise InventoryError(f"{path}: columns differ from expected")
        rows = list(reader)
    if not rows:
        raise InventoryError(f"{path}: empty")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    base = Path(__file__).resolve().parents[1]
    parser.add_argument("--inventory", type=Path, default=base / "clients.lock.json")
    args = parser.parse_args()

    try:
        data = validate_inventory(args.inventory)
        surface_rows = validate_csv(
            base / "data" / "surface-map.csv",
            ["id","kind","version","distribution","mutation_capability","secret_dependency","classification","multi_exchange_engine_policy"],
        )
        exchange_rows = validate_csv(
            base / "data" / "exchange-adapters.csv",
            ["exchange","alias","chain","adapter_source","public_api","capability_family","multi_exchange_engine_policy"],
        )
    except (OSError, json.JSONDecodeError, InventoryError) as exc:
        print(f"perp-cli inventory verification failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({
        "ok": True,
        "snapshot_at": data["snapshot_at"],
        "official_components": len(data["official_components"]),
        "supported_exchanges": len(data["supported_exchanges"]),
        "third_party_surfaces": len(data["third_party_surfaces"]),
        "surface_rows": surface_rows,
        "exchange_rows": exchange_rows,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
