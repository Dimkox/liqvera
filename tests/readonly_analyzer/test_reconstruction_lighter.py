"""Lighter subscribed/order_book reconstruction is fail-closed."""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from mee_contracts.evidence import RawPublicEnvelope
from mee_contracts.market import BookLevel, InstrumentIdentity
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence
from mee_readonly_analyzer.reconstruction import ReconstructionError, reconstruct_books

RUN = UUID("00000000-0000-0000-0000-000000000001")
LIGHTER_SNAPSHOT = (
    b'{"channel":"order_book:1","type":"subscribed/order_book","timestamp":1,'
    b'"symbol":"BTC","order_book":{"nonce":10,"bids":[{"price":"1.0","size":"1.0"}],'
    b'"asks":[{"price":"1.1","size":"1.0"}]}}'
)
LIGHTER_UPDATE = (
    b'{"channel":"order_book:1","type":"update/order_book","timestamp":2,'
    b'"symbol":"BTC","order_book":{"begin_nonce":10,"nonce":11,'
    b'"bids":[{"price":"1.0","size":"2.0"}],"asks":[]}}'
)
FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
)
LIGHTER_DECODER_ID = "mee-lighter-subscribed-order-book-snapshot/v1"
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
    venue: str = "lighter",
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


def _snapshot_bytes(**overrides: object) -> bytes:
    document = json.loads(LIGHTER_SNAPSHOT)
    document.update(overrides)
    return json.dumps(document, separators=(",", ":")).encode("ascii")


def _book_bytes(**overrides: object) -> bytes:
    document = json.loads(LIGHTER_SNAPSHOT)
    book = dict(document["order_book"])
    book.update(overrides)
    document["order_book"] = book
    return json.dumps(document, separators=(",", ":")).encode("ascii")


def _omit_symbol(payload: bytes) -> bytes:
    document = json.loads(payload)
    document.pop("symbol", None)
    return json.dumps(document, separators=(",", ":")).encode("ascii")


def _lighter_mapping(**overrides: object) -> MarketMappingEvidence:
    values: dict[str, object] = {
        "mapping_id": "map-lighter-1",
        "mapping_version": "v1",
        "decision": MappingDecision.APPROVED,
        "venue": "lighter",
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
        "lighter_market_index": 1,
    }
    values.update(overrides)
    return MarketMappingEvidence(**values)  # type: ignore[arg-type]


def _update_bytes(**overrides: object) -> bytes:
    document = json.loads(LIGHTER_UPDATE)
    book = dict(document["order_book"])
    for key in ("begin_nonce", "nonce", "bids", "asks"):
        if key in overrides:
            book[key] = overrides.pop(key)
    document.update(overrides)
    document["order_book"] = book
    return json.dumps(document, separators=(",", ":")).encode("ascii")


def test_subscribed_order_book_reconstructs_uncrossed_btc_snapshot() -> None:
    books = reconstruct_books((_envelope(LIGHTER_SNAPSHOT, observed_at_ms=99),))
    assert len(books) == 1
    book = books[0]
    snapshot = book.snapshot
    assert snapshot.venue == "LIGHTER"
    assert snapshot.symbol == "BTC"
    assert snapshot.sequence == 10
    assert type(snapshot.sequence) is int
    assert snapshot.exchange_timestamp_ms == 1
    assert snapshot.received_timestamp_ms == 99
    assert snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("1.0")),)
    assert snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("1.0")),)
    assert snapshot.best_bid.price < snapshot.best_ask.price
    assert book.envelope_index == 0
    assert book.payload_sha256 == hashlib.sha256(LIGHTER_SNAPSHOT).hexdigest()
    assert book.decoder_id == LIGHTER_DECODER_ID
    assert book.epoch_id == 0
    assert book.mapping_id is None
    assert book.mapping is None
    assert book.channel == "order_book:1"


