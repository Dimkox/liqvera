# A2 Credential-Free Raw-Wire Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove a credential-free Python collector that retains
replayable public Hyperliquid and Lighter application-message bytes for ten
frozen common perpetual markets through a 60-minute warm-up and one fixed
five-day measured window.

**Architecture:** A Python modular monolith separates immutable wire evidence,
pure venue-semantic observers, bounded dual-venue ingress, one durable
PostgreSQL writer, lifecycle/quality calculation, deterministic replay, and a
read-only status API. PostgreSQL is authoritative; n8n observes but cannot
control runs. Stateful book reconstruction and arbitrage evaluation remain
outside A2.

**Tech Stack:** Python 3.12, `aiohttp` 3.14.3, Psycopg 3.3.4, PostgreSQL 16+
(CI 16.11/17.7 and the existing Claw 16 deployment), standard-library
`unittest`, immutable dataclasses, `Decimal`, canonical NDJSON, deterministic
raw-deflate gzip, Docker, GitHub Actions, Syft 1.49.0, and Trivy 0.72.0.

**Deployment Source of Truth:** collector source and image build live in
`Dimkox/multi-exchange-engine`; `/home/operator/app-stack` Compose, n8n, and
self-hosted deployment integration live in
`https://github.com/Dimkox/openclaw-airgap-farm`. The latter's remote `main`
was `5109675c17c1b3d8975c208c83d054bbc4e5b550` when this plan was written and
must be refreshed before cross-repository work.

## Global Constraints

- Binding design:
  `docs/superpowers/specs/2026-07-27-a2-raw-wire-capture-design.md`.
- Runtime branch: `feature/a2-raw-wire-capture`.
- A2 may call only public Hyperliquid and Lighter discovery/subscription
  endpoints. It has no account, signer, transaction, order, cancellation,
  transfer, withdrawal, RFQ, or private channel.
- The raw application-message bytes are retained before JSON parsing. A
  decoder result can annotate evidence but can never replace or suppress it.
- Hyperliquid `l2Book` messages are complete snapshots without a fabricated
  sequence. Lighter continuity is
  `current.begin_nonce == previous.nonce`; `offset` is evidence only.
- A2 never reconstructs a book, evaluates A1, computes arbitrage, claims
  profitability, or places a trade.
- The frozen universe contains exactly ten reviewed common linear perpetuals,
  ranked by the lower cross-venue 24-hour quote volume.
- One event-loop ingress sequencer assigns a total local arrival ticket before
  a no-await queue admission. One writer preserves that order and allocates
  contiguous durable `ingest_index` values.
- Hyperliquid and Lighter use separate bounded queues. Queue saturation,
  persistence failure, decoder failure, gap, reconnect, and clock failure are
  typed evidence; no overwrite or silent drop is allowed.
- Batch format is `mee-a2-ndjson/v1`.
- Envelope format is `mee-a2-envelope/v1`.
- Capture boundary profile is
  `websocket-application-message-post-decompression/v1`.
- Compression profile is
  `gzip-raw-deflate-6-mtime0-os255/v1`.
- Decoder profiles are `hyperliquid-public-wire/v1` and
  `lighter-public-wire/v1`.
- Status format is `mee-a2-soak-status/v1`.
- Application code lines remain at most 88 characters.
- Every task uses RED/GREEN TDD, updates the canonical root `handoff.md` when
  state changes, passes its focused checks plus the full Python suite and
  `compileall`, runs `git diff --check`, and ends in its own commit.
- Never stage `.env`, database secret material, venue credentials, or unrelated
  worktree changes.

---

## File Responsibility Map

```text
multi_exchange_engine/a2/model.py
  Immutable wire, decoder, batch, feed, run, quality, and decision records.

multi_exchange_engine/a2/codec.py
  Exact text/binary payload conversion and strict canonical NDJSON envelopes.

multi_exchange_engine/a2/batch.py
  One-second/size batch assembly, deterministic gzip, and both hash checks.

multi_exchange_engine/a2/universe.py
  Reviewed discovery evidence, exact volume ranking, and frozen manifest.

multi_exchange_engine/a2/hyperliquid_semantics.py
multi_exchange_engine/a2/lighter_semantics.py
  Pure message classification and venue-native continuity state.

multi_exchange_engine/a2/clock.py
  Recorder clock-error and wall/monotonic divergence evidence.

multi_exchange_engine/a2/pipeline.py
  Dual bounded queues, global ingress ordering, durable acknowledgements.

multi_exchange_engine/a2/repository.py
  PostgreSQL ownership, append-only writes, idempotency, and replay reads.

multi_exchange_engine/a2/transport.py
  Fixed public endpoint policy and proxy-only HTTP/WebSocket primitives.

multi_exchange_engine/a2/hyperliquid_feed.py
multi_exchange_engine/a2/lighter_feed.py
  Public subscriptions, epoch management, reconnect, and raw admission.

multi_exchange_engine/a2/quality.py
multi_exchange_engine/a2/lifecycle.py
multi_exchange_engine/a2/soak_gate.py
  Fixed-slot coverage, warm-up, measured window, and immutable decision.

multi_exchange_engine/a2/status_api.py
multi_exchange_engine/a2/config.py
multi_exchange_engine/a2/app.py
multi_exchange_engine/a2/__main__.py
  Safe configuration, run composition, and GET-only status surface.

multi_exchange_engine/a2/replay.py
  Bounded database replay and evidence/semantic consistency verification.
```

The live feed modules may import `model`, `transport`, venue-semantic observers,
and `pipeline`. They must not import `domain.book`, `shadow`, `execution`, or
any signing/account module.

---

### Task 1: Immutable Wire Model and Deterministic Batch Codec

**Files:**

- Create: `requirements-a2.txt`
- Create: `multi_exchange_engine/a2/__init__.py`
- Create: `multi_exchange_engine/a2/model.py`
- Create: `multi_exchange_engine/a2/codec.py`
- Create: `multi_exchange_engine/a2/batch.py`
- Create: `tests/a2/__init__.py`
- Create: `tests/a2/test_model.py`
- Create: `tests/a2/test_codec.py`
- Create: `tests/a2/test_batch.py`
- Modify: `handoff.md`

**Pinned runtime requirements:**

```text
aiohappyeyeballs==2.7.1
aiohttp==3.14.3
aiosignal==1.4.0
attrs==26.1.0
frozenlist==1.8.0
idna==3.18
multidict==6.7.1
propcache==0.5.2
psycopg==3.3.4
psycopg-binary==3.3.4
typing-extensions==4.16.0; python_version < "3.13"
tzdata==2026.3; sys_platform == "win32"
yarl==1.24.5
```

All listed versions were verified from PyPI on 2026-07-27.

**Interfaces:**

```python
class Venue(StrEnum):
    HYPERLIQUID = "HYPERLIQUID"
    LIGHTER = "LIGHTER"


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


def application_payload_bytes(
    message_type: WebSocketMessageType,
    data: str | bytes,
) -> bytes: ...


def encode_envelope(
    frame: ReceivedFrame,
    ingest_index: int,
    observation: DecoderObservation,
) -> bytes: ...


def decode_envelope(line: bytes) -> RawFrameEnvelope: ...


def build_raw_batch(
    run_id: UUID,
    batch_sequence: int,
    envelopes: Sequence[bytes],
) -> RawWireBatch: ...


def verify_raw_batch(batch: RawWireBatch) -> tuple[RawFrameEnvelope, ...]: ...
```

`application_payload_bytes` accepts text only as an exact built-in `str` and
returns UTF-8 bytes; binary accepts only exact built-in `bytes`. It rejects
subclasses and mismatched types. The model rejects booleans where integers are
required, negative indexes/timestamps, non-finite `Decimal`, empty identifiers,
non-lowercase SHA-256, and mutable payloads.

Market and channel routing comes from the typed decoder observation because
each venue connection is multiplexed. Malformed/unroutable frames use null
market fields and channel `UNKNOWN`; their raw payload is still retained.
Decoder detail is a bounded 256-character code-oriented explanation and never
contains a raw-payload excerpt.

`build_raw_batch` joins complete canonical envelope lines with one terminal LF.
It constructs gzip bytes manually from the fixed ten-byte header, raw DEFLATE
level 6, CRC32, and input size so the OS byte is always 255 on Python 3.12.

- [ ] **Step 1: Write failing strict-model and codec tests**

Cover text/binary byte identity, Unicode escapes, NUL bytes, malformed base64,
payload length/hash mismatch, duplicate/unknown keys, subclass rejection,
non-finite clock error, exact enum membership, and exact round trip.

