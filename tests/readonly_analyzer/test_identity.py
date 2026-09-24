"""Fail-closed bind of reconstructed Hyperliquid books to sealed mappings."""

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
from mee_contracts.market import InstrumentIdentity
from mee_contracts.provenance import MappingDecision, MarketMappingEvidence
from mee_readonly_analyzer.identity import IdentityBindError, bind_reconstructed_books
from mee_readonly_analyzer.reconstruction import ReconstructionError, reconstruct_books

RUN = UUID("00000000-0000-0000-0000-000000000001")
FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
)
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


def _reconstruct(payload: bytes = FIXTURE_BOOK, **envelope_kwargs: object):
    books = reconstruct_books((_envelope(payload, **envelope_kwargs),))  # type: ignore[arg-type]
    assert len(books) == 1
    return books


def test_identity_bind_error_is_not_reconstruction_error() -> None:
    assert issubclass(IdentityBindError, ValueError)
    assert not issubclass(IdentityBindError, ReconstructionError)


def test_unique_sample_mapping_binds_btc_book() -> None:
    books = _reconstruct()
    mapping = _mapping()
    bound = bind_reconstructed_books(books, (mapping,))
    assert len(bound) == 1
    book = bound[0]
    assert book.mapping_id == "map-1"
    assert book.mapping is mapping
    assert book.mapping.identity.base_asset == "BTC"
    assert book.mapping.displayed_size_unit == "coin"
    assert book.mapping.reviewed_contract_multiplier == Decimal("1")
    assert book.snapshot is books[0].snapshot
    assert books[0].mapping_id is None
    assert books[0].mapping is None
    assert book.channel is None
    assert books[0].channel is None


def test_reconstruct_leaves_mapping_unbound() -> None:
    book = _reconstruct()[0]
    assert book.mapping_id is None
    assert book.mapping is None


def test_empty_mappings_raise_identity_bind_error() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), ())


def test_rejected_only_mapping_raises() -> None:
    rejected = _mapping(decision=MappingDecision.REJECTED)
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (rejected,))


def test_rejected_plus_approved_binds_approved() -> None:
    rejected = _mapping(mapping_id="map-rej", decision=MappingDecision.REJECTED)
    approved = _mapping()
    bound = bind_reconstructed_books(_reconstruct(), (rejected, approved))
    assert bound[0].mapping_id == "map-1"
    assert bound[0].mapping is approved


def test_two_current_approved_btc_rows_same_identity_raise() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(),
            (_mapping(), _mapping(mapping_id="map-2")),
        )


def test_two_current_approved_btc_rows_different_identity_raise() -> None:
    other = _mapping(
        mapping_id="map-2",
        identity=replace(IDENTITY, payoff_kind="inverse"),
    )
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (_mapping(), other))


def test_valid_from_after_observed_raises() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (_mapping(valid_from_ms=10),))


def test_valid_until_before_observed_raises() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(),
            (_mapping(valid_from_ms=0, valid_until_ms=0),),
        )


def test_valid_until_equal_observed_binds() -> None:
    mapping = _mapping(valid_from_ms=0, valid_until_ms=1)
    bound = bind_reconstructed_books(_reconstruct(), (mapping,))
    assert bound[0].mapping is mapping


def test_lighter_only_mapping_raises() -> None:
    lighter = _mapping(venue="lighter")
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (lighter,))


def test_hyperliquid_and_lighter_btc_binds_hyperliquid() -> None:
    approved = _mapping()
    lighter = _mapping(mapping_id="map-lighter-1", venue="lighter")
    bound = bind_reconstructed_books(_reconstruct(), (approved, lighter))
    assert bound[0].mapping is approved


def test_unique_lighter_mapping_binds_lighter_btc_book() -> None:
    books = _reconstruct(LIGHTER_SNAPSHOT, venue="lighter")
    mapping = _mapping(mapping_id="map-lighter-1", venue="lighter")
    bound = bind_reconstructed_books(books, (mapping,))
    assert bound[0].mapping_id == "map-lighter-1"
    assert bound[0].mapping is mapping
    assert bound[0].snapshot.venue == "LIGHTER"
    assert bound[0].channel == "order_book:1"
    assert books[0].mapping_id is None
    assert books[0].channel == "order_book:1"


def test_hyperliquid_mapping_does_not_bind_lighter_book() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
            (_mapping(),),
        )


def test_lighter_book_with_both_venues_binds_lighter() -> None:
    hyperliquid = _mapping()
    lighter = _mapping(mapping_id="map-lighter-1", venue="lighter")
    bound = bind_reconstructed_books(
        _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
        (hyperliquid, lighter),
    )
    assert bound[0].mapping is lighter


def test_two_current_approved_lighter_btc_rows_same_identity_raise() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
            (
                _mapping(mapping_id="map-lighter-1", venue="lighter"),
                _mapping(mapping_id="map-lighter-2", venue="lighter"),
            ),
        )