def test_extra_keys_offset_begin_nonce_last_updated_at_still_reconstruct() -> None:
    payload = _book_bytes(offset=3, begin_nonce=9, last_updated_at=1_000)
    document = json.loads(payload)
    document["code"] = 0
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    books = reconstruct_books((_envelope(payload),))
    assert len(books) == 1
    snapshot = books[0].snapshot
    assert snapshot.venue == "LIGHTER"
    assert snapshot.sequence == 10
    assert snapshot.symbol == "BTC"


def test_lone_typed_update_reconstructs_empty() -> None:
    assert reconstruct_books((_envelope(LIGHTER_UPDATE),)) == ()


def test_missing_symbol_raises() -> None:
    document = json.loads(LIGHTER_SNAPSHOT)
    del document["symbol"]
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_missing_nonce_raises() -> None:
    document = json.loads(LIGHTER_SNAPSHOT)
    del document["order_book"]["nonce"]
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_bool_nonce_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_book_bytes(nonce=True)),))


def test_json_number_price_raises() -> None:
    payload = _book_bytes(bids=[{"price": 1.0, "size": "1.0"}])
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_hyperliquid_fixture_bytes_under_lighter_venue_raise() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(FIXTURE_BOOK),))


def test_size_zero_raises() -> None:
    payload = _book_bytes(bids=[{"price": "1.0", "size": "0"}])
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_unsorted_bids_raise() -> None:
    payload = _book_bytes(bids=[{"price": "0.9", "size": "1.0"}, {"price": "1.0", "size": "1.0"}])
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_crossed_book_raises() -> None:
    payload = _book_bytes(
        bids=[{"price": "1.1", "size": "1.0"}],
        asks=[{"price": "1.0", "size": "1.0"}],
    )
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_empty_asks_raise() -> None:
    payload = _book_bytes(asks=[])
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_two_snapshots_non_contiguous_nonces_admit_independently() -> None:
    first = _book_bytes(nonce=10)
    second = _book_bytes(nonce=12)
    books = reconstruct_books(
        (
            _envelope(first, envelope_index=0),
            _envelope(second, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.sequence == 10
    assert books[1].snapshot.sequence == 12
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1


def test_two_snapshots_nonce_regression_still_admit() -> None:
    first = _book_bytes(nonce=12)
    second = _book_bytes(nonce=10)
    books = reconstruct_books(
        (
            _envelope(first, envelope_index=0),
            _envelope(second, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.sequence == 12
    assert books[1].snapshot.sequence == 10
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1


def test_received_timestamp_is_envelope_observed_at() -> None:
    books = reconstruct_books((_envelope(LIGHTER_SNAPSHOT, observed_at_ms=7),))
    assert books[0].snapshot.received_timestamp_ms == 7
    assert books[0].snapshot.exchange_timestamp_ms == 1


def test_hyperliquid_decoder_id_on_lighter_snapshot_raises() -> None:
    book = reconstruct_books((_envelope(LIGHTER_SNAPSHOT),))[0]
    with pytest.raises(ReconstructionError):
        replace(book, decoder_id="mee-hyperliquid-l2book-snapshot/v1")


def test_none_sequence_on_lighter_snapshot_raises() -> None:
    book = reconstruct_books((_envelope(LIGHTER_SNAPSHOT),))[0]
    with pytest.raises(ReconstructionError):
        replace(book, snapshot=replace(book.snapshot, sequence=None))


def test_contiguous_update_replaces_bid_size() -> None:
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0, observed_at_ms=7),
            _envelope(LIGHTER_UPDATE, envelope_index=1, observed_at_ms=9),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.sequence == 10
    assert books[1].snapshot.sequence == 11
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1
    assert books[1].envelope_index == 1
    assert books[1].decoder_id == LIGHTER_DECODER_ID
    assert books[1].mapping_id is None
    assert books[1].mapping is None
    assert books[0].channel == "order_book:1"
    assert books[1].channel == "order_book:1"
    assert books[1].snapshot.venue == "LIGHTER"
    assert books[1].snapshot.symbol == "BTC"
    assert books[1].snapshot.exchange_timestamp_ms == 2
    assert books[1].snapshot.received_timestamp_ms == 9
    assert books[1].snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("2.0")),)
    assert books[1].snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("1.0")),)


def test_contiguous_update_integer_skip_applies() -> None:
    update = _update_bytes(begin_nonce=10, nonce=12)
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 12


def test_contiguous_update_replaces_ask_size() -> None:
    update = _update_bytes(bids=[], asks=[{"price": "1.1", "size": "2.0"}])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 11
    assert books[1].snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("1.0")),)
    assert books[1].snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("2.0")),)


