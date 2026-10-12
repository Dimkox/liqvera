"""Hypothesis: Stage A wheels contain no Go or foreign application trees."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from tools.conformance.distributions import build_all

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def wheels(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("artifact-wheels")
    build_all("dirty", dest, root=ROOT, require_clean=False)
    return dest


def test_wheels_exclude_go_and_foreign_namespaces(wheels: Path) -> None:
    names = sorted(path.name for path in wheels.glob("liqvera_*.whl"))
    assert len(names) == 3
    forbidden = ("cmd/", "internal/", "go.mod", "go.sum", "liqvera_workspace/")
    for wheel in wheels.glob("liqvera_*.whl"):
        with zipfile.ZipFile(wheel) as archive:
            members = tuple(archive.namelist())
        for item in members:
            assert not item.endswith(".go")
            assert all(token not in item.replace("\\", "/") for token in forbidden)
