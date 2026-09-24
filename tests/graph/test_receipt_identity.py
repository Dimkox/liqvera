"""Fail-closed structural identity requirements for realized receipts."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import GraphLoadError, load_graph, load_receipt_validation_context
from tools.graph_checker.model import Phase, ReceiptRequirement


CONTENT_HASH = "0123456789abcdef" * 4
VERIFICATION_HASH = "fedcba9876543210" * 4
SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"


def _receipt(
    *,
    node: str = "gate:one",
    content_hash: str = CONTENT_HASH,
    verification_hash: str = VERIFICATION_HASH,
    producer: str = "module:producer",
    verifier: str = "module:verifier",
    produced_at: str = "2026-08-11T12:00:00Z",
    verified_at: str = "2026-08-11T12:01:00Z",
) -> str:
    return f"""\
  - node: {node}
    required_from: merge
    evidence_type: ClawValidationReceipt
    status: realized
    content_hash: {content_hash}
    source_sha: {SOURCE_SHA}
    producer: {producer}
    produced_at: "{produced_at}"
    verifier: {verifier}
    verification_hash: {verification_hash}
    verified_at: "{verified_at}"
"""


def _manifest(receipts: str) -> str:
    return f"""\
manifest_version: 1
nodes:
  - {{id: gate:one, kind: ClawGate, owner: ci, lifecycle: DECLARED}}
  - {{id: gate:two, kind: ClawGate, owner: ci, lifecycle: DECLARED}}
  - {{id: module:producer, kind: SourceModule, owner: ci, lifecycle: IMPLEMENTED}}
  - {{id: module:verifier, kind: SourceModule, owner: ci, lifecycle: IMPLEMENTED}}
receipts:
{receipts}"""


def _write_manifest(tmp_path: Path, receipts: str) -> Path:
    path = tmp_path / "architecture.yaml"
    path.write_text(_manifest(receipts), encoding="utf-8")
    return tmp_path


def test_realized_receipt_requires_bound_identity_fields(tmp_path: Path) -> None:
    receipt = """\
  - node: gate:one
    required_from: merge
    evidence_type: ClawValidationReceipt
    status: realized
"""

    with pytest.raises(GraphLoadError, match="realized receipt requires"):
        load_graph(_write_manifest(tmp_path, receipt), allow_single_file_fixture=True)


def test_realized_receipt_rejects_placeholder_content_hash(tmp_path: Path) -> None:
    with pytest.raises(GraphLoadError, match="content_hash"):
        load_graph(
            _write_manifest(tmp_path, _receipt(content_hash="0" * 64)),
            allow_single_file_fixture=True,
        )


def test_realized_receipt_rejects_unknown_verifier(tmp_path: Path) -> None:
    with pytest.raises(GraphLoadError, match="verifier must reference an active node"):
        load_graph(
            _write_manifest(tmp_path, _receipt(verifier="module:unknown")),
            allow_single_file_fixture=True,
        )


def test_realized_receipt_rejects_produced_after_verified(tmp_path: Path) -> None:
    with pytest.raises(GraphLoadError, match="produced_at must not be after verified_at"):
        load_graph(
            _write_manifest(
                tmp_path,
                _receipt(
                    produced_at="2026-08-11T12:02:00Z",
                    verified_at="2026-08-11T12:01:00Z",
                ),
            ),
            allow_single_file_fixture=True,
        )


def test_realized_receipt_rejects_hash_copied_to_another_subject(tmp_path: Path) -> None:
    copied = _receipt() + _receipt(node="gate:two")

    with pytest.raises(GraphLoadError, match="content_hash is reused"):
        load_graph(_write_manifest(tmp_path, copied), allow_single_file_fixture=True)


def test_bound_realized_receipt_satisfies_the_phase_gate(tmp_path: Path) -> None:
    graph = load_graph(
        _write_manifest(tmp_path, _receipt()), allow_single_file_fixture=True
    )
    registry = tmp_path / "verified-receipts.json"
    registry.write_text(
        json.dumps(
            {
                "registry_version": 1,
                "receipts": [
                    {
                        "node": "gate:one",
                        "content_hash": CONTENT_HASH,
                        "source_sha": SOURCE_SHA,
                        "producer": "module:producer",
                        "produced_at": "2026-08-11T12:00:00Z",
                        "verifier": "module:verifier",
                        "verification_hash": VERIFICATION_HASH,
                        "verified_at": "2026-08-11T12:01:00Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    trust = load_receipt_validation_context(
        evidence_cutoff_utc="2026-08-11T12:02:00Z",
        expected_source_sha=SOURCE_SHA,
        registry_path=registry,
    )

    diagnostics = check_graph(graph, Phase.MERGE, trust)

    assert "RECEIPT_TRUST_ANCHOR_UNAVAILABLE" in {item.code for item in diagnostics}


def test_manually_constructed_unbound_realized_receipt_cannot_satisfy_gate() -> None:
    graph = load_graph(Path("tests/fixtures/graph/valid"))
    graph = replace(
        graph,
        policy_times_trusted=True,
        receipts=(ReceiptRequirement("gate:graph-check", Phase.MERGE, "ClawValidationReceipt", "realized"),),
    )

    diagnostics = check_graph(graph, Phase.MERGE)

    assert {"RECEIPT_IDENTITY_INCOMPLETE", "RECEIPT_TRUST_ANCHOR_UNAVAILABLE"} == {
        item.code for item in diagnostics
    }


def test_manually_constructed_realized_receipt_rejects_unknown_verifier() -> None:
    graph = load_graph(Path("tests/fixtures/graph/valid"))
    graph = replace(
        graph,
        policy_times_trusted=True,
        receipts=(
            ReceiptRequirement(
                "gate:graph-check",
                Phase.MERGE,
                "ClawValidationReceipt",
                "realized",
                CONTENT_HASH,
                SOURCE_SHA,
                "module:graph-checker",
                "2026-08-11T12:00:00Z",
                "module:unknown",
                VERIFICATION_HASH,
                "2026-08-11T12:01:00Z",
            ),
        ),
    )

    diagnostics = check_graph(graph, Phase.MERGE)

    assert {"RECEIPT_IDENTITY_NODE_INVALID", "RECEIPT_TRUST_ANCHOR_UNAVAILABLE"} == {
        item.code for item in diagnostics
    }
