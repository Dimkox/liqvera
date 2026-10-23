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


def trove_risk(*, collateral: int, principal: int, interest: int, price: int,
               mcr: int, ccr: int, tcr: int, status: int) -> dict:
    """Snapshot risk from the verified six-value Mezo ABI's first three totals.

    Ratios are displayed as ratios; buffer_pct is percentage points (100 times
    price/threshold-1). The threshold assumes a constant debt/collateral snapshot
    and is not a prediction of protocol liquidation eligibility.
    """
    values = (collateral, principal, interest, price, mcr, ccr, tcr, status)
    maximum = 2**256 - 1
    if (any(type(v) is not int or not 0 <= v <= maximum for v in values)
            or price == 0 or mcr == 0 or ccr < mcr or status not in range(5)
            or principal + interest > maximum):
        raise ValueError("MEZO_TROVE_INVALID_INPUT")
    debt = principal + interest
    if (status == 1 and debt == 0) or (debt > 0 and collateral * price > maximum):
        raise ValueError("MEZO_TROVE_INVALID_INPUT")
    unit = 10**18
    icr = collateral * price // debt if debt else maximum
    active = status == 1
    flags = ([] if active else ["NOT_ACTIVE"])
    if active and icr < mcr:
        flags.append("LIQUIDATABLE")
    if tcr < ccr:
        flags.append("RECOVERY_MODE")
    threshold = Fraction(mcr * debt, collateral * unit) if active and collateral else None
    buffer = (Fraction(price, unit) / threshold - 1) * 100 if threshold else None
    scenarios = []
    for reduction in (10, 20, 30):
        scenario_price = price * (100 - reduction) // 100
        scenario_icr = collateral * scenario_price // debt if debt else maximum
        scenarios.append({"price_change_pct": str(-reduction),
                          "price_musd": _display(Fraction(scenario_price, unit)),
                          "icr": _display(Fraction(scenario_icr, unit)) if active else None,
                          "status": ("NOT_ACTIVE" if not active else
                                     "LIQUIDATABLE" if scenario_icr < mcr else "ABOVE_MCR")})
    return {"status": "ACTIVE" if active else "NOT_ACTIVE", "contract_status": status,
            "debt_musd": _display(Fraction(debt, unit)),
            "collateral_btc": _display(Fraction(collateral, unit)),
            "price_musd": _display(Fraction(price, unit)),
            "icr_atomic": str(icr), "icr": _display(Fraction(icr, unit)) if active else None,
            "mcr": _display(Fraction(mcr, unit)), "ccr": _display(Fraction(ccr, unit)),
            "tcr": _display(Fraction(tcr, unit)),
            "liquidation_price_musd": _display(threshold) if threshold is not None else None,
            "buffer_pct": _display(buffer) if buffer is not None else None,
            "flags": flags, "scenarios": scenarios}