- [ ] **Step 2: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_model `
  tests.a2.test_codec `
  tests.a2.test_batch -v
```

Expected: import failure because `multi_exchange_engine.a2` does not exist.

- [ ] **Step 3: Implement the minimum immutable model and strict codec**

Use `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=False)`
and `json.loads(..., parse_float=Decimal, object_pairs_hook=...)`. The object
pairs hook must reject duplicate keys before conversion to a mapping.

- [ ] **Step 4: Implement deterministic batching and verification**

Tests must prove two fresh Python processes generate byte-identical NDJSON,
gzip bytes, uncompressed hash, and compressed hash.

- [ ] **Step 5: Run GREEN and dependency integrity**

```powershell
python -m pip install -r requirements-a2.txt
python -m pip check
python -B -m unittest `
  tests.a2.test_model `
  tests.a2.test_codec `
  tests.a2.test_batch -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero; the pre-A2 suite remains green.

- [ ] **Step 6: Update handoff and commit**

```powershell
git add -- requirements-a2.txt multi_exchange_engine/a2 tests/a2 handoff.md
git commit -m "feat: define A2 raw evidence codec"
```

---

### Task 2: Reviewed Discovery Evidence and Frozen Universe

**Files:**

- Create: `multi_exchange_engine/a2/universe.py`
- Create: `tests/a2/test_universe.py`
- Modify: `handoff.md`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ReviewedPerpetualMapping:
    mapping_id: str
    identity: InstrumentIdentity
    hyperliquid_market_id: str
    lighter_market_id: str
    valuation_currency: str
    settlement_currency: str
    payoff: str
    hyperliquid_quote_reference: str
    lighter_quote_reference: str
    basis_risk_policy: str
    hyperliquid_multiplier: Decimal
    lighter_multiplier: Decimal
    evidence_version: str


@dataclass(frozen=True, slots=True)
class VenueDiscoveryEvidence:
    venue: Venue
    mapping_id: str
    venue_market_id: str
    quote_volume_24h: Decimal
    payload_sha256: str
    observed_at_ns: int


@dataclass(frozen=True, slots=True)
class FrozenMapping:
    rank: int
    mapping_id: str
    identity: InstrumentIdentity
    hyperliquid_market_id: str
    lighter_market_id: str
    valuation_currency: str
    settlement_currency: str
    payoff: str
    hyperliquid_quote_reference: str
    lighter_quote_reference: str
    basis_risk_policy: str
    hyperliquid_multiplier: Decimal
    lighter_multiplier: Decimal
    evidence_version: str
    hyperliquid_quote_volume_24h: Decimal
    lighter_quote_volume_24h: Decimal
    shared_liquidity_score: Decimal
    hyperliquid_discovery_sha256: str
    lighter_discovery_sha256: str
    hyperliquid_observed_at_ns: int
    lighter_observed_at_ns: int


@dataclass(frozen=True, slots=True)
class FrozenUniverse:
    run_id: UUID
    mappings: tuple[FrozenMapping, ...]
    manifest_sha256: str


def freeze_universe(
    run_id: UUID,
    reviewed: Sequence[ReviewedPerpetualMapping],
    discovered: Sequence[VenueDiscoveryEvidence],
    *,
    required_count: int = 10,
) -> FrozenUniverse: ...
```

The function admits one positive venue-reported USD-valued volume record from
each venue per mapping. It requires the same base asset, `1x` linear payoff,
USDC settlement, base-asset displayed size, and an explicit
`EXPLICIT_ORACLE_STABLECOIN_BASIS/v1` policy with separate venue quote
references. It computes the exact `Decimal` minimum and sorts by descending
score then `mapping_id.encode("utf-8")`. It fails before returning when fewer
than ten eligible mappings exist. The manifest hash covers every frozen field,
both quote references, the basis-risk policy, and both discovery payload
hashes.

- [ ] **Step 1: Write failing universe tests**

Cover eleven candidates, exact top ten, asymmetric volume, byte-order tie,
duplicate venue evidence, missing venue, zero/negative/non-finite volume,
valuation/settlement mismatch, non-`1x` multiplier, missing quote-reference or
basis policy, fewer than ten, input permutation, and manifest-hash stability.

- [ ] **Step 2: Run RED**

```powershell
python -B -m unittest tests.a2.test_universe -v
```

Expected: import failure for `multi_exchange_engine.a2.universe`.

- [ ] **Step 3: Implement exact validation, ranking, and manifest hashing**

Reuse `InstrumentIdentity`; do not infer equivalence from ticker equality.
Never convert discovery values through `float`.

- [ ] **Step 4: Run focused and full checks**

```powershell
python -B -m unittest tests.a2.test_universe -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [ ] **Step 5: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/universe.py `
  tests/a2/test_universe.py handoff.md
git commit -m "feat: freeze A2 discovery universe"
```

---

### Task 3: Venue-Native Semantic Observers and Pinned Fixtures

**Files:**

- Create: `multi_exchange_engine/a2/hyperliquid_semantics.py`
- Create: `multi_exchange_engine/a2/lighter_semantics.py`
- Create: `tests/a2/test_hyperliquid_semantics.py`
- Create: `tests/a2/test_lighter_semantics.py`
- Create: `tests/fixtures/a2/hyperliquid-l2-snapshot.json`
- Create: `tests/fixtures/a2/hyperliquid-trades.json`
- Create: `tests/fixtures/a2/hyperliquid-asset-context.json`
- Create: `tests/fixtures/a2/lighter-order-book-snapshot.json`
- Create: `tests/fixtures/a2/lighter-order-book-delta.json`
- Create: `tests/fixtures/a2/lighter-trades.json`
- Create: `tests/fixtures/a2/lighter-market-stats.json`
- Create: `tests/fixtures/a2/manifest.json`
- Modify: `handoff.md`

**Interfaces:**

```python
class HyperliquidSemanticObserver:
    version = "hyperliquid-public-wire/v1"

    def __init__(
        self,
        routes: Mapping[str, str],
    ) -> None: ...

    def observe(
        self,
        payload: bytes,
    ) -> DecoderObservation: ...


class LighterSemanticObserver:
    version = "lighter-public-wire/v1"

    def __init__(
        self,
        routes: Mapping[str, str],
    ) -> None: ...

    def observe(
        self,
        payload: bytes,
    ) -> DecoderObservation: ...
```

Each observer owns only one multiplexed venue connection epoch and receives
the frozen venue-market routing map at construction. Keys are exact venue
market IDs as strings (`coin` for Hyperliquid and the numeric market-index
suffix from Lighter channels); values are canonical market-identity strings
prepared by the universe layer. The observer copies and validates this map.
Reconnect creates a fresh observer instance and fresh per-market continuity
state.

Hyperliquid rules:

- `l2Book` is `SNAPSHOT`;
- a source-time regression returns `INVALID_SOURCE_TIME` and never advances
  the last valid source time;
- `trades` is `TRADE`;
- `activeAssetCtx` is `MARKET_STATS`; published funding remains retained in
  the immutable raw payload and is validated as a finite `Decimal`, but A2's
  bounded `DecoderObservation` does not duplicate it;
- no sequence or nonce is fabricated.

Lighter rules:

- `subscribed/order_book` opens `VALID` with its `nonce`;
- `update/order_book` is `DELTA` only when its `begin_nonce` equals the last
  valid `nonce` and its new `nonce` is greater;
- a mismatch returns `GAP_OPEN`; later deltas return `AWAITING_SNAPSHOT`;
- a new snapshot restores `VALID`;
- `offset` is retained and never compared for continuity;
- `trade` and `market_stats` are typed without affecting L2 nonce state.

Malformed JSON, duplicate keys, wrong top-level type, missing required fields,
and type mismatch return a typed observation instead of raising past the
observer boundary.

- [ ] **Step 1: Pin representative public-format fixtures**

Record source URL, retrieval UTC instant, byte length, and lowercase SHA-256 in
`tests/fixtures/a2/manifest.json`. Fixtures contain no account, transaction,
order, signer, or credential data.

- [ ] **Step 2: Write failing classification and continuity tests**

Cover Hyperliquid equal/increasing/regressing source time, Lighter valid chain,
gap, post-gap delta, fresh snapshot, drastic offset change with valid nonce,
malformed messages, unknown message types, and state isolation across observer
instances.

- [ ] **Step 3: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_hyperliquid_semantics `
  tests.a2.test_lighter_semantics -v
