#!/usr/bin/env python3
"""Produce an A01–A30 result; no acceptance case runs without an explicit plan."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.mezo_acceptance.runner import main

if __name__ == "__main__":
    raise SystemExit(main())
