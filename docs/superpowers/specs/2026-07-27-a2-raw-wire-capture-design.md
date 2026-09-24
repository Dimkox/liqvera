# A2 Credential-Free Raw-Wire Capture Design

Date: 2026-07-27

Status: approved

## Objective

A2 must collect replayable public market-data evidence from Hyperliquid and
Lighter before any stateful book reconstruction or profitability claim.

The first run covers ten reviewed cross-venue-compatible linear perpetual
markets for exactly five measured days after a 60-minute warm-up. The market
universe is frozen at run start. A2 captures order-book, trade, and
market/funding channels without credentials or private exchange methods.

A2 exists to answer one question:

> Did the collector preserve enough authentic, ordered, timestamped evidence
> to reconstruct and audit both venues later without contacting them again?

It does not determine whether an arbitrage opportunity exists.

## Claim Boundary

An A2 `PASS` proves only:

- exact public application-message payloads were durably retained at the
  declared capture boundary;
- per-connection frame order, retained ingest order, and connection epochs are
  replayable;
- venue-specific continuity rules were applied without silent repair;
- clock, gap, reconnect, parse, backpressure, and persistence evidence exists;
- the fixed five-day capture met the stated completeness gates.

An A2 `PASS` does not prove:

- reconstructed order-book correctness;
- cross-venue causal alignment;
- A1 pair-domain parity over live venue data;
- executable prices, fills, expectancy, or revenue;
- signing, order placement, cancellation, reconciliation, or account safety;
- production Go parity or live-trading readiness.

A3 owns stateful reconstruction. Later shadow stages own economics.

## Approved Scope

### Venues

- Hyperliquid mainnet public REST and WebSocket APIs.
- Lighter mainnet public REST and WebSocket APIs.

Lighter may use its documented read-only WebSocket query mode when required by
the network route. No account token or API key is allowed.

### Frozen Market Universe

At run creation, discovery obtains current public market catalogs and 24-hour
quote volume from both venues.

A candidate is admitted only when reviewed mapping evidence proves:

- both contracts are linear perpetuals;
- both use the same base asset, one base-asset unit per displayed size, a
  `1x` linear multiplier, USDC settlement, and a USD-valued price;
- each venue's quote/oracle reference is recorded independently and the
  mapping carries the exact
  `EXPLICIT_ORACLE_STABLECOIN_BASIS/v1` risk policy;
- tick, lot, minimum quantity, and minimum notional are known;
- both venues report a valid positive 24-hour quote volume.

This compatibility contract does not assert identical oracle composition or
stablecoin exposure. Hyperliquid's USDT-denominated oracle convention and
Lighter's USD-index/USDC-PnL convention remain explicit basis-risk evidence.
A2 may compare the venues' reported USD-valued notionals for discovery
ranking, but later economics must not assume that this basis is zero.

Candidates are ranked by:

```text
shared_liquidity_score =
    min(hyperliquid_24h_quote_volume, lighter_24h_quote_volume)
```

Ties are resolved by canonical mapping ID in ascending byte order. A run fails
before warm-up when fewer than ten reviewed candidates exist. Volume values
must be positive venue-reported USD-valued notionals. A2 performs no FX
conversion and retains the quote-reference mismatch in the frozen manifest.

The top ten mappings are persisted with their discovery payload hashes and
frozen for the complete warm-up and measured run. Markets are not added,
removed, or reranked during a run.

This avoids survivor bias and gives every coverage calculation a fixed
denominator of twenty venue-market streams per required channel.

### Channels

For every frozen market, A2 captures:

- order-book data;
- public trades;
- public market statistics;
- published funding state or funding context.

Discovery and subscription acknowledgements are retained as control evidence.
Private user, order, position, fill, ledger, signing, transaction, transfer,
withdrawal, and RFQ channels are forbidden.

## Authoritative Venue Semantics

### Hyperliquid

The `l2Book` stream is treated as a sequence of complete order-book snapshots.
Each message replaces the previous observed book for that market in A3.

Hyperliquid does not expose a continuity nonce for this snapshot stream.
A2 must not invent one. It retains:

- exact frame bytes;
- venue source time when present;
- recorder wall and monotonic receive times;
- connection epoch and arrival index.

A non-monotonic source time invalidates the current epoch. Reconnect creates a
new epoch and recovery begins from a new full snapshot.

### Lighter

The `order_book/{market_index}` stream is treated as:

