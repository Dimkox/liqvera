"""Venue dispatch for snapshot reconstruction."""

from __future__ import annotations

import hashlib
from uuid import UUID

import pytest
from mee_contracts.evidence import RawPublicEnvelope
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


def test_claimed_lighter_hyperliquid_bytes_raise() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(FIXTURE_BOOK, venue="lighter"),))


def test_mixed_lighter_garbage_and_hyperliquid_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books(
            (
                _envelope(b"garbage", venue="lighter", envelope_index=0),
                _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
            )
        )


def test_unknown_venue_is_skipped() -> None:
    books = reconstruct_books((_envelope(FIXTURE_BOOK, venue="binance"),))
    assert books == ()


def test_mixed_unknown_and_hyperliquid_admits_the_book() -> None:
    books = reconstruct_books(
        (
            _envelope(b"garbage", venue="binance", envelope_index=0),
            _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.venue == "HYPERLIQUID"
    assert books[0].snapshot.symbol == "BTC"
    assert books[0].envelope_index == 1
    assert books[0].epoch_id == 0


def test_mixed_valid_lighter_and_hyperliquid_admits_both() -> None:
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, venue="lighter", envelope_index=0),
            _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.venue == "LIGHTER"
    assert books[0].snapshot.sequence == 10
    assert books[0].epoch_id == 0
    assert books[0].channel == "order_book:1"
    assert books[1].snapshot.venue == "HYPERLIQUID"
    assert books[1].snapshot.sequence is None
    assert books[1].epoch_id == 1
    assert books[1].channel is None


def test_mixed_lighter_update_and_hyperliquid_admits_hyperliquid() -> None:
    update = (
        b'{"channel":"order_book:1","type":"update/order_book","timestamp":1,'
        b'"symbol":"BTC","order_book":{"nonce":11,"begin_nonce":10,'
        b'"bids":[{"price":"1.0","size":"1.0"}],"asks":[{"price":"1.1","size":"1.0"}]}}'
    )
    books = reconstruct_books(
        (
            _envelope(update, venue="lighter", envelope_index=0),
            _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=1),
        )
    )
    assert len(books) == 1
    assert books[0].snapshot.venue == "HYPERLIQUID"
    assert books[0].snapshot.symbol == "BTC"
    assert books[0].snapshot.sequence is None
    assert books[0].envelope_index == 1
    assert books[0].epoch_id == 0


def test_mixed_lighter_snap_gap_and_hyperliquid_admits_remaining() -> None:
    gap = (
        b'{"channel":"order_book:1","type":"update/order_book","timestamp":2,'
        b'"symbol":"BTC","order_book":{"begin_nonce":12,"nonce":13,'
        b'"bids":[],"asks":[]}}'
    )
    books = reconstruct_books(
        (
            _envelope(LIGHTER_SNAPSHOT, venue="lighter", envelope_index=0),
            _envelope(gap, venue="lighter", envelope_index=1),
            _envelope(FIXTURE_BOOK, venue="hyperliquid", envelope_index=2),
        )
    )
    assert len(books) == 2
    assert books[0].snapshot.venue == "LIGHTER"
    assert books[0].snapshot.sequence == 10
    assert books[0].epoch_id == 0
    assert books[1].snapshot.venue == "HYPERLIQUID"
    assert books[1].snapshot.sequence is None
    assert books[1].epoch_id == 1


def test_claimed_hyperliquid_garbage_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(b'{"type":"update/order_book"}'),))


def test_empty_envelopes_return_empty() -> None:
    assert reconstruct_books(()) == ()


def test_decreasing_envelope_index_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books(
            (
                _envelope(FIXTURE_BOOK, envelope_index=1),
                _envelope(FIXTURE_BOOK, envelope_index=0),
            )
        )
