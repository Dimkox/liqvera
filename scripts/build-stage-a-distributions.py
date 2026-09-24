#!/usr/bin/env python3
"""Build the three Stage A wheels at an exact source SHA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.conformance.distributions import build_all
from tools.conformance.runner import ConformanceError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        built = build_all(args.source_sha, args.out, root=ROOT)
    except ConformanceError as error:
        print(error, file=sys.stderr)
        return 1
    print(
        json.dumps(
            [
                {"distribution": item.distribution, "path": str(item.path), "sha256": item.sha256}
                for item in built
            ],
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
