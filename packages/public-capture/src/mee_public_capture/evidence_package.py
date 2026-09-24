"""Non-destructive F3 writer preserving the inherited sealed package format."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from uuid import UUID

from mee_public_capture.evidence_capture import CapturedResponse, capture_responses
from mee_public_capture.package import PACKAGE_SCHEMA, canonical_json_bytes, sha256_bytes

FIXTURE_REFERENCE = "https://schemas.liqvera.invalid/fixture/btc-perpetual/v1"
FIXTURE_IDENTITY = {
    "schema": "mee-fixture-identity/v1", "source_mode": "fixture",
    "reference": FIXTURE_REFERENCE, "base_asset": "BTC", "quote_asset": "USD",
    "settlement_asset": "USDC", "product_kind": "perp", "payoff_kind": "linear",
    "displayed_size_unit": "coin", "contract_multiplier": "1",
    "limitation": "Synthetic mapping for simulation only; no live identity approval.",
}


def fixture_mapping() -> dict[str, object]:
    return {
        "mapping_id": "fixture-btc-perpetual", "mapping_version": "fixture/v1",
        "decision": "APPROVED", "venue": "hyperliquid", "symbol": "BTC",
        "identity": {key: FIXTURE_IDENTITY[key] for key in (
            "base_asset", "quote_asset", "product_kind", "settlement_asset", "payoff_kind")},
        "evidence_sha256": sha256_bytes(canonical_json_bytes(FIXTURE_IDENTITY)),
        "evidence_reference": FIXTURE_REFERENCE, "valid_from_ms": 0,
        "valid_until_ms": None, "reviewed_contract_multiplier": "1",
        "displayed_size_unit": "coin", "quantity_step": "0.00001", "price_tick": "0.1",
        "price_decimals": None, "max_price_significant_digits": None,
        "min_quantity": None, "min_notional": "10",
    }


def capture_members(capture_id: UUID, source_mode: str,
                    responses: tuple[CapturedResponse, CapturedResponse]) -> dict[str, bytes]:
    if type(capture_id) is not UUID or source_mode not in {"fixture", "live-public"}:
        raise ValueError("INVALID_INPUT")
    metadata, book = responses
    if (metadata.kind, book.kind) != ("metadata", "book"):
        raise ValueError("INVALID_DATASET")
    observed = book.received_at_ms
    # Live metadata is retained without inventing a human-approved mapping.
    mapping = [fixture_mapping()] if source_mode == "fixture" else []
    members = {
        "control_evidence/records.ndjson": canonical_json_bytes({
            "recorded_at_ms": observed, "kind": "epoch",
            "payload_sha256": sha256_bytes(book.payload)}),
        "raw_batches/0.bin": book.payload,
        "raw_envelopes/records.ndjson": canonical_json_bytes({
            "envelope_index": 0, "observed_at_ms": observed, "venue": "hyperliquid",
            "payload_hex": book.payload.hex()}),
        "quality_minutes/records.ndjson": canonical_json_bytes({
            "minute_start_ms": observed - observed % 60_000,
            "venue": "hyperliquid", "accepted": 1, "rejected": 0}),
        "mapping_snapshot.json": canonical_json_bytes({"mappings": mapping}),
        "terminal.json": canonical_json_bytes({"terminated_at_ms": observed, "status": "sealed"}),
        "source/metadata.bin": metadata.payload,
        "source/book.bin": book.payload,
        "source/capture.json": canonical_json_bytes({
            "schema": "mee-evidence-capture/v1", "capture_id": str(capture_id),
            "source_mode": source_mode, "identity_status": "SIMULATED" if mapping else "UNVERIFIED",
            "responses": [item.evidence(source_mode) for item in responses]}),
    }
    if mapping:
        members["source/mapping-evidence.json"] = canonical_json_bytes(FIXTURE_IDENTITY)
    manifest = {
        "schema": PACKAGE_SCHEMA, "capture_run_id": str(capture_id),
        "started_at_ms": metadata.started_at_ms, "venue_set": ["hyperliquid"],
        "members": [{"path": path, "sha256": sha256_bytes(raw), "length": len(raw)}
                    for path, raw in sorted(members.items())],
    }
    manifest["manifest_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    members["manifest.json"] = canonical_json_bytes(manifest)
    return members


def capture_package(root: Path, capture_id: UUID, *, source_mode: str = "fixture") -> Path:
    """Publish only a new server-generated capture directory under an owned root."""
    root = Path(root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError("INVALID_INPUT")
    if type(capture_id) is not UUID:
        raise ValueError("INVALID_INPUT")
    target = root / str(capture_id)
    lock = root / f".{capture_id}.lock"
    lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    staging = None
    try:
        if os.path.lexists(target):
            raise FileExistsError("capture already exists")
        members = capture_members(capture_id, source_mode, capture_responses(source_mode))
        staging = Path(tempfile.mkdtemp(prefix=f".{capture_id}.", dir=root))
        staging.chmod(0o750)
        for name, raw in members.items():
            path = staging / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.parent.chmod(0o750)
            with path.open("xb") as stream:
                os.fchmod(stream.fileno(), 0o640)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if sha256_bytes(path.read_bytes()) != sha256_bytes(raw):
                raise OSError("capture integrity failure")
        for directory, _, _ in os.walk(staging, topdown=False):
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        if os.path.lexists(target):
            raise FileExistsError("capture already exists")
        staging.rename(target)
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        return target
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        os.close(lock_fd)
        lock.unlink()
