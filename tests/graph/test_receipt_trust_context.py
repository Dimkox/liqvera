"""Caller-supplied receipt validation data never authorizes M0 realization."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import GraphLoadError, load_graph, load_receipt_validation_context
from tools.graph_checker.model import Phase, ReceiptRequirement


CONTENT_HASH = "0123456789abcdef" * 4
VERIFICATION_HASH = "fedcba9876543210" * 4
SOURCE_SHA = "0123456789abcdef0123456789abcdef01234567"
ROOT = Path(__file__).resolve().parents[2]


def _receipt(**changes: str) -> ReceiptRequirement:
    values = {
        "node_id": "gate:graph-check",
        "required_from": Phase.MERGE,
        "evidence_type": "ClawValidationReceipt",
        "status": "realized",
        "content_hash": CONTENT_HASH,
        "source_sha": SOURCE_SHA,
        "producer": "module:graph-checker",
        "produced_at": "2026-08-11T12:00:00Z",
        "verifier": "module:graph-checker",
        "verification_hash": VERIFICATION_HASH,
        "verified_at": "2026-08-11T12:01:00Z",
    }
    values.update(changes)
    return ReceiptRequirement(**values)


def _graph(receipt: ReceiptRequirement) -> object:
    return replace(
        load_graph(Path("tests/fixtures/graph/valid")),
        receipts=(receipt,),
        policy_times_trusted=True,
    )


def _registry_entry(receipt: ReceiptRequirement) -> dict[str, str]:
    return {
        "node": receipt.node_id,
        "content_hash": receipt.content_hash or "",
        "source_sha": receipt.source_sha or "",
        "producer": receipt.producer or "",
        "produced_at": receipt.produced_at or "",
        "verifier": receipt.verifier or "",
        "verification_hash": receipt.verification_hash or "",
        "verified_at": receipt.verified_at or "",
    }


def _validation_context(tmp_path: Path, receipt: ReceiptRequirement, **changes: object) -> object:
    registry = {"registry_version": 1, "receipts": [_registry_entry(receipt)]}
    registry.update(changes.pop("registry", {}))
    path = tmp_path / "verified-receipts.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    return load_receipt_validation_context(
        evidence_cutoff_utc=changes.pop("evidence_cutoff_utc", "2026-08-11T12:02:00Z"),
        expected_source_sha=changes.pop("expected_source_sha", SOURCE_SHA),
        registry_path=path,
    )


def test_realized_receipt_needs_explicit_validation_context() -> None:
    diagnostics = check_graph(_graph(_receipt()), Phase.MERGE)

    assert "RECEIPT_TRUST_ANCHOR_UNAVAILABLE" in {item.code for item in diagnostics}


def test_forged_matching_registry_and_late_cutoff_still_needs_m0_trust_anchor(tmp_path: Path) -> None:
    receipt = _receipt()
    diagnostics = check_graph(
        _graph(receipt),
        Phase.MERGE,
        _validation_context(tmp_path, receipt, evidence_cutoff_utc="2099-01-01T00:00:00Z"),
    )

    assert [item.code for item in diagnostics] == ["RECEIPT_TRUST_ANCHOR_UNAVAILABLE"]


def test_receipt_trust_anchor_is_declared_prospective_rollback_chain() -> None:
    graph = load_graph(ROOT / "architecture")

    assert graph.node("contract:receipt-trust-anchor-v1").lifecycle.value == "DECLARED"
    assert "contract:receipt-trust-anchor-v1" not in {receipt.node_id for receipt in graph.receipts}
    assert {
        ("requirement:CI-003", "contract:receipt-trust-anchor-v1"),
        ("requirement:SEC-005", "contract:receipt-trust-anchor-v1"),
        ("contract:receipt-trust-anchor-v1", "module:graph-checker"),
        ("module:graph-checker", "dataflow:capture-to-frozen-package"),
        ("dataflow:capture-to-frozen-package", "test:receipt-trust-anchor-v1"),
        ("test:receipt-trust-anchor-v1", "gate:receipt-trust-anchor-v1"),
        ("gate:receipt-trust-anchor-v1", "artifact:receipt-trust-anchor-v1"),
        ("artifact:receipt-trust-anchor-v1", "evidence-plan:receipt-trust-anchor-v1"),
        ("evidence-plan:receipt-trust-anchor-v1", "rollback:graph-authority"),
    } <= {(edge.from_id, edge.to_id) for edge in graph.edges}


def test_context_rejects_receipt_after_injected_cutoff(tmp_path: Path) -> None:
    receipt = _receipt(produced_at="2099-01-01T00:00:00Z", verified_at="2099-01-01T00:01:00Z")
    trust = _validation_context(tmp_path, receipt, evidence_cutoff_utc="2026-08-11T12:02:00Z")

    diagnostics = check_graph(_graph(receipt), Phase.MERGE, trust)

    assert {"RECEIPT_TRUST_CUTOFF_EXCEEDED", "RECEIPT_TRUST_ANCHOR_UNAVAILABLE"} <= {
        item.code for item in diagnostics
    }


def test_context_rejects_expected_source_sha_mismatch(tmp_path: Path) -> None:
    receipt = _receipt()
    trust = _validation_context(tmp_path, receipt, expected_source_sha="abcdef0123456789abcdef0123456789abcdef01")

    diagnostics = check_graph(_graph(receipt), Phase.MERGE, trust)

    assert {"RECEIPT_TRUST_SOURCE_SHA_MISMATCH", "RECEIPT_TRUST_ANCHOR_UNAVAILABLE"} <= {
        item.code for item in diagnostics
    }


def test_context_rejects_absent_or_duplicate_registry_match(tmp_path: Path) -> None:
    receipt = _receipt()
    absent = _validation_context(tmp_path, receipt, registry={"receipts": []})
    duplicate = _validation_context(
        tmp_path,
        receipt,
        registry={"receipts": [_registry_entry(receipt), _registry_entry(receipt)]},
    )

    for context in (absent, duplicate):
        assert {
            "RECEIPT_TRUST_REGISTRY_MATCH_INVALID",
            "RECEIPT_TRUST_ANCHOR_UNAVAILABLE",
        } <= {item.code for item in check_graph(_graph(receipt), Phase.MERGE, context)}


def test_context_rejects_registry_field_mismatch(tmp_path: Path) -> None:
    receipt = _receipt()
    trust = _validation_context(
        tmp_path,
        receipt,
        registry={"receipts": [{**_registry_entry(receipt), "producer": "module:other"}]},
    )

    diagnostics = check_graph(_graph(receipt), Phase.MERGE, trust)

    assert {
        "RECEIPT_TRUST_REGISTRY_MATCH_INVALID",
        "RECEIPT_TRUST_ANCHOR_UNAVAILABLE",
    } <= {item.code for item in diagnostics}


def test_registry_is_closed_and_rejects_self_asserted_cutoff(tmp_path: Path) -> None:
    path = tmp_path / "verified-receipts.json"
    path.write_text(
        json.dumps({"registry_version": 1, "evidence_cutoff_utc": "2099-01-01T00:00:00Z", "receipts": []}),
        encoding="utf-8",
    )

    with pytest.raises(GraphLoadError, match="unsupported keys"):
        load_receipt_validation_context(
            evidence_cutoff_utc="2026-08-11T12:02:00Z",
            expected_source_sha=SOURCE_SHA,
            registry_path=path,
        )


def test_cli_requires_all_validation_inputs_for_realized_receipts(tmp_path: Path) -> None:
    receipt = _receipt()
    manifest = tmp_path / "architecture.yaml"
    manifest.write_text(
        f"""\
manifest_version: 1
nodes:
  - {{id: gate:graph-check, kind: ClawGate, owner: ci, lifecycle: DECLARED}}
  - {{id: module:graph-checker, kind: SourceModule, owner: ci, lifecycle: IMPLEMENTED}}
receipts:
  - node: {receipt.node_id}
    required_from: merge
    evidence_type: {receipt.evidence_type}
    status: realized
    content_hash: {receipt.content_hash}
    source_sha: {receipt.source_sha}
    producer: {receipt.producer}
    produced_at: \"{receipt.produced_at}\"
    verifier: {receipt.verifier}
    verification_hash: {receipt.verification_hash}
    verified_at: \"{receipt.verified_at}\"
""",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "tools.graph_checker",
            "--manifest-root",
            str(tmp_path),
            "--phase",
            "merge",
            "--single-file-fixture",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "realized receipts require diagnostic cutoff" in completed.stdout
