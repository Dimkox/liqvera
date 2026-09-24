"""Closed, deterministic loader for fixture and repository architecture graphs."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .model import (
    ArchitectureGraph,
    ArtifactBinding,
    Classification,
    GraphEdge,
    GraphNode,
    InventoryExclusionReason,
    Lifecycle,
    NodeKind,
    PathClass,
    Phase,
    ReceiptRequirement,
    ReceiptValidationContext,
    RepositoryArtifact,
    RepositoryInventoryExclusion,
    RequirementClass,
    RuntimeDependency,
    VerifiedReceiptRegistryEntry,
)


class GraphLoadError(ValueError):
    """Input shape or YAML errors, distinct from graph policy violations."""


_ROOT_KEYS = {
    "manifest_version",
    "nodes",
    "edges",
    "runtime_dependencies",
    "receipts",
    "phase_policy_times",
    "repository_inventory",
}
_NODE_KEYS = {
    "id",
    "kind",
    "owner",
    "lifecycle",
    "active",
    "requirements",
    "requirement_id",
    "requirement_class",
    "approval",
    "classifications",
    "canonical_for",
    "replacement",
    "expiry_utc",
    "removal_gate",
    "rollback_node",
    "expiry_conflict",
    "required_from",
    "required_lifecycle",
    "profile",
    "capabilities",
    "shared_proof",
}
_EDGE_KEYS = {"from", "to", "kind", "proof_for", "non_proof_reason"}
_RUNTIME_KEYS = {"from", "to"}
_RECEIPT_KEYS = {
    "node",
    "required_from",
    "evidence_type",
    "status",
    "content_hash",
    "source_sha",
    "producer",
    "produced_at",
    "verifier",
    "verification_hash",
    "verified_at",
}
_REALIZED_RECEIPT_KEYS = {
    "content_hash",
    "source_sha",
    "producer",
    "produced_at",
    "verifier",
    "verification_hash",
    "verified_at",
}
_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
_UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_REGISTRY_ROOT_KEYS = {"registry_version", "receipts"}
_REGISTRY_ENTRY_KEYS = {
    "node",
    "content_hash",
    "source_sha",
    "producer",
    "produced_at",
    "verifier",
    "verification_hash",
    "verified_at",
}
_REPOSITORY_MANIFESTS = (
    "requirements.yaml",
    "architecture.yaml",
    "runtime.yaml",
    "data-contracts.yaml",
    "strategies.yaml",
    "release.yaml",
)
_INVENTORY_KEYS = {"bindings", "exclusions", "exclusion_prefixes"}
_BINDING_KEYS = {"path", "node", "path_class"}
_EXCLUSION_KEYS = {"path", "reason_code", "authority_node", "path_class"}
_PREFIX_EXCLUSION_KEYS = {"prefix", "reason_code", "authority_node"}
_VENDORED_PREFIXES = frozenset({".agents/", "_bmad/", ".grok/", ".grok-stack/"})
_ADAPTIVE_GROK_SHIMS = frozenset(
    {
        "session_start.py",
        "session_end.py",
        "user_prompt_submit.py",
        "pre_tool_use.py",
        "post_tool_use.py",
        "pre_compact.py",
        "subagent_start.py",
        "subagent_stop.py",
        "stop_gate.py",
        "scripts/grok_approve.py",
        "scripts/grok_change.py",
        "scripts/grok_deploy.py",
        "scripts/grok_doctor.py",
        "scripts/grok_review.py",
        "scripts/grok_route.py",
        "scripts/grok_status.py",
        "scripts/grok_verify.py",
        "ruff.toml",
        "bandit.yaml",
        ".coveragerc",
    }
)


def load_graph(
    manifest_root: Path, *, allow_single_file_fixture: bool = False
) -> ArchitectureGraph:
    """Load a closed manifest set in a deterministic, platform-independent order.

    Reviewed fixtures intentionally remain single-file ``architecture.yaml``
    graphs.  Repository authority roots use the complete six-file manifest set.
    """
    root = Path(manifest_root)
    paths = _manifest_paths(root, allow_single_file_fixture=allow_single_file_fixture)
    documents = tuple(_load_document(path) for path in paths)
    if len(paths) == len(_REPOSITORY_MANIFESTS) and any(
        document["manifest_version"] != 2 for document in documents
    ):
        raise GraphLoadError("repository authority manifests require manifest_version 2")
    nodes = tuple(
        _node(value, index)
        for document in documents
        for index, value in enumerate(_list(document, "nodes"))
    )
    node_ids = tuple(node.id for node in nodes)
    if len(set(node_ids)) != len(node_ids):
        raise GraphLoadError("node ids must be unique across the manifest set")

    edges = tuple(
        _edge(value, index)
        for document in documents
        for index, value in enumerate(_list(document, "edges"))
    )
    runtime = tuple(
        _runtime_dependency(value, index)
        for document in documents
        for index, value in enumerate(_list(document, "runtime_dependencies"))
    )
    receipts = tuple(
        _receipt(value, index)
        for document in documents
        for index, value in enumerate(_list(document, "receipts"))
    )
    phase_policy_times = _phase_policy_times(documents)
    repository_artifacts = _tracked_repository_artifacts(root)
    artifact_bindings, inventory_exclusions = _repository_inventory(
        documents, repository_artifacts
    )
    # M0 cannot self-attest controller/default-branch authority. Story 1.1/M6
    # must supply and verify the external controller context before this may
    # ever become true.
    policy_times_trusted = False
    _validate_receipt_bindings(receipts, nodes)
    return ArchitectureGraph(
        nodes=tuple(sorted(nodes, key=lambda item: item.id)),
        edges=tuple(
            sorted(
                edges,
                key=lambda item: (
                    item.from_id,
                    item.kind,
                    item.to_id,
                    item.proof_for or "",
                    item.non_proof_reason or "",
                ),
            )
        ),
        runtime_dependencies=tuple(sorted(runtime, key=lambda item: (item.from_id, item.to_id))),
        receipts=tuple(
            sorted(
                receipts,
                key=lambda item: (item.node_id, item.required_from, item.evidence_type),
            )
        ),
        phase_policy_times=phase_policy_times,
        policy_times_trusted=policy_times_trusted,
        repository_artifacts=repository_artifacts,
        artifact_bindings=artifact_bindings,
        inventory_exclusions=inventory_exclusions,
    )


def _repository_inventory(
    documents: tuple[dict[str, Any], ...],
    repository_artifacts: tuple[RepositoryArtifact, ...],
) -> tuple[tuple[ArtifactBinding, ...], tuple[RepositoryInventoryExclusion, ...]]:
    declarations = [
        document["repository_inventory"]
        for document in documents
        if "repository_inventory" in document
    ]
    if len(declarations) > 1:
        raise GraphLoadError("repository_inventory must be declared exactly once")
    if not declarations:
        return (), ()
    inventory = _mapping(declarations[0], "repository_inventory")
    _closed_keys(inventory, _INVENTORY_KEYS, "repository_inventory")
    bindings: list[ArtifactBinding] = []
    for index, raw in enumerate(_list(inventory, "bindings")):
        label = f"repository_inventory.bindings[{index}]"
        item = _mapping(raw, label)
        _closed_keys(item, _BINDING_KEYS, label)
        bindings.append(
            ArtifactBinding(
                _required_string(item, "path", label),
                _required_string(item, "node", label),
                PathClass(_required_string(item, "path_class", label)),
            )
        )
    exclusions: list[RepositoryInventoryExclusion] = []
    for index, raw in enumerate(_list(inventory, "exclusions")):
        label = f"repository_inventory.exclusions[{index}]"
        item = _mapping(raw, label)
        _closed_keys(item, _EXCLUSION_KEYS, label)
        exclusions.append(
            RepositoryInventoryExclusion(
                _required_string(item, "path", label),
                InventoryExclusionReason(_required_string(item, "reason_code", label)),
                _required_string(item, "authority_node", label),
                PathClass(_required_string(item, "path_class", label)),
            )
        )
    for index, raw in enumerate(_list(inventory, "exclusion_prefixes")):
        label = f"repository_inventory.exclusion_prefixes[{index}]"
        item = _mapping(raw, label)
        _closed_keys(item, _PREFIX_EXCLUSION_KEYS, label)
        prefix = _required_string(item, "prefix", label)
        if prefix not in _VENDORED_PREFIXES:
            raise GraphLoadError(f"{label}.prefix is not an approved vendored prefix")
        reason = InventoryExclusionReason(
            _required_string(item, "reason_code", label)
        )
        if reason is not InventoryExclusionReason.VENDORED_TOOLING:
            raise GraphLoadError(f"{label}.reason_code must be VENDORED_TOOLING")
        authority = _required_string(item, "authority_node", label)
        exclusions.extend(
            RepositoryInventoryExclusion(
                artifact.path,
                reason,
                authority,
                artifact.path_class,
            )
            for artifact in repository_artifacts
            if artifact.path.startswith(prefix)
        )
    return (
        tuple(sorted(bindings, key=lambda item: (item.path, item.node_id))),
        tuple(sorted(exclusions, key=lambda item: item.path)),
    )


def _tracked_repository_artifacts(root: Path) -> tuple[RepositoryArtifact, ...]:
    if root.name != "architecture":
        return ()
    completed = subprocess.run(
        ["git", "-C", str(root.parent), "ls-files", "-z"],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise GraphLoadError("repository inventory requires a readable Git index")
    paths = completed.stdout.decode("utf-8").split("\0")
    artifacts = (
        _repository_artifact(root.parent, path, _classify_repository_path(path))
        for path in paths
        if path
    )
    return tuple(sorted(artifacts, key=lambda item: item.path))


_PYTHON_SOURCE_CLASSES = frozenset(
    {
        PathClass.RUNTIME_SOURCE,
        PathClass.EXECUTION_SOURCE,
        PathClass.TEST_SOURCE,
        PathClass.TOOL_SOURCE,
    }
)
_FORBIDDEN_EXPORTED_NAMES = frozenset(
    {
        "cancel",
        "cancel_all",
        "cancel_order",
        "order",
        "place_order",
        "private",
        "promotion",
        "promote",
        "send_order",
        "sign",
        "signer",
        "submit_order",
        "trading",
    }
)
_FORBIDDEN_MODULE_SEGMENTS = frozenset(
    {"cancel", "execution", "order", "private", "promotion", "signer", "trading"}
)


def _repository_artifact(
    repository_root: Path, path: str, path_class: PathClass
) -> RepositoryArtifact:
    module_name = _python_module_name(path)
    if module_name is None or path_class not in _PYTHON_SOURCE_CLASSES:
        return RepositoryArtifact(path, path_class)
    source_path = repository_root / Path(path)
    try:
        stat = source_path.stat()
    except OSError as error:
        raise GraphLoadError(f"cannot stat tracked Python artifact {path}: {error}") from error
    return _parsed_repository_artifact(
        str(source_path.resolve()), path, path_class, stat.st_mtime_ns, stat.st_size
    )


@lru_cache(maxsize=2048)
def _parsed_repository_artifact(
    source_path_text: str,
    path: str,
    path_class: PathClass,
    _mtime_ns: int,
    _size: int,
) -> RepositoryArtifact:
    source_path = Path(source_path_text)
    module_name = _python_module_name(path)
    assert module_name is not None
    try:
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=path)
    except (OSError, SyntaxError, UnicodeError) as error:
        raise GraphLoadError(
            f"cannot statically parse tracked Python artifact {path}: {error}"
        ) from error
    imports: set[str] = set()
    forbidden: set[str] = set()
    package = module_name if path.endswith("/__init__.py") else module_name.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
                forbidden.update(_forbidden_module_tokens(alias.name))
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(package, node.module, node.level)
            if resolved:
                imports.add(resolved)
                forbidden.update(_forbidden_module_tokens(resolved))
                for alias in node.names:
                    if alias.name != "*":
                        imports.add(f"{resolved}.{alias.name}")
                        forbidden.update(_forbidden_export_tokens(alias.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith("_"):
                forbidden.update(_forbidden_export_tokens(node.name))
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            for target in targets:
                if isinstance(target, ast.Name) and not target.id.startswith("_"):
                    forbidden.update(_forbidden_export_tokens(target.id))
    return RepositoryArtifact(
        path,
        path_class,
        module_name,
        tuple(sorted(imports)),
        tuple(sorted(forbidden)),
    )


def _python_module_name(path: str) -> str | None:
    normalized = path.replace("\\", "/")
    if not normalized.endswith(".py"):
        return None
    if normalized.startswith("src/"):
        normalized = normalized[4:]
    module = normalized[:-3].replace("/", ".")
    if module.endswith(".__init__"):
        module = module[: -len(".__init__")]
    return module or None


def _resolve_import_from(package: str, module: str | None, level: int) -> str:
    if level == 0:
        return module or ""
    parts = package.split(".") if package else []
    keep = max(0, len(parts) - level + 1)
    prefix = parts[:keep]
    if module:
        prefix.extend(module.split("."))
    return ".".join(prefix)


def _identifier_tokens(value: str) -> tuple[str, ...]:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", value).casefold()
    return tuple(token for token in re.split(r"[^a-z0-9]+", snake) if token)


def _forbidden_export_tokens(value: str) -> set[str]:
    lowered = value.casefold()
    tokens = _identifier_tokens(value)
    findings = {
        item
        for item in _FORBIDDEN_EXPORTED_NAMES
        if lowered == item or (item != "order" and lowered.startswith(f"{item}_"))
    }
    if (
        "order" in tokens
        and not {"book", "books"} & set(tokens)
        and (
            tokens == ("order",)
            or bool(
                {
                    "request",
                    "result",
                    "command",
                    "place",
                    "submit",
                    "cancel",
                    "send",
                }
                & set(tokens)
            )
        )
    ):
        findings.add("order")
    return findings


def _forbidden_module_tokens(value: str) -> set[str]:
    return set(value.casefold().split(".")) & _FORBIDDEN_MODULE_SEGMENTS


def _is_repository_artifact(path: str) -> bool:
    return True


_EXECUTION_PATHS = frozenset(
    {
        "multi_exchange_engine/domain/execution.py",
        "multi_exchange_engine/exchange/contracts.py",
        "multi_exchange_engine/exchange/hyperliquid.py",
        "multi_exchange_engine/exchange/lighter.py",
        "multi_exchange_engine/exchange/lighter_normalize.py",
        "scripts/probe_bybit_md.py",
        "scripts/probe_hl_md.py",
        "scripts/probe_lighter_md.py",
        "scripts/run_shadow_scan.py",
        "src/multi_exchange_engine/adapters/bybit/trading.py",
        "src/multi_exchange_engine/adapters/hyperliquid/trading.py",
        "src/multi_exchange_engine/adapters/lighter/trading.py",
        "src/multi_exchange_engine/core/execution/state_machine.py",
    }
)


def _classify_repository_path(path: str) -> PathClass:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1].casefold()
    if normalized.startswith((".agents/", "_bmad/", ".grok/", ".grok-stack/")):
        return PathClass.VENDORED_TOOLING
    if normalized in _ADAPTIVE_GROK_SHIMS:
        return PathClass.VENDORED_TOOLING
    if name.endswith(".ps1"):
        return PathClass.POWERSHELL
    stem = name.rsplit(".", 1)[0]
    execution_names = {"submit", "cancel", "sign", "signer", "send", "trading", "execution"}
    if (
        normalized in _EXECUTION_PATHS
        or normalized.startswith("experiments/")
        or normalized.startswith("src/multi_exchange_engine/")
        or (
            normalized.startswith(
                ("multi_exchange_engine/", "packages/", "services/", "app/", "future_runtime/")
            )
            and (stem in execution_names or "/execution/" in normalized)
        )
        or any(
            token in {"private", "trader", "trading", "signer", "order", "cancel", "execution"}
            for token in _identifier_tokens(stem)
        )
    ):
        return PathClass.EXECUTION_SOURCE
    if normalized.startswith("deploy/images/") and name.startswith("dockerfile"):
        return PathClass.BUILD_PACKAGING
    if (
        normalized == "scripts/promote-a2-candidate.sh"
        or normalized.startswith(("deploy/", "deployment/"))
        or (name.endswith(".sh") and stem in {"deploy", "promote", "promotion"})
    ):
        return PathClass.DEPLOYMENT_ENTRYPOINT
    if normalized.startswith((".github/workflows/", ".github/actions/")):
        return PathClass.WORKFLOW
    if normalized.startswith(("k8s/", "kubernetes/", "helm/", "charts/")):
        return PathClass.K8S_MANIFEST
    if name.endswith(".sh"):
        return PathClass.SHELL_SCRIPT
    if normalized.startswith("ci/claw/"):
        return PathClass.CONFIGURATION
    if name.endswith((".cmd", ".bat")):
        return PathClass.BATCH_SCRIPT
    if name.startswith("docker-compose") or name.startswith("compose."):
        return PathClass.COMPOSE
    if normalized.startswith("tests/") or "/tests/" in normalized or (
        normalized.startswith("internal/") and name.endswith("_test.go")
    ):
        return PathClass.TEST_SOURCE
    if normalized.startswith(("docs/", "engineering/changes/", "provenance/")) or (
        "/" not in normalized and name.endswith(".md")
    ):
        return PathClass.DOCUMENTATION
    if normalized.startswith("architecture/"):
        return PathClass.SCHEMA_MANIFEST
    if normalized.startswith("schemas/") and name.endswith(".json"):
        return PathClass.SCHEMA_MANIFEST
    if normalized.startswith("migrations/"):
        return PathClass.MIGRATION
    if normalized.startswith(("research/", "scripts/research/")) and name.endswith(".py"):
        return PathClass.TOOL_SOURCE
    if normalized.startswith("research/") or normalized.startswith("scripts/research/"):
        return PathClass.RESEARCH
    if normalized.startswith(("cmd/", "internal/")) or normalized == "go.mod":
        return PathClass.GO_SOURCE
    if normalized.startswith(("multi_exchange_engine/", "src/", "future_runtime/")):
        if "/fixtures/" in normalized:
            return PathClass.FIXTURE_DATA
        return PathClass.RUNTIME_SOURCE
    if normalized.startswith(("scripts/", "tools/")):
        return PathClass.TOOL_SOURCE
    if name.startswith("dockerfile") or normalized == ".dockerignore":
        return PathClass.BUILD_PACKAGING
    if normalized.startswith("config/") or normalized.startswith(".github/") or normalized in {
        ".env.example", ".gitignore", "pyproject.toml", "requirements.txt",
        "requirements-a2.txt", "Makefile",
    }:
        return PathClass.CONFIGURATION
    if normalized in {
        "packages/contracts/pyproject.toml",
        "packages/public-capture/pyproject.toml",
        "packages/readonly-analyzer/pyproject.toml",
    }:
        return PathClass.CONFIGURATION
    if (
        normalized.startswith("packages/contracts/src/mee_contracts/")
        and name.endswith(".py")
    ):
        return PathClass.RUNTIME_SOURCE
    if (
        normalized.startswith("packages/public-capture/src/mee_public_capture/")
        and name.endswith(".py")
    ):
        return PathClass.RUNTIME_SOURCE
    if (
        normalized.startswith("packages/readonly-analyzer/src/mee_readonly_analyzer/")
        and name.endswith(".py")
    ):
        return PathClass.RUNTIME_SOURCE
    return PathClass.UNKNOWN_TRACKED


def _phase_policy_times(
    documents: tuple[dict[str, Any], ...],
) -> tuple[tuple[Phase, str], ...]:
    values: dict[Phase, str] = {}
    for document in documents:
        raw = document.get("phase_policy_times", {})
        if not isinstance(raw, dict):
            raise GraphLoadError("phase_policy_times must be a mapping")
        for raw_phase, timestamp in raw.items():
            try:
                phase = Phase(raw_phase)
            except (TypeError, ValueError) as error:
                raise GraphLoadError("phase_policy_times contains an unrecognized phase") from error
            if phase in values:
                raise GraphLoadError(f"phase_policy_times duplicates {phase.value}")
            if not isinstance(timestamp, str) or not timestamp:
                raise GraphLoadError(
                    f"phase_policy_times.{phase.value} must be a non-empty string"
                )
            values[phase] = timestamp
    return tuple(sorted(values.items(), key=lambda item: _phase_sort_key(item[0])))


def _phase_sort_key(phase: Phase) -> int:
    return tuple(Phase).index(phase)


def _manifest_paths(
    root: Path, *, allow_single_file_fixture: bool
) -> tuple[Path, ...]:
    present = {path.name for path in root.glob("*.yaml")}
    expected = set(_REPOSITORY_MANIFESTS)
    explicit_fixture_path = "tests/fixtures/graph" in root.as_posix()
    if (allow_single_file_fixture or explicit_fixture_path) and present == {"architecture.yaml"}:
        return (root / "architecture.yaml",)
    missing = sorted(expected - present)
    unexpected = sorted(present - expected)
    details = [
        *(f"missing: {', '.join(missing)}" for _ in [None] if missing),
        *(f"unexpected: {', '.join(unexpected)}" for _ in [None] if unexpected),
    ]
    if details:
        raise GraphLoadError(f"repository manifest set is invalid ({'; '.join(details)})")
    return tuple(root / name for name in _REPOSITORY_MANIFESTS)


def _load_document(path: Path) -> dict[str, Any]:
    try:
        stat = path.stat()
    except OSError as error:
        raise GraphLoadError(f"cannot load {path}: {error}") from error
    return _load_document_cached(
        str(path.resolve()), stat.st_mtime_ns, stat.st_size
    )


@lru_cache(maxsize=256)
def _load_document_cached(
    path_text: str, _mtime_ns: int, _size: int
) -> dict[str, Any]:
    path = Path(path_text)
    try:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise GraphLoadError(f"cannot load {path}: {error}") from error
    if not isinstance(document, dict):
        raise GraphLoadError("manifest root must be a mapping")
    _closed_keys(document, _ROOT_KEYS, "manifest")
    if document.get("manifest_version") not in {1, 2}:
        raise GraphLoadError("manifest_version must be 1 or 2")
    return document


def _list(document: dict[str, Any], key: str) -> list[Any]:
    value = document.get(key, [])
    if not isinstance(value, list):
        raise GraphLoadError(f"{key} must be a list")
    return value


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GraphLoadError(f"{label} must be a mapping")
    return value


def _closed_keys(value: dict[str, Any], allowed: set[str], label: str) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise GraphLoadError(f"{label} has unsupported keys: {', '.join(unexpected)}")


def _required_string(value: dict[str, Any], key: str, label: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise GraphLoadError(f"{label}.{key} must be a non-empty string")
    return item


def _node(value: Any, index: int) -> GraphNode:
    label = f"nodes[{index}]"
    item = _mapping(value, label)
    _closed_keys(item, _NODE_KEYS, label)
    requirements = item.get("requirements", [])
    if not isinstance(requirements, list) or any(
        not isinstance(requirement, str) or not requirement for requirement in requirements
    ):
        raise GraphLoadError(f"{label}.requirements must be a list of non-empty strings")
    active = item.get("active", True)
    if not isinstance(active, bool):
        raise GraphLoadError(f"{label}.active must be a boolean")
    requirement_id = item.get("requirement_id")
    requirement_class = item.get("requirement_class")
    approval = item.get("approval")
    classifications = item.get("classifications", [])
    canonical_for = item.get("canonical_for")
    replacement = item.get("replacement")
    expiry_utc = item.get("expiry_utc")
    removal_gate = item.get("removal_gate")
    rollback_node = item.get("rollback_node")
    expiry_conflict = item.get("expiry_conflict")
    required_from = item.get("required_from")
    required_lifecycle = item.get("required_lifecycle")
    profile = item.get("profile")
    capabilities = item.get("capabilities", [])
    shared_proof = item.get("shared_proof", False)
    if requirement_id is not None and (not isinstance(requirement_id, str) or not requirement_id):
        raise GraphLoadError(f"{label}.requirement_id must be a non-empty string")
    if requirement_class is not None:
        try:
            requirement_class = RequirementClass(requirement_class)
        except (TypeError, ValueError) as error:
            raise GraphLoadError(f"{label}.requirement_class is not recognized") from error
    if canonical_for is not None and (not isinstance(canonical_for, str) or not canonical_for):
        raise GraphLoadError(f"{label}.canonical_for must be a non-empty string")
    if approval is not None and (not isinstance(approval, str) or not approval):
        raise GraphLoadError(f"{label}.approval must be a non-empty string")
    if (
        not isinstance(classifications, list)
        or any(not isinstance(classification, str) or not classification for classification in classifications)
        or len(set(classifications)) != len(classifications)
    ):
        raise GraphLoadError(f"{label}.classifications must be a unique list of non-empty strings")
    try:
        classifications = tuple(Classification(classification) for classification in classifications)
    except ValueError as error:
        raise GraphLoadError(f"{label}.classifications contains an unrecognized value") from error
    if profile is not None and (not isinstance(profile, str) or not profile):
        raise GraphLoadError(f"{label}.profile must be a non-empty string")
    for key, field in (
        ("replacement", replacement),
        ("expiry_utc", expiry_utc),
        ("removal_gate", removal_gate),
        ("rollback_node", rollback_node),
        ("expiry_conflict", expiry_conflict),
    ):
        if field is not None and (not isinstance(field, str) or not field):
            raise GraphLoadError(f"{label}.{key} must be a non-empty string")
    if (
        not isinstance(capabilities, list)
        or any(not isinstance(capability, str) or not capability for capability in capabilities)
        or len(set(capabilities)) != len(capabilities)
    ):
        raise GraphLoadError(f"{label}.capabilities must be a unique list of non-empty strings")
    if not isinstance(shared_proof, bool):
        raise GraphLoadError(f"{label}.shared_proof must be a boolean")
    if required_from is not None:
        try:
            required_from = Phase(required_from)
        except ValueError as error:
            raise GraphLoadError(f"{label}.required_from is not recognized") from error
        if required_lifecycle is None:
            required_lifecycle = Lifecycle.IMPLEMENTED
        else:
            try:
                required_lifecycle = Lifecycle(required_lifecycle)
            except ValueError as error:
                raise GraphLoadError(f"{label}.required_lifecycle is not recognized") from error
    elif required_lifecycle is not None:
        raise GraphLoadError(f"{label}.required_lifecycle requires required_from")
    try:
        lifecycle = Lifecycle(_required_string(item, "lifecycle", label))
    except ValueError as error:
        raise GraphLoadError(f"{label}.lifecycle is not recognized") from error
    try:
        kind = NodeKind(_required_string(item, "kind", label))
    except ValueError as error:
        raise GraphLoadError(f"{label}.kind is not recognized") from error
    return GraphNode(
        id=_required_string(item, "id", label),
        kind=kind,
        owner=_required_string(item, "owner", label),
        lifecycle=lifecycle,
        active=active,
        requirements=tuple(requirements),
        requirement_id=requirement_id,
        requirement_class=requirement_class,
        approval=approval,
        classifications=classifications,
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


def _edge(value: Any, index: int) -> GraphEdge:
    label = f"edges[{index}]"
    item = _mapping(value, label)
    _closed_keys(item, _EDGE_KEYS, label)
    proof_for = item.get("proof_for")
    non_proof_reason = item.get("non_proof_reason")
    if proof_for is not None and (not isinstance(proof_for, str) or not proof_for):
        raise GraphLoadError(f"{label}.proof_for must be one non-empty stable requirement ID")
    if non_proof_reason is not None and (
        not isinstance(non_proof_reason, str) or not non_proof_reason
    ):
        raise GraphLoadError(f"{label}.non_proof_reason must be a non-empty string")
    return GraphEdge(
        _required_string(item, "from", label),
        _required_string(item, "to", label),
        _required_string(item, "kind", label),
        proof_for,
        non_proof_reason,
    )


def _runtime_dependency(value: Any, index: int) -> RuntimeDependency:
    label = f"runtime_dependencies[{index}]"
    item = _mapping(value, label)
    _closed_keys(item, _RUNTIME_KEYS, label)
    return RuntimeDependency(_required_string(item, "from", label), _required_string(item, "to", label))


def _receipt(value: Any, index: int) -> ReceiptRequirement:
    label = f"receipts[{index}]"
    item = _mapping(value, label)
    _closed_keys(item, _RECEIPT_KEYS, label)
    try:
        required_from = Phase(_required_string(item, "required_from", label))
    except ValueError as error:
        raise GraphLoadError(f"{label}.required_from is not recognized") from error
    status = _required_string(item, "status", label)
    if status not in {"prospective", "realized"}:
        raise GraphLoadError(f"{label}.status must be prospective or realized")
    if status == "prospective":
        if _REALIZED_RECEIPT_KEYS & set(item):
            raise GraphLoadError(f"{label} prospective receipt must not carry realized identity")
        return ReceiptRequirement(
            _required_string(item, "node", label), required_from, _required_string(item, "evidence_type", label), status
        )
    missing = sorted(_REALIZED_RECEIPT_KEYS - set(item))
    if missing:
        raise GraphLoadError(f"{label} realized receipt requires: {', '.join(missing)}")
    content_hash = _hash(item, "content_hash", label, 64)
    source_sha = _hash(item, "source_sha", label, 40)
    verification_hash = _hash(item, "verification_hash", label, 64)
    produced_at = _utc_timestamp(item, "produced_at", label)
    verified_at = _utc_timestamp(item, "verified_at", label)
    if produced_at > verified_at:
        raise GraphLoadError(f"{label}.produced_at must not be after verified_at")
    return ReceiptRequirement(
        _required_string(item, "node", label),
        required_from,
        _required_string(item, "evidence_type", label),
        status,
        content_hash,
        source_sha,
        _required_string(item, "producer", label),
        item["produced_at"],
        _required_string(item, "verifier", label),
        verification_hash,
        item["verified_at"],
    )


def _hash(item: dict[str, Any], key: str, label: str, length: int) -> str:
    value = _required_string(item, key, label)
    pattern = _HEX_64 if length == 64 else _HEX_40
    if not pattern.fullmatch(value) or len(set(value)) == 1:
        raise GraphLoadError(f"{label}.{key} must be a non-placeholder {length}-hex value")
    return value


def _utc_timestamp(item: dict[str, Any], key: str, label: str) -> datetime:
    value = _required_string(item, key, label)
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise GraphLoadError(f"{label}.{key} must be a UTC timestamp")
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise GraphLoadError(f"{label}.{key} must be a UTC timestamp") from error


def _validate_receipt_bindings(
    receipts: tuple[ReceiptRequirement, ...], nodes: tuple[GraphNode, ...]
) -> None:
    active_nodes = {node.id for node in nodes if node.active}
    content_subjects: dict[str, str] = {}
    verification_subjects: dict[str, str] = {}
    for receipt in receipts:
        if receipt.status != "realized":
            continue
        for role, node_id in (("producer", receipt.producer), ("verifier", receipt.verifier)):
            if node_id not in active_nodes:
                raise GraphLoadError(f"{role} must reference an active node")
        for field, value, subjects in (
            ("content_hash", receipt.content_hash, content_subjects),
            ("verification_hash", receipt.verification_hash, verification_subjects),
        ):
            if value in subjects and subjects[value] != receipt.node_id:
                raise GraphLoadError(f"{field} is reused for another receipt subject")
            subjects[value] = receipt.node_id


def load_receipt_validation_context(
    *, evidence_cutoff_utc: str, expected_source_sha: str, registry_path: Path
) -> ReceiptValidationContext:
    """Load caller-supplied diagnostic inputs; they cannot authorize realization."""
    cutoff_document = {"evidence_cutoff_utc": evidence_cutoff_utc}
    _utc_timestamp(cutoff_document, "evidence_cutoff_utc", "receipt validation context")
    source_document = {"source_sha": expected_source_sha}
    _hash(source_document, "source_sha", "receipt validation context", 40)
    try:
        document = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GraphLoadError(f"cannot load verified receipt registry: {error}") from error
    if not isinstance(document, dict):
        raise GraphLoadError("verified receipt registry must be a mapping")
    _closed_keys(document, _REGISTRY_ROOT_KEYS, "verified receipt registry")
    if document.get("registry_version") != 1:
        raise GraphLoadError("verified receipt registry version must be 1")
    values = document.get("receipts")
    if not isinstance(values, list):
        raise GraphLoadError("verified receipt registry receipts must be a list")
    entries = tuple(_registry_entry(value, index) for index, value in enumerate(values))
    return ReceiptValidationContext(evidence_cutoff_utc, expected_source_sha, entries)


def _registry_entry(value: Any, index: int) -> VerifiedReceiptRegistryEntry:
    label = f"verified receipt registry.receipts[{index}]"
    item = _mapping(value, label)
    _closed_keys(item, _REGISTRY_ENTRY_KEYS, label)
    missing = sorted(_REGISTRY_ENTRY_KEYS - set(item))
    if missing:
        raise GraphLoadError(f"{label} requires: {', '.join(missing)}")
    produced_at = _utc_timestamp(item, "produced_at", label)
    verified_at = _utc_timestamp(item, "verified_at", label)
    if produced_at > verified_at:
        raise GraphLoadError(f"{label}.produced_at must not be after verified_at")
    return VerifiedReceiptRegistryEntry(
        _required_string(item, "node", label),
        _hash(item, "content_hash", label, 64),
        _hash(item, "source_sha", label, 40),
        _required_string(item, "producer", label),
        item["produced_at"],
        _required_string(item, "verifier", label),
        _hash(item, "verification_hash", label, 64),
        item["verified_at"],
    )
