"""Prototype artifact and CLI behavior for the intentionally unverified F3 MVP."""

from __future__ import annotations

import hashlib
import importlib
import json
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType, SimpleNamespace
from uuid import UUID
from zipfile import ZIP_STORED, ZipFile

import pytest
from mee_contracts.exact import ExactDecimal
from mee_readonly_analyzer.vwap import Side

PACKAGE_SRC = Path(__file__).parents[2] / "packages" / "evidence-report" / "src"


@pytest.fixture
def mvp_modules(monkeypatch: pytest.MonkeyPatch):
    """Load the owned modules against the agreed core surface while it is built in parallel."""

    monkeypatch.syspath_prepend(str(PACKAGE_SRC))

    @dataclass(frozen=True)
    class MvpReportRequest:
        report_id: UUID
        side: Side
        quantity_base: ExactDecimal
        created_at_ms: int | None = None
        engine_commit: str = "0" * 40

    class MvpReportRejected(ValueError):
        pass

    canonical = ModuleType("mee_evidence_report.canonical")
    canonical.canonical_json_bytes = lambda value: (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        + b"\n"
    )
    model = ModuleType("mee_evidence_report.model")
    model.MvpReportRequest = MvpReportRequest
    model.MvpReportRejected = MvpReportRejected
    builder = ModuleType("mee_evidence_report.builder")
    builder.build_simulated_report = lambda package_root, request: None
    monkeypatch.setitem(sys.modules, canonical.__name__, canonical)
    monkeypatch.setitem(sys.modules, model.__name__, model)
    monkeypatch.setitem(sys.modules, builder.__name__, builder)
    sys.modules.pop("mee_evidence_report.bundle", None)
    sys.modules.pop("mee_evidence_report.cli", None)

    bundle = importlib.import_module("mee_evidence_report.bundle")
    cli = importlib.import_module("mee_evidence_report.cli")
    return bundle, cli, MvpReportRejected


def _built_report() -> SimpleNamespace:
    report_bytes = b'{"mode":"SIMULATED","report_id":"demo"}\n'
    return SimpleNamespace(
        document={"mode": "SIMULATED", "report_id": "demo"},
        report_bytes=report_bytes,
        report_sha256=hashlib.sha256(report_bytes).hexdigest(),
    )


def _package(root: Path) -> Path:
    root.mkdir()
    (root / "manifest.json").write_bytes(b'{"schema":"fixture"}\n')
    (root / "raw_batches").mkdir()
    (root / "raw_batches" / "0.bin").write_bytes(b"book-bytes")
    return root


def test_writer_builds_identical_stored_archives_with_fixed_metadata(
    tmp_path: Path, mvp_modules
):
    bundle, _, _ = mvp_modules
    built = _built_report()

    first = bundle.write_mvp_artifact(tmp_path / "out-a", built, _package(tmp_path / "pkg-a"))
    second = bundle.write_mvp_artifact(tmp_path / "out-b", built, _package(tmp_path / "pkg-b"))

    first_bytes = first.bundle_path.read_bytes()
    assert first_bytes == second.bundle_path.read_bytes()
    assert first.report_path.read_bytes() == built.report_bytes
    assert first.report_sha256 == hashlib.sha256(built.report_bytes).hexdigest()
    assert first.bundle_sha256 == hashlib.sha256(first_bytes).hexdigest()

    with ZipFile(first.bundle_path) as archive:
        assert archive.namelist() == [
            "report.json",
            "sealed-input/manifest.json",
            "sealed-input/raw_batches/0.bin",
        ]
        assert archive.read("report.json") == built.report_bytes
        for info in archive.infolist():
            assert info.compress_type == ZIP_STORED
            assert info.date_time == (1980, 1, 1, 0, 0, 0)
            assert info.create_system == 3
            assert stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG
            assert stat.S_IMODE(info.external_attr >> 16) == 0o644
            assert info.extra == b""
            assert info.comment == b""


def test_writer_refuses_an_existing_output_directory(tmp_path: Path, mvp_modules):
    bundle, _, _ = mvp_modules
    output = tmp_path / "existing"
    output.mkdir()

    with pytest.raises(FileExistsError):
        bundle.write_mvp_artifact(output, _built_report(), _package(tmp_path / "pkg"))

    assert list(output.iterdir()) == []


def test_writer_rejects_package_symlinks_without_publishing(tmp_path: Path, mvp_modules):
    bundle, _, _ = mvp_modules
    package = _package(tmp_path / "pkg")
    (package / "linked.bin").symlink_to(package / "manifest.json")
    output = tmp_path / "out"

    with pytest.raises(ValueError, match="symlink"):
        bundle.write_mvp_artifact(output, _built_report(), package)

    assert not output.exists()


def test_writer_rejects_unsafe_member_names(tmp_path: Path, mvp_modules):
    bundle, _, _ = mvp_modules
    package = _package(tmp_path / "pkg")
    (package / "unsafe\\name.json").write_bytes(b"{}\n")

    with pytest.raises(ValueError, match="unsafe"):
        bundle.write_mvp_artifact(tmp_path / "out", _built_report(), package)


def test_cli_builds_simulated_request_and_prints_one_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, mvp_modules
):
    bundle, cli, _ = mvp_modules
    report_id = UUID("11111111-1111-4111-8111-111111111111")
    built = _built_report()
    observed: dict[str, object] = {}

    def fake_build(package_root: Path, request: object):
        observed["package_root"] = package_root
        observed["request"] = request
        return built

    artifact = bundle.MvpArtifact(
        report_path=tmp_path / "out" / "report.json",
        bundle_path=tmp_path / "out" / "evidence.zip",
        report_sha256=built.report_sha256,
        bundle_sha256="b" * 64,
    )
    monkeypatch.setattr(cli, "build_simulated_report", fake_build)
    monkeypatch.setattr(cli, "write_mvp_artifact", lambda output, value, package: artifact)

    exit_code = cli.main(
        [
            "--package",
            str(tmp_path / "package"),
            "--output",
            str(tmp_path / "out"),
            "--side",
            "BUY",
            "--quantity",
            "0.25",
            "--report-id",
            str(report_id),
            "--engine-commit",
            "a" * 40,
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "bundle_sha256": "b" * 64,
        "mode": "SIMULATED",
        "report_id": str(report_id),
        "report_sha256": built.report_sha256,
        "warning": "UNVERIFIED_MVP_NO_PAYMENT",
    }
    request = observed["request"]
    assert observed["package_root"] == tmp_path / "package"
    assert request.report_id == report_id
    assert request.side is Side.BUY
    assert request.quantity_base == ExactDecimal.parse("0.25")
    assert request.engine_commit == "a" * 40


def test_cli_returns_one_for_an_expected_build_rejection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, mvp_modules
):
    _, cli, rejected = mvp_modules

    def reject(package_root: Path, request: object):
        raise rejected("fixture package is invalid")

    monkeypatch.setattr(cli, "build_simulated_report", reject)

    exit_code = cli.main(
        [
            "--package",
            str(tmp_path / "package"),
            "--output",
            str(tmp_path / "out"),
            "--side",
            "SELL",
            "--quantity",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error": "REJECTED",
        "message": "fixture package is invalid",
    }
