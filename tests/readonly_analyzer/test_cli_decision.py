"""Analyzer CLI emits one closed Stage A decision JSON document."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from uuid import UUID

import pytest
from mee_readonly_analyzer.__main__ import main
from mee_readonly_analyzer.config import load_analyzer_configuration

from tests.readonly_analyzer.package_factory import (
    write_sufficient_package,
    write_valid_package,
)

RUN = UUID("00000000-0000-0000-0000-000000000001")


def _run_cli(monkeypatch: pytest.MonkeyPatch, environ: Mapping[str, str]) -> int:
    monkeypatch.setattr(
        "mee_readonly_analyzer.__main__.load_analyzer_configuration",
        lambda: load_analyzer_configuration(environ),
    )
    return main()


def _stdout_document(capsys: pytest.CaptureFixture[str]) -> tuple[dict[str, object], str]:
    captured = capsys.readouterr()
    assert "frozen package ok" not in captured.out
    assert "GO" not in captured.out
    return json.loads(captured.out), captured.err


def test_valid_package_emits_insufficient_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    code = _run_cli(monkeypatch, {"MEE_FROZEN_PACKAGE": str(package)})
    document, err = _stdout_document(capsys)
    assert code == 0
    assert err == ""
    assert document["schema"] == "mee-stage-a-decision/v1"
    assert document["decision"] == "INSUFFICIENT_EVIDENCE"
    assert document["capture_run_id"] == str(RUN)
    assert document["package_schema"] == "mee-readonly-frozen-package/v1"
    reasons = document["reasons"]
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(item, str) and item.startswith("INSUFFICIENT_") for item in reasons)
    assert len(reasons) > 1
    assert "INSUFFICIENT_ACQUISITION_WINDOW" in reasons
    assert "INSUFFICIENT_COMPLETE_UTC_DAYS" in reasons
    assert "INSUFFICIENT_STRICT_HEALTHY_MINUTES" in reasons
    assert "INSUFFICIENT_INDEPENDENT_EPISODES" in reasons


def test_extra_undeclared_file_emits_invalid_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN)
    (package / "stale.bin").write_bytes(b"old")
    code = _run_cli(monkeypatch, {"MEE_FROZEN_PACKAGE": str(package)})
    document, _err = _stdout_document(capsys)
    assert code == 1
    assert document["decision"] == "INVALID_DATASET"
    reasons = document["reasons"]
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(item, str) and item.startswith("INVALID_") for item in reasons)
    assert "INVALID_MEMBER_SET_MISMATCH" in reasons
    assert not any(item.startswith("INSUFFICIENT_") for item in reasons)


def test_malformed_mapping_emits_invalid_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = write_valid_package(tmp_path / "pkg", RUN, mappings=[{"mapping_id": "bad"}])
    code = _run_cli(monkeypatch, {"MEE_FROZEN_PACKAGE": str(package)})
    document, _err = _stdout_document(capsys)
    assert code == 1
    assert document["decision"] == "INVALID_DATASET"
    reasons = document["reasons"]
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(item, str) and item.startswith("INVALID_") for item in reasons)
    assert "INVALID_RECORD" in reasons
    assert not any(item.startswith("INSUFFICIENT_") for item in reasons)


def test_missing_frozen_package_env_is_config_reject(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code = _run_cli(monkeypatch, {})
    captured = capsys.readouterr()
    assert code == 2
    assert captured.out == ""
    assert "readonly analyzer configuration rejected" in captured.err


def test_sufficient_empty_mappings_emits_invalid_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = write_sufficient_package(tmp_path / "pkg", RUN, mappings=[])
    code = _run_cli(monkeypatch, {"MEE_FROZEN_PACKAGE": str(package)})
    document, _err = _stdout_document(capsys)
    assert code == 1
    assert document["decision"] == "INVALID_DATASET"
    assert document["reasons"] == ["INVALID_RECORD"]
    assert "GO" not in document["decision"]


def test_sufficient_extend_package_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    package = write_sufficient_package(tmp_path / "pkg", RUN)
    code = _run_cli(monkeypatch, {"MEE_FROZEN_PACKAGE": str(package)})
    document, err = _stdout_document(capsys)
    assert code == 0
    assert err == ""
    assert document["schema"] == "mee-stage-a-decision/v1"
    assert document["decision"] == "EXTEND_LONGER_SHADOW"
    assert document["reasons"] == ["EXTEND_ALL_V2_GATES_PASS"]
    assert document["capture_run_id"] == str(RUN)