```

Expected: import failures for both semantic modules.

- [ ] **Step 4: Implement pure observers**

Parse with `Decimal` for JSON floats. Do not import or call
`LighterBookReducer`, `OrderBookSnapshot`, or any A1/shadow evaluator.

- [ ] **Step 5: Run focused and full checks**

```powershell
python -B -m unittest `
  tests.a2.test_hyperliquid_semantics `
  tests.a2.test_lighter_semantics -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [ ] **Step 6: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/hyperliquid_semantics.py `
  multi_exchange_engine/a2/lighter_semantics.py `
  tests/a2/test_hyperliquid_semantics.py `
  tests/a2/test_lighter_semantics.py tests/fixtures/a2 handoff.md
git commit -m "feat: classify A2 venue wire semantics"
```

---

### Task 4: Clock Guard, Bounded Ingress, and Durable Tickets

**Files:**

- Create: `multi_exchange_engine/a2/clock.py`
- Create: `multi_exchange_engine/a2/pipeline.py`
- Create: `tests/a2/test_clock.py`
- Create: `tests/a2/test_pipeline.py`
- Modify: `handoff.md`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ClockReading:
    wall_ns: int
    monotonic_ns: int
    estimated_error_ms: Decimal


class ClockGuard:
    def observe(self, reading: ClockReading) -> ClockDecision: ...


class ClockEvidenceProvider(Protocol):
    def read(self) -> HostClockEvidence: ...


class BatchSink(Protocol):
    async def persist(
        self,
        batch: RawWireBatch,
        observations: Sequence[PersistedDecoderObservation],
    ) -> None: ...


class CaptureIngress:
    def admit(
        self,
        venue: Venue,
        frame_factory: Callable[[int], ReceivedFrame],
    ) -> AdmittedFrame: ...


class BatchWriter:
    async def run(self) -> None: ...
    async def stop_at_boundary(self) -> None: ...
```

Fixed trusted defaults live in `pipeline.py` constants:

```python
VENUE_QUEUE_CAPACITY = 20_000
VENUE_QUEUE_BYTE_CAPACITY = 64 * 1024 * 1024
MAX_FRAME_BYTES = 8 * 1024 * 1024
MAX_BATCH_UNCOMPRESSED_BYTES = 16 * 1024 * 1024
BATCH_WALL_INTERVAL_NS = 1_000_000_000
MAX_CLOCK_ERROR_MS = Decimal("25")
MAX_WALL_MONOTONIC_DIVERGENCE_MS = Decimal("50")
MAX_CLOCK_EVIDENCE_AGE_MS = Decimal("2000")
```

`HostClockEvidence` is read from an atomically replaced, read-only JSON file
generated on the Claw host from `chronyc -c tracking`. The host writer records
sample wall time, absolute system-time offset, root dispersion, root delay, and
leap status. The collector computes the conservative error bound
`abs(offset) + root_dispersion + root_delay / 2`. Missing, stale, malformed, or
non-normal leap status is invalid evidence and blocks readiness.

`CaptureIngress.admit` copies the raw bytes, allocates one increasing arrival
ticket, and performs `put_nowait` without an intervening await. It returns an
`AdmittedFrame` containing a one-shot observation port and a durable ticket.
The receiver synchronously completes the observation port with either a
semantic result or a typed decoder failure. Saturation raises
`QueueSaturated`; it never evicts an older frame. `BatchWriter` selects the
lowest queued arrival ticket across both queue heads, requires its observation
port to be complete, assigns the next durable `ingest_index`, and closes on
wall-second or size boundary. A `DurableTicket` becomes successful only after
`BatchSink.persist` commits.

Count and byte budgets must both admit a frame. An application message above
8 MiB closes the epoch with `FRAME_TOO_LARGE` and makes the run fail; the code
must not truncate it or claim that the unavailable bytes were captured.

- [ ] **Step 1: Write failing clock and pipeline tests**

Cover exact threshold boundaries, wall step, monotonic stability, interleaved
venue ordering, count and byte saturation, oversized frame, no eviction,
one-second boundary, early size close,
fresh/stale/malformed/unsynchronized host clock evidence, one-shot observation
attachment, typed decoder failure, sink outage, durable-ticket timing, retry
of the same immutable batch, and stop only at a batch boundary.

- [ ] **Step 2: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_clock `
  tests.a2.test_pipeline -v
```

Expected: import failures for `clock` and `pipeline`.

- [ ] **Step 3: Implement clock decisions and bounded ingress**

Use one event-loop thread for admission. Do not use a cross-thread global
counter or wall time to break ties.

- [ ] **Step 4: Implement batch writer and failure propagation**

On persistence failure, stop accepting both venue streams, fail the affected
epoch through a typed callback, retain the immutable pending batch, and retry
only after the sink readiness probe succeeds.

- [ ] **Step 5: Run focused and full checks**

```powershell
python -B -m unittest tests.a2.test_clock tests.a2.test_pipeline -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [ ] **Step 6: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/clock.py `
  multi_exchange_engine/a2/pipeline.py `
  tests/a2/test_clock.py tests/a2/test_pipeline.py handoff.md
git commit -m "feat: bound A2 capture ingress"
```

---

### Task 5: Append-Only PostgreSQL Schema and Repository

**Files:**

- Create: `migrations/000002_a2_raw_capture.up.sql`
- Create: `migrations/000002_a2_raw_capture.down.sql`
- Create: `multi_exchange_engine/a2/repository.py`
- Create: `scripts/a2-migrate.py`
- Create: `scripts/run-a2-postgres-tests.py`
- Create: `tests/a2/test_repository_unit.py`
- Create: `tests/a2/integration/__init__.py`
- Create: `tests/a2/integration/test_repository_postgres.py`
- Modify: `handoff.md`

**Schema contract:**

Create schema `a2` and these append-only tables:

```text
a2.raw_capture_runs
  (run_id, event_index, state, occurred_at, boot_id, measured_start,
   measured_end, reason_code, run_manifest_json, manifest_sha256)

a2.raw_instrument_mappings
  (run_id, mapping_id, rank, identity_json, hyperliquid_market_id,
   lighter_market_id, hyperliquid_quote_volume, lighter_quote_volume,
   shared_liquidity_score, hyperliquid_discovery_sha256,
   lighter_discovery_sha256)

a2.raw_feed_connections
  (event_day, run_id, venue, venue_market_id, channel, connection_epoch,
   event_kind, occurred_wall_ns, boot_id, websocket_library,
   websocket_library_version, negotiated_extensions, reason_code)

a2.raw_wire_batches
  (capture_day, run_id, batch_sequence, first_ingest_index,
   last_ingest_index, first_wall_ns, last_wall_ns, first_monotonic_ns,
   last_monotonic_ns, frame_count, uncompressed_bytes, compressed_bytes,
   uncompressed_sha256, compressed_sha256, compression_profile,
   gzip_payload)

a2.raw_decoder_observations
  (observation_day, run_id, ingest_index, decoder_version, message_class,
   continuity_state, error_code, error_detail)

a2.raw_quality_minutes
  (minute_day, run_id, venue, venue_market_id, channel, minute_start,
   expected_slots, valid_slots, max_source_age_ms,
   max_cross_venue_receive_skew_ms, invalid_reason_counts, quality_sha256)

a2.raw_soak_decisions
  (run_id, decided_at, decision, report_sha256, reason_codes,
   measured_start, measured_end)
```

`raw_capture_runs` is an immutable event stream keyed by
`(run_id, event_index)`. Repeated `WARMING` events are legal after warm-up
reset. A partial unique index permits only one `PASS` or `FAIL` event per run.
`raw_wire_batches` is partitioned by `capture_day`; feed, decoder, and quality
time series are partitioned by their UTC day columns.

Partitioned primary keys include their day column. Logical keys are
`(run_id, batch_sequence)`, `(run_id, ingest_index)`, and
`(run_id, venue, venue_market_id, channel, minute_start)`. The repository
derives every day from integer epoch nanoseconds and rejects a caller-supplied
day mismatch, preventing the same logical key from escaping uniqueness through
another partition. A transition trigger serializes each new run event and
enforces the lifecycle graph in Task 8.

Every table receives the same trigger function that raises SQLSTATE `55000` on
`UPDATE` or `DELETE`. The migration creates `a2.ensure_day_partitions(date)`
and `a2.drop_expired_raw_partitions(date)`. Retention drops only closed
`raw_wire_batches` partitions strictly older than seven complete UTC days and
refuses to drop a partition containing a nonterminal run.

The two DDL helpers are `SECURITY DEFINER`, owned by the A2 schema owner, set an
exact safe `search_path`, validate generated partition identifiers, and expose
only their narrow signatures to the writer role. `PUBLIC` execution is
revoked. The writer role has `SELECT`, `INSERT`, and helper execution only; it
cannot issue arbitrary DDL or update/delete evidence.

**Repository interfaces:**

```python
class RawEvidenceRepository:
    @classmethod
    def connect(cls, dsn: str) -> RawEvidenceRepository: ...

    def claim_run(self, run_id: UUID) -> RunLease: ...
    def append_run_event(self, event: RunEvent) -> None: ...
    def persist_universe(
        self,
        universe: FrozenUniverse,
        discovery_evidence: Sequence[DiscoveryControlEvidence],
    ) -> None: ...
    def append_feed_event(self, event: FeedConnectionEvent) -> None: ...
    def persist(
        self,
        batch: RawWireBatch,
        observations: Sequence[PersistedDecoderObservation],
    ) -> None: ...
    def append_quality_minute(self, minute: QualityMinute) -> None: ...
    def append_decision(self, decision: SoakDecision) -> None: ...
    def iter_batches(self, run_id: UUID) -> Iterator[RawWireBatch]: ...
    def ready(self) -> bool: ...
