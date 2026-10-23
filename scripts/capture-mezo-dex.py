#!/usr/bin/env python3
"""Explicit read-only Testnet capture; never submits a transaction."""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for package in ("contracts", "public-capture"):
    sys.path.insert(0, str(ROOT / "packages" / package / "src"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", required=True, action="store_true")
    parser.add_argument("--side", choices=("BUY", "SELL"), required=True)
    parser.add_argument("--quantity", required=True, help="BTC decimal string")
    parser.add_argument("--output", type=Path, required=True, help="New JSON path; never overwritten")
    args = parser.parse_args()
    from liqvera_public_capture.public_adapters.mezo_dex import capture_live_dex
    try:
        import re
        if re.fullmatch(r"[0-9]{1,20}(?:\.[0-9]{1,18})?", args.quantity) is None:
            raise ValueError("MEZO_DEX_INVALID_INPUT")
        quantity = Fraction(args.quantity) * 10**18
        if quantity.denominator != 1 or quantity <= 0:
            raise ValueError("MEZO_DEX_INVALID_INPUT")
        capture = capture_live_dex(args.side, quantity.numerator)
        with args.output.open("x") as output:
            json.dump(capture, output, sort_keys=True, separators=(",", ":"))
            output.write("\n")
        print(json.dumps({"status": "CAPTURED", "source": capture["source"],
                          "block_number": str(int(capture["probe"]["block"]["result"]["number"], 16)),
                          "output": str(args.output)}))
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "REJECTED", "code": str(error) if isinstance(error, ValueError)
                          else "OUTPUT_UNAVAILABLE"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
