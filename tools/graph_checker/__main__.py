"""Command-line interface for deterministic architecture-graph validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .checker import check_graph
from .loader import GraphLoadError, load_graph, load_receipt_validation_context
from .model import Diagnostic, GraphNode, Lifecycle, Phase

_M0_DECLARED_CONFLICT_ALLOWLIST = frozenset(
    {
        GraphNode(
            "conflict:go-stage-a-build",
            "Conflict",
            "runtime",
            Lifecycle.DECLARED,
            requirements=("ARCH-GO-001", "ARCH-GO-004"),
        ),
        GraphNode(
            "conflict:ci-008-host-docker-boundary",
            "Conflict",
            "ci",
            Lifecycle.DECLARED,
            requirements=("CI-003", "CI-005", "CI-008", "SEC-004", "SEC-005"),
        ),
        GraphNode(
            "conflict:a2-private-production-image",
            "Conflict",
            "security",
            Lifecycle.DECLARED,
            requirements=("ARCH-003", "SEC-003"),
        ),
        GraphNode(
            "conflict:retained-promotion-entrypoint",
            "Conflict",
            "release",
            Lifecycle.DECLARED,
            requirements=("CI-007", "SEC-003"),
        ),
        GraphNode(
            "conflict:trusted-controller-authority",
            "Conflict",
            "ci",
            Lifecycle.DECLARED,
            requirements=(
                "CI-001",
                "CI-003",
                "CI-005",
                "CI-008",
                "SEC-004",
                "SEC-005",
            ),
        ),
        GraphNode(
            "conflict:controller-self-protection",
            "Conflict",
            "security",
            Lifecycle.DECLARED,
            requirements=("CI-008", "SEC-004", "SEC-005"),
        ),
        GraphNode(
            "conflict:full-graph-suite-controller-gate",
            "Conflict",
            "ci",
            Lifecycle.DECLARED,
            requirements=("GRAPH-006", "GRAPH-008", "CI-005"),
        ),
    }
)


def _is_m0_waived_conflict(graph: object, node_id: str | None) -> bool:
    if node_id is None:
        return False
    try:
        node = graph.node(node_id)
    except KeyError:
        return False
    return node in _M0_DECLARED_CONFLICT_ALLOWLIST


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-root", type=Path, required=True)
    parser.add_argument("--phase", type=Phase, choices=tuple(Phase), required=True)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--allow-declared-conflicts", action="store_true")
    parser.add_argument("--single-file-fixture", action="store_true")
    parser.add_argument("--evidence-cutoff-utc")
    parser.add_argument("--expected-source-sha")
    parser.add_argument("--verified-receipt-registry", type=Path)
    return parser


def _as_json(diagnostics: tuple[Diagnostic, ...]) -> str:
    return json.dumps(
        [
            {
                "code": item.code,
                "node_id": item.node_id,
                "path": list(item.path),
                "requirement_ids": list(item.requirement_ids),
                "message": item.message,
            }
            for item in diagnostics
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _as_text(diagnostics: tuple[Diagnostic, ...], phase: Phase) -> str:
    if not diagnostics:
        return f"graph check passed: phase={phase.value} diagnostics=0"
    return "\n".join(
        " ".join(
            part
            for part in (item.code, item.node_id or "-", " -> ".join(item.path), item.message)
            if part
        )
        for item in diagnostics
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.allow_declared_conflicts and args.phase is not Phase.PRECOMMIT:
        print("--allow-declared-conflicts is legal only with --phase precommit")
        return 2
    try:
        graph = load_graph(
            args.manifest_root,
            allow_single_file_fixture=args.single_file_fixture,
        )
        receipt_context = None
        if any(receipt.status == "realized" for receipt in graph.receipts):
            if (
                args.evidence_cutoff_utc is None
                or args.expected_source_sha is None
                or args.verified_receipt_registry is None
            ):
                raise GraphLoadError("realized receipts require diagnostic cutoff, source SHA, and registry")
            receipt_context = load_receipt_validation_context(
                evidence_cutoff_utc=args.evidence_cutoff_utc,
                expected_source_sha=args.expected_source_sha,
                registry_path=args.verified_receipt_registry,
            )
        diagnostics = check_graph(graph, args.phase, receipt_context)
    except (GraphLoadError, ValueError) as error:
        print(f"malformed graph input: {error}")
        return 2
    print(_as_json(diagnostics) if args.format == "json" else _as_text(diagnostics, args.phase))
    blocking = tuple(
        item
        for item in diagnostics
        if not (
            args.allow_declared_conflicts
            and item.code == "DECLARED_CONFLICT"
            and _is_m0_waived_conflict(graph, item.node_id)
        )
    )
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