def test_contiguous_update_appends_worse_ask() -> None:
    update = _update_bytes(bids=[], asks=[{"price": "1.2", "size": "1.0"}])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.asks == (
        BookLevel(Decimal("1.1"), Decimal("1.0")),
        BookLevel(Decimal("1.2"), Decimal("1.0")),
    )


def test_size_zero_delete_on_update_keeps_two_sided_book() -> None:
    snapshot = _book_bytes(
        bids=[{"price": "1.0", "size": "1.0"}, {"price": "0.9", "size": "1.0"}],
    )
    update = _update_bytes(bids=[{"price": "0.9", "size": "0"}], asks=[])
    books = reconstruct_books(
        (
            _envelope(snapshot, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 11
    assert books[1].snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("1.0")),)
    assert books[1].snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("1.0")),)


def test_size_zero_delete_emptying_side_closes_without_raise() -> None:
    update = _update_bytes(bids=[{"price": "1.0", "size": "0"}], asks=[])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_size_zero_missing_price_is_noop_and_advances_nonce() -> None:
    update = _update_bytes(bids=[{"price": "0.5", "size": "0"}], asks=[])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 11
    assert books[1].snapshot.bids == books[0].snapshot.bids
    assert books[1].snapshot.asks == books[0].snapshot.asks


def test_empty_delta_arrays_advance_nonce() -> None:
    update = _update_bytes(bids=[], asks=[])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 11
    assert books[1].snapshot.bids == books[0].snapshot.bids
    assert books[1].snapshot.asks == books[0].snapshot.asks


def test_duplicate_prices_in_one_update_last_wins() -> None:
    update = _update_bytes(
        bids=[{"price": "1.0", "size": "2.0"}, {"price": "1.0", "size": "3.0"}],
        asks=[],
    )
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("3.0")),)


def test_append_unsorting_best_bid_closes_without_raise() -> None:
    update = _update_bytes(bids=[{"price": "1.05", "size": "1.0"}], asks=[])
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_gap_begin_nonce_mismatch_is_ignored() -> None:
    update = _update_bytes(begin_nonce=12, nonce=13)
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_nonce_not_greater_than_begin_nonce_is_ignored() -> None:
    update = _update_bytes(begin_nonce=10, nonce=10)
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_gap_then_new_snapshot_admits() -> None:
    gap = _update_bytes(begin_nonce=12, nonce=13)
    second = _book_bytes(nonce=20)
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(gap, envelope_index=1),
            _envelope(second, envelope_index=2),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.sequence == 10
    assert books[1].snapshot.sequence == 20
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1


def test_gap_then_later_update_is_ignored() -> None:
    gap = _update_bytes(begin_nonce=12, nonce=13)
    later = _update_bytes(begin_nonce=10, nonce=11)
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(gap, envelope_index=1),
            _envelope(later, envelope_index=2),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_two_symbols_apply_only_matching_update() -> None:
    eth_document = json.loads(LIGHTER_SNAPSHOT)
    eth_document["symbol"] = "ETH"
    eth_document["channel"] = "order_book:2"
    eth = json.dumps(eth_document, separators=(",", ":")).encode("ascii")
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(eth, envelope_index=1),
            _envelope(LIGHTER_UPDATE, envelope_index=2),
        )
    )
    assert len(books) == 3
    assert books[0].snapshot.symbol == "BTC"
    assert books[1].snapshot.symbol == "ETH"
    assert books[2].snapshot.symbol == "BTC"
    assert books[2].snapshot.sequence == 11
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1
    assert books[2].epoch_id == 2


