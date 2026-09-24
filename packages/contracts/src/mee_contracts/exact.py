"""Context-independent exact arithmetic for shadow financial calculations."""

from __future__ import annotations

import math
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DecimalException,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from fractions import Fraction

NON_TERMINATING_OUTPUT_PRECISION = 28
_OUTPUT_CONTEXT = Context(
    prec=NON_TERMINATING_OUTPUT_PRECISION,
    rounding=ROUND_HALF_EVEN,
    Emin=MIN_EMIN,
    Emax=MAX_EMAX,
    capitals=1,
    clamp=0,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)


class DecimalRenderingError(ValueError):
    """A finite Fraction cannot be represented by the display contract."""


class ExactError(ValueError):
    """An ExactDecimal value is malformed, non-finite, or otherwise rejected."""


class ExactPrecisionError(ExactError):
    """A value uses more than eight decimal places."""


class ExactOverflowError(ExactError):
    """A scaled value does not fit in a signed 64-bit integer."""


class ExactDivisionError(ExactError):
    """Division by zero is rejected."""


class ExactDecimal:
    """Eight-decimal scaled integer used as the Stage A exact money/size kernel.

    Construction accepts only an int scaled by 1e8, or a decimal string via
    ``parse``. Binary floats and non-finite Decimals fail closed.
    """

    DECIMALS = 8
    SCALE = 100_000_000
    _MIN_SCALED = -9223372036854775808
    _MAX_SCALED = 9223372036854775807

    __slots__ = ("_scaled",)

    def __init__(self, scaled: int) -> None:
        if type(scaled) is not int:
            raise TypeError("ExactDecimal scaled value must be int")
        if scaled < self._MIN_SCALED or scaled > self._MAX_SCALED:
            raise ExactOverflowError("scaled value overflows int64")
        self._scaled = scaled

    @classmethod
    def parse(cls, raw: str) -> ExactDecimal:
        if type(raw) is not str:
            raise TypeError("ExactDecimal.parse accepts only str")
        if raw == "" or raw.strip() != raw:
            raise ExactError(f"invalid exact value: {raw!r}")
        sign = 1
        text = raw
        if text[0] == "-":
            sign = -1
            text = text[1:]
        elif text[0] == "+":
            text = text[1:]
        if text == "" or any(marker in text for marker in "eEnN"):
            raise ExactError(f"exponent or non-finite exact value: {raw!r}")
        parts = text.split(".")
        if len(parts) > 2 or parts[0] == "":
            raise ExactError(f"malformed exact value: {raw!r}")
        if len(parts) == 2 and (parts[1] == "" or not parts[1].isdigit()):
            raise ExactError(f"malformed exact value: {raw!r}")
        if not parts[0].isdigit() or (len(parts) == 2 and not parts[1].isdigit()):
            raise ExactError(f"non-digit exact value: {raw!r}")
        if len(parts) == 2 and len(parts[1]) > cls.DECIMALS:
            raise ExactPrecisionError(raw)
        whole = int(parts[0]) * cls.SCALE
        if len(parts) == 2:
            whole += int(parts[1] + ("0" * (cls.DECIMALS - len(parts[1]))))
        return cls(sign * whole)

    @classmethod
    def from_decimal(cls, value: Decimal) -> ExactDecimal:
        if type(value) is not Decimal:
            raise TypeError("ExactDecimal.from_decimal accepts only Decimal")
        if not value.is_finite():
            raise ExactError("non-finite Decimal is rejected")
        return cls.parse(format(value, "f"))

    @property
    def scaled(self) -> int:
        return self._scaled

    def __str__(self) -> str:
        sign = "-" if self._scaled < 0 else ""
        magnitude = abs(self._scaled)
        whole, fraction = divmod(magnitude, self.SCALE)
        if fraction == 0:
            return f"{sign}{whole}"
        frac = f"{fraction:08d}".rstrip("0")
        return f"{sign}{whole}.{frac}"

    def __repr__(self) -> str:
        return f"ExactDecimal.parse({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not ExactDecimal:
            return NotImplemented
        return self._scaled == other._scaled

    def __hash__(self) -> int:
        return hash(self._scaled)

    def __lt__(self, other: ExactDecimal) -> bool:
        if type(other) is not ExactDecimal:
            return NotImplemented
        return self._scaled < other._scaled

    def __le__(self, other: ExactDecimal) -> bool:
        if type(other) is not ExactDecimal:
            return NotImplemented
        return self._scaled <= other._scaled

    def add(self, other: ExactDecimal) -> ExactDecimal:
        if type(other) is not ExactDecimal:
            raise TypeError("add requires ExactDecimal")
        return ExactDecimal(self._scaled + other._scaled)

    def sub(self, other: ExactDecimal) -> ExactDecimal:
        if type(other) is not ExactDecimal:
            raise TypeError("sub requires ExactDecimal")
        return ExactDecimal(self._scaled - other._scaled)

    def mul(self, other: ExactDecimal) -> ExactDecimal:
        if type(other) is not ExactDecimal:
            raise TypeError("mul requires ExactDecimal")
        product = (self._scaled * other._scaled) // self.SCALE
        return ExactDecimal(product)

    def div(self, other: ExactDecimal) -> ExactDecimal:
        if type(other) is not ExactDecimal:
            raise TypeError("div requires ExactDecimal")
        if other._scaled == 0:
            raise ExactDivisionError("division by zero")
        quotient = (self._scaled * self.SCALE) // other._scaled
        return ExactDecimal(quotient)

    def is_zero(self) -> bool:
        return self._scaled == 0


