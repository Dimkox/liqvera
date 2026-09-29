from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.exact import ExactDecimal
from mee_evidence_report import evidence_bundle
from mee_evidence_report.evidence_bundle import (
    publish_artifact,
    read_published,
    verify_bundle,
)
from mee_evidence_report.evidence_io import EvidenceRejected
from mee_evidence_report.report import ReportRequest, build_report
from mee_public_capture.evidence_package import capture_package
from mee_readonly_analyzer.vwap import Side

CAPTURE_ID = UUID("123e4567-e89b-42d3-a456-426614174010")
REPORT_ID = UUID("123e4567-e89b-42d3-a456-426614174011")
ENGINE_COMMIT = "c" * 40


def _built(tmp_path: Path):
    capture_root = tmp_path / "captures"
    capture_root.mkdir()
    package = capture_package(capture_root, CAPTURE_ID, source_mode="fixture")
    request = ReportRequest(
        report_id=REPORT_ID,
        side=Side.BUY,
        quantity_base=ExactDecimal.parse("0.15"),
        engine_commit=ENGINE_COMMIT,
    )
    return build_report(package, request)


def test_canonical_fixture_publishes_and_reproduces_exact_artifact(tmp_path: Path) -> None:
    # Catches source/MVP substitution, noncanonical output, and lost report/bundle binding.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    output.mkdir()

    published = publish_artifact(output, built)
    reproduced, readback = read_published(output, str(REPORT_ID))

    assert set((output / str(REPORT_ID)).iterdir()) == {
        output / str(REPORT_ID) / "report.json",
        output / str(REPORT_ID) / "evidence.zip",
    }
    assert reproduced == built
    assert readback == published
    assert reproduced.document["calculation"]["notional_quote"] == {
        "numerator": "15005",
        "denominator": "1",
    }
    assert reproduced.document["quality"]["snapshot_status"] == "SIMULATED"
    assert reproduced.document["boundaries"]["execution_authority"] == "NONE"
    assert verify_bundle(
        output / str(REPORT_ID) / "evidence.zip",
        expected_report_sha256=published.report_sha256,
    ) == built


def test_tampered_bundle_and_trusted_digest_are_rejected(tmp_path: Path) -> None:
    # Catches accepting altered archive bytes or a caller-supplied digest mismatch.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    output.mkdir()
    published = publish_artifact(output, built)
    bundle = output / str(REPORT_ID) / "evidence.zip"

    with pytest.raises(EvidenceRejected, match="INVALID_DATASET"):
        verify_bundle(bundle, expected_report_sha256="0" * 64)

    raw = bytearray(bundle.read_bytes())
    raw[len(raw) // 2] ^= 1
    bundle.write_bytes(raw)
    with pytest.raises(EvidenceRejected, match="INVALID_DATASET"):
        verify_bundle(bundle, expected_report_sha256=published.report_sha256)


def test_duplicate_report_uuid_never_replaces_original_bytes(tmp_path: Path) -> None:
    # Catches an idempotency shortcut that overwrites immutable UUID output.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    output.mkdir()
    publish_artifact(output, built)
    target = output / str(REPORT_ID)
    original = {path.name: path.read_bytes() for path in target.iterdir()}

    with pytest.raises(FileExistsError, match="immutable report already exists"):
        publish_artifact(output, built)
    changed = build_report(
        tmp_path / "captures" / str(CAPTURE_ID),
        ReportRequest(
            report_id=REPORT_ID,
            side=Side.SELL,
            quantity_base=ExactDecimal.parse("0.15"),
            engine_commit=ENGINE_COMMIT,
        ),
    )
    with pytest.raises(FileExistsError, match="immutable report already exists"):
        publish_artifact(output, changed)

    assert {path.name: path.read_bytes() for path in target.iterdir()} == original


def test_standalone_report_tamper_cannot_split_from_verified_bundle(tmp_path: Path) -> None:
    # Catches serving a changed convenience report beside a still-valid archive.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    output.mkdir()
    publish_artifact(output, built)
    report = output / str(REPORT_ID) / "report.json"
    report.write_bytes(report.read_bytes() + b" ")

    with pytest.raises(EvidenceRejected, match="ARTIFACT_INTEGRITY_FAILED"):
        read_published(output, str(REPORT_ID))


def test_partial_target_is_never_merged_or_replaced(tmp_path: Path) -> None:
    # Catches treating a visible incomplete UUID directory as resumable publication state.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    target = output / str(REPORT_ID)
    target.mkdir(parents=True)
    partial = target / "report.json"
    partial.write_bytes(b"partial")

    with pytest.raises(FileExistsError, match="immutable report already exists"):
        publish_artifact(output, built)
    with pytest.raises(EvidenceRejected, match="ARTIFACT_INTEGRITY_FAILED"):
        read_published(output, str(REPORT_ID))

    assert partial.read_bytes() == b"partial"
    assert set(target.iterdir()) == {partial}


def test_failed_staged_verification_exposes_no_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Catches leaking a partial target or staging directory after pre-rename failure.
    built = _built(tmp_path)
    output = tmp_path / "artifacts"
    output.mkdir()

    def reject(*args, **kwargs):
        raise EvidenceRejected("INVALID_DATASET")

    monkeypatch.setattr(evidence_bundle, "verify_bundle", reject)
    with pytest.raises(EvidenceRejected, match="INVALID_DATASET"):
        publish_artifact(output, built)

    assert not (output / str(REPORT_ID)).exists()
    assert {path.name for path in output.iterdir()} == {f".{REPORT_ID}.lock"}
