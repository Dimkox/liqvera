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


def test_retired_go_reference_is_documented_and_recoverable_from_git() -> None:
    from pathlib import Path

    from tools.graph_checker.loader import load_graph
    from tools.graph_checker.model import Classification, Lifecycle, NodeKind

    graph = load_graph(Path("architecture"))
    reference = graph.node("source:retired-go-stage-zero-provenance")
    assert reference.kind is NodeKind.SOURCE_MODULE
    assert reference.lifecycle is Lifecycle.IMPLEMENTED
    assert reference.active is True
    assert reference.classifications == (Classification.TEST_ONLY_EXECUTABLE_SPEC,)

    manifest = Path("architecture/conformance/manifest.yaml").read_text(encoding="utf-8")
    assert manifest.count("git:8734907d489168a8a6567b93bc85920001fefd85:") == 5
    assert manifest.count("retirement_state: RETIRED") == 5