def test_channel_mismatch_closes_without_raise() -> None:
    update = _update_bytes(channel="order_book:2")
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_extra_keys_on_contiguous_update_still_apply() -> None:
    document = json.loads(LIGHTER_UPDATE)
    document["code"] = 0
    document["order_book"]["offset"] = 3
    document["order_book"]["last_updated_at"] = 1_000
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(payload, envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.sequence == 11


def test_malformed_update_missing_begin_nonce_raises() -> None:
    document = json.loads(LIGHTER_UPDATE)
    del document["order_book"]["begin_nonce"]
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_malformed_update_bool_nonce_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_update_bytes(nonce=True)),))


def test_malformed_update_json_number_size_raises() -> None:
    payload = _update_bytes(bids=[{"price": "1.0", "size": 2.0}], asks=[])
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_official_snapshot_joins_unique_indexed_mapping() -> None:
    mapping = _lighter_mapping()
    books = reconstruct_books(
        (_envelope(_omit_symbol(LIGHTER_SNAPSHOT), observed_at_ms=99),),
        (mapping,),
    )
    assert len(books) == 1
    snapshot = books[0].snapshot
    assert snapshot.venue == "LIGHTER"
    assert snapshot.symbol == "BTC"
    assert snapshot.sequence == 10
    assert snapshot.exchange_timestamp_ms == 1
    assert snapshot.received_timestamp_ms == 99
    assert snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("1.0")),)
    assert snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("1.0")),)
    assert books[0].decoder_id == LIGHTER_DECODER_ID
    assert books[0].epoch_id == 0
    assert books[0].mapping_id is None
    assert books[0].mapping is None
    assert books[0].channel == "order_book:1"


def test_official_update_inherits_channel_ticker() -> None:
    mapping = _lighter_mapping()
    books = reconstruct_books(
        (
            _envelope(_omit_symbol(LIGHTER_SNAPSHOT), envelope_index=0, observed_at_ms=7),
            _envelope(_omit_symbol(LIGHTER_UPDATE), envelope_index=1, observed_at_ms=9),
        ),
        (mapping,),
    )
    assert len(books) == 2
    assert books[0].snapshot.symbol == "BTC"
    assert books[1].snapshot.symbol == "BTC"
    assert books[0].snapshot.sequence == 10
    assert books[1].snapshot.sequence == 11
    assert books[0].epoch_id == 0
    assert books[1].epoch_id == 1
    assert books[1].snapshot.received_timestamp_ms == 9
    assert books[1].mapping_id is None
    assert books[1].mapping is None
    assert books[0].channel == "order_book:1"
    assert books[1].channel == "order_book:1"
    assert books[1].snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("2.0")),)


def test_official_snapshot_without_mappings_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),))


def test_official_snapshot_with_only_hyperliquid_mapping_raises() -> None:
    hyperliquid = _lighter_mapping(
        mapping_id="map-1",
        venue="hyperliquid",
        lighter_market_index=None,
    )
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),), (hyperliquid,))


def test_two_indexed_mappings_same_index_raise() -> None:
    first = _lighter_mapping(mapping_id="map-lighter-1", lighter_market_index=1)
    second = _lighter_mapping(mapping_id="map-lighter-2", lighter_market_index=1)
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),), (first, second))


def test_two_unindexed_lighter_mappings_raise() -> None:
    first = _lighter_mapping(mapping_id="map-lighter-1", lighter_market_index=None)
    second = _lighter_mapping(mapping_id="map-lighter-2", lighter_market_index=None)
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),), (first, second))


def test_sole_unindexed_lighter_mapping_is_not_guessed() -> None:
    mapping = _lighter_mapping(lighter_market_index=None)
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),), (mapping,))


