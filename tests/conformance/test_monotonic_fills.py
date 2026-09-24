"""Hypothesis: cumulative fills are monotonic, non-negative, and bounded."""

from __future__ import annotations

import pytest
from mee_contracts.exact import ExactDecimal

from tests.conformance.invariants import apply_cumulative


def test_duplicate_cumulative_is_idempotent() -> None:
    current = ExactDecimal.parse("25")
    base = ExactDecimal.parse("100")
    assert apply_cumulative(current, ExactDecimal.parse("25"), base) == current


def test_regression_and_overfill_fail_closed() -> None:
    current = ExactDecimal.parse("25")
    base = ExactDecimal.parse("100")
    with pytest.raises(ValueError, match="fill regression"):
        apply_cumulative(current, ExactDecimal.parse("24"), base)
    with pytest.raises(ValueError, match="overfill"):
        apply_cumulative(current, ExactDecimal.parse("101"), base)
    with pytest.raises(ValueError, match="negative fill"):
        apply_cumulative(ExactDecimal.parse("0"), ExactDecimal.parse("-1"), base)
