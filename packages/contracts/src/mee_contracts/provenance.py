"""Immutable reviewed market mappings for shadow pair evaluation."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from fractions import Fraction

from mee_contracts.exact import fraction_from_decimal
from mee_contracts.market import InstrumentIdentity, VenueMarket

SUPPORTED_ADDITIONAL_COST_COMPONENTS = frozenset(
    {
        ("GAS", "documented-entry-cost/v1"),
        ("ENTRY_STRESS", "synthetic-entry-stress/v1"),
    }
)


class LiquidityRole(StrEnum):
    """Liquidity role backed by documented fee evidence."""

    TAKER = "TAKER"


class FeeRoundingRule(StrEnum):
    """Venue fee rounding rule supported by the entry-cost model."""

    EXACT_QUOTE = "EXACT_QUOTE"


@dataclass(frozen=True, slots=True)
class FeeEvidence:
    """Versioned source evidence for one synthetic taker leg's fee."""

    venue: str
    liquidity_role: LiquidityRole
    fee_rate_bps: Decimal | None
    fee_currency: str | None
    fee_tier: str | None
    fee_scenario: str | None
    schedule_as_of_ms: int | None
    schedule_sha256: str | None
    rounding_rule: FeeRoundingRule | None
    minimum_fee_quote: Decimal | None


@dataclass(frozen=True, slots=True)
class CostComponent:
    """One documented non-fee entry-cost component in quote currency."""

    component_type: str
    amount_quote: Decimal | None
    currency: str | None
    model_version: str | None
    as_of_ms: int | None
    evidence_sha256: str | None


@dataclass(frozen=True, slots=True)
class EntryCostModel:
    """Immutable versioned provenance for both entry legs and extra costs."""

    model_version: str
    buy_fee: FeeEvidence
    sell_fee: FeeEvidence
    additional_costs: tuple[CostComponent, ...]


@dataclass(frozen=True, slots=True)
class ExactEntryCosts:
    """Exact quote-currency entry cost attribution before rendering."""

    buy_fee_quote: Fraction
    sell_fee_quote: Fraction
    additional_cost_quote: Fraction


def calculate_entry_costs(
    *,
    model: EntryCostModel,
    evaluated_at_ms: int,
    quote_currency: str,
    buy_venue: str,
    sell_venue: str,
    buy_notional: Fraction,
    sell_notional: Fraction,
) -> ExactEntryCosts | None:
    """Return exact per-leg costs only for complete quote-currency evidence."""
    if (
        type(model) is not EntryCostModel
        or type(model.model_version) is not str
        or model.model_version != "displayed-taker-entry-cost/v1"
        or not _is_timestamp(evaluated_at_ms)
        or not _nonempty_ascii(quote_currency)
        or not _nonempty_ascii(buy_venue)
        or not _nonempty_ascii(sell_venue)
        or type(buy_notional) is not Fraction
        or type(sell_notional) is not Fraction
        or buy_notional < 0
        or sell_notional < 0
        or type(model.additional_costs) is not tuple
    ):
        return None
    buy_fee = _fee_cost(
        evidence=model.buy_fee,
        venue=buy_venue,
        quote_currency=quote_currency,
        evaluated_at_ms=evaluated_at_ms,
        notional=buy_notional,
    )
    sell_fee = _fee_cost(
        evidence=model.sell_fee,
        venue=sell_venue,
        quote_currency=quote_currency,
        evaluated_at_ms=evaluated_at_ms,
        notional=sell_notional,
    )
    additional_cost = _additional_cost(
        components=model.additional_costs,
        quote_currency=quote_currency,
        evaluated_at_ms=evaluated_at_ms,
    )
    if buy_fee is None or sell_fee is None or additional_cost is None:
        return None
    return ExactEntryCosts(buy_fee, sell_fee, additional_cost)


def _fee_cost(
    *,
    evidence: FeeEvidence,
    venue: str,
    quote_currency: str,
    evaluated_at_ms: int,
    notional: Fraction,
) -> Fraction | None:
    if (
        type(evidence) is not FeeEvidence
        or not _nonempty_ascii(evidence.venue)
        or evidence.venue != venue
        or type(evidence.liquidity_role) is not LiquidityRole
        or evidence.liquidity_role is not LiquidityRole.TAKER
        or not _nonempty_ascii(evidence.fee_currency)
        or evidence.fee_currency != quote_currency
        or type(evidence.rounding_rule) is not FeeRoundingRule
        or evidence.rounding_rule is not FeeRoundingRule.EXACT_QUOTE
        or not _nonnegative_decimal(evidence.fee_rate_bps)
        or not _nonnegative_decimal(evidence.minimum_fee_quote)
        or not _nonempty_ascii(evidence.fee_tier)
        or not _nonempty_ascii(evidence.fee_scenario)
        or not _is_timestamp(evidence.schedule_as_of_ms)
        or evidence.schedule_as_of_ms > evaluated_at_ms
        or not _is_sha256(evidence.schedule_sha256)
    ):
        return None
    rate_fee = notional * fraction_from_decimal(evidence.fee_rate_bps) / 10_000
    return max(rate_fee, fraction_from_decimal(evidence.minimum_fee_quote))


def _additional_cost(
    *,
    components: tuple[CostComponent, ...],
    quote_currency: str,
    evaluated_at_ms: int,
) -> Fraction | None:
    result = Fraction()
    for component in components:
        if (
            type(component) is not CostComponent
            or not _nonempty_ascii(component.component_type)
            or not _nonnegative_decimal(component.amount_quote)
            or not _nonempty_ascii(component.currency)
            or component.currency != quote_currency
            or not _nonempty_ascii(component.model_version)
            or (
                component.component_type,
                component.model_version,
            )
            not in SUPPORTED_ADDITIONAL_COST_COMPONENTS
            or not _is_timestamp(component.as_of_ms)
            or component.as_of_ms > evaluated_at_ms
            or not _is_sha256(component.evidence_sha256)
        ):
            return None
        result += fraction_from_decimal(component.amount_quote)
    return result


