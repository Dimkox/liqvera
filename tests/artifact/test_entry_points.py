"""Hypothesis: only capture and analyzer expose console entries."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.conformance.distributions import build_all, install_one, make_venv

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def wheels(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("entry-wheels")
    build_all("dirty", dest, root=ROOT, require_clean=False)
    return dest


def test_console_entries_match_distributions(tmp_path: Path, wheels: Path) -> None:
    contracts = install_one(make_venv(tmp_path / "c"), wheels, "mee-contracts")
    capture = install_one(make_venv(tmp_path / "p"), wheels, "mee-public-capture")
    analyzer = install_one(make_venv(tmp_path / "a"), wheels, "mee-readonly-analyzer")
    assert contracts.entry_points == ()
    assert "mee-public-capture" in capture.entry_points
    assert "mee-readonly-analyzer" in analyzer.entry_points
    assert "engine" not in capture.entry_points
    assert "engine" not in analyzer.entry_points
