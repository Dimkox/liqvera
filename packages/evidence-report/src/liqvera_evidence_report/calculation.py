"""Exact report arithmetic and canonical display formatting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from fractions import Fraction

from liqvera_contracts.exact import decimal_from_fraction, fraction_from_decimal
from liqvera_readonly_analyzer.reconstruction import ReconstructedBook
from liqvera_readonly_analyzer.vwap import Side


def _price_impact_bps(book: ReconstructedBook, side: Side, vwap: Fraction) -> Fraction:
    if side is Side.BUY:
        best = fraction_from_decimal(book.snapshot.best_ask.price)
        return (vwap - best) * 10_000 / best
    best = fraction_from_decimal(book.snapshot.best_bid.price)
    return (best - vwap) * 10_000 / best


def _rational(value: Fraction) -> dict[str, str]:
    return {"numerator": str(value.numerator), "denominator": str(value.denominator)}


def _display(value: Fraction) -> str:
    rendered: Decimal = decimal_from_fraction(value)
    return format(rendered, "f")


def _timestamp(milliseconds: int) -> str:
    instant = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=milliseconds)
    if instant.microsecond == 0:
        return instant.strftime("%Y-%m-%dT%H:%M:%SZ")
    return instant.strftime("%Y-%m-%dT%H:%M:%S.") + f"{instant.microsecond // 1000:03d}Z"
