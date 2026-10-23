#!/usr/bin/env python3
"""Produce core A01–A30 or separate retained-proof A31/A32 evidence from an explicit plan."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mezo_acceptance.runner import main

if __name__ == "__main__":
    selector = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    selector.add_argument("--suite", choices=["core", "mezo-readonly"], default="core")
    options, remaining = selector.parse_known_args()
    if options.suite == "mezo-readonly":
        for package in ("contracts", "public-capture", "readonly-analyzer", "evidence-report"):
            sys.path.insert(0, str(ROOT / "packages" / package / "src"))
        from tools.mezo_acceptance.readonly_cases import main as readonly_main
        raise SystemExit(readonly_main(remaining))
    sys.argv = [sys.argv[0], *remaining]
    raise SystemExit(main())
