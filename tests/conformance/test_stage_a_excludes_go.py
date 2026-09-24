"""Hypothesis: Stage A package trees contain no Go inputs or engine binary."""

from __future__ import annotations

from pathlib import Path

from tools.conformance.artifacts import scan

ROOT = Path(__file__).resolve().parents[2]


def test_packages_tree_has_no_go_inputs() -> None:
    hits = scan(
        (ROOT / "packages",),
        ("cmd/**", "internal/**", "go.mod", "go.sum"),
        "engine",
    )
    assert hits == []
