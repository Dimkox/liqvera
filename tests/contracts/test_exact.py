"""ExactDecimal kernel: string-only construction and eight-place arithmetic."""

from __future__ import annotations

from decimal import Decimal

import pytest
from mee_contracts.exact import (
    ExactDecimal,
    ExactDivisionError,
    ExactError,
    ExactOverflowError,
    ExactPrecisionError,
)


def test_parse_round_trip() -> None:
    cases = ("0", "1", "-1", "0.00000001", "456.78", "-92233720368.54775808")
    for raw in cases:
        assert str(ExactDecimal.parse(raw)) == raw


def test_reject_nonfinite() -> None:
    for raw in ("NaN", "nan", "Inf", "Infinity", "-Inf", "1e2", "1E-2"):
        with pytest.raises(ExactError):
            ExactDecimal.parse(raw)
    for value in (Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity")):
        with pytest.raises(ExactError):
            ExactDecimal.from_decimal(value)


def test_reject_binary_float() -> None:
    with pytest.raises(TypeError):
        ExactDecimal.parse(1.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ExactDecimal(1.25)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ExactDecimal.from_decimal(1.25)  # type: ignore[arg-type]


def test_reject_precision_and_overflow() -> None:
    with pytest.raises(ExactPrecisionError):
        ExactDecimal.parse("0.000000001")
    with pytest.raises(ExactOverflowError):
        ExactDecimal.parse("92233720368.54775808")
    maximum = ExactDecimal.parse("92233720368.54775807")
    assert maximum.scaled == 9223372036854775807
    with pytest.raises(ExactOverflowError):
        maximum.add(ExactDecimal.parse("0.00000001"))


def test_mul_div() -> None:
    value = ExactDecimal.parse("12.5").mul(ExactDecimal.parse("2"))
    assert str(value) == "25"
    assert str(value.div(ExactDecimal.parse("4"))) == "6.25"
    with pytest.raises(ExactDivisionError):
        value.div(ExactDecimal.parse("0"))
