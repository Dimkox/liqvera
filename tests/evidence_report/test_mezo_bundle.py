"""Mezo sidecars remain bounded, optional, request-bound and offline reproducible."""

import json
from pathlib import Path
from uuid import UUID

import pytest
from liqvera_contracts.exact import ExactDecimal
from liqvera_evidence_report.evidence_bundle import build_bundle, verify_bundle_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected
from liqvera_evidence_report.report import ReportRequest, build_report
from liqvera_public_capture.evidence_capture import (
    FIXTURE_BOOK,
    FIXTURE_METADATA,
    FIXTURE_TIME_MS,
    CapturedResponse,
)
from liqvera_public_capture.evidence_package import capture_members
from liqvera_readonly_analyzer.vwap import Side

ROOT = Path(__file__).resolve().parents[2]


def built_with_mezo(tmp_path):
    capture_id = UUID("123e4567-e89b-42d3-a456-426614174010")
    members = capture_members(capture_id, "fixture", (
        CapturedResponse("metadata", FIXTURE_METADATA, FIXTURE_TIME_MS, FIXTURE_TIME_MS, 0),
        CapturedResponse("book", FIXTURE_BOOK.replace(b'"sz":"0.1"', b'"sz":"10"'), FIXTURE_TIME_MS, FIXTURE_TIME_MS, 0),
    ))
    for name, raw in members.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    probe = json.loads((ROOT / "evidence/mezo-testnet/2026-10-23-protocol-probe.json").read_bytes())
    capture = {"schema": "liqvera-mezo-dex-capture/v1", "source": "mezo-dex:MUSD-BTC:testnet",
               "side": "SELL", "quantity_wei": str(10**18), "probe": probe}
    return build_report(tmp_path, ReportRequest(
        UUID("123e4567-e89b-42d3-a456-426614174011"), Side.SELL,
        ExactDecimal.parse("1"), "c" * 40), mezo_capture=capture)


def test_optional_mezo_report_reproduces_every_member_offline(tmp_path, monkeypatch):
    built = built_with_mezo(tmp_path)
    assert built.document["mezo_dex"]["fee_bps"] == 4
    assert built.document["venue_comparison"]["better_venue"] == "hyperliquid"
    bundle = build_bundle(built)
    monkeypatch.setattr("socket.socket", lambda *a, **k: pytest.fail("offline verifier attempted network"))
    assert verify_bundle_bytes(bundle) == built


def test_changing_raw_call_after_capture_fails_even_with_rehashed_manifest(tmp_path):
    from liqvera_evidence_report import evidence_bundle
    from liqvera_evidence_report.canonical import canonical_json_bytes
    from liqvera_evidence_report.evidence_io import digest

    built = built_with_mezo(tmp_path)
    members = evidence_bundle._read_archive(build_bundle(built))
    captured = json.loads(members["mezo-dex/capture.json"])
    captured["probe"]["calls"][5]["response"]["result"] = "0x" + format(30, "064x")
    members["mezo-dex/capture.json"] = canonical_json_bytes(captured)
    manifest = json.loads(members["manifest.json"])
    for item in manifest["members"]:
        item["sha256"] = digest(members[item["path"]])
        item["length"] = len(members[item["path"]])
    members["manifest.json"] = canonical_json_bytes(manifest)
    with pytest.raises(EvidenceRejected):
        verify_bundle_bytes(evidence_bundle._zip(members))


def test_mezo_sidecar_in_sealed_capture_is_automatically_reported(tmp_path):
    from liqvera_evidence_report.sealed_input import inspect_members

    probe = json.loads((ROOT / "evidence/mezo-testnet/2026-10-23-protocol-probe.json").read_bytes())
    captured = {"schema": "liqvera-mezo-dex-capture/v1", "source": "mezo-dex:MUSD-BTC:testnet",
                "side": "SELL", "quantity_wei": str(10**18), "probe": probe}
    members = capture_members(UUID("123e4567-e89b-42d3-a456-426614174010"), "fixture", (
        CapturedResponse("metadata", FIXTURE_METADATA, FIXTURE_TIME_MS, FIXTURE_TIME_MS, 0),
        CapturedResponse("book", FIXTURE_BOOK.replace(b'"sz":"0.1"', b'"sz":"10"'), FIXTURE_TIME_MS, FIXTURE_TIME_MS, 0),
    ), mezo_capture=captured)
    inspected = inspect_members(members)
    from liqvera_evidence_report.report import build_inspected_report
    built = build_inspected_report(inspected, ReportRequest(
        UUID("123e4567-e89b-42d3-a456-426614174011"), Side.SELL,
        ExactDecimal.parse("1"), "c" * 40))
    assert built.document["mezo_dex"]["match"]
    assert verify_bundle_bytes(build_bundle(built)) == built


def test_enabled_mezo_source_rejects_omitted_sidecar():
    from types import SimpleNamespace

    from liqvera_evidence_report.service import require_mezo_source

    with pytest.raises(EvidenceRejected,match="MEZO_SOURCE_UNAVAILABLE"):
        require_mezo_source(SimpleNamespace(input_members={}, document={}, extra_members={}))
