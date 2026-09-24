"""Hyperliquid REST l2Book reconstruction is fail-closed."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from uuid import UUID

import pytest
from mee_contracts.evidence import RawPublicEnvelope
from mee_contracts.market import BookLevel
from mee_readonly_analyzer.reconstruction import ReconstructionError, reconstruct_books

RUN = UUID("00000000-0000-0000-0000-000000000001")
FIXTURE_BOOK = (
    b'{"coin":"BTC","time":1,"levels":[[{"px":"1.0","sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
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


def test_fixture_book_reconstructs_uncrossed_btc_snapshot() -> None:
    books = reconstruct_books((_envelope(FIXTURE_BOOK),))
    assert len(books) == 1
    book = books[0]
    snapshot = book.snapshot
    assert snapshot.venue == "HYPERLIQUID"
    assert snapshot.symbol == "BTC"
    assert snapshot.sequence is None
    assert snapshot.exchange_timestamp_ms == 1
    assert snapshot.received_timestamp_ms == 1
    assert snapshot.bids == (BookLevel(Decimal("1.0"), Decimal("1.0")),)
    assert snapshot.asks == (BookLevel(Decimal("1.1"), Decimal("1.0")),)
    assert snapshot.best_bid.price < snapshot.best_ask.price
    assert book.envelope_index == 0
    assert book.payload_sha256 == hashlib.sha256(FIXTURE_BOOK).hexdigest()
    assert book.decoder_id == "mee-hyperliquid-l2book-snapshot/v1"
    assert book.epoch_id == 0
    assert book.mapping_id is None
    assert book.mapping is None
    assert book.channel is None


def test_non_json_payload_raises() -> None:
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(b"hi"),))


def test_json_number_px_raises() -> None:
    payload = (
        b'{"coin":"BTC","time":1,"levels":[[{"px":1.0,"sz":"1.0"}],[{"px":"1.1","sz":"1.0"}]]}'
    )
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_crossed_book_raises() -> None:
    payload = (
        b'{"coin":"BTC","time":1,"levels":[[{"px":"1.1","sz":"1.0"}],[{"px":"1.0","sz":"1.0"}]]}'
    )
    with pytest.raises(ReconstructionError):
        reconstruct_books((_envelope(payload),))


def test_extra_level_key_n_still_reconstructs() -> None:
    payload = (
        b'{"coin":"BTC","time":1,"levels":['
        b'[{"px":"1.0","sz":"1.0","n":1}],'
        b'[{"px":"1.1","sz":"1.0","n":2}]]}'
    )
    books = reconstruct_books((_envelope(payload),))
    assert len(books) == 1
    snapshot = books[0].snapshot
    assert snapshot.symbol == "BTC"
    assert snapshot.sequence is None
    assert snapshot.bids[0].price == Decimal("1.0")
    assert snapshot.asks[0].price == Decimal("1.1")