1. a complete snapshot after subscription; then
2. state-change batches, normally emitted every 50 milliseconds.

Continuity requires:

```text
current.begin_nonce == previous.nonce
```

`offset` belongs to an API server and may change across reconnects. It is
retained but is never used as the continuity identity.

Any nonce mismatch invalidates the epoch. Later deltas remain unusable until a
new complete snapshot opens a new valid epoch.

## Architecture

A2 is a credential-free Python modular monolith with isolated components:

1. `UniverseDiscovery`
   - obtains public catalogs and volume evidence;
   - validates reviewed mappings;
   - freezes the ten-market run manifest.
2. `HyperliquidRawCollector`
   - owns Hyperliquid public connections and subscriptions;
   - extracts only envelope metadata;
   - never reconstructs books.
3. `LighterRawCollector`
   - owns Lighter public connections and subscriptions;
   - classifies snapshot/delta messages and continuity;
   - never repairs or applies deltas.
4. `RawFrameBatcher`
   - assigns arrival indexes;
   - forms one-second batches without reordering frames;
   - emits immutable uncompressed and compressed hashes.
5. `RawEvidenceRepository`
   - performs append-only PostgreSQL writes;
   - owns UTC partitions, idempotency, and retention.
6. `SoakGate`
   - calculates coverage and integrity metrics from persisted evidence;
   - emits only `PASS` or `FAIL`.
7. `ReadOnlyStatusAPI`
   - exposes health, readiness, and soak progress;
   - cannot mutate the run or evidence.

The two venue collectors have separate bounded queues. A blocked queue is a
typed failure, not permission to drop or overwrite a frame.

## Capture Byte Boundary

The retained payload is the exact application-message byte sequence delivered
by the WebSocket library after TLS handling, WebSocket framing, and negotiated
WebSocket decompression, and before JSON parsing.

A2 does not claim to capture:

- TCP or TLS records;
- WebSocket frame headers or masking;
- the compressed on-network representation of a
  `permessage-deflate` message.

The run manifest records the WebSocket library, version, negotiated
extensions, message type, and this byte-boundary profile. Replay begins at
this application-message boundary.

## Raw Frame Envelope

Every received WebSocket text or binary frame is wrapped before semantic
decoding. Exact payload bytes are base64-encoded so JSON serialization cannot
change escaping or Unicode byte representation.

The immutable envelope contains:

```text
schema_version
run_id
boot_id
venue
market_identity
venue_market_id
channel
connection_epoch
connection_frame_index
ingest_index
received_wall_ns
received_monotonic_ns
recorder_clock_error_ms
source_timestamp_value
source_timestamp_unit
source_nonce
source_begin_nonce
source_offset
message_class
continuity_state
websocket_message_type
payload_encoding
payload_base64
payload_length
payload_sha256
```

Optional source fields are `null` when the venue does not supply them.
Absence is never represented by zero or a fabricated sequence.

`connection_frame_index` is contiguous only inside one connection epoch.
`ingest_index` is the single writer's retained total order. It is evidence of
local ingestion order, not a claim that independently received venue frames
have a source-causal global order. Cross-venue work must use clock-qualified
receive timestamps.

`message_class` is one of:

```text
CONTROL
SNAPSHOT
DELTA
TRADE
MARKET_STATS
FUNDING
UNKNOWN
```

`continuity_state` is one of:

```text
NOT_APPLICABLE
VALID
GAP_OPEN
AWAITING_SNAPSHOT
INVALID_SOURCE_TIME
```

Unknown and malformed messages are retained as raw evidence with a typed
decoder observation.

## Batch and Persistence Contract

Frames are serialized in retained `ingest_index` order as LF-only NDJSON. Each
line is one complete envelope. A batch normally spans one recorder second, but
size limits may close it earlier.

For every batch A2 calculates:

- SHA-256 over the exact uncompressed NDJSON bytes;
- gzip bytes using a frozen compression profile;
- SHA-256 over the gzip bytes;
- first and last ingest indexes;
- first and last wall and monotonic receive times;
- frame count and uncompressed/compressed byte counts.

The gzip profile is deterministic: fixed compression level, `mtime=0`, empty
filename and comment, and a pinned implementation/profile identifier in the
run manifest.

PostgreSQL table `raw_wire_batches` stores the gzip payload as `bytea` with
the metadata above. This name supersedes the unimplemented
`raw_l2_batches` name in the earlier Stage A draft because A2 also retains
trades and market/funding channels.

