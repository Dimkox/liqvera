"""Hypothesis: each core Liqvera wheel installs only its allowed namespaces."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.conformance.distributions import (
    ALLOWED_NAMESPACES,
    FORBIDDEN_SHARED,
    build_all,
    install_one,
    make_venv,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def wheels(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("core-wheels")
    built = build_all("dirty", dest, root=ROOT, require_clean=False)
    assert {item.distribution for item in built} == set(ALLOWED_NAMESPACES)
    return dest


@pytest.mark.parametrize(
    ("distribution", "allowed", "forbidden"),
    [
        ("liqvera-contracts", {"liqvera_contracts"}, {"liqvera_public_capture", "liqvera_readonly_analyzer"}),
        ("liqvera-public-capture", {"liqvera_contracts", "liqvera_public_capture"}, {"liqvera_readonly_analyzer"}),
        (
            "liqvera-readonly-analyzer",
            {"liqvera_contracts", "liqvera_readonly_analyzer"},
            {"liqvera_public_capture"},
        ),
    ],
)
def test_fresh_install_contains_only_allowed_namespaces(
    distribution: str,
    allowed: set[str],
    forbidden: set[str],
    artifact_env: Path,
    wheels: Path,
) -> None:
    python = make_venv(artifact_env / distribution)
    installed = install_one(python, wheels, distribution)
    assert installed.namespaces == allowed
    assert installed.namespaces.isdisjoint(forbidden | FORBIDDEN_SHARED)


@pytest.fixture
def artifact_env(tmp_path: Path) -> Path:
    return tmp_path
