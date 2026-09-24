"""Fail-closed retirement policy for Python-only invariant evidence."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

BLOCKED = "BLOCKED"
ELIGIBLE = "ELIGIBLE"
RETIRED = "RETIRED"

_HEX40 = __import__("re").compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True, slots=True)
class ConformanceRow:
    invariant_id: str
    reference_source: str
    contract_symbol: str
    python_test: str
    negative_tests: tuple[str, ...]
    claw_gate: str
    source_sha: str
    review_result: str | None
    claw_receipt: Mapping[str, object] | None
    python_passed: bool
    stage_a_packaging_allowed: bool = False


def receipt_for_head(root: Path | None = None) -> dict[str, str]:
    """Bind a receipt identity to the current exact HEAD. Does not approve retirement."""
    repository = Path(root) if root is not None else Path.cwd()
    completed = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError("receipt_for_head requires a readable Git HEAD")
    source_sha = completed.stdout.strip()
    if not _HEX40.fullmatch(source_sha):
        raise RuntimeError("receipt_for_head produced a non-SHA identity")
    return {"source_sha": source_sha, "execution_backend": "python", "go_executed": "false"}


def retirement_state(row: ConformanceRow) -> str:
    """Same-named Python tests never retire a reference. Packaging stays forbidden."""
    if row.stage_a_packaging_allowed:
        return BLOCKED
    if not row.python_passed:
        return BLOCKED
    if row.review_result != "APPROVED":
        return BLOCKED
    receipt = row.claw_receipt
    if not isinstance(receipt, Mapping):
        return BLOCKED
    receipt_sha = receipt.get("source_sha")
    if receipt_sha != row.source_sha or not _HEX40.fullmatch(str(receipt_sha)):
        return BLOCKED
    if receipt.get("execution_backend") != "python":
        return BLOCKED
    if str(receipt.get("go_executed", "")).lower() not in {"false", "0"}:
        return BLOCKED
    return ELIGIBLE


def conformance_row(
    *,
    review_result: str | None,
    claw_receipt: Mapping[str, object] | None,
    python_passed: bool = True,
    source_sha: str | None = None,
    python_test: str = "tests/conformance/test_exact_arithmetic.py",
    stage_a_packaging_allowed: bool = False,
) -> ConformanceRow:
    sha = source_sha
    if sha is None:
        if claw_receipt is not None and isinstance(claw_receipt.get("source_sha"), str):
            sha = str(claw_receipt["source_sha"])
        else:
            sha = "0" * 40
    return ConformanceRow(
        invariant_id="EXACT-001",
        reference_source="internal/fixed",
        contract_symbol="mee_contracts.exact.ExactDecimal",
        python_test=python_test,
        negative_tests=("reject_nonfinite", "reject_binary_float"),
        claw_gate="python-conformance",
        source_sha=sha,
        review_result=review_result,
        claw_receipt=claw_receipt,
        python_passed=python_passed,
        stage_a_packaging_allowed=stage_a_packaging_allowed,
    )
