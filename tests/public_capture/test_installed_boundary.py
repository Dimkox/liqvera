"""Install liqvera-public-capture into a fresh venv outside the checkout."""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tomllib
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "packages" / "contracts"
CAPTURE = ROOT / "packages" / "public-capture"
SRC = CAPTURE / "src" / "liqvera_public_capture"
INSPECT = ROOT / "scripts" / "inspect-installed-distribution.py"


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def _build_wheel(python: Path, source: Path, name: str, tmp_path: Path) -> Path:
    build_root = tmp_path / f"{name}-src"
    shutil.copytree(
        source,
        build_root,
        ignore=shutil.ignore_patterns("dist", "*.egg-info", "__pycache__"),
    )
    _run([str(python), "-m", "hatchling", "build", "--target", "wheel"], cwd=build_root)
    wheels = sorted((build_root / "dist").glob(f"{name}-0.2.0-py3-none-any.whl"))
    assert wheels, f"expected {name} 0.2.0 wheel"
    return wheels[-1]


def test_public_capture_metadata_and_source_boundary() -> None:
    metadata = tomllib.loads((CAPTURE / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["name"] == "liqvera-public-capture"
    assert metadata["project"]["scripts"] == {
        "liqvera-public-capture": "liqvera_public_capture.__main__:main",
        "liqvera-evidence-capture-service": "liqvera_public_capture.evidence_service:main",
    }
    assert metadata["project"]["dependencies"] == [
        "liqvera-contracts==0.2.0",
        "httpx==0.28.1",
        "websockets==17.1",
    ]
    forbidden = {
        "liqvera_workspace",
        "liqvera_readonly_analyzer",
        "psycopg",
        "asyncpg",
        "eth_account",
    }
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
        assert imported.isdisjoint(forbidden), path


def test_public_capture_has_only_public_entry_point(tmp_path: Path) -> None:
    build_venv = tmp_path / "build-venv"
    install_venv = tmp_path / "capture-venv"
    venv.EnvBuilder(with_pip=True, symlinks=True).create(build_venv)
    venv.EnvBuilder(with_pip=True, symlinks=True).create(install_venv)
    build_python = build_venv / "bin" / "python"
    install_python = install_venv / "bin" / "python"
    _run([str(build_python), "-m", "pip", "install", "hatchling==1.32.4"])
    contracts_wheel = _build_wheel(build_python, CONTRACTS, "liqvera_contracts", tmp_path)
    capture_wheel = _build_wheel(build_python, CAPTURE, "liqvera_public_capture", tmp_path)
    _run([str(install_python), "-m", "pip", "install", "--no-deps", str(contracts_wheel)])
    _run([str(install_python), "-m", "pip", "install", "--no-deps", str(capture_wheel)])
    probe = _run(
        [
            str(install_python),
            "-I",
            "-c",
            "import importlib.metadata, liqvera_public_capture;"
            "eps=importlib.metadata.entry_points();"
            "group=eps.select(group='console_scripts') if hasattr(eps,'select') else [];"
            "scripts={item.name: item.value for item in group};"
            "print(scripts['liqvera-public-capture']);"
            "assert 'liqvera_readonly_analyzer' not in liqvera_public_capture.__name__;"
            "import liqvera_public_capture as pkg;"
            "assert pkg.__name__=='liqvera_public_capture'",
        ],
        cwd=tmp_path,
    )
    assert probe.stdout.strip() == "liqvera_public_capture.__main__:main"
    missing = _run(
        [
            str(install_python),
            "-I",
            "-c",
            "import importlib.util, json;"
            "print(json.dumps({"
            "'analyzer': importlib.util.find_spec('liqvera_readonly_analyzer') is not None,"
            "'legacy': importlib.util.find_spec('liqvera_workspace') is not None"
            "}))",
        ],
        cwd=tmp_path,
    )
    leaked = json.loads(missing.stdout)
    assert leaked == {"analyzer": False, "legacy": False}
    inspect = _run(
        [
            sys.executable,
            str(INSPECT),
            "--python",
            str(install_python),
            "--distribution",
            "liqvera-public-capture",
            "--allow-namespace",
            "liqvera_public_capture",
            "--forbid-namespace",
            "liqvera_readonly_analyzer",
            "liqvera_workspace",
            "--allow-dependency",
            "liqvera-contracts",
            "httpx",
            "websockets",
            "--forbid-dependency",
            "psycopg",
            "asyncpg",
            "hyperliquid-python-sdk",
            "eth-account",
            "--forbid-symbol",
            "signer",
            "wallet",
            "order",
            "cancel",
            "amend",
            "withdraw",
            "transfer",
            "private",
            "account",
        ]
    )
    assert "installed boundary passed: liqvera-public-capture" in inspect.stdout
    launched = _run(
        [
            str(install_python),
            "-I",
            "-c",
            "from liqvera_public_capture.config import load_public_configuration;"
            "from liqvera_public_capture.runtime import run_public_capture;"
            "raise SystemExit(run_public_capture(load_public_configuration({})))",
        ],
        cwd=tmp_path,
    )
    assert launched.returncode == 0
