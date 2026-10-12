from __future__ import annotations

import tomllib
from pathlib import Path


def test_dev_extra_contains_the_exact_root_build_backend() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    build_requirements = set(metadata["build-system"]["requires"])
    dev_requirements = set(metadata["project"]["optional-dependencies"]["dev"])

    assert "hatchling==1.32.4" in build_requirements
    assert build_requirements <= dev_requirements


def test_root_workspace_has_no_trading_sdk() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    requirements = metadata["project"]["dependencies"]
    assert not any("sdk" in name or "eth-account" in name for name in requirements)