class MappingDecision(StrEnum):
    """Reviewed mapping disposition."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class MarketMappingEvidence:
    """Reviewed evidence binding one active market to its contract metadata."""

    mapping_id: str
    mapping_version: str
    decision: MappingDecision
    venue: str
    symbol: str
    identity: InstrumentIdentity
    evidence_sha256: str
    evidence_reference: str
    valid_from_ms: int
    valid_until_ms: int | None
    reviewed_contract_multiplier: Decimal
    displayed_size_unit: str
    quantity_step: Decimal
    price_tick: Decimal | None
    price_decimals: int | None
    max_price_significant_digits: int | None
    min_quantity: Decimal | None
    min_notional: Decimal
    lighter_market_index: int | None = None

    def __post_init__(self) -> None:
        for value in (
            self.mapping_id,
            self.mapping_version,
            self.venue,
            self.symbol,
            self.evidence_reference,
            self.displayed_size_unit,
        ):
            _require_printable_ascii(value)
        if type(self.decision) is not MappingDecision:
            raise TypeError("mapping decision must be MappingDecision")
        if type(self.identity) is not InstrumentIdentity:
            raise TypeError("identity must be InstrumentIdentity")
        _require_sha256(self.evidence_sha256)
        _require_timestamp(self.valid_from_ms)
        if self.valid_until_ms is not None:
            _require_timestamp(self.valid_until_ms)
            if self.valid_until_ms < self.valid_from_ms:
                raise ValueError("validity interval is inconsistent")
        for value in (
            self.reviewed_contract_multiplier,
            self.quantity_step,
            self.min_notional,
        ):
            _require_positive_decimal(value)
        _require_optional_positive_decimal(self.price_tick)
        _require_optional_positive_decimal(self.min_quantity)
        _require_optional_nonnegative_int(self.price_decimals)
        _require_optional_positive_int(self.max_price_significant_digits)
        if (
            self.price_tick is None
            and self.price_decimals is None
            and self.max_price_significant_digits is None
        ):
            raise ValueError("mapping must define a price rule")
        if self.lighter_market_index is not None:
            if type(self.lighter_market_index) is not int:
                raise TypeError("lighter_market_index must be an integer")
            if self.lighter_market_index < 0:
                raise ValueError("lighter_market_index must be nonnegative")

    def valid_for(
        self,
        market: VenueMarket,
        evaluated_at_ms: int,
    ) -> bool:
        """Return whether this approved evidence exactly covers one market."""
        if type(market) is not VenueMarket or not _is_timestamp(evaluated_at_ms):
            return False
        if self.decision is not MappingDecision.APPROVED:
            return False
        if evaluated_at_ms < self.valid_from_ms:
            return False
        if self.valid_until_ms is not None and evaluated_at_ms > self.valid_until_ms:
            return False
        return (
            self.venue == market.venue
            and self.symbol == market.symbol
            and self.identity == market.identity
            and self.reviewed_contract_multiplier == market.contract_multiplier
            and self.displayed_size_unit == market.displayed_size_unit
            and self.quantity_step == market.quantity_step
            and self.price_tick == market.price_tick
            and self.price_decimals == market.price_decimals
            and self.max_price_significant_digits == market.max_price_significant_digits
            and self.min_quantity == market.min_quantity
            and self.min_notional == market.min_notional
        )


def validate_mapping_pair(
    *,
    evaluated_at_ms: int,
    buy_market: VenueMarket,
    buy_mapping: MarketMappingEvidence | None,
    sell_market: VenueMarket,
    sell_mapping: MarketMappingEvidence | None,
) -> bool:
    """Return whether both active markets have current approved mappings."""
    return (
        type(buy_mapping) is MarketMappingEvidence
        and type(sell_mapping) is MarketMappingEvidence
        and buy_mapping.mapping_id != sell_mapping.mapping_id
        and buy_mapping.valid_for(buy_market, evaluated_at_ms)
        and sell_mapping.valid_for(sell_market, evaluated_at_ms)
    )


def _require_printable_ascii(value: object) -> None:
    if (
        type(value) is not str
        or not value
        or any(character == "\\" or not 33 <= ord(character) <= 126 for character in value)
    ):
        raise ValueError("mapping text must be nonempty printable ASCII")


def _require_sha256(value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("evidence SHA-256 must be lowercase hexadecimal")


def _require_timestamp(value: object) -> None:
    if not _is_timestamp(value):
        raise TypeError("timestamp must be an integer")


def _is_timestamp(value: object) -> bool:
    return type(value) is int and value >= 0


def _is_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _nonempty_ascii(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and all(33 <= ord(character) <= 126 and character != "\\" for character in value)
    )


def _nonnegative_decimal(value: object) -> bool:
    return type(value) is Decimal and value.is_finite() and value >= Decimal("0")


def _require_positive_decimal(value: object) -> None:
    if type(value) is not Decimal:
        raise TypeError("value must be Decimal")
    if not value.is_finite() or value <= Decimal("0"):
        raise ValueError("Decimal value must be finite and positive")


def _require_optional_positive_decimal(value: object) -> None:
    if value is not None:
        _require_positive_decimal(value)


def _require_optional_nonnegative_int(value: object) -> None:
    if value is not None and (type(value) is not int or value < 0):
        raise TypeError("decimal places must be a nonnegative integer")


def _require_optional_positive_int(value: object) -> None:
    if value is not None and (type(value) is not int or value <= 0):
        raise TypeError("significant digits must be a positive integer")
