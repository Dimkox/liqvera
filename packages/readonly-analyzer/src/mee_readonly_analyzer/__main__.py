"""Console entry for the network-free frozen-package reader."""

from __future__ import annotations

import sys

from mee_contracts.decision import StageADecisionCode

from mee_readonly_analyzer.config import AnalyzerConfigError, load_analyzer_configuration
from mee_readonly_analyzer.verdict import evaluate_frozen_package


def main() -> int:
    try:
        config = load_analyzer_configuration()
    except AnalyzerConfigError:
        print("readonly analyzer configuration rejected", file=sys.stderr)
        return 2
    try:
        decision = evaluate_frozen_package(config.package_root)
    except Exception:
        print("readonly analyzer rejected the frozen package", file=sys.stderr)
        return 1
    sys.stdout.write(decision.to_canonical_json().decode("ascii"))
    if decision.decision is StageADecisionCode.INVALID_DATASET:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