```

`claim_run` holds a session-level PostgreSQL advisory lock for the lease
lifetime. `persist` uses one transaction for partition creation, batch insert,
and decoder observations. An identical conflict returns success only after
every stored metadata field and payload byte matches. Any mismatch raises
`IntegrityConflict`.

- [ ] **Step 1: Write failing unit and SQL-contract tests**

Cover DSN redaction, advisory-lock key stability, exact idempotency comparison,
conflict typing, table/trigger/function presence, no `pgvector`, and no SQL
update/delete in repository production paths. Verify definer ownership, fixed
search path, identifier validation, revoked public execution, and writer-role
grants.

- [ ] **Step 2: Run unit RED**

```powershell
python -B -m unittest tests.a2.test_repository_unit -v
```

Expected: import failure for `repository`.

- [ ] **Step 3: Write migrations and minimal repository**

The down migration drops only A2 functions/tables/schema and never touches
`000001_init` objects.

- [ ] **Step 4: Write real PostgreSQL integration tests**

Use `A2_TEST_DATABASE_URL`. Tests must apply up/down/up, exercise owner-level
append-only triggers, reject a second run lease, verify identical retry,
conflicting retry, UTC day partition names, both seven-day boundaries, rollback
after a forced exception, and clean restart.

Integration modules use an explicit unittest skip when the DSN is absent so
the ordinary unit suite remains runnable. `scripts/run-a2-postgres-tests.py`
requires the DSN, treats any skip as failure, and is the binding local/CI
PostgreSQL gate. With no module arguments it runs every `tests.a2.integration`
module; with arguments it runs exactly those fully qualified modules.

- [ ] **Step 5: Run PostgreSQL RED/GREEN**

```powershell
python -B -m unittest tests.a2.test_repository_unit -v
python scripts/run-a2-postgres-tests.py
```

Expected before a test PostgreSQL DSN exists: the runner fails explicitly with
`A2_TEST_DATABASE_URL is required`. With the CI/local PostgreSQL DSN set, both
commands exit zero and the runner reports zero skips.

- [ ] **Step 6: Run full checks**

```powershell
python -m compileall -q multi_exchange_engine tests scripts
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero in the configured PostgreSQL environment.

- [ ] **Step 7: Update handoff and commit**

```powershell
git add -- migrations/000002_a2_raw_capture.up.sql `
  migrations/000002_a2_raw_capture.down.sql `
  multi_exchange_engine/a2/repository.py scripts/a2-migrate.py `
  scripts/run-a2-postgres-tests.py `
  tests/a2/test_repository_unit.py tests/a2/integration handoff.md
git commit -m "feat: persist A2 evidence in PostgreSQL"
```

---

### Task 6: Pipeline-to-Repository Crash and Recovery Contract

**Files:**

- Modify: `multi_exchange_engine/a2/pipeline.py`
- Modify: `multi_exchange_engine/a2/repository.py`
- Create: `tests/a2/integration/test_pipeline_postgres.py`
- Modify: `handoff.md`

**Required behavior:**

- the writer resumes `batch_sequence` and `ingest_index` from the last committed
  batch under the held run lease;
- a crash before commit leaves no batch or decoder rows;
- a crash after commit replays as an identical idempotent insert;
- PostgreSQL outage stops feed admission, closes active epochs with
  `PERSISTENCE_UNAVAILABLE`, and does not discard the pending immutable batch;
- persistence readiness must return before collectors reconnect;
- a new process gets a new `boot_id` and new connection epochs but does not
  extend the measured window.

- [ ] **Step 1: Write failing integration tests**

Use a child process and a database barrier table created only by the test to
terminate before commit and immediately after commit. Assert exact row counts,
indexes, and hashes after restart.

- [ ] **Step 2: Run RED**

```powershell
python scripts/run-a2-postgres-tests.py `
  tests.a2.integration.test_pipeline_postgres
```

Expected: failures because restart cursors and the durable sink adapter are not
implemented.

- [ ] **Step 3: Implement repository cursor recovery and sink adapter**

Do not infer the next index from sequence counts; read the last committed
`last_ingest_index` and `batch_sequence` under the run lease.

- [ ] **Step 4: Run focused and full checks**

```powershell
python scripts/run-a2-postgres-tests.py `
  tests.a2.integration.test_pipeline_postgres
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [ ] **Step 5: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/pipeline.py `
  multi_exchange_engine/a2/repository.py `
  tests/a2/integration/test_pipeline_postgres.py handoff.md
git commit -m "feat: recover A2 durable capture state"
```

---

### Task 7: Fixed Public Transports, Discovery, and Venue Feeds

**Files:**

- Modify: `migrations/000002_a2_raw_capture.up.sql`
- Modify: `multi_exchange_engine/a2/repository.py`
- Create: `multi_exchange_engine/a2/transport.py`
- Create: `multi_exchange_engine/a2/hyperliquid_feed.py`
- Create: `multi_exchange_engine/a2/lighter_feed.py`
- Create: `scripts/build-a2-mapping-review.py`
- Create: `config/a2-reviewed-perpetual-mappings.json`
- Create: `docs/a2-mapping-review.md`
- Create: `tests/a2/test_transport.py`
- Create: `tests/a2/test_mapping_registry.py`
- Create: `tests/a2/test_hyperliquid_feed.py`
- Create: `tests/a2/test_lighter_feed.py`
- Modify: `tests/a2/integration/test_repository_postgres.py`
- Modify: `multi_exchange_engine/a2/universe.py`
- Modify: `handoff.md`

**Public endpoint policy:**

```python
HYPERLIQUID_INFO_URL = "https://api.hyperliquid.xyz/info"
HYPERLIQUID_WS_URL = "wss://api.hyperliquid.xyz/ws"
LIGHTER_ORDER_BOOKS_URL = (
    "https://mainnet.zklighter.elliot.ai/api/v1/orderBooks"
)
LIGHTER_WS_URL = (
    "wss://mainnet.zklighter.elliot.ai/stream?readonly=true"
)
```

Production configuration cannot override hosts or remove Lighter's
`readonly=true`. Tests inject fake sessions instead of changing production
URLs.

**Allowed outbound application messages:**

```python
def hyperliquid_subscriptions(coin: str) -> tuple[dict[str, object], ...]:
    return (
        {"method": "subscribe", "subscription": {"type": "l2Book", "coin": coin}},
        {"method": "subscribe", "subscription": {"type": "trades", "coin": coin}},
        {
            "method": "subscribe",
            "subscription": {"type": "activeAssetCtx", "coin": coin},
        },
    )


def lighter_subscriptions(market_index: int) -> tuple[dict[str, str], ...]:
    return (
        {"type": "subscribe", "channel": f"order_book/{market_index}"},
        {"type": "subscribe", "channel": f"trade/{market_index}"},
        {"type": "subscribe", "channel": f"market_stats/{market_index}"},
    )
```

Lighter discovery first subscribes to `market_stats/all` in read-only mode to
obtain current positive daily quote volume. Hyperliquid discovery uses only
`{"type": "metaAndAssetCtxs"}` and reads exact decimal strings such as
`dayNtlVlm`. Both raw discovery payloads enter the control-evidence stream and
their hashes bind the frozen universe.

`scripts/build-a2-mapping-review.py` writes a deterministic candidate report
from current public metadata. It never auto-approves a mapping. The committed
registry contains every common candidate accepted by documented review, not a
volume-preselected ten, and records pair mapping ID, both symbols, identity,
USD valuation, USDC settlement, per-venue quote references, the explicit
basis-risk policy, payoff/multiplier/displayed-size semantics, decision,
evidence URL/hash, reviewer, and review UTC instant. Runtime discovery joins
current venue market IDs, tick/lot/minimums, and volume to that registry. Task
GREEN requires at least ten accepted current candidates.

