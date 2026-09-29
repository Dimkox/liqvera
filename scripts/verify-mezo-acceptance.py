#!/usr/bin/env python3
"""Reload and verify a sealed Liqvera acceptance result and all bindings."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mezo_acceptance.runner import verify_sealed_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    result = verify_sealed_result(args.result.resolve(), args.sha256)
    print(f"VERIFIED: {result['overall_status']} {args.result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
