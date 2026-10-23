"""Trove reports must rebuild from raw calls and reject changes without RPC."""

import copy
import json
from pathlib import Path
from uuid import UUID

import pytest
from liqvera_evidence_report.evidence_bundle import build_bundle, verify_bundle_bytes
from liqvera_evidence_report.evidence_io import EvidenceRejected
from liqvera_evidence_report.trove_report import TroveReportRequest, build_trove_report

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evidence/mezo-testnet/2026-10-23-trove-active-native.json"


def inputs():
    capture = json.loads(CAPTURE.read_text())
    request = TroveReportRequest(
        UUID("123e4567-e89b-42d3-a456-426614174050"),
        capture["borrower"],
        "c" * 40,
        int(capture["block"]["result"]["timestamp"], 16) * 1000,
        source_mode="fixture",
    )
    return capture, request


def test_native_trove_bundle_reproduces_all_outputs_offline(monkeypatch):
    import socket

    monkeypatch.setattr(
        socket, "create_connection", lambda *a, **k: pytest.fail("Verifier used network")
    )
    capture, request = inputs()
    built = build_trove_report(capture, request)
    assert built.document["request"] == {
        "product_id": "trove_risk",
        "borrower": capture["borrower"],
    }
    assert built.document["trove_risk"]["redemption_position"] == 1
    assert built.document["trove_risk"]["block_number"] == "16320987"
    assert built.document["quality"]["snapshot_status"] == "SIMULATED"
    assert (
        verify_bundle_bytes(build_bundle(built), expected_report_sha256=built.report_sha256)
        == built
    )


@pytest.mark.parametrize("change", ["chain", "block", "neighbor", "debt"])
def test_trove_report_rejects_changed_raw_proofs(change):
    capture, request = inputs()
    capture = copy.deepcopy(capture)
    if change == "chain":
        capture["chain"]["result"] = "0x1"
    elif change == "block":
        capture["block_after"]["result"]["hash"] = "0x" + "0" * 64
    else:
        selector = "0xb72703ac" if change == "neighbor" else "0xb91af97c"
        call = next(c for c in capture["calls"] if c["data"].startswith(selector))
        call["response"]["result"] = "0x" + "0" * (40 if change == "neighbor" else 64)
    with pytest.raises(EvidenceRejected):
        build_trove_report(capture, request)


def test_trove_bundle_wrong_digest_or_one_changed_byte_fails():
    capture, request = inputs()
    built = build_trove_report(capture, request)
    raw = build_bundle(built)
    with pytest.raises(EvidenceRejected):
        verify_bundle_bytes(raw, expected_report_sha256="0" * 64)
    changed = bytearray(raw)
    changed[len(changed) // 2] ^= 1
    with pytest.raises(EvidenceRejected):
        verify_bundle_bytes(bytes(changed))


def test_trove_report_binds_borrower_and_discloses_historical_snapshot():
    capture, request = inputs()
    with pytest.raises(EvidenceRejected):
        build_trove_report(
            capture,
            TroveReportRequest(
                request.report_id, "0x" + "1" * 40, request.engine_commit, request.created_at_ms
            ),
        )
    historical = TroveReportRequest(
        request.report_id, request.borrower, request.engine_commit, request.created_at_ms + 60_000
    )
    assert (
        build_trove_report(capture, historical).document["quality"]["snapshot_status"]
        == "HISTORICAL_SNAPSHOT"
    )


def test_nonobject_report_rejects_with_public_reason():
    from dataclasses import replace

    from liqvera_evidence_report.evidence_io import digest

    capture, request = inputs()
    built = build_trove_report(capture, request)
    malformed = replace(built, report_bytes=b"[]\n", report_sha256=digest(b"[]\n"))
    with pytest.raises(EvidenceRejected, match="INVALID_DATASET"):
        verify_bundle_bytes(build_bundle(malformed))


def test_trove_cli_verify_prints_only_a_fixed_block_optional_recheck(tmp_path, capsys):
    from liqvera_evidence_report.evidence_bundle import publish_artifact
    from liqvera_evidence_report.evidence_cli import verify_main

    capture, request = inputs()
    built = build_trove_report(capture, request)
    publish_artifact(tmp_path, built)
    assert verify_main([str(tmp_path / str(request.report_id) / "evidence.zip")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "INTEGRITY_REPRODUCED"
    assert output["mezo_block_number"] == "16320987"
    assert not output["online_recheck_executed"]
    assert "eth_call" in output["online_recheck_command"]
    assert "0x0fdb11cf" in output["online_recheck_command"]


@pytest.mark.parametrize("member", ["calls", "abi", "report"])
def test_recomputed_manifest_cannot_hide_changed_proofs_or_calculation(member):
    from dataclasses import replace

    from liqvera_evidence_report.canonical import canonical_json_bytes
    from liqvera_evidence_report.evidence_io import digest

    capture, request = inputs()
    built = build_trove_report(capture, request)
    extra = built.extra_members.copy()
    if member == "calls":
        altered = copy.deepcopy(capture)
        altered["calls"][0]["response"]["result"] = "0x" + "0" * 64
        extra["mezo-troves/capture.json"] = canonical_json_bytes(altered)
        extra["mezo-troves/calls.json"] = canonical_json_bytes(altered["calls"])
        modified = replace(built, extra_members=extra)
    elif member == "abi":
        name = "mezo-troves/TroveManager.implementation.testnet.json"
        extra[name] += b" "
        modified = replace(built, extra_members=extra)
    else:
        report = copy.deepcopy(built.document)
        report["trove_risk"]["icr"] = "999"
        raw = canonical_json_bytes(report)
        modified = replace(built, report_bytes=raw, report_sha256=digest(raw))
    with pytest.raises(EvidenceRejected, match="INVALID_DATASET"):
        verify_bundle_bytes(build_bundle(modified))


@pytest.mark.parametrize("clock", [-1, 253_402_300_800_000, True])
def test_report_clock_is_a_bounded_integer(clock):
    capture, request = inputs()
    with pytest.raises(EvidenceRejected, match="INVALID_INPUT"):
        TroveReportRequest(request.report_id, request.borrower, request.engine_commit, clock)
