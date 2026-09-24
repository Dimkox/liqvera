import importlib
import unittest
from decimal import Decimal

book = importlib.import_module("mee_contracts.market")


class OrderBookTests(unittest.TestCase):
    def test_accepts_exact_sorted_non_crossed_snapshot(self):
        level_type = getattr(book, "BookLevel", None)
        snapshot_type = getattr(book, "OrderBookSnapshot", None)

        self.assertIsNotNone(level_type)
        self.assertIsNotNone(snapshot_type)

        snapshot = snapshot_type(
            venue="DEX_A",
            symbol="DOGE",
            sequence=42,
            exchange_timestamp_ms=1_000,
            received_timestamp_ms=1_005,
            bids=(
                level_type(Decimal("0.1234"), Decimal("100")),
                level_type(Decimal("0.1233"), Decimal("200")),
            ),
            asks=(
                level_type(Decimal("0.1235"), Decimal("150")),
                level_type(Decimal("0.1236"), Decimal("250")),
            ),
        )

        self.assertEqual(snapshot.best_bid.price, Decimal("0.1234"))
        self.assertEqual(snapshot.best_ask.price, Decimal("0.1235"))
        self.assertEqual(snapshot.age_at_receive_ms, 5)

    def test_allows_snapshot_without_an_exchange_sequence(self):
        level_type = getattr(book, "BookLevel", None)
        snapshot_type = getattr(book, "OrderBookSnapshot", None)

        self.assertIsNotNone(level_type)
        self.assertIsNotNone(snapshot_type)
        self.assertEqual(snapshot_type.__annotations__["sequence"], int | None)

        snapshot = snapshot_type(
            venue="DEX_WITHOUT_SEQUENCE",
            symbol="ARBITRARY",
            sequence=None,
            exchange_timestamp_ms=1_000,
            received_timestamp_ms=1_005,
            bids=(level_type(Decimal("1.0"), Decimal("2")),),
            asks=(level_type(Decimal("1.1"), Decimal("3")),),
        )

        self.assertIsNone(snapshot.sequence)

    def test_rejects_invalid_levels_ordering_and_crossed_books(self):
        level_type = getattr(book, "BookLevel", None)
        snapshot_type = getattr(book, "OrderBookSnapshot", None)

        self.assertIsNotNone(level_type)
        self.assertIsNotNone(snapshot_type)

        for price, quantity in (
            (Decimal("0"), Decimal("1")),
            (Decimal("1"), Decimal("0")),
        ):
            with self.subTest(price=price, quantity=quantity):
                with self.assertRaises(ValueError):
                    level_type(price, quantity)

        valid = {
            "venue": "DEX_A",
            "symbol": "DOGE",
            "sequence": 42,
            "exchange_timestamp_ms": 1_000,
            "received_timestamp_ms": 1_005,
        }
        with self.assertRaises(ValueError):
            snapshot_type(
                **valid,
                bids=(
                    level_type(Decimal("1"), Decimal("1")),
                    level_type(Decimal("2"), Decimal("1")),
                ),
                asks=(level_type(Decimal("3"), Decimal("1")),),
            )
        with self.assertRaises(ValueError):
            snapshot_type(
                **valid,
                bids=(level_type(Decimal("2"), Decimal("1")),),
                asks=(level_type(Decimal("2"), Decimal("1")),),
            )


if __name__ == "__main__":
    unittest.main()
