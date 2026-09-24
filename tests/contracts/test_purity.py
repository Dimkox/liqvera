"""Purity and export contracts for the mee-contracts distribution."""

from __future__ import annotations

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "packages" / "contracts"
SRC = CONTRACTS / "src" / "mee_contracts"


def test_contracts_pyproject_has_empty_dependency_closure() -> None:
    metadata = tomllib.loads((CONTRACTS / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "mee-contracts"
    assert project["version"] == "0.1.0"
    assert project.get("dependencies", []) == []
    assert "dependencies" in metadata["project"]


def test_contracts_source_has_no_forbidden_imports() -> None:
    forbidden = {
        "httpx",
        "websockets",
        "psycopg",
        "asyncpg",
        "hyperliquid",
        "eth_account",
        "pydantic",
        "orjson",
        "structlog",
        "multi_exchange_engine",
        "mee_public_capture",
        "mee_readonly_analyzer",
        "adaptive_grok",
    }
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden), path


def test_contracts_package_exports_kernel() -> None:
    import mee_contracts as pkg

    assert pkg.ShadowRejectCode.DEPTH_INSUFFICIENT.value == "DEPTH_INSUFFICIENT"
    assert pkg.fraction_from_decimal is not None
    assert pkg.ExactDecimal.parse("1.25").scaled == 125_000_000
    assert pkg.EvidenceReader is not None
    assert pkg.StageADecisionCode.INVALID_DATASET.value == "INVALID_DATASET"
    assert "GO" not in {item.value for item in pkg.StageADecisionCode}
    assert "multi_exchange_engine" not in pkg.__all__


def test_contracts_exports_reader_protocol() -> None:
    source = (SRC / "evidence.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    classes = {
        node.name: node
        for node in module.body
        if isinstance(node, ast.ClassDef)
    }
    assert "EvidenceReader" in classes
    methods = {
        item.name
        for item in classes["EvidenceReader"].body
        if isinstance(item, ast.FunctionDef)
    }
    assert methods >= {
        "read_capture_manifest",
        "capture_terminal",
        "iter_control_evidence",
        "iter_raw_batches",
        "iter_raw_envelopes",
        "iter_quality_minutes",
        "read_mapping_snapshot",
    }
