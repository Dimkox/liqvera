"""Canonical Liqvera reports built from one strictly inspected immutable input."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path
from uuid import UUID

from liqvera_contracts.exact import ExactDecimal
from liqvera_readonly_analyzer.vwap import DepthRejected, Side, sweep_depth

from liqvera_evidence_report.calculation import _display, _price_impact_bps, _rational, _timestamp
from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest, identifier
from liqvera_evidence_report.schema_validation import validate
from liqvera_evidence_report.sealed_input import InspectedInput, inspect_package

VERSIONS = [
    {"name": "liqvera-contracts", "version": "0.2.0"},
    {"name": "liqvera-readonly-analyzer", "version": "0.2.0"},
    {"name": "liqvera-public-capture", "version": "0.2.0"},
    {"name": "liqvera-evidence-report", "version": "0.2.0"},
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
    include_mezo_dex: bool = False

    def __post_init__(self) -> None:
        if type(self.report_id) is not UUID or type(self.side) is not Side:
            raise EvidenceRejected("INVALID_INPUT")
        if type(self.quantity_base) is not ExactDecimal or self.quantity_base.scaled <= 0:
            raise EvidenceRejected("INVALID_INPUT")
        if type(self.engine_commit) is not str or re.fullmatch(r"[0-9a-f]{40}", self.engine_commit) is None:
            raise EvidenceRejected("INVALID_INPUT")
        if self.created_at_ms is not None and (type(self.created_at_ms) is not int or self.created_at_ms < 0):
            raise EvidenceRejected("INVALID_INPUT")
        if type(self.include_mezo_dex) is not bool:
            raise EvidenceRejected("INVALID_INPUT")


@dataclass(frozen=True)
class BuiltReport:
    document: dict
    report_bytes: bytes
    report_sha256: str
    input_members: dict[str, bytes]
    algorithm_bytes: bytes
    dependency_bytes: bytes
    extra_members: dict[str, bytes] = field(default_factory=dict)


def parse_request(body: object, *, engine_commit: str) -> ReportRequest:
    if type(body) is not dict or set(body) not in (
        {"report_id", "instrument_id", "side", "quantity_base"},
        {"report_id", "instrument_id", "side", "quantity_base", "mezo_dex"},
    ) or ("mezo_dex" in body and body["mezo_dex"] is not True):
        raise EvidenceRejected("INVALID_INPUT")
    if body["instrument_id"] != "hyperliquid:BTC:perpetual":
        raise EvidenceRejected("UNSUPPORTED_INSTRUMENT")
    quantity = body["quantity_base"]
    if type(quantity) is not str or len(quantity) > 32 or re.fullmatch(r"[+]?[0-9]+(?:\.[0-9]{1,8})?", quantity) is None:
        raise EvidenceRejected("INVALID_INPUT")
    try:
        return ReportRequest(UUID(identifier(body["report_id"])), Side(body["side"]),
                             ExactDecimal.parse(quantity), engine_commit,
                             include_mezo_dex=body.get("mezo_dex", False))
    except (ValueError, TypeError) as error:
        raise EvidenceRejected("INVALID_INPUT") from error


def algorithm_document(engine_commit: str, dependencies: bytes, live_identity_approved: bool = False) -> dict:
    return {
        "schema": "liqvera-evidence-algorithm/v1", "calculation_version": "snapshot-sweep/v1",
        "policy_version": "snapshot-policy/v1", "serialization_version": "canonical-json/v1",
        "engine_commit": engine_commit, "package_versions": VERSIONS,
        "dependency_lock_sha256": digest(dependencies), "maximum_source_age_ms": 5000,
        "maximum_future_skew_ms": 1000, "maximum_metadata_age_ms": 86_400_000,
        "live_identity_approved": live_identity_approved, "display_precision": 28, "display_rounding": "ROUND_HALF_EVEN",
        "boundary": "Integrity and recalculation do not authenticate the exchange or promise execution.",
    }


def build_report(package_root: Path, request: ReportRequest, *, mezo_capture: dict | None = None) -> BuiltReport:
    return build_inspected_report(inspect_package(package_root), request, mezo_capture=mezo_capture)


def build_inspected_report(evidence: InspectedInput, request: ReportRequest, *, mezo_capture: dict | None = None) -> BuiltReport:
    if type(request) is not ReportRequest or type(evidence) is not InspectedInput:
        raise EvidenceRejected("INVALID_INPUT")
    book = evidence.book
    mode = evidence.capture["source_mode"]
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
    dependencies = files("liqvera_evidence_report").joinpath("resources", "runtime-dependencies.txt").read_bytes()
    algorithm = algorithm_document(request.engine_commit, dependencies, mode == "live-public")
    validate("algorithm.schema.json", algorithm)
    algorithm_bytes = canonical_json_bytes(algorithm)
    inputs = {f"sealed-input/{name}": payload for name, payload in evidence.members.items()}
    inputs["algorithm.json"] = algorithm_bytes
    inputs["runtime-dependencies.txt"] = dependencies
    impact = _price_impact_bps(book, request.side, fill.vwap)
    quantities = {"notional_quote": fill.notional_quote, "vwap": fill.vwap,
                  "worst_price": fill.worst_price, "price_impact_bps": impact}
    document = {
        "schema": "liqvera-evidence-report/v1", "report_id": str(request.report_id),
        "identity": {
            "venue": "hyperliquid", "instrument_id": "hyperliquid:BTC:perpetual",
            "product_kind": "perpetual", "payoff_kind": "linear", "base_asset": "BTC",
            "quote_asset": "USD", "settlement_asset": mapping.identity.settlement_asset,
            "quantity_unit": "BTC", "displayed_size_unit": "coin", "contract_multiplier": "1",
            "mapping_version": mapping.mapping_version,
            "evidence": [{"reference": mapping.evidence_reference, "sha256": mapping.evidence_sha256}],
        },
        "request": {"side": request.side.value, "quantity_base": str(request.quantity_base),
                    **({"mezo_dex": True} if request.include_mezo_dex else {})},
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
            "snapshot_status": "SIMULATED" if mode == "fixture" else "VALID_FOR_SNAPSHOT_CALCULATION",
            "reason_codes": ["SIMULATED_SOURCE"] if mode == "fixture" else [],
            "checks": [{"name": name, "result": "PASS"} for name in (
                "sealed bytes and source bindings", "exact snapshot sweep")]
                + [{"name": "live identity approval", "result": "PASS" if mode == "live-public" else "UNCERTAIN"}],
            "limitations": ([
                "SIMULATED fixture input and timestamps; never eligible for a chargeable quote.",
            ] if mode == "fixture" else [
                "Public snapshot identity is policy-validated; exchange authenticity is not independently attested.",
            ]) + [
                "Calculation over the available snapshot depth, at most 20 levels per side.",
                "Hypothetical snapshot sweep; no fees, funding, net PnL, or execution guarantee.",
                "Hashes establish integrity relative to the bundle, not exchange authenticity.",
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
    if "source/mezo-dex.json" in evidence.members:
        from liqvera_evidence_report.evidence_io import strict_json
        sealed_mezo = strict_json(evidence.members["source/mezo-dex.json"])
        if mezo_capture is not None and mezo_capture != sealed_mezo:
            raise EvidenceRejected("MEZO_DEX_INVALID_EVIDENCE")
        mezo_capture = sealed_mezo
    extras = {}
    if mezo_capture is not None:
        from liqvera_evidence_report.mezo_dex import build_dex_report, dex_members, venue_comparison
        try:
            dex = build_dex_report(mezo_capture, side=request.side.value,
                                   quantity_btc=str(request.quantity_base))
            extras = dex_members(mezo_capture)
        except ValueError as error:
            raise EvidenceRejected("MEZO_DEX_INVALID_EVIDENCE") from error
        document["mezo_dex"] = dex
        document["venue_comparison"] = venue_comparison(dex, fill.vwap, side=request.side.value)
        inputs.update(extras)
        document["reproducibility"]["input_files"] = [
            {"path": name, "sha256": digest(raw)} for name, raw in sorted(inputs.items())]
    validate("report.schema.json", document)
    raw = canonical_json_bytes(document)
    return BuiltReport(document, raw, digest(raw), dict(evidence.members), algorithm_bytes, dependencies, extras)
