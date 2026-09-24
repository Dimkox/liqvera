#!/usr/bin/env python3
"""Run the fixture-only Liqvera F3 MVP demonstration."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _validated_mvp_root(repository_root: Path) -> Path:
    repository_root = repository_root.resolve()
    mvp_root = repository_root / ".mvp"
    if mvp_root.is_symlink():
        raise RuntimeError("refusing a symlinked .mvp directory")
    resolved = mvp_root.resolve()
    if resolved.parent != repository_root or resolved.name != ".mvp":
        raise RuntimeError("MVP output root escaped the repository")
    resolved.mkdir(mode=0o755, exist_ok=True)
    return resolved


def _clean_owned_directory(mvp_root: Path, target: Path) -> Path:
    resolved = target.resolve()
    try:
        relative = resolved.relative_to(mvp_root)
    except ValueError as error:
        raise RuntimeError("MVP cleanup target escaped .mvp") from error
    if relative not in (Path("package"), Path("output")):
        raise RuntimeError("MVP cleanup is limited to package and output")
    if target.is_symlink():
        raise RuntimeError("refusing a symlinked MVP cleanup target")
    if target.exists():
        if not target.is_dir():
            raise RuntimeError("MVP cleanup target is not a directory")
        shutil.rmtree(target)
    return target


def main() -> int:
    from mee_evidence_report import cli as report_cli
    from mee_public_capture.config import load_public_configuration
    from mee_public_capture.runtime import run_public_capture

    repository_root = Path(__file__).resolve().parents[1]
    mvp_root = _validated_mvp_root(repository_root)
    package_root = _clean_owned_directory(mvp_root, mvp_root / "package")
    output_root = _clean_owned_directory(mvp_root, mvp_root / "output")
    package_root.mkdir(mode=0o755)

    side = os.environ.get("MVP_SIDE", "BUY")
    quantity = os.environ.get("MVP_QUANTITY", "0.15")

    print("Liqvera F3 MVP: SIMULATED / UNVERIFIED fixture demonstration")
    print("Payments and live verification are not implemented.")

    capture_config = load_public_configuration(
        {
            "MEE_PUBLIC_VENUES": "hyperliquid",
            "MEE_PUBLIC_MODE": "public",
            "MEE_CAPTURE_SOURCE": "fixture",
            "MEE_CAPTURE_OUT": str(package_root),
        }
    )
    capture_exit = run_public_capture(capture_config)
    if capture_exit != 0:
        print(f"Fixture capture failed with exit code {capture_exit}.")
        return capture_exit

    report_exit = report_cli.main(
        [
            "--package",
            str(package_root),
            "--output",
            str(output_root),
            "--side",
            side,
            "--quantity",
            quantity,
        ]
    )
    if report_exit != 0:
        return report_exit

    print(f"MVP report: {output_root / 'report.json'}")
    print(f"MVP evidence: {output_root / 'evidence.zip'}")
    print("SIMULATED / UNVERIFIED: Payments and live verification are not implemented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
