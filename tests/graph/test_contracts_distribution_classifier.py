"""Classifier coverage for the M1 mee_contracts distribution."""

from __future__ import annotations

import pytest

from tools.graph_checker.loader import _classify_repository_path


@pytest.mark.parametrize(
    ("path", "expected"),
    (
        ("packages/contracts/pyproject.toml", "CONFIGURATION"),
        ("packages/contracts/src/mee_contracts/market.py", "RUNTIME_SOURCE"),
        ("packages/contracts/src/mee_contracts/decision.py", "RUNTIME_SOURCE"),
        ("packages/contracts/src/mee_contracts/economics.py", "RUNTIME_SOURCE"),
        ("packages/public-capture/pyproject.toml", "CONFIGURATION"),
        ("packages/public-capture/src/mee_public_capture/__main__.py", "RUNTIME_SOURCE"),
        ("packages/readonly-analyzer/pyproject.toml", "CONFIGURATION"),
        ("packages/readonly-analyzer/src/mee_readonly_analyzer/__main__.py", "RUNTIME_SOURCE"),
        ("packages/readonly-analyzer/src/mee_readonly_analyzer/verdict.py", "RUNTIME_SOURCE"),
        (
            "packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/common.py",
            "RUNTIME_SOURCE",
        ),
        (
            "packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/hyperliquid.py",
            "RUNTIME_SOURCE",
        ),
        (
            "packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/lighter.py",
            "RUNTIME_SOURCE",
        ),
        ("packages/readonly-analyzer/src/mee_readonly_analyzer/vwap.py", "RUNTIME_SOURCE"),
        ("packages/readonly-analyzer/src/mee_readonly_analyzer/identity.py", "RUNTIME_SOURCE"),
        ("tests/readonly_analyzer/test_reconstruction_hyperliquid.py", "TEST_SOURCE"),
        ("tests/readonly_analyzer/test_reconstruction_lighter.py", "TEST_SOURCE"),
        ("tests/readonly_analyzer/test_vwap.py", "TEST_SOURCE"),
        ("tests/readonly_analyzer/test_identity.py", "TEST_SOURCE"),
        ("Makefile", "CONFIGURATION"),
        (".grok/hooks.json", "VENDORED_TOOLING"),
        ("scripts/grok_verify.py", "VENDORED_TOOLING"),
        ("packages/evil/execution.py", "EXECUTION_SOURCE"),
        ("deploy/images/Dockerfile.public-capture", "BUILD_PACKAGING"),
        ("deploy/images/Dockerfile.readonly-analyzer", "BUILD_PACKAGING"),
        ("deploy/n8n/stage-a-orchestrator.workflow.json", "DEPLOYMENT_ENTRYPOINT"),
        ("compose.stage-a.yml", "COMPOSE"),
    ),
)
def test_contracts_distribution_paths_are_classified(path: str, expected: str) -> None:
    assert _classify_repository_path(path).value == expected
