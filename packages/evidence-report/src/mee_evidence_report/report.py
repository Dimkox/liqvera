"""Canonical F3 reports built from one strictly inspected immutable input."""

from __future__ import annotations

import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from uuid import UUID

from mee_contracts.exact import ExactDecimal
from mee_readonly_analyzer.vwap import DepthRejected, Side, sweep_depth

from mee_evidence_report.builder import _display, _price_impact_bps, _rational, _timestamp
from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.evidence_io import EvidenceRejected, digest, identifier
from mee_evidence_report.schema_validation import validate
from mee_evidence_report.sealed_input import InspectedInput, inspect_package

VERSIONS = [
    {"name": "mee-contracts", "version": "0.1.0"},
    {"name": "mee-readonly-analyzer", "version": "0.1.0"},
    {"name": "mee-evidence-report", "version": "0.1.0"},
    {"name": "jsonschema", "version": "4.23.0"},
    {"name": "referencing", "version": "0.35.1"},
]


@dataclass(frozen=True)
class ReportRequest:
    report_id: UUID
    side: Side
    quantity_base: ExactDecimal
    engine_commit: str
    created_at_ms: int | None = None

    def __post_init__(self) -> None:
        if type(self.report_id) is not UUID or type(self.side) is not Side:
            raise EvidenceRejected("INVALID_INPUT")
        if type(self.quantity_base) is not ExactDecimal or self.quantity_base.scaled <= 0:
            raise EvidenceRejected("INVALID_INPUT")
        if type(self.engine_commit) is not str or re.fullmatch(r"[0-9a-f]{40}", self.engine_commit) is None:
            raise EvidenceRejected("INVALID_INPUT")
        if self.created_at_ms is not None and (type(self.created_at_ms) is not int or self.created_at_ms < 0):
            raise EvidenceRejected("INVALID_INPUT")


@dataclass(frozen=True)
class BuiltReport:
    document: dict
    report_bytes: bytes
    report_sha256: str
    input_members: dict[str, bytes]
    algorithm_bytes: bytes
    dependency_bytes: bytes


def parse_request(body: object, *, engine_commit: str) -> ReportRequest:
    if type(body) is not dict or set(body) != {"report_id", "instrument_id", "side", "quantity_base"}:
        raise EvidenceRejected("INVALID_INPUT")
    if body["instrument_id"] != "hyperliquid:BTC:perpetual":
        raise EvidenceRejected("UNSUPPORTED_INSTRUMENT")
    quantity = body["quantity_base"]
    if type(quantity) is not str or len(quantity) > 32 or re.fullmatch(r"[+]?[0-9]+(?:\.[0-9]{1,8})?", quantity) is None:
        raise EvidenceRejected("INVALID_INPUT")
    try:
        return ReportRequest(UUID(identifier(body["report_id"])), Side(body["side"]),
                             ExactDecimal.parse(quantity), engine_commit)
    except (ValueError, TypeError) as error:
        raise EvidenceRejected("INVALID_INPUT") from error


def algorithm_document(engine_commit: str, dependencies: bytes) -> dict:
    return {
        "schema": "mee-evidence-algorithm/v1", "calculation_version": "snapshot-sweep/v1",
        "policy_version": "snapshot-policy/v1", "serialization_version": "canonical-json/v1",
        "engine_commit": engine_commit, "package_versions": VERSIONS,
        "dependency_lock_sha256": digest(dependencies), "maximum_source_age_ms": 5000,
        "maximum_future_skew_ms": 1000, "maximum_metadata_age_ms": 86_400_000,
        "live_identity_approved": False, "display_precision": 28, "display_rounding": "ROUND_HALF_EVEN",
        "boundary": "Integrity and recalculation do not authenticate the exchange or promise execution.",
    }


def build_report(package_root: Path, request: ReportRequest) -> BuiltReport:
    return build_inspected_report(inspect_package(package_root), request)


