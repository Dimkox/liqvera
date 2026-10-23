"""Exact borrower risk reports from fixed-block raw Mezo calls; no RPC here."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from importlib.resources import files
from pathlib import Path
from uuid import UUID

from liqvera_public_capture.public_adapters.mezo_troves import (
    PRICE_FEED,
    SORTED_TROVES,
    TROVE_MANAGER,
    verify_trove_capture,
)

from liqvera_evidence_report.calculation import _display, _timestamp, trove_risk
from liqvera_evidence_report.canonical import canonical_json_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected, digest, strict_json
from liqvera_evidence_report.report import BuiltReport
from liqvera_evidence_report.schema_validation import validate

TROVE_ABIS = (
    "TroveManager.implementation.testnet.json",
    "SortedTroves.implementation.testnet.json",
    "PriceFeed.implementation.testnet.json",
)
TROVE_NAMES = {"mezo-troves/capture.json", "mezo-troves/calls.json"} | {
    "mezo-troves/" + name for name in TROVE_ABIS
}


@dataclass(frozen=True)
class TroveReportRequest:
    report_id: UUID
    borrower: str
    engine_commit: str
    created_at_ms: int
    source_mode: str = "live-public"

    def __post_init__(self):
        if (
            type(self.report_id) is not UUID
            or type(self.borrower) is not str
            or re.fullmatch(r"0x[0-9a-fA-F]{40}", self.borrower) is None
            or int(self.borrower, 16) == 0
            or type(self.engine_commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", self.engine_commit) is None
            or type(self.created_at_ms) is not int
            or not 0 <= self.created_at_ms <= 253_402_300_799_999
            or self.source_mode not in ("fixture", "live-public")
        ):
            raise EvidenceRejected("INVALID_INPUT")


def _abi(name):
    resource = files("liqvera_evidence_report").joinpath("resources", "mezo", name)
    if resource.is_file():
        return resource.read_bytes()
    return (
        Path(__file__).resolve().parents[4] / "packages/mezo-protocol/vendor" / name
    ).read_bytes()


def build_trove_report(capture: dict, request: TroveReportRequest) -> BuiltReport:
    if type(request) is not TroveReportRequest:
        raise EvidenceRejected("INVALID_INPUT")
    try:
        raw = verify_trove_capture(capture)
        if raw["borrower"].lower() != request.borrower.lower():
            raise ValueError("Borrower differs from request")
        risk = trove_risk(
            **{
                key: raw[key]
                for key in (
                    "collateral",
                    "principal",
                    "interest",
                    "price",
                    "mcr",
                    "ccr",
                    "tcr",
                    "status",
                )
            }
        )
        if int(risk["icr_atomic"]) != raw["icr"]:
            raise ValueError("Contract ICR differs")
    except (ValueError, KeyError, TypeError) as error:
        raise EvidenceRejected("INVALID_DATASET") from error
    source_ms = raw["block_timestamp"] * 1000
    if source_ms > 253_402_300_799_999:
        raise EvidenceRejected("INVALID_DATASET")
    if request.created_at_ms + 1000 < source_ms:
        raise EvidenceRejected("CLOCK_SKEW")
    status = (
        "SIMULATED"
        if request.source_mode == "fixture"
        else "HISTORICAL_SNAPSHOT"
        if request.created_at_ms - source_ms > 30_000
        else "VALID_FOR_SNAPSHOT_CALCULATION"
    )

    def musd(value):
        return _display(Fraction(value, 10**18)) if value is not None else None

    risk.update(
        {
            key: raw[key]
            for key in (
                "borrower",
                "block_number",
                "block_hash",
                "redemption_position",
                "sorted_troves_size",
                "queue_status",
            )
        }
    )
    risk["borrower"] = request.borrower
    risk.update(
        {
            "price_source": "PriceFeed.fetchPrice()",
            "debt_ahead_musd": musd(raw["debt_ahead"]),
            "redeemable_debt_ahead_musd": musd(raw["redeemable_debt_ahead"]),
            "principal_musd": musd(raw["principal"]),
            "interest_musd": musd(raw["interest"]),
            "liquidation_reserve_musd": musd(raw["gas_compensation"]),
            "explorer_links": {
                "block": "https://explorer.test.mezo.org/block/" + raw["block_number"],
                "trove_manager": "https://explorer.test.mezo.org/address/" + TROVE_MANAGER,
                "sorted_troves": "https://explorer.test.mezo.org/address/" + SORTED_TROVES,
                "price_feed": "https://explorer.test.mezo.org/address/" + PRICE_FEED,
            },
            "caveats": [
                "Mezo Testnet snapshot; read only, not financial advice.",
                "Debt and collateral already include pending rewards; principal and interest are not counted twice.",
                "Interest accrual and future oracle changes alter these snapshot quantities.",
                "The MCR crossing assumes constant debt and collateral; recovery-mode liquidation rules also apply.",
                "Redemption rank skips positions below MCR; redeemable debt ahead excludes each eligible position liquidation reserve.",
                "RPC observations and a block hash do not prove chain inclusion or oracle authenticity.",
            ],
        }
    )
    dependencies = (
        files("liqvera_evidence_report")
        .joinpath("resources", "runtime-dependencies.txt")
        .read_bytes()
    )
    algorithm = {
        "schema": "liqvera-trove-risk-algorithm/v1",
        "calculation_version": "mezo-trove-risk/v1",
        "engine_commit": request.engine_commit,
        "source_mode": request.source_mode,
        "created_at_ms": request.created_at_ms,
        "maximum_source_age_ms": 30_000,
        "queue_limit": 500,
        "display_precision": 28,
        "display_rounding": "ROUND_HALF_EVEN",
        "dependency_lock_sha256": digest(dependencies),
    }
    algorithm_bytes = canonical_json_bytes(algorithm)
    document = {
        "schema": "liqvera-trove-risk-report/v1",
        "report_id": str(request.report_id),
        "request": {"product_id": "trove_risk", "borrower": request.borrower},
        "source": {
            "source_mode": request.source_mode,
            "source_at": _timestamp(source_ms),
            "created_at": _timestamp(request.created_at_ms),
        },
        "trove_risk": risk,
        "quality": {
            "snapshot_status": status,
            "limitations": risk["caveats"],
            "reason_codes": ["SIMULATED_SOURCE"]
            if status == "SIMULATED"
            else ["STALE_SOURCE"]
            if status == "HISTORICAL_SNAPSHOT"
            else [],
            "checks": [
                {"name": name, "result": "PASS"}
                for name in (
                    "RAW_CALL_RECALCULATION",
                    "CONTRACT_ICR_AGREEMENT",
                    "QUEUE_EVIDENCE_POLICY",
                )
            ],
        },
        "reproducibility": {
            "engine_commit": request.engine_commit,
            "algorithm_sha256": digest(algorithm_bytes),
            "dependency_lock_sha256": digest(dependencies),
        },
        "boundaries": {"execution_authority": "NONE", "execution_promise": False},
    }
    validate("trove-risk-report.schema.json", document)
    report_bytes = canonical_json_bytes(document)
    extras = {
        "mezo-troves/capture.json": canonical_json_bytes(capture),
        "mezo-troves/calls.json": canonical_json_bytes(capture["calls"]),
        **{"mezo-troves/" + name: _abi(name) for name in TROVE_ABIS},
    }
    return BuiltReport(
        document, report_bytes, digest(report_bytes), {}, algorithm_bytes, dependencies, extras
    )


def rebuild_trove_members(members):
    report = strict_json(members["report.json"])
    validate("trove-risk-report.schema.json", report)
    algorithm = strict_json(members["algorithm.json"])
    request = TroveReportRequest(
        UUID(report["report_id"]),
        report["request"]["borrower"],
        algorithm["engine_commit"],
        algorithm["created_at_ms"],
        algorithm["source_mode"],
    )
    return build_trove_report(strict_json(members["mezo-troves/capture.json"]), request)
