"""Immutable values used by the deterministic architecture graph checker."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum


class Phase(StrEnum):
    PRECOMMIT = "precommit"
    MERGE = "merge"
    RELEASE = "release"
    PROMOTION = "promotion"
    DEPLOYMENT = "deployment"


class NodeKind(StrEnum):
    ACTOR = "Actor"
    OUTCOME = "Outcome"
    HYPOTHESIS = "Hypothesis"
    METRIC = "Metric"
    REQUIREMENT = "Requirement"
    ACCEPTANCE_CRITERION = "AcceptanceCriterion"
    KILL_CRITERION = "KillCriterion"
    APPROVAL = "Approval"
    ADR = "ADR"
    CONTRACT = "Contract"
    SOURCE_MODULE = "SourceModule"
    DATA_FLOW = "DataFlow"
    CONFIGURATION = "Configuration"
    MIGRATION = "Migration"
    TEST_OR_EVAL = "TestOrEval"
    CLAW_GATE = "ClawGate"
    ARTIFACT = "Artifact"
    DEPLOYMENT = "Deployment"
    TELEMETRY = "Telemetry"
    EVIDENCE = "Evidence"
    ROLLBACK = "Rollback"
    CONFLICT = "Conflict"


class RequirementClass(StrEnum):
    PRODUCT = "PRODUCT"
    NON_PRODUCT = "NON_PRODUCT"


class PathClass(StrEnum):
    RUNTIME_SOURCE = "RUNTIME_SOURCE"
    EXECUTION_SOURCE = "EXECUTION_SOURCE"
    TEST_SOURCE = "TEST_SOURCE"
    TOOL_SOURCE = "TOOL_SOURCE"
    GO_SOURCE = "GO_SOURCE"
    WORKFLOW = "WORKFLOW"
    DEPLOYMENT_ENTRYPOINT = "DEPLOYMENT_ENTRYPOINT"
    BUILD_PACKAGING = "BUILD_PACKAGING"
    CONFIGURATION = "CONFIGURATION"
    DOCUMENTATION = "DOCUMENTATION"
    SCHEMA_MANIFEST = "SCHEMA_MANIFEST"
    MIGRATION = "MIGRATION"
    FIXTURE_DATA = "FIXTURE_DATA"
    COMPOSE = "COMPOSE"
    POWERSHELL = "POWERSHELL"
    SHELL_SCRIPT = "SHELL_SCRIPT"
    BATCH_SCRIPT = "BATCH_SCRIPT"
    K8S_MANIFEST = "K8S_MANIFEST"
    VENDORED_TOOLING = "VENDORED_TOOLING"
    UNKNOWN_TRACKED = "UNKNOWN_TRACKED"
    RESEARCH = "RESEARCH"


class InventoryExclusionReason(StrEnum):
    RESEARCH_ONLY = "RESEARCH_ONLY"
    ARCHIVED_REFERENCE = "ARCHIVED_REFERENCE"
    VENDORED_TOOLING = "VENDORED_TOOLING"


class Lifecycle(StrEnum):
    DECLARED = "DECLARED"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"
    REALIZED = "REALIZED"
    RETIRED = "RETIRED"


class Classification(StrEnum):
    MIGRATING = "MIGRATING"
    QUARANTINED = "QUARANTINED"
    TEST_ONLY_EXECUTABLE_SPEC = "TEST_ONLY_EXECUTABLE_SPEC"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    node_id: str | None
    path: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class GraphNode:
    id: str
    kind: NodeKind
    owner: str
    lifecycle: Lifecycle
    active: bool = True
    requirements: tuple[str, ...] = ()
    requirement_id: str | None = None
    requirement_class: RequirementClass | None = None
    approval: str | None = None
    classifications: tuple[Classification, ...] = ()
    canonical_for: str | None = None
    replacement: str | None = None
    expiry_utc: str | None = None
    removal_gate: str | None = None
    rollback_node: str | None = None
    expiry_conflict: str | None = None
    required_from: Phase | None = None
    required_lifecycle: Lifecycle | None = None
    profile: str | None = None
    capabilities: tuple[str, ...] = ()
    shared_proof: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", NodeKind(self.kind))
        if self.requirement_class is not None:
            object.__setattr__(
                self,
                "requirement_class",
                RequirementClass(self.requirement_class),
            )
        if self.required_from is not None and self.required_lifecycle is None:
            object.__setattr__(self, "required_lifecycle", Lifecycle.IMPLEMENTED)
        if self.required_from is None and self.required_lifecycle is not None:
            raise ValueError("required_lifecycle needs required_from")


@dataclass(frozen=True, slots=True)
class GraphEdge:
    from_id: str
    to_id: str
    kind: str
    proof_for: str | None = None
    non_proof_reason: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeDependency:
    from_id: str
    to_id: str


@dataclass(frozen=True, slots=True)
class ReceiptRequirement:
    node_id: str
    required_from: Phase
    evidence_type: str
    status: str
    content_hash: str | None = None
    source_sha: str | None = None
    producer: str | None = None
    produced_at: str | None = None
    verifier: str | None = None
    verification_hash: str | None = None
    verified_at: str | None = None


@dataclass(frozen=True, slots=True)
class VerifiedReceiptRegistryEntry:
    node_id: str
    content_hash: str
    source_sha: str
    producer: str
    produced_at: str
    verifier: str
    verification_hash: str
    verified_at: str


@dataclass(frozen=True, slots=True)
class ReceiptValidationContext:
    evidence_cutoff_utc: str
    expected_source_sha: str
    registry: tuple[VerifiedReceiptRegistryEntry, ...]


@dataclass(frozen=True, slots=True)
class ControllerTrustContext:
    """Closed future Phase C2 trust input; Phase A never admits an instance."""
    repository: str
    controller_sha: str
    controller_tree: str
    workflow_path: str
    workflow_blob_sha: str
    source_sha: str
    source_tree: str
    phase_b_validation_receipt_sha256: str
    phase_b_cleanup_receipt_sha256: str
    phase_b_self_validation_receipt_sha256: str
    phase_policy_cutoff: str
    status: str


@dataclass(frozen=True, slots=True)
class ArtifactBinding:
    path: str
    node_id: str
    path_class: PathClass | None = None


@dataclass(frozen=True, slots=True)
class RepositoryArtifact:
    path: str
    path_class: PathClass
    module_name: str | None = None
    imports: tuple[str, ...] = ()
    forbidden_symbols: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RepositoryInventoryExclusion:
    path: str
    reason_code: InventoryExclusionReason
    authority_node_id: str | None = None
    path_class: PathClass | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_code", InventoryExclusionReason(self.reason_code))


@dataclass(frozen=True, slots=True)
class ArchitectureGraph:
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...] = ()
    runtime_dependencies: tuple[RuntimeDependency, ...] = ()
    receipts: tuple[ReceiptRequirement, ...] = ()
    schema_errors: tuple[str, ...] = ()
    phase_policy_times: tuple[tuple[Phase, str], ...] = ()
    policy_times_trusted: bool = False
    repository_artifacts: tuple[RepositoryArtifact, ...] = ()
    artifact_bindings: tuple[ArtifactBinding, ...] = ()
    inventory_exclusions: tuple[RepositoryInventoryExclusion, ...] = ()

    def node(self, node_id: str) -> GraphNode:
        for node in self.nodes:
            if node.id == node_id:
                return node
        raise KeyError(node_id)

    def has_edge(self, from_id: str, kind: str, to_id: str) -> bool:
        return any(
            edge.from_id == from_id and edge.kind == kind and edge.to_id == to_id
            for edge in self.edges
        )

    def policy_time(self, phase: Phase) -> str | None:
        return dict(self.phase_policy_times).get(phase)

    def with_node(
        self,
        node_id: str,
        *,
        kind: str,
        owner: str,
        lifecycle: Lifecycle = Lifecycle.IMPLEMENTED,
        active: bool = True,
        requirements: tuple[str, ...] = (),
        requirement_id: str | None = None,
        requirement_class: RequirementClass | None = None,
        approval: str | None = None,
        classifications: tuple[Classification, ...] = (),
        canonical_for: str | None = None,
        replacement: str | None = None,
        expiry_utc: str | None = None,
        removal_gate: str | None = None,
        rollback_node: str | None = None,
        expiry_conflict: str | None = None,
        required_from: Phase | None = None,
        required_lifecycle: Lifecycle | None = None,
        profile: str | None = None,
        capabilities: tuple[str, ...] = (),
        shared_proof: bool = False,
    ) -> ArchitectureGraph:
        node = GraphNode(
            id=node_id,
            kind=kind,
            owner=owner,
            lifecycle=Lifecycle(lifecycle),
            active=active,
            requirements=tuple(requirements),
            requirement_id=requirement_id,
            requirement_class=requirement_class,
            approval=approval,
            classifications=tuple(classifications),
            canonical_for=canonical_for,
            replacement=replacement,
            expiry_utc=expiry_utc,
            removal_gate=removal_gate,
            rollback_node=rollback_node,
            expiry_conflict=expiry_conflict,
            required_from=required_from,
            required_lifecycle=required_lifecycle,
            profile=profile,
            capabilities=tuple(capabilities),
            shared_proof=shared_proof,
        )
        retained = tuple(item for item in self.nodes if item.id != node_id)
        return replace(self, nodes=retained + (node,))
