"""Capture-evidence reader protocol and immutable record types."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID

from mee_contracts.provenance import MarketMappingEvidence


def _require_sha256(value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("evidence SHA-256 must be lowercase hexadecimal")


def _require_timestamp(value: object) -> None:
    if type(value) is not int or value < 0:
        raise TypeError("timestamp must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class CaptureManifest:
    """Immutable capture-run identity returned by an evidence reader."""

    capture_run_id: UUID
    started_at_ms: int
    venue_set: tuple[str, ...]
    schema_version: str

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        _require_timestamp(self.started_at_ms)
        if type(self.venue_set) is not tuple or not self.venue_set:
            raise ValueError("venue_set must be a nonempty tuple")
        if type(self.schema_version) is not str or not self.schema_version:
            raise ValueError("schema_version is required")


@dataclass(frozen=True, slots=True)
class CaptureTerminal:
    """Sealed-run summary. Does not compute a seal hash."""

    capture_run_id: UUID
    terminated_at_ms: int
    status: str

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        _require_timestamp(self.terminated_at_ms)
        if type(self.status) is not str or not self.status:
            raise ValueError("status is required")


@dataclass(frozen=True, slots=True)
class ControlEvidenceRecord:
    """One control or continuity evidence value."""

    capture_run_id: UUID
    recorded_at_ms: int
    kind: str
    payload_sha256: str

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        _require_timestamp(self.recorded_at_ms)
        if type(self.kind) is not str or not self.kind:
            raise ValueError("kind is required")
        _require_sha256(self.payload_sha256)


@dataclass(frozen=True, slots=True)
class RawBatchRecord:
    """Stored compressed batch bytes plus both stored hashes. Does not decode."""

    capture_run_id: UUID
    batch_index: int
    stored_sha256: str
    content_sha256: str
    payload: bytes

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        if type(self.batch_index) is not int or self.batch_index < 0:
            raise ValueError("batch_index must be a nonnegative integer")
        _require_sha256(self.stored_sha256)
        _require_sha256(self.content_sha256)
        if type(self.payload) is not bytes:
            raise TypeError("payload must be bytes")


@dataclass(frozen=True, slots=True)
class RawPublicEnvelope:
    """One raw public wire envelope identity. Not a reconstructed book."""

    capture_run_id: UUID
    envelope_index: int
    observed_at_ms: int
    venue: str
    payload_sha256: str
    payload: bytes

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        if type(self.envelope_index) is not int or self.envelope_index < 0:
            raise ValueError("envelope_index must be a nonnegative integer")
        _require_timestamp(self.observed_at_ms)
        if type(self.venue) is not str or not self.venue:
            raise ValueError("venue is required")
        _require_sha256(self.payload_sha256)
        if type(self.payload) is not bytes:
            raise TypeError("payload must be bytes")


@dataclass(frozen=True, slots=True)
class QualityMinuteRecord:
    """Minute-level quality record. Not soak or aggregation logic."""

    capture_run_id: UUID
    minute_start_ms: int
    venue: str
    accepted: int
    rejected: int

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        _require_timestamp(self.minute_start_ms)
        if type(self.venue) is not str or not self.venue:
            raise ValueError("venue is required")
        if type(self.accepted) is not int or self.accepted < 0:
            raise ValueError("accepted must be a nonnegative integer")
        if type(self.rejected) is not int or self.rejected < 0:
            raise ValueError("rejected must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class MappingSnapshot:
    """Frozen reviewed-mapping snapshot returned by an evidence reader."""

    capture_run_id: UUID
    mappings: tuple[MarketMappingEvidence, ...]
    snapshot_sha256: str

    def __post_init__(self) -> None:
        if type(self.capture_run_id) is not UUID:
            raise TypeError("capture_run_id must be UUID")
        if type(self.mappings) is not tuple:
            raise TypeError("mappings must be a tuple")
        if any(type(item) is not MarketMappingEvidence for item in self.mappings):
            raise TypeError("mappings must contain MarketMappingEvidence")
        _require_sha256(self.snapshot_sha256)


@runtime_checkable
class EvidenceReader(Protocol):
    """Sole capture-evidence reader. Fee and strategy config are not methods."""

    def read_capture_manifest(self, capture_run_id: UUID) -> CaptureManifest: ...

    def capture_terminal(self, capture_run_id: UUID) -> CaptureTerminal: ...

    def iter_control_evidence(
        self, capture_run_id: UUID
    ) -> Iterator[ControlEvidenceRecord]: ...

    def iter_raw_batches(self, capture_run_id: UUID) -> Iterator[RawBatchRecord]: ...

    def iter_raw_envelopes(
        self, capture_run_id: UUID
    ) -> Iterator[RawPublicEnvelope]: ...

    def iter_quality_minutes(
        self, capture_run_id: UUID
    ) -> Iterator[QualityMinuteRecord]: ...

    def read_mapping_snapshot(self, capture_run_id: UUID) -> MappingSnapshot: ...
