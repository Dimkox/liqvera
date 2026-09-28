#!/usr/bin/env python3
"""Use Adaptive Grok v2.0.19's bounded parallel runner for Liqvera tests."""

from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tooling/adaptive-grok-build-pro"
sys.path.insert(0, str(SOURCE / ".grok-stack"))

from adaptive_grok import python_test_runner, verification  # noqa: E402

PRODUCT_PYTHONPATH = (
    "packages/contracts/src",
    "packages/public-capture/src",
    "packages/readonly-analyzer/src",
    "packages/evidence-report/src",
)


def _parallel_python(root: Path, mode: str) -> list[verification.CheckResult]:
    """Run Liqvera tests through v2.0.19's bounded xdist implementation."""

    results = [verification._ruff(root), verification._bandit(root)]
    try:
        requested = python_test_runner.selected_workers(root)
        if requested is None or requested < 1:
            raise python_test_runner.RunnerError(
                "Liqvera requires a positive parallel worker selection"
            )
        effective, engine = python_test_runner.select_engine(
            requested, measured=mode in {"pr", "release"}
        )
        if effective != requested or engine != "pytest-xdist":
            raise python_test_runner.RunnerError(
                "Liqvera parallel verification cannot use pytest-xdist"
            )
        previous_pythonpath = os.environ.get("PYTHONPATH")
        project_paths = [str(root / relative) for relative in PRODUCT_PYTHONPATH]
        if previous_pythonpath:
            project_paths.append(previous_pythonpath)
        os.environ["PYTHONPATH"] = os.pathsep.join(project_paths)
        original_command = python_test_runner._pytest_command

        def liqvera_command(workers: int, distribution: str) -> list[str]:
            return [
                *original_command(workers, distribution),
                "--ignore=tests/release",
                "-m",
                "not live",
            ]

        python_test_runner._pytest_command = liqvera_command
        try:
            core = python_test_runner.run_core_tests(root, mode, requested)
        finally:
            python_test_runner._pytest_command = original_command
            if previous_pythonpath is None:
                os.environ.pop("PYTHONPATH", None)
            else:
                os.environ["PYTHONPATH"] = previous_pythonpath
        if core.workers < 1:
            raise python_test_runner.RunnerError(
                "Liqvera parallel verification degraded to a serial engine"
            )
    except python_test_runner.RunnerError as exc:
        results.append(verification.CheckResult("python-unittest", "fail", str(exc)))
        if mode in {"pr", "release"}:
            results.append(
                verification.CheckResult(
                    "coverage", "fail", "required parallel Core run unavailable"
                )
            )
        return results

    for name, process in (("python-unittest", core.tests), ("coverage", core.coverage)):
        if process is None:
            continue
        results.append(
            verification.CheckResult(
                name,
                "pass" if process.returncode == 0 else "fail",
                f"pytest-xdist workers={core.workers} exit={process.returncode} "
                f"seconds={process.seconds:.3f}",
                command=process.command,
                stdout=process.stdout[-12000:],
                stderr=process.stderr[-12000:],
                details=[
                    {
                        "severity": "info",
                        "path": "tests",
                        "message": "backend=pytest-xdist; fresh invocation-owned coverage",
                        "requested_workers": str(requested),
                        "versions": json.dumps(core.versions, sort_keys=True),
                        "coverage": json.dumps(core.coverage_metadata, sort_keys=True),
                    }
                ],
            )
        )
    return results


def main() -> None:
    verification._python = _parallel_python
    runpy.run_path(str(SOURCE / "scripts/grok_verify.py"), run_name="__main__")


if __name__ == "__main__":
    main()
