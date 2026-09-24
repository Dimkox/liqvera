"""Credential-free Lighter public market-data capability."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol

from mee_contracts.market import BookLevel, InstrumentIdentity, OrderBookSnapshot, VenueMarket

ReadTransport = Callable[[str, Mapping[str, object]], Awaitable[object]]


@dataclass(frozen=True, slots=True)
class LighterInstrumentMapping:
    identity: InstrumentIdentity
    contract_multiplier: Decimal
    displayed_size_unit: str
    equivalence_evidence: str

    def __post_init__(self) -> None:
        if (
            self.contract_multiplier <= Decimal(0)
            or not self.displayed_size_unit.strip()
            or not self.equivalence_evidence.strip()
        ):
            raise ValueError("reviewed Lighter mapping is required")


class LighterMappingProvider(Protocol):
    def mapping_for(
        self,
        symbol: str,
        detail: Mapping[str, object],
    ) -> LighterInstrumentMapping | None:
        """Return only formally reviewed economic equivalence."""


@dataclass(frozen=True, slots=True)
class _KnownMarket:
    market_index: int
    market: VenueMarket


class LighterBookReducer:
    """Authoritative nonce reducer; any gap makes the book unavailable."""

    def __init__(
        self,
        symbol: str,
        market_index: int,
        received_timestamp_ms: Callable[[], int],
    ) -> None:
        self._symbol, self._market_index = symbol, market_index
        self._received_timestamp_ms = received_timestamp_ms
        self._bids: dict[Decimal, Decimal] = {}
        self._asks: dict[Decimal, Decimal] = {}
        self._nonce: int | None = None
        self._timestamp_ms: int | None = None
        self.unavailable = True

    def apply(self, message: Mapping[str, object]) -> OrderBookSnapshot | None:
        try:
            channel = _string(message.get("channel"), "channel")
            if channel != f"order_book:{self._market_index}":
                raise ValueError("order book channel does not match market")
            book = _object(message.get("order_book"), "order_book")
            message_type = _string(message.get("type"), "message type")
            if message_type == "subscribed/order_book":
                self._bids = _levels(book, "bids")
                self._asks = _levels(book, "asks")
                self._nonce = _integer(book.get("nonce"), "nonce")
                self.unavailable = False
                return self._snapshot(message)
            if self.unavailable or message_type != "update/order_book":
                return None
            begin_nonce = _integer(book.get("begin_nonce"), "begin nonce")
            next_nonce = _integer(book.get("nonce"), "nonce")
            if begin_nonce != self._nonce or next_nonce <= begin_nonce:
                self.unavailable = True
                return None
            _apply_levels(self._bids, book, "bids")
            _apply_levels(self._asks, book, "asks")
            self._nonce = next_nonce
            return self._snapshot(message)
        except Exception:
            self.unavailable = True
            raise

    def _snapshot(self, message: Mapping[str, object]) -> OrderBookSnapshot:
        self._timestamp_ms = _integer(message.get("timestamp"), "timestamp")
        return self.snapshot()

    def snapshot(self) -> OrderBookSnapshot:
        if self.unavailable or self._nonce is None or self._timestamp_ms is None:
            raise ValueError("Lighter order book is unavailable")
        return OrderBookSnapshot(
            venue=LighterPublicAdapter.venue,
            symbol=self._symbol,
            sequence=self._nonce,
            exchange_timestamp_ms=self._timestamp_ms,
            received_timestamp_ms=self._received_timestamp_ms(),
            bids=tuple(
                BookLevel(price, size)
                for price, size in sorted(self._bids.items(), reverse=True)
            ),
            asks=tuple(
                BookLevel(price, size)
                for price, size in sorted(self._asks.items())
            ),
        )


class LighterPublicAdapter:
    """Public Lighter discovery and websocket book reduction only."""

    venue = "LIGHTER"

    def __init__(
        self,
        *,
        read_transport: ReadTransport,
        mapping_provider: LighterMappingProvider,
        received_timestamp_ms: Callable[[], int],
    ) -> None:
        self._read_transport = read_transport
        self._mapping_provider = mapping_provider
        self._received_timestamp_ms = received_timestamp_ms
        self._known: dict[str, _KnownMarket] = {}
        self._books: dict[str, LighterBookReducer] = {}

    async def list_markets(self) -> Sequence[VenueMarket]:
        payload = _response(
            await self._read_transport("order_book_details", {"filter": "perp"})
        )
        known: dict[str, _KnownMarket] = {}
        for raw in _array(payload.get("order_book_details"), "order book details"):
            detail = _object(raw, "order book detail")
            if _string(detail.get("market_type"), "market type") != "perp":
                raise ValueError("perp filter returned a non-perp market")
            if _string(detail.get("status"), "market status") != "active":
                continue
            symbol = _string(detail.get("symbol"), "symbol")
            mapping = self._mapping_provider.mapping_for(symbol, detail)
            if mapping is None:
                continue
            size_decimals = _integer(
                detail.get("supported_size_decimals"), "size decimals"
            )
            price_decimals = _integer(
                detail.get("supported_price_decimals"), "price decimals"
            )
            if size_decimals < 0 or price_decimals < 0:
                raise ValueError("decimal places must be nonnegative")
            market = VenueMarket(
                self.venue,
                symbol,
                mapping.identity,
                mapping.contract_multiplier,
                mapping.displayed_size_unit,
                Decimal(1).scaleb(-size_decimals),
                Decimal(1).scaleb(-price_decimals),
                _decimal(detail.get("min_quote_amount"), "min quote"),
                mapping.equivalence_evidence,
                min_quantity=_decimal(
                    detail.get("min_base_amount"),
                    "min base",
                ),
            )
            known[symbol] = _KnownMarket(
                _integer(detail.get("market_id"), "market id"), market
            )
        self._known = known
        return tuple(item.market for item in known.values())

    async def order_book(self, market: VenueMarket) -> OrderBookSnapshot:
        self._require_market(market)
        reducer = self._books.get(market.symbol)
        if reducer is None or reducer.unavailable:
            raise ValueError("Lighter websocket book is unavailable")
        return reducer.snapshot()

    def apply_order_book_message(
        self,
        market: VenueMarket,
        message: Mapping[str, object],
    ) -> OrderBookSnapshot | None:
        """Apply an injected official websocket snapshot or update message."""

        known = self._require_market(market)
        reducer = self._books.setdefault(
            market.symbol,
            LighterBookReducer(
                market.symbol,
                known.market_index,
                self._received_timestamp_ms,
            ),
        )
        return reducer.apply(message)

    def _require_market(self, market: VenueMarket) -> _KnownMarket:
        known = self._known.get(market.symbol)
        if market.venue != self.venue or known is None or known.market != market:
            raise ValueError("market is not currently discovered")
        return known


def _levels(book: Mapping[str, object], side: str) -> dict[Decimal, Decimal]:
    levels: dict[Decimal, Decimal] = {}
    _apply_levels(levels, book, side)
    return levels


def _apply_levels(
    levels: dict[Decimal, Decimal],
    book: Mapping[str, object],
    side: str,
) -> None:
    for item in _array(book.get(side), side):
        level = _object(item, side)
        price = _decimal(level.get("price"), "price")
        size = _decimal(level.get("size"), "size")
        if size < 0 or price <= 0:
            raise ValueError("invalid L2 level")
        if size == 0:
            levels.pop(price, None)
        else:
            levels[price] = size


def _response(value: object) -> Mapping[str, object]:
    result = _object(value, "response")
    if _integer(result.get("code"), "response code") != 200:
        raise ValueError("Lighter response is not accepted")
    return result


def _object(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _array(value: object, name: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be an array")
    return tuple(value)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _decimal(value: object, name: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{name} must be a decimal string") from error
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result
