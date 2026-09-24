import importlib
import unittest
from decimal import Decimal

market = importlib.import_module("mee_contracts.market")


class MarketCatalogTests(unittest.TestCase):
    def test_discovers_any_verified_contract_shared_by_two_venues(self):
        identity_type = getattr(market, "InstrumentIdentity", None)
        venue_market_type = getattr(market, "VenueMarket", None)
        discover = getattr(market, "discover_common_markets", None)

        self.assertIsNotNone(identity_type)
        self.assertIsNotNone(venue_market_type)
        self.assertIsNotNone(discover)

        doge_perp = identity_type(
            base_asset="DOGE",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )
        markets = (
            venue_market_type(
                venue="HYPERLIQUID",
                symbol="DOGE",
                identity=doge_perp,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.00001"),
                min_notional=Decimal("10"),
                equivalence_evidence="sha256:hl-doge",
            ),
            venue_market_type(
                venue="LIGHTER",
                symbol="DOGE",
                identity=doge_perp,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.000001"),
                min_notional=Decimal("10"),
                equivalence_evidence="sha256:lighter-doge",
            ),
        )

        common = discover(markets, minimum_venues=2)

        self.assertEqual(len(common), 1)
        self.assertEqual(common[0].identity, doge_perp)
        self.assertEqual(
            {item.venue for item in common[0].markets},
            {"HYPERLIQUID", "LIGHTER"},
        )

    def test_excludes_unverified_or_non_equivalent_ticker_matches(self):
        identity_type = getattr(market, "InstrumentIdentity", None)
        venue_market_type = getattr(market, "VenueMarket", None)
        discover = getattr(market, "discover_common_markets", None)

        self.assertIsNotNone(identity_type)
        self.assertIsNotNone(venue_market_type)
        self.assertIsNotNone(discover)

        linear = identity_type(
            base_asset="PUMP",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )
        inverse = identity_type(
            base_asset="PUMP",
            quote_asset="USD",
            product_kind="PERPETUAL",
            settlement_asset="PUMP",
            payoff_kind="INVERSE",
        )
        markets = (
            venue_market_type(
                venue="DEX_A",
                symbol="PUMP",
                identity=linear,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.000001"),
                min_notional=Decimal("10"),
                equivalence_evidence="sha256:dex-a-pump",
            ),
            venue_market_type(
                venue="DEX_B",
                symbol="PUMP",
                identity=linear,
                contract_multiplier=Decimal("1000"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.000001"),
                min_notional=Decimal("10"),
                equivalence_evidence="",
            ),
            venue_market_type(
                venue="CEX_C",
                symbol="PUMP",
                identity=inverse,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.01"),
                min_notional=Decimal("10"),
                equivalence_evidence="sha256:cex-c-pump",
            ),
        )

        common = discover(markets, minimum_venues=2)

        self.assertEqual(common, ())

    def test_rejects_invalid_market_math_and_single_venue_discovery(self):
        identity = market.InstrumentIdentity(
            base_asset="DOGE",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )
        valid = {
            "venue": "DEX_A",
            "symbol": "DOGE",
            "identity": identity,
            "contract_multiplier": Decimal("1"),
            "displayed_size_unit": "contracts",
            "quantity_step": Decimal("1"),
            "price_tick": Decimal("0.00001"),
            "min_notional": Decimal("10"),
            "equivalence_evidence": "sha256:dex-a-doge",
        }

        for field in (
            "contract_multiplier",
            "quantity_step",
            "price_tick",
            "min_notional",
        ):
            invalid = dict(valid)
            invalid[field] = Decimal("0")
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    market.VenueMarket(**invalid)

        with self.assertRaises(ValueError):
            market.discover_common_markets((), minimum_venues=1)

    def test_rejects_bool_and_int_market_numeric_fields(self):
        identity = market.InstrumentIdentity(
            base_asset="DOGE",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )
        valid = {
            "venue": "DEX_A",
            "symbol": "DOGE",
            "identity": identity,
            "contract_multiplier": Decimal("1"),
            "displayed_size_unit": "contracts",
            "quantity_step": Decimal("1"),
            "price_tick": Decimal("0.00001"),
            "min_notional": Decimal("10"),
            "equivalence_evidence": "sha256:dex-a-doge",
        }

        for field in (
            "contract_multiplier",
            "quantity_step",
            "min_notional",
        ):
            for malformed in (True, 1):
                with self.subTest(field=field, malformed=malformed):
                    invalid = valid | {field: malformed}
                    with self.assertRaises(TypeError):
                        market.VenueMarket(**invalid)

    def test_rejects_ambiguous_identity_within_one_venue(self):
        identity = market.InstrumentIdentity(
            base_asset="DOGE",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )

        def venue_market(symbol):
            return market.VenueMarket(
                venue="DEX_A",
                symbol=symbol,
                identity=identity,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("1"),
                price_tick=Decimal("0.00001"),
                min_notional=Decimal("10"),
                equivalence_evidence=f"sha256:{symbol.lower()}",
            )

        with self.assertRaises(ValueError):
            market.discover_common_markets(
                (venue_market("DOGE"), venue_market("1000DOGE")),
                minimum_venues=2,
            )

    def test_supports_decimal_and_significant_digit_price_rules(self):
        fields = market.VenueMarket.__dataclass_fields__
        self.assertIn("price_decimals", fields)
        self.assertIn("max_price_significant_digits", fields)

        identity = market.InstrumentIdentity(
            base_asset="ARBITRARY",
            quote_asset="USDC",
            product_kind="PERPETUAL",
            settlement_asset="USDC",
            payoff_kind="LINEAR",
        )

        venue_market = market.VenueMarket(
            venue="DEX_VARIABLE_TICK",
            symbol="ARBITRARY",
            identity=identity,
            contract_multiplier=Decimal("1"),
            displayed_size_unit="contracts",
            quantity_step=Decimal("0.001"),
            price_tick=None,
            min_notional=Decimal("10"),
            equivalence_evidence="sha256:variable-tick",
            price_decimals=3,
            max_price_significant_digits=5,
        )

        self.assertIsNone(venue_market.price_tick)
        self.assertEqual(venue_market.price_decimals, 3)

        with self.assertRaises(ValueError):
            market.VenueMarket(
                venue="DEX_WITHOUT_PRICE_RULE",
                symbol="ARBITRARY",
                identity=identity,
                contract_multiplier=Decimal("1"),
                displayed_size_unit="contracts",
                quantity_step=Decimal("0.001"),
                price_tick=None,
                min_notional=Decimal("10"),
                equivalence_evidence="sha256:missing-price-rule",
            )


if __name__ == "__main__":
    unittest.main()