`aiohttp.ClientSession` uses explicit `proxy="http://proxy-gateway:1080"` for
HTTPS and WebSocket handshakes. `NO_PROXY` is limited to loopback,
`postgres-db`, and internal RFC1918 destinations. WebSocket heartbeat is 30
seconds, below Lighter's two-minute keepalive limit. WebSocket
`max_msg_size` equals the trusted 8 MiB frame limit. TLS certificate and
hostname verification use the default trusted CA context and cannot be
disabled by configuration.

- [ ] **Step 1: Write failing endpoint and outbound-message tests**

Reject userinfo URLs, redirects to an unapproved host, non-TLS venue URLs,
missing read-only query, arbitrary REST request types, transaction messages,
private channel names, and any production URL override.

- [ ] **Step 2: Write failing fake-feed tests**

Fake sessions deliver text and binary frames, subscription acknowledgements,
malformed payloads, disconnects, queue saturation, and reconnects. Assert raw
admission precedes observer invocation and every reconnect increments the
epoch with a fresh semantic observer. Assert each OPEN event records the
actual WebSocket response extension header and exact `aiohttp` version.

Each venue uses one multiplexed live WebSocket connection for all frozen
markets and required channels. Feed connection OPEN/CLOSE rows therefore use
null market ID and channel `MULTIPLEXED`; per-market subscription state comes
from retained control messages.

- [ ] **Step 3: Write failing mapping-registry tests**

Reject automatic approval, ticker-only equivalence, unknown fields, missing
evidence hashes, unequal linear multipliers, non-perpetual payoff, duplicate
symbols/IDs, volume-derived membership, and fewer than ten current accepted
candidates.

- [ ] **Step 4: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_transport `
  tests.a2.test_mapping_registry `
  tests.a2.test_hyperliquid_feed `
  tests.a2.test_lighter_feed -v
```

Expected: import/file failures for transport, registry, and feed modules.

- [ ] **Step 5: Implement public transport and discovery**

Redirect handling is disabled. Parse discovery numbers with `Decimal`, reject
JSON floats outside a `Decimal` parser, and never import an SDK signer.

- [ ] **Step 6: Build and review the production mapping registry**

Generate the current candidate report, verify the accepted records against
official public contract metadata, record hashes and decisions in
`docs/a2-mapping-review.md`, and run the registry tests. Do not admit a record
merely because its symbols match.

- [ ] **Step 7: Implement both raw feed collectors**

The receiver records wall/monotonic timestamps and application bytes, admits
the raw frame, then invokes its observer. A decoder exception becomes a typed
observation and cannot cancel raw persistence.

- [ ] **Step 8: Run focused and full checks**

```powershell
python -B -m unittest `
  tests.a2.test_transport `
  tests.a2.test_mapping_registry `
  tests.a2.test_hyperliquid_feed `
  tests.a2.test_lighter_feed -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero; tests use fixtures after the reviewed
registry is committed.

- [ ] **Step 9: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/transport.py `
  multi_exchange_engine/a2/hyperliquid_feed.py `
  multi_exchange_engine/a2/lighter_feed.py `
  multi_exchange_engine/a2/universe.py `
  scripts/build-a2-mapping-review.py `
  config/a2-reviewed-perpetual-mappings.json `
  docs/a2-mapping-review.md tests/a2/test_transport.py `
  tests/a2/test_mapping_registry.py `
  tests/a2/test_hyperliquid_feed.py tests/a2/test_lighter_feed.py handoff.md
git commit -m "feat: collect A2 public venue frames"
```

---

### Task 8: Warm-Up, Fixed Measured Window, and Soak Gate

**Files:**

- Create: `multi_exchange_engine/a2/quality.py`
- Create: `multi_exchange_engine/a2/lifecycle.py`
- Create: `multi_exchange_engine/a2/soak_gate.py`
- Create: `tests/a2/test_quality.py`
- Create: `tests/a2/test_lifecycle.py`
- Modify: `multi_exchange_engine/a2/model.py`
- Modify: `multi_exchange_engine/a2/repository.py`
- Modify: `migrations/000002_a2_raw_capture.up.sql`
- Modify: `tests/a2/test_repository_unit.py`
- Modify: `tests/a2/integration/test_pipeline_postgres.py`
- Modify: `tests/a2/integration/test_repository_postgres.py`
- Modify: `handoff.md`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class SlotEvidence:
    second_start_ns: int
    subscription_acknowledged: bool
    epoch_active: bool
    recorder_clock_valid: bool
    persistence_ready: bool
    continuity_open: bool


def slot_is_valid(evidence: SlotEvidence) -> bool: ...


class SoakLifecycle:
    def apply(self, event: LifecycleEvent) -> tuple[RunEvent, ...]: ...


class SoakGate:
    def decide(
        self,
        run: CompletedMeasuredRun,
        mappings: FrozenUniverse,
        quality: Sequence[QualityMinute],
        integrity: ReplayIntegrity,
    ) -> SoakDecision: ...
```

Constants:

```python
WARMUP_MINUTES = 60
MEASURED_SECONDS = 5 * 24 * 60 * 60
REQUIRED_MAPPING_COUNT = 10
REQUIRED_L2_STREAM_COUNT = 20
MIN_L2_SLOT_COVERAGE = Decimal("0.995")
HYPERLIQUID_BOOK_AGE_REFERENCE_MS = Decimal("750")
LIGHTER_BOOK_AGE_REFERENCE_MS = Decimal("200")
CROSS_VENUE_RECEIVE_SKEW_REFERENCE_MS = Decimal("250")
```

A quality minute stores 60 expected slots per frozen L2 stream. Quiet healthy
seconds are valid. Trades/stats/funding must be subscribed and replayable but
do not use message-frequency coverage.

For every observed L2 message, quality records source-time age when the source
unit is qualified. For each mapping/second with observations from both venues,
it records the absolute skew between the latest receive times without
constructing or comparing books. Minute summaries retain maxima and counts
against the 750/200/250 millisecond reference thresholds. These measurements
are evidence for A3 and do not independently fail A2 coverage.

The lifecycle allows:

```text
PLANNED -> WARMING -> MEASURING -> PASS
PLANNED -> FAIL
WARMING -> WARMING
WARMING -> FAIL
MEASURING -> FAIL
```

The repeated `WARMING` event records a reset reason. `MEASURING` persists one
UTC `measured_start` and `measured_end = measured_start + 432000 seconds`.
Restart cannot change either instant.

- [x] **Step 1: Write failing slot and lifecycle tests**

Cover every validity predicate, quiet stream, half-open boundaries, leap over a
minute, warm-up reset, exactly 60 valid minutes, restart during measurement,
exact 99.5 percent pass, one invalid slot below threshold, missing mapping,
missing stream, source-time age, receive-time skew, negative source age, hash
failure, silent-drop failure, and immutable terminal state.

- [x] **Step 2: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_quality `
  tests.a2.test_lifecycle -v
```

Expected: import failures for `quality` and `lifecycle`.

- [x] **Step 3: Implement quality aggregation and lifecycle reducer**

All interval comparisons use integer nanoseconds. Do not use local time or
floating-point percentages.

- [x] **Step 4: Implement exhaustive fail-closed decision**

`SoakGate` returns only `PASS` or `FAIL`. It has no extend, go, override, or
manual-success input.

- [x] **Step 5: Run focused and full checks**

```powershell
python -B -m unittest tests.a2.test_quality tests.a2.test_lifecycle -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [x] **Step 6: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/quality.py `
  multi_exchange_engine/a2/lifecycle.py `
  multi_exchange_engine/a2/soak_gate.py `
  tests/a2/test_quality.py tests/a2/test_lifecycle.py handoff.md
git commit -m "feat: gate the A2 measured soak"
```

---

### Task 9: Safe Configuration, Application Composition, and GET-Only Status

**Files:**

- Create: `multi_exchange_engine/a2/config.py`
- Create: `multi_exchange_engine/a2/status_api.py`
- Create: `multi_exchange_engine/a2/app.py`
- Create: `multi_exchange_engine/a2/runtime.py`
- Create: `multi_exchange_engine/a2/fixture_runtime.py`
- Create: `multi_exchange_engine/a2/__main__.py`
- Create: `tests/a2/test_config.py`
- Create: `tests/a2/test_status_api.py`
- Create: `tests/a2/test_app.py`
- Create: `tests/a2/test_runtime.py`
- Modify: `multi_exchange_engine/a2/feed.py`
- Modify: `multi_exchange_engine/a2/hyperliquid_feed.py`
- Modify: `multi_exchange_engine/a2/lighter_feed.py`
- Modify: `multi_exchange_engine/a2/pipeline.py`
- Modify: `multi_exchange_engine/a2/repository.py`
- Modify: `handoff.md`

