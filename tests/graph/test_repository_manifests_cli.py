"""Repository authority manifests and their command-line validation boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import load_graph
from tools.graph_checker.model import Lifecycle, Phase

ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURE = ROOT / "architecture"


def test_repository_manifest_set_loads_in_deterministic_order() -> None:
    first = load_graph(ARCHITECTURE)
    second = load_graph(ARCHITECTURE)

    assert first == second
    assert [node.id for node in first.nodes] == sorted(node.id for node in first.nodes)
    assert {
        "conflict:duplicate-python-namespace",
        "conflict:go-stage-a-build",
    }.issubset({node.id for node in first.nodes})
    assert first.node("conflict:duplicate-python-namespace").lifecycle is Lifecycle.RETIRED
    assert first.node("conflict:duplicate-python-namespace").active is False


def test_active_authority_implementations_have_a_prospective_evidence_path() -> None:
    graph = load_graph(ARCHITECTURE)
    by_source: dict[str, set[str]] = {}
    kinds = {node.id: node.kind for node in graph.nodes}
    for edge in graph.edges:
        by_source.setdefault(edge.from_id, set()).add(edge.to_id)

    def reachable_kinds(node_id: str) -> set[str]:
        pending = [node_id]
        seen: set[str] = set()
        found: set[str] = set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            found.add(kinds[current])
            pending.extend(by_source.get(current, ()))
        return found

    authority_kinds = {"SourceModule", "ADR", "Configuration"}
    for node in graph.nodes:
        if node.active and node.kind in authority_kinds:
            assert {"TestOrEval", "ClawGate", "Artifact", "Evidence", "Rollback"} <= reachable_kinds(
                node.id
            )


def test_cli_reports_declared_baseline_conflicts_without_blocking_when_allowed() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            "architecture",
            "--phase",
            "precommit",
            "--format",
            "json",
            "--allow-declared-conflicts",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    diagnostics = json.loads(completed.stdout)
    assert [item["node_id"] for item in diagnostics] == [
        "conflict:a2-private-production-image",
        "conflict:ci-008-host-docker-boundary",
        "conflict:controller-self-protection",
        "conflict:full-graph-suite-controller-gate",
        "conflict:go-stage-a-build",
        "conflict:retained-promotion-entrypoint",
        "conflict:trusted-controller-authority",
    ]
    assert {item["code"] for item in diagnostics} == {"DECLARED_CONFLICT"}


def test_merge_stays_fail_closed_on_declared_conflicts_and_untrusted_policy_time() -> None:
    graph = load_graph(ARCHITECTURE)
    diagnostics = check_graph(graph, Phase.MERGE)
    by_code: dict[str, list[str | None]] = {}
    for item in diagnostics:
        by_code.setdefault(item.code, []).append(item.node_id)

    assert by_code["DECLARED_CONFLICT"] == [
        "conflict:a2-private-production-image",
        "conflict:ci-008-host-docker-boundary",
        "conflict:controller-self-protection",
        "conflict:full-graph-suite-controller-gate",
        "conflict:go-stage-a-build",
        "conflict:retained-promotion-entrypoint",
        "conflict:trusted-controller-authority",
    ]
    assert by_code["PHASE_POLICY_TIME_TRUST_MISSING"] == [None]
    assert set(by_code) == {"DECLARED_CONFLICT", "PHASE_POLICY_TIME_TRUST_MISSING"}


def test_ci_008_disposable_pr_sandbox_is_declared_with_a_blocking_resolution_path() -> None:
    graph = load_graph(ARCHITECTURE)
    node_ids = {node.id for node in graph.nodes}
    assert {
        "configuration:claw-workspace-isolation",
        "configuration:claw-disposable-pr-sandbox",
        "conflict:ci-008-host-docker-boundary",
    } <= node_ids
    current_boundary = graph.node("configuration:claw-workspace-isolation")
    resolution = graph.node("configuration:claw-disposable-pr-sandbox")
    conflict = graph.node("conflict:ci-008-host-docker-boundary")

    assert current_boundary.lifecycle is Lifecycle.DECLARED
    assert resolution.lifecycle is Lifecycle.DECLARED
    assert conflict.active is True
    assert conflict.kind == "Conflict"
    assert "CI-008" in conflict.requirements
    assert graph.has_edge(
        "conflict:ci-008-host-docker-boundary",
        "resolved_by",
        "configuration:claw-disposable-pr-sandbox",
    )
    assert graph.has_edge(
        "configuration:claw-disposable-pr-sandbox",
        "specified_by",
        "contract:architecture-authority",
    )
    assert all(receipt.status == "prospective" for receipt in graph.receipts)


def test_cli_uses_exit_two_for_malformed_input() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            "tests/fixtures/graph/valid",
            "--phase",
            "not-a-phase",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2


def test_repository_script_runs_from_the_repository_root() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "scripts/check-architecture-graph.py",
            "--manifest-root",
            "architecture",
            "--phase",
            "precommit",
            "--allow-declared-conflicts",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
