"""Fixture-only MVP report construction over the sealed Stage A package."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.exact import ExactDecimal
from mee_evidence_report import (
    MvpReportRejected,
    MvpReportRequest,
    build_simulated_report,
    canonical_json_bytes,
)
from mee_public_capture.package import REVIEWED_BTC, write_frozen_package
from mee_readonly_analyzer.vwap import Side

_RUN_ID = UUID("123e4567-e89b-42d3-a456-426614174001")
_REPORT_ID = UUID("123e4567-e89b-42d3-a456-426614174000")
_OBSERVED_AT_MS = 1_700_000_000_000
_BOOK = (
    b'{"coin":"BTC","time":1700000000000,"levels":['
    b'[{"px":"100","sz":"0.1"},{"px":"99","sz":"0.1"}],'
    b'[{"px":"101","sz":"0.1"},{"px":"102","sz":"0.1"}]]}'
)


def _package(tmp_path: Path) -> Path:
    root = tmp_path / "sealed-input"
    return write_frozen_package(
        root,
        run_id=_RUN_ID,
        started_at_ms=_OBSERVED_AT_MS,
        terminated_at_ms=_OBSERVED_AT_MS + 1,
        venues=("hyperliquid",),
        envelopes=(("hyperliquid", _BOOK),),
        mappings=[REVIEWED_BTC],
    )


def _request(side: Side, quantity: str = "0.15") -> MvpReportRequest:
    return MvpReportRequest(
        report_id=_REPORT_ID,
        side=side,
        quantity_base=ExactDecimal.parse(quantity),
        engine_commit="c" * 40,
    )


def test_builds_exact_buy_report_from_fixture_package(tmp_path: Path) -> None:
    # Catches walking bids for BUY, losing the partial second level, or using
    # rendered decimals instead of exact rationals for the impact calculation.
    built = build_simulated_report(_package(tmp_path), _request(Side.BUY))

    assert built.document["calculation"] == {
        "requested_quantity": "0.15",
        "filled_quantity": "0.15",
        "notional_quote": {"numerator": "76", "denominator": "5"},
        "vwap": {"numerator": "304", "denominator": "3"},
        "worst_price": {"numerator": "102", "denominator": "1"},
        "price_impact_bps": {"numerator": "10000", "denominator": "303"},
        "consumed_levels": 2,
        "display": {
            "notional_quote": "15.2",
            "vwap": "101.3333333333333333333333333",
            "worst_price": "102",
            "price_impact_bps": "33.00330033003300330033003300",
        },
        "display_precision": 28,
        "display_rounding": "ROUND_HALF_EVEN",
    }
    assert built.document["request"] == {"side": "BUY", "quantity_base": "0.15"}


def test_builds_exact_sell_report_from_fixture_package(tmp_path: Path) -> None:
    # Catches walking asks for SELL and the common reversed SELL impact formula.
    calculation = build_simulated_report(
        _package(tmp_path), _request(Side.SELL)
    ).document["calculation"]

    assert calculation["notional_quote"] == {"numerator": "299", "denominator": "20"}
    assert calculation["vwap"] == {"numerator": "299", "denominator": "3"}
    assert calculation["worst_price"] == {"numerator": "99", "denominator": "1"}
    assert calculation["price_impact_bps"] == {
        "numerator": "100",
        "denominator": "3",
    }


def test_insufficient_depth_raises_typed_rejection_without_report(tmp_path: Path) -> None:
    # Catches partial-report publication after sweep_depth rejects the request.
    with pytest.raises(MvpReportRejected) as caught:
        build_simulated_report(_package(tmp_path), _request(Side.BUY, "0.21"))

    assert caught.value.code == "DEPTH_INSUFFICIENT"


def test_report_bytes_are_deterministic_and_digest_is_external(tmp_path: Path) -> None:
    # Catches ambient-clock/UUID use, noncanonical JSON, and report self-hashing.
    package = _package(tmp_path)
    first = build_simulated_report(package, _request(Side.BUY))
    second = build_simulated_report(package, _request(Side.BUY))

    assert first == second
    assert first.report_bytes == canonical_json_bytes(first.document)
    assert first.report_bytes.endswith(b"\n")
    assert not first.report_bytes.endswith(b"\n\n")
    assert "report_sha256" not in first.document
    assert first.report_sha256 not in first.report_bytes.decode("utf-8")


def test_fixture_report_is_simulated_read_only_and_discloses_mvp_limits(
    tmp_path: Path,
) -> None:
    # Catches fixture elevation to chargeable/live status or payment authority.
    document = build_simulated_report(_package(tmp_path), _request(Side.BUY)).document

    assert document["schema"] == "mee-evidence-report/v1"
    assert document["source"]["source_mode"] == "fixture"
    assert document["source"]["source_at"] == "2023-11-14T22:13:20Z"
    assert document["source"]["created_at"] == "2023-11-14T22:13:20Z"
    assert document["quality"]["snapshot_status"] == "SIMULATED"
    assert document["quality"]["reason_codes"] == ["SIMULATED_SOURCE"]
    assert document["boundaries"]["execution_authority"] == "NONE"
    assert document["quality"]["stage_a"]["decision"] == "INSUFFICIENT_EVIDENCE"
    assert any(
        "fixture timestamp" in limitation.lower()
        for limitation in document["quality"]["limitations"]
    )
    assert any(
        "unverified mvp" in limitation.lower()
        for limitation in document["quality"]["limitations"]
    )
    forbidden = {"payment", "price_musd", "pay_to", "terms", "receipt", "tx_hash"}
    assert forbidden.isdisjoint(_all_keys(document))


def test_canonical_json_rejects_nested_float() -> None:
    # Catches binary floating point leaking through a nested report field.
    with pytest.raises(TypeError, match="float"):
        canonical_json_bytes({"safe": [1, {"unsafe": 0.1}]})


def _all_keys(value: object) -> set[str]:
    if type(value) is dict:
        document = value
        return set(document) | {
            key
            for child in document.values()
            for key in _all_keys(child)
        }
    if type(value) is list:
        return {key for child in value for key in _all_keys(child)}
    return set()
