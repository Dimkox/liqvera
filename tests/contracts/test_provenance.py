"""Tests for reviewed market-mapping evidence."""

import unittest
from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

from mee_contracts import provenance
from mee_contracts.market import InstrumentIdentity, VenueMarket
from mee_contracts.provenance import (
    CostComponent,
    EntryCostModel,
    FeeEvidence,
    FeeRoundingRule,
    LiquidityRole,
    MappingDecision,
    MarketMappingEvidence,
    calculate_entry_costs,
    validate_mapping_pair,
)

IDENTITY = InstrumentIdentity(
    base_asset="TOKEN",
    quote_asset="USD",
    product_kind="PERPETUAL",
    settlement_asset="USD",
    payoff_kind="LINEAR",
)


class StringSubclass(str):
    """Deliberately non-exact string used at the strict provenance boundary."""


class EqualitySpoof:
    """Non-string that can compare equal to one expected provenance value."""

    def __init__(self, expected: str) -> None:
        self.expected = expected

    def __eq__(self, other: object) -> bool:
        return other == self.expected


def market(venue: str, *, size_unit: str = "contracts") -> VenueMarket:
    return VenueMarket(
        venue=venue,
        symbol="TOKEN-PERP",
        identity=IDENTITY,
        contract_multiplier=Decimal("10"),
        displayed_size_unit=size_unit,
        quantity_step=Decimal("0.01"),
        price_tick=Decimal("0.01"),
        min_notional=Decimal("1"),
        equivalence_evidence="reviewed-equivalence-v1",
    )


def mapping(mapping_venue: str, **overrides: object) -> MarketMappingEvidence:
    values: dict[str, object] = {
        "mapping_id": f"mapping-{mapping_venue.lower()}-token-usd-v1",
        "mapping_version": "mapping/v1",
        "decision": MappingDecision.APPROVED,
        "venue": mapping_venue,
        "symbol": "TOKEN-PERP",
        "identity": IDENTITY,
        "evidence_sha256": "a" * 64,
        "evidence_reference": "repo:docs/mappings/token-usd-v1",
        "valid_from_ms": 1,
        "valid_until_ms": None,
        "reviewed_contract_multiplier": Decimal("10"),
        "displayed_size_unit": "contracts",
        "quantity_step": Decimal("0.01"),
        "price_tick": Decimal("0.01"),
        "price_decimals": None,
        "max_price_significant_digits": None,
        "min_quantity": None,
        "min_notional": Decimal("1"),
    }
    values.update(overrides)
    return MarketMappingEvidence(**values)  # type: ignore[arg-type]


def fee(venue: str, **overrides: object) -> FeeEvidence:
    values: dict[str, object] = {
        "venue": venue,
        "liquidity_role": LiquidityRole.TAKER,
        "fee_rate_bps": Decimal("10"),
        "fee_currency": "USD",
        "fee_tier": "STANDARD",
        "fee_scenario": "DOCUMENTED",
        "schedule_as_of_ms": 10_000,
        "schedule_sha256": "b" * 64,
        "rounding_rule": FeeRoundingRule.EXACT_QUOTE,
        "minimum_fee_quote": Decimal("0"),
    }
    values.update(overrides)
    return FeeEvidence(**values)  # type: ignore[arg-type]


def component(**overrides: object) -> CostComponent:
    values: dict[str, object] = {
        "component_type": "GAS",
        "amount_quote": Decimal("1.25"),
        "currency": "USD",
        "model_version": "documented-entry-cost/v1",
        "as_of_ms": 10_000,
        "evidence_sha256": "c" * 64,
    }
    values.update(overrides)
    return CostComponent(**values)  # type: ignore[arg-type]


def costs(model: EntryCostModel) -> object:
    return calculate_entry_costs(
        model=model,
        evaluated_at_ms=10_200,
        quote_currency="USD",
        buy_venue="BUY",
        sell_venue="SELL",
        buy_notional=Fraction(100),
        sell_notional=Fraction(120),
    )


