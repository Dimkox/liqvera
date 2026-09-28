#!/usr/bin/env python3
"""Use Adaptive Grok v2.0.19's bounded parallel runner for Liqvera tests."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLING = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLING))

from adaptive_grok_pin import ToolingPinError, validate  # noqa: E402

try:
    SOURCE = validate(ROOT)
except ToolingPinError as exc:
    print(f"Adaptive Grok pin validation failed: {exc}", file=sys.stderr)
    raise SystemExit(2) from None

sys.path.insert(0, str(SOURCE / ".grok-stack"))

from adaptive_grok import python_test_runner, verification  # noqa: E402

PRODUCT_PYTHONPATH = (
    "packages/contracts/src",
    "packages/public-capture/src",
    "packages/readonly-analyzer/src",
    "packages/evidence-report/src",
)
TRIVY_SEVERITY = "MEDIUM,HIGH,CRITICAL"


def _container_config_targets(root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        return ()
    targets: list[str] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        relative = raw.decode("utf-8", "strict")
        name = Path(relative).name.lower()
        is_dockerfile = name.startswith("dockerfile") and not name.endswith(
            ".dockerignore"
        )
        is_compose = (
            name.startswith("compose.") or name.startswith("docker-compose.")
        ) and name.endswith((".yaml", ".yml"))
        if is_dockerfile or is_compose:
            targets.append(relative)
    return tuple(sorted(targets))


def _explicit_trivy(root: Path) -> verification.CheckResult:
    targets = _container_config_targets(root)
    if not targets:
        return verification.CheckResult(
            "trivy-config", "fail", "no tracked container configuration targets"
        )
    if not verification.command_exists("trivy"):
        return verification.CheckResult(
            "trivy-config", "fail", "trivy is required for container configuration"
        )
    checks = [
        verification._command_check(
            root,
            f"trivy-config:{target}",
            [
                "trivy",
                "config",
                "--exit-code",
                "1",
                "--severity",
                TRIVY_SEVERITY,
                target,
            ],
            300,
        )
        for target in targets
    ]
    failures = [item for item in checks if item.status != "pass"]
    return verification.CheckResult(
        "trivy-config",
        "fail" if failures else "pass",
        f"scanned={len(targets)} severity={TRIVY_SEVERITY} failures={len(failures)}",
        stdout="\n".join(item.stdout for item in checks if item.stdout)[-12000:],
        stderr="\n".join(item.stderr for item in checks if item.stderr)[-12000:],
        details=[
            {
                "severity": "error" if item.status != "pass" else "info",
                "path": target,
                "message": item.summary,
            }
            for target, item in zip(targets, checks, strict=True)
        ],
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
    verification._trivy_config = _explicit_trivy
    runpy.run_path(str(SOURCE / "scripts/grok_verify.py"), run_name="__main__")


if __name__ == "__main__":
    main()
