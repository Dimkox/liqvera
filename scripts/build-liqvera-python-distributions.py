#!/usr/bin/env python3
"""Build the complete Liqvera Python wheel set from a clean source commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.conformance.distributions import build_all
from tools.conformance.runner import ConformanceError, require_clean_exact_head

REPORT_DISTRIBUTION = "liqvera-evidence-report"
REPORT_PACKAGE = Path("packages/evidence-report")


def _report_wheel(output: Path) -> Path:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "hatchling",
            "build",
            "--target",
            "wheel",
            "--directory",
            str(output),
        ],
        cwd=ROOT / REPORT_PACKAGE,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise ConformanceError(completed.stderr or completed.stdout or "report wheel build failed")
    wheels = sorted(output.glob("liqvera_evidence_report-*.whl"))
    if len(wheels) != 1:
        raise ConformanceError(f"expected exactly one report wheel, got {wheels}")
    return wheels[0]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.out.resolve()
    try:
        require_clean_exact_head(args.source_sha, ROOT)
        stage_a = build_all(args.source_sha, output, root=ROOT, require_clean=False)
        report = _report_wheel(output)
    except ConformanceError as error:
        print(error, file=sys.stderr)
        return 1
    artifacts = [
        *(
            {"distribution": item.distribution, "path": str(item.path), "sha256": item.sha256}
            for item in stage_a
        ),
        {
            "distribution": REPORT_DISTRIBUTION,
            "path": str(report),
            "sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
        },
    ]
    print(json.dumps({"source_sha": args.source_sha, "artifacts": artifacts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