def test_indexed_row_wins_over_unindexed_sibling() -> None:
    indexed = _lighter_mapping(mapping_id="map-lighter-1", lighter_market_index=1)
    unindexed = _lighter_mapping(mapping_id="map-lighter-2", lighter_market_index=None)
    books = reconstruct_books(
        (_envelope(_omit_symbol(LIGHTER_SNAPSHOT)),),
        (indexed, unindexed),
    )
    assert len(books) == 1
    assert books[0].snapshot.symbol == "BTC"
    assert books[0].mapping_id is None
    assert books[0].channel == "order_book:1"


def test_indexed_mapping_outside_window_raises() -> None:
    mapping = _lighter_mapping(lighter_market_index=1, valid_from_ms=10)
    with pytest.raises(ReconstructionError):
        reconstruct_books(
            (_envelope(_omit_symbol(LIGHTER_SNAPSHOT), observed_at_ms=1),),
            (mapping,),
        )


def test_lone_official_update_reconstructs_empty() -> None:
    assert reconstruct_books((_envelope(_omit_symbol(LIGHTER_UPDATE)),)) == ()


def test_official_update_inherits_stuffed_snapshot_ticker() -> None:
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(_omit_symbol(LIGHTER_UPDATE), envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[1].snapshot.symbol == "BTC"
    assert books[1].snapshot.sequence == 11


def test_channel_mismatch_does_not_close_other_channel() -> None:
    mismatch = _update_bytes(channel="order_book:2")
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(mismatch, envelope_index=1),
            _envelope(LIGHTER_UPDATE, envelope_index=2),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.sequence == 10
    assert books[1].snapshot.sequence == 11
    assert books[1].snapshot.symbol == "BTC"


def test_stuffed_symbol_wins_over_indexed_mapping() -> None:
    payload = _snapshot_bytes(symbol="ETH")
    mapping = _lighter_mapping(lighter_market_index=1, symbol="BTC")
    books = reconstruct_books((_envelope(payload),), (mapping,))
    assert len(books) == 1
    assert books[0].snapshot.symbol == "ETH"
    assert books[0].mapping_id is None


def test_stuffed_ticker_mismatch_on_same_channel_closes() -> None:
    update = _update_bytes(symbol="ETH")
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, envelope_index=0),
            _envelope(update, envelope_index=1),
            _envelope(LIGHTER_UPDATE, envelope_index=2),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.sequence == 10


def test_null_symbol_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_snapshot_bytes(symbol=None)),), (_lighter_mapping(),))


def test_empty_symbol_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(_snapshot_bytes(symbol="")),), (_lighter_mapping(),))


def test_mixed_official_lighter_and_hyperliquid_admits_both() -> None:
    mapping = _lighter_mapping()
    books = reconstruct_books(
        (
            _envelope(_omit_symbol(LIGHTER_SNAPSHOT), envelope_index=0),
            _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
        ),
        (mapping,),
    )
    assert len(books) == 2
    assert books[0].snapshot.venue == "LIGHTER"
    assert books[0].snapshot.symbol == "BTC"
    assert books[1].snapshot.venue == "HYPERLIQUID"
    assert books[1].snapshot.symbol == "BTC"


def test_mixed_official_lighter_without_mapping_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books(
            (
                _envelope(_omit_symbol(LIGHTER_SNAPSHOT), envelope_index=0),
                _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
            )
        )


def test_non_tuple_mappings_raise() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(LIGHTER_SNAPSHOT),), [])  # type: ignore[arg-type]


def test_lighter_source_forbids_clock_network_and_capture() -> None:
    from mee_readonly_analyzer.reconstruction import lighter

    source = Path(inspect.getfile(lighter)).read_text(encoding="utf-8")
    assert "mee_public_capture" not in source
    assert "LighterBookReducer" not in source
    assert "httpx" not in source
    assert "import time" not in source
    assert "from time " not in source
    assert "datetime" not in source
    assert "sorted(" not in source
