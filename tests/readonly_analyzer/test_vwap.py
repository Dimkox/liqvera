"""Full-depth Hyperliquid VWAP over reconstructed books is fail-closed."""

from __future__ import annotations

import hashlib
import inspect
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.evidence import RawPublicEnvelope
from mee_contracts.exact import ExactDecimal
from mee_contracts.market import InstrumentIdentity
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence
from mee_contracts.reasons import ShadowRejectCode
from mee_readonly_analyzer.identity import IdentityBindError, bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import reconstruct_books
from mee_readonly_analyzer.vwap import (
    DepthRejected,
    ExecutableFill,
    Side,
    VwapError,
    sweep_depth,
)

RUN = UUID("00000000-0000-0000-0000-000000000001")
FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
)
LIGHTER_SNAPSHOT = (
    b'{"channel":"order_book:1","type":"subscribed/order_book","timestamp":1,'
    b'"symbol":"BTC","order_book":{"nonce":10,"bids":[{"price":"1.0","size":"1.0"}],'
    b'"asks":[{"price":"1.1","size":"1.0"}]}}'
)
TWO_ASK_BOOK = (
    b'{"coin":"BTC","time":1,"levels":['
    b'[{"px":"1.0","sz":"1.0"}],'
    b'[{"px":"1.1","sz":"1.0"},{"px":"1.2","sz":"1.0"}]]}'
)
IDENTITY = InstrumentIdentity(
    base_asset="BTC",
    quote_asset="USD",
    product_kind="perp",
    settlement_asset="USD",
    payoff_kind="linear",
)


def _envelope(
    payload: bytes,
    *,
    venue: str = "hyperliquid",
    envelope_index: int = 0,
    observed_at_ms: int = 1,
) -> RawPublicEnvelope:
    return RawPublicEnvelope(
        capture_run_id=RUN,
        envelope_index=envelope_index,
        observed_at_ms=observed_at_ms,
        venue=venue,
        payload_sha256=hashlib.sha256(payload).hexdigest(),
        payload=payload,
    )


def _mapping(**overrides: object) -> MarketMappingEvidence:
    values: dict[str, object] = {
        "mapping_id": "map-1",
        "mapping_version": "v1",
        "decision": MappingDecision.APPROVED,
        "venue": "hyperliquid",
        "symbol": "BTC",
        "identity": IDENTITY,
        "evidence_sha256": "a" * 64,
        "evidence_reference": "reviewed/v1",
        "valid_from_ms": 0,
        "valid_until_ms": None,
        "reviewed_contract_multiplier": Decimal("1"),
        "displayed_size_unit": "coin",
        "quantity_step": Decimal("0.001"),
        "price_tick": Decimal("0.1"),
        "price_decimals": None,
        "max_price_significant_digits": None,
        "min_quantity": None,
        "min_notional": Decimal("10"),
    }
    values.update(overrides)
    return MarketMappingEvidence(**values)  # type: ignore[arg-type]


def _reconstruct(payload: bytes):
    books = reconstruct_books((_envelope(payload),))
    assert len(books) == 1
    return books[0]


def _bound(payload: bytes, **mapping_overrides: object):
    books = reconstruct_books((_envelope(payload),))
    assert len(books) == 1
    bound = bind_reconstructed_books(books, (_mapping(**mapping_overrides),))
    assert len(bound) == 1
    return bound[0]


def test_fixture_buy_one_sweeps_the_ask() -> None:
    book = _bound(FIXTURE_BOOK)
    snapshot = book.snapshot
    fill = sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert fill.side is Side.BUY
    assert fill.envelope_index == book.envelope_index
    assert fill.payload_sha256 == book.payload_sha256
    assert fill.epoch_id == book.epoch_id
    assert fill.requested_quantity == Fraction(1)
    assert fill.filled_quantity == fill.requested_quantity
    assert fill.notional_quote == Fraction(11, 10)
    assert fill.vwap == Fraction(11, 10)
    assert fill.worst_price == Fraction(11, 10)
    assert fill.consumed_levels == 1
    assert book.snapshot is snapshot
    assert book.snapshot == snapshot
    assert book.mapping is not None
    assert book.mapping.displayed_size_unit == "coin"
    assert book.mapping.reviewed_contract_multiplier == Decimal("1")


def test_fixture_sell_one_sweeps_the_bid() -> None:
    book = _bound(FIXTURE_BOOK)
    fill = sweep_depth(book, Side.SELL, ExactDecimal.parse("1"))
    assert fill.side is Side.SELL
    assert fill.vwap == Fraction(1)
    assert fill.worst_price == Fraction(1)
    assert fill.notional_quote == Fraction(1)
    assert fill.filled_quantity == Fraction(1)
    assert fill.consumed_levels == 1
    assert fill.envelope_index == book.envelope_index
    assert fill.payload_sha256 == book.payload_sha256
    assert fill.epoch_id == book.epoch_id


def test_same_inputs_yield_equal_fills() -> None:
    book = _bound(FIXTURE_BOOK)
    first = sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    second = sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert first == second


def test_fixture_buy_just_over_depth_is_rejected() -> None:
    book = _bound(FIXTURE_BOOK)
    with pytest.raises(DepthRejected) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1.00000001"))
    assert caught.value.code is ShadowRejectCode.DEPTH_INSUFFICIENT
    assert not isinstance(caught.value, ExecutableFill)
    assert not hasattr(caught.value, "vwap")
    assert not hasattr(caught.value, "best_ask")
    assert not hasattr(caught.value, "best_bid")