**Configuration contract:**

```text
A2_RUN_ID
A2_FEED_MODE=public
A2_DATABASE_URL_FILE=/run/secrets/a2_database_url
A2_CLOCK_EVIDENCE_FILE=/run/a2-clock/clock.json
A2_PROXY_URL=http://proxy-gateway:1080
A2_STATUS_HOST=0.0.0.0
A2_STATUS_PORT=8081
A2_LOG_LEVEL=INFO
```

`A2_DATABASE_URL` is intentionally rejected. The process reads the DSN from
the named file, validates that it is a regular file with no group/other access
on Linux, and never includes the value in `repr`, logs, status, exceptions, or
evidence.

`A2_FEED_MODE` accepts only `public` or `fixture`. Fixture mode uses the
committed A2 feed corpus and cannot contact venue hosts; public mode uses the
fixed endpoint policy.

**Status routes:**

```text
GET /health
GET /ready
GET /v1/a2/soak-status
```

`/health` proves the event loop responds. `/ready` requires held run ownership,
database readiness, frozen universe, and both collector readiness states.
Soak status returns state, immutable window bounds, warm-up progress, coverage,
typed failure counts, batch/index/hash progress, and no configuration values.

- [x] **Step 1: Write failing configuration tests**

Cover missing file, symlink, directory, permissive Linux mode, empty DSN,
credential-bearing environment value, invalid UUID/port/proxy, safe repr, and
redacted errors.

- [x] **Step 2: Write failing status/application tests**

Assert exact schemas and content types, 405 for POST/PUT/PATCH/DELETE, no route
that starts/stops/extends/decides a run, readiness transitions, ownership
conflict, signal-driven boundary shutdown, and absence of DSN/token/key fields.

- [x] **Step 3: Run RED**

```powershell
python -B -m unittest `
  tests.a2.test_config `
  tests.a2.test_status_api `
  tests.a2.test_app -v
```

Expected: import failures for configuration, API, and application modules.

- [x] **Step 4: Implement safe config and status API**

Use `aiohttp.web`; register GET routes explicitly. Do not add generic route
handlers.

- [x] **Step 5: Compose app ownership, discovery, feeds, writer, and lifecycle**

Startup order is database/lease, discovery/freeze, writer, feeds, status.
Shutdown order is stop admission, close epochs, flush one batch boundary,
persist state, release lease, stop status.

- [x] **Step 6: Run focused and full checks**

```powershell
python -B -m unittest `
  tests.a2.test_config `
  tests.a2.test_status_api `
  tests.a2.test_app -v
python -m compileall -q multi_exchange_engine tests
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero.

- [x] **Step 7: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/config.py `
  multi_exchange_engine/a2/status_api.py `
  multi_exchange_engine/a2/app.py `
  multi_exchange_engine/a2/__main__.py `
  tests/a2/test_config.py tests/a2/test_status_api.py `
  tests/a2/test_app.py handoff.md
git commit -m "feat: compose the A2 collector service"
```

---

### Task 10: Deterministic Replay and Fault Matrix

**Files:**

- Create: `multi_exchange_engine/a2/replay.py`
- Create: `scripts/replay-a2-run.py`
- Create: `tests/a2/test_replay.py`
- Create: `tests/a2/integration/test_replay_postgres.py`
- Create: `tests/a2/integration/test_fault_matrix.py`
- Modify: `multi_exchange_engine/a2/model.py`
- Modify: `multi_exchange_engine/a2/repository.py`
- Modify: `handoff.md`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ReplayIntegrity:
    run_id: UUID
    batch_count: int
    frame_count: int
    first_ingest_index: int
    last_ingest_index: int
    terminal_evidence_sha256: str
    integrity_state: Literal["VERIFIED", "FAILED"]
    reason_codes: tuple[str, ...]


def replay_run(
    repository: RawEvidenceRepository,
    run_id: UUID,
) -> ReplayIntegrity: ...
```

Replay streams one batch at a time, verifies compressed hash before
decompression, verifies uncompressed hash after decompression, strictly parses
every envelope, checks contiguous durable indexes and epoch-local frame
indexes, creates fresh venue observers per epoch, and compares reproduced
semantic observations with stored observations. It never builds an order book.

- [x] **Step 1: Write failing unit replay tests**

Cover valid multi-epoch evidence, gzip corruption, both hash mismatches,
truncation, appended bytes, duplicate/missing ingest index, epoch merge,
connection-frame gap, semantic mismatch, decoder-version mismatch, and bounded
iteration.

- [x] **Step 2: Write failing PostgreSQL/fault tests**

Inject PostgreSQL outage/recovery, queue saturation, WebSocket disconnect,
Lighter nonce gap/offset jump, Hyperliquid time regression, decoder schema
change, and process termination at both sides of a batch commit.

The already-binding `test_pipeline_postgres` crash/outage harness is reused
instead of copied. Focused Task 10 execution names that module explicitly;
`test_fault_matrix` binds it and injects the remaining cross-component faults.

- [x] **Step 3: Run RED**

```powershell
python -B -m unittest tests.a2.test_replay -v
python scripts/run-a2-postgres-tests.py `
  tests.a2.integration.test_replay_postgres `
  tests.a2.integration.test_fault_matrix `
  tests.a2.integration.test_pipeline_postgres
```

Expected: import failure for `replay`.

- [x] **Step 4: Implement bounded replay and canonical report**

`scripts/replay-a2-run.py` writes canonical JSON to stdout and diagnostics to
stderr without exposing connection data. Two fresh processes against the same
database snapshot must emit byte-identical stdout.

- [x] **Step 5: Run focused, repeatability, and full checks**

```powershell
python -B -m unittest tests.a2.test_replay -v
python scripts/run-a2-postgres-tests.py `
  tests.a2.integration.test_replay_postgres `
  tests.a2.integration.test_fault_matrix `
  tests.a2.integration.test_pipeline_postgres
python -m compileall -q multi_exchange_engine tests scripts
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all commands exit zero and both fresh-process report byte streams
match.

- [x] **Step 6: Update handoff and commit**

```powershell
git add -- multi_exchange_engine/a2/replay.py `
  scripts/replay-a2-run.py tests/a2/test_replay.py `
  tests/a2/integration/test_replay_postgres.py `
  tests/a2/integration/test_fault_matrix.py handoff.md
git commit -m "feat: replay and fault-test A2 evidence"
```

---

### Task 11: Forbidden-Capability Scan and Claim-Boundary Regression

**Files:**

- Create: `scripts/check-a2-boundary.py`
- Create: `tests/a2/test_dependency_boundary.py`
- Modify: `handoff.md`

**Boundary rules:**

- `multi_exchange_engine.a2` cannot import
  `multi_exchange_engine.domain.execution`, `multi_exchange_engine.shadow`, or
  any signer/account/trading SDK module;
- production A2 source cannot contain private endpoints or outbound message
  types for transaction, order, cancel, transfer, withdrawal, RFQ, account,
  position, fill, ledger, API key, signer, or auth token;
- only `aiohttp`, `psycopg`, and standard-library imports may cross the package
  boundary;
- URL literals in production A2 source must equal the four approved public
  constants;
- no `OrderBookSnapshot`, `LighterBookReducer`, `evaluate_pair`, or normalized
  book construction may appear in A2 source.

- [ ] **Step 1: Write mutation-tested failing boundary scan**

The test copies the A2 package to a temporary directory, inserts one forbidden
import/message/URL per subtest, and proves the scanner rejects each mutation.

- [ ] **Step 2: Run RED**

```powershell
python -B -m unittest tests.a2.test_dependency_boundary -v
```

Expected: import or file-not-found failure for the scanner.

- [ ] **Step 3: Implement AST and literal scan**

Do not use a raw substring scan alone. Parse imports and string constants so
comments cannot create false safety evidence.

- [ ] **Step 4: Run scanner and full checks**

```powershell
python scripts/check-a2-boundary.py
python -B -m unittest tests.a2.test_dependency_boundary -v
python -m compileall -q multi_exchange_engine tests scripts
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: scanner reports `A2_BOUNDARY_OK`; all commands exit zero.

- [ ] **Step 5: Update handoff and commit**

```powershell
git add -- scripts/check-a2-boundary.py `
  tests/a2/test_dependency_boundary.py handoff.md
git commit -m "test: enforce the A2 public-only boundary"
```

