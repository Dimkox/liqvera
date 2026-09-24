"""Hypothesis: contracts stay empty; capture and analyzer share only contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.conformance.distributions import build_all, install_one, make_venv

ROOT = Path(__file__).resolve().parents[2]


def _names(requires: tuple[str, ...]) -> set[str]:
    found: set[str] = set()
    for item in requires:
        found.add(item.split(" ", 1)[0].split("[", 1)[0].split("==", 1)[0].lower())
    return found


@pytest.fixture(scope="module")
def wheels(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("dep-wheels")
    build_all("dirty", dest, root=ROOT, require_clean=False)
    return dest


def test_dependency_closures(tmp_path: Path, wheels: Path) -> None:
    contracts = install_one(make_venv(tmp_path / "c"), wheels, "mee-contracts")
    capture = install_one(make_venv(tmp_path / "p"), wheels, "mee-public-capture")
    analyzer = install_one(make_venv(tmp_path / "a"), wheels, "mee-readonly-analyzer")
    assert _names(contracts.dependencies) == set()
    assert "mee-contracts" in _names(capture.dependencies)
    assert "mee-readonly-analyzer" not in _names(capture.dependencies)
    assert _names(analyzer.dependencies) == {"mee-contracts"}
    assert "httpx" not in _names(analyzer.dependencies)
    assert "websockets" not in _names(analyzer.dependencies)
