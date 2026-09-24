"""In-memory full-depth VWAP over one reconstructed Hyperliquid book."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

from mee_contracts.exact import ExactDecimal, ExactError
from mee_contracts.reasons import ShadowRejectCode

from mee_readonly_analyzer.reconstruction import ReconstructedBook

_COIN_UNIT = "coin"
_UNIT_MULTIPLIER = Decimal("1")


class Side(StrEnum):
    BUY = "BUY"  # walk snapshot.asks, stored ascending
    SELL = "SELL"  # walk snapshot.bids, stored descending


@dataclass(frozen=True, slots=True)
class ExecutableFill:
    side: Side
    envelope_index: int
    payload_sha256: str
    epoch_id: int
    requested_quantity: Fraction
    filled_quantity: Fraction
    notional_quote: Fraction
    vwap: Fraction
    worst_price: Fraction
    consumed_levels: int


class DepthRejected(ValueError):
    """Requested quantity exceeds displayed depth."""

    def __init__(self) -> None:
        self.code = ShadowRejectCode.DEPTH_INSUFFICIENT
        super().__init__(self.code.value)


class VwapError(ValueError):
    """Caller/invariant failure (type, non-positive quantity, ExactDecimal conversion)."""


def _require_coin_unit_identity(book: ReconstructedBook) -> None:
    mapping = book.mapping
    if mapping is None:
        raise VwapError("book must be bound to sealed identity")
    if mapping.displayed_size_unit != _COIN_UNIT:
        raise VwapError("displayed size unit is not coin")
    if mapping.reviewed_contract_multiplier != _UNIT_MULTIPLIER:
        raise VwapError("contract multiplier is not 1")


def sweep_depth(
    book: ReconstructedBook,
    side: Side,
    quantity: ExactDecimal,
) -> ExecutableFill:
    """Consume exact displayed quantity from stored snapshot levels, or reject."""
    if type(book) is not ReconstructedBook:
        raise VwapError("book must be ReconstructedBook")
    if type(side) is not Side:
        raise VwapError("side must be Side")
    if type(quantity) is not ExactDecimal or quantity.scaled <= 0:
        raise VwapError("quantity must be a strictly positive ExactDecimal")
    _require_coin_unit_identity(book)
    levels = book.snapshot.asks if side is Side.BUY else book.snapshot.bids
    remaining = Fraction(quantity.scaled, ExactDecimal.SCALE)
    notional = Fraction(0)
    consumed = 0
    worst: Fraction | None = None
    for level in levels:
        try:
            px = ExactDecimal.from_decimal(level.price)
            sz = ExactDecimal.from_decimal(level.quantity)
        except (ExactError, TypeError) as error:
            raise VwapError("level price or quantity is not ExactDecimal-admissible") from error
        available = Fraction(sz.scaled, ExactDecimal.SCALE)
        price = Fraction(px.scaled, ExactDecimal.SCALE)
        taken = remaining if remaining <= available else available
        if taken == 0:
            continue
        notional += price * taken
        remaining -= taken
        consumed += 1
        worst = price
        if remaining == 0:
            break
    if remaining != 0:
        raise DepthRejected()
    if worst is None:
        raise VwapError("sweep produced no consumed levels")
    filled = Fraction(quantity.scaled, ExactDecimal.SCALE)
    return ExecutableFill(
        side=side,
        envelope_index=book.envelope_index,
        payload_sha256=book.payload_sha256,
        epoch_id=book.epoch_id,
        requested_quantity=filled,
        filled_quantity=filled,
        notional_quote=notional,
        vwap=notional / filled,
        worst_price=worst,
        consumed_levels=consumed,
    )
