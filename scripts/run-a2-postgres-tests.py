"""Binding PostgreSQL gate for all A2 integration tests."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest


def main(arguments: list[str] | None = None) -> int:
    if not os.environ.get("A2_TEST_DATABASE_URL"):
        print("A2_TEST_DATABASE_URL is required", file=sys.stderr)
        return 2

    names = list(sys.argv[1:] if arguments is None else arguments)
    loader = unittest.defaultTestLoader
    if names:
        suite = loader.loadTestsFromNames(names)
    else:
        root = Path(__file__).resolve().parents[1]
        suite = loader.discover(
            str(root / "tests" / "a2" / "integration"),
            pattern="test*.py",
            top_level_dir=str(root),
        )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.skipped:
        print(
            f"A2 PostgreSQL gate rejects {len(result.skipped)} skipped test(s)",
            file=sys.stderr,
        )
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