def entry_cost_model(
    *,
    model_version: str = "displayed-taker-entry-cost/v1",
    buy_fee: FeeEvidence | None = None,
    sell_fee: FeeEvidence | None = None,
    additional_costs: tuple[CostComponent, ...] = (),
) -> EntryCostModel:
    return EntryCostModel(
        model_version=model_version,
        buy_fee=fee("BUY") if buy_fee is None else buy_fee,
        sell_fee=fee("SELL") if sell_fee is None else sell_fee,
        additional_costs=additional_costs,
    )


class MarketMappingEvidenceTests(unittest.TestCase):
    def test_approved_current_matching_mappings_accept(self) -> None:
        self.assertTrue(
            validate_mapping_pair(
                evaluated_at_ms=10,
                buy_market=market("BUY"),
                buy_mapping=mapping("BUY"),
                sell_market=market("SELL"),
                sell_mapping=mapping("SELL"),
            )
        )

    def test_rejects_missing_or_non_evidence_mappings(self) -> None:
        for buy_mapping, sell_mapping in (
            (None, mapping("SELL")),
            (mapping("BUY"), None),
            (object(), mapping("SELL")),
            (mapping("BUY"), object()),
        ):
            with self.subTest(buy_mapping=buy_mapping, sell_mapping=sell_mapping):
                self.assertFalse(
                    validate_mapping_pair(
                        evaluated_at_ms=10,
                        buy_market=market("BUY"),
                        buy_mapping=buy_mapping,  # type: ignore[arg-type]
                        sell_market=market("SELL"),
                        sell_mapping=sell_mapping,  # type: ignore[arg-type]
                    )
                )

    def test_rejects_equal_mapping_ids_across_pair_legs(self) -> None:
        shared_id = "mapping-shared-token-usd-v1"

        self.assertFalse(
            validate_mapping_pair(
                evaluated_at_ms=10,
                buy_market=market("BUY"),
                buy_mapping=mapping("BUY", mapping_id=shared_id),
                sell_market=market("SELL"),
                sell_mapping=mapping("SELL", mapping_id=shared_id),
            )
        )

    def test_rejects_unapproved_or_out_of_window_mappings(self) -> None:
        invalid = (
            replace(mapping("BUY"), decision=MappingDecision.REJECTED),
            replace(mapping("BUY"), valid_from_ms=11),
            replace(mapping("BUY"), valid_until_ms=9),
        )
        for buy_mapping in invalid:
            with self.subTest(buy_mapping=buy_mapping):
                self.assertFalse(
                    validate_mapping_pair(
                        evaluated_at_ms=10,
                        buy_market=market("BUY"),
                        buy_mapping=buy_mapping,
                        sell_market=market("SELL"),
                        sell_mapping=mapping("SELL"),
                    )
                )

    def test_rejects_any_mismatched_reviewed_market_field(self) -> None:
        alternatives = (
            {"identity": replace(IDENTITY, base_asset="OTHER")},
            {"symbol": "OTHER-PERP"},
            {"venue": "OTHER"},
            {"reviewed_contract_multiplier": Decimal("11")},
            {"displayed_size_unit": "lots"},
            {"quantity_step": Decimal("0.1")},
            {"price_tick": Decimal("0.1")},
            {"price_decimals": 2, "price_tick": None},
            {"max_price_significant_digits": 5, "price_tick": None},
            {"min_quantity": Decimal("1")},
            {"min_notional": Decimal("2")},
        )
        for replacement in alternatives:
            with self.subTest(replacement=replacement):
                self.assertFalse(mapping("BUY", **replacement).valid_for(market("BUY"), 10))

    def test_rejects_missing_empty_or_mismatched_active_size_unit(self) -> None:
        valid_mapping = mapping("BUY")
        with self.assertRaises(ValueError):
            market("BUY", size_unit="")
        self.assertFalse(valid_mapping.valid_for(market("BUY", size_unit="lots"), 10))
        with self.assertRaises(TypeError):
            VenueMarket(  # type: ignore[call-arg]
                venue="BUY",
                symbol="TOKEN-PERP",
                identity=IDENTITY,
                contract_multiplier=Decimal("10"),
                quantity_step=Decimal("0.01"),
                price_tick=Decimal("0.01"),
                min_notional=Decimal("1"),
                equivalence_evidence="reviewed-equivalence-v1",
            )

    def test_lighter_market_index_defaults_to_none(self) -> None:
        evidence = mapping("BUY")
        self.assertIsNone(evidence.lighter_market_index)

    def test_lighter_market_index_accepts_nonnegative_int(self) -> None:
        self.assertEqual(mapping("lighter", lighter_market_index=0).lighter_market_index, 0)
        self.assertEqual(mapping("lighter", lighter_market_index=1).lighter_market_index, 1)

    def test_lighter_market_index_rejects_bool_and_negative(self) -> None:
        with self.assertRaises(TypeError):
            mapping("lighter", lighter_market_index=True)
        with self.assertRaises(ValueError):
            mapping("lighter", lighter_market_index=-1)

    def test_rejects_invalid_evidence_construction(self) -> None:
        invalid = (
            {"mapping_id": ""},
            {"mapping_version": ""},
            {"evidence_reference": ""},
            {"evidence_sha256": "A" * 64},
            {"evidence_sha256": "a" * 63},
            {"valid_from_ms": True},
            {"valid_until_ms": True},
            {"valid_until_ms": 0},
            {"reviewed_contract_multiplier": 10.0},
            {"quantity_step": 0.01},
            {"price_tick": 0.01},
            {"min_quantity": 0.01},
            {"min_notional": 1.0},
        )
        for replacement in invalid:
            with self.subTest(replacement=replacement):
                with self.assertRaises((TypeError, ValueError)):
                    mapping("BUY", **replacement)

    def test_rejects_malformed_active_market_numerics(self) -> None:
        for field in (
            "contract_multiplier",
            "quantity_step",
            "min_notional",
        ):
            for malformed in (True, 1):
                with self.subTest(field=field, malformed=malformed):
                    with self.assertRaises(TypeError):
                        replace(market("BUY"), **{field: malformed})

    def test_leaves_mapping_and_market_inputs_unchanged(self) -> None:
        active_market = market("BUY")
        active_mapping = mapping("BUY")
        before = (active_market, active_mapping)

        self.assertTrue(active_mapping.valid_for(active_market, 10))

        self.assertEqual((active_market, active_mapping), before)


