"""Fixture-only exact report assembly over a sealed Stage A package."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from mee_contracts.exact import decimal_from_fraction, fraction_from_decimal
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.identity import bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import ReconstructedBook, reconstruct_books
from mee_readonly_analyzer.verdict import evaluate_frozen_package
from mee_readonly_analyzer.vwap import DepthRejected, Side, sweep_depth

from mee_evidence_report.canonical import canonical_json_bytes
from mee_evidence_report.model import BuiltMvpReport, MvpReportRejected, MvpReportRequest

_INSTRUMENT_ID = "hyperliquid:BTC:perpetual"
_DEPENDENCY_LOCK = b"mee-contracts==0.1.0\nmee-readonly-analyzer==0.1.0\n"


def build_simulated_report(
    package_root: Path,
    request: MvpReportRequest,
) -> BuiltMvpReport:
    """Build one deterministic simulated report from retained fixture evidence."""

    if not isinstance(package_root, Path):
        raise TypeError("package_root must be Path")
    if type(request) is not MvpReportRequest:
        raise TypeError("request must be MvpReportRequest")

    try:
        reader = FrozenPackageEvidenceReader(package_root)
        run_id = reader.capture_run_id
        capture = reader.read_capture_manifest(run_id)
        envelopes = tuple(reader.iter_raw_envelopes(run_id))
        mappings = reader.read_mapping_snapshot(run_id).mappings
        books = bind_reconstructed_books(reconstruct_books(envelopes, mappings), mappings)
        book = _select_fixture_book(books)
        fill = sweep_depth(book, request.side, request.quantity_base)
    except DepthRejected as error:
        raise MvpReportRejected("DEPTH_INSUFFICIENT") from error
    except MvpReportRejected:
        raise
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise MvpReportRejected("INVALID_DATASET") from error

    source_at_ms = book.snapshot.received_timestamp_ms
    created_at_ms = source_at_ms if request.created_at_ms is None else request.created_at_ms
    manifest_bytes = (package_root / "manifest.json").read_bytes()
    package_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_document = json.loads(manifest_bytes)
    stage_a = evaluate_frozen_package(package_root)
    impact = _price_impact_bps(book, request.side, fill.vwap)
    mapping = book.mapping
    if mapping is None:  # bind_reconstructed_books makes this unreachable.
        raise MvpReportRejected("IDENTITY_UNVERIFIED")

    document: dict[str, object] = {
        "schema": "mee-evidence-report/v1",
        "report_id": str(request.report_id),
        "identity": {
            "venue": "hyperliquid",
            "instrument_id": _INSTRUMENT_ID,
            "product_kind": "perpetual",
            "payoff_kind": "linear",
            "base_asset": "BTC",
            "quote_asset": "USD",
            "settlement_asset": "USDC",
            "quantity_unit": "BTC",
            "displayed_size_unit": "coin",
            "contract_multiplier": "1",
            "mapping_version": mapping.mapping_version,
            "evidence": [
                {
                    "reference": "https://example.invalid/liqvera/mvp-fixture-mapping/v1",
                    "sha256": mapping.evidence_sha256,
                }
            ],
        },
        "request": {"side": request.side.value, "quantity_base": str(request.quantity_base)},
        "source": {
            "source_mode": "fixture",
            "started_at": _timestamp(capture.started_at_ms),
            "observed_at": _timestamp(source_at_ms),
            "source_at": _timestamp(source_at_ms),
            "created_at": _timestamp(created_at_ms),
            "build_age_ms": created_at_ms - source_at_ms,
            "payload_sha256": fill.payload_sha256,
            "package_sha256": package_sha256,
            "available_bid_levels": len(book.snapshot.bids),
            "available_ask_levels": len(book.snapshot.asks),
        },
        "calculation": {
            "requested_quantity": str(request.quantity_base),
            "filled_quantity": _display(fill.filled_quantity),
            "notional_quote": _rational(fill.notional_quote),
            "vwap": _rational(fill.vwap),
            "worst_price": _rational(fill.worst_price),
            "price_impact_bps": _rational(impact),
            "consumed_levels": fill.consumed_levels,
            "display": {
                "notional_quote": _display(fill.notional_quote),
                "vwap": _display(fill.vwap),
                "worst_price": _display(fill.worst_price),
                "price_impact_bps": _display(impact),
            },
            "display_precision": 28,
            "display_rounding": "ROUND_HALF_EVEN",
        },
        "quality": {
            "snapshot_status": "SIMULATED",
            "reason_codes": ["SIMULATED_SOURCE"],
            "checks": [
                {"name": "sealed package integrity", "result": "PASS"},
                {"name": "fixture identity binding", "result": "PASS"},
                {"name": "exact depth sweep", "result": "PASS"},
                {"name": "live source provenance", "result": "UNCERTAIN"},
            ],
            "limitations": [
                "Fixture input is simulated and cannot establish live-source acceptance.",
                "The fixture timestamp is retained evidence, not a live freshness claim.",
                "This unverified MVP has no hardened bundle or offline verifier.",
                "The calculation is hypothetical and excludes fees, funding, and net PnL.",
            ],
            "stage_a": {
                "schema": stage_a.schema,
                "package_schema": stage_a.package_schema,
                "capture_run_id": (
                    None if stage_a.capture_run_id is None else str(stage_a.capture_run_id)
                ),
                "decision": stage_a.decision.value,
                "reasons": [reason.value for reason in stage_a.reasons],
            },
        },
        "reproducibility": {
            "engine_commit": request.engine_commit,
            "package_versions": [
                {"name": "mee-contracts", "version": "0.1.0"},
                {"name": "mee-readonly-analyzer", "version": "0.1.0"},
                {"name": "mee-evidence-report", "version": "0.1.0"},
            ],
            "lockfile_digests": [
                {
                    "path": "mvp/runtime-dependencies.txt",
                    "sha256": hashlib.sha256(_DEPENDENCY_LOCK).hexdigest(),
                }
            ],
            "calculation_version": "snapshot-sweep/v1",
            "policy_version": "snapshot-policy/v1",
            "serialization_version": "canonical-json/v1",
            "input_files": _input_file_digests(manifest_document, package_sha256),
        },
        "boundaries": {
            "execution_authority": "NONE",
            "fees_calculated": False,
            "funding_calculated": False,
            "net_pnl_calculated": False,
            "execution_promise": False,
            "calculation_label": "hypothetical snapshot sweep",
        },
    }
    report_bytes = canonical_json_bytes(document)
    return BuiltMvpReport(
        document=document,
        report_bytes=report_bytes,
        report_sha256=hashlib.sha256(report_bytes).hexdigest(),
    )


def _select_fixture_book(books: tuple[ReconstructedBook, ...]) -> ReconstructedBook:
    candidates = [
        book
        for book in books
        if book.snapshot.venue == "HYPERLIQUID" and book.snapshot.symbol == "BTC"
    ]
    if not candidates:
        raise MvpReportRejected("UNSUPPORTED_INSTRUMENT")
    return max(candidates, key=lambda book: book.envelope_index)


def _price_impact_bps(book: ReconstructedBook, side: Side, vwap: Fraction) -> Fraction:
    if side is Side.BUY:
        best = fraction_from_decimal(book.snapshot.best_ask.price)
        return (vwap - best) * 10_000 / best
    best = fraction_from_decimal(book.snapshot.best_bid.price)
    return (best - vwap) * 10_000 / best


def _rational(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _display(value: Fraction) -> str:
    rendered: Decimal = decimal_from_fraction(value)
    return format(rendered, "f")


def _timestamp(milliseconds: int) -> str:
    instant = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=milliseconds)
    if instant.microsecond == 0:
        return instant.strftime("%Y-%m-%dT%H:%M:%SZ")
    return instant.strftime("%Y-%m-%dT%H:%M:%S.") + f"{instant.microsecond // 1000:03d}Z"


def _input_file_digests(manifest: object, manifest_sha256: str) -> list[dict[str, str]]:
    if type(manifest) is not dict or type(manifest.get("members")) is not list:
        raise MvpReportRejected("INVALID_DATASET")
    result = [{"path": "sealed-input/manifest.json", "sha256": manifest_sha256}]
    for member in manifest["members"]:
        if type(member) is not dict:
            raise MvpReportRejected("INVALID_DATASET")
        path = member.get("path")
        digest = member.get("sha256")
        if type(path) is not str or type(digest) is not str:
            raise MvpReportRejected("INVALID_DATASET")
        result.append({"path": f"sealed-input/{path}", "sha256": digest})
    return sorted(result, key=lambda item: item["path"])
