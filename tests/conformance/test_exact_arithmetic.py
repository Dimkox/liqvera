"""Hypothesis: exact values are string-only, eight-place, and overflow-closed."""

from __future__ import annotations

from decimal import Decimal

import pytest
from mee_contracts.exact import (
    ExactDecimal,
    ExactError,
    ExactOverflowError,
    ExactPrecisionError,
)


def test_round_trip_matches_display_contract() -> None:
    for raw in ("0", "1", "-1", "0.00000001", "456.78"):
        assert str(ExactDecimal.parse(raw)) == raw


def test_reject_nonfinite() -> None:
    for raw in ("NaN", "Inf", "-Infinity", "1e8"):
        with pytest.raises(ExactError):
            ExactDecimal.parse(raw)
    with pytest.raises(ExactError):
        ExactDecimal.from_decimal(Decimal("NaN"))


def test_reject_binary_float() -> None:
    with pytest.raises(TypeError):
        ExactDecimal.parse(0.1)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ExactDecimal.from_decimal(0.1)  # type: ignore[arg-type]


def test_precision_and_scaled_overflow_fail_closed() -> None:
    with pytest.raises(ExactPrecisionError):
        ExactDecimal.parse("0.000000001")
    with pytest.raises(ExactOverflowError):
        ExactDecimal.parse("92233720368.54775807").add(ExactDecimal.parse("0.00000001"))