def test_two_ask_buy_one_and_a_half_uses_partial_last_level() -> None:
    book = _bound(TWO_ASK_BOOK)
    fill = sweep_depth(book, Side.BUY, ExactDecimal.parse("1.5"))
    assert fill.notional_quote == Fraction(17, 10)
    assert fill.vwap == Fraction(17, 15)
    assert fill.worst_price == Fraction(6, 5)
    assert fill.consumed_levels == 2
    assert fill.filled_quantity == Fraction(3, 2)
    assert fill.filled_quantity == fill.requested_quantity


def test_two_ask_buy_three_is_rejected() -> None:
    book = _bound(TWO_ASK_BOOK)
    with pytest.raises(DepthRejected) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("3"))
    assert caught.value.code is ShadowRejectCode.DEPTH_INSUFFICIENT
    assert not isinstance(caught.value, ExecutableFill)
    assert not hasattr(caught.value, "vwap")
    assert not hasattr(caught.value, "best_ask")


def test_unbound_book_is_vwap_error() -> None:
    book = _reconstruct(FIXTURE_BOOK)
    assert book.mapping is None
    assert book.mapping_id is None
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert type(caught.value) is VwapError
    assert not isinstance(caught.value, DepthRejected)
    assert not isinstance(caught.value, IdentityBindError)
    assert not isinstance(caught.value, ExecutableFill)
    assert not hasattr(caught.value, "vwap")
    assert not hasattr(caught.value, "filled_quantity")


def test_bound_lighter_coin_unit_buy_one_matches_hyperliquid_fill() -> None:
    books = reconstruct_books((_envelope(LIGHTER_SNAPSHOT, venue="lighter"),))
    bound = bind_reconstructed_books(
        books,
        (_mapping(mapping_id="map-lighter-1", venue="lighter"),),
    )
    fill = sweep_depth(bound[0], Side.BUY, ExactDecimal.parse("1"))
    assert fill.vwap == Fraction(11, 10)
    assert fill.notional_quote == Fraction(11, 10)
    assert fill.filled_quantity == Fraction(1)
    assert fill.consumed_levels == 1


def test_unbound_lighter_book_is_vwap_error() -> None:
    books = reconstruct_books((_envelope(LIGHTER_SNAPSHOT, venue="lighter"),))
    book = books[0]
    assert book.mapping is None
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert type(caught.value) is VwapError
    assert not isinstance(caught.value, DepthRejected)
    assert not isinstance(caught.value, IdentityBindError)


def test_unbound_over_depth_is_vwap_error_not_depth_rejected() -> None:
    book = _reconstruct(FIXTURE_BOOK)
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1.00000001"))
    assert type(caught.value) is VwapError
    assert not isinstance(caught.value, DepthRejected)
    assert not isinstance(caught.value, IdentityBindError)


@pytest.mark.parametrize("unit", ("COIN", "contract"))
def test_bound_non_coin_unit_is_vwap_error(unit: str) -> None:
    book = _bound(FIXTURE_BOOK, displayed_size_unit=unit)
    assert book.mapping is not None
    assert book.mapping.displayed_size_unit == unit
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert type(caught.value) is VwapError
    assert not isinstance(caught.value, DepthRejected)
    assert not isinstance(caught.value, IdentityBindError)
    assert not hasattr(caught.value, "vwap")
    assert not hasattr(caught.value, "filled_quantity")


def test_bound_multiplier_ten_is_vwap_error() -> None:
    book = _bound(FIXTURE_BOOK, reviewed_contract_multiplier=Decimal("10"))
    assert book.mapping is not None
    assert book.mapping.reviewed_contract_multiplier == Decimal("10")
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert type(caught.value) is VwapError
    assert not isinstance(caught.value, DepthRejected)
    assert not isinstance(caught.value, IdentityBindError)
    assert not hasattr(caught.value, "vwap")
    assert not hasattr(caught.value, "filled_quantity")


def test_extra_scale_multiplier_one_still_sweeps() -> None:
    book = _bound(FIXTURE_BOOK, reviewed_contract_multiplier=Decimal("1.00000000"))
    fill = sweep_depth(book, Side.BUY, ExactDecimal.parse("1"))
    assert fill.vwap == Fraction(11, 10)
    assert fill.filled_quantity == Fraction(1)


@pytest.mark.parametrize(
    "quantity",
    (
        ExactDecimal.parse("0"),
        ExactDecimal.parse("-1"),
        1.0,
        True,
        None,
        "1",
    ),
)
def test_non_positive_or_wrong_type_quantity_is_vwap_error(quantity: object) -> None:
    book = _reconstruct(FIXTURE_BOOK)
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, Side.BUY, quantity)  # type: ignore[arg-type]
    assert not isinstance(caught.value, DepthRejected)


def test_unknown_side_is_vwap_error() -> None:
    book = _reconstruct(FIXTURE_BOOK)
    with pytest.raises(VwapError) as caught:
        sweep_depth(book, "BUY", ExactDecimal.parse("1"))  # type: ignore[arg-type]
    assert not isinstance(caught.value, DepthRejected)


def test_non_book_input_is_vwap_error() -> None:
    with pytest.raises(VwapError) as caught:
        sweep_depth(None, Side.BUY, ExactDecimal.parse("1"))  # type: ignore[arg-type]
    assert not isinstance(caught.value, DepthRejected)


def test_vwap_source_forbids_clock_network_and_truncated_kernel() -> None:
    source = Path(inspect.getfile(sweep_depth)).read_text(encoding="utf-8")
    assert "mee_public_capture" not in source
    assert "httpx" not in source
    assert "import time" not in source
    assert "from time " not in source
    assert "datetime" not in source
    assert "localcontext" not in source
    assert ".mul(" not in source
    assert ".div(" not in source
    assert "IdentityBindError" not in source
    assert "bind_reconstructed_books" not in source
    assert "casefold" not in source
    assert "valid_for" not in source
    assert "VenueMarket" not in source
    assert "from fractions import Fraction" in source