def build_inspected_report(evidence: InspectedInput, request: ReportRequest) -> BuiltReport:
    if type(request) is not ReportRequest or type(evidence) is not InspectedInput:
        raise EvidenceRejected("INVALID_INPUT")
    book = evidence.book
    mode = evidence.capture["source_mode"]
    if mode != "fixture":
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    source_at = book.snapshot.exchange_timestamp_ms
    received = book.snapshot.received_timestamp_ms
    created = received if request.created_at_ms is None else request.created_at_ms
    # The fixture clock is explicitly simulated. A stale fixture is not silently
    # relabeled with current wall time to obtain a schema-valid live report.
    if created < received or source_at - created > 1000:
        raise EvidenceRejected("CLOCK_SKEW")
    if created - source_at > 5000:
        raise EvidenceRejected("STALE_SOURCE")
    try:
        fill = sweep_depth(book, request.side, request.quantity_base)
    except DepthRejected as error:
        raise EvidenceRejected("DEPTH_INSUFFICIENT") from error
    mapping = book.mapping
    if mapping is None:
        raise EvidenceRejected("IDENTITY_UNVERIFIED")
    dependencies = files("mee_evidence_report").joinpath("resources", "runtime-dependencies.txt").read_bytes()
    algorithm = algorithm_document(request.engine_commit, dependencies)
    validate("algorithm.schema.json", algorithm)
    algorithm_bytes = canonical_json_bytes(algorithm)
    inputs = {f"sealed-input/{name}": payload for name, payload in evidence.members.items()}
    inputs["algorithm.json"] = algorithm_bytes
    inputs["runtime-dependencies.txt"] = dependencies
    impact = _price_impact_bps(book, request.side, fill.vwap)
    quantities = {"notional_quote": fill.notional_quote, "vwap": fill.vwap,
                  "worst_price": fill.worst_price, "price_impact_bps": impact}
    document = {
        "schema": "mee-evidence-report/v1", "report_id": str(request.report_id),
        "identity": {
            "venue": "hyperliquid", "instrument_id": "hyperliquid:BTC:perpetual",
            "product_kind": "perpetual", "payoff_kind": "linear", "base_asset": "BTC",
            "quote_asset": "USD", "settlement_asset": mapping.identity.settlement_asset,
            "quantity_unit": "BTC", "displayed_size_unit": "coin", "contract_multiplier": "1",
            "mapping_version": mapping.mapping_version,
            "evidence": [{"reference": mapping.evidence_reference, "sha256": mapping.evidence_sha256}],
        },
        "request": {"side": request.side.value, "quantity_base": str(request.quantity_base)},
        "source": {
            "source_mode": mode, "started_at": _timestamp(evidence.capture["responses"][0]["started_at_ms"]),
            "observed_at": _timestamp(received), "source_at": _timestamp(source_at),
            "created_at": _timestamp(created), "build_age_ms": created - source_at,
            "payload_sha256": fill.payload_sha256, "package_sha256": evidence.package_sha256,
            "available_bid_levels": len(book.snapshot.bids), "available_ask_levels": len(book.snapshot.asks),
        },
        "calculation": {
            "requested_quantity": str(request.quantity_base), "filled_quantity": str(request.quantity_base),
            **{key: _rational(value) for key, value in quantities.items()},
            "consumed_levels": fill.consumed_levels,
            "display": {key: _display(value) for key, value in quantities.items()},
            "display_precision": 28, "display_rounding": "ROUND_HALF_EVEN",
        },
        "quality": {
            "snapshot_status": "SIMULATED", "reason_codes": ["SIMULATED_SOURCE"],
            "checks": [{"name": name, "result": "PASS"} for name in (
                "sealed bytes and source bindings", "explicit simulated identity", "exact snapshot sweep")]
                + [{"name": "live identity approval", "result": "UNCERTAIN"}],
            "limitations": [
                "SIMULATED fixture input and timestamps; never eligible for a chargeable quote.",
                "Calculation over the available snapshot depth, at most 20 levels per side.",
                "Hypothetical snapshot sweep; no fees, funding, net PnL, or execution guarantee.",
                "Hashes establish integrity relative to the bundle, not exchange authenticity.",
                "Live identity approval is absent; live reports remain blocked.",
            ],
            "stage_a": evidence.stage_a,
        },
        "reproducibility": {
            "engine_commit": request.engine_commit, "package_versions": VERSIONS,
            "lockfile_digests": [{"path": "runtime-dependencies.txt", "sha256": digest(dependencies)}],
            "calculation_version": "snapshot-sweep/v1", "policy_version": "snapshot-policy/v1",
            "serialization_version": "canonical-json/v1",
            "input_files": [{"path": name, "sha256": digest(raw)} for name, raw in sorted(inputs.items())],
        },
        "boundaries": {
            "execution_authority": "NONE", "fees_calculated": False, "funding_calculated": False,
            "net_pnl_calculated": False, "execution_promise": False,
            "calculation_label": "hypothetical snapshot sweep",
        },
    }
    validate("report.schema.json", document)
    raw = canonical_json_bytes(document)
    return BuiltReport(document, raw, digest(raw), dict(evidence.members), algorithm_bytes, dependencies)
