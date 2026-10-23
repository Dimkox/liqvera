"""CLI previews are free, bounded, reproducible, and never substitute a fixture."""

import json
from pathlib import Path

import pytest
from liqvera_evidence_report import trove_cli
from liqvera_evidence_report.evidence_bundle import verify_bundle

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evidence/mezo-testnet/2026-10-23-trove-active-native.json"
BORROWER = json.loads(CAPTURE.read_text())["borrower"]


def test_retained_capture_cli_never_uses_network_and_publishes_verifiable_zip(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(trove_cli, "capture_live_trove", lambda *_: pytest.fail("Unexpected RPC"))
    assert (
        trove_cli.main(
            [
                BORROWER,
                "--engine-commit",
                "c" * 40,
                "--capture",
                str(CAPTURE),
                "--output-root",
                str(tmp_path),
                "--fixture",
            ]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert not result["chargeable"] and result["execution_authority"] == "NONE"
    built = verify_bundle(
        Path(result["evidence_zip"]), expected_report_sha256=result["artifact"]["report_sha256"]
    )
    assert (
        built.document == result["report"]
        and built.document["quality"]["snapshot_status"] == "SIMULATED"
    )


def test_live_rpc_failure_leaves_no_report_or_fixture(tmp_path, monkeypatch, capsys):
    def fail(_):
        raise ValueError("MEZO_TROVE_SOURCE_UNAVAILABLE")

    monkeypatch.setattr(trove_cli, "capture_live_trove", fail)
    assert (
        trove_cli.main([BORROWER, "--engine-commit", "c" * 40, "--output-root", str(tmp_path)]) == 2
    )
    assert json.loads(capsys.readouterr().err) == {
        "status": "REJECTED",
        "code": "SOURCE_UNAVAILABLE",
    }
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "args",
    [
        ["invalid-borrower"],
        [BORROWER, "--report-id", "not-a-uuid"],
        [BORROWER, "--fixture"],
    ],
)
def test_invalid_cli_input_rejects_before_any_rpc(args, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        trove_cli, "capture_live_trove", lambda *_: pytest.fail("Invalid input used RPC")
    )
    assert trove_cli.main([*args, "--engine-commit", "c" * 40, "--output-root", str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().err) == {"status": "REJECTED", "code": "INVALID_INPUT"}
    assert not list(tmp_path.iterdir())
