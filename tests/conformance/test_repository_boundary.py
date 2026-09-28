"""Repository-only dependencies stay pinned and outside the Liqvera product tree."""

from __future__ import annotations

import configparser
import hashlib
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADAPTIVE_GROK_PATH = "tooling/adaptive-grok-build-pro"
ADAPTIVE_GROK_COMMIT = "cb9af4073ba6c3d515145164d771c75ebdfa3224"


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def _load_launcher():
    spec = importlib.util.spec_from_file_location(
        "liqvera_adaptive_grok_launcher", ROOT / "tooling/run-adaptive-grok.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_inherited_go_stage_zero_is_not_tracked() -> None:
    tracked = set(_git("ls-files").splitlines())

    assert "go.mod" not in tracked
    assert "go.sum" not in tracked
    assert "Dockerfile" not in tracked
    assert "migrations/000001_init.up.sql" not in tracked
    assert "migrations/000001_init.down.sql" not in tracked
    assert not {path for path in tracked if path.endswith(".go")}
    assert not {path for path in tracked if path.startswith(("cmd/", "internal/"))}


def test_preserved_data_and_provenance_are_byte_identical() -> None:
    assert {
        "migrations/000002_a2_raw_capture.up.sql": _sha256(
            "migrations/000002_a2_raw_capture.up.sql"
        ),
        "migrations/000002_a2_raw_capture.down.sql": _sha256(
            "migrations/000002_a2_raw_capture.down.sql"
        ),
        "apps/mezo-gateway/migrations/001_ledger.sql": _sha256(
            "apps/mezo-gateway/migrations/001_ledger.sql"
        ),
        "packages/evidence-report/migrations/001_local_demo.sql": _sha256(
            "packages/evidence-report/migrations/001_local_demo.sql"
        ),
        "provenance/import-manifest.json": _sha256("provenance/import-manifest.json"),
        "schemas/mezo-evidence/v1/vectors.json": _sha256(
            "schemas/mezo-evidence/v1/vectors.json"
        ),
    } == {
        "migrations/000002_a2_raw_capture.up.sql": (
            "51fd413e55005752f9d19779a71bfee45a00b9c8e9a7d73320142564fba29244"
        ),
        "migrations/000002_a2_raw_capture.down.sql": (
            "b373e028f9a291add6c9e10b486901f25ceff294840d353a7c37348b1ca0cf20"
        ),
        "apps/mezo-gateway/migrations/001_ledger.sql": (
            "bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b"
        ),
        "packages/evidence-report/migrations/001_local_demo.sql": (
            "d8c7cac0d725214d42edb9ecd8a70c52d4610974fe0cb69a40f383beef77d3da"
        ),
        "provenance/import-manifest.json": (
            "a672596489fe75e208c607ac8040044dc3d00fc486bef1483f5ac4565b5b0993"
        ),
        "schemas/mezo-evidence/v1/vectors.json": (
            "606a4a2a406c71456aa0ade984f613c10bdef46a6ac020a953b8d3b6386717cc"
        ),
    }


def test_adaptive_grok_static_pin_is_a_v2019_gitlink() -> None:
    lock = json.loads((ROOT / "tooling/tooling-lock.json").read_text())
    pin = lock["adaptive_grok_build_pro"]
    assert pin == {
        "version": "2.0.19",
        "tag": "v2.0.19",
        "commit": ADAPTIVE_GROK_COMMIT,
        "repository": "https://github.com/Dimkox/adaptive-grok-build-pro.git",
        "release_asset_sha256": (
            "4176a872acdca873e840855d0b2c9e379cf8f796c9de69e5560b3e2bf85634b9"
        ),
    }
    index = _git("ls-files", "-s", "--", ADAPTIVE_GROK_PATH).split()
    assert index[:2] == ["160000", ADAPTIVE_GROK_COMMIT]
    gitmodules = (ROOT / ".gitmodules").read_text()
    assert "https://github.com/Dimkox/adaptive-grok-build-pro.git" in gitmodules


def test_adaptive_grok_launcher_fails_closed_before_execution(tmp_path: Path) -> None:
    launcher = _load_launcher()
    lock_path = tmp_path / "tooling/tooling-lock.json"
    lock_path.parent.mkdir()
    lock_path.write_text(
        json.dumps(
            {
                "adaptive_grok_build_pro": {
                    "version": "2.0.18",
                    "tag": "v2.0.18",
                    "commit": ADAPTIVE_GROK_COMMIT,
                    "repository": "https://github.com/Dimkox/adaptive-grok-build-pro.git",
                    "release_asset_sha256": "0" * 64,
                }
            }
        )
    )
    with pytest.raises(launcher.ToolingPinError, match="lock does not match"):
        launcher.validate(tmp_path)

    lock_path.write_text((ROOT / "tooling/tooling-lock.json").read_text())
    with pytest.raises(launcher.ToolingPinError, match="submodule is missing"):
        launcher.validate(tmp_path)


def test_factory_discovery_paths_are_thin_links_to_the_gitlink() -> None:
    expected_links = {
        ".agents/skills": "../tooling/adaptive-grok-build-pro/.agents/skills",
        ".grok/agents": "../tooling/adaptive-grok-build-pro/.grok/agents",
        ".grok/skills": "../tooling/adaptive-grok-build-pro/.grok/skills",
        ".grok/hooks": "../tooling/adaptive-grok-build-pro/.grok/hooks",
        ".grok-stack/adaptive_grok": "../tooling/adaptive-grok-build-pro/.grok-stack/adaptive_grok",
        ".grok-stack/templates": "../tooling/adaptive-grok-build-pro/.grok-stack/templates",
        "scripts/grok_verify.py": "../tooling/run-adaptive-grok.py",
    }
    expected_links.update(
        {
            f"scripts/grok_{name}.py": "../tooling/run-adaptive-grok.py"
            for name in (
                "approve",
                "change",
                "deploy",
                "doctor",
                "review",
                "route",
                "status",
            )
        }
    )
    for relative, target in expected_links.items():
        path = ROOT / relative
        assert path.is_symlink(), relative
        assert os.readlink(path) == target

    assert os.access(ROOT / "tooling/run-adaptive-grok.py", os.X_OK)


def test_parallel_verifier_is_explicitly_enabled() -> None:
    assert json.loads((ROOT / ".grok-test-runner.json").read_text()) == {
        "schema_version": 1,
        "workers": "auto",
    }
    assert (ROOT / "tooling/grok-verify.py").is_file()


def test_coverage_baseline_measures_only_liqvera_owned_sources() -> None:
    config = configparser.ConfigParser()
    config.read(ROOT / ".coveragerc")

    assert {line.strip() for line in config.get("run", "source").splitlines() if line.strip()} == {
        "packages/contracts/src/mee_contracts",
        "packages/public-capture/src/mee_public_capture",
        "packages/readonly-analyzer/src/mee_readonly_analyzer",
        "packages/evidence-report/src/mee_evidence_report",
        "tools/conformance",
        "tools/graph_checker",
        "tools/mezo_acceptance",
    }
    assert config.getint("report", "fail_under") == 59


def test_bmad_is_locked_but_not_vendored() -> None:
    lock = json.loads((ROOT / "tooling/tooling-lock.json").read_text())
    assert lock["bmad_method"] == {
        "package": "bmad-method",
        "version": "6.10.0",
        "tarball": "https://registry.npmjs.org/bmad-method/-/bmad-method-6.10.0.tgz",
        "integrity": (
            "sha512-Z14VEk9R7JE0d016BLPiJPNcsS/ZIu97rC/76Ahe1IN7Wkqz3pK6Frljf5/FH8NZGOBawDY5SLyCybFcPJ/eMw=="
        ),
    }
    tracked = set(_git("ls-files").splitlines())
    assert not {path for path in tracked if path == "_bmad" or path.startswith("_bmad/")}
    assert not {path for path in tracked if path.startswith(".agents/skills/bmad-")}


def test_actual_product_dockerfiles_are_explicitly_scannable() -> None:
    dockerfiles = sorted(
        path
        for path in _git("ls-files", "*Dockerfile*").splitlines()
        if not path.endswith(".dockerignore")
    )
    assert dockerfiles == [
        "deploy/images/Dockerfile.public-capture",
        "deploy/images/Dockerfile.readonly-analyzer",
        "deploy/mezo-evidence/Dockerfile.capture",
        "deploy/mezo-evidence/Dockerfile.edge",
        "deploy/mezo-evidence/Dockerfile.gateway",
        "deploy/mezo-evidence/Dockerfile.report",
        "deploy/mezo-evidence/Dockerfile.web",
    ]
