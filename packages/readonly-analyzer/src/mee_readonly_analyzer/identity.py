"""Fail-closed bind of reconstructed books to sealed mappings."""

from __future__ import annotations

from dataclasses import replace

from mee_contracts.provenance import MappingDecision, MarketMappingEvidence

from mee_readonly_analyzer.reconstruction import ReconstructedBook

_CHANNEL_PREFIX = "order_book:"


class IdentityBindError(ValueError):
    """Claimed book has no unique current approved mapping for its snapshot venue.
    Mapped to INVALID_RECORD."""


def bind_reconstructed_books(
    books: tuple[ReconstructedBook, ...],
    mappings: tuple[MarketMappingEvidence, ...],
) -> tuple[ReconstructedBook, ...]:
    """Attach the unique current approved mapping for each book's snapshot venue."""
    if type(books) is not tuple:
        raise IdentityBindError("books must be a tuple")
    if type(mappings) is not tuple:
        raise IdentityBindError("mappings must be a tuple")
    for mapping in mappings:
        if type(mapping) is not MarketMappingEvidence:
            raise IdentityBindError("mapping must be MarketMappingEvidence")
    if books == ():
        return ()
    bound: list[ReconstructedBook] = []
    for book in books:
        if type(book) is not ReconstructedBook:
            raise IdentityBindError("book must be ReconstructedBook")
        if book.mapping_id is not None or book.mapping is not None:
            raise IdentityBindError("book is already bound")
        if book.snapshot.venue.casefold() == "lighter":
            candidates = _lighter_candidates(mappings, book)
        else:
            candidates = [mapping for mapping in mappings if _is_candidate(mapping, book)]
        if len(candidates) != 1:
            raise IdentityBindError(
                "claimed book has no unique current approved mapping for its snapshot venue"
            )
        chosen = candidates[0]
        bound.append(replace(book, mapping_id=chosen.mapping_id, mapping=chosen))
    return tuple(bound)


def _is_candidate(mapping: MarketMappingEvidence, book: ReconstructedBook) -> bool:
    if mapping.decision is not MappingDecision.APPROVED:
        return False
    if mapping.venue.casefold() != book.snapshot.venue.casefold():
        return False
    if mapping.symbol != book.snapshot.symbol:
        return False
    evaluated_at_ms = book.snapshot.received_timestamp_ms
    if evaluated_at_ms < mapping.valid_from_ms:
        return False
    if mapping.valid_until_ms is not None and evaluated_at_ms > mapping.valid_until_ms:
        return False
    return True


def _lighter_candidates(
    mappings: tuple[MarketMappingEvidence, ...],
    book: ReconstructedBook,
) -> list[MarketMappingEvidence]:
    channel = book.channel
    if type(channel) is not str:
        raise IdentityBindError("Lighter book channel is missing")
    if not channel.startswith(_CHANNEL_PREFIX):
        raise IdentityBindError("Lighter book channel must start with order_book:")
    suffix = channel[len(_CHANNEL_PREFIX) :]
    if not suffix.isdigit():
        raise IdentityBindError("Lighter book channel market index must be digits")
    index = int(suffix)
    indexed = [
        mapping
        for mapping in mappings
        if _is_candidate(mapping, book) and mapping.lighter_market_index == index
    ]
    if indexed:
        return indexed
    return [
        mapping
        for mapping in mappings
        if _is_candidate(mapping, book) and mapping.lighter_market_index is None
    ]
