from __future__ import annotations

import tomllib
from pathlib import Path


def test_dev_extra_contains_the_exact_root_build_backend() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    build_requirements = set(metadata["build-system"]["requires"])
    dev_requirements = set(metadata["project"]["optional-dependencies"]["dev"])

    assert "hatchling==1.32.4" in build_requirements
    assert build_requirements <= dev_requirements


def test_root_exchange_dependencies_use_compatible_exact_pins() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    requirements = set(metadata["project"]["dependencies"])

    assert "hyperliquid-python-sdk==0.24.0" in requirements
    assert "eth-account==0.13.7" in requirements
