"""Hypothesis: Dockerfiles are wheel-only and images do not copy repository source."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
IMAGES = (
    ROOT / "deploy" / "images" / "Dockerfile.public-capture",
    ROOT / "deploy" / "images" / "Dockerfile.readonly-analyzer",
)
COMPOSE = ROOT / "compose.stage-a.yml"
MAKEFILE = ROOT / "Makefile"


def test_dockerfiles_copy_wheels_not_source_trees() -> None:
    for path in IMAGES:
        text = path.read_text(encoding="utf-8")
        assert "COPY dist/" in text
        assert "COPY packages/" not in text
        assert "COPY cmd/" not in text
        assert "COPY internal/" not in text
        assert "go.mod" not in text
        assert "multi_exchange_engine" not in text
        assert "ENTRYPOINT" in text


def test_dockerfiles_use_digest_pinned_python_base() -> None:
    pin = "python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d"
    for path in IMAGES:
        assert pin in path.read_text(encoding="utf-8")


def test_images_default_to_data_volume_without_credentials() -> None:
    capture = IMAGES[0].read_text(encoding="utf-8")
    analyzer = IMAGES[1].read_text(encoding="utf-8")
    assert "ENV MEE_CAPTURE_OUT=/data" in capture
    assert "ENV MEE_FROZEN_PACKAGE=/data" in analyzer
    stack_text = COMPOSE.read_text(encoding="utf-8")
    assert "mee-public-capture:stage-a" in stack_text
    assert "mee-readonly-analyzer:stage-a" in stack_text
    lowered = stack_text.casefold()
    assert "password" not in lowered
    assert "secret" not in lowered
    assert "token" not in lowered
    assert "env_file" not in lowered


def test_prod_wraps_fixture_compose_stack() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "docker compose -f compose.stage-a.yml" in makefile
    assert "docker volume create" not in makefile
    stack = yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))
    assert stack["name"] == "mee-stage-a"
    assert stack["volumes"]["package"]["name"] == "mee-stage-a-data"
    prepare = stack["services"]["prepare-data"]
    capture = stack["services"]["capture"]
    analyzer = stack["services"]["analyzer"]
    assert prepare["user"] == "0:0"
    assert capture["user"] == "65534:65534"
    assert analyzer["user"] == "65534:65534"
    assert capture["environment"]["MEE_CAPTURE_SOURCE"] == "fixture"
    assert analyzer["volumes"] == ["package:/data:ro"]
    for service in (prepare, capture, analyzer):
        assert service["network_mode"] == "none"
        assert "env_file" not in service
        assert "ports" not in service
        assert "privileged" not in service
