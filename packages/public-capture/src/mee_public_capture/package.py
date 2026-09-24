"""Write a sealed Stage A frozen package. Does not import the analyzer."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from uuid import UUID

PACKAGE_SCHEMA = "mee-readonly-frozen-package/v1"

REVIEWED_BTC = {
    "mapping_id": "btc-usd-linear-perpetual",
    "mapping_version": "v1",
    "decision": "APPROVED",
    "venue": "hyperliquid",
    "symbol": "BTC",
    "identity": {
        "base_asset": "BTC",
        "quote_asset": "USD",
        "product_kind": "perp",
        "settlement_asset": "USD",
        "payoff_kind": "linear",
    },
    "evidence_sha256": "a" * 64,
    "evidence_reference": "reviewed/v1",
    "valid_from_ms": 0,
    "valid_until_ms": None,
    "reviewed_contract_multiplier": "1",
    "displayed_size_unit": "coin",
    "quantity_step": "0.001",
    "price_tick": "0.1",
    "price_decimals": None,
    "max_price_significant_digits": None,
    "min_quantity": None,
    "min_notional": "10",
}

REVIEWED_LIGHTER_BTC = {
    "mapping_id": "lighter-btc-usd-linear-perpetual",
    "mapping_version": "v1",
    "decision": "APPROVED",
    "venue": "lighter",
    "symbol": "BTC",
    "identity": {
        "base_asset": "BTC",
        "quote_asset": "USD",
        "product_kind": "perp",
        "settlement_asset": "USD",
        "payoff_kind": "linear",
    },
    "evidence_sha256": "a" * 64,
    "evidence_reference": "reviewed/v1",
    "valid_from_ms": 0,
    "valid_until_ms": None,
    "reviewed_contract_multiplier": "1",
    "displayed_size_unit": "coin",
    "quantity_step": "0.001",
    "price_tick": "0.1",
    "price_decimals": None,
    "max_price_significant_digits": None,
    "min_quantity": None,
    "min_notional": "10",
    "lighter_market_index": 1,
}


def canonical_json_bytes(document: object) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_frozen_package(
    root: Path,
    *,
    run_id: UUID,
    started_at_ms: int,
    terminated_at_ms: int,
    venues: tuple[str, ...],
    envelopes: tuple[tuple[str, bytes], ...],
    mappings: list[dict[str, object]],
) -> Path:
    if not root.is_absolute():
        raise ValueError("package root must be absolute")
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise ValueError("package root must be a real directory")
    if not envelopes:
        raise ValueError("envelopes must not be empty")
    root.mkdir(parents=True, exist_ok=True)
    _clear_package_root(root)
    batch_payload = envelopes[0][1]
    envelope_ndjson = "".join(
        json.dumps(
            {
                "envelope_index": index,
                "observed_at_ms": started_at_ms,
                "venue": venue,
                "payload_hex": payload.hex(),
            }
        )
        + "\n"
        for index, (venue, payload) in enumerate(envelopes)
    ).encode("utf-8")
    members: dict[str, bytes] = {
        "control_evidence/records.ndjson": (
            json.dumps(
                {
                    "recorded_at_ms": started_at_ms,
                    "kind": "epoch",
                    "payload_sha256": sha256_bytes(batch_payload),
                }
            )
            + "\n"
        ).encode("utf-8"),
        "raw_batches/0.bin": batch_payload,
        "raw_envelopes/records.ndjson": envelope_ndjson,
        "quality_minutes/records.ndjson": (
            json.dumps(
                {
                    "minute_start_ms": started_at_ms - (started_at_ms % 60_000),
                    "venue": venues[0],
                    "accepted": 1,
                    "rejected": 0,
                }
            )
            + "\n"
        ).encode("utf-8"),
        "mapping_snapshot.json": (json.dumps({"mappings": mappings}) + "\n").encode("utf-8"),
        "terminal.json": (
            json.dumps({"terminated_at_ms": terminated_at_ms, "status": "sealed"}) + "\n"
        ).encode("ascii"),
    }
    declared = []
    for path, payload in members.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        declared.append({"path": path, "sha256": sha256_bytes(payload), "length": len(payload)})
    unsigned = {
        "schema": PACKAGE_SCHEMA,
        "capture_run_id": str(run_id),
        "started_at_ms": started_at_ms,
        "venue_set": list(venues),
        "members": declared,
    }
    unsigned["manifest_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    (root / "manifest.json").write_bytes(canonical_json_bytes(unsigned))
    return root


def _clear_package_root(root: Path) -> None:
    for child in root.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