Supporting append-only tables are:

- `raw_capture_runs`;
- `raw_instrument_mappings`;
- `raw_control_evidence`;
- `raw_feed_connections`;
- `raw_decoder_observations`;
- `raw_quality_minutes`;
- `raw_soak_decisions`.

Time-series evidence is partitioned by UTC day. Raw batches retain seven
complete UTC days. Exact discovery response bytes, run manifests, processed
mapping evidence, quality summaries, hashes, and decisions are retained.
Discovery responses are strictly parsed and processed before one transaction
persists the raw control evidence and its hash-bound frozen universe. Neither
side may be persisted as a successful universe without the other.

The application role cannot update or delete evidence rows. Retention drops
only closed partitions outside an active run.

Duplicate batch identity is idempotent only when all hashes and byte counts
match. A conflicting duplicate is a hard integrity error.

## Failure Model

### Persist Before Continue

A frame is not acknowledged internally as captured until its batch is
durable. The batch writer must bound memory and report queue pressure.

When a queue cannot accept a frame or PostgreSQL cannot durably commit:

1. stop consuming the affected connection;
2. close its connection epoch with a typed reason;
3. retain any already committed batches;
4. reconnect only after persistence readiness returns;
5. require venue-specific recovery evidence.

Silent drop, overwrite, unbounded buffering, and best-effort continuation are
forbidden.

### Decoder Failure

Raw bytes are batched before decoder success is required. A schema or decoder
failure:

- retains the original frame;
- records the decoder version and typed error;
- marks the affected channel minute invalid;
- does not mutate earlier evidence.

### Reconnect and Gap Rules

Every reconnect creates a new `connection_epoch`.

- Hyperliquid recovers from a new complete snapshot.
- Lighter recovers from a new complete snapshot after subscription.
- Old and new epochs are never merged.
- A Lighter delta cannot close a gap.
- A failed frame cannot advance continuity state.

### Clock Rules

Collectors record wall and monotonic receive timestamps at the byte-receive
boundary.

- recorder clock error above 25 milliseconds invalidates temporal evidence;
- wall/monotonic divergence above 50 milliseconds closes the epoch;
- source timestamps are evidence, not substitutes for receive time.

A2 measures the existing later-stage thresholds:

- Hyperliquid maximum book age: 750 milliseconds;
- Lighter maximum book age: 200 milliseconds;
- maximum cross-venue receive-time skew: 250 milliseconds.

A2 does not use these values to construct or pair books. A3 owns that gate.

## Soak Lifecycle

One A2 run has immutable states:

```text
PLANNED
WARMING
MEASURING
PASS
FAIL
```

After discovery, storage, clock, and both venue collectors are ready, the run
requires 60 contiguous valid warm-up minutes. A gap, invalid clock, restart,
or persistence outage resets warm-up progress without deleting evidence.
Warm-up evidence is retained but excluded from the five-day denominator.

The measured window starts at a persisted UTC instant and ends exactly
432000 seconds later. Evidence belongs to the half-open interval
`[measured_start, measured_end)`. Report generation may happen later, but
restart does not extend or reset the window. A gap caused by restart counts
against coverage.

Only one process may own a run. Startup must detect and fail closed on
conflicting ownership.

## A2 Success Gate

A2 returns `PASS` only when every condition holds:

- measured duration is exactly five complete days after a completed warm-up;
- the frozen manifest contains ten reviewed common perpetual mappings;
- silent or overwritten frames equal zero;
- every committed batch passes gzip decode and both hash checks;
- replay reproduces frame bytes, ingest order, connection epochs, and gap
  classifications;
- every required venue-market L2 stream has at least 99.5 percent capture
  coverage;
- every reconnect, gap, decoder error, backpressure event, and persistence
  failure has a typed retained reason;
- restart recovery leaves no partially committed or contradictory batch;
- UTC partitions and seven-day raw retention behave at both boundaries;
- credential and private/trading endpoint scans are clean.

Capture coverage uses fixed one-second slots. A slot is valid only when the
subscription is acknowledged, its connection epoch is active, the recorder
clock is valid, persistence is ready, and no venue-specific continuity gap is
open. A quiet but healthy stream remains valid; message frequency is not used
as a proxy for continuity.

Trades and market/funding channels must remain subscribed and replayable, but
their message-frequency coverage is not compared with L2 frequency because a
valid quiet period can contain no event.

