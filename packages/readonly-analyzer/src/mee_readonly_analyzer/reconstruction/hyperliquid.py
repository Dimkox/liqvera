"""Decode Hyperliquid REST l2Book bytes into an admitted snapshot."""

from __future__ import annotations

import json
from decimal import Decimal

from mee_contracts.exact import ExactDecimal, ExactError
from mee_contracts.market import BookLevel, OrderBookSnapshot

from mee_readonly_analyzer.reconstruction.common import ReconstructionError

_VENUE = "HYPERLIQUID"


def decode_hyperliquid_l2book(payload: bytes, *, observed_at_ms: int) -> OrderBookSnapshot:
    """Map REST l2Book bytes. Extra keys allowed; levels are not sorted."""
    try:
        return _decode(payload, observed_at_ms=observed_at_ms)
    except ReconstructionError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
        ExactError,
    ) as error:
        raise ReconstructionError(
            "claimed Hyperliquid envelope is not an admitted l2Book snapshot"
        ) from error


def _decode(payload: bytes, *, observed_at_ms: int) -> OrderBookSnapshot:
    if type(payload) is not bytes:
        raise ReconstructionError("l2Book payload must be bytes")
    document = json.loads(payload.decode("utf-8"))
    if type(document) is not dict:
        raise ReconstructionError("l2Book payload must be an object")
    coin = document.get("coin")
    if type(coin) is not str or not coin.strip():
        raise ReconstructionError("l2Book coin must be a nonempty string")
    time = document.get("time")
    if type(time) is not int:
        raise ReconstructionError("l2Book time must be an integer")
    levels = document.get("levels")
    if type(levels) is not list or len(levels) != 2:
        raise ReconstructionError("l2Book levels must contain bid and ask arrays")
    return OrderBookSnapshot(
        venue=_VENUE,
        symbol=coin,
        sequence=None,
        exchange_timestamp_ms=time,
        received_timestamp_ms=observed_at_ms,
        bids=_book_levels(levels[0], "bids"),
        asks=_book_levels(levels[1], "asks"),
    )


def _book_levels(raw: object, side: str) -> tuple[BookLevel, ...]:
    if type(raw) is not list:
        raise ReconstructionError(f"{side} must be an array")
    levels: list[BookLevel] = []
    for item in raw:
        if type(item) is not dict:
            raise ReconstructionError(f"{side} level must be an object")
        px = item.get("px")
        sz = item.get("sz")
        if type(px) is not str or type(sz) is not str:
            raise ReconstructionError(f"{side} px/sz must be decimal strings")
        price = ExactDecimal.parse(px)
        quantity = ExactDecimal.parse(sz)
        levels.append(BookLevel(Decimal(str(price)), Decimal(str(quantity))))
    return tuple(levels)
