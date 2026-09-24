"""Strict F3 inspection before using the retained Stage A reconstruction."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from mee_contracts.exact import ExactDecimal
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.identity import bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import ReconstructedBook, reconstruct_books
from mee_readonly_analyzer.verdict import evaluate_frozen_package

from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.evidence_io import (
    EvidenceRejected, digest, identifier, integer, object_keys, read_tree, safe_member, strict_json,
)
from mee_evidence_report.schema_validation import validate

BASE_MEMBERS = frozenset({
    "manifest.json", "control_evidence/records.ndjson", "raw_batches/0.bin",
    "raw_envelopes/records.ndjson", "quality_minutes/records.ndjson",
    "mapping_snapshot.json", "terminal.json", "source/capture.json",
    "source/metadata.bin", "source/book.bin",
})
MAPPING_KEYS = {
    "mapping_id", "mapping_version", "decision", "venue", "symbol", "identity",
    "evidence_sha256", "evidence_reference", "valid_from_ms", "valid_until_ms",
    "reviewed_contract_multiplier", "displayed_size_unit", "quantity_step", "price_tick",
    "price_decimals", "max_price_significant_digits", "min_quantity", "min_notional",
}
IDENTITY = {"base_asset": "BTC", "quote_asset": "USD", "settlement_asset": "USDC",
            "product_kind": "perp", "payoff_kind": "linear"}
FIXTURE_REFERENCE = "https://schemas.liqvera.invalid/fixture/btc-perpetual/v1"


@dataclass(frozen=True)
class InspectedInput:
    members: dict[str, bytes]
    capture: dict
    book: ReconstructedBook
    stage_a: dict
    package_sha256: str


def inspect_package(root: Path) -> InspectedInput:
    return inspect_members(read_tree(root))


def inspect_members(members: dict[str, bytes]) -> InspectedInput:
    try:
        return _inspect(members)
    except EvidenceRejected:
        raise
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        raise EvidenceRejected("INVALID_DATASET") from error


def _inspect(members: dict[str, bytes]) -> InspectedInput:
    capture = strict_json(members["source/capture.json"])
    validate("capture-evidence.schema.json", capture)
    mode = capture["source_mode"]
    expected = BASE_MEMBERS | ({"source/mapping-evidence.json"} if mode == "fixture" else set())
    if set(members) != expected:
        raise EvidenceRejected("INVALID_DATASET")
    manifest = object_keys(strict_json(members["manifest.json"]), {
        "schema", "capture_run_id", "started_at_ms", "venue_set", "members", "manifest_sha256"})
    if (manifest["schema"] != "mee-readonly-frozen-package/v1"
            or manifest["venue_set"] != ["hyperliquid"]
            or identifier(manifest["capture_run_id"]) != capture["capture_id"]):
        raise EvidenceRejected("INVALID_DATASET")
    unsigned = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    if (digest(canonical_json_bytes(unsigned)) != manifest["manifest_sha256"]
            or canonical_json_bytes(manifest) != members["manifest.json"]):
        raise EvidenceRejected("INVALID_DATASET")
    declarations = manifest["members"]
    if type(declarations) is not list or len(declarations) != len(members) - 1:
        raise EvidenceRejected("INVALID_DATASET")
    seen = set()
    for entry in declarations:
        object_keys(entry, {"path", "sha256", "length"})
        path = safe_member(entry["path"])
        if path in seen or path == "manifest.json" or path not in members:
            raise EvidenceRejected("INVALID_DATASET")
        seen.add(path)
        if integer(entry["length"]) != len(members[path]) or entry["sha256"] != digest(members[path]):
            raise EvidenceRejected("INVALID_DATASET")
    if seen != set(members) - {"manifest.json"}:
        raise EvidenceRejected("INVALID_DATASET")
    metadata, response = capture["responses"]
    for item, kind, request_body in (
        (metadata, "metadata", '{"type":"meta"}'),
        (response, "book", '{"type":"l2Book","coin":"BTC"}'),
    ):
        if (item["kind"] != kind or item["request_body"] != request_body
                or item["source_mode"] != mode or item["payload_path"] != f"source/{kind}.bin"
                or item["payload_sha256"] != digest(members[item["payload_path"]])
                or item["payload_length"] != len(members[item["payload_path"]])):
            raise EvidenceRejected("INVALID_DATASET")
        if item["received_at_ms"] < item["started_at_ms"]:
            raise EvidenceRejected("CLOCK_SKEW")
        if item["elapsed_ns"] > 12_000_000_000:
            raise EvidenceRejected("SOURCE_UNAVAILABLE")
    if (metadata["received_at_ms"] > response["started_at_ms"]
            or manifest["started_at_ms"] != metadata["started_at_ms"]):
        raise EvidenceRejected("INVALID_DATASET")
    if mode == "fixture" and any(item["elapsed_ns"] != 0 for item in (metadata, response)):
        raise EvidenceRejected("INVALID_DATASET")
    received = response["received_at_ms"]
    if received - metadata["received_at_ms"] > 86_400_000:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    if mode == "live-public":
        if (received - metadata["started_at_ms"] > 12_000
                or capture["identity_status"] != "UNVERIFIED"):
            raise EvidenceRejected("INVALID_DATASET")
        for item in (metadata, response):
            measured_ms = item["elapsed_ns"] // 1_000_000
            wall_ms = item["received_at_ms"] - item["started_at_ms"]
            if abs(measured_ms - wall_ms) > 1000:
                raise EvidenceRejected("CLOCK_SKEW")
    raw = members["source/book.bin"]
    book_doc = strict_json(raw)
    if type(book_doc) is not dict:
        raise EvidenceRejected("INVALID_DATASET")
    if book_doc.get("coin") != "BTC":
        raise EvidenceRejected("IDENTITY_MISMATCH")
    source_at = integer(book_doc.get("time"))
    if mode == "live-public":
        if received - source_at > 5000:
            raise EvidenceRejected("STALE_SOURCE")
        if source_at - received > 1000:
            raise EvidenceRejected("CLOCK_SKEW")
    levels = book_doc.get("levels")
    if type(levels) is not list or len(levels) != 2:
        raise EvidenceRejected("INVALID_DATASET")
    for index, side in enumerate(levels):
        if type(side) is not list or not 1 <= len(side) <= 20:
            raise EvidenceRejected("INVALID_DATASET")
        previous = None
        for level in side:
            if type(level) is not dict or not {"px", "sz"} <= set(level) <= {"px", "sz", "n"}:
                raise EvidenceRejected("INVALID_DATASET")
            for name in ("px", "sz"):
                text = level[name]
                if type(text) is not str or len(text) > 32 or not text.isascii():
                    raise EvidenceRejected("INVALID_DATASET")
            price, size = ExactDecimal.parse(level["px"]), ExactDecimal.parse(level["sz"])
            # The existing reconstruction contract requires positive sizes;
            # zero-size rows are rejected without normalization.
            if price.scaled <= 0 or size.scaled <= 0:
                raise EvidenceRejected("INVALID_DATASET")
            if "n" in level:
                integer(level["n"])
            if previous is not None and ((index == 0 and price.scaled >= previous)
                                          or (index == 1 and price.scaled <= previous)):
                raise EvidenceRejected("INVALID_DATASET")
            previous = price.scaled
    if ExactDecimal.parse(levels[0][0]["px"]) >= ExactDecimal.parse(levels[1][0]["px"]):
        raise EvidenceRejected("CROSSED_BOOK")
    meta = strict_json(members["source/metadata.bin"])
    if type(meta) is not dict or type(meta.get("universe")) is not list:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    candidates = [item for item in meta["universe"] if type(item) is dict and item.get("name") == "BTC"]
    if len(candidates) != 1 or type(candidates[0].get("szDecimals")) is not int:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    if not 0 <= candidates[0]["szDecimals"] <= 8 or candidates[0].get("isDelisted", False) is not False:
        raise EvidenceRejected("UNSUPPORTED_INSTRUMENT")
    if members["raw_batches/0.bin"] != raw:
        raise EvidenceRejected("INVALID_DATASET")
    envelope = object_keys(strict_json(members["raw_envelopes/records.ndjson"]), {
        "envelope_index", "observed_at_ms", "venue", "payload_hex"})
    if (type(envelope["envelope_index"]) is not int or envelope["envelope_index"] != 0
            or type(envelope["observed_at_ms"]) is not int or envelope["observed_at_ms"] != received
            or envelope["venue"] != "hyperliquid" or envelope["payload_hex"] != raw.hex()):
        raise EvidenceRejected("INVALID_DATASET")
    for name, expected_record in {
        "terminal.json": {"terminated_at_ms": received, "status": "sealed"},
        "control_evidence/records.ndjson": {"recorded_at_ms": received, "kind": "epoch", "payload_sha256": digest(raw)},
        "quality_minutes/records.ndjson": {"minute_start_ms": received - received % 60_000,
                                           "venue": "hyperliquid", "accepted": 1, "rejected": 0},
    }.items():
        if canonical_json_bytes(strict_json(members[name])) != canonical_json_bytes(expected_record):
            raise EvidenceRejected("INVALID_DATASET")
    mapping_doc = object_keys(strict_json(members["mapping_snapshot.json"]), {"mappings"})
    if mode == "live-public":
        if mapping_doc["mappings"] != []:
            raise EvidenceRejected("IDENTITY_UNVERIFIED")
        # No runtime string, environment setting, or bundled claim can approve
        # absent reviewed evidence. A later reviewed implementation owns this gate.
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    if capture["identity_status"] != "SIMULATED" or type(mapping_doc["mappings"]) is not list or len(mapping_doc["mappings"]) != 1:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    mapping = object_keys(mapping_doc["mappings"][0], MAPPING_KEYS)
    source = strict_json(members["source/mapping-evidence.json"])
    expected_source = {
        "schema": "mee-fixture-identity/v1", "source_mode": "fixture", "reference": FIXTURE_REFERENCE,
        **IDENTITY, "displayed_size_unit": "coin", "contract_multiplier": "1",
        "limitation": "Synthetic mapping for simulation only; no live identity approval.",
    }
    if source != expected_source or canonical_json_bytes(source) != members["source/mapping-evidence.json"]:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    expected_mapping = {
        "mapping_id": "fixture-btc-perpetual", "mapping_version": "fixture/v1",
        "decision": "APPROVED", "venue": "hyperliquid", "symbol": "BTC", "identity": IDENTITY,
        "evidence_sha256": digest(members["source/mapping-evidence.json"]), "evidence_reference": FIXTURE_REFERENCE,
        "valid_from_ms": 0, "valid_until_ms": None, "reviewed_contract_multiplier": "1",
        "displayed_size_unit": "coin", "quantity_step": "0.00001", "price_tick": "0.1",
        "price_decimals": None, "max_price_significant_digits": None, "min_quantity": None, "min_notional": "10",
    }
    if canonical_json_bytes(mapping) != canonical_json_bytes(expected_mapping):
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    # Reuse the inherited reader over a private snapshot of already bounded bytes.
    # Original files are never reopened during reconstruction or bundle assembly.
    with tempfile.TemporaryDirectory(prefix="liqvera-inspect-") as directory:
        root = Path(directory)
        for name, payload in members.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        reader = FrozenPackageEvidenceReader(root)
        mappings = reader.read_mapping_snapshot(reader.capture_run_id).mappings
        books = bind_reconstructed_books(reconstruct_books(tuple(reader.iter_raw_envelopes(reader.capture_run_id)), mappings), mappings)
        stage = evaluate_frozen_package(root)
    if len(books) != 1:
        raise EvidenceRejected("INVALID_DATASET")
    stage_doc = {"schema": stage.schema, "package_schema": stage.package_schema,
                 "capture_run_id": str(stage.capture_run_id) if stage.capture_run_id else None,
                 "decision": stage.decision.value, "reasons": [reason.value for reason in stage.reasons]}
    return InspectedInput(dict(members), capture, books[0], stage_doc, digest(members["manifest.json"]))
