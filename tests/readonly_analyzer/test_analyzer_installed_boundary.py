"""Install mee-readonly-analyzer into a fresh venv outside the checkout."""

from __future__ import annotations

import ast
import shutil
import subprocess
import sys
import tomllib
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "packages" / "contracts"
ANALYZER = ROOT / "packages" / "readonly-analyzer"
SRC = ANALYZER / "src" / "mee_readonly_analyzer"
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
    wheels = sorted((build_root / "dist").glob(f"{name}-0.1.0-py3-none-any.whl"))
    assert wheels, f"expected {name} 0.1.0 wheel"
    return wheels[-1]


def test_analyzer_source_has_no_writer_or_network() -> None:
    metadata = tomllib.loads((ANALYZER / "pyproject.toml").read_text(encoding="utf-8"))
    assert metadata["project"]["dependencies"] == ["mee-contracts==0.1.0"]
    assert metadata["project"]["scripts"] == {
        "mee-readonly-analyzer": "mee_readonly_analyzer.__main__:main"
    }
    forbidden = {
        "httpx",
        "websockets",
        "psycopg",
        "multi_exchange_engine",
        "mee_public_capture",
        "aiohttp",
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
        source = path.read_text(encoding="utf-8")
        assert "write_frozen_package" not in source
        assert "atomic_write" not in source


def test_analyzer_wheel_installs_outside_checkout(tmp_path: Path) -> None:
    build_venv = tmp_path / "build-venv"
    install_venv = tmp_path / "analyzer-venv"
    venv.EnvBuilder(with_pip=True, symlinks=True).create(build_venv)
    venv.EnvBuilder(with_pip=True, symlinks=True).create(install_venv)
    build_python = build_venv / "bin" / "python"
    install_python = install_venv / "bin" / "python"
    _run([str(build_python), "-m", "pip", "install", "hatchling==1.31.0"])
    contracts = _build_wheel(build_python, CONTRACTS, "mee_contracts", tmp_path)
    analyzer = _build_wheel(build_python, ANALYZER, "mee_readonly_analyzer", tmp_path)
    _run([str(install_python), "-m", "pip", "install", "--no-deps", str(contracts)])
    _run([str(install_python), "-m", "pip", "install", "--no-deps", str(analyzer)])
    inspect = _run(
        [
            sys.executable,
            str(INSPECT),
            "--python",
            str(install_python),
            "--distribution",
            "mee-readonly-analyzer",
            "--allow-namespace",
            "mee_readonly_analyzer",
            "--forbid-namespace",
            "mee_public_capture",
            "multi_exchange_engine",
            "--allow-dependency",
            "mee-contracts",
            "--forbid-dependency",
            "httpx",
            "websockets",
            "hyperliquid-python-sdk",
            "eth-account",
            "--forbid-symbol",
            "signer",
            "wallet",
            "cancel",
            "amend",
            "withdraw",
            "transfer",
            "write_frozen_package",
            "atomic_write",
        ]
    )
    assert "installed boundary passed: mee-readonly-analyzer" in inspect.stdout
