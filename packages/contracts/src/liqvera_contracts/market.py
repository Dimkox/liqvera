"""Market identity, discovery, and public order-book contracts."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, order=True, slots=True)
class InstrumentIdentity:
    """Venue-neutral economic identity of one derivative contract."""

    base_asset: str
    quote_asset: str
    product_kind: str
    settlement_asset: str
    payoff_kind: str


@dataclass(frozen=True, slots=True)
class VenueMarket:
    """One venue's representation of a normalized instrument."""

    venue: str
    symbol: str
    identity: InstrumentIdentity
    contract_multiplier: Decimal
    displayed_size_unit: str
    quantity_step: Decimal
    price_tick: Decimal | None
    min_notional: Decimal
    equivalence_evidence: str
    price_decimals: int | None = None
    max_price_significant_digits: int | None = None
    min_quantity: Decimal | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.displayed_size_unit, str)
            or not self.displayed_size_unit
        ):
            raise ValueError("displayed size unit is required")
        positive_fields = (
            self.contract_multiplier,
            self.quantity_step,
            self.min_notional,
        )
        if any(type(value) is not Decimal for value in positive_fields):
            raise TypeError("market numeric constraints must be Decimal")
        if any(not value.is_finite() for value in positive_fields):
            raise ValueError("market numeric constraints must be finite")
        if any(value <= Decimal("0") for value in positive_fields):
            raise ValueError("market numeric constraints must be positive")
        if self.price_tick is not None:
            if not isinstance(self.price_tick, Decimal):
                raise TypeError("price_tick must be Decimal or None")
            if self.price_tick <= Decimal("0"):
                raise ValueError("price_tick must be positive")
        if self.min_quantity is not None:
            if not isinstance(self.min_quantity, Decimal):
                raise TypeError("min_quantity must be Decimal or None")
            if self.min_quantity <= Decimal("0"):
                raise ValueError("min_quantity must be positive")
        if self.price_decimals is not None and self.price_decimals < 0:
            raise ValueError("price_decimals cannot be negative")
        if (
            self.max_price_significant_digits is not None
            and self.max_price_significant_digits <= 0
        ):
            raise ValueError(
                "max_price_significant_digits must be positive",
            )
        if (
            self.price_tick is None
            and self.price_decimals is None
            and self.max_price_significant_digits is None
        ):
            raise ValueError("market must define a price rule")


@dataclass(frozen=True, slots=True)
class CommonMarket:
    """Verified representations of one instrument on multiple venues."""

    identity: InstrumentIdentity
    markets: tuple[VenueMarket, ...]


def discover_common_markets(
    markets: Iterable[VenueMarket],
    *,
    minimum_venues: int,
) -> tuple[CommonMarket, ...]:
    """Return verified identities represented by distinct venues."""

    if minimum_venues < 2:
        raise ValueError("common market discovery requires two venues")

    grouped: dict[InstrumentIdentity, dict[str, VenueMarket]] = defaultdict(
        dict,
    )
    for item in markets:
        if not item.equivalence_evidence.strip():
            continue
        if item.venue in grouped[item.identity]:
            raise ValueError(
                "venue returned an ambiguous normalized instrument",
            )
        grouped[item.identity][item.venue] = item

    common = (
        CommonMarket(
            identity=identity,
            markets=tuple(
                venue_markets[venue]
                for venue in sorted(venue_markets)
            ),
        )
        for identity, venue_markets in grouped.items()
        if len(venue_markets) >= minimum_venues
    )
    return tuple(sorted(common, key=lambda item: item.identity))


@dataclass(frozen=True, slots=True)
class BookLevel:
    """One exact price level."""

    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if self.price <= Decimal("0") or self.quantity <= Decimal("0"):
            raise ValueError("book level values must be positive")


@dataclass(frozen=True, slots=True)
class OrderBookSnapshot:
    """One complete, ordered, venue-native L2 snapshot."""

    venue: str
    symbol: str
    sequence: int | None
    exchange_timestamp_ms: int
    received_timestamp_ms: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]

    def __post_init__(self) -> None:
        if not self.bids or not self.asks:
            raise ValueError("order book must contain both sides")
        if not _strictly_descending(self.bids):
            raise ValueError("bids must be strictly price-descending")
        if not _strictly_ascending(self.asks):
            raise ValueError("asks must be strictly price-ascending")
        if self.bids[0].price >= self.asks[0].price:
            raise ValueError("order book cannot be crossed or locked")

    @property
    def best_bid(self) -> BookLevel:
        return self.bids[0]

    @property
    def best_ask(self) -> BookLevel:
        return self.asks[0]

    @property
    def age_at_receive_ms(self) -> int:
        return self.received_timestamp_ms - self.exchange_timestamp_ms


def _strictly_descending(levels: tuple[BookLevel, ...]) -> bool:
    return all(
        previous.price > current.price
        for previous, current in zip(levels, levels[1:], strict=False)
    )


def _strictly_ascending(levels: tuple[BookLevel, ...]) -> bool:
    return all(
        previous.price < current.price
        for previous, current in zip(levels, levels[1:], strict=False)
    )
