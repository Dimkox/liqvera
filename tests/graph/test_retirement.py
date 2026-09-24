"""Fail-closed retirement of superseded owners."""

from __future__ import annotations

from tools.graph_checker.model import Lifecycle
from tools.graph_checker.retirement import (
    ReceiptSet,
    apply_retirement,
    eligible_graph,
    graph_with_go_reference,
    retirement_decision,
)


def test_retirement_fails_without_every_required_receipt() -> None:
    decision = retirement_decision(graph_with_go_reference(), "go:fixed", ReceiptSet())
    assert decision.allowed is False
    assert decision.reason_codes == ("CONFORMANCE_RECEIPT_MISSING", "REVIEW_RESULT_MISSING")


def test_go_reference_stays_blocked_without_review_even_with_conformance() -> None:
    decision = retirement_decision(
        graph_with_go_reference(),
        "go:fixed",
        ReceiptSet(conformance={"source_sha": "abc"}, review_result=None),
    )
    assert decision.allowed is False
    assert decision.reason_codes == ("REVIEW_RESULT_MISSING",)


def test_superseded_a2_packaging_owner_is_retired() -> None:
    from pathlib import Path

    from tools.graph_checker.loader import load_graph

    graph = load_graph(Path("architecture"))
    node = graph.node("artifact:a2-production-image")
    assert node.lifecycle is Lifecycle.RETIRED
    assert node.active is False
    assert graph.has_edge(
        "artifact:public-capture-image", "supersedes", "artifact:a2-production-image"
    )
    assert graph.has_edge(
        "artifact:a2-production-image", "rolled_back_by", "rollback:graph-authority"
    )


def test_retirement_preserves_provenance_and_rollback() -> None:
    receipts = ReceiptSet(artifact={"path": "deploy/images"}, review_result="APPROVED")
    retired = apply_retirement(
        eligible_graph(), "legacy:a2-root", rollback_id="git:a0cdbbf", receipts=receipts
    )
    node = retired.node("legacy:a2-root")
    assert node.lifecycle == Lifecycle.RETIRED
    assert node.active is False
    assert retired.has_edge("legacy:a2-root", "derived_from", "git:a0cdbbf")
    assert retired.has_edge("legacy:a2-root", "rolled_back_by", "git:a0cdbbf")