class EntryCostEvidenceTests(unittest.TestCase):
    def test_supported_additional_cost_pairs_are_exact_and_immutable(self) -> None:
        allowlist = getattr(
            provenance,
            "SUPPORTED_ADDITIONAL_COST_COMPONENTS",
            None,
        )

        self.assertEqual(
            allowlist,
            frozenset(
                {
                    ("GAS", "documented-entry-cost/v1"),
                    ("ENTRY_STRESS", "synthetic-entry-stress/v1"),
                }
            ),
        )
        self.assertIsInstance(allowlist, frozenset)
        with self.assertRaises(AttributeError):
            allowlist.add(("OTHER", "other/v1"))  # type: ignore[union-attr]

    def test_accepts_each_supported_additional_cost_pair(self) -> None:
        supported = (
            ("GAS", "documented-entry-cost/v1"),
            ("ENTRY_STRESS", "synthetic-entry-stress/v1"),
        )

        for component_type, model_version in supported:
            with self.subTest(
                component_type=component_type,
                model_version=model_version,
            ):
                result = costs(
                    entry_cost_model(
                        additional_costs=(
                            component(
                                component_type=component_type,
                                model_version=model_version,
                            ),
                        )
                    )
                )
                self.assertIsNotNone(result)

    def test_rejects_unknown_additional_cost_type_version_pairs(self) -> None:
        unsupported = (
            ("UNKNOWN", "documented-entry-cost/v1"),
            ("GAS", "unknown-entry-cost/v1"),
            ("GAS", "synthetic-entry-stress/v1"),
            ("ENTRY_STRESS", "documented-entry-cost/v1"),
        )

        for component_type, model_version in unsupported:
            with self.subTest(
                component_type=component_type,
                model_version=model_version,
            ):
                self.assertIsNone(
                    costs(
                        entry_cost_model(
                            additional_costs=(
                                component(
                                    component_type=component_type,
                                    model_version=model_version,
                                ),
                            )
                        )
                    )
                )

    def test_complete_taker_evidence_calculates_exact_per_leg_costs(self) -> None:
        result = costs(
            EntryCostModel(
                model_version="displayed-taker-entry-cost/v1",
                buy_fee=fee("BUY"),
                sell_fee=fee("SELL", fee_rate_bps=Decimal("20")),
                additional_costs=(component(), component(amount_quote=Decimal("0.75"))),
            )
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.buy_fee_quote, Fraction(1, 10))
        self.assertEqual(result.sell_fee_quote, Fraction(6, 25))
        self.assertEqual(result.additional_cost_quote, Fraction(2))

    def test_minimum_fee_applies_to_each_synthetic_leg_order(self) -> None:
        result = costs(
            EntryCostModel(
                model_version="displayed-taker-entry-cost/v1",
                buy_fee=fee("BUY", minimum_fee_quote=Decimal("0.5")),
                sell_fee=fee("SELL", minimum_fee_quote=Decimal("0.75")),
                additional_costs=(),
            )
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.buy_fee_quote, Fraction(1, 2))
        self.assertEqual(result.sell_fee_quote, Fraction(3, 4))

    def test_rejects_unknown_or_invalid_cost_evidence(self) -> None:
        invalid_models = (
            entry_cost_model(buy_fee=fee("BUY", fee_rate_bps=None)),
            entry_cost_model(buy_fee=fee("BUY", schedule_sha256=None)),
            entry_cost_model(buy_fee=fee("BUY", schedule_as_of_ms=None)),
            entry_cost_model(buy_fee=fee("BUY", rounding_rule=None)),
            entry_cost_model(buy_fee=fee("BUY", minimum_fee_quote=None)),
            entry_cost_model(buy_fee=fee("BUY", liquidity_role=object())),
            entry_cost_model(buy_fee=fee("BUY", liquidity_role="MAKER")),
            entry_cost_model(buy_fee=fee("BUY", fee_currency=None)),
            entry_cost_model(buy_fee=fee("BUY", fee_currency="EUR")),
            entry_cost_model(buy_fee=fee(StringSubclass("BUY"))),
            entry_cost_model(buy_fee=fee(EqualitySpoof("BUY"))),
            entry_cost_model(buy_fee=fee("BUY", fee_currency=StringSubclass("USD"))),
            entry_cost_model(buy_fee=fee("BUY", fee_currency=EqualitySpoof("USD"))),
            entry_cost_model(buy_fee=replace(fee("BUY"), venue="SELL")),
            entry_cost_model(buy_fee=fee("BUY", schedule_as_of_ms=10_201)),
            entry_cost_model(model_version="unsupported/v1"),
            entry_cost_model(buy_fee=fee("BUY", fee_rate_bps=10.0)),
            entry_cost_model(buy_fee=fee("BUY", fee_rate_bps=Decimal("-1"))),
            entry_cost_model(buy_fee=fee("BUY", fee_rate_bps=Decimal("NaN"))),
            entry_cost_model(additional_costs=(component(amount_quote=None),)),
            entry_cost_model(additional_costs=(component(currency=None),)),
            entry_cost_model(additional_costs=(component(currency="EUR"),)),
            entry_cost_model(additional_costs=(component(currency=StringSubclass("USD")),)),
            entry_cost_model(additional_costs=(component(currency=EqualitySpoof("USD")),)),
            entry_cost_model(additional_costs=(component(model_version=None),)),
            entry_cost_model(additional_costs=(component(as_of_ms=None),)),
            entry_cost_model(additional_costs=(component(as_of_ms=10_201),)),
            entry_cost_model(additional_costs=(component(evidence_sha256=None),)),
            entry_cost_model(additional_costs=(component(amount_quote=Decimal("-1")),)),
            entry_cost_model(additional_costs=(component(amount_quote=Decimal("Infinity")),)),
        )

        for model in invalid_models:
            with self.subTest(model=model):
                self.assertIsNone(costs(model))

    def test_documented_decimal_zero_is_not_unknown(self) -> None:
        result = costs(
            EntryCostModel(
                model_version="displayed-taker-entry-cost/v1",
                buy_fee=fee("BUY", fee_rate_bps=Decimal("0")),
                sell_fee=fee("SELL", fee_rate_bps=Decimal("0")),
                additional_costs=(component(amount_quote=Decimal("0")),),
            )
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result, type(result)(Fraction(), Fraction(), Fraction()))


if __name__ == "__main__":
    unittest.main()
