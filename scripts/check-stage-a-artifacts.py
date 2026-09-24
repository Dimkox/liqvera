#!/usr/bin/env python3
"""Fail closed if Stage A package trees contain Go inputs or engine binaries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.conformance.artifacts import scan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forbid-path", nargs="*", default=["cmd/**", "internal/**", "go.mod", "go.sum"])
    parser.add_argument("--forbid-binary", default="engine")
    parser.add_argument("--dist", type=Path, default=None)
    args = parser.parse_args(argv)
    roots = [ROOT / "packages"]
    if args.dist is not None:
        roots.append(args.dist)
    hits = scan(tuple(roots), tuple(args.forbid_path), args.forbid_binary)
    if hits:
        print("stage-a artifacts contain forbidden Go inputs:", file=sys.stderr)
        for hit in hits:
            print(hit, file=sys.stderr)
        return 1
    print("stage-a artifacts contain no Go inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
