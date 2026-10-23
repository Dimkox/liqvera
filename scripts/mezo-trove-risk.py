#!/usr/bin/env python3
"""Repository wrapper: fixed-block Testnet risk preview, without wallet or payment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package in ("contracts", "readonly-analyzer", "public-capture", "evidence-report"):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))


def main():
    if any(arg in ("--help", "-h") for arg in sys.argv[1:]):
        from liqvera_evidence_report.trove_cli import main as cli

        return cli(["--help"])
    # Bind live preview output to actual committed code, including ABI/schema inputs.
    paths = [
        "packages/contracts",
        "packages/readonly-analyzer",
        "packages/public-capture",
        "packages/evidence-report",
        "packages/mezo-protocol",
        "schemas",
        "requirements.lock",
        "scripts/mezo-trove-risk.py",
    ]
    if subprocess.check_output(["git", "status", "--porcelain", "--", *paths], cwd=ROOT):
        print(json.dumps({"status": "REJECTED", "code": "SOURCE_TREE_DIRTY"}), file=sys.stderr)
        return 2
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    from liqvera_evidence_report.trove_cli import main as cli

    if any(arg == "--engine-commit" or arg.startswith("--engine-commit=") for arg in sys.argv[1:]):
        print(
            json.dumps({"status": "REJECTED", "code": "ENGINE_REVISION_OVERRIDE"}), file=sys.stderr
        )
        return 2
    return cli([*sys.argv[1:], "--engine-commit", revision])


if __name__ == "__main__":
    raise SystemExit(main())
