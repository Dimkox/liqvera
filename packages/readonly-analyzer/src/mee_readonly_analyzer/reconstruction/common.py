"""Reconstruction of claimed Hyperliquid snapshots and Lighter snapshots/updates."""

from __future__ import annotations

from dataclasses import dataclass

from mee_contracts.evidence import RawPublicEnvelope
from mee_contracts.market import OrderBookSnapshot
from mee_contracts.provenance import MarketMappingEvidence

HYPERLIQUID_DECODER_ID = "mee-hyperliquid-l2book-snapshot/v1"
LIGHTER_DECODER_ID = "mee-lighter-subscribed-order-book-snapshot/v1"
_CHANNEL_PREFIX = "order_book:"


class ReconstructionError(ValueError):
    """Claimed venue book cannot be admitted. Mapped to INVALID_RECORD."""


@dataclass(frozen=True, slots=True)
class ReconstructedBook:
    snapshot: OrderBookSnapshot
    envelope_index: int
    payload_sha256: str
    decoder_id: str
    epoch_id: int
    mapping_id: str | None
    mapping: MarketMappingEvidence | None = None
    channel: str | None = None

    def __post_init__(self) -> None:
        if type(self.snapshot) is not OrderBookSnapshot:
            raise ReconstructionError("snapshot must be OrderBookSnapshot")
        if self.snapshot.venue == "HYPERLIQUID":
            if self.snapshot.sequence is not None:
                raise ReconstructionError("Hyperliquid snapshot sequence must be None")
            if self.decoder_id != HYPERLIQUID_DECODER_ID:
                raise ReconstructionError("decoder_id is not the Hyperliquid snapshot decoder")
        elif self.snapshot.venue == "LIGHTER":
            if type(self.snapshot.sequence) is not int:
                raise ReconstructionError("Lighter snapshot sequence must be an integer nonce")
            if self.decoder_id != LIGHTER_DECODER_ID:
                raise ReconstructionError("decoder_id is not the Lighter snapshot decoder")
        else:
            raise ReconstructionError("snapshot venue must be HYPERLIQUID or LIGHTER")
        if type(self.envelope_index) is not int or self.envelope_index < 0:
            raise ReconstructionError("envelope_index must be a nonnegative integer")
        if type(self.epoch_id) is not int or self.epoch_id < 0:
            raise ReconstructionError("epoch_id must be a nonnegative integer")
        _require_sha256(self.payload_sha256)
        if (self.mapping is None) != (self.mapping_id is None):
            raise ReconstructionError("mapping and mapping_id must both be set or both None")
        if self.mapping_id is not None and (
            type(self.mapping_id) is not str or not self.mapping_id
        ):
            raise ReconstructionError("mapping_id must be a nonempty string or None")
        if self.mapping is not None:
            if type(self.mapping) is not MarketMappingEvidence:
                raise ReconstructionError("mapping must be MarketMappingEvidence")
            if self.mapping.mapping_id != self.mapping_id:
                raise ReconstructionError("mapping.mapping_id must equal mapping_id")
        _require_channel(self.snapshot.venue, self.channel)


