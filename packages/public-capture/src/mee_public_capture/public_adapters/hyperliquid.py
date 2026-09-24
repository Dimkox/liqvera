"""Credential-free Hyperliquid public market-data capability."""

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal, Protocol, TypedDict

from mee_contracts.market import BookLevel, InstrumentIdentity, OrderBookSnapshot, VenueMarket


class HyperliquidInfoRequest(TypedDict, total=False):
    """Official public POST /info payload for metadata and L2 discovery."""

    type: Literal["metaAndAssetCtxs", "l2Book"]
    coin: str


InfoTransport = Callable[[HyperliquidInfoRequest], Awaitable[object]]


@dataclass(frozen=True, slots=True)
class HyperliquidInstrumentMapping:
    """Externally evidenced economic mapping; never inferred from a ticker."""

    identity: InstrumentIdentity
    contract_multiplier: Decimal
    displayed_size_unit: str
    min_notional: Decimal
    equivalence_evidence: str

    def __post_init__(self) -> None:
        if self.contract_multiplier <= Decimal("0"):
            raise ValueError("contract multiplier must be positive")
        if self.min_notional <= Decimal("0"):
            raise ValueError("minimum notional must be positive")
        if not self.displayed_size_unit.strip():
            raise ValueError("displayed size unit is required")
        if not self.equivalence_evidence.strip():
            raise ValueError("equivalence evidence is required")


class HyperliquidMappingProvider(Protocol):
    """Data-driven source of formally reviewed contract equivalence evidence."""

    def mapping_for(
        self,
        symbol: str,
        metadata: Mapping[str, object],
    ) -> HyperliquidInstrumentMapping | None:
        """Return the external mapping for a current meta symbol, if verified."""


@dataclass(frozen=True, slots=True)
class _KnownMarket:
    asset_index: int
    market: VenueMarket


class HyperliquidPublicAdapter:
    """Public discovery and L2 mapping without account or order capability."""

    venue = "HYPERLIQUID"

    def __init__(
        self,
        *,
        info_transport: InfoTransport,
        mapping_provider: HyperliquidMappingProvider,
        received_timestamp_ms: Callable[[], int],
    ) -> None:
        self._info_transport = info_transport
        self._mapping_provider = mapping_provider
        self._received_timestamp_ms = received_timestamp_ms
        self._known_markets: dict[str, _KnownMarket] = {}

    async def list_markets(self) -> Sequence[VenueMarket]:
        """Discover current perps from official ``metaAndAssetCtxs`` response."""

        response = await self._info_transport({"type": "metaAndAssetCtxs"})
        universe, contexts = _meta_and_contexts(response)
        known: dict[str, _KnownMarket] = {}
        for asset_index, metadata in enumerate(universe):
            symbol = _string(metadata.get("name"), "meta name")
            sz_decimals = _integer(metadata.get("szDecimals"), "szDecimals")
            if not 0 <= sz_decimals <= 6:
                raise ValueError("Hyperliquid szDecimals is outside perp bounds")
            mapping = self._mapping_provider.mapping_for(symbol, metadata)
            if mapping is None:
                continue
            market = VenueMarket(
                venue=self.venue,
                symbol=symbol,
                identity=mapping.identity,
                contract_multiplier=mapping.contract_multiplier,
                displayed_size_unit=mapping.displayed_size_unit,
                quantity_step=Decimal(1).scaleb(-sz_decimals),
                price_tick=None,
                min_notional=mapping.min_notional,
                equivalence_evidence=mapping.equivalence_evidence,
                price_decimals=6 - sz_decimals,
                max_price_significant_digits=5,
            )
            known[symbol] = _KnownMarket(asset_index, market)
        self._known_markets = known
        return tuple(item.market for item in known.values())

    async def order_book(self, market: VenueMarket) -> OrderBookSnapshot:
        """Map official ``l2Book`` levels; Hyperliquid supplies no sequence."""

        self._require_market(market)
        response = await self._info_transport(
            {"type": "l2Book", "coin": market.symbol},
        )
        payload = _mapping(response, "l2Book response")
        if _string(payload.get("coin"), "l2Book coin") != market.symbol:
            raise ValueError("l2Book coin does not match requested market")
        timestamp = _integer(payload.get("time"), "l2Book time")
        levels = _sequence(payload.get("levels"), "l2Book levels")
        if len(levels) != 2:
            raise ValueError("l2Book must contain bid and ask arrays")
        return OrderBookSnapshot(
            venue=self.venue,
            symbol=market.symbol,
            sequence=None,
            exchange_timestamp_ms=timestamp,
            received_timestamp_ms=self._received_timestamp_ms(),
            bids=_book_levels(levels[0], "bids"),
            asks=_book_levels(levels[1], "asks"),
        )

    def _require_market(self, market: VenueMarket) -> _KnownMarket:
        if market.venue != self.venue:
            raise ValueError("market does not belong to Hyperliquid")
        known = self._known_markets.get(market.symbol)
        if known is None or known.market != market:
            raise ValueError("market was not discovered from current metadata")
        return known


def _meta_and_contexts(
    response: object,
) -> tuple[Sequence[Mapping[str, object]], Sequence[object]]:
    outer = _sequence(response, "metaAndAssetCtxs response")
    if len(outer) != 2:
        raise ValueError("metaAndAssetCtxs must contain metadata and contexts")
    metadata = _mapping(outer[0], "meta")
    universe = _sequence(metadata.get("universe"), "meta universe")
    contexts = _sequence(outer[1], "asset contexts")
    if len(universe) != len(contexts):
        raise ValueError("meta universe and asset contexts length mismatch")
    return tuple(_mapping(item, "universe entry") for item in universe), contexts


def _book_levels(raw: object, side: str) -> tuple[BookLevel, ...]:
    levels = tuple(
        BookLevel(
            _decimal(_mapping(item, side).get("px"), f"{side} price"),
            _decimal(_mapping(item, side).get("sz"), f"{side} size"),
        )
        for item in _sequence(raw, side)
    )
    if not levels:
        raise ValueError(f"{side} cannot be empty")
    return levels


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{name} must be an array")
    return tuple(value)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    return value


def _decimal(value: object, name: str) -> Decimal:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a decimal string")
    try:
        decimal = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(f"{name} must be a decimal string") from error
    if not decimal.is_finite():
        raise ValueError(f"{name} must be finite")
    return decimal
