"""Stage A product is the three canonical packages."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_stage_a_namespaces_import() -> None:
    import liqvera_contracts
    import liqvera_public_capture
    import liqvera_readonly_analyzer

    assert liqvera_contracts.__version__ == "0.2.0"
    assert liqvera_public_capture.__version__ == "0.2.0"
    assert liqvera_readonly_analyzer.__version__ == "0.2.0"
    assert liqvera_public_capture.Venue.HYPERLIQUID.value == "HYPERLIQUID"
    assert liqvera_contracts.EvidenceReader is not None
    assert liqvera_contracts.StageADecisionCode.INVALID_DATASET.value == "INVALID_DATASET"
    assert "GO" not in {item.value for item in liqvera_contracts.StageADecisionCode}
    assert "ClosedLifecycle" not in liqvera_public_capture.__all__


def test_stage_a_entrypoints_use_fail_closed_config() -> None:
    from liqvera_public_capture.config import load_public_configuration
    from liqvera_public_capture.runtime import run_public_capture
    from liqvera_readonly_analyzer.config import AnalyzerConfigError, load_analyzer_configuration

    assert run_public_capture(load_public_configuration({})) == 0
    try:
        load_analyzer_configuration({})
    except AnalyzerConfigError:
        return
    raise AssertionError("analyzer must reject a missing frozen package")


def test_stage_a_analyzer_rejects_credential_env_names(tmp_path: Path) -> None:
    from liqvera_readonly_analyzer.config import AnalyzerConfigError, load_analyzer_configuration

    with pytest.raises(AnalyzerConfigError, match="credential environment is forbidden"):
        load_analyzer_configuration(
            {"LIQVERA_FROZEN_PACKAGE": str(tmp_path), "VENUE_TOKEN": "1"}
        )


def test_stage_a_package_roots_exist() -> None:
    root = Path("packages")
    assert (root / "contracts").is_dir()
    assert (root / "public-capture").is_dir()
    assert (root / "readonly-analyzer").is_dir()
