"""Regression tests for the M0 final-review graph-policy fixes."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import subprocess
import sys

import yaml

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import GraphLoadError, load_graph
from tools.graph_checker.model import (
    ArchitectureGraph,
    Classification,
    GraphEdge,
    GraphNode,
    Lifecycle,
    Phase,
)


FIXTURES = Path("tests/fixtures/graph")
ROOT = Path(__file__).resolve().parents[2]


def _non_product_graph(
    *, requirement_active: bool = True, approval: str | None = "owner-approved"
) -> ArchitectureGraph:
    proof_for = "GRAPH-001"

    def edge(from_id: str, to_id: str, kind: str) -> GraphEdge:
        return GraphEdge(from_id, to_id, kind, proof_for=proof_for)

    requirement = GraphNode(
        "requirement:GRAPH-001",
        "Requirement",
        "architecture",
        Lifecycle.DECLARED,
        active=requirement_active,
        requirement_id="GRAPH-001",
        requirement_class="NON_PRODUCT",
        approval=approval,
    )
    def node(node_id: str, kind: str, owner: str = "architecture") -> GraphNode:
        return GraphNode(node_id, kind, owner, Lifecycle.DECLARED, requirements=("GRAPH-001",))
    approval_node = node("approval:graph-policy", "Approval")
    contract = node("contract:graph-policy", "Contract")
    source = node("module:graph-policy", "SourceModule")
    dataflow = node("dataflow:graph-policy", "DataFlow")
    test = node("test:graph-policy", "TestOrEval")
    gate = node("gate:graph-policy", "ClawGate")
    artifact = node("artifact:graph-policy", "Artifact")
    evidence = node("evidence:graph-policy", "Evidence")
    rollback = node("rollback:graph-policy", "Rollback")
    return ArchitectureGraph(
        nodes=(requirement, approval_node, contract, source, dataflow, test, gate, artifact, evidence, rollback),
        edges=(
            edge(requirement.id, approval_node.id, "approved_by"),
            edge(requirement.id, contract.id, "specified_by"),
            edge(contract.id, source.id, "implements"),
            edge(source.id, dataflow.id, "produces"),
            edge(dataflow.id, test.id, "validated_by"),
            edge(test.id, gate.id, "gated_by"),
            edge(gate.id, artifact.id, "packaged_in"),
            edge(artifact.id, evidence.id, "evidenced_by"),
            edge(evidence.id, rollback.id, "rolled_back_by"),
        ),
    )


def _product_graph(
    *,
    include_criterion: bool = True,
    criterion_kind: str = "AcceptanceCriterion",
) -> ArchitectureGraph:
    proof_for = "PROD-001"

    def edge(from_id: str, to_id: str, kind: str) -> GraphEdge:
        return GraphEdge(from_id, to_id, kind, proof_for=proof_for)

    def node(node_id: str, kind: str, owner: str = "product") -> GraphNode:
        return GraphNode(node_id, kind, owner, Lifecycle.DECLARED, requirements=("PROD-001",))
    actor = node("actor:operator", "Actor")
    outcome = node("outcome:shadow-decision", "Outcome")
    requirement = GraphNode(
        "requirement:PROD-001",
        "Requirement",
        "product",
        Lifecycle.DECLARED,
        requirement_id="PROD-001",
        requirement_class="PRODUCT",
        approval="owner-approved",
    )
    approval_node = node("approval:shadow-decision", "Approval")
    criterion = node("acceptance:shadow-decision", criterion_kind)
    metric = node("metric:shadow-decision", "Metric")
    contract = node("contract:shadow-decision", "Contract")
    source = node("module:shadow-decision", "SourceModule")
    dataflow = node("dataflow:shadow-decision", "DataFlow")
    test = node("test:shadow-decision", "TestOrEval")
    gate = node("gate:shadow-decision", "ClawGate")
    artifact = node("artifact:shadow-decision", "Artifact")
    evidence = node("evidence:shadow-decision", "Evidence")
    rollback = node("rollback:shadow-decision", "Rollback")
    criterion_edges = (
        edge(
            requirement.id,
            criterion.id,
            "specified_by",
        ),
        edge(criterion.id, metric.id, "measured_by"),
    ) if include_criterion else (
        edge(requirement.id, metric.id, "specified_by"),
    )
    return ArchitectureGraph(
        nodes=(
            actor,
            outcome,
            requirement,
            approval_node,
            criterion,
            metric,
            contract,
            source,
            dataflow,
            test,
            gate,
            artifact,
            evidence,
            rollback,
        ),
        edges=(
            edge(actor.id, outcome.id, "intends"),
            edge(outcome.id, requirement.id, "serves"),
            edge(requirement.id, approval_node.id, "approved_by"),
            *criterion_edges,
            edge(metric.id, contract.id, "specified_by"),
            edge(contract.id, source.id, "implements"),
            edge(source.id, dataflow.id, "produces"),
            edge(dataflow.id, test.id, "validated_by"),
            edge(test.id, gate.id, "gated_by"),
            edge(gate.id, artifact.id, "packaged_in"),
            edge(artifact.id, evidence.id, "evidenced_by"),
            edge(evidence.id, rollback.id, "rolled_back_by"),
        ),
    )


def test_unknown_edge_kind_is_a_blocking_diagnostic() -> None:
    graph = load_graph(FIXTURES / "valid")
    graph = replace(
        graph,
        edges=(*graph.edges, GraphEdge("contract:graph-manifest-v1", "module:graph-checker", "unknown")),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("EDGE_KIND_UNKNOWN", ("contract:graph-manifest-v1", "module:graph-checker")) in {
        (item.code, item.path) for item in diagnostics
    }


def test_known_edge_kind_with_wrong_node_kinds_is_a_blocking_diagnostic() -> None:
    graph = load_graph(FIXTURES / "valid")
    graph = replace(
        graph,
        edges=(*graph.edges, GraphEdge("contract:graph-manifest-v1", "module:graph-checker", "gated_by")),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("EDGE_KIND_PAIR_INVALID", ("contract:graph-manifest-v1", "module:graph-checker")) in {
        (item.code, item.path) for item in diagnostics
    }


def test_inactive_requirement_cannot_cover_an_active_implementation_path() -> None:
    diagnostics = check_graph(_non_product_graph(requirement_active=False), Phase.PRECOMMIT)

    assert ("IMPLEMENTATION_ORPHAN", "contract:graph-policy") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_unapproved_requirement_cannot_cover_an_active_implementation_path() -> None:
    diagnostics = check_graph(_non_product_graph(approval="draft"), Phase.PRECOMMIT)

    codes_by_node = {(item.code, item.node_id) for item in diagnostics}
    assert ("REQUIREMENT_OWNER_APPROVAL_MISSING", "requirement:GRAPH-001") in codes_by_node
    assert ("IMPLEMENTATION_ORPHAN", "contract:graph-policy") in codes_by_node


def test_active_migrating_requirement_cannot_supply_traceability() -> None:
    graph = _non_product_graph()
    graph = replace(
        graph,
        nodes=tuple(
            replace(node, classifications=(Classification.MIGRATING,))
            if node.id == "requirement:GRAPH-001"
            else node
            for node in graph.nodes
        ),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("IMPLEMENTATION_ORPHAN", "contract:graph-policy") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_every_active_requirement_needs_identity_and_approval_even_if_quarantined() -> None:
    graph = _non_product_graph()
    graph = replace(
        graph,
        nodes=tuple(
            replace(
                node,
                requirement_id=None,
                approval=None,
                classifications=(Classification.QUARANTINED,),
            )
            if node.id == "requirement:GRAPH-001"
            else node
            for node in graph.nodes
        ),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    codes_by_node = {(item.code, item.node_id) for item in diagnostics}
    assert ("REQUIREMENT_STABLE_ID_MISSING", "requirement:GRAPH-001") in codes_by_node
    assert ("REQUIREMENT_OWNER_APPROVAL_MISSING", "requirement:GRAPH-001") in codes_by_node


def test_active_requirements_need_unique_stable_ids() -> None:
    graph = _non_product_graph()
    duplicate = GraphNode(
        "requirement:GRAPH-001-DUPLICATE",
        "Requirement",
        "architecture",
        Lifecycle.DECLARED,
        requirement_id="GRAPH-001",
        approval="owner-approved",
    )

    diagnostics = check_graph(replace(graph, nodes=(*graph.nodes, duplicate)), Phase.PRECOMMIT)

    assert ("REQUIREMENT_STABLE_ID_DUPLICATE", "requirement:GRAPH-001-DUPLICATE") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_metadata_only_requirement_coverage_is_not_a_traceability_path() -> None:
    graph = _non_product_graph()
    metadata_only = GraphNode(
        "module:metadata-only",
        "SourceModule",
        "architecture",
        Lifecycle.IMPLEMENTED,
        requirements=("GRAPH-001",),
    )

    diagnostics = check_graph(replace(graph, nodes=(*graph.nodes, metadata_only)), Phase.PRECOMMIT)

    assert ("IMPLEMENTATION_ORPHAN", "module:metadata-only") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_complete_product_traceability_chain_is_accepted() -> None:
    assert check_graph(_product_graph(), Phase.PRECOMMIT) == ()


def test_complete_product_traceability_chain_accepts_a_kill_criterion() -> None:
    assert check_graph(_product_graph(criterion_kind="KillCriterion"), Phase.PRECOMMIT) == ()


def test_product_requirement_cannot_skip_acceptance_or_kill_criterion() -> None:
    diagnostics = check_graph(_product_graph(include_criterion=False), Phase.PRECOMMIT)

    assert ("PRODUCT_TRACEABILITY_INCOMPLETE", "requirement:PROD-001") in {
        (item.code, item.node_id) for item in diagnostics
    }


def _migration_document() -> dict[str, object]:
    requirement = {
        "id": "requirement:MIG-001", "kind": "Requirement", "owner": "architecture",
        "lifecycle": "DECLARED", "requirement_id": "MIG-001",
        "requirement_class": "NON_PRODUCT", "approval": "owner-approved",
    }
    predecessor = {
        "id": "configuration:legacy-policy", "kind": "Configuration", "owner": "architecture",
        "lifecycle": "IMPLEMENTED", "active": False, "classifications": ["MIGRATING"],
        "replacement": "configuration:canonical-policy", "expiry_utc": "2030-01-01T00:00:00Z",
        "removal_gate": "gate:legacy-policy-removal", "rollback_node": "rollback:legacy-policy",
    }
    nodes = [
        requirement,
        predecessor,
        {"id": "configuration:canonical-policy", "kind": "Configuration", "owner": "architecture", "lifecycle": "IMPLEMENTED", "canonical_for": predecessor["id"], "requirements": ["MIG-001"]},
        {"id": "approval:migration-policy", "kind": "Approval", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "contract:migration-policy", "kind": "Contract", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "module:migration-policy", "kind": "SourceModule", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "dataflow:migration-policy", "kind": "DataFlow", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "test:canonical-policy", "kind": "TestOrEval", "owner": "architecture", "lifecycle": "IMPLEMENTED", "requirements": ["MIG-001"]},
        {"id": "gate:legacy-policy-removal", "kind": "ClawGate", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "artifact:canonical-policy", "kind": "Artifact", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "evidence:canonical-policy", "kind": "Evidence", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
        {"id": "rollback:legacy-policy", "kind": "Rollback", "owner": "architecture", "lifecycle": "DECLARED", "requirements": ["MIG-001"]},
    ]
    edges = [
        {"from": requirement["id"], "to": "approval:migration-policy", "kind": "approved_by"},
        {"from": requirement["id"], "to": "contract:migration-policy", "kind": "specified_by"},
        {"from": "contract:migration-policy", "to": "configuration:canonical-policy", "kind": "implements"},
        {"from": "contract:migration-policy", "to": "module:migration-policy", "kind": "implements"},
        {"from": "module:migration-policy", "to": "dataflow:migration-policy", "kind": "produces"},
        {"from": "dataflow:migration-policy", "to": "test:canonical-policy", "kind": "validated_by"},
        {"from": "test:canonical-policy", "to": "gate:legacy-policy-removal", "kind": "gated_by"},
        {"from": "gate:legacy-policy-removal", "to": "artifact:canonical-policy", "kind": "packaged_in"},
        {"from": "artifact:canonical-policy", "to": "evidence:canonical-policy", "kind": "evidenced_by"},
        {"from": "evidence:canonical-policy", "to": "rollback:legacy-policy", "kind": "rolled_back_by"},
        {"from": "configuration:canonical-policy", "to": predecessor["id"], "kind": "supersedes"},
        {"from": predecessor["id"], "to": "gate:legacy-policy-removal", "kind": "gated_by"},
        {"from": predecessor["id"], "to": "rollback:legacy-policy", "kind": "rolled_back_by"},
    ]
    for edge in edges:
        if edge["kind"] not in {"supersedes", "conflicts_with", "resolved_by", "derived_from", "falsified_by"}:
            edge["proof_for"] = "MIG-001"
    return {
        "manifest_version": 1,
        "phase_policy_times": {"precommit": "2029-12-31T23:59:59Z"},
        "nodes": nodes,
        "edges": edges,
    }


def _load_migration_graph(tmp_path: Path, document: dict[str, object]):
    (tmp_path / "architecture.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )
    return load_graph(tmp_path, allow_single_file_fixture=True)


def _migration_codes(
    tmp_path: Path,
    document: dict[str, object],
    *,
    policy_time_utc: str | None = None,
) -> set[str]:
    if policy_time_utc is not None:
        document["phase_policy_times"] = {"precommit": policy_time_utc}
    graph = _load_migration_graph(tmp_path, document)
    diagnostics = check_graph(graph, Phase.PRECOMMIT)
    return {item.code for item in diagnostics}


def test_proof_lifecycle_is_limited_to_the_five_proof_states() -> None:
    assert {item.value for item in Lifecycle} == {
        "DECLARED",
        "IMPLEMENTED",
        "VERIFIED",
        "REALIZED",
        "RETIRED",
    }


def test_migration_is_an_orthogonal_classification_not_a_proof_lifecycle(tmp_path: Path) -> None:
    graph = _load_migration_graph(tmp_path, _migration_document())

    assert graph is not None
    legacy = graph.node("configuration:legacy-policy")
    assert legacy.lifecycle is Lifecycle.IMPLEMENTED
    assert {item.value for item in legacy.classifications} == {"MIGRATING"}


def test_migration_requires_an_inactive_predecessor(tmp_path: Path) -> None:
    document = _migration_document()
    document["nodes"][1]["active"] = True

    assert "MIGRATION_PREDECESSOR_ACTIVE" in _migration_codes(tmp_path, document)


def test_migration_requires_replacement_expiry_removal_gate_and_rollback(tmp_path: Path) -> None:
    for field, expected_code in (
        ("replacement", "MIGRATION_REPLACEMENT_MISSING"),
        ("expiry_utc", "MIGRATION_EXPIRY_MISSING"),
        ("removal_gate", "MIGRATION_REMOVAL_GATE_MISSING"),
        ("rollback_node", "MIGRATION_ROLLBACK_MISSING"),
    ):
        document = _migration_document()
        del document["nodes"][1][field]

        assert expected_code in _migration_codes(tmp_path, document)


def test_migration_requires_exactly_one_active_canonical_replacement_and_edge(tmp_path: Path) -> None:
    no_edge = _migration_document()
    no_edge["edges"] = [
        edge for edge in no_edge["edges"] if edge["kind"] != "supersedes"
    ]
    assert "MIGRATION_REPLACEMENT_EDGE_MISSING" in _migration_codes(tmp_path, no_edge)

    dual_owner = _migration_document()
    dual_owner["nodes"].append(
        {
            "id": "configuration:second-canonical-policy",
            "kind": "Configuration",
            "owner": "architecture",
            "lifecycle": "IMPLEMENTED",
            "canonical_for": "configuration:legacy-policy",
        }
    )
    assert "MIGRATION_CANONICAL_OWNER_INVALID" in _migration_codes(tmp_path, dual_owner)


def test_migration_rejects_an_inactive_or_missing_canonical_owner(tmp_path: Path) -> None:
    inactive_owner = _migration_document()
    inactive_owner["nodes"][2]["active"] = False
    assert "MIGRATION_CANONICAL_OWNER_INVALID" in _migration_codes(
        tmp_path,
        inactive_owner,
    )

    missing_owner = _migration_document()
    del missing_owner["nodes"][2]["canonical_for"]
    assert "MIGRATION_CANONICAL_OWNER_INVALID" in _migration_codes(
        tmp_path,
        missing_owner,
    )


def test_migration_rejects_invalid_expiry_removal_gate_and_rollback(tmp_path: Path) -> None:
    invalid_expiry = _migration_document()
    invalid_expiry["nodes"][1]["expiry_utc"] = "not-a-utc-time"
    assert "MIGRATION_EXPIRY_INVALID" in _migration_codes(tmp_path, invalid_expiry)

    invalid_gate = _migration_document()
    invalid_gate["nodes"][1]["removal_gate"] = "rollback:legacy-policy"
    assert "MIGRATION_REMOVAL_GATE_INVALID" in _migration_codes(tmp_path, invalid_gate)

    invalid_rollback = _migration_document()
    invalid_rollback["nodes"][1]["rollback_node"] = "gate:legacy-policy-removal"
    assert "MIGRATION_ROLLBACK_INVALID" in _migration_codes(tmp_path, invalid_rollback)


def test_migration_must_be_runtime_unreachable(tmp_path: Path) -> None:
    document = _migration_document()
    document["runtime_dependencies"] = [
        {"from": "configuration:legacy-policy", "to": "configuration:canonical-policy"},
    ]

    assert "MIGRATION_RUNTIME_REACHABLE" in _migration_codes(tmp_path, document)


def test_migration_requires_versioned_phase_policy_time(tmp_path: Path) -> None:
    document = _migration_document()
    del document["phase_policy_times"]
    assert "MIGRATION_POLICY_TIME_MISSING" in _migration_codes(tmp_path, document)


def test_migration_rejects_an_invalid_versioned_phase_policy_time(tmp_path: Path) -> None:
    assert "MIGRATION_POLICY_TIME_INVALID" in _migration_codes(
        tmp_path,
        _migration_document(),
        policy_time_utc="not-a-utc-time",
    )


def test_expired_migration_requires_a_named_active_blocking_conflict(tmp_path: Path) -> None:
    assert "MIGRATION_EXPIRY_CONFLICT_MISSING" in _migration_codes(
        tmp_path,
        _migration_document(),
        policy_time_utc="2030-01-01T00:00:00Z",
    )


def test_expired_migration_accepts_a_named_active_blocking_conflict(tmp_path: Path) -> None:
    document = _migration_document()
    document["nodes"].append(
        {
            "id": "conflict:legacy-policy-expiry",
            "kind": "Conflict",
            "owner": "architecture",
            "lifecycle": "DECLARED",
        }
    )
    document["nodes"][1]["expiry_conflict"] = "conflict:legacy-policy-expiry"
    document["edges"].append(
        {
            "from": "configuration:legacy-policy",
            "to": "conflict:legacy-policy-expiry",
            "kind": "conflicts_with",
        }
    )

    assert "MIGRATION_EXPIRY_CONFLICT_MISSING" not in _migration_codes(
        tmp_path,
        document,
        policy_time_utc="2030-01-01T00:00:00Z",
    )


def _write_declared_conflict_fixture(tmp_path: Path, conflict_id: str) -> Path:
    tmp_path.mkdir()
    document = yaml.safe_load(
        (FIXTURES / "valid" / "architecture.yaml").read_text(encoding="utf-8")
    )
    document["receipts"] = []
    document["nodes"].append(
        {
            "id": conflict_id,
            "kind": "Conflict",
            "owner": "architecture",
            "lifecycle": "DECLARED",
            "requirements": ["GRAPH-011"],
        }
    )
    path = tmp_path / "architecture.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return tmp_path


def _run_graph_cli(manifest_root: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            str(manifest_root),
            "--phase",
            phase,
            "--format",
            "json",
            "--allow-declared-conflicts",
            "--single-file-fixture",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_declared_conflict_waiver_is_closed_to_precommit_m0_baseline(tmp_path: Path) -> None:
    baseline = ROOT / "architecture"
    malicious = _write_declared_conflict_fixture(
        tmp_path / "malicious",
        "conflict:malicious-waiver",
    )

    precommit = _run_graph_cli(baseline, "precommit")
    merge = _run_graph_cli(baseline, "merge")
    unknown = _run_graph_cli(malicious, "precommit")

    assert precommit.returncode == 0, precommit.stderr
    assert "DECLARED_CONFLICT" in precommit.stdout
    assert merge.returncode != 0
    assert unknown.returncode != 0


def test_cli_uses_versioned_manifest_time_and_rejects_caller_injection(tmp_path: Path) -> None:
    _load_migration_graph(tmp_path, _migration_document())

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            str(tmp_path),
            "--phase",
            "precommit",
            "--single-file-fixture",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    injected = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            str(tmp_path),
            "--phase",
            "precommit",
            "--evaluation-time-utc",
            "2029-12-31T23:59:59Z",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout
    assert injected.returncode == 2
    assert "unrecognized arguments" in injected.stderr