def fraction_from_decimal(value: Decimal) -> Fraction:
    """Convert one finite Decimal exactly without using Decimal arithmetic."""
    sign, digits, exponent = value.as_tuple()
    coefficient = 0
    for digit in digits:
        coefficient = coefficient * 10 + digit
    if sign:
        coefficient = -coefficient
    if exponent >= 0:
        return Fraction(coefficient * 10**exponent)
    return Fraction(coefficient, 10 ** (-exponent))


def decimal_from_fraction(value: Fraction) -> Decimal:
    """Return an exact Decimal or the fixed non-terminating output contract."""
    denominator = value.denominator
    twos = 0
    fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator == 1:
        scale = max(twos, fives)
        coefficient = value.numerator * 2 ** (scale - twos)
        coefficient *= 5 ** (scale - fives)
        sign = int(coefficient < 0)
        digits = tuple(int(digit) for digit in str(abs(coefficient)))
        return Decimal((sign, digits, -scale))
    return _rounded_decimal(value)


def is_terminating_fraction(value: Fraction) -> bool:
    """Return whether the reduced fraction has a finite decimal expansion."""
    denominator = value.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    return denominator == 1


def fraction_lcm(left: Fraction, right: Fraction) -> Fraction:
    """Return the smallest positive rational multiple of both inputs."""
    denominator = math.lcm(left.denominator, right.denominator)
    left_integer = left.numerator * (denominator // left.denominator)
    right_integer = right.numerator * (denominator // right.denominator)
    return Fraction(math.lcm(left_integer, right_integer), denominator)


def round_up_to_multiple(value: Fraction, lot: Fraction) -> Fraction:
    """Round a positive rational value upward to a positive rational lot."""
    units = value / lot
    return ((units.numerator + units.denominator - 1) // units.denominator) * lot


def is_multiple(value: Fraction, step: Fraction) -> bool:
    """Return whether the exact fraction is an integral count of step."""
    return (value / step).denominator == 1


def _rounded_decimal(value: Fraction) -> Decimal:
    try:
        with localcontext(_OUTPUT_CONTEXT):
            rendered = Decimal(value.numerator) / Decimal(value.denominator)
    except DecimalException as error:
        raise DecimalRenderingError(
            "non-terminating Decimal output is unrenderable"
        ) from error
    if not rendered.is_finite() or (value != 0 and rendered.is_zero()):
        raise DecimalRenderingError("non-terminating Decimal output is unrenderable")
    return rendered
