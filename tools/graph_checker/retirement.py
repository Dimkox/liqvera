"""Fail-closed retirement decisions for superseded graph owners."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable

from tools.graph_checker.model import (
    ArchitectureGraph,
    Classification,
    GraphEdge,
    GraphNode,
    Lifecycle,
)


@dataclass(frozen=True, slots=True)
class ReceiptSet:
    conformance: object | None = None
    review_result: str | None = None
    artifact: object | None = None


@dataclass(frozen=True, slots=True)
class RetirementDecision:
    allowed: bool
    reason_codes: tuple[str, ...]


def required_retirement_evidence(
    graph: ArchitectureGraph, node_id: str
) -> tuple[tuple[str, Callable[[ReceiptSet], bool]], ...]:
    node = graph.node(node_id)
    if Classification.TEST_ONLY_EXECUTABLE_SPEC in node.classifications:
        return (
            ("CONFORMANCE_RECEIPT_MISSING", lambda receipts: receipts.conformance is not None),
            ("REVIEW_RESULT_MISSING", lambda receipts: receipts.review_result == "APPROVED"),
        )
    return (
        ("ARTIFACT_RECEIPT_MISSING", lambda receipts: receipts.artifact is not None),
        ("REVIEW_RESULT_MISSING", lambda receipts: receipts.review_result == "APPROVED"),
    )


def runtime_reachable(graph: ArchitectureGraph, node_id: str) -> bool:
    return any(
        dependency.from_id == node_id or dependency.to_id == node_id
        for dependency in graph.runtime_dependencies
    )


def retirement_decision(
    graph: ArchitectureGraph, node_id: str, receipts: ReceiptSet
) -> RetirementDecision:
    missing = tuple(
        code
        for code, predicate in required_retirement_evidence(graph, node_id)
        if not predicate(receipts)
    )
    if missing:
        return RetirementDecision(False, missing)
    if runtime_reachable(graph, node_id):
        return RetirementDecision(False, ("OWNER_STILL_REACHABLE",))
    return RetirementDecision(True, ())


def apply_retirement(
    graph: ArchitectureGraph,
    node_id: str,
    *,
    rollback_id: str,
    receipts: ReceiptSet,
) -> ArchitectureGraph:
    decision = retirement_decision(graph, node_id, receipts)
    if not decision.allowed:
        raise ValueError(decision.reason_codes)
    node = graph.node(node_id)
    retired = replace(node, lifecycle=Lifecycle.RETIRED, active=False)
    nodes = tuple(item if item.id != node_id else retired for item in graph.nodes)
    edges = graph.edges + (
        GraphEdge(node_id, rollback_id, "derived_from"),
        GraphEdge(node_id, rollback_id, "rolled_back_by"),
    )
    return replace(graph, nodes=nodes, edges=edges)


def graph_with_go_reference() -> ArchitectureGraph:
    return ArchitectureGraph(
        (
            GraphNode(
                "go:fixed",
                "SourceModule",
                "runtime",
                Lifecycle.IMPLEMENTED,
                classifications=(Classification.TEST_ONLY_EXECUTABLE_SPEC,),
            ),
        )
    )


def eligible_graph() -> ArchitectureGraph:
    return ArchitectureGraph(
        (
            GraphNode("legacy:a2-root", "Artifact", "release", Lifecycle.DECLARED, active=False),
            GraphNode("git:a0cdbbf", "Rollback", "release", Lifecycle.IMPLEMENTED),
        )
    )
