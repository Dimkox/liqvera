"""Console entry for credential-free public capture."""

from __future__ import annotations

import sys

from mee_public_capture.config import PublicConfigError, load_public_configuration
from mee_public_capture.runtime import run_public_capture


def main() -> int:
    try:
        return run_public_capture(load_public_configuration())
    except PublicConfigError:
        print("public capture configuration rejected", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
