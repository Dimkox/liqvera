"""Decode claimed Lighter subscribed/order_book and typed update/order_book bytes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal

from mee_contracts.exact import ExactDecimal, ExactError
from mee_contracts.market import BookLevel, OrderBookSnapshot
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence

from mee_readonly_analyzer.reconstruction.common import ReconstructionError

_VENUE = "LIGHTER"
_CHANNEL_PREFIX = "order_book:"
_SNAPSHOT_TYPE = "subscribed/order_book"
_UPDATE_TYPE = "update/order_book"


@dataclass(frozen=True, slots=True)
class LighterSnapshot:
    channel: str
    symbol: str | None
    timestamp: int
    nonce: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]


@dataclass(frozen=True, slots=True)
class LighterUpdate:
    channel: str
    symbol: str | None
    timestamp: int
    nonce: int
    begin_nonce: int
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]


def decode_lighter_envelope(
    payload: bytes,
    *,
    observed_at_ms: int,
) -> LighterSnapshot | LighterUpdate:
    """Claimed Lighter book bytes. Extra keys allowed. Snapshots are not sorted."""
    try:
        return _decode_envelope(payload)
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
            "claimed Lighter envelope is not an admitted snapshot or typed update"
        ) from error


def decode_lighter_subscribed_order_book(
    payload: bytes,
    *,
    observed_at_ms: int,
) -> OrderBookSnapshot:
    """Map claimed subscribed/order_book bytes. Extra keys allowed; levels are not sorted."""
    decoded = decode_lighter_envelope(payload, observed_at_ms=observed_at_ms)
    if type(decoded) is not LighterSnapshot:
        raise ReconstructionError("type must be subscribed/order_book")
    if decoded.symbol is None:
        raise ReconstructionError("symbol must be a nonempty string")
    try:
        return OrderBookSnapshot(
            venue=_VENUE,
            symbol=decoded.symbol,
            sequence=decoded.nonce,
            exchange_timestamp_ms=decoded.timestamp,
            received_timestamp_ms=observed_at_ms,
            bids=decoded.bids,
            asks=decoded.asks,
        )
    except (TypeError, ValueError) as error:
        raise ReconstructionError("claimed Lighter envelope is not an admitted snapshot") from error


def apply_lighter_update(
    previous: OrderBookSnapshot,
    update: LighterUpdate,
    *,
    observed_at_ms: int,
) -> OrderBookSnapshot:
    """Replace/delete/append without sorting. Caller treats ValueError as epoch-close."""
    symbol = update.symbol if update.symbol is not None else previous.symbol
    return OrderBookSnapshot(
        venue=_VENUE,
        symbol=symbol,
        sequence=update.nonce,
        exchange_timestamp_ms=update.timestamp,
        received_timestamp_ms=observed_at_ms,
        bids=_apply_side(previous.bids, update.bids),
        asks=_apply_side(previous.asks, update.asks),
    )


def lighter_ticker_for_channel(
    channel: str,
    mappings: tuple[MarketMappingEvidence, ...],
    observed_at_ms: int,
) -> str:
    """Resolve omitted payload ticker from a unique current indexed Lighter mapping."""
    index = int(channel[len(_CHANNEL_PREFIX) :])
    candidates = [
        mapping
        for mapping in mappings
        if type(mapping) is MarketMappingEvidence
        and mapping.decision is MappingDecision.APPROVED
        and mapping.venue.casefold() == "lighter"
        and mapping.lighter_market_index == index
        and observed_at_ms >= mapping.valid_from_ms
        and (mapping.valid_until_ms is None or observed_at_ms <= mapping.valid_until_ms)
    ]
    if len(candidates) != 1:
        raise ReconstructionError("claimed Lighter snapshot has no unique current indexed mapping")
    return candidates[0].symbol


def _decode_envelope(payload: bytes) -> LighterSnapshot | LighterUpdate:
    if type(payload) is not bytes:
        raise ReconstructionError("claimed Lighter payload must be bytes")
    document = json.loads(payload.decode("utf-8"))
    if type(document) is not dict:
        raise ReconstructionError("claimed Lighter payload must be an object")
    message_type = document.get("type")
    if message_type == _SNAPSHOT_TYPE:
        return _decode_snapshot(document)
    if message_type == _UPDATE_TYPE:
        return _decode_update(document)
    raise ReconstructionError("type must be subscribed/order_book or update/order_book")


def _decode_snapshot(document: dict) -> LighterSnapshot:
    channel = _channel(document)
    timestamp = _require_int(document.get("timestamp"), "timestamp")
    symbol = _optional_symbol(document)
    order_book = document.get("order_book")
    if type(order_book) is not dict:
        raise ReconstructionError("order_book must be an object")
    nonce = _require_int(order_book.get("nonce"), "nonce")
    return LighterSnapshot(
        channel=channel,
        symbol=symbol,
        timestamp=timestamp,
        nonce=nonce,
        bids=_book_levels(order_book.get("bids"), "bids"),
        asks=_book_levels(order_book.get("asks"), "asks"),
    )


def _decode_update(document: dict) -> LighterUpdate:
    channel = _channel(document)
    timestamp = _require_int(document.get("timestamp"), "timestamp")
    symbol = _optional_symbol(document)
    order_book = document.get("order_book")
    if type(order_book) is not dict:
        raise ReconstructionError("order_book must be an object")
    begin_nonce = _require_int(order_book.get("begin_nonce"), "begin_nonce")
    nonce = _require_int(order_book.get("nonce"), "nonce")
    return LighterUpdate(
        channel=channel,
        symbol=symbol,
        timestamp=timestamp,
        nonce=nonce,
        begin_nonce=begin_nonce,
        bids=_delta_levels(order_book.get("bids"), "bids"),
        asks=_delta_levels(order_book.get("asks"), "asks"),
    )


def _channel(document: dict) -> str:
    channel = document.get("channel")
    if type(channel) is not str or not channel:
        raise ReconstructionError("channel must be a nonempty string")
    if not channel.startswith(_CHANNEL_PREFIX):
        raise ReconstructionError("channel must start with order_book:")
    suffix = channel[len(_CHANNEL_PREFIX) :]
    if not suffix.isdigit() or type(int(suffix)) is not int:
        raise ReconstructionError("channel market index must be digits")
    return channel


def _optional_symbol(document: dict) -> str | None:
    if "symbol" not in document:
        return None
    symbol = document["symbol"]
    if type(symbol) is not str or not symbol:
        raise ReconstructionError("symbol must be a nonempty string")
    return symbol


def _require_int(value: object, name: str) -> int:
    if type(value) is not int:
        raise ReconstructionError(f"{name} must be an integer")
    return value


def _book_levels(raw: object, side: str) -> tuple[BookLevel, ...]:
    if type(raw) is not list:
        raise ReconstructionError(f"{side} must be an array")
    levels: list[BookLevel] = []
    for item in raw:
        if type(item) is not dict:
            raise ReconstructionError(f"{side} level must be an object")
        price_raw = item.get("price")
        size_raw = item.get("size")
        if type(price_raw) is not str or type(size_raw) is not str:
            raise ReconstructionError(f"{side} price/size must be decimal strings")
        price = ExactDecimal.parse(price_raw)
        quantity = ExactDecimal.parse(size_raw)
        levels.append(BookLevel(Decimal(str(price)), Decimal(str(quantity))))
    return tuple(levels)


def _delta_levels(raw: object, side: str) -> tuple[tuple[Decimal, Decimal], ...]:
    if type(raw) is not list:
        raise ReconstructionError(f"{side} must be an array")
    levels: list[tuple[Decimal, Decimal]] = []
    for item in raw:
        if type(item) is not dict:
            raise ReconstructionError(f"{side} level must be an object")
        price_raw = item.get("price")
        size_raw = item.get("size")
        if type(price_raw) is not str or type(size_raw) is not str:
            raise ReconstructionError(f"{side} price/size must be decimal strings")
        price = ExactDecimal.parse(price_raw)
        quantity = ExactDecimal.parse(size_raw)
        price_decimal = Decimal(str(price))
        quantity_decimal = Decimal(str(quantity))
        if price_decimal <= 0 or quantity_decimal < 0:
            raise ReconstructionError(f"{side} price must be positive and size nonnegative")
        levels.append((price_decimal, quantity_decimal))
    return tuple(levels)


def _apply_side(
    previous: tuple[BookLevel, ...],
    deltas: tuple[tuple[Decimal, Decimal], ...],
) -> tuple[BookLevel, ...]:
    levels = list(previous)
    for price, size in deltas:
        if size == 0:
            levels = [level for level in levels if level.price != price]
            continue
        replaced = False
        for index, level in enumerate(levels):
            if level.price == price:
                levels[index] = BookLevel(price, size)
                replaced = True
                break
        if not replaced:
            levels.append(BookLevel(price, size))
    return tuple(levels)
