from dataclasses import replace
from pathlib import Path

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import load_graph
from tools.graph_checker.model import GraphEdge, Lifecycle, Phase, ReceiptRequirement


FIXTURES = Path("tests/fixtures/graph")


def test_runtime_cycle_reports_stable_path() -> None:
    graph = load_graph(FIXTURES / "cycle")

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert [(item.code, item.path) for item in diagnostics] == [
        ("RUNTIME_CYCLE", ("module:a", "module:b", "module:a")),
    ]

def test_active_source_without_reverse_requirement_path_is_orphan() -> None:
    graph = load_graph(FIXTURES / "valid")
    orphan = graph.with_node("module:orphan", kind="SourceModule", owner="capture")

    diagnostics = check_graph(orphan, Phase.PRECOMMIT)

    assert [
        (item.code, item.node_id, item.path, item.requirement_ids) for item in diagnostics
    ] == [
        ("IMPLEMENTATION_ORPHAN", "module:orphan", ("module:orphan",), ()),
    ]


def test_source_naming_unknown_requirement_without_reverse_path_is_orphan() -> None:
    graph = load_graph(FIXTURES / "valid")
    orphan = graph.with_node(
        "module:unverified-requirement",
        kind="SourceModule",
        owner="capture",
        requirements=("GRAPH-DOES-NOT-EXIST",),
    )

    diagnostics = check_graph(orphan, Phase.PRECOMMIT)

    assert [
        (item.code, item.node_id, item.path, item.requirement_ids) for item in diagnostics
    ] == [
        ("IMPLEMENTATION_ORPHAN", "module:unverified-requirement", ("module:unverified-requirement",), ()),
        (
            "PROOF_NODE_PROJECTION_MISMATCH",
            "module:unverified-requirement",
            ("module:unverified-requirement",),
            ("GRAPH-DOES-NOT-EXIST",),
        ),
        (
            "REQUIREMENT_METADATA_MISMATCH",
            "module:unverified-requirement",
            ("module:unverified-requirement",),
            ("GRAPH-DOES-NOT-EXIST",),
        ),
    ]


def test_diagnostics_are_sorted_deterministically() -> None:
    graph = load_graph(FIXTURES / "valid")
    graph = graph.with_node("module:z", kind="SourceModule", owner="capture")
    graph = graph.with_node("module:a", kind="SourceModule", owner="capture")

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert [(item.code, item.path) for item in diagnostics] == [
        ("IMPLEMENTATION_ORPHAN", ("module:a",)),
        ("IMPLEMENTATION_ORPHAN", ("module:z",)),
    ]


def test_active_node_requires_one_nonempty_owner() -> None:
    graph = load_graph(FIXTURES / "valid")
    ownerless = graph.with_node("module:ownerless", kind="SourceModule", owner="")

    diagnostics = check_graph(ownerless, Phase.PRECOMMIT)

    assert diagnostics[0].code == "MISSING_CANONICAL_OWNER"


def test_retired_node_cannot_remain_active() -> None:
    graph = load_graph(FIXTURES / "valid")
    invalid = graph.with_node(
        "module:retired",
        kind="SourceModule",
        owner="architecture",
        lifecycle=Lifecycle.RETIRED,
        active=True,
        requirements=("GRAPH-008",),
    )

    diagnostics = check_graph(invalid, Phase.PRECOMMIT)

    assert diagnostics[0].code == "INVALID_LIFECYCLE"


def test_phase_lifecycle_requirement_is_enforced_only_when_due() -> None:
    graph = load_graph(FIXTURES / "valid")
    graph = replace(graph, receipts=(), policy_times_trusted=True)
    graph = graph.with_node(
        "module:graph-checker",
        kind="SourceModule",
        owner="architecture",
        lifecycle=Lifecycle.DECLARED,
        requirements=("GRAPH-006", "GRAPH-008", "GRAPH-011"),
        required_from=Phase.MERGE,
        required_lifecycle=Lifecycle.REALIZED,
        shared_proof=True,
    )

    assert check_graph(graph, Phase.PRECOMMIT) == ()
    diagnostics = check_graph(graph, Phase.MERGE)

    assert [(item.code, item.node_id, item.path) for item in diagnostics] == [
        ("LIFECYCLE_PHASE_REQUIREMENT", "module:graph-checker", ("module:graph-checker",)),
        ("RECEIPT_REQUIRED_MISSING", "module:graph-checker", ("module:graph-checker",)),
    ]


def test_declared_conflict_remains_a_reported_blocker() -> None:
    graph = load_graph(FIXTURES / "valid")
    conflicted = graph.with_node(
        "conflict:baseline",
        kind="Conflict",
        owner="architecture",
        requirements=("GRAPH-011",),
    )
    conflicted = replace(
        conflicted,
        edges=(*conflicted.edges, GraphEdge("requirement:GRAPH-011", "conflict:baseline", "conflicts_with")),
    )

    diagnostics = check_graph(conflicted, Phase.PRECOMMIT)

    assert [(item.code, item.node_id) for item in diagnostics] == [
        ("DECLARED_CONFLICT", "conflict:baseline"),
    ]


def test_prospective_evidence_declaration_is_not_a_realized_merge_receipt() -> None:
    graph = replace(load_graph(FIXTURES / "valid"), policy_times_trusted=True)

    assert check_graph(graph, Phase.PRECOMMIT) == ()
    diagnostics = check_graph(graph, Phase.MERGE)

    assert [(item.code, item.node_id) for item in diagnostics] == [
        ("RECEIPT_NOT_REALIZED", "gate:graph-check"),
    ]


def test_receipt_targeting_unknown_node_is_a_schema_error() -> None:
    graph = load_graph(FIXTURES / "valid")
    graph = replace(
        graph,
        policy_times_trusted=True,
        receipts=(ReceiptRequirement("gate:unknown", Phase.MERGE, "ClawValidationReceipt", "realized"),),
    )

    diagnostics = check_graph(graph, Phase.MERGE)

    assert {
        ("SCHEMA_DANGLING_RECEIPT", "gate:unknown", ("gate:unknown",)),
        ("RECEIPT_TRUST_ANCHOR_UNAVAILABLE", "gate:unknown", ("gate:unknown",)),
    } == {(item.code, item.node_id, item.path) for item in diagnostics}
