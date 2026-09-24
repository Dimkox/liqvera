"""Hypothesis: conformance executes Python only and never invokes Go."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.conformance.runner import (
    ConformanceError,
    load_manifest,
    require_python_only_environment,
    run_conformance,
)

ROOT = Path(__file__).resolve().parents[2]


def test_manifest_is_python_only() -> None:
    document = load_manifest(ROOT / "architecture" / "conformance" / "manifest.yaml")
    assert document["execution_backend"] == "python"
    assert document["go_executed"] is False


def test_go_environment_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GO_EXECUTE", "1")
    with pytest.raises(ConformanceError, match="Go execution is forbidden"):
        require_python_only_environment()


def test_runner_source_never_calls_go() -> None:
    source = (ROOT / "tools" / "conformance" / "runner.py").read_text(encoding="utf-8")
    entry = (ROOT / "scripts" / "run-conformance.py").read_text(encoding="utf-8")
    combined = source + "\n" + entry
    assert "go test" not in combined
    assert "GOROOT" not in combined
    assert "/sdk/go" not in combined


def test_dirty_tree_fails_closed(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"
    with pytest.raises(ConformanceError, match="dirty|does not match"):
        run_conformance(
            ROOT / "architecture" / "conformance" / "manifest.yaml",
            "0" * 40,
            output,
            root=ROOT,
        )
    assert not output.exists()
