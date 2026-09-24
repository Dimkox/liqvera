"""Install mee-contracts into a fresh venv outside the checkout."""

from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "packages" / "contracts"
INSPECT = ROOT / "scripts" / "inspect-installed-distribution.py"


def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )


def test_contracts_wheel_installs_outside_checkout(tmp_path: Path) -> None:
    build_root = tmp_path / "contracts-src"
    build_venv = tmp_path / "build-venv"
    install_venv = tmp_path / "contracts-venv"
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    shutil.copytree(
        CONTRACTS,
        build_root,
        ignore=shutil.ignore_patterns("dist", "*.egg-info", "__pycache__"),
    )
    venv.EnvBuilder(with_pip=True, symlinks=True).create(build_venv)
    venv.EnvBuilder(with_pip=True, symlinks=True).create(install_venv)
    build_python = build_venv / "bin" / "python"
    install_python = install_venv / "bin" / "python"
    _run([str(build_python), "-m", "pip", "install", "hatchling==1.31.0"])
    _run(
        [
            str(build_python),
            "-m",
            "hatchling",
            "build",
            "--target",
            "wheel",
        ],
        cwd=build_root,
    )
    produced = sorted((build_root / "dist").glob("mee_contracts-0.1.0-py3-none-any.whl"))
    assert produced, "expected mee_contracts 0.1.0 wheel"
    wheel = produced[-1]
    copied = dist_dir / wheel.name
    copied.write_bytes(wheel.read_bytes())
    _run(
        [
            str(install_python),
            "-m",
            "pip",
            "install",
            "--no-deps",
            str(copied),
        ]
    )
    probe = _run(
        [
            str(install_python),
            "-I",
            "-c",
            "import mee_contracts; from mee_contracts.evidence import EvidenceReader; "
            "assert EvidenceReader.__module__ == 'mee_contracts.evidence'",
        ],
        cwd=tmp_path,
    )
    assert probe.returncode == 0
    inspect = _run(
        [
            sys.executable,
            str(INSPECT),
            "--python",
            str(install_python),
            "--distribution",
            "mee-contracts",
            "--allow-namespace",
            "mee_contracts",
            "--forbid-namespace",
            "mee_public_capture",
            "mee_readonly_analyzer",
            "multi_exchange_engine",
            "--forbid-dependency",
            "httpx",
            "websockets",
            "psycopg",
            "asyncpg",
            "hyperliquid-python-sdk",
            "eth-account",
        ]
    )
    assert "installed boundary passed: mee-contracts" in inspect.stdout