def test_two_current_approved_lighter_btc_rows_different_identity_raise() -> None:
    other = _mapping(
        mapping_id="map-lighter-2",
        venue="lighter",
        identity=replace(IDENTITY, payoff_kind="inverse"),
    )
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
            (_mapping(mapping_id="map-lighter-1", venue="lighter"), other),
        )


def test_uppercase_lighter_venue_still_binds() -> None:
    mapping = _mapping(mapping_id="map-lighter-1", venue="LIGHTER")
    bound = bind_reconstructed_books(
        _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
        (mapping,),
    )
    assert bound[0].mapping is mapping


def test_already_bound_lighter_book_raises() -> None:
    bound = bind_reconstructed_books(
        _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
        (_mapping(mapping_id="map-lighter-1", venue="lighter"),),
    )
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            bound,
            (_mapping(mapping_id="map-lighter-1", venue="lighter"),),
        )


def test_extra_eth_mapping_does_not_block_btc_bind() -> None:
    eth = _mapping(
        mapping_id="map-eth",
        symbol="ETH",
        identity=replace(IDENTITY, base_asset="ETH"),
    )
    approved = _mapping()
    bound = bind_reconstructed_books(_reconstruct(), (approved, eth))
    assert bound[0].mapping_id == "map-1"
    assert bound[0].mapping is approved


def test_uppercase_hyperliquid_venue_still_binds() -> None:
    mapping = _mapping(venue="HYPERLIQUID")
    bound = bind_reconstructed_books(_reconstruct(), (mapping,))
    assert bound[0].mapping is mapping


def test_lowercase_symbol_does_not_match_btc() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (_mapping(symbol="btc"),))


def test_bind_once_rejects_already_bound_book() -> None:
    bound = bind_reconstructed_books(_reconstruct(), (_mapping(),))
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(bound, (_mapping(),))


def test_empty_books_return_empty_tuple() -> None:
    assert bind_reconstructed_books((), (_mapping(),)) == ()


def test_non_tuple_books_or_mappings_raise() -> None:
    books = _reconstruct()
    mapping = _mapping()
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(list(books), (mapping,))  # type: ignore[arg-type]
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(books, [mapping])  # type: ignore[arg-type]


def test_non_mapping_element_raises() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(_reconstruct(), (object(),))  # type: ignore[arg-type]


def test_non_book_element_raises() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books((object(),), (_mapping(),))  # type: ignore[arg-type]


def test_adjacent_windows_bind_each_book() -> None:
    books = reconstruct_books(
        (
            _envelope(FIXTURE_BOOK, envelope_index=0, observed_at_ms=1),
            _envelope(FIXTURE_BOOK, envelope_index=1, observed_at_ms=2),
        )
    )
    early = _mapping(mapping_id="map-early", valid_from_ms=0, valid_until_ms=1)
    late = _mapping(mapping_id="map-late", valid_from_ms=2, valid_until_ms=None)
    bound = bind_reconstructed_books(books, (early, late))
    assert bound[0].mapping is early
    assert bound[1].mapping is late


def test_extra_level_key_n_still_binds() -> None:
    payload = (
        b'{"coin":"BTC","time":1,"levels":['
        b'[{"px":"1.0","sz":"1.0","n":1}],'
        b'[{"px":"1.1","sz":"1.0","n":2}]]}'
    )
    bound = bind_reconstructed_books(_reconstruct(payload), (_mapping(),))
    assert bound[0].mapping_id == "map-1"
    assert bound[0].snapshot.symbol == "BTC"


def test_constructor_mapping_and_id_must_agree() -> None:
    book = _reconstruct()[0]
    mapping = _mapping()
    with pytest.raises(ReconstructionError):
        replace(book, mapping_id="map-1")
    with pytest.raises(ReconstructionError):
        replace(book, mapping=mapping)
    with pytest.raises(ReconstructionError):
        replace(book, mapping_id="other", mapping=mapping)


def test_official_snap_binds_unique_indexed_lighter_btc() -> None:
    document = json.loads(LIGHTER_SNAPSHOT)
    del document["symbol"]
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    mapping = _mapping(
        mapping_id="map-lighter-1",
        venue="lighter",
        lighter_market_index=1,
    )
    books = reconstruct_books((_envelope(payload, venue="lighter"),), (mapping,))
    bound = bind_reconstructed_books(books, (mapping,))
    assert bound[0].mapping_id == "map-lighter-1"
    assert bound[0].mapping is mapping
    assert bound[0].snapshot.symbol == "BTC"
    assert bound[0].channel == "order_book:1"
    assert books[0].mapping_id is None
    assert books[0].channel == "order_book:1"


