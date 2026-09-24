"""Deterministic policy checks over an immutable architecture graph."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
import re

from .model import (
    ArchitectureGraph,
    Classification,
    Diagnostic,
    GraphNode,
    InventoryExclusionReason,
    Lifecycle,
    NodeKind,
    PathClass,
    Phase,
    ReceiptValidationContext,
    RequirementClass,
)


_PHASE_ORDER = {phase: index for index, phase in enumerate(Phase)}
_TRACEABILITY_EXEMPT_KINDS = {NodeKind.REQUIREMENT, NodeKind.CONFLICT}
_NON_ACTIVE_LIFECYCLES = {Lifecycle.RETIRED}
_PROOF_LIFECYCLES = frozenset(
    {Lifecycle.DECLARED, Lifecycle.IMPLEMENTED, Lifecycle.VERIFIED, Lifecycle.REALIZED}
)
_NON_PRODUCT_FORWARD_PATH_STAGES = (
    frozenset({NodeKind.CONTRACT}),
    frozenset({NodeKind.SOURCE_MODULE}),
    frozenset({NodeKind.DATA_FLOW}),
    frozenset({NodeKind.TEST_OR_EVAL}),
    frozenset({NodeKind.CLAW_GATE}),
    frozenset({NodeKind.ARTIFACT}),
    frozenset({NodeKind.EVIDENCE}),
    frozenset({NodeKind.ROLLBACK}),
)
_PRODUCT_FORWARD_PATH_STAGES = (
    frozenset({NodeKind.ACCEPTANCE_CRITERION, NodeKind.KILL_CRITERION}),
    frozenset({NodeKind.METRIC}),
    frozenset({NodeKind.CONTRACT}),
    frozenset({NodeKind.SOURCE_MODULE}),
    frozenset({NodeKind.DATA_FLOW}),
    frozenset({NodeKind.TEST_OR_EVAL}),
    frozenset({NodeKind.CLAW_GATE}),
    frozenset({NodeKind.ARTIFACT}),
    frozenset({NodeKind.EVIDENCE}),
    frozenset({NodeKind.ROLLBACK}),
)
_RUNTIME_PROFILE_CAPABILITIES = {
    (NodeKind.SOURCE_MODULE, "contracts"): frozenset(),
    (NodeKind.SOURCE_MODULE, "public-capture"): frozenset(
        {"public-venue", "capture-write"}
    ),
    (NodeKind.SOURCE_MODULE, "readonly-analyzer"): frozenset(
        {"capture-read", "analysis-write"}
    ),
    (NodeKind.SOURCE_MODULE, "mezo-protocol"): frozenset(),
    (NodeKind.SOURCE_MODULE, "evidence-report"): frozenset(
        {"capture-read", "analysis-write"}
    ),
    (NodeKind.SOURCE_MODULE, "capture-service"): frozenset(
        {"public-venue", "capture-write"}
    ),
    (NodeKind.SOURCE_MODULE, "report-service"): frozenset(
        {"capture-read", "analysis-write"}
    ),
    (NodeKind.SOURCE_MODULE, "mezo-gateway"): frozenset(
        {
            "artifact-read",
            "ledger-write",
            "payment-verify",
            "payment-settle",
            "report-request",
            "rpc-read",
        }
    ),
    (NodeKind.SOURCE_MODULE, "mezo-web"): frozenset(
        {"public-api-read", "user-wallet-request"}
    ),
    (NodeKind.SOURCE_MODULE, "local-demo"): frozenset(),
    (NodeKind.SOURCE_MODULE, "acceptance"): frozenset({"evidence-read"}),
    (NodeKind.SOURCE_MODULE, "liqvera-factory"): frozenset(),
    (NodeKind.DEPLOYMENT, "liqvera-deploy"): frozenset(),
    (NodeKind.SOURCE_MODULE, "go-test-only"): frozenset(),
    (NodeKind.ARTIFACT, "execution"): frozenset(),
}
_FORBIDDEN_CAPABILITIES = frozenset(
    {
        "signer",
        "wallet",
        "private",
        "account",
        "order",
        "cancel",
        "transfer",
        "withdrawal",
        "n8n",
        "live",
        "deploy",
    }
)
_KNOWN_CAPABILITIES = frozenset(
    {
        "public-venue",
        "capture-write",
        "capture-read",
        "analysis-write",
        "artifact-read",
        "ledger-write",
        "payment-verify",
        "payment-settle",
        "report-request",
        "rpc-read",
        "public-api-read",
        "user-wallet-request",
        "evidence-read",
        *_FORBIDDEN_CAPABILITIES,
    }
)
_ALLOWED_RUNTIME_DEPENDENCIES = frozenset(
    {
        ("public-capture", "contracts"),
        ("readonly-analyzer", "contracts"),
        ("evidence-report", "contracts"),
        ("evidence-report", "readonly-analyzer"),
        ("evidence-report", "public-capture"),
        ("capture-service", "contracts"),
        ("capture-service", "public-capture"),
        ("report-service", "evidence-report"),
        ("mezo-gateway", "mezo-protocol"),
        ("mezo-web", "mezo-protocol"),
    }
)
_MIGRATABLE_KINDS = frozenset(
    {
        NodeKind.ARTIFACT,
        NodeKind.CONFIGURATION,
        NodeKind.CONTRACT,
        NodeKind.DATA_FLOW,
        NodeKind.MIGRATION,
        NodeKind.SOURCE_MODULE,
    }
)
_EDGE_KIND_MATRIX = {
    "serves": frozenset({(NodeKind.OUTCOME, NodeKind.REQUIREMENT)}),
    "intends": frozenset({(NodeKind.ACTOR, NodeKind.OUTCOME)}),
    "measured_by": frozenset(
        {
            (NodeKind.ACCEPTANCE_CRITERION, NodeKind.METRIC),
            (NodeKind.KILL_CRITERION, NodeKind.METRIC),
            (NodeKind.OUTCOME, NodeKind.METRIC),
        }
    ),
    "falsified_by": frozenset({(NodeKind.HYPOTHESIS, NodeKind.TEST_OR_EVAL)}),
    "approved_by": frozenset({(NodeKind.REQUIREMENT, NodeKind.APPROVAL)}),
    "specified_by": frozenset({
        (NodeKind.REQUIREMENT, NodeKind.ACCEPTANCE_CRITERION),
        (NodeKind.REQUIREMENT, NodeKind.KILL_CRITERION),
        (NodeKind.REQUIREMENT, NodeKind.ADR),
        (NodeKind.REQUIREMENT, NodeKind.CLAW_GATE),
        (NodeKind.REQUIREMENT, NodeKind.CONFIGURATION),
        (NodeKind.REQUIREMENT, NodeKind.CONTRACT),
        (NodeKind.REQUIREMENT, NodeKind.DEPLOYMENT),
        (NodeKind.REQUIREMENT, NodeKind.METRIC),
        (NodeKind.REQUIREMENT, NodeKind.SOURCE_MODULE),
        (NodeKind.METRIC, NodeKind.CONTRACT),
        (NodeKind.CONFIGURATION, NodeKind.CONTRACT),
    }),
    "owned_by": frozenset(
        (kind, NodeKind.ACTOR) for kind in NodeKind if kind is not NodeKind.ACTOR
    ),
    "implements": frozenset(
        {
            (NodeKind.CONTRACT, NodeKind.CONFIGURATION),
            (NodeKind.CONTRACT, NodeKind.SOURCE_MODULE),
        }
    ),
    "consumes": frozenset(
        {
            (NodeKind.SOURCE_MODULE, NodeKind.CONFIGURATION),
            (NodeKind.SOURCE_MODULE, NodeKind.CONTRACT),
            (NodeKind.SOURCE_MODULE, NodeKind.DATA_FLOW),
        }
    ),
    "produces": frozenset(
        {
            (NodeKind.SOURCE_MODULE, NodeKind.ARTIFACT),
            (NodeKind.SOURCE_MODULE, NodeKind.DATA_FLOW),
            (NodeKind.SOURCE_MODULE, NodeKind.EVIDENCE),
        }
    ),
    "validated_by": frozenset({
        (NodeKind.ADR, NodeKind.TEST_OR_EVAL),
        (NodeKind.CONFIGURATION, NodeKind.TEST_OR_EVAL),
        (NodeKind.CONTRACT, NodeKind.TEST_OR_EVAL),
        (NodeKind.DATA_FLOW, NodeKind.TEST_OR_EVAL),
        (NodeKind.DEPLOYMENT, NodeKind.TEST_OR_EVAL),
        (NodeKind.METRIC, NodeKind.TEST_OR_EVAL),
        (NodeKind.SOURCE_MODULE, NodeKind.TEST_OR_EVAL),
    }),
    "gated_by": frozenset(
        {(NodeKind.TEST_OR_EVAL, NodeKind.CLAW_GATE)}
        | {(kind, NodeKind.CLAW_GATE) for kind in _MIGRATABLE_KINDS}
    ),
    "packaged_in": frozenset({(NodeKind.CLAW_GATE, NodeKind.ARTIFACT)}),
    "deployed_by": frozenset({(NodeKind.ARTIFACT, NodeKind.DEPLOYMENT)}),
    "observed_by": frozenset(
        {
            (NodeKind.DEPLOYMENT, NodeKind.TELEMETRY),
            (NodeKind.SOURCE_MODULE, NodeKind.TELEMETRY),
        }
    ),
    "evidenced_by": frozenset(
        {
            (NodeKind.ARTIFACT, NodeKind.EVIDENCE),
            (NodeKind.TELEMETRY, NodeKind.EVIDENCE),
        }
    ),
    "rolled_back_by": frozenset(
        {
            (NodeKind.DEPLOYMENT, NodeKind.ROLLBACK),
            (NodeKind.EVIDENCE, NodeKind.ROLLBACK),
            *((kind, NodeKind.ROLLBACK) for kind in _MIGRATABLE_KINDS),
        }
    ),
    "supersedes": frozenset(
        {(kind, kind) for kind in _MIGRATABLE_KINDS}
        | {(NodeKind.EVIDENCE, NodeKind.EVIDENCE)}
    ),
    "conflicts_with": frozenset(
        {
            (NodeKind.REQUIREMENT, NodeKind.ARTIFACT),
            (NodeKind.REQUIREMENT, NodeKind.CONFLICT),
            *((kind, NodeKind.CONFLICT) for kind in _MIGRATABLE_KINDS),
        }
    ),
    "resolved_by": frozenset(
        {
            (NodeKind.CONFLICT, NodeKind.CONFIGURATION),
            (NodeKind.CONFLICT, NodeKind.MIGRATION),
        }
    ),
    "derived_from": frozenset({(NodeKind.EVIDENCE, NodeKind.EVIDENCE)}),
}
_NON_PROVENANCE_EDGE_KINDS = frozenset(
    {"conflicts_with", "falsified_by", "resolved_by"}
)
_LINEAGE_EDGE_KINDS = frozenset({"derived_from", "supersedes"})
_NON_PROOF_EDGE_KINDS = frozenset(
    {*_NON_PROVENANCE_EDGE_KINDS, *_LINEAGE_EDGE_KINDS}
)
_PROOF_EDGE_KINDS = frozenset(set(_EDGE_KIND_MATRIX) - _NON_PROOF_EDGE_KINDS)
_PROOF_CRITICAL_KINDS = frozenset(
    {
        NodeKind.ACCEPTANCE_CRITERION,
        NodeKind.KILL_CRITERION,
        NodeKind.METRIC,
        NodeKind.CONTRACT,
        NodeKind.DATA_FLOW,
        NodeKind.TEST_OR_EVAL,
        NodeKind.CLAW_GATE,
        NodeKind.EVIDENCE,
        NodeKind.ROLLBACK,
    }
)
_NON_PROOF_REASON = "AGGREGATE_SEMANTIC_CONTEXT"
_RECEIPT_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_RECEIPT_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_RECEIPT_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REQUIREMENT_STABLE_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]{3}$")
_NON_EXCLUDABLE_PATH_CLASSES = frozenset(
    {
        PathClass.RUNTIME_SOURCE,
        PathClass.EXECUTION_SOURCE,
        PathClass.TEST_SOURCE,
        PathClass.TOOL_SOURCE,
        PathClass.GO_SOURCE,
        PathClass.WORKFLOW,
        PathClass.DEPLOYMENT_ENTRYPOINT,
        PathClass.BUILD_PACKAGING,
        PathClass.COMPOSE,
        PathClass.POWERSHELL,
        PathClass.SHELL_SCRIPT,
        PathClass.BATCH_SCRIPT,
        PathClass.K8S_MANIFEST,
        PathClass.UNKNOWN_TRACKED,
    }
)
_LIFECYCLE_MATURITY = {
    Lifecycle.DECLARED: 0,
    Lifecycle.IMPLEMENTED: 1,
    Lifecycle.VERIFIED: 2,
    Lifecycle.REALIZED: 3,
    Lifecycle.RETIRED: -1,
}


def check_graph(
    graph: ArchitectureGraph,
    phase: Phase,
    receipt_context: ReceiptValidationContext | None = None,
) -> tuple[Diagnostic, ...]:
    """Return sorted, immutable graph-policy diagnostics for ``phase``."""
    diagnostics = [
        *_check_schema(graph),
        *_check_edges(graph),
        *_check_proof_scopes(graph),
        *_check_owners(graph),
        *_check_requirements(graph),
    ]
    diagnostics.extend(_check_lifecycle(graph, phase))
    diagnostics.extend(_check_traceability(graph))
    diagnostics.extend(_check_requirement_metadata(graph))
    diagnostics.extend(_check_requirement_forward_paths(graph))
    diagnostics.extend(_check_runtime_capabilities(graph))
    diagnostics.extend(_check_runtime_dag(graph))
    diagnostics.extend(_check_evidence_derivation_dag(graph))
    diagnostics.extend(_check_semantic_supersedes(graph))
    diagnostics.extend(_check_phase_policy_time_context(graph, phase))
    diagnostics.extend(_check_migrations(graph, phase))
    diagnostics.extend(_check_receipts(graph, phase, receipt_context))
    diagnostics.extend(_check_repository_inventory(graph))
    diagnostics.extend(_check_active_source_import_reachability(graph))
    return tuple(sorted(diagnostics, key=lambda item: (item.code, item.path, item.node_id or "")))


def _diagnostic(
    code: str,
    node_id: str | None,
    path: tuple[str, ...],
    requirement_ids: tuple[str, ...] = (),
    message: str = "",
) -> Diagnostic:
    return Diagnostic(code, node_id, path, tuple(sorted(requirement_ids)), message)


def _check_schema(graph: ArchitectureGraph) -> list[Diagnostic]:
    diagnostics = [
        _diagnostic("SCHEMA_SHAPE", None, (), message=error) for error in graph.schema_errors
    ]
    nodes = {node.id for node in graph.nodes}
    for edge in graph.edges:
        if edge.from_id not in nodes or edge.to_id not in nodes:
            diagnostics.append(
                _diagnostic(
                    "SCHEMA_DANGLING_EDGE",
                    None,
                    (edge.from_id, edge.to_id),
                    message="graph edge references an unknown node",
                )
            )
    for edge in graph.runtime_dependencies:
        if edge.from_id not in nodes or edge.to_id not in nodes:
            diagnostics.append(
                _diagnostic(
                    "SCHEMA_DANGLING_RUNTIME_EDGE",
                    None,
                    (edge.from_id, edge.to_id),
                    message="runtime dependency references an unknown node",
                )
            )
    for receipt in graph.receipts:
        if receipt.node_id not in nodes:
            diagnostics.append(
                _diagnostic(
                    "SCHEMA_DANGLING_RECEIPT",
                    receipt.node_id,
                    (receipt.node_id,),
                    message="receipt references an unknown node",
                )
            )
    return diagnostics


def _check_repository_inventory(graph: ArchitectureGraph) -> list[Diagnostic]:
    tracked = {artifact.path: artifact for artifact in graph.repository_artifacts}
    nodes = {node.id: node for node in graph.nodes}
    bindings: dict[str, list[str]] = defaultdict(list)
    exclusions: dict[str, list[str]] = defaultdict(list)
    diagnostics: list[Diagnostic] = []
    for artifact in graph.repository_artifacts:
        if artifact.path_class is PathClass.UNKNOWN_TRACKED:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_PATH_CLASS_UNKNOWN",
                    None,
                    (artifact.path,),
                    message="every tracked path needs an explicit closed classifier rule",
                )
            )
    for binding in graph.artifact_bindings:
        bindings[binding.path].append(binding.node_id)
        artifact = tracked.get(binding.path)
        if artifact is None:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_ARTIFACT_NOT_TRACKED",
                    binding.node_id,
                    (binding.path,),
                    message="manifest binding names an artifact not tracked by Git",
                )
            )
        if binding.node_id not in nodes:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_ARTIFACT_OWNER_UNKNOWN",
                    binding.node_id,
                    (binding.path, binding.node_id),
                    message="manifest binding names an unknown graph node",
                )
            )
        elif artifact is not None and binding.path_class is not artifact.path_class:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_PATH_CLASS_MISMATCH",
                    binding.node_id,
                    (binding.path,),
                    message="binding path_class must equal deterministic classification",
                )
            )
        elif artifact is not None and not _binding_authority_allowed(
            artifact.path_class, nodes[binding.node_id]
        ):
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_BINDING_AUTHORITY_INVALID", binding.node_id,
                    (binding.path, binding.node_id),
                    message="path class is incompatible with node kind/profile/lifecycle authority",
                )
            )
    for exclusion in graph.inventory_exclusions:
        exclusions[exclusion.path].append(exclusion.reason_code.value)
        artifact = tracked.get(exclusion.path)
        authority = nodes.get(exclusion.authority_node_id or "")
        if (
            artifact is None
            or authority is None
            or exclusion.path_class is not artifact.path_class
            or exclusion.reason_code not in set(InventoryExclusionReason)
        ):
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_INVENTORY_EXCLUSION_INVALID",
                    None,
                    (exclusion.path,),
                    message="exclusions require exact class, closed reason code, and known authority",
                )
            )
        elif artifact.path_class in _NON_EXCLUDABLE_PATH_CLASSES:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_INVENTORY_EXCLUSION_FORBIDDEN",
                    exclusion.authority_node_id,
                    (exclusion.path,),
                    message="runtime/workflow/deploy entrypoints cannot be excluded",
                )
            )
        elif not (
            (
                (
                    artifact.path_class is PathClass.RESEARCH
                    and exclusion.reason_code is InventoryExclusionReason.RESEARCH_ONLY
                    and authority.active
                    and authority.kind is NodeKind.ADR
                )
                or (
                    artifact.path_class is PathClass.DOCUMENTATION
                    and exclusion.reason_code
                    is InventoryExclusionReason.ARCHIVED_REFERENCE
                    and authority.active
                    and authority.kind is NodeKind.ADR
                )
                or (
                    artifact.path_class is PathClass.VENDORED_TOOLING
                    and exclusion.reason_code is InventoryExclusionReason.VENDORED_TOOLING
                    and not authority.active
                    and authority.kind is NodeKind.ARTIFACT
                    and Classification.QUARANTINED in authority.classifications
                )
            )
        ):
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_INVENTORY_EXCLUSION_AUTHORITY_INVALID",
                    exclusion.authority_node_id,
                    (exclusion.path,),
                    message="exclusion reason and closed authority must match path class",
                )
            )
    for path in sorted(tracked):
        identities = len(bindings.get(path, ())) + len(exclusions.get(path, ()))
        if identities == 0:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_ARTIFACT_UNDECLARED",
                    None,
                    (path,),
                    message="tracked runtime/source/workflow/config/entrypoint artifact is undeclared",
                )
            )
        elif identities != 1:
            diagnostics.append(
                _diagnostic(
                    "REPOSITORY_ARTIFACT_DECLARATION_DUPLICATE",
                    None,
                    (path,),
                    message="tracked artifact needs exactly one binding or exclusion",
                )
            )
    return diagnostics


def _binding_authority_allowed(path_class: PathClass, node: GraphNode) -> bool:
    if path_class in {
        PathClass.EXECUTION_SOURCE,
        PathClass.POWERSHELL,
    }:
        return (
            node.kind is NodeKind.ARTIFACT
            and node.profile == "execution"
            and not node.active
            and Classification.QUARANTINED in node.classifications
        )
    if path_class is PathClass.DEPLOYMENT_ENTRYPOINT:
        return (
            node.kind is NodeKind.DEPLOYMENT
            and node.active
            and node.profile == "liqvera-deploy"
        ) or (
            node.kind is NodeKind.ARTIFACT
            and node.profile == "execution"
            and not node.active
            and Classification.QUARANTINED in node.classifications
        )
    if path_class is PathClass.RUNTIME_SOURCE:
        return node.kind is NodeKind.SOURCE_MODULE and node.active and node.profile in {
            "contracts",
            "public-capture",
            "readonly-analyzer",
            "mezo-protocol",
            "evidence-report",
            "capture-service",
            "report-service",
            "mezo-gateway",
            "mezo-web",
            "local-demo",
            "acceptance",
            "liqvera-factory",
        }
    if path_class is PathClass.GO_SOURCE:
        return (
            node.kind is NodeKind.SOURCE_MODULE
            and node.profile == "go-test-only"
            and Classification.TEST_ONLY_EXECUTABLE_SPEC in node.classifications
        )
    if path_class is PathClass.TEST_SOURCE:
        return node.kind is NodeKind.TEST_OR_EVAL
    if path_class in {PathClass.WORKFLOW, PathClass.CONFIGURATION}:
        return node.kind is NodeKind.CONFIGURATION and node.active
    if path_class is PathClass.DOCUMENTATION:
        return node.kind is NodeKind.ADR
    if path_class is PathClass.SCHEMA_MANIFEST:
        return node.kind in {NodeKind.CONFIGURATION, NodeKind.CONTRACT}
    if path_class is PathClass.MIGRATION:
        return node.kind is NodeKind.CONTRACT
    if path_class is PathClass.TOOL_SOURCE:
        return node.kind is NodeKind.SOURCE_MODULE
    if path_class is PathClass.BUILD_PACKAGING:
        return node.kind is NodeKind.ARTIFACT
    if path_class is PathClass.FIXTURE_DATA:
        return node.kind in {NodeKind.ARTIFACT, NodeKind.SOURCE_MODULE}
    if path_class in {PathClass.SHELL_SCRIPT, PathClass.BATCH_SCRIPT}:
        return (
            node.kind in {NodeKind.SOURCE_MODULE, NodeKind.TEST_OR_EVAL, NodeKind.CONFIGURATION}
            and node.active
        )
    if path_class is PathClass.K8S_MANIFEST:
        return node.kind in {NodeKind.CONFIGURATION, NodeKind.DEPLOYMENT} and node.active
    if path_class is PathClass.COMPOSE:
        return node.kind is NodeKind.ARTIFACT and node.active
    if path_class is PathClass.VENDORED_TOOLING:
        return False
    if path_class is PathClass.UNKNOWN_TRACKED:
        return False
    return path_class is PathClass.RESEARCH and node.kind is NodeKind.ADR


def _check_active_source_import_reachability(
    graph: ArchitectureGraph,
) -> list[Diagnostic]:
    artifacts = {artifact.path: artifact for artifact in graph.repository_artifacts}
    by_module: dict[str, set[str]] = defaultdict(set)
    for artifact in graph.repository_artifacts:
        if artifact.module_name is not None:
            by_module[artifact.module_name].add(artifact.path)
    owned_paths: dict[str, set[str]] = defaultdict(set)
    for binding in graph.artifact_bindings:
        owned_paths[binding.node_id].add(binding.path)

    diagnostics: list[Diagnostic] = []
    for authority in sorted(graph.nodes, key=lambda item: item.id):
        if not authority.active or authority.kind is not NodeKind.SOURCE_MODULE:
            continue
        pending = sorted(owned_paths.get(authority.id, ()), reverse=True)
        seen: set[str] = set()
        while pending:
            path = pending.pop()
            if path in seen:
                continue
            seen.add(path)
            artifact = artifacts.get(path)
            if artifact is None:
                continue
            if artifact.path_class is PathClass.EXECUTION_SOURCE or artifact.forbidden_symbols:
                diagnostics.append(
                    _diagnostic(
                        "ACTIVE_SOURCE_REACHES_FORBIDDEN_MODULE",
                        authority.id,
                        (authority.id, path, *artifact.forbidden_symbols),
                        authority.requirements,
                        "active source authority reaches execution/private/trading authority",
                    )
                )
                continue
            imported_paths: set[str] = set()
            for imported in artifact.imports:
                parts = imported.split(".")
                for index in range(2, len(parts) + 1):
                    imported_paths.update(by_module.get(".".join(parts[:index]), ()))
            pending.extend(sorted(imported_paths - seen, reverse=True))
    return diagnostics


def _check_edges(graph: ArchitectureGraph) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    diagnostics: list[Diagnostic] = []
    for edge in graph.edges:
        source = nodes.get(edge.from_id)
        target = nodes.get(edge.to_id)
        if source is None or target is None:
            continue
        allowed_pairs = _EDGE_KIND_MATRIX.get(edge.kind)
        if allowed_pairs is None:
            diagnostics.append(
                _diagnostic(
                    "EDGE_KIND_UNKNOWN",
                    edge.from_id,
                    (edge.from_id, edge.to_id),
                    source.requirements,
                    "graph edge kind is not in the closed policy matrix",
                )
            )
        elif (source.kind, target.kind) not in allowed_pairs:
            diagnostics.append(
                _diagnostic(
                    "EDGE_KIND_PAIR_INVALID",
                    edge.from_id,
                    (edge.from_id, edge.to_id),
                    source.requirements,
                    "graph edge kind does not allow this source and target kind pair",
                )
            )
    return diagnostics


def _check_proof_scopes(graph: ArchitectureGraph) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    requirements = {
        node.requirement_id: node
        for node in graph.nodes
        if _is_approved_requirement(node) and node.requirement_id is not None
    }
    incident: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    diagnostics: list[Diagnostic] = []
    for edge in graph.edges:
        if edge.kind not in _PROOF_EDGE_KINDS:
            if edge.proof_for is not None or edge.non_proof_reason is not None:
                diagnostics.append(
                    _diagnostic(
                        "PROOF_EDGE_SCOPE_INVALID",
                        edge.from_id,
                        (edge.from_id, edge.to_id),
                        (edge.proof_for,) if edge.proof_for else (),
                        "negative and lineage relations cannot carry proof scope metadata",
                    )
                )
            continue
        if edge.proof_for is None:
            if edge.non_proof_reason != _NON_PROOF_REASON:
                diagnostics.append(
                    _diagnostic(
                        "PROOF_EDGE_SCOPE_MISSING",
                        edge.from_id,
                        (edge.from_id, edge.to_id),
                        message=(
                            "positive trace edges require one proof_for or the closed "
                            "non-proof marker"
                        ),
                    )
                )
            continue
        if edge.non_proof_reason is not None or edge.proof_for not in requirements:
            diagnostics.append(
                _diagnostic(
                    "PROOF_EDGE_SCOPE_INVALID",
                    edge.from_id,
                    (edge.from_id, edge.to_id),
                    (edge.proof_for,),
                    (
                        "proof_for must name exactly one approved stable requirement and "
                        "cannot be combined"
                    ),
                )
            )
            continue
        source = nodes.get(edge.from_id)
        target = nodes.get(edge.to_id)
        if (
            source is not None
            and source.kind is NodeKind.REQUIREMENT
            and source.requirement_id != edge.proof_for
        ) or (
            target is not None
            and target.kind is NodeKind.REQUIREMENT
            and target.requirement_id != edge.proof_for
        ):
            diagnostics.append(
                _diagnostic(
                    "PROOF_EDGE_SCOPE_INVALID",
                    edge.from_id,
                    (edge.from_id, edge.to_id),
                    (edge.proof_for,),
                    "a requirement endpoint must match the edge proof_for scope",
                )
            )
            continue
        incident[edge.from_id].add(edge.proof_for)
        incident[edge.to_id].add(edge.proof_for)
        outgoing[edge.from_id].add(edge.proof_for)
        incoming[edge.to_id].add(edge.proof_for)

    for node in sorted(graph.nodes, key=lambda item: item.id):
        if not _is_traceable_node(node) or node.kind in {
            NodeKind.REQUIREMENT,
            NodeKind.CONFLICT,
        }:
            continue
        scopes = incident.get(node.id, set())
        expected = tuple(sorted(scopes))
        actual = tuple(sorted(node.requirements))
        if actual != expected:
            diagnostics.append(
                _diagnostic(
                    "PROOF_NODE_PROJECTION_MISMATCH",
                    node.id,
                    (node.id,),
                    tuple(sorted(set((*actual, *expected)))),
                    "requirements is the exact projection of incident proof_for scopes",
                )
            )
        if node.kind in _PROOF_CRITICAL_KINDS and (scopes or node.requirements):
            scoped_requirement = (
                requirements.get(next(iter(scopes))) if len(scopes) == 1 else None
            )
            if (
                len(scopes) != 1
                or scoped_requirement is None
                or node.owner != scoped_requirement.owner
            ):
                diagnostics.append(
                    _diagnostic(
                        "PROOF_CRITICAL_SCOPE_INVALID",
                        node.id,
                        (node.id,),
                        expected,
                        (
                            "proof-critical witnesses must be singleton and owned by that "
                            "requirement domain"
                        ),
                    )
                )
        if node.kind is NodeKind.SOURCE_MODULE:
            invalid_shared = (
                (len(scopes) > 1 and not node.shared_proof)
                or any(
                    requirement_id not in incoming.get(node.id, set())
                    or requirement_id not in outgoing.get(node.id, set())
                    for requirement_id in scopes
                )
            )
            if invalid_shared:
                diagnostics.append(
                    _diagnostic(
                        "PROOF_SHARED_SOURCE_INVALID",
                        node.id,
                        (node.id,),
                        expected,
                        (
                            "shared SourceModule proof needs explicit scope and an in/out lane "
                            "per requirement"
                        ),
                    )
                )
        elif node.shared_proof:
            diagnostics.append(
                _diagnostic(
                    "PROOF_SHARED_SOURCE_INVALID",
                    node.id,
                    (node.id,),
                    expected,
                    "shared_proof is legal only on SourceModule nodes",
                )
            )
    return diagnostics


def _check_owners(graph: ArchitectureGraph) -> list[Diagnostic]:
    return [
        _diagnostic(
            "MISSING_CANONICAL_OWNER",
            node.id,
            (node.id,),
            node.requirements,
            "every active node requires one non-empty owner",
        )
        for node in graph.nodes
        if node.active and not node.owner.strip()
    ]


def _check_requirements(graph: ArchitectureGraph) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    by_stable_id: dict[str, list[GraphNode]] = defaultdict(list)
    for node in graph.nodes:
        if not node.active or node.kind != "Requirement":
            continue
        stable_id = node.requirement_id
        if stable_id is None:
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_STABLE_ID_MISSING",
                    node.id,
                    (node.id,),
                    message="every active requirement needs a stable requirement_id",
                )
            )
        elif not _REQUIREMENT_STABLE_ID.fullmatch(stable_id):
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_STABLE_ID_INVALID",
                    node.id,
                    (node.id,),
                    (stable_id,),
                    "requirement_id must use the canonical uppercase family-NNN form",
                )
            )
        else:
            by_stable_id[stable_id].append(node)
        if node.requirement_class is None:
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_CLASS_MISSING",
                    node.id,
                    (node.id,),
                    (stable_id,) if stable_id is not None else (),
                    "every active requirement needs an explicit closed classification",
                )
            )
        elif (node.requirement_class is RequirementClass.PRODUCT) != bool(
            stable_id and stable_id.startswith("PROD-")
        ):
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_CLASS_ID_MISMATCH",
                    node.id,
                    (node.id,),
                    (stable_id,) if stable_id is not None else (),
                    "PRODUCT classification and the PROD stable-ID family must agree",
                )
            )
        if not node.owner.strip():
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_OWNER_MISSING",
                    node.id,
                    (node.id,),
                    message="every active requirement needs a non-empty owner",
                )
            )
        if node.approval != "owner-approved":
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_OWNER_APPROVAL_MISSING",
                    node.id,
                    (node.id,),
                    (stable_id,) if stable_id is not None else (),
                    "every active requirement needs explicit owner-approved approval",
                )
            )
    for stable_id, nodes in sorted(by_stable_id.items()):
        if len(nodes) < 2:
            continue
        for node in sorted(nodes, key=lambda item: item.id):
            diagnostics.append(
                _diagnostic(
                    "REQUIREMENT_STABLE_ID_DUPLICATE",
                    node.id,
                    tuple(item.id for item in sorted(nodes, key=lambda item: item.id)),
                    (stable_id,),
                    "active requirement stable IDs must be unique",
                )
            )
    return diagnostics


def _is_traceable_node(node: GraphNode) -> bool:
    return (
        node.active
        and node.lifecycle in _PROOF_LIFECYCLES
        and Classification.MIGRATING not in node.classifications
        and Classification.QUARANTINED not in node.classifications
    )


def _is_approved_requirement(node: GraphNode) -> bool:
    return (
        _is_traceable_node(node)
        and node.kind is NodeKind.REQUIREMENT
        and bool(node.owner.strip())
        and node.requirement_id is not None
        and _REQUIREMENT_STABLE_ID.fullmatch(node.requirement_id) is not None
        and node.requirement_class is not None
        and (node.requirement_class is RequirementClass.PRODUCT)
        == node.requirement_id.startswith("PROD-")
        and node.approval == "owner-approved"
    )


def _is_product_requirement(node: GraphNode) -> bool:
    return node.requirement_class is RequirementClass.PRODUCT


def _is_allowed_edge(edge: object, source: GraphNode, target: GraphNode) -> bool:
    pairs = _EDGE_KIND_MATRIX.get(getattr(edge, "kind"))
    return pairs is not None and (source.kind, target.kind) in pairs


def _is_provenance_edge(edge: object, source: GraphNode, target: GraphNode) -> bool:
    return (
        getattr(edge, "kind") not in _NON_PROVENANCE_EDGE_KINDS
        and _is_allowed_edge(edge, source, target)
    )


def _active_adjacency(
    graph: ArchitectureGraph,
    nodes: dict[str, GraphNode],
    *,
    proof_for: str | None = None,
) -> dict[str, tuple[str, ...]]:
    adjacency: dict[str, tuple[str, ...]] = defaultdict(tuple)
    for edge in graph.edges:
        source = nodes.get(edge.from_id)
        target = nodes.get(edge.to_id)
        if (
            source is None
            or target is None
            or not _is_traceable_node(source)
            or not _is_traceable_node(target)
            or not _is_provenance_edge(edge, source, target)
            or (proof_for is not None and edge.proof_for != proof_for)
        ):
            continue
        adjacency[edge.from_id] = tuple(sorted((*adjacency[edge.from_id], edge.to_id)))
    return adjacency


def _active_reverse_adjacency(
    graph: ArchitectureGraph,
    nodes: dict[str, GraphNode],
    *,
    proof_for: str | None = None,
) -> dict[str, tuple[str, ...]]:
    reverse: dict[str, tuple[str, ...]] = defaultdict(tuple)
    for edge in graph.edges:
        source = nodes.get(edge.from_id)
        target = nodes.get(edge.to_id)
        if (
            source is None
            or target is None
            or not _is_traceable_node(source)
            or not _is_traceable_node(target)
            or not _is_provenance_edge(edge, source, target)
            or (proof_for is not None and edge.proof_for != proof_for)
        ):
            continue
        reverse[edge.to_id] = tuple(sorted((*reverse[edge.to_id], edge.from_id)))
    return reverse


def _active_all_adjacency(
    graph: ArchitectureGraph, nodes: dict[str, GraphNode], *, reverse: bool = False
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = defaultdict(tuple)
    for edge in graph.edges:
        source = nodes.get(edge.from_id)
        target = nodes.get(edge.to_id)
        if (
            source is None
            or target is None
            or not _is_traceable_node(source)
            or not _is_traceable_node(target)
            or not _is_provenance_edge(edge, source, target)
        ):
            continue
        key, value = (
            (edge.to_id, edge.from_id) if reverse else (edge.from_id, edge.to_id)
        )
        result[key] = tuple(sorted((*result[key], value)))
    return result


def _actor_reaches_product_requirement(
    actor_id: str, nodes: dict[str, GraphNode], adjacency: dict[str, tuple[str, ...]]
) -> bool:
    for outcome_id in adjacency.get(actor_id, ()):
        outcome = nodes.get(outcome_id)
        if outcome is None or outcome.kind != "Outcome":
            continue
        if any(
            requirement is not None
            and _is_approved_requirement(requirement)
            and _is_product_requirement(requirement)
            for requirement in (nodes.get(requirement_id) for requirement_id in adjacency.get(outcome_id, ()))
        ):
            return True
    return False


def _outcome_has_product_context(
    outcome_id: str,
    nodes: dict[str, GraphNode],
    reverse: dict[str, tuple[str, ...]],
    adjacency: dict[str, tuple[str, ...]],
) -> bool:
    has_actor = any(
        node is not None and node.kind == "Actor" for node in (nodes.get(actor_id) for actor_id in reverse.get(outcome_id, ()))
    )
    has_requirement = any(
        node is not None and _is_approved_requirement(node) and _is_product_requirement(node)
        for node in (nodes.get(requirement_id) for requirement_id in adjacency.get(outcome_id, ()))
    )
    return has_actor and has_requirement


def _has_product_path(
    requirement_id: str,
    nodes: dict[str, GraphNode],
    reverse: dict[str, tuple[str, ...]],
    adjacency: dict[str, tuple[str, ...]],
) -> bool:
    has_product_origin = any(
        outcome is not None
        and outcome.kind == "Outcome"
        and any(
            actor is not None and actor.kind == "Actor"
            for actor in (nodes.get(actor_id) for actor_id in reverse.get(outcome.id, ()))
        )
        for outcome in (nodes.get(outcome_id) for outcome_id in reverse.get(requirement_id, ()))
    )
    return has_product_origin and _has_forward_path(
        requirement_id, nodes, adjacency, _PRODUCT_FORWARD_PATH_STAGES
    )


def _check_lifecycle(graph: ArchitectureGraph, phase: Phase) -> list[Diagnostic]:
    diagnostics = [
        _diagnostic(
            "M0_REALIZED_LIFECYCLE_FORBIDDEN",
            node.id,
            (node.id,),
            node.requirements,
            "M0 cannot claim the REALIZED lifecycle without trusted controller authority",
        )
        for node in graph.nodes
        if node.lifecycle is Lifecycle.REALIZED
    ]
    diagnostics.extend(
        [
        _diagnostic(
            "INVALID_LIFECYCLE",
            node.id,
            (node.id,),
            node.requirements,
            f"{node.lifecycle.value} nodes cannot remain active",
        )
        for node in graph.nodes
        if node.active and node.lifecycle in _NON_ACTIVE_LIFECYCLES
        ]
    )
    diagnostics.extend(
        _diagnostic(
            "LIFECYCLE_PHASE_REQUIREMENT",
            node.id,
            (node.id,),
            node.requirements,
            (
                f"{node.lifecycle.value} is below required "
                f"{node.required_lifecycle.value} at {phase.value}"
            ),
        )
        for node in graph.nodes
        if (
            node.active
            and node.required_from is not None
            and _PHASE_ORDER[phase] >= _PHASE_ORDER[node.required_from]
            and _LIFECYCLE_MATURITY[node.lifecycle]
            < _LIFECYCLE_MATURITY[node.required_lifecycle or Lifecycle.IMPLEMENTED]
        )
    )
    diagnostics.extend(
        _diagnostic(
            "CLASSIFICATION_ACTIVE_INVALID",
            node.id,
            (node.id,),
            node.requirements,
            f"{classification.value} nodes cannot remain active",
        )
        for node in graph.nodes
        for classification in (Classification.MIGRATING, Classification.QUARANTINED)
        if node.active and classification in node.classifications
    )
    diagnostics.extend(
        _diagnostic(
            "DECLARED_CONFLICT",
            node.id,
            (node.id,),
            node.requirements,
            "declared conflict remains a blocking graph node",
        )
        for node in graph.nodes
        if node.active and node.kind == "Conflict"
    )
    return diagnostics


def _check_traceability(graph: ArchitectureGraph) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    reverse = _active_reverse_adjacency(graph, nodes)
    adjacency = _active_adjacency(graph, nodes)
    diagnostics: list[Diagnostic] = []
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if not _is_traceable_node(node) or not node.owner.strip() or node.kind in _TRACEABILITY_EXEMPT_KINDS:
            continue
        if node.kind == "Actor":
            if _actor_reaches_product_requirement(node.id, nodes, adjacency):
                continue
        elif node.kind == "Outcome":
            if _outcome_has_product_context(node.id, nodes, reverse, adjacency):
                continue
        else:
            requirement_ids = _reachable_requirement_ids(node.id, nodes, reverse)
            if requirement_ids:
                continue
        diagnostics.append(
            _diagnostic(
                "IMPLEMENTATION_ORPHAN",
                node.id,
                (node.id,),
                (),
                "active node has no reverse path to an approved active requirement",
            )
        )
    return diagnostics


def _forward_reachable_requirement_ids(
    node_id: str,
    nodes: dict[str, GraphNode],
    adjacency: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    pending = [node_id]
    seen: set[str] = set()
    requirement_ids: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        node = nodes.get(current)
        if node is not None and node.kind is NodeKind.REQUIREMENT:
            if _is_approved_requirement(node):
                requirement_ids.add(node.requirement_id)
            continue
        pending.extend(reversed(adjacency.get(current, ())))
    return tuple(sorted(requirement_ids))


def _check_requirement_metadata(graph: ArchitectureGraph) -> list[Diagnostic]:
    proof_scopes: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        if edge.kind in _PROOF_EDGE_KINDS and edge.proof_for is not None:
            proof_scopes[edge.from_id].add(edge.proof_for)
            proof_scopes[edge.to_id].add(edge.proof_for)
    diagnostics: list[Diagnostic] = []
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if (
            not _is_traceable_node(node)
            or node.kind in {NodeKind.REQUIREMENT, NodeKind.CONFLICT}
        ):
            continue
        expected = tuple(sorted(proof_scopes.get(node.id, set())))
        actual = tuple(sorted(node.requirements))
        if actual == expected:
            continue
        diagnostics.append(
            _diagnostic(
                "REQUIREMENT_METADATA_MISMATCH",
                node.id,
                (node.id,),
                tuple(sorted(set((*actual, *expected)))),
                "requirements metadata must exactly equal reachable approved stable IDs",
            )
        )
    return diagnostics


def _check_requirement_forward_paths(graph: ArchitectureGraph) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    diagnostics: list[Diagnostic] = []
    for node in sorted(graph.nodes, key=lambda item: item.id):
        if not _is_approved_requirement(node):
            continue
        adjacency = _active_adjacency(graph, nodes, proof_for=node.requirement_id)
        reverse = _active_reverse_adjacency(graph, nodes, proof_for=node.requirement_id)
        has_approval = any(
            edge.from_id == node.id
            and edge.kind == "approved_by"
            and edge.proof_for == node.requirement_id
            and (approval := nodes.get(edge.to_id)) is not None
            and _is_traceable_node(approval)
            and approval.kind is NodeKind.APPROVAL
            for edge in graph.edges
        )
        has_path = (
            _has_product_path(node.id, nodes, reverse, adjacency)
            if _is_product_requirement(node)
            else _has_forward_path(node.id, nodes, adjacency, _NON_PRODUCT_FORWARD_PATH_STAGES)
        )
        if has_approval and has_path:
            continue
        diagnostics.append(
            _diagnostic(
                "PRODUCT_TRACEABILITY_INCOMPLETE"
                if _is_product_requirement(node)
                else (
                    "REQUIREMENT_FORWARD_PATH_MISSING"
                    if not adjacency.get(node.id)
                    else "REQUIREMENT_FORWARD_PATH_INCOMPLETE"
                ),
                node.id,
                (node.id,),
                (node.requirement_id,),
                (
                    "product requirement needs Actor, Outcome, criterion, metric, contract, dataflow, "
                    "validation, evidence, and rollback"
                    if _is_product_requirement(node)
                    else "requirement needs an edge path through validation, evidence, and rollback"
                ),
            )
        )
    return diagnostics


def _has_forward_path(
    requirement_id: str,
    nodes: dict[str, object],
    adjacency: dict[str, tuple[str, ...]],
    stages: tuple[frozenset[str], ...],
) -> bool:
    pending = [(requirement_id, 0)]
    seen: set[tuple[str, int]] = set()
    while pending:
        current, stage = pending.pop()
        if (current, stage) in seen:
            continue
        seen.add((current, stage))
        for next_id in adjacency.get(current, ()):
            next_node = nodes.get(next_id)
            if next_node is None:
                continue
            if next_id != requirement_id and getattr(next_node, "kind") is NodeKind.REQUIREMENT:
                continue
            next_stage = stage
            if stage < len(stages) and getattr(next_node, "kind") in stages[stage]:
                next_stage += 1
            if next_stage == len(stages):
                return True
            pending.append((next_id, next_stage))
    return False


def _check_runtime_capabilities(graph: ArchitectureGraph) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    diagnostics: list[Diagnostic] = []
    for node in sorted(graph.nodes, key=lambda item: item.id):
        unknown = tuple(sorted(set(node.capabilities) - _KNOWN_CAPABILITIES))
        diagnostics.extend(
            _diagnostic(
                "CAPABILITY_UNKNOWN",
                node.id,
                (node.id, capability),
                node.requirements,
                "capability is not in the closed Stage A vocabulary",
            )
            for capability in unknown
        )
        if node.profile is None:
            if node.capabilities:
                diagnostics.append(
                    _diagnostic(
                        "NODE_CAPABILITY_COMBINATION_INVALID",
                        node.id,
                        (node.id,),
                        node.requirements,
                        "nodes without a runtime profile must declare no capabilities",
                    )
                )
            continue
        allowed = _RUNTIME_PROFILE_CAPABILITIES.get((node.kind, node.profile))
        if allowed is None:
            diagnostics.append(
                _diagnostic(
                    "RUNTIME_PROFILE_UNKNOWN",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "profile is not allowed for this closed node kind",
                )
            )
            diagnostics.append(
                _diagnostic(
                    "NODE_CAPABILITY_COMBINATION_INVALID",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "node kind, profile, and capabilities are not an approved combination",
                )
            )
            continue
        forbidden = tuple(sorted(set(node.capabilities) & _FORBIDDEN_CAPABILITIES))
        diagnostics.extend(
            _diagnostic(
                "RUNTIME_CAPABILITY_FORBIDDEN", node.id, (node.id, capability), node.requirements,
                "Stage A runtime capability is forbidden",
            )
            for capability in forbidden
        )
        if frozenset(node.capabilities) != allowed:
            diagnostics.append(
                _diagnostic(
                    "RUNTIME_CAPABILITY_INVALID", node.id, (node.id,), node.requirements,
                    f"{node.profile} capabilities must be exactly {', '.join(sorted(allowed)) or 'none'}",
                )
            )
            diagnostics.append(
                _diagnostic(
                    "NODE_CAPABILITY_COMBINATION_INVALID",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "node kind, profile, and capabilities are not an approved combination",
                )
            )
        if (
            node.profile == "go-test-only"
            and Classification.TEST_ONLY_EXECUTABLE_SPEC not in node.classifications
        ):
            diagnostics.append(_diagnostic("RUNTIME_GO_PROFILE_INVALID", node.id, (node.id,), node.requirements, "Go is test-only"))
        if node.profile == "execution" and (
            node.kind != "Artifact"
            or node.active
            or Classification.QUARANTINED not in node.classifications
        ):
            diagnostics.append(_diagnostic("RUNTIME_EXECUTION_BOUNDARY_INVALID", node.id, (node.id,), node.requirements, "execution is inactive and quarantined"))
    for dependency in graph.runtime_dependencies:
        source = nodes.get(dependency.from_id)
        target = nodes.get(dependency.to_id)
        if source is None or target is None:
            continue
        if source.profile is None and target.profile is None:
            continue
        if (
            source.profile is None
            or target.profile is None
            or (source.profile, target.profile) not in _ALLOWED_RUNTIME_DEPENDENCIES
        ):
            diagnostics.append(
                _diagnostic(
                    "RUNTIME_DEPENDENCY_FORBIDDEN", dependency.from_id,
                    (dependency.from_id, dependency.to_id),
                    source.requirements,
                    "runtime dependency crosses a forbidden Stage A boundary",
                )
            )
    return diagnostics


def _reachable_requirement_ids(
    node_id: str, nodes: dict[str, GraphNode], reverse: dict[str, tuple[str, ...]]
) -> tuple[str, ...]:
    pending = [node_id]
    seen: set[str] = set()
    requirement_ids: set[str] = set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        node = nodes.get(current)
        if node is not None and node.kind is NodeKind.REQUIREMENT:
            if _is_approved_requirement(node):
                requirement_ids.add(node.requirement_id)
            continue
        pending.extend(reversed(reverse.get(current, ())))
    return tuple(sorted(requirement_ids))


def _check_runtime_dag(graph: ArchitectureGraph) -> list[Diagnostic]:
    adjacency: dict[str, tuple[str, ...]] = defaultdict(tuple)
    for edge in graph.runtime_dependencies:
        adjacency[edge.from_id] = tuple(sorted((*adjacency[edge.from_id], edge.to_id)))
    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []

    def visit(node_id: str) -> tuple[str, ...] | None:
        visited.add(node_id)
        active.add(node_id)
        stack.append(node_id)
        for next_id in adjacency.get(node_id, ()):
            if next_id in active:
                return tuple(stack[stack.index(next_id) :] + [next_id])
            if next_id not in visited:
                cycle = visit(next_id)
                if cycle:
                    return cycle
        stack.pop()
        active.remove(node_id)
        return None

    for node_id in sorted(adjacency):
        if node_id not in visited:
            cycle = visit(node_id)
            if cycle:
                return [
                    _diagnostic(
                        "RUNTIME_CYCLE",
                        cycle[0],
                        cycle,
                        message="runtime dependencies must form a DAG",
                    )
                ]
    return []


def _cycle_in_adjacency(
    adjacency: dict[str, tuple[str, ...]],
) -> tuple[str, ...] | None:
    visited: set[str] = set()
    active: set[str] = set()
    stack: list[str] = []

    def visit(node_id: str) -> tuple[str, ...] | None:
        visited.add(node_id)
        active.add(node_id)
        stack.append(node_id)
        for next_id in adjacency.get(node_id, ()):
            if next_id in active:
                return tuple(stack[stack.index(next_id) :] + [next_id])
            if next_id not in visited:
                cycle = visit(next_id)
                if cycle:
                    return cycle
        stack.pop()
        active.remove(node_id)
        return None

    for node_id in sorted(adjacency):
        if node_id not in visited:
            cycle = visit(node_id)
            if cycle:
                return cycle
    return None


def _check_evidence_derivation_dag(graph: ArchitectureGraph) -> list[Diagnostic]:
    adjacency: dict[str, tuple[str, ...]] = defaultdict(tuple)
    for edge in graph.edges:
        if edge.kind in _LINEAGE_EDGE_KINDS:
            adjacency[edge.from_id] = tuple(
                sorted((*adjacency[edge.from_id], edge.to_id))
            )
    cycle = _cycle_in_adjacency(adjacency)
    if cycle is None:
        return []
    return [
        _diagnostic(
            "PROVENANCE_LINEAGE_CYCLE",
            cycle[0],
            cycle,
            message="combined derived_from and supersedes provenance must form one DAG",
        )
    ]


def _check_semantic_supersedes(graph: ArchitectureGraph) -> list[Diagnostic]:
    successors: dict[str, set[str]] = defaultdict(set)
    for edge in graph.edges:
        if edge.kind in _LINEAGE_EDGE_KINDS:
            successors[edge.to_id].add(edge.from_id)
    return [
        _diagnostic(
            "SUPERSEDES_SUCCESSOR_AMBIGUOUS",
            predecessor,
            tuple(sorted(successor_ids)),
            message="one predecessor may have only one semantic superseding successor",
        )
        for predecessor, successor_ids in sorted(successors.items())
        if len(successor_ids) > 1
    ]


def _check_phase_policy_time_context(
    graph: ArchitectureGraph, phase: Phase
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    previous_phase: Phase | None = None
    previous_time: datetime | None = None
    for declared_phase, value in sorted(
        graph.phase_policy_times, key=lambda item: _PHASE_ORDER[item[0]]
    ):
        parsed = _parse_receipt_timestamp(value)
        if parsed is None:
            continue
        if previous_time is not None and parsed < previous_time:
            diagnostics.append(
                _diagnostic(
                    "PHASE_POLICY_TIME_NON_MONOTONIC",
                    None,
                    (previous_phase.value, declared_phase.value),
                    message="phase policy times must be monotonic in lifecycle order",
                )
            )
        previous_phase = declared_phase
        previous_time = parsed
    if phase is not Phase.PRECOMMIT and not graph.policy_times_trusted:
        diagnostics.append(
            _diagnostic(
                "PHASE_POLICY_TIME_TRUST_MISSING",
                None,
                (phase.value,),
                message="merge and later phases require repository-root trusted policy time",
            )
        )
    return diagnostics


def _check_migrations(graph: ArchitectureGraph, phase: Phase) -> list[Diagnostic]:
    nodes = {node.id: node for node in graph.nodes}
    owners: dict[str, list[GraphNode]] = defaultdict(list)
    migration_fields = (
        "replacement",
        "expiry_utc",
        "removal_gate",
        "rollback_node",
        "expiry_conflict",
    )
    diagnostics: list[Diagnostic] = []
    for node in graph.nodes:
        if node.active and node.canonical_for:
            owners[node.canonical_for].append(node)
        if (
            Classification.MIGRATING not in node.classifications
            and any(getattr(node, field) is not None for field in migration_fields)
        ):
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_FIELD_WITHOUT_CLASSIFICATION",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "predecessor migration fields require the MIGRATING classification",
                )
            )
        if node.canonical_for is not None:
            predecessor = nodes.get(node.canonical_for)
            if (
                not node.active
                or predecessor is None
                or Classification.MIGRATING not in predecessor.classifications
                or predecessor.replacement != node.id
            ):
                diagnostics.append(
                    _diagnostic(
                        "MIGRATION_CANONICAL_OWNER_INVALID",
                        node.id,
                        (node.id, node.canonical_for),
                        node.requirements,
                        "canonical_for must bind an active replacement to its MIGRATING predecessor",
                    )
                )
    for subject, owner_nodes in sorted(owners.items()):
        if len(owner_nodes) > 1:
            path = tuple(sorted(node.id for node in owner_nodes))
            diagnostics.append(
                _diagnostic(
                    "MULTIPLE_CANONICAL_MIGRATION_OWNERS",
                    None,
                    path,
                    message=f"{subject} has more than one canonical migration owner",
                )
            )

    migrating = [
        node for node in graph.nodes if Classification.MIGRATING in node.classifications
    ]
    policy_time_utc = graph.policy_time(phase)
    evaluation_time = _parse_receipt_timestamp(policy_time_utc)
    for node in sorted(migrating, key=lambda item: item.id):
        if node.active:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_PREDECESSOR_ACTIVE",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "a MIGRATING predecessor must be inactive",
                )
            )
        if any(
            dependency.from_id == node.id or dependency.to_id == node.id
            for dependency in graph.runtime_dependencies
        ):
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_RUNTIME_REACHABLE",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "a MIGRATING predecessor must be runtime-unreachable",
                )
            )

        replacement = nodes.get(node.replacement or "")
        if node.replacement is None:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_REPLACEMENT_MISSING",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "a MIGRATING predecessor must name its replacement",
                )
            )
        else:
            canonical_owners = owners.get(node.id, [])
            if (
                len(canonical_owners) != 1
                or replacement is None
                or not replacement.active
                or replacement.id != canonical_owners[0].id
                or replacement.kind != node.kind
            ):
                diagnostics.append(
                    _diagnostic(
                        "MIGRATION_CANONICAL_OWNER_INVALID",
                        node.id,
                        (node.id, node.replacement),
                        node.requirements,
                        "a MIGRATING predecessor needs exactly one active canonical replacement owner",
                    )
                )
            if not graph.has_edge(node.replacement, "supersedes", node.id):
                diagnostics.append(
                    _diagnostic(
                        "MIGRATION_REPLACEMENT_EDGE_MISSING",
                        node.id,
                        (node.id, node.replacement),
                        node.requirements,
                        "a MIGRATING predecessor needs a typed replacement edge",
                    )
                )

        expiry = _parse_receipt_timestamp(node.expiry_utc)
        if node.expiry_utc is None:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_EXPIRY_MISSING",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "a MIGRATING predecessor needs a deterministic expiry",
                )
            )
        elif expiry is None:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_EXPIRY_INVALID",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "migration expiry must be an exact UTC timestamp",
                )
            )

        _check_migration_target(
            diagnostics,
            graph,
            nodes,
            node,
            node.removal_gate,
            "ClawGate",
            "MIGRATION_REMOVAL_GATE",
            "removal gate",
            "gated_by",
        )
        _check_migration_target(
            diagnostics,
            graph,
            nodes,
            node,
            node.rollback_node,
            "Rollback",
            "MIGRATION_ROLLBACK",
            "rollback node",
            "rolled_back_by",
        )

        if policy_time_utc is None:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_POLICY_TIME_MISSING",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "MIGRATING nodes require a versioned deterministic time for this phase",
                )
            )
        elif evaluation_time is None:
            diagnostics.append(
                _diagnostic(
                    "MIGRATION_POLICY_TIME_INVALID",
                    node.id,
                    (node.id,),
                    node.requirements,
                    "versioned migration policy time must be an exact UTC timestamp",
                )
            )
        elif expiry is not None and evaluation_time >= expiry:
            conflict = nodes.get(node.expiry_conflict or "")
            if (
                conflict is None
                or not conflict.active
                or conflict.kind is not NodeKind.CONFLICT
                or not graph.has_edge(node.id, "conflicts_with", conflict.id)
            ):
                diagnostics.append(
                    _diagnostic(
                        "MIGRATION_EXPIRY_CONFLICT_MISSING",
                        node.id,
                        (node.id, *( (node.expiry_conflict,) if node.expiry_conflict else () )),
                        node.requirements,
                        "an expired migration requires a named active blocking conflict",
                    )
                )
    return diagnostics


def _check_migration_target(
    diagnostics: list[Diagnostic],
    graph: ArchitectureGraph,
    nodes: dict[str, GraphNode],
    migration: GraphNode,
    target_id: str | None,
    target_kind: str,
    code_prefix: str,
    target_label: str,
    edge_kind: str,
) -> None:
    if target_id is None:
        diagnostics.append(
            _diagnostic(
                f"{code_prefix}_MISSING",
                migration.id,
                (migration.id,),
                migration.requirements,
                f"a MIGRATING predecessor needs a {target_label}",
            )
        )
        return
    target = nodes.get(target_id)
    if target is None or not target.active or target.kind != target_kind:
        diagnostics.append(
            _diagnostic(
                f"{code_prefix}_INVALID",
                migration.id,
                (migration.id, target_id),
                migration.requirements,
                f"migration {target_label} must name an active {target_kind}",
            )
        )
    elif not graph.has_edge(migration.id, edge_kind, target_id):
        diagnostics.append(
            _diagnostic(
                f"{code_prefix}_EDGE_MISSING",
                migration.id,
                (migration.id, target_id),
                migration.requirements,
                f"migration {target_label} requires the exact {edge_kind} relation",
            )
        )


def _check_receipts(
    graph: ArchitectureGraph, phase: Phase, receipt_context: ReceiptValidationContext | None
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    nodes = {node.id: node for node in graph.nodes}
    for node in graph.nodes:
        lifecycle_requires_receipt = (
            node.lifecycle in {Lifecycle.VERIFIED, Lifecycle.REALIZED}
        )
        phase_requires_receipt = (
            node.active
            and node.required_from is not None
            and _PHASE_ORDER[phase] >= _PHASE_ORDER[node.required_from]
            and _LIFECYCLE_MATURITY[node.required_lifecycle or Lifecycle.IMPLEMENTED]
            >= _LIFECYCLE_MATURITY[Lifecycle.VERIFIED]
        )
        if not (lifecycle_requires_receipt or phase_requires_receipt):
            continue
        if any(
            receipt.node_id == node.id
            and _PHASE_ORDER[receipt.required_from] <= _PHASE_ORDER[phase]
            for receipt in graph.receipts
        ):
            continue
        diagnostics.append(
            _diagnostic(
                "RECEIPT_REQUIRED_MISSING",
                node.id,
                (node.id,),
                node.requirements,
                "the node lifecycle or phase requirement mandates a receipt declaration",
            )
        )
    content_subjects: dict[str, str] = {}
    verification_subjects: dict[str, str] = {}
    for receipt in graph.receipts:
        if receipt.status == "realized":
            if receipt.node_id not in nodes:
                diagnostics.append(
                    _diagnostic(
                        "RECEIPT_TRUST_ANCHOR_UNAVAILABLE",
                        receipt.node_id,
                        (receipt.node_id,),
                        message="M0 has no trusted default-branch controller authority",
                    )
                )
                continue
            identity_error = _receipt_identity_error(receipt, nodes)
            if identity_error is not None:
                diagnostics.append(
                    _diagnostic(
                        identity_error, receipt.node_id, (receipt.node_id,),
                        message="receipt identity is not structurally bound",
                    )
                )
            else:
                if _hash_reused(receipt.content_hash or "", receipt.node_id, content_subjects):
                    diagnostics.append(
                        _diagnostic(
                            "RECEIPT_CONTENT_HASH_REUSED", receipt.node_id, (receipt.node_id,),
                            message="content hash is reused for another receipt subject",
                        )
                    )
                if _hash_reused(receipt.verification_hash or "", receipt.node_id, verification_subjects):
                    diagnostics.append(
                        _diagnostic(
                            "RECEIPT_VERIFICATION_HASH_REUSED", receipt.node_id, (receipt.node_id,),
                            message="verification hash is reused for another receipt subject",
                        )
                    )
                validation_error = _receipt_validation_error(receipt, receipt_context)
                if validation_error is not None:
                    diagnostics.append(
                        _diagnostic(
                            validation_error, receipt.node_id, (receipt.node_id,),
                            message="receipt validation binding failed",
                        )
                    )
            diagnostics.append(
                _diagnostic(
                    "RECEIPT_TRUST_ANCHOR_UNAVAILABLE",
                    receipt.node_id,
                    (receipt.node_id,),
                    message="M0 has no trusted default-branch controller authority",
                )
            )
            continue
        if receipt.node_id not in nodes:
            continue
        identity_error = _receipt_identity_error(receipt, nodes)
        if identity_error is not None:
            diagnostics.append(
                _diagnostic(
                    identity_error, receipt.node_id, (receipt.node_id,),
                    message="receipt identity is not structurally bound",
                )
            )
            continue
        if _PHASE_ORDER[phase] < _PHASE_ORDER[receipt.required_from]:
            continue
        if receipt.status != "realized":
            diagnostics.append(
                _diagnostic(
                    "RECEIPT_NOT_REALIZED",
                    receipt.node_id,
                    (receipt.node_id,),
                    message=(
                        f"{receipt.evidence_type} is {receipt.status}; "
                        "a phase-applicable receipt must be realized"
                    ),
                )
            )
    return diagnostics


def _receipt_validation_error(
    receipt: object, context: ReceiptValidationContext | None
) -> str | None:
    if context is None:
        return "RECEIPT_TRUST_CONTEXT_MISSING"
    cutoff = _parse_receipt_timestamp(context.evidence_cutoff_utc)
    if cutoff is None:
        return "RECEIPT_TRUST_CONTEXT_INVALID"
    produced_at = _parse_receipt_timestamp(receipt.produced_at)
    verified_at = _parse_receipt_timestamp(receipt.verified_at)
    if produced_at is None or verified_at is None:
        return "RECEIPT_TRUST_CONTEXT_INVALID"
    if produced_at > cutoff or verified_at > cutoff:
        return "RECEIPT_TRUST_CUTOFF_EXCEEDED"
    if receipt.source_sha != context.expected_source_sha:
        return "RECEIPT_TRUST_SOURCE_SHA_MISMATCH"
    matches = [entry for entry in context.registry if _registry_matches_receipt(entry, receipt)]
    return None if len(matches) == 1 else "RECEIPT_TRUST_REGISTRY_MATCH_INVALID"


def _registry_matches_receipt(entry: object, receipt: object) -> bool:
    return (
        entry.node_id == receipt.node_id
        and entry.content_hash == receipt.content_hash
        and entry.source_sha == receipt.source_sha
        and entry.producer == receipt.producer
        and entry.produced_at == receipt.produced_at
        and entry.verifier == receipt.verifier
        and entry.verification_hash == receipt.verification_hash
        and entry.verified_at == receipt.verified_at
    )


def _receipt_identity_error(receipt: object, nodes: dict[str, object]) -> str | None:
    if receipt.status not in {"prospective", "realized"}:
        return "RECEIPT_STATUS_INVALID"
    identity = (
        receipt.content_hash,
        receipt.source_sha,
        receipt.producer,
        receipt.produced_at,
        receipt.verifier,
        receipt.verification_hash,
        receipt.verified_at,
    )
    if receipt.status == "prospective":
        return "RECEIPT_IDENTITY_PROSPECTIVE" if any(value is not None for value in identity) else None
    if any(value is None for value in identity):
        return "RECEIPT_IDENTITY_INCOMPLETE"
    if not _valid_receipt_hash(receipt.content_hash, _RECEIPT_HEX_64):
        return "RECEIPT_CONTENT_HASH_INVALID"
    if not _valid_receipt_hash(receipt.source_sha, _RECEIPT_HEX_40):
        return "RECEIPT_SOURCE_SHA_INVALID"
    if not _valid_receipt_hash(receipt.verification_hash, _RECEIPT_HEX_64):
        return "RECEIPT_VERIFICATION_HASH_INVALID"
    for node_id in (receipt.producer, receipt.verifier):
        node = nodes.get(node_id or "")
        if node is None or not node.active:
            return "RECEIPT_IDENTITY_NODE_INVALID"
    produced_at = _parse_receipt_timestamp(receipt.produced_at)
    verified_at = _parse_receipt_timestamp(receipt.verified_at)
    if produced_at is None or verified_at is None:
        return "RECEIPT_TIMESTAMP_INVALID"
    if produced_at > verified_at:
        return "RECEIPT_TIMESTAMP_ORDER_INVALID"
    return None


def _valid_receipt_hash(value: str | None, pattern: re.Pattern[str]) -> bool:
    return value is not None and pattern.fullmatch(value) is not None and len(set(value)) > 1


def _parse_receipt_timestamp(value: str | None) -> datetime | None:
    if value is None or _RECEIPT_UTC.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None


def _hash_reused(value: str, subject: str, subjects: dict[str, str]) -> bool:
    previous = subjects.get(value)
    if previous is not None and previous != subject:
        return True
    subjects[value] = subject
    return False