Any failed condition produces immutable `FAIL`. A2 has no `GO`, `EXTEND`, or
manual override state. Failed evidence remains available for diagnosis.

## Testing Strategy

### Unit and Property Tests

Tests cover:

- exact payload-byte preservation through base64 and NDJSON;
- per-connection and retained ingest ordering with bounded queues;
- Hyperliquid complete-snapshot classification;
- Lighter snapshot/delta classification and nonce continuity;
- unknown fields, malformed JSON, duplicate, and out-of-order frames;
- non-monotonic source time;
- reconnect and connection-epoch isolation;
- compression and both hash layers;
- immutable identifiers and conflicting duplicates;
- clock-step and wall/monotonic divergence;
- frozen-universe ranking and tie-breaking.

### PostgreSQL Tests

Tests use a real PostgreSQL instance and verify:

- migrations up and down;
- append-only triggers and application-role permissions;
- idempotent identical inserts and conflicting duplicate rejection;
- UTC partition creation;
- retention at both sides of the seven-day boundary;
- crash between staging and commit;
- restart without partial evidence.

`pgvector` is not used in A2. Raw evidence needs exact bytes and relational
integrity, not similarity search.

### Replay and Fault Tests

Pinned public-format fixtures cover both venues. Replay runs twice in fresh
processes and must produce byte-identical derived evidence.

Fault injection covers:

- PostgreSQL outage and recovery;
- queue saturation;
- WebSocket disconnect;
- Lighter nonce gap and server-offset change;
- Hyperliquid source-time regression;
- gzip corruption;
- frame and batch hash mismatch;
- decoder schema change;
- process termination at batch boundaries.

### CI Gates

CI runs in this order:

1. Python unit and property tests;
2. PostgreSQL migration and repository tests;
3. fake-feed replay and crash recovery;
4. credential/private-endpoint dependency scan;
5. Docker verify-stage build;
6. SBOM, dependency, and image vulnerability scans.

No image is published after a failed gate.

## Claw Deployment

A2 runs as one Python collector container under
`/home/operator/app-stack`.

The deployment contract requires:

- outbound traffic only through the existing `proxy-gateway`;
- membership in the intended `app-stack_airgap_net`;
- no direct default-bridge egress;
- PostgreSQL reachable only on the internal application network;
- non-root process;
- read-only root filesystem;
- dropped Linux capabilities;
- `no-new-privileges`;
- bounded CPU and memory based on fake-feed burst tests;
- no venue API keys, wallet/account secrets, or private-endpoint credentials;
- PostgreSQL authentication supplied only through the existing `/app-stack`
  secret/config boundary, never logged or written into captured evidence.

The container exposes only:

```text
GET /health
GET /ready
GET /v1/a2/soak-status
```

n8n may read these endpoints. It cannot start, stop, extend, pass, or fail a
run and cannot write evidence.

Rollout order is:

1. fixture-only CI;
2. local fake-feed run;
3. Claw deployment with no measured run;
4. 60-minute warm-up;
5. frozen five-day measured soak;
6. immutable report and handoff checkpoint.

## Non-Goals

A2 does not implement:

- stateful order-book reconstruction;
- normalized `OrderBookSnapshot` production from live feeds;
- cross-venue pairing or A1 evaluation;
- opportunity alerts or Telegram output;
- backtesting, prediction, or profitability scoring;
- account APIs, credentials, signing, orders, cancellation, or reconciliation;
- production Go or Rust collectors;
- pgvector;
- multi-host failover;
- n8n control over evidence or decisions.

## Source Contracts

The design is grounded in:

- Hyperliquid WebSocket, `l2Book`, subscription, and limit documentation under
  `https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api`;
- Lighter WebSocket reference:
  `https://apidocs.lighter.xyz/docs/websocket-reference`
- existing project contracts in `docs/five-day-stage-a-spec.md`;
- the A1 claim boundary in
  `docs/superpowers/specs/2026-07-26-a1-pair-domain-parity-tape-design.md`.

External documentation remains mutable. Implementation must pin representative
fixtures and record their retrieval date and hashes.

## Next Boundary

After A2 passes, A3 may reconstruct venue-native books from the retained raw
evidence and prove deterministic state hashes across replay, gaps, reconnects,
and process restarts.

A2 failure blocks A3 promotion but does not erase the captured evidence.
