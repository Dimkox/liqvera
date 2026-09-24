"""Regression coverage for the third M0 final-review correction wave."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import (
    GraphLoadError,
    _classify_repository_path,
    load_graph,
)
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


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        ("src/new_runtime/component.rs", PathClass.RUNTIME_SOURCE),
        ("tests/future/test_component.rs", PathClass.TEST_SOURCE),
        ("docs/operator-runbook.md", PathClass.DOCUMENTATION),
        ("README.md", PathClass.DOCUMENTATION),
        ("SECURITY.md", PathClass.DOCUMENTATION),
        ("ops/windows/promote.ps1", PathClass.POWERSHELL),
        ("compose.stage-a.yaml", PathClass.COMPOSE),
        ("future_runtime/module.wasm", PathClass.RUNTIME_SOURCE),
    ),
)
def test_repository_classifier_is_prefix_registry_not_extension_allowlist(
    path: str, expected: PathClass
) -> None:
    assert _classify_repository_path(path) is expected


@pytest.mark.parametrize(
    "path",
    (
        "scripts/promote-a2-candidate.sh",
        "deploy/n8n/stage-a-orchestrator.workflow.json",
    ),
)
def test_private_and_mutating_entrypoints_are_never_public_authority(path: str) -> None:
    graph = load_graph(Path("architecture"))
    binding = next(item for item in graph.artifact_bindings if item.path == path)
    authority = graph.node(binding.node_id)

    assert binding.path_class in {PathClass.EXECUTION_SOURCE, PathClass.DEPLOYMENT_ENTRYPOINT}
    assert authority.id == "artifact:stage-a-execution"
    assert not authority.active
    assert Classification.QUARANTINED in authority.classifications
    assert authority.profile == "execution"


@pytest.mark.parametrize("path", ("README.md", "SECURITY.md"))
def test_top_level_governance_documents_have_explicit_active_inventory_authority(
    path: str,
) -> None:
    graph = load_graph(Path("architecture"))
    binding = next(item for item in graph.artifact_bindings if item.path == path)
    authority = graph.node(binding.node_id)

    assert binding.path_class is PathClass.DOCUMENTATION
    assert authority.id == "document:graph-authority-handoff"
    assert authority.kind == "ADR" and authority.active


def test_stage_a_images_are_active_packaging_and_private_image_stays_blocked() -> None:
    graph = load_graph(Path("architecture"))
    capture = next(
        item
        for item in graph.artifact_bindings
        if item.path == "deploy/images/Dockerfile.public-capture"
    )
    analyzer = next(
        item
        for item in graph.artifact_bindings
        if item.path == "deploy/images/Dockerfile.readonly-analyzer"
    )

    assert capture.path_class is PathClass.BUILD_PACKAGING
    assert analyzer.path_class is PathClass.BUILD_PACKAGING
    assert graph.node(capture.node_id).kind == "Artifact"
    assert graph.node(capture.node_id).active
    assert graph.node(analyzer.node_id).active
    assert ("DECLARED_CONFLICT", "conflict:a2-private-production-image") in {
        (item.code, item.node_id) for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_production_loader_requires_all_six_manifests(tmp_path: Path) -> None:
    (tmp_path / "architecture.yaml").write_text("manifest_version: 1\n", encoding="utf-8")

    with pytest.raises(GraphLoadError, match="repository manifest set is invalid"):
        load_graph(tmp_path)

    graph = load_graph(tmp_path, allow_single_file_fixture=True)
    assert graph.nodes == ()


def test_copied_six_file_manifest_set_does_not_gain_repository_authority(
    tmp_path: Path,
) -> None:
    manifest_names = (
        "requirements.yaml",
        "architecture.yaml",
        "runtime.yaml",
        "data-contracts.yaml",
        "strategies.yaml",
        "release.yaml",
    )
    for index, name in enumerate(manifest_names):
        document: dict[str, object] = {"manifest_version": 2}
        if index == 0:
            document["phase_policy_times"] = {"merge": "2030-01-01T00:00:00Z"}
        (tmp_path / name).write_text(
            yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
        )

    graph = load_graph(tmp_path)

    assert not graph.policy_times_trusted
    assert "PHASE_POLICY_TIME_TRUST_MISSING" in {
        item.code for item in check_graph(graph, Phase.MERGE)
    }


def _inventory_graph(
    artifact: RepositoryArtifact,
    *,
    authority: GraphNode,
    binding: ArtifactBinding | None = None,
    exclusion: RepositoryInventoryExclusion | None = None,
) -> ArchitectureGraph:
    return ArchitectureGraph(
        (authority,),
        repository_artifacts=(artifact,),
        artifact_bindings=(binding,) if binding else (),
        inventory_exclusions=(exclusion,) if exclusion else (),
    )


def test_path_class_binding_matrix_rejects_public_binding_for_execution_source() -> None:
    authority = GraphNode(
        "runtime:public-capture",
        "SourceModule",
        "capture",
        Lifecycle.IMPLEMENTED,
        profile="public-capture",
        capabilities=("public-venue", "capture-write"),
    )
    artifact = RepositoryArtifact("src/venue/trading.rs", PathClass.EXECUTION_SOURCE)
    binding = ArtifactBinding(artifact.path, authority.id, artifact.path_class)

    diagnostics = check_graph(
        _inventory_graph(artifact, authority=authority, binding=binding),
        Phase.PRECOMMIT,
    )

    assert "REPOSITORY_BINDING_AUTHORITY_INVALID" in {item.code for item in diagnostics}


@pytest.mark.parametrize(
    "path_class",
    (PathClass.RUNTIME_SOURCE, PathClass.WORKFLOW, PathClass.DEPLOYMENT_ENTRYPOINT),
)
def test_runtime_workflow_and_deploy_entrypoints_cannot_be_excluded(
    path_class: PathClass,
) -> None:
    authority = GraphNode("contract:inventory", "Contract", "architecture", Lifecycle.DECLARED)
    artifact = RepositoryArtifact("future/item", path_class)
    exclusion = RepositoryInventoryExclusion(
        artifact.path,
        "RESEARCH_ONLY",
        authority.id,
        artifact.path_class,
    )

    diagnostics = check_graph(
        _inventory_graph(artifact, authority=authority, exclusion=exclusion),
        Phase.PRECOMMIT,
    )

    assert "REPOSITORY_INVENTORY_EXCLUSION_FORBIDDEN" in {
        item.code for item in diagnostics
    }


def test_inventory_rejects_wrong_class_and_unknown_exclusion_authority() -> None:
    authority = GraphNode(
        "runtime:contracts",
        "SourceModule",
        "contracts",
        Lifecycle.IMPLEMENTED,
        profile="contracts",
    )
    artifact = RepositoryArtifact("src/module.rs", PathClass.RUNTIME_SOURCE)
    wrong_binding = ArtifactBinding(artifact.path, authority.id, PathClass.TEST_SOURCE)
    invalid_exclusion = RepositoryInventoryExclusion(
        artifact.path,
        "RESEARCH_ONLY",
        "adr:missing",
        artifact.path_class,
    )

    binding_codes = {
        item.code
        for item in check_graph(
            _inventory_graph(artifact, authority=authority, binding=wrong_binding),
            Phase.PRECOMMIT,
        )
    }
    exclusion_codes = {
        item.code
        for item in check_graph(
            _inventory_graph(artifact, authority=authority, exclusion=invalid_exclusion),
            Phase.PRECOMMIT,
        )
    }

    assert "REPOSITORY_PATH_CLASS_MISMATCH" in binding_codes
    assert "REPOSITORY_INVENTORY_EXCLUSION_INVALID" in exclusion_codes


def test_evidence_derived_from_must_form_a_dag() -> None:
    first = GraphNode("evidence:first", "Evidence", "ci", Lifecycle.DECLARED)
    second = GraphNode("evidence:second", "Evidence", "ci", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (first, second),
        (
            GraphEdge(first.id, second.id, "derived_from"),
            GraphEdge(second.id, first.id, "derived_from"),
        ),
    )

    assert "PROVENANCE_LINEAGE_CYCLE" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


@pytest.mark.parametrize("relation", ("derived_from", "supersedes"))
def test_combined_provenance_rejects_self_cycles(relation: str) -> None:
    evidence = GraphNode("evidence:self", "Evidence", "ci", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (evidence,),
        (GraphEdge(evidence.id, evidence.id, relation),),
    )

    assert "PROVENANCE_LINEAGE_CYCLE" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_one_predecessor_cannot_have_multiple_semantic_superseding_successors() -> None:
    predecessor = GraphNode(
        "configuration:legacy",
        "Configuration",
        "architecture",
        Lifecycle.IMPLEMENTED,
        active=False,
    )
    first = GraphNode(
        "configuration:first", "Configuration", "architecture", Lifecycle.IMPLEMENTED
    )
    second = GraphNode(
        "configuration:second", "Configuration", "architecture", Lifecycle.IMPLEMENTED
    )
    graph = ArchitectureGraph(
        (predecessor, first, second),
        (
            GraphEdge(first.id, predecessor.id, "supersedes"),
            GraphEdge(second.id, predecessor.id, "supersedes"),
        ),
    )

    assert "SUPERSEDES_SUCCESSOR_AMBIGUOUS" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_one_predecessor_cannot_split_across_lineage_relations() -> None:
    predecessor = GraphNode(
        "evidence:predecessor", "Evidence", "ci", Lifecycle.DECLARED
    )
    first = GraphNode("evidence:first", "Evidence", "ci", Lifecycle.DECLARED)
    second = GraphNode("evidence:second", "Evidence", "ci", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (predecessor, first, second),
        (
            GraphEdge(first.id, predecessor.id, "derived_from"),
            GraphEdge(second.id, predecessor.id, "supersedes"),
        ),
    )

    assert "SUPERSEDES_SUCCESSOR_AMBIGUOUS" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_phase_policy_times_must_be_monotonic() -> None:
    graph = ArchitectureGraph(
        (),
        phase_policy_times=(
            (Phase.PRECOMMIT, "2030-01-02T00:00:00Z"),
            (Phase.MERGE, "2030-01-01T00:00:00Z"),
        ),
        policy_times_trusted=True,
    )

    assert "PHASE_POLICY_TIME_NON_MONOTONIC" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


@pytest.mark.parametrize("phase", tuple(Phase)[1:])
def test_merge_and_later_fail_closed_without_trusted_policy_time_context(
    phase: Phase,
) -> None:
    graph = ArchitectureGraph(
        (),
        phase_policy_times=((phase, "2030-01-01T00:00:00Z"),),
    )

    assert "PHASE_POLICY_TIME_TRUST_MISSING" in {
        item.code for item in check_graph(graph, phase)
    }


@pytest.mark.parametrize(
    "filename",
    ("verify-a2-pr-on-claw.yml", "build-a2-on-claw.yml"),
)
@pytest.mark.parametrize(
    "unbound",
    (
        "postgresql://a2_fixed:",
        ":pg-fixed@localhost:",
        "@localhost:5432/",
        "/a2_fixed",
    ),
)
def test_each_postgres_workflow_rejects_unbound_url_segments(
    filename: str, unbound: str
) -> None:
    workflow = (Path(".github/workflows") / filename).read_text(encoding="utf-8")
    url = 'A2_TEST_DATABASE_URL="postgresql://${postgres_identity}:${postgres_password}@127.0.0.1:${postgres_port}/${postgres_identity}"'
    assert url in workflow
    assert url not in workflow.replace(url, unbound)
    assert "openssl rand -hex 32" in workflow
    assert "--publish 127.0.0.1::5432" in workflow
    assert not re.search(r"(?m)^\s*POSTGRES_PASSWORD:",workflow)


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        (".agents/skills/example/SKILL.md", "VENDORED_TOOLING"),
        ("_bmad/scripts/check.py", "VENDORED_TOOLING"),
        ("packages/evil/execution.py", "EXECUTION_SOURCE"),
        ("services/private_api.py", "EXECUTION_SOURCE"),
        ("app/trader.py", "EXECUTION_SOURCE"),
        ("ops/deploy.sh", "DEPLOYMENT_ENTRYPOINT"),
        ("scripts/check.sh", "SHELL_SCRIPT"),
        ("ops/check.cmd", "BATCH_SCRIPT"),
        ("ops/check.bat", "BATCH_SCRIPT"),
        ("k8s/stage-a/deployment.yaml", "K8S_MANIFEST"),
        (".github/actions/graph/action.yml", "WORKFLOW"),
        ("future_unknown/component.wasm", "UNKNOWN_TRACKED"),
    ),
)
def test_repository_classifier_is_closed_and_default_deny(
    path: str, expected: str
) -> None:
    assert _classify_repository_path(path).value == expected


def test_repository_inventory_covers_all_tracked_paths_exactly_once() -> None:
    graph = load_graph(Path("architecture"))
    declarations = [item.path for item in graph.artifact_bindings] + [
        item.path for item in graph.inventory_exclusions
    ]

    assert len(graph.repository_artifacts) >= 626
    assert len(declarations) == len(graph.repository_artifacts)
    assert len(set(declarations)) == len(graph.repository_artifacts)
    assert {item.path for item in graph.repository_artifacts} == set(declarations)


def test_claw_host_inventory_paths_are_exactly_host_001_scoped() -> None:
    graph = load_graph(Path("architecture"))
    expected = {
        "schemas/claw-host-inventory-observation-v2.schema.json": "contract:proof-HOST-001",
        "scripts/collect_claw_host_inventory.py": "runtime:proof-HOST-001",
        "scripts/verify_claw_host_inventory.py": "runtime:proof-HOST-001",
        "tests/release/test_claw_host_inventory.py": "test:proof-HOST-001",
    }
    actual = {item.path: item.node_id for item in graph.artifact_bindings if item.path in expected}
    assert actual == expected
    for node_id in set(expected.values()):
        node = graph.node(node_id)
        assert node.active
        assert "HOST-001" in node.requirements


def test_claw_host_deployment_contract_paths_are_exactly_scoped() -> None:
    graph = load_graph(Path("architecture"))
    expected = {
        "schemas/claw-host-deployment-request-v1.schema.json": "contract:proof-HOST-009",
        "schemas/claw-host-deployment-receipt-v1.schema.json": "contract:proof-HOST-009",
        "schemas/claw-host-deployment-rollback-receipt-v1.schema.json": "contract:proof-HOST-009",
        "scripts/claw_host_deployment_contract.py": "runtime:proof-HOST-009",
        "scripts/verify_claw_host_deployment_approval.py": "runtime:proof-HOST-012",
        "tests/release/test_claw_host_deployment_contract.py": "test:proof-HOST-009",
    }
    actual = {item.path: item.node_id for item in graph.artifact_bindings if item.path in expected}
    assert actual == expected


def test_claw_host_deployment_d0_paths_are_exactly_scoped() -> None:
    graph = load_graph(Path("architecture"))
    expected = {
        "ci/claw/host-deployment-controller-manifest.json": "configuration:claw-disposable-pr-sandbox",
        "ci/claw/install-host-deployment-controller.sh": "runtime:proof-HOST-009",
        "ci/claw/systemd/mee-claw-host-deploy.socket": "configuration:claw-disposable-pr-sandbox",
        "ci/claw/systemd/mee-claw-host-deploy@.service": "configuration:claw-disposable-pr-sandbox",
        "ci/claw/systemd/mee-claw-host-deploy-reconcile.service": "configuration:claw-disposable-pr-sandbox",
        "ci/claw/systemd/mee-claw-host-deploy-reconcile.timer": "configuration:claw-disposable-pr-sandbox",
        "schemas/claw-host-deployment-d0-receipt-v1.schema.json": "contract:proof-HOST-009",
        "schemas/claw-host-deployment-response-v1.schema.json": "contract:proof-HOST-009",
        "schemas/claw-host-input-bundle-v1.schema.json": "contract:proof-HOST-002",
        "scripts/claw_host_deployment_client.py": "runtime:proof-HOST-009",
        "scripts/claw_host_deployment_controller.py": "runtime:proof-OCIAPATH-003",
        "scripts/claw_host_deployment_install.py": "runtime:proof-HOST-009",
        "tests/release/test_claw_host_deployment_install.py": "test:proof-HOST-009",
        "tests/release/test_claw_host_deployment_controller.py": "test:proof-HOST-009",
        "tests/release/test_claw_host_deployment_acquisition.py": "test:proof-OCIAPATH-003",
        "tests/release/test_claw_host_deployment_finalize.py": "test:proof-OCIAPATH-005",
        "tests/release/test_claw_host_pending_finalize.py": "test:proof-HOST-009",
    }
    actual = {item.path: item.node_id for item in graph.artifact_bindings if item.path in expected}
    assert actual == expected


def test_ociapath_requirements_have_exact_closed_source_only_proof_lanes() -> None:
    graph = load_graph(Path("architecture"))
    stable_ids = tuple(f"OCIAPATH-{ordinal:03d}" for ordinal in range(1, 6))
    lane = (
        ("approval", "Approval"),
        ("contract", "Contract"),
        ("runtime", "SourceModule"),
        ("dataflow", "DataFlow"),
        ("test", "TestOrEval"),
        ("gate", "ClawGate"),
        ("artifact", "Artifact"),
        ("evidence", "Evidence"),
        ("rollback", "Rollback"),
    )
    edge_lane = (
        ("requirement", "approved_by", "approval"),
        ("requirement", "specified_by", "contract"),
        ("contract", "implements", "runtime"),
        ("runtime", "produces", "dataflow"),
        ("dataflow", "validated_by", "test"),
        ("test", "gated_by", "gate"),
        ("gate", "packaged_in", "artifact"),
        ("artifact", "evidenced_by", "evidence"),
        ("evidence", "rolled_back_by", "rollback"),
    )
    expected_scoped_edges: set[tuple[str, str, str, str]] = set()

    for stable_id in stable_ids:
        requirement = graph.node(f"requirement:{stable_id}")
        assert requirement.owner == "security"
        assert requirement.lifecycle is Lifecycle.DECLARED
        assert requirement.requirement_id == stable_id
        assert requirement.approval == "owner-approved"
        for prefix, kind in lane:
            node = graph.node(f"{prefix}:proof-{stable_id}")
            assert node.kind.value == kind
            assert node.owner == "security"
            assert node.lifecycle is Lifecycle.DECLARED
            assert node.requirements == (stable_id,)
        for source, relation, target in edge_lane:
            source_id = f"requirement:{stable_id}" if source == "requirement" else f"{source}:proof-{stable_id}"
            target_id = f"{target}:proof-{stable_id}"
            expected_scoped_edges.add((source_id, relation, target_id, stable_id))
            matching = [
                edge for edge in graph.edges
                if edge.from_id == source_id
                and edge.kind == relation
                and edge.to_id == target_id
                and edge.proof_for == stable_id
            ]
            assert len(matching) == 1
        expected_scoped_edges.add((
            f"requirement:{stable_id}",
            "specified_by",
            "document:ociapath-source-only-authority-none",
            stable_id,
        ))
        expected_scoped_edges.add((
            "document:ociapath-source-only-authority-none",
            "validated_by",
            f"test:proof-{stable_id}",
            stable_id,
        ))

    actual_scoped_edges = {
        (edge.from_id, edge.kind, edge.to_id, edge.proof_for)
        for edge in graph.edges
        if edge.proof_for in stable_ids
    }
    assert actual_scoped_edges == expected_scoped_edges

    assert not [receipt for receipt in graph.receipts if "OCIAPATH-" in receipt.node_id]
    assert not [
        node for node in graph.nodes
        if node.kind.value == "Conflict"
        and set(node.requirements).intersection(stable_ids)
    ]


def test_ociapath_source_test_and_document_inventory_is_exactly_bound() -> None:
    graph = load_graph(Path("architecture"))
    expected = {
        "scripts/verify_oci_evidence_approval.py": "runtime:proof-OCIAPATH-001",
        "scripts/claw_host_deployment_controller.py": "runtime:proof-OCIAPATH-003",
        "scripts/claw_host_bootstrap_transaction.py": "runtime:proof-OCIAPATH-004",
        "tests/release/test_oci_evidence_v2.py": "test:proof-OCIAPATH-001",
        "tests/release/test_claw_host_deployment_acquisition.py": "test:proof-OCIAPATH-003",
        "tests/release/test_claw_host_transaction_matrix.py": "test:proof-OCIAPATH-004",
        "tests/release/test_claw_host_deployment_finalize.py": "test:proof-OCIAPATH-005",
        "tests/release/test_claw_source_controller_policy.py": "test:proof-OCIAPATH-005",
        "docs/implementation/1-2a-claw-engine-runner-host-transition.md":
            "document:ociapath-source-only-authority-none",
        "docs/planning/sprint-change-proposal-2026-08-13.md":
            "document:ociapath-source-only-authority-none",
        "docs/superpowers/plans/2026-08-13-claw-installed-approval-path.md":
            "document:ociapath-source-only-authority-none",
        "docs/superpowers/specs/2026-08-13-claw-host-deployment-controller-design.md":
            "document:ociapath-source-only-authority-none",
        "handoff.md": "document:ociapath-source-only-authority-none",
    }
    actual = {
        binding.path: binding.node_id
        for binding in graph.artifact_bindings
        if binding.path in expected
    }
    assert actual == expected
    authority = graph.node("document:ociapath-source-only-authority-none")
    assert authority.owner == "security"
    assert authority.lifecycle is Lifecycle.DECLARED
    assert set(authority.requirements) == {
        f"OCIAPATH-{ordinal:03d}" for ordinal in range(1, 6)
    }


def test_unified_program_documents_have_exact_graph_authority() -> None:
    graph = load_graph(Path("architecture"))
    expected = {
        "docs/implementation/1-1-bootstrap-trusted-default-branch-pr-identity-controller.md":
            "document:story-1-1-bootstrap-controller",
        "docs/implementation/1-2-vypolnyat-validation-v-disposable-multi-project-claw-sandbox.md":
            "document:story-1-2-disposable-claw-sandbox",
        "docs/implementation/sprint-status.yaml": "document:unified-program-sprint-status",
        "docs/planning/epics.md": "document:unified-graph-execution-program",
        "docs/planning/implementation-readiness-report-2026-08-11.md":
            "document:unified-graph-execution-program",
        "docs/superpowers/plans/2026-08-11-m0-m3-canonical-distributions-and-graph.md":
            "document:unified-graph-execution-program",
        "docs/superpowers/plans/2026-08-11-m4-evidence-runs-and-frozen-data.md":
            "document:unified-graph-execution-program",
        "docs/superpowers/plans/2026-08-11-m5-stage-a-v2-strategy-economics.md":
            "document:unified-graph-execution-program",
        "docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md":
            "document:unified-graph-execution-program",
        "docs/superpowers/plans/2026-08-11-unified-graph-migration-program.md":
            "document:unified-graph-execution-program",
    }

    actual = {
        binding.path: binding.node_id
        for binding in graph.artifact_bindings
        if binding.path in expected
    }
    assert actual == expected
    for authority_id in set(expected.values()):
        authority = graph.node(authority_id)
        assert authority.kind == "ADR"
        assert authority.active
        assert authority.owner.strip()
        assert authority.requirements
        assert graph.has_edge(authority_id, "validated_by", "test:graph-repository-manifests")


def test_story_1_1_and_sprint_status_are_consistent() -> None:
    story_key = "1-1-bootstrap-trusted-default-branch-pr-identity-controller"
    sprint = yaml.safe_load(Path("docs/implementation/sprint-status.yaml").read_text(encoding="utf-8"))
    story = Path(f"docs/implementation/{story_key}.md").read_text(encoding="utf-8")
    epics = Path("docs/planning/epics.md").read_text(encoding="utf-8")

    assert sprint["development_status"]["epic-1"] == "in-progress"
    assert sprint["development_status"][story_key] == "done"
    assert "Status: done" in story
    assert "5264583724" in story
    assert "36b583744f7c46dee34bc713a35c978799fa58923ef7db873c1f32dd375785b3" in story
    assert "RETIRED_UNUSED" in story
    assert "Story 1.1" in story
    assert "### Story 1.1: Bootstrap trusted default-branch PR identity controller" in epics


def test_story_1_2_four_phase_readiness_contract_is_graph_bound() -> None:
    key = "1-2-vypolnyat-validation-v-disposable-multi-project-claw-sandbox"
    story = Path(f"docs/implementation/{key}.md").read_text(encoding="utf-8")
    sprint = yaml.safe_load(Path("docs/implementation/sprint-status.yaml").read_text(encoding="utf-8"))
    graph = load_graph(Path("architecture"))

    assert sprint["development_status"][key] == "in-progress"
    for token in (
        "TOFU_SANDBOX_CONTROLLER_INSTALL",
        "Phase B — minimal probe PR",
        "Phase C1 — immutable evidence-proposal PR",
        "Phase C2 — evidence-admission PR",
        "phase-c1-evidence-proposal-v1",
        "/var/lib/mee-controller",
        "/usr/local/libexec/mee-controller-ledger",
        "claw-engine-runner",
        "ControllerTrustContext",
        "GITHUB_PHASE_C1_MERGE_COMMIT_COMMITTER_DATE",
        "phase_policy_cutoff_api_payload_sha256",
        "phase_b_completed_at <= phase_policy_cutoff == phase_c1_merge_committer_at <= phase_c2_controller_verification_completed_at",
        "scripts/write_bootstrap_nonce_consumption.py",
        "scripts/verify_bootstrap_nonce_consumption.py",
        "schemas/bootstrap-nonce-consumption-v1.schema.json",
        "RETIRED_UNUSED",
        "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8",
    ):
        assert token in story
    assert "--policy-cutoff" not in story
    assert "--trusted-policy-cutoff" not in story

    governed_text = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in (
            f"docs/implementation/{key}.md",
            "docs/planning/epics.md",
            "handoff.md",
        )
    )
    assert "Story 1.1 pending" not in governed_text
    assert "Story 1.2 consumes PR24 nonce" not in governed_text
    assert "Story 1.2 consumes PR #24 nonce" not in governed_text

    binding = next(
        item for item in graph.artifact_bindings
        if item.path == f"docs/implementation/{key}.md"
    )
    assert binding.node_id == "document:story-1-2-disposable-claw-sandbox"
    authority = graph.node(binding.node_id)
    assert authority.active and authority.owner == "ci" and authority.requirements
    assert graph.has_edge(binding.node_id, "validated_by", "test:graph-repository-manifests")


def test_vendored_tooling_exclusions_are_exact_and_inactively_authorized() -> None:
    graph = load_graph(Path("architecture"))
    vendored = [
        item
        for item in graph.inventory_exclusions
        if item.path_class.value == "VENDORED_TOOLING"
    ]

    assert len(vendored) == 403
    assert all(item.reason_code.value == "VENDORED_TOOLING" for item in vendored)
    assert {item.authority_node_id for item in vendored} == {
        "artifact:vendored-agent-tooling"
    }
    authority = graph.node("artifact:vendored-agent-tooling")
    assert not authority.active


def test_unknown_tracked_path_blocks_even_when_a_caller_binds_it() -> None:
    authority = GraphNode(
        "module:unknown-owner", "SourceModule", "architecture", Lifecycle.IMPLEMENTED
    )
    artifact = RepositoryArtifact(
        "future_unknown/component.wasm",
        _classify_repository_path("future_unknown/component.wasm"),
    )
    graph = _inventory_graph(
        artifact,
        authority=authority,
        binding=ArtifactBinding(artifact.path, authority.id, artifact.path_class),
    )

    assert "REPOSITORY_PATH_CLASS_UNKNOWN" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_executable_workflow_and_deployment_classes_are_never_excluded() -> None:
    graph = load_graph(Path("architecture"))
    forbidden = {
        "RUNTIME_SOURCE",
        "EXECUTION_SOURCE",
        "TEST_SOURCE",
        "TOOL_SOURCE",
        "GO_SOURCE",
        "WORKFLOW",
        "DEPLOYMENT_ENTRYPOINT",
        "BUILD_PACKAGING",
        "COMPOSE",
        "POWERSHELL",
        "SHELL_SCRIPT",
        "BATCH_SCRIPT",
        "K8S_MANIFEST",
        "UNKNOWN_TRACKED",
    }

    assert not [
        item.path for item in graph.inventory_exclusions if item.path_class.value in forbidden
    ]


def test_active_source_authorities_do_not_reach_forbidden_execution_modules() -> None:
    graph = load_graph(Path("architecture"))
    diagnostics = check_graph(graph, Phase.PRECOMMIT)
    assert "ACTIVE_SOURCE_REACHES_FORBIDDEN_MODULE" not in {
        item.code for item in diagnostics
    }
    assert not any(
        item.path.startswith(("multi_exchange_engine/", "src/multi_exchange_engine/"))
        for item in graph.artifact_bindings
    )


def test_combined_evidence_and_supersedes_lineage_rejects_cross_relation_cycle() -> None:
    first = GraphNode("evidence:first", "Evidence", "ci", Lifecycle.DECLARED)
    second = GraphNode("evidence:second", "Evidence", "ci", Lifecycle.DECLARED)
    graph = ArchitectureGraph(
        (first, second),
        (
            GraphEdge(first.id, second.id, "derived_from"),
            GraphEdge(second.id, first.id, "supersedes"),
        ),
    )

    assert "PROVENANCE_LINEAGE_CYCLE" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_staged_six_manifest_git_repo_cannot_self_attest_phase_trust(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "forged"
    architecture = repository / "architecture"
    architecture.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "remote",
            "add",
            "origin",
            "https://github.com/Dimkox/multi-exchange-engine.git",
        ],
        check=True,
    )
    for index, name in enumerate(
        (
            "requirements.yaml",
            "architecture.yaml",
            "runtime.yaml",
            "data-contracts.yaml",
            "strategies.yaml",
            "release.yaml",
        )
    ):
        document: dict[str, object] = {"manifest_version": 2}
        if index == 0:
            document["phase_policy_times"] = {"merge": "2030-01-01T00:00:00Z"}
        (architecture / name).write_text(
            yaml.safe_dump(document, sort_keys=False), encoding="utf-8"
        )
    subprocess.run(["git", "-C", str(repository), "add", "architecture"], check=True)

    graph = load_graph(architecture)

    assert not graph.policy_times_trusted
    assert "PHASE_POLICY_TIME_TRUST_MISSING" in {
        item.code for item in check_graph(graph, Phase.MERGE)
    }


def test_unscoped_cross_domain_mega_hub_cannot_prove_requirements() -> None:
    data = GraphNode(
        "requirement:DATA-001",
        "Requirement",
        "data",
        Lifecycle.DECLARED,
        requirement_id="DATA-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    ci = GraphNode(
        "requirement:CI-001",
        "Requirement",
        "ci",
        Lifecycle.DECLARED,
        requirement_id="CI-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    hub = GraphNode(
        "contract:mega-hub",
        "Contract",
        "architecture",
        Lifecycle.IMPLEMENTED,
        requirements=("CI-001", "DATA-001"),
    )
    graph = ArchitectureGraph(
        (data, ci, hub),
        (
            GraphEdge(data.id, hub.id, "specified_by"),
            GraphEdge(ci.id, hub.id, "specified_by"),
        ),
    )

    codes = {item.code for item in check_graph(graph, Phase.PRECOMMIT)}
    assert "PROOF_EDGE_SCOPE_MISSING" in codes
    assert "PROOF_CRITICAL_SCOPE_INVALID" in codes


def test_manifest_v2_rejects_list_valued_proof_scope(tmp_path: Path) -> None:
    manifest = {
        "manifest_version": 2,
        "nodes": [
            {
                "id": "requirement:GRAPH-001",
                "kind": "Requirement",
                "owner": "architecture",
                "lifecycle": "DECLARED",
                "requirement_id": "GRAPH-001",
                "requirement_class": "NON_PRODUCT",
                "approval": "owner-approved",
            },
            {
                "id": "contract:graph-001",
                "kind": "Contract",
                "owner": "architecture",
                "lifecycle": "IMPLEMENTED",
                "requirements": ["GRAPH-001"],
            },
        ],
        "edges": [
            {
                "from": "requirement:GRAPH-001",
                "to": "contract:graph-001",
                "kind": "specified_by",
                "proof_for": ["GRAPH-001"],
            }
        ],
    }
    (tmp_path / "architecture.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
    )

    with pytest.raises(GraphLoadError, match="proof_for must be one"):
        load_graph(tmp_path, allow_single_file_fixture=True)


def test_cross_family_critical_hub_is_rejected_even_with_scoped_edges() -> None:
    data = GraphNode(
        "requirement:DATA-001",
        "Requirement",
        "data",
        Lifecycle.DECLARED,
        requirement_id="DATA-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    ci = GraphNode(
        "requirement:CI-001",
        "Requirement",
        "ci",
        Lifecycle.DECLARED,
        requirement_id="CI-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    hub = GraphNode(
        "contract:cross-family",
        "Contract",
        "data",
        Lifecycle.IMPLEMENTED,
        requirements=("CI-001", "DATA-001"),
    )
    graph = ArchitectureGraph(
        (data, ci, hub),
        (
            GraphEdge(data.id, hub.id, "specified_by", "DATA-001"),
            GraphEdge(ci.id, hub.id, "specified_by", "CI-001"),
        ),
    )

    assert "PROOF_CRITICAL_SCOPE_INVALID" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_shared_source_module_cannot_splice_requirement_scopes() -> None:
    data_requirement = GraphNode(
        "requirement:DATA-001",
        "Requirement",
        "data",
        Lifecycle.DECLARED,
        requirement_id="DATA-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    ci_requirement = GraphNode(
        "requirement:CI-001",
        "Requirement",
        "ci",
        Lifecycle.DECLARED,
        requirement_id="CI-001",
        requirement_class="NON_PRODUCT",
        approval="owner-approved",
    )
    data = GraphNode(
        "contract:data",
        "Contract",
        "data",
        Lifecycle.IMPLEMENTED,
        requirements=("DATA-001",),
    )
    ci = GraphNode(
        "dataflow:ci",
        "DataFlow",
        "ci",
        Lifecycle.IMPLEMENTED,
        requirements=("CI-001",),
    )
    shared = GraphNode(
        "module:shared",
        "SourceModule",
        "architecture",
        Lifecycle.IMPLEMENTED,
        requirements=("CI-001", "DATA-001"),
        shared_proof=True,
    )
    graph = ArchitectureGraph(
        (data_requirement, ci_requirement, data, shared, ci),
        (
            GraphEdge(data.id, shared.id, "implements", "DATA-001"),
            GraphEdge(shared.id, ci.id, "produces", "CI-001"),
        ),
    )

    assert "PROOF_SHARED_SOURCE_INVALID" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_active_authority_static_import_reachability_blocks_execution_module() -> None:
    public = GraphNode(
        "runtime:contracts",
        "SourceModule",
        "contracts",
        Lifecycle.IMPLEMENTED,
        profile="contracts",
    )
    execution = GraphNode(
        "artifact:stage-a-execution",
        "Artifact",
        "execution",
        Lifecycle.IMPLEMENTED,
        active=False,
        profile="execution",
        classifications=(Classification.QUARANTINED,),
    )
    safe = RepositoryArtifact(
        "multi_exchange_engine/contracts.py",
        PathClass.RUNTIME_SOURCE,
        module_name="multi_exchange_engine.contracts",
        imports=("multi_exchange_engine.domain.execution",),
    )
    forbidden = RepositoryArtifact(
        "multi_exchange_engine/domain/execution.py",
        PathClass.EXECUTION_SOURCE,
        module_name="multi_exchange_engine.domain.execution",
        forbidden_symbols=("order",),
    )
    graph = ArchitectureGraph(
        (public, execution),
        repository_artifacts=(safe, forbidden),
        artifact_bindings=(
            ArtifactBinding(safe.path, public.id, safe.path_class),
            ArtifactBinding(forbidden.path, execution.id, forbidden.path_class),
        ),
    )

    assert "ACTIVE_SOURCE_REACHES_FORBIDDEN_MODULE" in {
        item.code for item in check_graph(graph, Phase.PRECOMMIT)
    }


def test_repository_uses_requirement_scoped_proof_lanes_without_cross_domain_hub() -> None:
    graph = load_graph(Path("architecture"))
    diagnostics = check_graph(graph, Phase.PRECOMMIT)
    codes = {item.code for item in diagnostics}
    graph_checker = graph.node("module:graph-checker")

    assert not {
        "PROOF_EDGE_SCOPE_MISSING",
        "PROOF_CRITICAL_SCOPE_INVALID",
        "PROOF_NODE_PROJECTION_MISMATCH",
        "PROOF_SHARED_SOURCE_INVALID",
        "REQUIREMENT_FORWARD_PATH_MISSING",
        "REQUIREMENT_FORWARD_PATH_INCOMPLETE",
        "PRODUCT_TRACEABILITY_INCOMPLETE",
    } & codes
    assert not {
        requirement
        for requirement in graph_checker.requirements
        if requirement.startswith(("PROD-", "DATA-", "STRAT-"))
    }


def test_m0_repository_loader_never_self_grants_controller_trust() -> None:
    graph = load_graph(Path("architecture"))

    assert not graph.policy_times_trusted
    assert "PHASE_POLICY_TIME_TRUST_MISSING" in {
        item.code for item in check_graph(graph, Phase.MERGE)
    }
