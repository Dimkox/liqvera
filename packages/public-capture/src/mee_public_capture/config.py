"""Fail-closed public-only process configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

ALLOWED_VENUES = ("hyperliquid", "lighter")
ALLOWED_MODES = ("public",)
ALLOWED_SOURCES = ("fixture", "public")
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


class PublicConfigError(RuntimeError):
    """Public capture configuration is unsafe or incomplete."""


@dataclass(frozen=True, slots=True)
class PublicCaptureConfig:
    venues: tuple[str, ...]
    mode: str
    source: str
    output: Path | None


def load_public_configuration(
    environ: Mapping[str, str] | None = None,
) -> PublicCaptureConfig:
    env = dict(os.environ if environ is None else environ)
    for key in env:
        upper = key.upper()
        if any(marker in upper for marker in _FORBIDDEN_ENV_MARKERS):
            raise PublicConfigError("credential environment is forbidden")
    raw_venues = env.get("MEE_PUBLIC_VENUES", "hyperliquid,lighter")
    venues = tuple(item.strip() for item in raw_venues.split(",") if item.strip())
    if not venues or any(venue not in ALLOWED_VENUES for venue in venues):
        raise PublicConfigError("venues must be the public Hyperliquid/Lighter pair")
    mode = env.get("MEE_PUBLIC_MODE", "public")
    if mode not in ALLOWED_MODES:
        raise PublicConfigError("mode must be public")
    source = env.get("MEE_CAPTURE_SOURCE", "fixture")
    if source not in ALLOWED_SOURCES:
        raise PublicConfigError("source must be fixture or public")
    raw_output = env.get("MEE_CAPTURE_OUT")
    output: Path | None = None
    if raw_output:
        output = Path(raw_output)
        if not output.is_absolute():
            raise PublicConfigError("MEE_CAPTURE_OUT must be an absolute path")
    return PublicCaptureConfig(venues=venues, mode=mode, source=source, output=output)
