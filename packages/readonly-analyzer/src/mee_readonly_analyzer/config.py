"""Fail-closed read-only analyzer configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_FORBIDDEN_ENV_MARKERS = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PRIVATE",
    "WALLET",
    "SIGNER",
    "API_KEY",
    "APIKEY",
)


class AnalyzerConfigError(RuntimeError):
    """Analyzer configuration is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class AnalyzerConfig:
    package_root: Path


def load_analyzer_configuration(
    environ: Mapping[str, str] | None = None,
) -> AnalyzerConfig:
    env = dict(os.environ if environ is None else environ)
    for key in env:
        if any(marker in key.upper() for marker in _FORBIDDEN_ENV_MARKERS):
            raise AnalyzerConfigError("credential environment is forbidden")
    raw = env.get("MEE_FROZEN_PACKAGE")
    if not raw:
        raise AnalyzerConfigError("MEE_FROZEN_PACKAGE is required")
    root = Path(raw)
    if not root.is_absolute() or not root.exists() or not root.is_dir():
        raise AnalyzerConfigError("frozen package path is invalid")
    return AnalyzerConfig(package_root=root)