def test_official_snap_and_update_bind_same_mapping() -> None:
    snap_document = json.loads(LIGHTER_SNAPSHOT)
    del snap_document["symbol"]
    snap = json.dumps(snap_document, separators=(",", ":")).encode("ascii")
    update_document = json.loads(LIGHTER_UPDATE)
    del update_document["symbol"]
    update = json.dumps(update_document, separators=(",", ":")).encode("ascii")
    mapping = _mapping(
        mapping_id="map-lighter-1",
        venue="lighter",
        lighter_market_index=1,
    )
    books = reconstruct_books(
        (
            _envelope(snap, venue="lighter", envelope_index=0, observed_at_ms=1),
            _envelope(update, venue="lighter", envelope_index=1, observed_at_ms=2),
        ),
        (mapping,),
    )
    bound = bind_reconstructed_books(books, (mapping,))
    assert bound[0].mapping_id == "map-lighter-1"
    assert bound[1].mapping_id == "map-lighter-1"
    assert bound[1].snapshot.symbol == "BTC"
    assert bound[1].snapshot.sequence == 11
    assert bound[0].channel == "order_book:1"
    assert bound[1].channel == "order_book:1"


def test_official_snap_two_lighter_btc_rows_binds_indexed() -> None:
    document = json.loads(LIGHTER_SNAPSHOT)
    del document["symbol"]
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    indexed = _mapping(
        mapping_id="map-lighter-1",
        venue="lighter",
        lighter_market_index=1,
    )
    other = _mapping(mapping_id="map-lighter-2", venue="lighter")
    books = reconstruct_books((_envelope(payload, venue="lighter"),), (indexed, other))
    assert books[0].snapshot.symbol == "BTC"
    assert books[0].mapping_id is None
    bound = bind_reconstructed_books(books, (indexed, other))
    assert bound[0].mapping is indexed
    assert bound[0].mapping_id == "map-lighter-1"
    assert bound[0].channel == "order_book:1"


def test_two_indexed_lighter_btc_rows_same_index_raise() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
            (
                _mapping(
                    mapping_id="map-lighter-1",
                    venue="lighter",
                    lighter_market_index=1,
                ),
                _mapping(
                    mapping_id="map-lighter-2",
                    venue="lighter",
                    lighter_market_index=1,
                ),
            ),
        )


def test_two_indexed_lighter_btc_rows_different_indexes_binds_channel() -> None:
    indexed_one = _mapping(
        mapping_id="map-lighter-1",
        venue="lighter",
        lighter_market_index=1,
    )
    indexed_two = _mapping(
        mapping_id="map-lighter-2",
        venue="lighter",
        lighter_market_index=2,
    )
    bound = bind_reconstructed_books(
        _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
        (indexed_one, indexed_two),
    )
    assert bound[0].mapping is indexed_one
    assert bound[0].mapping_id == "map-lighter-1"
    assert bound[0].channel == "order_book:1"


def test_stuffed_lighter_btc_wrong_index_raises() -> None:
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(LIGHTER_SNAPSHOT, venue="lighter"),
            (
                _mapping(
                    mapping_id="map-lighter-1",
                    venue="lighter",
                    lighter_market_index=2,
                ),
            ),
        )


def test_stuffed_lighter_eth_does_not_bind_indexed_btc() -> None:
    document = json.loads(LIGHTER_SNAPSHOT)
    document["symbol"] = "ETH"
    payload = json.dumps(document, separators=(",", ":")).encode("ascii")
    with pytest.raises(IdentityBindError):
        bind_reconstructed_books(
            _reconstruct(payload, venue="lighter"),
            (
                _mapping(
                    mapping_id="map-lighter-1",
                    venue="lighter",
                    lighter_market_index=1,
                ),
            ),
        )


def test_hyperliquid_channel_must_be_none() -> None:
    book = _reconstruct()[0]
    assert book.channel is None
    with pytest.raises(ReconstructionError):
        replace(book, channel="order_book:1")


def test_lighter_channel_must_be_order_book_digits() -> None:
    book = _reconstruct(LIGHTER_SNAPSHOT, venue="lighter")[0]
    assert book.channel == "order_book:1"
    with pytest.raises(ReconstructionError):
        replace(book, channel=None)
    with pytest.raises(ReconstructionError):
        replace(book, channel="book:1")
    with pytest.raises(ReconstructionError):
        replace(book, channel="order_book:")
    with pytest.raises(ReconstructionError):
        replace(book, channel="order_book:1a")
    with pytest.raises(ReconstructionError):
        replace(book, channel="Order_book:1")
    mapping = _mapping(mapping_id="map-lighter-1", venue="lighter")
    kept = replace(book, mapping_id="map-lighter-1", mapping=mapping)
    assert kept.channel == "order_book:1"


def test_identity_source_forbids_clock_network_and_valid_for() -> None:
    source = Path(inspect.getfile(bind_reconstructed_books)).read_text(encoding="utf-8")
    assert "mee_public_capture" not in source
    assert "httpx" not in source
    assert "import time" not in source
    assert "from time " not in source
    assert "datetime" not in source
    assert "valid_for" not in source
    assert "VenueMarket" not in source
    assert "sweep_depth" not in source
    assert "FrozenPackageError" not in source
