"""Fail-closed authority and Stage A capability policy checks."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import GraphLoadError, load_graph
from tools.graph_checker.model import Lifecycle, Phase


FIXTURES = Path("tests/fixtures/graph")


def test_requirement_needs_real_forward_evidence_path_not_metadata() -> None:
    graph = load_graph(FIXTURES / "valid").with_node(
        "requirement:FAKE-001",
        kind="Requirement",
        owner="architecture",
        lifecycle=Lifecycle.DECLARED,
        requirement_id="FAKE-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    ).with_node(
        "module:metadata-only",
        kind="SourceModule",
        owner="architecture",
        requirements=("FAKE-001",),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("REQUIREMENT_FORWARD_PATH_MISSING", "requirement:FAKE-001") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_repository_has_one_real_forward_path_for_every_approved_requirement() -> None:
    graph = load_graph(Path("architecture"))
    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    requirement_nodes = {node.id for node in graph.nodes if node.kind == "Requirement"}
    requirements_with_real_outgoing_edges = {edge.from_id for edge in graph.edges} & requirement_nodes

    uncovered = {
        item.node_id
        for item in diagnostics
        if item.code in {"REQUIREMENT_FORWARD_PATH_MISSING", "REQUIREMENT_FORWARD_PATH_INCOMPLETE"}
    }
    assert len(requirement_nodes) == 116
    assert requirements_with_real_outgoing_edges == requirement_nodes
    assert uncovered == set()


def test_runtime_capability_fixture_rejects_forbidden_capabilities_and_dependencies() -> None:
    graph = load_graph(FIXTURES / "capability-violation")

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert {
        "RUNTIME_CAPABILITY_FORBIDDEN",
        "RUNTIME_CAPABILITY_INVALID",
        "RUNTIME_DEPENDENCY_FORBIDDEN",
        "NODE_CAPABILITY_COMBINATION_INVALID",
        "RUNTIME_PROFILE_UNKNOWN",
    } <= {item.code for item in diagnostics}
    assert ("RUNTIME_DEPENDENCY_FORBIDDEN", ("runtime:public-capture", "runtime:unprofiled")) in {
        (item.code, item.path) for item in diagnostics
    }


def test_single_file_fixture_mode_rejects_rogue_yaml(tmp_path: Path) -> None:
    (tmp_path / "architecture.yaml").write_text("manifest_version: 1\n", encoding="utf-8")
    (tmp_path / "rogue.yaml").write_text("manifest_version: 1\n", encoding="utf-8")

    with pytest.raises(GraphLoadError, match="repository manifest set is invalid"):
        load_graph(tmp_path)
