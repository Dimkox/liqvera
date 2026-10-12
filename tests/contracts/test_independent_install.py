"""Install liqvera-contracts into a fresh venv outside the checkout."""

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
    _run([str(build_python), "-m", "pip", "install", "hatchling==1.32.4"])
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
    produced = sorted((build_root / "dist").glob("liqvera_contracts-0.2.0-py3-none-any.whl"))
    assert produced, "expected liqvera_contracts 0.2.0 wheel"
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
            "import liqvera_contracts; from liqvera_contracts.evidence import EvidenceReader; "
            "assert EvidenceReader.__module__ == 'liqvera_contracts.evidence'",
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
            "liqvera-contracts",
            "--allow-namespace",
            "liqvera_contracts",
            "--forbid-namespace",
            "liqvera_public_capture",
            "liqvera_readonly_analyzer",
            "liqvera_workspace",
            "--forbid-dependency",
            "httpx",
            "websockets",
            "psycopg",
            "asyncpg",
            "hyperliquid-python-sdk",
            "eth-account",
        ]
    )
    assert "installed boundary passed: liqvera-contracts" in inspect.stdout
