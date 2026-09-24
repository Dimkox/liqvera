"""Closed Stage A decision contract: four values, no GO, one reason class."""

from __future__ import annotations

import json
from uuid import UUID

import pytest
from mee_contracts.decision import StageADecision, StageADecisionCode, StageAReasonCode

RUN = UUID("00000000-0000-0000-0000-000000000001")


def test_stage_a_decision_code_is_the_closed_four() -> None:
    assert tuple(StageADecisionCode) == (
        StageADecisionCode.INVALID_DATASET,
        StageADecisionCode.INSUFFICIENT_EVIDENCE,
        StageADecisionCode.STOP,
        StageADecisionCode.EXTEND_LONGER_SHADOW,
    )


@pytest.mark.parametrize("forbidden", ("GO", "NO_GO", "KILL", "plausible", "inconclusive"))
def test_forbidden_decision_codes_are_not_constructible(forbidden: str) -> None:
    with pytest.raises(ValueError):
        StageADecisionCode(forbidden)


def test_empty_reasons_are_rejected() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        StageADecision(
            decision=StageADecisionCode.INSUFFICIENT_EVIDENCE,
            reasons=(),
            capture_run_id=RUN,
        )


def test_mixed_reason_classes_are_rejected() -> None:
    with pytest.raises(ValueError, match="one class"):
        StageADecision(
            decision=StageADecisionCode.INVALID_DATASET,
            reasons=(
                StageAReasonCode.INVALID_RECORD,
                StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,
            ),
            capture_run_id=RUN,
        )


def test_stop_and_extend_decisions_construct_with_matching_class() -> None:
    stop = StageADecision(
        decision=StageADecisionCode.STOP,
        reasons=(StageAReasonCode.STOP_TOTAL_NET_NON_POSITIVE,),
        capture_run_id=RUN,
    )
    assert stop.decision is StageADecisionCode.STOP
    assert stop.reasons == (StageAReasonCode.STOP_TOTAL_NET_NON_POSITIVE,)
    extend = StageADecision(
        decision=StageADecisionCode.EXTEND_LONGER_SHADOW,
        reasons=(StageAReasonCode.EXTEND_ALL_V2_GATES_PASS,),
        capture_run_id=RUN,
    )
    assert extend.decision is StageADecisionCode.EXTEND_LONGER_SHADOW
    assert extend.reasons == (StageAReasonCode.EXTEND_ALL_V2_GATES_PASS,)
    with pytest.raises(ValueError, match="one class"):
        StageADecision(
            decision=StageADecisionCode.STOP,
            reasons=(StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,),
            capture_run_id=RUN,
        )
    with pytest.raises(ValueError, match="one class"):
        StageADecision(
            decision=StageADecisionCode.EXTEND_LONGER_SHADOW,
            reasons=(StageAReasonCode.STOP_TOTAL_NET_NON_POSITIVE,),
            capture_run_id=RUN,
        )
    with pytest.raises(ValueError):
        StageADecisionCode("GO")


def test_canonical_json_round_trip_uses_sorted_keys() -> None:
    decision = StageADecision(
        decision=StageADecisionCode.INSUFFICIENT_EVIDENCE,
        reasons=(
            StageAReasonCode.INSUFFICIENT_INDEPENDENT_EPISODES,
            StageAReasonCode.INSUFFICIENT_ACQUISITION_WINDOW,
        ),
        capture_run_id=RUN,
    )
    payload = decision.to_canonical_json()
    assert payload.endswith(b"\n")
    document = json.loads(payload)
    assert tuple(document) == (
        "capture_run_id",
        "decision",
        "package_schema",
        "reasons",
        "schema",
    )
    assert document["schema"] == "mee-stage-a-decision/v1"
    assert document["package_schema"] == "mee-readonly-frozen-package/v1"
    assert document["decision"] == "INSUFFICIENT_EVIDENCE"
    assert document["capture_run_id"] == str(RUN)
    assert document["reasons"] == [
        "INSUFFICIENT_ACQUISITION_WINDOW",
        "INSUFFICIENT_INDEPENDENT_EPISODES",
    ]
    assert payload == (
        json.dumps(document, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")
