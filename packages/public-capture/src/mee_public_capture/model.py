"""Immutable, credential-free input models at the A2 capture boundary."""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

CAPTURE_BOUNDARY_PROFILE = "websocket-application-message-post-decompression/v1"
ENVELOPE_SCHEMA = "mee-a2-envelope/v1"
NDJSON_SCHEMA = "mee-a2-ndjson/v1"
COMPRESSION_PROFILE = "gzip-raw-deflate-6-mtime0-os255/v1"
WARMUP_MINUTES = 60
MEASURED_SECONDS = 5 * 24 * 60 * 60
MEASURED_WINDOW_NS = MEASURED_SECONDS * 1_000_000_000


class Venue(StrEnum):
    HYPERLIQUID = "HYPERLIQUID"
    LIGHTER = "LIGHTER"


class WebSocketMessageType(StrEnum):
    TEXT = "TEXT"
    BINARY = "BINARY"


class MessageClass(StrEnum):
    CONTROL = "CONTROL"
    SNAPSHOT = "SNAPSHOT"
    DELTA = "DELTA"
    TRADE = "TRADE"
    MARKET_STATS = "MARKET_STATS"
    FUNDING = "FUNDING"
    UNKNOWN = "UNKNOWN"


class ContinuityState(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    VALID = "VALID"
    GAP_OPEN = "GAP_OPEN"
    AWAITING_SNAPSHOT = "AWAITING_SNAPSHOT"
    INVALID_SOURCE_TIME = "INVALID_SOURCE_TIME"


class RunState(StrEnum):
    PLANNED = "PLANNED"
    WARMING = "WARMING"
    MEASURING = "MEASURING"
    PASS = "PASS"
    FAIL = "FAIL"


class A2ReasonCode(StrEnum):
    INSUFFICIENT_REVIEWED_MARKETS = "INSUFFICIENT_REVIEWED_MARKETS"
    MALFORMED_JSON = "MALFORMED_JSON"
    DUPLICATE_JSON_KEY = "DUPLICATE_JSON_KEY"
    UNEXPECTED_TOP_LEVEL = "UNEXPECTED_TOP_LEVEL"
    UNKNOWN_MESSAGE = "UNKNOWN_MESSAGE"
    MISSING_FIELD = "MISSING_FIELD"
    TYPE_MISMATCH = "TYPE_MISMATCH"
    UNROUTABLE_MARKET = "UNROUTABLE_MARKET"
    SUBSCRIPTION_REJECTED = "SUBSCRIPTION_REJECTED"
    SOURCE_TIME_REGRESSION = "SOURCE_TIME_REGRESSION"
    LIGHTER_NONCE_GAP = "LIGHTER_NONCE_GAP"
    QUEUE_SATURATED = "QUEUE_SATURATED"
    FRAME_TOO_LARGE = "FRAME_TOO_LARGE"
    PERSISTENCE_UNAVAILABLE = "PERSISTENCE_UNAVAILABLE"
    INTEGRITY_CONFLICT = "INTEGRITY_CONFLICT"
    WEBSOCKET_DISCONNECTED = "WEBSOCKET_DISCONNECTED"
    CLOCK_EVIDENCE_INVALID = "CLOCK_EVIDENCE_INVALID"
    CLOCK_ERROR_EXCEEDED = "CLOCK_ERROR_EXCEEDED"
    CLOCK_DIVERGENCE = "CLOCK_DIVERGENCE"
    OWNERSHIP_CONFLICT = "OWNERSHIP_CONFLICT"
    BATCH_HASH_MISMATCH = "BATCH_HASH_MISMATCH"
    DECODER_VERSION_MISMATCH = "DECODER_VERSION_MISMATCH"
    REPLAY_INTEGRITY_FAILED = "REPLAY_INTEGRITY_FAILED"
    RUN_WINDOW_INVALID = "RUN_WINDOW_INVALID"
    COVERAGE_BELOW_THRESHOLD = "COVERAGE_BELOW_THRESHOLD"
    SILENT_DROP_DETECTED = "SILENT_DROP_DETECTED"
    RETENTION_CHECK_FAILED = "RETENTION_CHECK_FAILED"
    WARMUP_RESET = "WARMUP_RESET"


@dataclass(frozen=True, slots=True)
class ReceivedFrame:
    run_id: UUID
    boot_id: UUID
    venue: Venue
    connection_epoch: int
    connection_frame_index: int
    arrival_ticket: int
    received_wall_ns: int
    received_monotonic_ns: int
    recorder_clock_error_ms: Decimal
    websocket_message_type: WebSocketMessageType
    payload: bytes

    def __post_init__(self) -> None:
        _require_exact(self.run_id, UUID)
        _require_exact(self.boot_id, UUID)
        _require_exact(self.venue, Venue)
        for value in (
            self.connection_epoch,
            self.connection_frame_index,
            self.arrival_ticket,
            self.received_wall_ns,
            self.received_monotonic_ns,
        ):
            _require_nonnegative_int(value)
        if (
            type(self.recorder_clock_error_ms) is not Decimal
            or not self.recorder_clock_error_ms.is_finite()
        ):
            raise ValueError("recorder_clock_error_ms")
        _require_exact(self.websocket_message_type, WebSocketMessageType)
        _require_exact(self.payload, bytes)


@dataclass(frozen=True, slots=True)
class DecoderObservation:
    decoder_version: str
    market_identity: str | None
    venue_market_id: str | None
    channel: str
    message_class: MessageClass
    continuity_state: ContinuityState
    source_timestamp_value: int | None
    source_timestamp_unit: str | None
    source_nonce: int | None
    source_begin_nonce: int | None
    source_offset: int | None
    error_code: A2ReasonCode | None
    error_detail: str | None

    def __post_init__(self) -> None:
        _require_identifier(self.decoder_version)
        _require_optional_identifier(self.market_identity)
        _require_optional_identifier(self.venue_market_id)
        _require_identifier(self.channel)
        _require_exact(self.message_class, MessageClass)
        _require_exact(self.continuity_state, ContinuityState)
        _require_optional_nonnegative_int(self.source_timestamp_value)
        _require_optional_identifier(self.source_timestamp_unit)
        _require_optional_nonnegative_int(self.source_nonce)
        _require_optional_nonnegative_int(self.source_begin_nonce)
        _require_optional_nonnegative_int(self.source_offset)
        if self.error_code is not None:
            _require_exact(self.error_code, A2ReasonCode)
        if self.error_detail is not None:
            _require_code_detail(self.error_detail)


@dataclass(frozen=True, slots=True)
class StoredDecoderEvidence:
    """The exact decoder fields stored outside the raw wire envelope."""

    ingest_index: int
    decoder_version: str
    message_class: MessageClass
    continuity_state: ContinuityState
    error_code: A2ReasonCode | None
    error_detail: str | None

    def __post_init__(self) -> None:
        _require_nonnegative_int(self.ingest_index)
        _require_identifier(self.decoder_version)
        _require_exact(self.message_class, MessageClass)
        _require_exact(self.continuity_state, ContinuityState)
        if self.error_code is not None:
            _require_exact(self.error_code, A2ReasonCode)
        if self.error_detail is not None:
            _require_code_detail(self.error_detail)


@dataclass(frozen=True, slots=True)
class CaptureProfile:
    collector_version: str
    python_version: str
    websocket_library: str
    websocket_library_version: str
    zlib_version: str
    capture_boundary_profile: str
    envelope_schema: str
    ndjson_schema: str
    compression_profile: str

    def __post_init__(self) -> None:
        for value in (
            self.collector_version,
            self.python_version,
            self.websocket_library,
            self.websocket_library_version,
            self.zlib_version,
        ):
            _require_identifier(value)
        if (
            type(self.capture_boundary_profile) is not str
            or self.capture_boundary_profile != CAPTURE_BOUNDARY_PROFILE
        ):
            raise ValueError("capture_boundary_profile")
        if type(self.envelope_schema) is not str or self.envelope_schema != ENVELOPE_SCHEMA:
            raise ValueError("envelope_schema")
        if type(self.ndjson_schema) is not str or self.ndjson_schema != NDJSON_SCHEMA:
            raise ValueError("ndjson_schema")
        if (
            type(self.compression_profile) is not str
            or self.compression_profile != COMPRESSION_PROFILE
        ):
            raise ValueError("compression_profile")


def application_payload_bytes(
    message_type: WebSocketMessageType,
    data: str | bytes,
) -> bytes:
    """Return exact application bytes for one text or binary WebSocket message."""
    _require_exact(message_type, WebSocketMessageType)
    if message_type is WebSocketMessageType.TEXT and type(data) is str:
        return data.encode("utf-8")
    if message_type is WebSocketMessageType.BINARY and type(data) is bytes:
        return data
    raise ValueError("message payload type")


def _require_exact(value: object, expected: type[object]) -> None:
    if type(value) is not expected:
        raise ValueError(expected.__name__)


def _require_nonnegative_int(value: object) -> None:
    if type(value) is not int or value < 0:
        raise ValueError("nonnegative integer")


def _require_optional_nonnegative_int(value: object) -> None:
    if value is not None:
        _require_nonnegative_int(value)


def _require_identifier(value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError("identifier")


def _require_optional_identifier(value: object) -> None:
    if value is not None:
        _require_identifier(value)


def _require_code_detail(value: object) -> None:
    if (
        type(value) is not str
        or not value
        or len(value) > 256
        or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789._:-" for character in value)
    ):
        raise ValueError("error_detail")