---

### Task 12: PostgreSQL CI, Hardened Python Image, SBOM, and Vulnerability Gate

**Files:**

- Create: `Dockerfile.a2`
- Modify: `.dockerignore`
- Modify: `.github/workflows/ci.yml`
- Create: `.github/workflows/build-a2-on-claw.yml`
- Create: `docs/a2-deployment.md`
- Create: `tests/a2/test_deployment_contract.py`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `handoff.md`

**Pinned images:**

```text
python:3.12.13-slim-bookworm@
sha256:d50fb7611f86d04a3b0471b46d7557818d88983fc3136726336b2a4c657aa30b

postgres:16.11-alpine@
sha256:4327b9fd295502f326f44153a1045a7170ddbfffed1c3829798328556cfd09e2

postgres:17.7-alpine@
sha256:bb377b7239d2774ac8cc76f481596ce96c5a6b5e9d141f6d0a0ee371a6e7c0f2

anchore/syft:v1.49.0@
sha256:13b53ebabe3d215268c90cf8fb9b875f0183908245f376fd4b3a2cb69d21d484

aquasec/trivy:0.72.0@
sha256:cffe3f5161a47a6823fbd23d985795b3ed72a4c806da4c4df16266c02accdd6f
```

Keep each `FROM` on one physical Dockerfile line; the wrapping above is
documentation only.

**Docker stages:**

```text
dependencies
  Install the exact `requirements-a2.txt` set into `/install`.

verify
  Copy source/tests/scripts and run unit tests, compileall, boundary scan,
  and `pip check`. PostgreSQL integration remains in CI service steps.

production
  Copy `/install`, the Python package, and migrations only; create UID/GID
  10001; set `org.opencontainers.image.revision` and
  `org.opencontainers.image.source`; expose 8081; run the module in exec
  form; use urllib healthcheck.
```

The production image has no compiler, shell startup script, Go binary, tests,
Git metadata, docs, credentials, or writable application directory.

- [ ] **Step 1: Write failing deployment-contract tests**

Parse Dockerfile/workflow text and assert pinned digests, non-root runtime,
exact test ordering, no venue secrets, no registry push, and no private/trading
runtime dependency.

- [ ] **Step 2: Run RED**

```powershell
python -B -m unittest tests.a2.test_deployment_contract -v
```

Expected: file-not-found failures for A2 image/CI artifacts.

- [ ] **Step 3: Generate Dockerfile, ignore rules, build workflow, and docs**

Use the `dockerfile-generator` security and Python multi-stage contract. Do not
modify the existing Go `Dockerfile`.

- [ ] **Step 4: Validate Dockerfile with the required validator loop**

Invoke `dockerfile-validator`; if unavailable, run its local script, then
Hadolint/Checkov if installed. Record up to three iterations in
`docs/a2-deployment.md`. Every warning is fixed or documented with risk,
mitigation, and review date.

- [ ] **Step 5: Extend CI in the design order**

The A2 job installs `requirements-a2.txt`, runs the complete PostgreSQL gate
against both pinned 16.11 and 17.7, runs unit/replay/fault/boundary suites,
builds `Dockerfile.a2 --target verify` and production, emits a CycloneDX SBOM
with pinned Syft, and fails on Trivy HIGH/CRITICAL findings. It never publishes
an image.

`build-a2-on-claw.yml` is manual-dispatch only, runs the same required gates on
`[self-hosted, claw]`, then builds local tag
`mee-a2:${{ github.sha }}` and updates local alias `mee-a2:candidate`. It never
starts a container and never pushes to a registry.

- [ ] **Step 6: Run local available checks**

```powershell
python -B -m unittest tests.a2.test_deployment_contract -v
python scripts/check-a2-boundary.py
python -m compileall -q multi_exchange_engine tests scripts
python -B -m unittest discover -s tests -t . -v
git diff --check
```

Expected: all available checks exit zero. If Docker is absent on Windows,
record that exact limitation; do not claim the image build passed there.

- [ ] **Step 7: Run Docker validation on Claw or CI**

```bash
docker build --target verify -f Dockerfile.a2 -t mee-a2:verify .
docker build -f Dockerfile.a2 -t mee-a2:candidate .
```

Expected: all commands exit zero. Run Syft and Trivy using the pinned images;
store non-secret reports as CI artifacts.

- [ ] **Step 8: Update docs/handoff and commit**

```powershell
git add -- Dockerfile.a2 .dockerignore .github/workflows/ci.yml `
  .github/workflows/build-a2-on-claw.yml docs/a2-deployment.md `
  README.md docs/architecture.md `
  tests/a2/test_deployment_contract.py handoff.md
git commit -m "build: package and verify the A2 collector"
```

---

### Task 13: Whole-Branch Adversarial Review and Release Candidate

**Files:**

- Modify only files with confirmed findings
- Modify: `handoff.md`

- [ ] **Step 1: Review every design statement against implementation**

Build a checklist for frozen universe, exact byte boundary, both venue
semantics, queue/persistence failure, clocks, replay, coverage, partitions,
retention, public-only endpoints, status API, n8n, Docker, and CI.

- [ ] **Step 2: Run adversarial mutations**

At minimum mutate one byte, one hash, one gzip trailer, one nonce, one source
time, one epoch, one ingest index, one UTC partition boundary, one coverage
slot, one endpoint, one outbound message type, and one Compose network. Each
mutation must fail for the intended typed reason.

- [ ] **Step 3: Run the complete release-candidate gate**

```powershell
python -m pip check
python scripts/check-a2-boundary.py
python scripts/run-a2-postgres-tests.py
python -m compileall -q multi_exchange_engine tests scripts
python -B -m unittest discover -s tests -t . -v
git diff --check
git status --short
```

On Claw/CI also run migration up/down/up, Docker verify/production builds,
Compose validation, SBOM generation, and Trivy. A cancelled, network-blocked,
or skipped gate remains unverified and blocks the release-candidate claim.

- [ ] **Step 4: Fix only confirmed findings and rerun the complete gate**

Do not fold A3 reconstruction, A1 live evaluation, Go/Rust parity, or any
trading method into review fixes.

- [ ] **Step 5: Update handoff and commit**

```powershell
git add -- handoff.md
git commit -m "fix: close A2 whole-branch review findings"
```

Before the first command, stage every confirmed source fix by its exact literal
path and verify `git diff --cached --name-only`; never use `git add -A` or
`git add .`. If review finds no source issue, commit only the evidence-bearing
handoff update with:

```powershell
git commit -m "docs: record A2 release-candidate verification"
```

---

### Task 14: Staged Claw Deployment Without Starting the Measured Run

**Files:**

- In `Dimkox/openclaw-airgap-farm`, create:
  `docker-compose.a2.yml`
- In `Dimkox/openclaw-airgap-farm`, create:
  `.github/workflows/deploy-a2.yml`
- In `Dimkox/openclaw-airgap-farm`, create:
  `n8n-workflows/a2-readonly-monitor.json`
- In `Dimkox/openclaw-airgap-farm`, create:
  `scripts/a2_db_bootstrap.sh`
- In `Dimkox/openclaw-airgap-farm`, create:
  `scripts/write_a2_clock_evidence.sh`
- In `Dimkox/openclaw-airgap-farm`, create:
  `systemd/mee-a2-clock-evidence.service`
- In `Dimkox/openclaw-airgap-farm`, create:
  `systemd/mee-a2-clock-evidence.timer`
- In `Dimkox/openclaw-airgap-farm`, create:
  `tests/test_a2_deployment_contract.py`
- In `Dimkox/openclaw-airgap-farm`, modify: `.env.example`
- In `Dimkox/openclaw-airgap-farm`, modify: `README.md`
- In `Dimkox/openclaw-airgap-farm`, modify: `handoff.md`
- In `Dimkox/multi-exchange-engine`, modify: `handoff.md`

- [ ] **Step 1: Push and build the engine release candidate on Claw**

```powershell
git push origin feature/a2-raw-wire-capture
& "C:\Program Files\GitHub CLI\gh.exe" workflow run `
  build-a2-on-claw.yml `
  --repo Dimkox/multi-exchange-engine `
  --ref feature/a2-raw-wire-capture
```

Expected: remote branch reaches the reviewed commit and the manual workflow
builds `mee-a2:candidate` locally on Claw without starting it.

- [ ] **Step 2: Create a fresh app-stack worktree from current remote main**