def reconstruct_books(
    envelopes: tuple[RawPublicEnvelope, ...],
    mappings: tuple[MarketMappingEvidence, ...] = (),
) -> tuple[ReconstructedBook, ...]:
    """Admit Hyperliquid l2Book snapshots and Lighter subscribed/order_book
    snapshots plus contiguous update/order_book applies.

    Skip unknown venues. Claimed Hyperliquid failures and claimed Lighter
    garbage/malformed bytes abort. Typed Lighter nonce gaps close that
    channel's in-memory epoch without aborting the tuple. Official Lighter
    snapshots that omit symbol join a unique sealed lighter_market_index.
    """
    from mee_readonly_analyzer.reconstruction.hyperliquid import decode_hyperliquid_l2book
    from mee_readonly_analyzer.reconstruction.lighter import (
        LighterSnapshot,
        LighterUpdate,
        apply_lighter_update,
        decode_lighter_envelope,
        lighter_ticker_for_channel,
    )

    if type(envelopes) is not tuple:
        raise ReconstructionError("envelopes must be a tuple")
    if type(mappings) is not tuple:
        raise ReconstructionError("mappings must be a tuple")
    for mapping in mappings:
        if type(mapping) is not MarketMappingEvidence:
            raise ReconstructionError("mapping must be MarketMappingEvidence")
    books: list[ReconstructedBook] = []
    previous_index: int | None = None
    next_epoch = 0
    lighter_epochs: dict[str, OrderBookSnapshot] = {}
    for envelope in envelopes:
        if type(envelope) is not RawPublicEnvelope:
            raise ReconstructionError("envelope must be RawPublicEnvelope")
        if previous_index is not None and envelope.envelope_index <= previous_index:
            raise ReconstructionError("envelope_index must be strictly increasing")
        previous_index = envelope.envelope_index
        venue = envelope.venue.casefold()
        if venue == "hyperliquid":
            snapshot = decode_hyperliquid_l2book(
                envelope.payload,
                observed_at_ms=envelope.observed_at_ms,
            )
            decoder_id = HYPERLIQUID_DECODER_ID
            channel = None
        elif venue == "lighter":
            decoded = decode_lighter_envelope(
                envelope.payload,
                observed_at_ms=envelope.observed_at_ms,
            )
            if type(decoded) is LighterSnapshot:
                symbol = decoded.symbol
                if symbol is None:
                    symbol = lighter_ticker_for_channel(
                        decoded.channel,
                        mappings,
                        envelope.observed_at_ms,
                    )
                try:
                    snapshot = OrderBookSnapshot(
                        venue="LIGHTER",
                        symbol=symbol,
                        sequence=decoded.nonce,
                        exchange_timestamp_ms=decoded.timestamp,
                        received_timestamp_ms=envelope.observed_at_ms,
                        bids=decoded.bids,
                        asks=decoded.asks,
                    )
                except (TypeError, ValueError) as error:
                    raise ReconstructionError(
                        "claimed Lighter snapshot is not an admitted book"
                    ) from error
                decoder_id = LIGHTER_DECODER_ID
                lighter_epochs[decoded.channel] = snapshot
                channel = decoded.channel
            elif type(decoded) is LighterUpdate:
                previous = lighter_epochs.get(decoded.channel)
                if previous is None:
                    continue
                if (
                    (decoded.symbol is not None and decoded.symbol != previous.symbol)
                    or decoded.begin_nonce != previous.sequence
                    or decoded.nonce <= decoded.begin_nonce
                ):
                    lighter_epochs.pop(decoded.channel, None)
                    continue
                try:
                    snapshot = apply_lighter_update(
                        previous,
                        decoded,
                        observed_at_ms=envelope.observed_at_ms,
                    )
                except ReconstructionError:
                    raise
                except ValueError:
                    lighter_epochs.pop(decoded.channel, None)
                    continue
                decoder_id = LIGHTER_DECODER_ID
                lighter_epochs[decoded.channel] = snapshot
                channel = decoded.channel
            else:
                raise ReconstructionError("claimed Lighter envelope is not an admitted book")
        else:
            continue
        books.append(
            ReconstructedBook(
                snapshot=snapshot,
                envelope_index=envelope.envelope_index,
                payload_sha256=envelope.payload_sha256,
                decoder_id=decoder_id,
                epoch_id=next_epoch,
                mapping_id=None,
                mapping=None,
                channel=channel,
            )
        )
        next_epoch += 1
    return tuple(books)


def _require_channel(venue: str, channel: object) -> None:
    if venue == "HYPERLIQUID":
        if channel is not None:
            raise ReconstructionError("Hyperliquid reconstructed book channel must be None")
        return
    if type(channel) is not str or not channel.startswith(_CHANNEL_PREFIX):
        raise ReconstructionError("Lighter reconstructed book channel must start with order_book:")
    suffix = channel[len(_CHANNEL_PREFIX) :]
    if not suffix.isdigit() or type(int(suffix)) is not int:
        raise ReconstructionError("Lighter reconstructed book channel market index must be digits")


def _require_sha256(value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ReconstructionError("payload_sha256 must be lowercase hexadecimal")
