"""Test-only frozen package builder. Not shipped in the analyzer wheel."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from mee_readonly_analyzer.frozen_package.codec import canonical_json_bytes, sha256_bytes
from mee_readonly_analyzer.frozen_package.types import PACKAGE_SCHEMA

FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
)

SAMPLE_MAPPING = {
    "mapping_id": "map-1",
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

SAMPLE_LIGHTER_MAPPING = {
    "mapping_id": "map-lighter-1",
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


_DEFAULT_ECONOMICS = object()
_MS_PER_MINUTE = 60_000
_SEVEN_DAY_MS = 7 * 86_400_000
_SEVEN_DAY_MINUTES = 7 * 1_440
_WEEK_QUALITY_MINUTES: bytes | None = None


def passing_economics(**overrides: object) -> dict[str, object]:
    document: dict[str, object] = {
        "independent_episode_count": 20,
        "largest_episode_concentration": "0.24",
        "median_net": "1",
        "schema": "mee-stage-a-sealed-economics/v1",
        "survived_both_fee_cases": True,
        "survived_delay_300ms": True,
        "survived_delay_500ms": True,
        "total_net": "1",
        "usd_1000_net": "1",
        "usd_5000_net": "0",
    }
    document.update(overrides)
    return document


def _quality_minutes_payload(count: int) -> bytes:
    global _WEEK_QUALITY_MINUTES
    if count == _SEVEN_DAY_MINUTES and _WEEK_QUALITY_MINUTES is not None:
        return _WEEK_QUALITY_MINUTES
    lines = [
        '{"minute_start_ms":%d,"venue":"hyperliquid","accepted":1,"rejected":0}'
        % (index * _MS_PER_MINUTE)
        for index in range(count)
    ]
    payload = ("\n".join(lines) + "\n").encode("ascii")
    if count == _SEVEN_DAY_MINUTES:
        _WEEK_QUALITY_MINUTES = payload
    return payload


def _economics_payload(document: dict[str, object]) -> bytes:
    return (json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def write_sufficient_package(
    root: Path,
    run_id: UUID,
    *,
    economics: dict[str, object] | bytes | None | object = _DEFAULT_ECONOMICS,
    started_at_ms: int = 0,
    terminated_at_ms: int = _SEVEN_DAY_MS,
    quality_minute_count: int = _SEVEN_DAY_MINUTES,
    mappings: list[dict[str, object]] | None = None,
    extra_declared: dict[str, bytes] | None = None,
    envelope_payload: bytes = FIXTURE_BOOK,
) -> Path:
    """Sealed synthetic package with a 7-day minute grid. Not a capture fixture."""
    root.mkdir(parents=True, exist_ok=True)
    members: dict[str, bytes] = {
        "control_evidence/records.ndjson": (
            json.dumps(
                {
                    "recorded_at_ms": 1,
                    "kind": "epoch",
                    "payload_sha256": "a" * 64,
                }
            )
            + "\n"
        ).encode("utf-8"),
        "raw_batches/0.bin": envelope_payload,
        "raw_envelopes/records.ndjson": (
            json.dumps(
                {
                    "envelope_index": 0,
                    "observed_at_ms": 1,
                    "venue": "hyperliquid",
                    "payload_hex": envelope_payload.hex(),
                }
            )
            + "\n"
        ).encode("utf-8"),
        "quality_minutes/records.ndjson": _quality_minutes_payload(quality_minute_count),
        "mapping_snapshot.json": (
            json.dumps({"mappings": [SAMPLE_MAPPING] if mappings is None else mappings}) + "\n"
        ).encode("utf-8"),
        "terminal.json": (
            json.dumps({"terminated_at_ms": terminated_at_ms, "status": "sealed"}) + "\n"
        ).encode("ascii"),
    }
    if extra_declared:
        members.update(extra_declared)
    if economics is _DEFAULT_ECONOMICS:
        members["economics.json"] = _economics_payload(passing_economics())
    elif economics is None:
        pass
    elif type(economics) is bytes:
        members["economics.json"] = economics
    elif type(economics) is dict:
        members["economics.json"] = _economics_payload(economics)
    else:
        raise TypeError("economics must be dict, bytes, or None")
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
        "venue_set": ["hyperliquid", "lighter"],
        "members": declared,
    }
    unsigned["manifest_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    (root / "manifest.json").write_bytes(canonical_json_bytes(unsigned))
    return root


def write_valid_package(
    root: Path,
    run_id: UUID,
    *,
    mappings: list[dict[str, object]] | None = None,
    envelope_payload: bytes = FIXTURE_BOOK,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    members: dict[str, bytes] = {
        "control_evidence/records.ndjson": (
            json.dumps(
                {
                    "recorded_at_ms": 1,
                    "kind": "epoch",
                    "payload_sha256": "a" * 64,
                }
            )
            + "\n"
        ).encode("utf-8"),
        "raw_batches/0.bin": envelope_payload,
        "raw_envelopes/records.ndjson": (
            json.dumps(
                {
                    "envelope_index": 0,
                    "observed_at_ms": 1,
                    "venue": "hyperliquid",
                    "payload_hex": envelope_payload.hex(),
                }
            )
            + "\n"
        ).encode("utf-8"),
        "quality_minutes/records.ndjson": (
            json.dumps(
                {
                    "minute_start_ms": 0,
                    "venue": "hyperliquid",
                    "accepted": 1,
                    "rejected": 0,
                }
            )
            + "\n"
        ).encode("utf-8"),
        "mapping_snapshot.json": (
            json.dumps({"mappings": [SAMPLE_MAPPING] if mappings is None else mappings}) + "\n"
        ).encode("utf-8"),
        "terminal.json": (json.dumps({"terminated_at_ms": 2, "status": "sealed"}) + "\n").encode(
            "ascii"
        ),
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
        "started_at_ms": 0,
        "venue_set": ["hyperliquid", "lighter"],
        "members": declared,
    }
    unsigned["manifest_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    (root / "manifest.json").write_bytes(canonical_json_bytes(unsigned))
    return root


def rebind_member(root: Path, relative: str, payload: bytes) -> None:
    target = root / relative
    target.write_bytes(payload)
    from mee_readonly_analyzer.frozen_package.codec import decode_canonical_json

    manifest = decode_canonical_json((root / "manifest.json").read_bytes())
    assert isinstance(manifest, dict)
    members = manifest["members"]
    assert isinstance(members, list)
    for member in members:
        assert isinstance(member, dict)
        if member["path"] == relative:
            member["sha256"] = sha256_bytes(payload)
            member["length"] = len(payload)
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(unsigned))
    (root / "manifest.json").write_bytes(canonical_json_bytes(manifest))
