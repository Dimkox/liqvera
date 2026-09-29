import json
import os
import site
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT_ID = "123e4567-e89b-42d3-a456-426614174021"
CAPTURE_ID = "123e4567-e89b-42d3-a456-426614174020"
ENGINE_COMMIT = "d" * 40


def _run(argv: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        capture_output=True,
        timeout=120,
    )


def test_installed_canonical_f3_builds_and_verifies_outside_checkout(tmp_path: Path) -> None:
    # Catches missing wheel resources/entry points and accidental source-checkout imports.
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    build_env = {**os.environ, "PIP_NO_INDEX": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    build_env.pop("PYTHONPATH", None)
    for package in ("contracts", "public-capture", "readonly-analyzer", "evidence-report"):
        _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(wheels),
                str(ROOT / "packages" / package),
            ],
            cwd=tmp_path,
            env=build_env,
        )

    environment = tmp_path / "venv"
    _run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(environment)],
        cwd=tmp_path,
        env=build_env,
    )
    python = environment / "bin" / "python"
    installed_env = {**build_env, "VIRTUAL_ENV": str(environment)}
    installed_env["PATH"] = f"{environment / 'bin'}:{build_env['PATH']}"
    # Reuse only the already provisioned pinned third-party dependencies. The
    # four Liqvera packages themselves must resolve from this isolated venv.
    installed_env["PYTHONPATH"] = os.pathsep.join(site.getsitepackages())
    _run(
        [
            str(python),
            "-m",
            "pip",
            "install",
            "--no-index",
            "--no-deps",
            "--force-reinstall",
            *[str(path) for path in sorted(wheels.glob("*.whl"))],
        ],
        cwd=tmp_path,
        env=installed_env,
    )

    locations = _run(
        [
            str(python),
            "-c",
            (
                "import mee_contracts, mee_public_capture, mee_readonly_analyzer, "
                "mee_evidence_report; "
                "print('\\n'.join(str(module.__file__) for module in "
                "(mee_contracts, mee_public_capture, mee_readonly_analyzer, mee_evidence_report)))"
            ),
        ],
        cwd=tmp_path,
        env=installed_env,
    ).stdout.splitlines()
    assert len(locations) == 4
    assert all(str(environment) in location for location in locations)
    assert all(str(ROOT) not in location for location in locations)

    captures = tmp_path / "captures"
    captures.mkdir()
    _run(
        [
            str(python),
            "-c",
            (
                "from pathlib import Path; from uuid import UUID; "
                "from mee_public_capture.evidence_package import capture_package; "
                f"capture_package(Path({str(captures)!r}), UUID({CAPTURE_ID!r}), source_mode='fixture')"
            ),
        ],
        cwd=tmp_path,
        env=installed_env,
    )
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    built = _run(
        [
            str(environment / "bin" / "mee-evidence-build"),
            "--package",
            str(captures / CAPTURE_ID),
            "--output-root",
            str(artifacts),
            "--report-id",
            REPORT_ID,
            "--side",
            "BUY",
            "--quantity",
            "0.15",
            "--engine-commit",
            ENGINE_COMMIT,
        ],
        cwd=tmp_path,
        env=installed_env,
    )
    receipt = json.loads(built.stdout)
    assert receipt["snapshot_status"] == "SIMULATED"
    assert receipt["chargeable"] is False
    assert receipt["execution_authority"] == "NONE"

    verified = _run(
        [
            str(environment / "bin" / "mee-evidence-verify"),
            str(artifacts / REPORT_ID / "evidence.zip"),
            "--report-sha256",
            receipt["report_sha256"],
        ],
        cwd=tmp_path,
        env=installed_env,
    )
    result = json.loads(verified.stdout)
    assert result == {
        "status": "INTEGRITY_REPRODUCED",
        "report_sha256": receipt["report_sha256"],
        "snapshot_status": "SIMULATED",
        "exchange_authenticity_verified": False,
        "execution_authority": "NONE",
    }
