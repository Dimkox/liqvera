"""Regression tests for the second M0 final-review correction wave."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from tools.graph_checker.__main__ import _is_m0_waived_conflict
from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import GraphLoadError, load_graph
from tools.graph_checker.model import (
    ArchitectureGraph,
    ArtifactBinding,
    Classification,
    GraphEdge,
    GraphNode,
    Lifecycle,
    PathClass,
    Phase,
    RepositoryArtifact,
    RepositoryInventoryExclusion,
)

SPEC_NODE_KINDS = {
    "Actor",
    "Outcome",
    "Hypothesis",
    "Metric",
    "Requirement",
    "AcceptanceCriterion",
    "KillCriterion",
    "Approval",
    "ADR",
    "Contract",
    "SourceModule",
    "DataFlow",
    "Configuration",
    "Migration",
    "TestOrEval",
    "ClawGate",
    "Artifact",
    "Deployment",
    "Telemetry",
    "Evidence",
    "Rollback",
    "Conflict",
}


def _write_manifest(tmp_path: Path, document: dict[str, object]) -> Path:
    (tmp_path / "architecture.yaml").write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )
    return tmp_path


def _requirement_document(**overrides: object) -> dict[str, object]:
    requirement = {
        "id": "requirement:GRAPH-001",
        "kind": "Requirement",
        "owner": "architecture",
        "lifecycle": "DECLARED",
        "requirement_id": "GRAPH-001",
        "requirement_class": "NON_PRODUCT",
        "approval": "owner-approved",
    }
    requirement.update(overrides)
    return {"manifest_version": 1, "nodes": [requirement]}


def test_loader_accepts_only_the_spec_node_kind_vocabulary(tmp_path: Path) -> None:
    for unsupported in (
        "RuntimeComponent",
        "Strategy",
        "Document",
        "Tool",
        "EvidencePlan",
        "ReleaseBoundary",
        "DeploymentBoundary",
    ):
        document = _requirement_document(kind=unsupported)
        del document["nodes"][0]["requirement_class"]

        with pytest.raises(GraphLoadError, match="kind is not recognized"):
            load_graph(_write_manifest(tmp_path, document), allow_single_file_fixture=True)


def test_requirement_classification_is_closed_and_loaded(tmp_path: Path) -> None:
    graph = load_graph(
        _write_manifest(tmp_path, _requirement_document()),
        allow_single_file_fixture=True,
    )

    requirement = graph.node("requirement:GRAPH-001")
    assert requirement.requirement_class == "NON_PRODUCT"

    invalid = _requirement_document(requirement_class="OWNER_NAME_HEURISTIC")
    with pytest.raises(GraphLoadError, match="requirement_class is not recognized"):
        load_graph(_write_manifest(tmp_path, invalid), allow_single_file_fixture=True)


def test_active_requirement_needs_canonical_stable_id_and_explicit_classification() -> None:
    requirement = GraphNode(
        "requirement:bad",
        "Requirement",
        "product",
        Lifecycle.DECLARED,
        requirement_id="prod-1",
        approval="owner-approved",
    )

    diagnostics = check_graph(ArchitectureGraph((requirement,)), Phase.PRECOMMIT)

    assert {
        "REQUIREMENT_CLASS_MISSING",
        "REQUIREMENT_STABLE_ID_INVALID",
    } <= {item.code for item in diagnostics}


def test_capabilities_are_closed_and_validated_for_every_node() -> None:
    contract = GraphNode(
        "contract:unexpected-capability",
        "Contract",
        "architecture",
        Lifecycle.DECLARED,
        capabilities=("capture-read",),
    )
    unknown = GraphNode(
        "module:unknown-capability",
        "SourceModule",
        "capture",
        Lifecycle.DECLARED,
        profile="public-capture",
        capabilities=("teleport-orders",),
    )

    diagnostics = check_graph(ArchitectureGraph((contract, unknown)), Phase.PRECOMMIT)

    codes_by_node = {(item.code, item.node_id) for item in diagnostics}
    assert ("NODE_CAPABILITY_COMBINATION_INVALID", contract.id) in codes_by_node
    assert ("CAPABILITY_UNKNOWN", unknown.id) in codes_by_node


SPEC_EDGE_KINDS = {
    "serves",
    "intends",
    "measured_by",
    "falsified_by",
    "approved_by",
    "specified_by",
    "owned_by",
    "implements",
    "consumes",
    "produces",
    "validated_by",
    "gated_by",
    "packaged_in",
    "deployed_by",
    "observed_by",
    "evidenced_by",
    "rolled_back_by",
    "supersedes",
    "conflicts_with",
    "resolved_by",
    "derived_from",
}


def _product_graph() -> ArchitectureGraph:
    requirement_id = "PROD-001"

    def edge(from_id: str, to_id: str, kind: str) -> GraphEdge:
        return GraphEdge(from_id, to_id, kind, proof_for=requirement_id)

    def node(node_id: str, kind: str, owner: str = "product") -> GraphNode:
        return GraphNode(
            node_id,
            kind,
            owner,
            Lifecycle.DECLARED,
            requirements=(requirement_id,),
        )

    actor = node("actor:operator", "Actor")
    outcome = node("outcome:decision", "Outcome")
    requirement = GraphNode(
        "requirement:PROD-001",
        "Requirement",
        "product",
        Lifecycle.DECLARED,
        requirement_id=requirement_id,
        requirement_class="PRODUCT",
        approval="owner-approved",
    )
    approval = node("approval:PROD-001", "Approval")
    criterion = node("acceptance:PROD-001", "AcceptanceCriterion")
    metric = node("metric:decision", "Metric")
    contract = node("contract:decision", "Contract")
    source = node("module:decision", "SourceModule")
    dataflow = node("dataflow:decision", "DataFlow")
    test = node("test:decision", "TestOrEval")
    gate = node("gate:decision", "ClawGate")
    artifact = node("artifact:decision", "Artifact")
    evidence = node("evidence:decision", "Evidence")
    rollback = node("rollback:decision", "Rollback")
    return ArchitectureGraph(
        (
            actor,
            outcome,
            requirement,
            approval,
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
        (
            edge(actor.id, outcome.id, "intends"),
            edge(outcome.id, requirement.id, "serves"),
            edge(requirement.id, approval.id, "approved_by"),
            edge(requirement.id, criterion.id, "specified_by"),
            edge(criterion.id, metric.id, "measured_by"),
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


def test_complete_spec_product_traceability_automaton_is_accepted() -> None:
    assert check_graph(_product_graph(), Phase.PRECOMMIT) == ()


@pytest.mark.parametrize(
    "missing_kind",
    (
        "Actor",
        "Outcome",
        "Approval",
        "AcceptanceCriterion",
        "Metric",
        "Contract",
        "SourceModule",
        "DataFlow",
        "TestOrEval",
        "ClawGate",
        "Artifact",
        "Evidence",
        "Rollback",
    ),
)
def test_product_traceability_rejects_every_missing_stage(missing_kind: str) -> None:
    graph = _product_graph()
    removed_ids = {node.id for node in graph.nodes if node.kind == missing_kind}
    graph = replace(
        graph,
        nodes=tuple(node for node in graph.nodes if node.id not in removed_ids),
        edges=tuple(
            edge
            for edge in graph.edges
            if edge.from_id not in removed_ids and edge.to_id not in removed_ids
        ),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert "PRODUCT_TRACEABILITY_INCOMPLETE" in {item.code for item in diagnostics}


def test_alternate_semantic_edge_aliases_are_not_accepted() -> None:
    graph = _product_graph()
    aliases = (
        "accepts",
        "deploys_to",
        "evaluated_by",
        "forbids",
        "governed_by",
        "plans_evidence",
        "pursues",
        "recovers_with",
        "requires",
        "resolves",
        "reviewed_by",
        "specifies",
        "transports",
        "validates",
    )

    for alias in aliases:
        candidate = replace(
            graph,
            edges=(GraphEdge("actor:operator", "outcome:decision", alias),),
        )
        diagnostics = check_graph(candidate, Phase.PRECOMMIT)
        assert "EDGE_KIND_UNKNOWN" in {item.code for item in diagnostics}, alias


def test_requirement_metadata_must_equal_reachable_approved_ids() -> None:
    graph = _product_graph()
    graph = replace(
        graph,
        nodes=tuple(
            replace(node, requirements=("PROD-999",))
            if node.id == "module:decision"
            else node
            for node in graph.nodes
        ),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("REQUIREMENT_METADATA_MISMATCH", "module:decision") in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_conflict_edges_never_supply_positive_provenance() -> None:
    requirement = GraphNode(
        "requirement:GRAPH-001",
        "Requirement",
        "architecture",
        Lifecycle.DECLARED,
        requirement_id="GRAPH-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    artifact = GraphNode(
        "artifact:forbidden",
        "Artifact",
        "security",
        Lifecycle.DECLARED,
        requirements=("GRAPH-001",),
    )
    graph = ArchitectureGraph(
        (requirement, artifact),
        (GraphEdge(requirement.id, artifact.id, "conflicts_with"),),
    )

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    assert ("IMPLEMENTATION_ORPHAN", artifact.id) in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_realized_lifecycle_is_always_forbidden_in_m0() -> None:
    node = GraphNode("evidence:impossible", "Evidence", "ci", Lifecycle.REALIZED, active=False)

    diagnostics = check_graph(ArchitectureGraph((node,)), Phase.PRECOMMIT)

    assert ("M0_REALIZED_LIFECYCLE_FORBIDDEN", node.id) in {
        (item.code, item.node_id) for item in diagnostics
    }


def test_receipt_declaration_is_required_by_lifecycle_and_due_phase() -> None:
    verified = GraphNode("evidence:verified", "Evidence", "ci", Lifecycle.VERIFIED)
    phase_due = GraphNode(
        "gate:due",
        "ClawGate",
        "ci",
        Lifecycle.IMPLEMENTED,
        required_from=Phase.MERGE,
        required_lifecycle=Lifecycle.VERIFIED,
    )
    graph = ArchitectureGraph((verified, phase_due))

    precommit = check_graph(graph, Phase.PRECOMMIT)
    merge = check_graph(graph, Phase.MERGE)

    assert ("RECEIPT_REQUIRED_MISSING", verified.id) in {
        (item.code, item.node_id) for item in precommit
    }
    assert ("RECEIPT_REQUIRED_MISSING", phase_due.id) not in {
        (item.code, item.node_id) for item in precommit
    }
    assert ("RECEIPT_REQUIRED_MISSING", phase_due.id) in {
        (item.code, item.node_id) for item in merge
    }


def _migration_graph(*, policy_time: str = "2029-12-31T23:59:59Z") -> ArchitectureGraph:
    predecessor = GraphNode(
        "configuration:legacy",
        "Configuration",
        "architecture",
        Lifecycle.IMPLEMENTED,
        active=False,
        classifications=(Classification.MIGRATING,),
        replacement="configuration:canonical",
        expiry_utc="2030-01-01T00:00:00Z",
        removal_gate="gate:remove-legacy",
        rollback_node="rollback:legacy",
        expiry_conflict="conflict:legacy-expired",
    )
    replacement = GraphNode(
        "configuration:canonical",
        "Configuration",
        "architecture",
        Lifecycle.IMPLEMENTED,
        canonical_for=predecessor.id,
    )
    gate = GraphNode("gate:remove-legacy", "ClawGate", "ci", Lifecycle.DECLARED)
    rollback = GraphNode("rollback:legacy", "Rollback", "architecture", Lifecycle.DECLARED)
    conflict = GraphNode(
        "conflict:legacy-expired", "Conflict", "architecture", Lifecycle.DECLARED, active=False
    )
    return ArchitectureGraph(
        (predecessor, replacement, gate, rollback, conflict),
        (
            GraphEdge(replacement.id, predecessor.id, "supersedes"),
            GraphEdge(predecessor.id, gate.id, "gated_by"),
            GraphEdge(predecessor.id, rollback.id, "rolled_back_by"),
            GraphEdge(predecessor.id, conflict.id, "conflicts_with"),
        ),
        phase_policy_times=((Phase.PRECOMMIT, policy_time),),
    )


def test_migration_uses_exact_typed_relations_and_trusted_phase_time() -> None:
    graph = _migration_graph()

    diagnostics = check_graph(graph, Phase.PRECOMMIT)

    migration_codes = {item.code for item in diagnostics if item.code.startswith("MIGRATION_")}
    assert migration_codes == set()


@pytest.mark.parametrize(
    ("field", "code"),
    (
        ("replacement", "MIGRATION_FIELD_WITHOUT_CLASSIFICATION"),
        ("expiry_utc", "MIGRATION_FIELD_WITHOUT_CLASSIFICATION"),
        ("removal_gate", "MIGRATION_FIELD_WITHOUT_CLASSIFICATION"),
        ("rollback_node", "MIGRATION_FIELD_WITHOUT_CLASSIFICATION"),
        ("expiry_conflict", "MIGRATION_FIELD_WITHOUT_CLASSIFICATION"),
    ),
)
def test_migration_predecessor_fields_require_migrating_classification(
    field: str, code: str
) -> None:
    node = GraphNode(
        "configuration:not-migrating",
        "Configuration",
        "architecture",
        Lifecycle.IMPLEMENTED,
        **{field: "bound:value"},
    )

    assert code in {item.code for item in check_graph(ArchitectureGraph((node,)), Phase.PRECOMMIT)}


@pytest.mark.parametrize(
    ("edge_kind", "expected_code"),
    (
        ("specified_by", "MIGRATION_REPLACEMENT_EDGE_MISSING"),
        ("validated_by", "MIGRATION_REMOVAL_GATE_EDGE_MISSING"),
        ("derived_from", "MIGRATION_ROLLBACK_EDGE_MISSING"),
    ),
)
def test_migration_relations_cannot_be_satisfied_by_wrong_edge_type(
    edge_kind: str, expected_code: str
) -> None:
    graph = _migration_graph()
    target = {
        "specified_by": "configuration:legacy",
        "validated_by": "gate:remove-legacy",
        "derived_from": "rollback:legacy",
    }[edge_kind]
    source = "configuration:canonical" if edge_kind == "specified_by" else "configuration:legacy"
    correct = {
        "specified_by": "supersedes",
        "validated_by": "gated_by",
        "derived_from": "rolled_back_by",
    }[edge_kind]
    graph = replace(
        graph,
        edges=tuple(edge for edge in graph.edges if edge.kind != correct)
        + (GraphEdge(source, target, edge_kind),),
    )

    assert expected_code in {item.code for item in check_graph(graph, Phase.PRECOMMIT)}


def test_expired_migration_requires_exact_named_conflict_identity_and_edge() -> None:
    graph = _migration_graph(policy_time="2030-01-01T00:00:00Z")
    wrong = GraphNode("conflict:other", "Conflict", "architecture", Lifecycle.DECLARED)
    graph = replace(
        graph,
        nodes=(*graph.nodes, wrong),
        edges=tuple(edge for edge in graph.edges if edge.kind != "conflicts_with")
        + (GraphEdge("configuration:legacy", wrong.id, "conflicts_with"),),
    )

    assert "MIGRATION_EXPIRY_CONFLICT_MISSING" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_migration_rejects_missing_or_invalid_manifest_phase_time() -> None:
    missing = replace(_migration_graph(), phase_policy_times=())
    invalid = replace(
        _migration_graph(), phase_policy_times=((Phase.PRECOMMIT, "caller-controlled"),)
    )

    assert "MIGRATION_POLICY_TIME_MISSING" in {
        item.code for item in check_graph(missing, Phase.PRECOMMIT)
    }
    assert "MIGRATION_POLICY_TIME_INVALID" in {
        item.code for item in check_graph(invalid, Phase.PRECOMMIT)
    }


def test_declared_conflict_waiver_fingerprints_the_full_immutable_identity() -> None:
    allowed = GraphNode(
        "conflict:go-stage-a-build",
        "Conflict",
        "runtime",
        Lifecycle.DECLARED,
        requirements=("ARCH-GO-001", "ARCH-GO-004"),
    )
    assert _is_m0_waived_conflict(ArchitectureGraph((allowed,)), allowed.id)

    for mutation in (
        replace(allowed, owner="attacker"),
        replace(allowed, requirements=("GRAPH-011",)),
        replace(allowed, active=False),
        replace(allowed, lifecycle=Lifecycle.IMPLEMENTED),
    ):
        assert not _is_m0_waived_conflict(ArchitectureGraph((mutation,)), mutation.id)


def test_repository_inventory_rejects_every_unbound_tracked_runtime_artifact() -> None:
    owner = GraphNode("module:inventory-owner", "SourceModule", "architecture", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (owner,),
        repository_artifacts=(
            RepositoryArtifact(
                "src/multi_exchange_engine/new_runtime.py", PathClass.RUNTIME_SOURCE
            ),
        ),
    )

    assert "REPOSITORY_ARTIFACT_UNDECLARED" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }

    bound = replace(
        graph,
        artifact_bindings=(
            ArtifactBinding(
                "src/multi_exchange_engine/new_runtime.py",
                owner.id,
                PathClass.RUNTIME_SOURCE,
            ),
        ),
    )
    assert "REPOSITORY_ARTIFACT_UNDECLARED" not in {
        item.code for item in check_graph(bound, Phase.PRECOMMIT)
    }


def test_repository_inventory_exclusions_are_exact_and_explained() -> None:
    authority = GraphNode(
        "document:inventory-exclusions", "ADR", "architecture", Lifecycle.DECLARED
    )
    graph = ArchitectureGraph(
        (authority,),
        repository_artifacts=(
            RepositoryArtifact("research/quarantined.json", PathClass.RESEARCH),
        ),
        inventory_exclusions=(
            RepositoryInventoryExclusion(
                "research/quarantined.json",
                "RESEARCH_ONLY",
                authority.id,
                PathClass.RESEARCH,
            ),
        ),
    )
    assert not {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    } & {"REPOSITORY_ARTIFACT_UNDECLARED", "REPOSITORY_INVENTORY_EXCLUSION_INVALID"}

    with pytest.raises(ValueError, match="InventoryExclusionReason"):
        RepositoryInventoryExclusion(
            "research/quarantined.json", "", authority.id, PathClass.RESEARCH
        )


def test_repository_inventory_rejects_binding_for_untracked_artifact() -> None:
    owner = GraphNode("module:inventory-owner", "SourceModule", "architecture", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (owner,),
        artifact_bindings=(ArtifactBinding("src/multi_exchange_engine/ghost.py", owner.id),),
    )

    assert "REPOSITORY_ARTIFACT_NOT_TRACKED" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_go_reference_cannot_escape_test_only_classification() -> None:
    graph = load_graph(Path("architecture"))
    graph = replace(
        graph,
        nodes=tuple(
            replace(node, classifications=()) if node.id == "runtime:go-reference" else node
            for node in graph.nodes
        ),
    )

    assert ("RUNTIME_GO_PROFILE_INVALID", "runtime:go-reference") in {
        (item.code, item.node_id) for item in check_graph(graph, Phase.PRECOMMIT)
    }


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    (
        ({"active": True}, "RUNTIME_EXECUTION_BOUNDARY_INVALID"),
        ({"classifications": ()}, "RUNTIME_EXECUTION_BOUNDARY_INVALID"),
        ({"kind": "SourceModule"}, "NODE_CAPABILITY_COMBINATION_INVALID"),
    ),
)
def test_quarantined_execution_artifact_cannot_become_runtime_authority(
    mutation: dict[str, object],
    expected_code: str,
) -> None:
    graph = load_graph(Path("architecture"))
    graph = replace(
        graph,
        nodes=tuple(
            replace(node, **mutation) if node.id == "artifact:stage-a-execution" else node
            for node in graph.nodes
        ),
    )

    assert (expected_code, "artifact:stage-a-execution") in {
        (item.code, item.node_id) for item in check_graph(graph, Phase.PRECOMMIT)
    }
