"""STOP/EXTEND evaluate sealed economics only after coverage is sufficient."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

from mee_contracts.decision import StageADecisionCode, StageAReasonCode
from mee_public_capture.config import load_public_configuration
from mee_public_capture.runtime import run_public_capture
from mee_readonly_analyzer.frozen_package.reader import FrozenPackageEvidenceReader
from mee_readonly_analyzer.identity import bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import reconstruct_books
from mee_readonly_analyzer.verdict import evaluate_frozen_package

from tests.readonly_analyzer.package_factory import (
    passing_economics,
    rebind_member,
    write_sufficient_package,
    write_valid_package,
)

RUN = UUID("00000000-0000-0000-0000-000000000001")

_ALL_STOP = (
    StageAReasonCode.STOP_TOTAL_NET_NON_POSITIVE,
    StageAReasonCode.STOP_MEDIAN_NET_NON_POSITIVE,
    StageAReasonCode.STOP_USD_1000_NET_NON_POSITIVE,
    StageAReasonCode.STOP_USD_5000_NET_NEGATIVE,
    StageAReasonCode.STOP_DELAY_300MS_NOT_SURVIVED,
    StageAReasonCode.STOP_DELAY_500MS_NOT_SURVIVED,
    StageAReasonCode.STOP_FEE_CASE_NOT_SURVIVED,
    StageAReasonCode.STOP_CONCENTRATION_NOT_BELOW_25_PERCENT,
)


def test_stub_package_is_insufficient_with_four_coverage_reasons(tmp_path: Path) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert decision.reasons == (
        StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,
        StageAReasonCode.INSUFFICIENT_COMPLETE_UTC_DAYS,
        StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES,
        StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES,
    )


def test_capture_written_fixture_is_insufficient_not_invalid(tmp_path: Path) -> None:
    root = tmp_path / "pkg"
    root.mkdir()
    config = load_public_configuration(
        {
            "MEE_CAPTURE_OUT": str(root),
            "MEE_CAPTURE_SOURCE": "fixture",
            "MEE_PUBLIC_VENUES": "hyperliquid,lighter",
        }
    )
    assert run_public_capture(config) == 0
    reader = FrozenPackageEvidenceReader(root)
    envelopes = tuple(reader.iter_raw_envelopes(reader.capture_run_id))
    mappings = reader.read_mapping_snapshot(reader.capture_run_id).mappings
    books = reconstruct_books(envelopes, mappings)
    assert len(books) == 2
    assert books[0].snapshot.venue == "HYPERLIQUID"
    assert books[1].snapshot.venue == "LIGHTER"
    assert books[0].mapping_id is None
    bound = bind_reconstructed_books(books, mappings)
    assert bound[0].mapping_id == "btc-usd-linear-perpetual"
    assert bound[1].mapping_id == "lighter-btc-usd-linear-perpetual"
    decision = evaluate_frozen_package(root)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert decision.reasons == (
        StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,
        StageAReasonCode.INSUFFICIENT_COMPLETE_UTC_DAYS,
        StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES,
        StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES,
    )
    assert all(item.value.startswith("INSUFFICIENT_") for item in decision.reasons)
    assert b"GO" not in decision.to_canonical_json()
    assert decision.decision is not StageADecisionCode.STOP
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW


def test_seven_day_minutes_without_economics_are_insufficient_episodes(
    tmp_path: Path,
) -> None:
    package = write_sufficient_package(tmp_path / "pkg", RUN, economics=None)
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES in decision.reasons
    assert all(item.value.startswith("INSUFFICIENT_") for item in decision.reasons)
    assert decision.decision is not StageADecisionCode.STOP
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW


def test_short_window_with_passing_economics_stays_insufficient(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        started_at_ms=0,
        terminated_at_ms=1,
        quality_minute_count=1,
        economics=passing_economics(),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW in decision.reasons
    assert StageAReasonCode.INSUFFICIENT_COMPLETE_UTC_DAYS in decision.reasons
    assert StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES in decision.reasons
    assert all(item.value.startswith("INSUFFICIENT_") for item in decision.reasons)
    assert StageAReasonCode.STOP_USD_1000_NET_NON_POSITIVE not in decision.reasons


def test_malformed_declared_economics_is_invalid_record(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        economics=passing_economics(total_net=1.25),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INVALID_DATASET
    assert decision.reasons == (StageAReasonCode.INVALID_RECORD,)
    assert decision.capture_run_id == RUN


def test_malformed_economics_extra_key_is_invalid_record(tmp_path: Path) -> None:
    document = passing_economics()
    document["episodes"] = []
    package = write_sufficient_package(tmp_path / "pkg", RUN, economics=document)
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INVALID_DATASET
    assert decision.reasons == (StageAReasonCode.INVALID_RECORD,)


def test_sufficient_usd_1000_net_zero_is_stop(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        economics=passing_economics(usd_1000_net="0"),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.STOP
    assert decision.reasons == (StageAReasonCode.STOP_USD_1000_NET_NON_POSITIVE,)


def test_sufficient_concentration_quarter_is_stop(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        economics=passing_economics(largest_episode_concentration="0.25"),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.STOP
    assert decision.reasons == (StageAReasonCode.STOP_CONCENTRATION_NOT_BELOW_25_PERCENT,)


def test_sufficient_failed_predicates_emit_every_stop_reason(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        economics=passing_economics(
            total_net="0",
            median_net="0",
            usd_1000_net="0",
            usd_5000_net="-1",
            survived_delay_300ms=False,
            survived_delay_500ms=False,
            survived_both_fee_cases=False,
            largest_episode_concentration="0.25",
        ),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.STOP
    assert decision.reasons == _ALL_STOP


def test_sufficient_passing_economics_is_extend(tmp_path: Path) -> None:
    package = write_sufficient_package(tmp_path / "pkg", RUN)
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.EXTEND_LONGER_SHADOW
    assert decision.reasons == (StageAReasonCode.EXTEND_ALL_V2_GATES_PASS,)
    assert b"GO" not in decision.to_canonical_json()


def test_sufficient_empty_mappings_is_invalid_record(tmp_path: Path) -> None:
    package = write_sufficient_package(tmp_path / "pkg", RUN, mappings=[])
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INVALID_DATASET
    assert decision.reasons == (StageAReasonCode.INVALID_RECORD,)
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW
    assert all(item.value.startswith("INVALID_") for item in decision.reasons)


def test_sufficient_garbage_hyperliquid_envelope_is_invalid_record(
    tmp_path: Path,
) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        envelope_payload=b"hi",
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INVALID_DATASET
    assert decision.reasons == (StageAReasonCode.INVALID_RECORD,)
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW
    assert all(item.value.startswith("INVALID_") for item in decision.reasons)


def test_sufficient_lighter_garbage_envelope_is_invalid_record(tmp_path: Path) -> None:
    payload = b"garbage"
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        envelope_payload=payload,
    )
    envelope = (
        json.dumps(
            {
                "envelope_index": 0,
                "observed_at_ms": 1,
                "venue": "lighter",
                "payload_hex": payload.hex(),
            }
        )
        + "\n"
    ).encode("utf-8")
    rebind_member(package, "raw_envelopes/records.ndjson", envelope)
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INVALID_DATASET
    assert decision.reasons == (StageAReasonCode.INVALID_RECORD,)
    assert decision.decision is not StageADecisionCode.EXTEND_LONGER_SHADOW
    assert all(item.value.startswith("INVALID_") for item in decision.reasons)


def test_nineteen_episodes_ignore_negative_nets(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        economics=passing_economics(independent_episode_count=19, total_net="-1"),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert decision.reasons == (StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES,)


def test_healthy_9575_is_insufficient_not_stop(tmp_path: Path) -> None:
    package = write_sufficient_package(
        tmp_path / "pkg",
        RUN,
        quality_minute_count=9575,
        economics=passing_economics(total_net="-1"),
    )
    decision = evaluate_frozen_package(package)
    assert decision.decision is StageADecisionCode.INSUFFICIENT_EVIDENCE
    assert StageAReasonCode.INSUFFICIENT_STRICT_HEALTHY_MINUTES in decision.reasons
    assert all(item.value.startswith("INSUFFICIENT_") for item in decision.reasons)