The local Windows clone currently diverges from the remote and must not be used
in place. Fetch `Dimkox/openclaw-airgap-farm`, create an isolated branch from
the refreshed `origin/main`, and read its README, handoff, deploy workflow,
Compose file, recent history, and status before editing.

- [ ] **Step 3: Add the isolated A2 Compose project**

`docker-compose.a2.yml` uses project name `mee-a2`, local image
`mee-a2:candidate`, and only external network `app-stack_airgap_net`. It
resolves `proxy-gateway:1080` and `postgres-db:5432`, declares no default/WAN
network, publishes no host port, and contains:

```yaml
read_only: true
user: "10001:10001"
cap_drop: ["ALL"]
security_opt: ["no-new-privileges:true"]
cpus: "2.0"
mem_limit: 512m
pids_limit: 128
tmpfs:
  - /tmp:size=32m,mode=1777
environment:
  HTTP_PROXY: http://proxy-gateway:1080
  HTTPS_PROXY: http://proxy-gateway:1080
  A2_PROXY_URL: http://proxy-gateway:1080
  A2_DATABASE_URL_FILE: /run/secrets/a2_database_url
  A2_CLOCK_EVIDENCE_FILE: /run/a2-clock/clock.json
  A2_REVIEWED_MAPPING_REGISTRY_FILE: /app/config/a2-reviewed-perpetual-mappings.json
  A2_REVIEWED_MAPPING_REGISTRY_SHA256: 8f17d2fb68518233e3de01af9ce202a5c6c5e1399e75673d72ce7d96fa2472c1
secrets:
  - a2_database_url
volumes:
  - /run/mee-a2/clock.json:/run/a2-clock/clock.json:ro
  - ${A2_REVIEWED_MAPPING_REGISTRY_HOST_PATH:?root-owned reviewed registry mount is required}:/app/config/a2-reviewed-perpetual-mappings.json:ro
expose:
  - "8081"
```

The secret source is
`/home/operator/app-stack/secrets/a2_database_url`; it is never committed. The
registry source path is provided only through
`A2_REVIEWED_MAPPING_REGISTRY_HOST_PATH`; before Compose validation it must be
an existing root-owned reviewed file whose SHA-256 exactly matches
`A2_REVIEWED_MAPPING_REGISTRY_SHA256`. Its target directory already exists in
the image and remains root-owned; the file bind must stay read-only. Do not
bake this registry into the image or replace the bind with a writable volume.
The separate Compose project prevents the main app-stack deploy's
`--remove-orphans` from deleting an active A2 soak.

- [ ] **Step 4: Add manual-only app-stack deployment and n8n observation**

`deploy-a2.yml` runs only by `workflow_dispatch`, checks that
`mee-a2:candidate` carries the requested engine commit label, validates
`docker-compose.a2.yml`, applies migrations, and supports exact phases
`fixture-start`, `fixture-stop`, `public-start`, `public-stop`, and `status`.
No push to app-stack `main` starts A2.

n8n reads `http://a2-collector:8081/v1/a2/soak-status` with GET and has no
credential or mutating node. Its imported workflow remains inactive.

- [ ] **Step 5: Validate app-stack source**

```powershell
python -B -m unittest discover `
  -s tests -p "test_a2_deployment_contract.py" -v
git diff --check
```

On Claw:

```bash
docker compose -p mee-a2 -f docker-compose.a2.yml config --quiet
```

Expected: all commands exit zero.

- [ ] **Step 6: Commit and push the app-stack integration**

```powershell
git add -- docker-compose.a2.yml .github/workflows/deploy-a2.yml `
  n8n-workflows/a2-readonly-monitor.json `
  scripts/a2_db_bootstrap.sh scripts/write_a2_clock_evidence.sh `
  systemd/mee-a2-clock-evidence.service `
  systemd/mee-a2-clock-evidence.timer `
  tests/test_a2_deployment_contract.py .env.example README.md handoff.md
git commit -m "feat: integrate the A2 collector on Claw"
git push origin HEAD
```

Open or fast-forward the reviewed app-stack change through its normal GitHub
flow. Do not edit `/home/operator/app-stack` outside the self-hosted deploy path.

- [ ] **Step 7: Validate Claw prerequisites read-only**

Verify `/home/operator/app-stack`, `proxy-gateway`, `postgres-db`,
`app-stack_airgap_net`, disk capacity for the bounded seven-day retention,
host time synchronization/error evidence, and Tailscale/LAN operator access.
Require working `chronyc -c tracking` with normal leap status. Install and
start the committed host timer, verify fresh `/run/mee-a2/clock.json`, and
block deployment rather than substitute an unqualified clock source. Do not
print `.env` or secret values.

- [ ] **Step 8: Create the dedicated database and secret boundary**

Create a non-login A2 schema-owner role and a login writer role with
`SELECT`/`INSERT` and only the required helper-function execution rights, no
update/delete, no superuser, and no access to venue/account tables. Write only
the writer DSN to
`/home/operator/app-stack/secrets/a2_database_url` with owner-only permissions.
`scripts/a2_db_bootstrap.sh` performs this idempotently with shell tracing
disabled, reads the existing PostgreSQL admin location without printing it,
and never echoes the generated DSN.

- [ ] **Step 9: Start with fixture feeds only**

Use the committed fake-feed mode, apply migrations, start the container, and
verify health/readiness/status, database lease, proxy-only DNS/egress, clean
restart, n8n GET-only observation, and zero direct route to venue hosts without
the proxy.

- [ ] **Step 10: Stop the fixture run at a batch boundary**

Replay all committed fixture evidence twice, compare canonical reports, verify
no partial batch, and leave the production measured run unstarted.

- [ ] **Step 11: Update engine handoff and commit deployment evidence**

Record commands, exit codes, image digest, migration state, non-secret network
evidence, replay hashes, resource measurements, and any blocker.

```powershell
git add -- handoff.md
git commit -m "docs: record A2 Claw fixture deployment"
git push origin feature/a2-raw-wire-capture
```

---

### Task 15: Public Warm-Up and Fixed Five-Day Measured Soak

**Files:**

- Modify only verified report/handoff artifacts
- Modify: `handoff.md`

- [ ] **Step 1: Create one run and freeze the universe**

Persist exact public discovery payload hashes and the ten ranked reviewed
mappings. Fail without starting warm-up if the count is not exactly ten.

- [ ] **Step 2: Run 60 contiguous valid warm-up minutes**

Observe through the GET-only status endpoint or n8n monitor. Any gap, restart,
clock failure, or persistence outage resets warm-up and is retained.

- [ ] **Step 3: Confirm the persisted measured window**

After warm-up, record one immutable `measured_start` and
`measured_end = measured_start + 432000 seconds`. Do not manually extend,
restart, or override it.

- [ ] **Step 4: Let the collector run through the fixed end**

Monitor health, disk, queue pressure, database readiness, typed failures, and
per-stream slot coverage without changing run state.

- [ ] **Step 5: Replay and decide after the half-open window closes**

Run deterministic replay twice, verify every batch and hash, calculate all
twenty L2 coverage values, test retention boundaries, and persist exactly one
immutable `PASS` or `FAIL`.

- [ ] **Step 6: Record the truthful A2 outcome**

The report must state the A2 claim boundary and all failed gates. A `PASS`
authorizes only planning A3 stateful reconstruction; it does not authorize
trading, production Go/Rust parity, or an arbitrage claim.

```powershell
git add -- handoff.md
git commit -m "docs: record the A2 measured soak outcome"
git push origin feature/a2-raw-wire-capture
```

---

## Final Self-Review Before Execution

- [ ] Every approved design requirement maps to one task and one test.
- [ ] Every production file has one responsibility and a named dependency
  direction.
- [ ] Every identifier, enum, schema/table, endpoint, interval, threshold,
  version, image, and environment variable is exact.
- [ ] No task reconstructs a book or invokes A1/shadow economics.
- [ ] Raw persistence is ordered before decoder success.
- [ ] Lighter `offset` is never a continuity key.
- [ ] Hyperliquid never receives a fabricated sequence.
- [ ] Queue/DB/clock/reconnect failures are typed and fail closed.
- [ ] PostgreSQL writes are append-only and duplicate conflicts compare bytes.
- [ ] The status and n8n surfaces are read-only.
- [ ] Venue credentials and private/trading methods are absent.
- [ ] PostgreSQL authentication uses only the dedicated app-stack secret file.
- [ ] Docker has a validator loop, SBOM, vulnerability gate, and no image
  publication.
- [ ] Windows without Docker is not reported as Docker-verified.
- [ ] Every significant checkpoint updates handoff, commits, pushes, and records
  a non-secret Basic Memory note.
