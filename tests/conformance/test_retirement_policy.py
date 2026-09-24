"""Retirement stays blocked without review and never implies deployability."""

from __future__ import annotations

from tools.conformance.policy import (
    BLOCKED,
    ELIGIBLE,
    conformance_row,
    receipt_for_head,
    retirement_state,
)


def test_same_named_python_test_never_makes_go_reference_eligible() -> None:
    row = conformance_row(review_result=None, claw_receipt=None)
    assert row.python_test.endswith("test_exact_arithmetic.py")
    assert retirement_state(row) == BLOCKED


def test_python_pass_without_review_stays_blocked() -> None:
    receipt = receipt_for_head()
    row = conformance_row(
        review_result=None,
        claw_receipt=receipt,
        python_passed=True,
        python_test="tests/conformance/test_exact_arithmetic.py",
    )
    assert retirement_state(row) == BLOCKED


def test_complete_exact_sha_evidence_is_eligible_not_deployable() -> None:
    row = conformance_row(review_result="APPROVED", claw_receipt=receipt_for_head())
    assert retirement_state(row) == ELIGIBLE
    assert row.stage_a_packaging_allowed is False


def test_go_executed_receipt_is_rejected() -> None:
    receipt = dict(receipt_for_head())
    receipt["go_executed"] = "true"
    row = conformance_row(review_result="APPROVED", claw_receipt=receipt)
    assert retirement_state(row) == BLOCKED


def test_live_go_reference_owner_is_not_eligible_to_retire() -> None:
    from pathlib import Path

    from tools.graph_checker.loader import load_graph
    from tools.graph_checker.retirement import ReceiptSet, retirement_decision

    graph = load_graph(Path("architecture"))
    decision = retirement_decision(graph, "runtime:go-reference", ReceiptSet())
    assert decision.allowed is False
    assert "CONFORMANCE_RECEIPT_MISSING" in decision.reason_codes
    assert "REVIEW_RESULT_MISSING" in decision.reason_codes
