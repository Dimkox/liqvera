#!/usr/bin/env python
"""Repository entry point for architecture graph validation."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.graph_checker.__main__ import main


if __name__ == "__main__":
    raise SystemExit(main())
