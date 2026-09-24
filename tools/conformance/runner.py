"""Run Python-only invariant conformance and write an exact-SHA receipt."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import yaml

from tools.conformance.policy import BLOCKED, conformance_row, retirement_state


class ConformanceError(RuntimeError):
    """Conformance input or policy failed closed."""


_FORBIDDEN_GO_ENV = ("GO_EXECUTE", "MEE_RUN_GO", "RUN_GO_TESTS")


def require_python_only_environment() -> None:
    if any(os.environ.get(name) for name in _FORBIDDEN_GO_ENV):
        raise ConformanceError("Go execution is forbidden")
    extra = os.environ.get("MEE_CONFORMANCE_BACKEND", "python")
    if extra != "python":
        raise ConformanceError("conformance backend must be python")


def require_clean_exact_head(source_sha: str, root: Path) -> None:
    if type(source_sha) is not str or len(source_sha) != 40:
        raise ConformanceError("source_sha must be a 40-character hex SHA")
    head = _git(root, "rev-parse", "HEAD")
    if head != source_sha:
        raise ConformanceError(f"HEAD {head} does not match source_sha {source_sha}")
    status = _git(root, "status", "--porcelain")
    if status:
        raise ConformanceError("working tree is dirty")


def load_manifest(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ConformanceError("conformance manifest must be a mapping")
    if loaded.get("execution_backend") != "python":
        raise ConformanceError("manifest execution_backend must be python")
    if loaded.get("go_executed") is not False:
        raise ConformanceError("manifest must declare go_executed=false")
    invariants = loaded.get("invariants")
    if not isinstance(invariants, list) or not invariants:
        raise ConformanceError("manifest invariants must be a non-empty list")
    return loaded


def run_named_python_tests(root: Path, python_tests: tuple[str, ...]) -> bool:
    require_python_only_environment()
    command = [sys.executable, "-B", "-m", "pytest", "-q", *python_tests]
    if any(token in {"go", "gotest"} for token in command):
        raise ConformanceError("Go invocation leaked into the Python runner")
    completed = subprocess.run(command, cwd=root, check=False)
    return completed.returncode == 0


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def run_conformance(manifest: Path, source_sha: str, output: Path, root: Path | None = None) -> dict[str, Any]:
    repository = root or Path.cwd()
    require_python_only_environment()
    require_clean_exact_head(source_sha, repository)
    document = load_manifest(manifest)
    python_tests = tuple(str(item["python_test"]) for item in document["invariants"])
    passed = run_named_python_tests(repository, python_tests)
    rows = []
    for item in document["invariants"]:
        row = conformance_row(
            review_result=None,
            claw_receipt=None,
            python_passed=passed,
            source_sha=source_sha,
            python_test=str(item["python_test"]),
            stage_a_packaging_allowed=bool(item.get("stage_a_packaging_allowed", False)),
        )
        rows.append(
            {
                "invariant_id": str(item["invariant_id"]),
                "reference_source": str(item.get("reference_source", "")),
                "contract_symbol": str(item["contract_symbol"]),
                "python_test": str(item["python_test"]),
                "negative_tests": list(item.get("negative_tests", [])),
                "claw_gate": str(item.get("claw_gate", "python-conformance")),
                "source_sha": source_sha,
                "review_result": None,
                "python_passed": passed,
                "retirement_state": retirement_state(row) if passed else BLOCKED,
                "stage_a_packaging_allowed": False,
            }
        )
    receipt = {
        "schema_version": 1,
        "execution_backend": "python",
        "go_executed": False,
        "source_sha": source_sha,
        "python_passed": passed,
        "rows": rows,
    }
    encoded = canonical_json(receipt)
    receipt["content_hash"] = hashlib.sha256(encoded).hexdigest()
    encoded = canonical_json(receipt)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(encoded)
    if not passed:
        raise ConformanceError("python conformance tests failed")
    return receipt


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()
