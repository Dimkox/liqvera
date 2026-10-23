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


def _amm_inputs(amount: int, reserve_in: int, reserve_out: int, fee_bps: int) -> None:
    if (any(type(v) is not int for v in (amount, reserve_in, reserve_out, fee_bps))
            or not 0 <= amount < 2**256 or not 0 < reserve_in < 2**256
            or not 0 < reserve_out < 2**256 or not 0 <= fee_bps < 10_000):
        raise ValueError("MEZO_DEX_INVALID_INPUT")


def amm_amount_out(amount: int, reserve_in: int, reserve_out: int, fee_bps: int) -> int:
    """Volatile Pool.getAmountOut: subtract the truncated fee before division."""
    _amm_inputs(amount, reserve_in, reserve_out, fee_bps)
    if amount * fee_bps >= 2**256:
        raise ValueError("MEZO_DEX_ARITHMETIC_OVERFLOW")
    net = amount - amount * fee_bps // 10_000
    if net * reserve_out >= 2**256 or reserve_in + net >= 2**256:
        raise ValueError("MEZO_DEX_ARITHMETIC_OVERFLOW")
    return net * reserve_out // (reserve_in + net)


def amm_amount_in(quantity: int, reserve_in: int, reserve_out: int, fee_bps: int) -> int:
    """Smallest input whose integer exact-input quote reaches the desired output.

    The pool charges floor(input * fee / 10000), so net input is
    ceil(input * (10000-fee) / 10000). Invert both integer ceilings exactly.
    A router only quotes exact input; achieved output may exceed the request.
    """
    _amm_inputs(quantity, reserve_in, reserve_out, fee_bps)
    if quantity >= reserve_out:
        raise ValueError("INSUFFICIENT_LIQUIDITY")
    if quantity == 0:
        return 0
    denominator = reserve_out - quantity
    required_net = (quantity * reserve_in + denominator - 1) // denominator
    amount = (required_net - 1) * 10_000 // (10_000 - fee_bps) + 1
    # The off-chain inverse itself uses unbounded exact arithmetic, but its
    # returned quote must be executable by the checked Solidity calculation.
    amm_amount_out(amount, reserve_in, reserve_out, fee_bps)
    return amount
