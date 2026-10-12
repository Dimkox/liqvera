#!/usr/bin/env python3
"""Reload and verify a sealed Liqvera acceptance result and all bindings."""

import argparse
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Verification needs the same declared dependencies as the producer, even when
# an operator invokes the script with a bare system interpreter.
if importlib.util.find_spec("jsonschema") is None:
    environment = ROOT / ".venv"
    python = environment / "bin" / "python"
    if python.is_file() and (sys.prefix != str(environment) or sys.flags.no_site):
        os.execv(str(python), [str(python), "-B", str(Path(__file__).resolve()), *sys.argv[1:]])
    raise SystemExit("Install Liqvera dependencies in .venv before verifying acceptance evidence")

from tools.mezo_acceptance.runner import verify_sealed_result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--allow-detached-subject", action="store_true",
                        help="verify content bindings without requiring the current checkout identity")
    args = parser.parse_args()
    result = verify_sealed_result(
        args.result.resolve(), args.sha256,
        require_current_repository=not args.allow_detached_subject,
    )
    print(f"VERIFIED: {result['overall_status']} {args.result.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
