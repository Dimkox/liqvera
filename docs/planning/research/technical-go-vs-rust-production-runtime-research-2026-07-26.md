---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 6
research_type: 'technical'
research_topic: 'Go vs Rust for the production hot path'
research_goals: 'Select by venue integration risk, latency, resource use, delivery cost, and maintainability while retaining Python for development and shadow validation'
user_name: 'Dmitry'
date: '2026-07-26'
web_research_enabled: true
source_verification: true
---

# Research Report: Go vs Rust for the production hot path

**Date:** 2026-07-26
**Author:** Dmitry
**Research Type:** technical

---

## Research Overview

This research selects the implementation boundary for a multi-exchange
arbitrage engine targeting Hyperliquid and Lighter first. It evaluates venue
SDK and protocol risk, deterministic recovery, tail latency, resource use,
delivery cost, and the ability to prove economic value before enabling private
trading.

The decision is **Python for research and shadow evidence, Go for the initial
production runtime, PostgreSQL for authoritative durable state, and Rust only
as a measured optimization escape hatch**. Go wins now because Lighter's
official reference signer is Go, a single Go process can own both venue state
machines without an IPC or FFI boundary, and the team can reach a reviewable
replay-tested runtime sooner. Rust remains technically credible, particularly
for Hyperliquid and tightly isolated compute kernels, but implementing a custom
Lighter signer before the trading thesis is proven would spend engineering
effort on protocol risk rather than revenue evidence.

The language decision does not validate the business. The next investment is
not private execution: it is a five-day credential-free shadow run that
measures executable, after-cost opportunities and produces a golden replay
corpus. Live paired execution is a separate go/no-go decision.

## Technical Research Scope Confirmation

**Research Topic:** Go vs Rust for the production hot path

**Research Goals:** Select by venue integration risk, latency, resource use,
delivery cost, and maintainability while retaining Python for development and
shadow validation.

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-07-26

## Technology Stack Analysis

### Programming Languages

The relevant stack is intentionally split by responsibility:

| Language | Proposed responsibility | Strongest evidence | Main risk |
|---|---|---|---|
| Python | Research, shadow execution, replay, fixtures, economics | Both initial venues publish Python SDKs | GC and dynamic typing are unnecessary risks in the final execution path |
| Go | Candidate production runtime for both venue adapters and coordination | Lighter publishes Go as one of its two public SDKs and calls `lighter-go` its reference signing and hashing implementation | Hyperliquid has no equivalent official Go SDK; signing and wire parity need golden vectors |
| Rust | Candidate production runtime or isolated optimized kernel | Hyperliquid publishes an official Rust trading SDK | No official Lighter Rust SDK was found; signing would require reimplementation or an additional language boundary |

Lighter officially lists only Python and Go SDKs. Its Go repository is the
reference implementation for transaction signing and hashing, while its Python
signer uses a binary built from that Go repository. Hyperliquid, conversely,
publishes a Rust SDK for API trading. This venue asymmetry is more important
than generic language benchmarks.

Sources:
[Lighter SDK list](https://apidocs.lighter.xyz/docs/repos),
[Lighter Go reference signer](https://github.com/elliottech/lighter-go),
[Lighter signer architecture](https://apidocs.lighter.xyz/docs/get-started),
[Hyperliquid Rust SDK](https://github.com/hyperliquid-dex/hyperliquid-rust-sdk).

**Confidence: high** for official SDK availability; **medium** for the effort
of a custom implementation until a signing parity spike is measured.

### Development Frameworks and Libraries

The Go path can use the existing standard-library service foundation,
`lighter-go` for Lighter signing, a deliberately narrow Hyperliquid transport
and signer, and `pgx` for PostgreSQL. `pgx` provides a native PostgreSQL
interface, pooling, batching, `COPY`, and `LISTEN`/`NOTIFY`.

The Rust path has a mature async stack: Tokio and Tokio Tungstenite are already
dependencies of the official Hyperliquid SDK, while SQLx provides async
PostgreSQL access and optional compile-time query checking. The missing
component is an authoritative Lighter Rust signer. A mixed Rust/Go runtime
would introduce FFI or IPC, two build systems, and another failure boundary.

Sources:
[pgx](https://github.com/jackc/pgx),
[SQLx](https://github.com/transact-rs/sqlx),
[Hyperliquid Rust SDK manifest](https://raw.githubusercontent.com/hyperliquid-dex/hyperliquid-rust-sdk/master/Cargo.toml).

**Preliminary stack fit:** Go is simpler across both venues; Rust is cleaner
for Hyperliquid alone.

### Database and Storage Technologies

PostgreSQL remains the authoritative durable store under either language.
Runtime selection does not justify changing the data model:

- in-memory single-writer book and risk state on the hot path;
- durable intent, ownership, idempotency, fill evidence, and reconciliation
  state in PostgreSQL;
- asynchronous batched market evidence where safety permits;
- synchronous persist-before-send for ownership and economic intent;
- pgvector restricted to offline research and incident similarity;
- no PostgreSQL or vector query in the per-tick opportunity decision.

Go's `pgx` and Rust's SQLx are both adequate. Database support is therefore not
a deciding factor. The deciding factor is preserving transaction boundaries
without allowing database latency into market-data processing.

Sources:
[pgx PostgreSQL features](https://github.com/jackc/pgx),
[SQLx PostgreSQL support](https://github.com/transact-rs/sqlx).

### Development Tools and Platforms

The repository already has a pinned Go 1.26.5 toolchain, unit tests, race-test
evidence, Docker verification, and a production-stage image. The current image
is 6,469,262 bytes, but that measurement covers the Stage 0 scaffold, not the
future two-venue hot path.

Rust would add Cargo, Clippy, Rustfmt, Tokio-aware tests, and an additional
container build cache. Cargo's own documentation recommends `cargo check` for
fast feedback and explicitly warns that build optimizations must be measured
against the actual workflow. Several faster compiler options remain nightly or
unstable.

AI-token and edit costs are not properties published by either language.
They must be treated as project estimates and measured using:

- number of edit/compile/test cycles per accepted change;
- wall-clock CI feedback;
- failed builds caused by type/lifetime/trait constraints;
- regression escape rate after review;
- tokens consumed per completed story.

The working estimate from three independent reviews is that Rust will require
more integration iterations initially. This is an inference, not benchmark
evidence.

Sources:
[Cargo build-performance guidance](https://doc.rust-lang.org/cargo/guide/build-performance.html),
[Go race detector](https://go.dev/doc/articles/race_detector).

### Cloud Infrastructure and Deployment

The target is the existing Claw Docker host, not a public cloud migration.
Both languages can produce compact containers, but only Go has repository and
Claw validation evidence today:

- pinned build and runtime images;
- non-root user;
- read-only and capability-dropped smoke test;
- static Stage 0 binary;
- approximately 6.17 MiB production image.

That static result must be revalidated after importing the real venue
dependencies. It must not be projected onto the completed engine.

The exchange dominates end-to-end latency. Lighter Standard documents 300 ms
taker latency and 200 ms maker/cancel latency. Therefore, a microsecond-scale
language advantage cannot be assumed to change fills without measured
opportunity-lifetime and missed-fill evidence.

Sources:
[Lighter account latency](https://apidocs.lighter.xyz/docs/account-types),
[Go garbage-collector guide](https://go.dev/doc/gc-guide).

### Technology Adoption and Decision Trends

Generic language popularity is not actionable for this project. The relevant
trend is venue-supported implementation:

- Hyperliquid reduces protocol risk for Rust through its official SDK.
- Lighter reduces protocol risk for Go through its reference signer.
- Python remains the fastest environment for changing research logic and
  producing deterministic golden fixtures.
- A full Rust rewrite would exchange possible lower runtime jitter for higher
  Lighter protocol and delivery risk.
- A later isolated Rust kernel remains viable if Go profiling proves a real
  local bottleneck.

### Step 2 Preliminary Finding

The stack evidence currently favors:

1. Python for research, shadow validation, and fixture generation.
2. Go for the first production implementation.
3. Rust only as a measured escape hatch for an isolated book/VWAP/decision
   kernel.

This is not the final architecture decision. Integration, failure boundaries,
implementation cost, and replay benchmarks remain to be assessed in later
steps.

## Integration Patterns Analysis

### API Design Patterns

The engine should use direct typed venue adapters, not a generic API gateway.
Each adapter exposes the same internal capabilities while preserving
venue-specific semantics:

- public instrument discovery;
- public market-data subscription and snapshot recovery;
- account and order-state queries;
- sign and submit;
- exact-owned cancel;
- authoritative reconciliation.

Hyperliquid exposes REST and WebSocket APIs. Transactions sent to an API server
are forwarded to its node, gossiped through HyperBFT, and answered after
inclusion in a committed block. Lighter exposes REST and WebSocket transaction
submission, but explicitly states that API acceptance does not guarantee
sequencer execution.

Therefore, an HTTP 200 or WebSocket acknowledgement is only transport
acceptance. The internal contract must return `accepted`, `rejected`, or
`unknown`, with terminal state determined later from authoritative order and
fill data.

Sources:
[Hyperliquid API servers](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers),
[Hyperliquid exchange endpoint](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint),
[Lighter transaction signing and acceptance](https://apidocs.lighter.xyz/docs/trading).

### Communication Protocols

#### Market data

Each venue requires a different recovery state machine:

- Hyperliquid warns that server-side disconnects may occur without notice.
  Reconnect acknowledgements include snapshots, and missing information can
  also be queried through the corresponding REST info request.
- Lighter sends a complete order-book snapshot on subscription and then
  batched changes every 50 ms. Book continuity is proven when the next
  `begin_nonce` equals the previous `nonce`. `offset` may change after
  reconnect and is not guaranteed continuous.

The normalized book consumer must therefore never assume that a generic
monotonic sequence exists across venues. Each adapter owns its native
continuity proof and emits either:

- a valid normalized snapshot;
- a valid ordered update;
- `GAP_DETECTED`, which invalidates the book until a fresh snapshot.

One goroutine or async task reads each socket. All writes on a socket pass
through one serialized writer. Ping/pong, reconnect, resubscribe, and snapshot
gating are adapter responsibilities. A full or blocked internal queue is a
data-integrity failure: the affected book becomes unusable instead of silently
dropping an update.

Sources:
[Hyperliquid WebSocket reconnect behavior](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket),
[Hyperliquid heartbeats](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/timeouts-and-heartbeats),
[Lighter WebSocket continuity](https://apidocs.lighter.xyz/docs/websocket-reference).

#### Trading requests

Submission should use one transport per venue behind the same state-machine
contract. REST versus WebSocket is a benchmarkable transport choice, not a
change to execution semantics.

Lighter supports `sendTx` and `sendTxBatch` over both transports. Hyperliquid
supports trading through its exchange REST endpoint and WebSocket posting.
Rate limits apply across transports, so changing transports does not create
extra capacity.

Sources:
[Lighter WebSocket sendTx](https://apidocs.lighter.xyz/docs/websocket-reference),
[Lighter rate limits](https://apidocs.lighter.xyz/docs/rate-limits),
[Hyperliquid rate limits](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits).

### Data Formats and Standards

External venue messages are JSON, but prices and quantities must not enter the
domain as binary floating-point values. The adapter converts strings and
venue-native integer ticks/lots into typed fixed-point values while checking:

- price and quantity scale;
- contract multiplier;
- minimum quantity and notional;
- side and position sign;
- timestamp unit;
- market and account identity.

The Python-to-production interoperability boundary is a versioned golden-event
file, not a runtime call. A fixture contains raw venue messages, normalized
events, decisions, fixed-point values, and final state hash. Go and any future
Rust kernel must reproduce the same result exactly.

This removes Python from production latency and prevents FFI, RPC, or a Python
sidecar from becoming an execution dependency.

### System Interoperability Approaches

The production engine should remain a modular monolith:

```text
venue WS/REST
    -> venue adapter
    -> normalized event
    -> single-writer book
    -> opportunity/risk reducer
    -> durable execution intent
    -> signer and submitter
    -> authoritative reconciliation
    -> PostgreSQL evidence
```

No service mesh, message broker, or network RPC belongs inside this path.
PostgreSQL is the durable coordination boundary; in-memory bounded channels are
the process-local boundary.

Four runtime combinations were evaluated:

| Runtime | Hyperliquid integration | Lighter integration | New boundary |
|---|---|---|---|
| Go only | Custom Go implementation verified against official SDK vectors | Official Go reference signer | None |
| Rust only | Official Rust SDK | Custom Lighter signer | None, but high protocol risk |
| Rust plus Go signer | Official Rust SDK | Official Go signer | FFI or IPC |
| Go plus Rust SDK | Rust SDK wrapper | Official Go signer | FFI or IPC |

Hyperliquid explicitly recommends using an existing SDK because signing has two
schemes and is sensitive to MessagePack field order, trailing zeroes, and
address casing. A Go implementation is therefore permitted only with official
Python/Rust wire and signature vectors.

Lighter signing is anchored in its Go reference implementation and uses
API-key-specific nonce behavior. Reimplementing it in Rust would create the
larger protocol-risk surface. Consequently, a single Go runtime currently has
the fewest dangerous integration boundaries.

Sources:
[Hyperliquid signing pitfalls](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing),
[Hyperliquid Rust SDK](https://github.com/hyperliquid-dex/hyperliquid-rust-sdk),
[Lighter Go reference implementation](https://github.com/elliottech/lighter-go).

### Execution Saga and Event-Driven Integration

Paired execution is a durable saga, not a database transaction spanning two
venues:

1. validate synchronized executable books and reserve risk;
2. persist execution group, both legs, ownership IDs, and idempotency keys;
3. submit the first approved action;
4. reconcile any timeout or ambiguous response before retrying;
5. submit or abort the hedge according to the explicit execution policy;
6. reconcile both legs from authoritative orders and fills;
7. reduce residual delta or freeze the account;
8. close the lifecycle only when terminal state and after-cost P&L are proven.

There is no automatic retry of an unknown submission. Outbox workers may retry
transport delivery only after reconciliation proves the economic action absent.
Exact-owned cancel is allowed; cancel-all is outside the normal execution path.

Market-data events can be batched asynchronously for evidence. Intent,
ownership, nonce reservation, submission outcome, and reconciliation events
must be durable and append-only.

### Nonce Ownership

Nonce handling requires a single writer per credential identity:

- Lighter maintains a separate nonce per API key and normally requires exact
  increment-by-one behavior. API acceptance and sequencer rejection affect
  nonce consumption differently.
- Hyperliquid tracks nonces per signer. Its documentation recommends a separate
  API wallet per trading process and an atomic counter, with batched order and
  cancel requests.

Nonce reservation, signed payload identity, and ownership must be persisted
before sending. Restart recovery loads the last authoritative state and blocks
new submission until conflicts are reconciled.

Sources:
[Lighter nonce management](https://apidocs.lighter.xyz/docs/api-keys),
[Lighter rejection and nonce behavior](https://apidocs.lighter.xyz/docs/trading),
[Hyperliquid nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets).

### Integration Security Patterns

- Public discovery uses no trading credentials.
- Lighter read-only tokens are used for auth-gated observation where needed.
- Trading credentials are injected at runtime and never written to fixtures,
  logs, PostgreSQL plaintext, images, Git, or research documents.
- Lighter API keys can authorize trading and some withdrawal operations, so
  compromise impact is materially greater than a market-data token.
- Hyperliquid uses a dedicated API wallet per isolated trading process.
- Signed payload hashes and non-secret ownership identifiers may be retained
  for audit; private keys and raw authorization headers may not.
- All outbound venue traffic on Claw follows the existing `/app-stack` proxy
  and external-network contract and fails closed if that route is unavailable.

Sources:
[Lighter API-key permissions and read-only tokens](https://apidocs.lighter.xyz/docs/api-keys),
[Hyperliquid API-wallet guidance](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets).

### Step 3 Finding

Integration risk strengthens the preliminary Go direction. Rust offers the
official Hyperliquid client, but lacks the authoritative Lighter signer. A
hybrid runtime would add FFI or IPC to the most safety-critical path. The
lowest-boundary design is:

1. Python generates replay and signing fixtures offline.
2. One Go production process owns both venue adapters and the execution saga.
3. PostgreSQL is the only durable coordination boundary.
4. Rust remains an optional in-process or side-by-side benchmark kernel only
   after the normalized-event contract is frozen.

## Architectural Patterns and Design

### System Architecture Pattern

The target architecture is a modular monolith with hexagonal venue adapters
and actor-like single-writer state ownership.

The monolith is preferable to microservices because the initial system has two
venues, one execution coordinator, and one Claw host. Splitting book, risk,
signing, and reconciliation into network services would add serialization,
deployment, clock, and partial-failure boundaries before there is a measured
scaling need.

Modules remain independently testable:

```text
discovery
  -> market-data adapters
  -> normalized book reducers
  -> equivalence and executable-VWAP selector
  -> risk and reservation
  -> paired execution saga
  -> venue signing/submission
  -> reconciliation and residual-delta control
  -> PostgreSQL evidence/outbox
```

Each mutable market book, credential nonce, account execution queue, and
execution group has exactly one logical writer. Other modules communicate by
immutable commands and events. This follows Go's own memory-model advice to
serialize shared writes with channels or synchronization primitives. Rust
would enforce more ownership constraints at compile time, but it would not
remove economic-ordering races such as fill-versus-cancel or duplicate intent.

Sources:
[Go memory model](https://go.dev/ref/mem),
[Rust concurrency model](https://doc.rust-lang.org/book/ch16-00-concurrency.html).

### Design Principles and Best Practices

The architectural invariants are:

1. **Determinism:** identical normalized input produces identical fixed-point
   decisions and state hashes in Python, Go, and any future Rust kernel.
2. **Fail closed:** stale, gapped, contradictory, or unowned state cannot
   create or cancel an order.
3. **Reconcile before retry:** a timeout is `unknown`, never equivalent to
   rejection.
4. **Persist before send:** ownership, economic intent, idempotency identity,
   nonce reservation, and signed-payload identity are durable before network
   submission.
5. **Exact ownership:** normal cancellation targets one proven bot-owned order;
   cancel-all is an explicit emergency operation.
6. **No floating point:** price, size, fee, funding, collateral, and P&L use
   typed integer scales with checked arithmetic.
7. **No secret-bearing evidence:** fixtures, events, traces, and logs contain
   identifiers and hashes, never private keys or authorization values.
8. **No semantic AI in execution:** pgvector and language models cannot approve
   an order or change risk state.

The domain interfaces are small and venue-neutral, while parsing, continuity,
signing, and reconciliation remain venue-specific. A "universal adapter" must
not erase differences in nonce consumption, acknowledgement meaning, position
sign, or order identity.

### Scalability and Performance Patterns

The first scaling strategy is bounded vertical scaling on Claw, not
distribution:

- one dedicated market-data task per venue connection;
- one single-writer reducer per book shard;
- immutable snapshot publication to readers;
- preallocated normalized events and reusable decode buffers where profiling
  proves value;
- bounded queues with explicit overload state;
- asynchronous, batched evidence writes;
- synchronous PostgreSQL only at safety-critical execution transitions;
- no pgvector, report generation, or LLM call in the decision path.

Unbounded queues are rejected for either language. Tokio's documentation
explicitly warns that unbounded queues eventually exhaust memory; the same
architectural rule applies to Go channels.

Go runtime tuning is downstream of measurement. `GOMEMLIMIT` is soft, and the
official GC guide recommends leaving container headroom. A near-zero-allocation
hot loop, runtime metrics, pprof profiles, and cgroup CPU/pressure measurements
come before GC flags or a Rust rewrite.

Sources:
[Tokio bounded-channel guidance](https://tokio.rs/tokio/tutorial/channels),
[Go GC guide](https://go.dev/doc/gc-guide),
[Go diagnostics and pprof](https://go.dev/doc/diagnostics),
[Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).

#### Proposed performance budgets

These are project gates, not measured facts:

| Stage | Initial budget |
|---|---:|
| decoded venue frame to normalized event p99.9 | <= 500 microseconds |
| normalized event to decision p99.9 | <= 500 microseconds |
| internal queue delay p99.9 | <= 1 millisecond |
| dropped or silently overwritten authoritative events | 0 |
| Go hot-loop allocations after warm-up | measured and driven toward 0 |
| sustained benchmark load | at least 5x observed peak |

Rust is reconsidered only if the Go implementation, after profiling and
allocation reduction:

- spends more than 1 ms p99.9 locally or more than 10% of profitable
  opportunity lifetime;
- loses economically valid opportunities because of local GC/scheduling;
- runs above 70% assigned CPU or violates the agreed memory ceiling; and
- a parity-preserving Rust kernel materially improves the economic result,
  with a target of at least 25% better p99.9 or CPU/RSS and at least 30%
  recovery of locally missed opportunities.

A faster synthetic loop without better end-to-end economics does not satisfy
the gate.

### Integration and Communication Patterns

Process-local communication uses bounded typed channels. PostgreSQL outbox rows
bridge durable state transitions to background work. There is no Kafka, NATS,
Redis, gRPC, service mesh, or internal HTTP in the initial production topology.

Market-data overload has a different policy from durable execution:

- public book backlog invalidates the book and triggers resnapshot;
- risk and execution commands apply backpressure and freeze new submissions;
- durable outbox delivery is retryable;
- unknown venue effects are not retried until reconciled.

Graceful shutdown stops new opportunity intake, freezes submission, drains only
bounded safe work, persists checkpoints, and leaves unresolved executions in a
reconcilable state. It does not wait indefinitely for a venue.

### Security Architecture Patterns

Credential and network blast radius are explicit:

- one dedicated Hyperliquid API wallet per trading process/account boundary;
- one Lighter nonce coordinator per `(account_index, api_key_index)`;
- public/read-only discovery separated from private execution clients;
- runtime secret injection only;
- no credentials in Git, images, PostgreSQL plaintext, logs, fixtures, or
  Basic Memory;
- withdrawal and transfer methods are absent from the engine interface;
- outbound traffic follows the Claw `/app-stack` proxy contract;
- the engine joins only the intended external airgap network;
- direct container egress fails closed;
- non-root runtime, read-only filesystem, dropped capabilities, and
  `no-new-privileges`.

An exposed credential is treated as compromised regardless of whether it still
authenticates. Rotation is an operational incident, not an application
fallback.

### Data Architecture Patterns

PostgreSQL is authoritative for:

- execution groups and legs;
- risk reservations;
- order ownership and client identifiers;
- nonce reservations and signed-payload hashes;
- submissions, orders, fills, fees, and funding;
- append-only execution events;
- outbox delivery state;
- audit records and lifecycle P&L.

One transaction creates the economic intent, both leg records, risk
reservation, ownership identity, and outbox command. Transaction-level row or
advisory locks enforce one writer for an account/credential boundary.
Serializable isolation is reserved for invariants that actually require it,
and callers must handle `40001` retries before any external send. Database
transaction retry is never equivalent to venue-action retry.

Sources:
[PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html),
[PostgreSQL advisory locks](https://www.postgresql.org/docs/current/functions-admin.html).

pgvector is an offline evidence facility:

- incident and research embeddings may share a dimensionless `vector` column
  until a model and dimension are selected;
- model ID, dimension, content hash, source, tenant, and metadata are stored
  alongside every embedding;
- no ANN index is created before real volume and recall requirements exist;
- no vector query participates in market selection, risk, execution, or
  reconciliation.

The pgvector project supports a dimensionless column and model-specific partial
indexes, which avoids guessing an embedding dimension now.

Source:
[pgvector storage and indexing](https://github.com/pgvector/pgvector).

### Deployment and Operations Architecture

The production unit is one versioned Go binary and PostgreSQL migrations in a
pinned multi-stage Docker build. Python tooling remains in development and CI,
not in the production image.

Claw deployment must provide:

- connection to the existing external `app-stack_airgap_net`;
- proxy environment routed to `proxy-gateway`;
- no direct default-bridge egress;
- PostgreSQL reachable only on the internal application network;
- explicit CPU and memory limits based on replay/soak evidence;
- health that distinguishes process liveness, database readiness, venue-feed
  readiness, and safe-to-submit state;
- `ENGINE_MODE=shadow` and live execution disabled by default;
- immutable image identity, SBOM, vulnerability scan, and provenance before
  promotion.

Docker enables outbound access by default on its standard bridge, so the
external-network and proxy contract must be tested, not assumed.

Sources:
[Docker networking](https://docs.docker.com/engine/network/),
[Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).

### Step 4 Architectural Finding

The production architecture should be:

> Python development and evidence pipeline, one Go modular monolith for the
> complete safety-critical runtime, PostgreSQL for durable truth, pgvector for
> offline research only, and Rust reserved behind a deterministic kernel
> contract if measured Go limits justify it.

This structure minimizes runtime boundaries while preserving a future
performance escape hatch. It also makes the cheapest next action clear:
complete the Python shadow/economics evidence and Go golden-fixture contract
before implementing live paired execution.

## Implementation Approaches and Technology Adoption

### Technology Adoption Strategy

The migration is a strangler process around deterministic behavior, not a
line-by-line Python rewrite:

1. Python remains the fastest place to develop venue normalization, shadow
   economics, and adversarial fixtures.
2. A versioned golden-event schema freezes inputs, normalized outputs,
   decisions, money values, and terminal state hashes.
3. Go implements one domain slice at a time and must reproduce every accepted
   Python fixture exactly.
4. Go becomes the production owner of a slice only after parity, race, fuzz,
   replay, restart, and fault-injection gates pass.
5. Python remains a non-production oracle after the Go cutover.
6. Rust is not added until a measured Go performance gate fails.

The repository currently contains 1,830 lines of Python reference code, 1,319
lines of Python tests, and 2,102 lines of Go scaffold and tests. The Python
suite has 42 passing tests. These counts describe current scope; they are not
productivity or quality metrics.

### Development Workflow and Tooling

Each significant story follows:

1. define or extend a Python golden fixture;
2. add a failing Go parity or state-machine test;
3. implement the smallest Go change;
4. run formatting, vet, unit, race, and targeted fuzz seeds;
5. run the immutable replay corpus;
6. inspect allocation, queue-delay, and p99.9 changes;
7. build and scan the container;
8. commit the story with evidence and handoff state.

The current Go CI already performs formatting, vet, race tests, coverage,
binary build, and Docker verify-stage build. It should be extended rather than
replaced.

Dependency caches may accelerate CI, but GitHub documents that restored caches
must be treated as untrusted and must never contain secrets. Artifacts, golden
corpora, logs, and benchmark reports are separate from reusable dependency
caches.

Sources:
[GitHub dependency caching](https://docs.github.com/en/actions/concepts/workflows-and-actions/dependency-caching),
[Cargo build feedback](https://doc.rust-lang.org/cargo/guide/build-performance.html).

### Testing and Quality Assurance

The required test pyramid is domain-specific:

| Lane | Required evidence |
|---|---|
| Python reference | unit tests, malformed venue messages, shadow economics |
| Golden parity | identical normalized events, decisions, money, and state hash |
| Go unit/property | fixed-point overflow, scale, sorting, VWAP, risk invariants |
| Go fuzz | JSON decoders, scale conversion, sequence/gap reducers, state transitions |
| Go race | concurrent WS, queue, account, nonce, and reconciliation paths |
| PostgreSQL | migrations up/down, RLS, locks, outbox claim, crash/restart |
| Contract | pinned official request/response and signature vectors |
| Replay | real bursts, reconnect, gaps, duplicate and out-of-order events |
| Chaos | timeout-after-accept, partial fill, cancel/fill race, DB interruption |
| Soak | 30-minute sustained and 6-hour burst/reconnect run |

Go fuzzing is built into the standard toolchain and persists failing inputs as
regression seeds. The race detector executes only observed paths and carries
substantial overhead, officially estimated at 2–20 times execution time and
5–10 times memory. Therefore, realistic race-built replay runs belong on Claw
or a scheduled CI lane, while focused race tests remain on every pull request.

If a Rust kernel is later introduced, its equivalent lane adds Rustfmt, Clippy,
tests, `#![forbid(unsafe_code)]`, and Miri where applicable. Miri is an
experimental undefined-behavior checker, not proof of economic or concurrency
correctness.

Sources:
[Go fuzzing](https://go.dev/doc/security/fuzz/),
[Go race detector](https://go.dev/doc/articles/race_detector),
[Clippy](https://doc.rust-lang.org/stable/clippy/usage.html),
[Rustup Miri component](https://rust-lang.github.io/rustup/concepts/components.html).

### Deployment and Operations Practices

Promotion stages are:

1. fixture-only development;
2. credential-free public-data shadow;
3. recorded replay on Claw;
4. testnet/private API conformance with live execution disabled by default;
5. isolated manual-confirm canary only after economic and business gates;
6. bounded automation after incident-free canary evidence.

Every release artifact is built from a commit, addressed by image digest, and
accompanied by:

- test and replay report;
- benchmark delta;
- migration plan and rollback;
- SBOM;
- provenance;
- vulnerability scan;
- configuration schema version.

Docker BuildKit can attach SBOM and provenance attestations. Build arguments
must not carry credentials because provenance may expose build-argument values;
runtime secrets or BuildKit secret mounts are required instead.

Sources:
[Docker build attestations](https://docs.docker.com/build/metadata/attestations/),
[Docker GitHub Actions attestations](https://docs.docker.com/build/ci/github-actions/attestations/).

### Team Organization and Skills

The minimum maintainable team shape is:

- one Go engineer owning runtime and operational response;
- one exchange-protocol reviewer capable of validating signing, nonce, order,
  fill, and reconciliation semantics;
- Python research capability for fixtures and shadow economics;
- PostgreSQL competence for locks, idempotency, outbox, migrations, and
  incident recovery.

One person may cover several roles, but review independence is required for
signing, nonce, and unknown-outcome changes.

A full Rust runtime additionally requires production Rust async, crypto/wire
protocol, and Rust incident-response competence. Without at least two people
able to debug the runtime, Rust creates unacceptable key-person risk.

### Cost and Resource Management

No credible CPU, RAM, CI, or AI-token total exists before the replay corpus and
real adapter dependency graph exist. The project will measure instead of
guessing:

- wall-clock edit-to-green time per story;
- compile/test iterations per accepted commit;
- CI CPU-minutes and peak memory;
- AI tokens per completed story;
- code-review findings and escaped defects;
- binary/image size;
- CPU milliseconds per million normalized messages;
- RSS/PSS peak;
- allocations per message;
- p50, p95, p99, and p99.9 stage latency;
- economically valid opportunities missed by local processing.

Planning estimates, explicitly not benchmark facts:

- Rust async exchange integration is expected to need 1.5–2.5 times more
  compile/fix iterations initially.
- Total AI-token use for a full Rust runtime is expected to be 30–70% higher
  than Go for the current team and SDK asymmetry.
- Rust may later reduce CPU, memory, or tail jitter, but that benefit has no
  economic value unless it recovers real opportunities.

The cheapest resource strategy is to avoid a second production toolchain until
Go fails a measured gate.

### Risk Assessment and Mitigation

| Risk | Current level | Mitigation |
|---|---|---|
| No executable after-cost edge | Critical | Five-day and fourteen-day shadow gates before live work |
| Protocol drift | High | Pin SDK/docs, contract captures, scheduled conformance |
| Hyperliquid Go signing divergence | High | Official Python/Rust golden wire and signature vectors |
| Custom Lighter Rust signer | Critical | Do not implement unless official support or audited parity exists |
| Unknown submission duplication | Critical | Persist-before-send and reconcile-before-retry |
| Go data race | High | Single-writer ownership, bounded channels, race-built replay |
| GC or scheduler tail | Unproven | Near-zero-allocation design, pprof/runtime metrics, Rust gate |
| Credential compromise | Critical | Runtime injection, rotation, least capability, no persistence |
| Direct container egress | High | `/app-stack` proxy/network contract and negative egress test |
| Database split brain | Critical | Account/credential locks, idempotency, one active writer |

## Technical Research Recommendations

### Implementation Roadmap

The following durations are engineering estimates for one experienced
developer assisted by agents, not commitments:

| Phase | Deliverable | Estimate |
|---|---|---:|
| 0 | Python public-data shadow and golden corpus | 5–7 days |
| 1 | Go book/VWAP/decision golden parity | 2–4 days |
| 2 | Go Hyperliquid and Lighter public WS | 3–5 days |
| 3 | PostgreSQL repositories, outbox, locks, nonce ownership | 3–5 days |
| 4 | Private signing, submit, and reconciliation | 5–8 days |
| 5 | Fault injection, soak, Docker release evidence | 3–5 days |

A defensible live paired-execution MVP is therefore roughly three to five
weeks after the shadow thesis passes. Claiming five days for live execution
would omit safety and evidence work.

### Technology Stack Recommendation

- Python 3.12+ for reference, shadow, replay, fixtures, and reports.
- Go 1.26.x for the production runtime.
- PostgreSQL 18 with SQL migrations and `pgx`.
- pgvector installed but isolated to offline evidence.
- Docker/Compose on Claw using the `/app-stack` network and proxy contract.
- Rust absent from production dependencies until the benchmark gate is met.

### Skill Development Requirements

- Go concurrency and memory model;
- fixed-point financial arithmetic;
- Hyperliquid and Lighter signing/nonce semantics;
- PostgreSQL locking, idempotency, and recovery;
- deterministic replay and latency histograms;
- container hardening and supply-chain evidence;
- incident response for partial fills and unknown outcomes.

### Success Metrics and KPIs

Implementation is successful only when:

- Python/Go golden parity is 100%;
- authoritative event loss is zero;
- all unknown-outcome and restart scenarios converge or freeze safely;
- no unowned cancel or duplicate economic intent is possible in tests;
- 5x observed burst stays within agreed p99.9/CPU/RSS budgets;
- the five-day and fourteen-day after-cost shadow gates pass;
- canary execution has complete order/fill/fee/P&L evidence;
- operator revenue remains positive without destroying trader edge.

---

## Final Research Synthesis

### Executive Summary

**Decision:** build the first production hot path as a modular Go monolith.
Keep Python as the reference implementation and evidence workbench. Keep
PostgreSQL as the only authoritative durable state boundary. Restrict pgvector
to offline research and incident similarity. Do not introduce Rust into the
production dependency graph until Go fails an explicit measured gate.

The decisive fact is not a generic language benchmark. It is the asymmetric
venue support:

- Lighter publishes Python and Go SDKs and identifies `lighter-go` as its
  reference signing and hashing implementation.
- Hyperliquid publishes an official Rust SDK, while a Go adapter needs narrow
  custom signing and wire compatibility verified against official fixtures.
- Choosing Go contains custom protocol work to one venue. Choosing Rust moves
  custom signing risk to Lighter, the venue whose official signing reference is
  Go. A Go/Rust hybrid creates a third failure surface at the IPC or FFI
  boundary.

Rust may eventually produce lower allocation rates, memory use, or latency
jitter. None of those benefits are currently connected to measured missed
profit. Starting with Rust now would optimize an unproven engine while delaying
the only evidence that matters: executable spread after fees, slippage,
funding, fill uncertainty, and reconciliation costs.

**Immediate recommendation:** complete the five-day public-data shadow gate and
golden corpus before porting private execution. If the economics fail, stop.
If they pass, migrate deterministic slices to Go through fixture parity,
replay, race, fuzz, restart, and chaos gates. Enable private methods only after
unknown-outcome reconciliation and exact-owned cancellation are proven.

### Table of Contents

1. [Technical Research Scope Confirmation](#technical-research-scope-confirmation)
2. [Technology Stack Analysis](#technology-stack-analysis)
3. [Integration Patterns Analysis](#integration-patterns-analysis)
4. [Architectural Patterns and Design](#architectural-patterns-and-design)
5. [Implementation Approaches and Technology Adoption](#implementation-approaches-and-technology-adoption)
6. [Technical Research Recommendations](#technical-research-recommendations)
7. [Final Research Synthesis](#final-research-synthesis)
8. [Strategic Verdict](#strategic-verdict)
9. [Decision Gates](#decision-gates)
10. [Source Registry](#source-registry)

### Strategic Verdict

#### What to build

- Python 3.12+ reference engine for discovery, normalized fixtures, shadow
  economics, replay, and reports.
- One Go 1.26.x production process with bounded internal queues and explicit
  ownership of order books, decisions, execution sagas, and nonce state.
- PostgreSQL repositories for intents, submissions, acknowledgements, fills,
  reconciliation, locks, and an outbox.
- Public Hyperliquid and Lighter WebSocket adapters first; private transports
  later and behind explicit runtime controls.
- Deterministic golden vectors for fixed-point arithmetic, normalization, book
  reconstruction, VWAP, decision output, wire payloads, and signatures.

#### What not to build yet

- No Rust production service or custom Lighter Rust signer.
- No Python sidecar in the production execution path.
- No service mesh, Redis, NATS, Kafka, gRPC, or internal HTTP split.
- No pgvector query on the order, risk, or reconciliation path.
- No live order placement merely because unit tests pass.
- No retry of an unknown submission until venue reconciliation resolves it.

#### Why Go wins this round

| Criterion | Weight | Python | Go | Rust |
|---|---:|---:|---:|---:|
| Venue integration assurance | 30% | 4 | 4 | 3 |
| Delivery and review velocity | 20% | 5 | 4 | 2 |
| Runtime determinism and control | 20% | 2 | 4 | 5 |
| Operational simplicity | 15% | 4 | 5 | 3 |
| Optimization ceiling | 15% | 2 | 4 | 5 |
| **Weighted score** | **100%** | **3.50** | **4.15** | **3.50** |

Scores are an architecture decision rubric, not benchmark measurements. The
result is sensitive to the current venue pair and team constraints. If Lighter
ships an audited Rust signer or Go demonstrably misses economically valid
opportunities, the score must be recalculated.

### Decision Gates

#### Gate 0: business falsification

Run public discovery continuously for five days and preserve raw inputs,
normalized events, reconstructed books, executable VWAP, freshness, and
after-cost opportunity calculations. Do not count indicative mid-price spread
as revenue.

Proceed only if the corpus contains repeatable opportunities that remain
positive after:

- venue fees and maker/taker classification;
- executable depth and size-dependent slippage;
- funding and borrow effects where applicable;
- transfer or inventory rebalancing costs;
- stale-book and sequence-gap rejection;
- realistic partial-fill and hedge-delay penalties.

#### Gate 1: deterministic parity

Go may own a calculation slice only after Python and Go produce identical
fixed-point outputs for the golden corpus. Required parity covers event
normalization, book state, VWAP, eligibility, size, rejection reasons, and
economic attribution.

#### Gate 2: runtime safety

Before private execution, require:

- authoritative event loss of zero under at least 5x observed burst;
- `go test -race`, fuzz, property, replay, restart, and sequence-gap tests;
- persist-before-send and idempotent intent identity;
- single-writer nonce ownership per credential identity;
- explicit `unknown` submission state and reconciliation-before-retry;
- exact-owned cancellation with no account-wide destructive fallback;
- crash recovery that converges or freezes safely.

#### Gate 3: live canary

Start with a capped, reversible canary and complete evidence for every order,
fill, fee, hedge, rejection, and realized P&L item. A live run is unsuccessful
if it cannot explain its own balance delta even when gross P&L is positive.

#### Gate 4: Rust reconsideration

Profile and reduce Go allocations before considering a rewrite. Open a bounded
Rust spike only when at least one condition is measured:

- local decision-path p99.9 remains above 1 ms or above 10% of the profitable
  opportunity lifetime;
- Go runtime behavior causes economically valid missed opportunities;
- the process remains above 70% of its assigned CPU or breaches its memory
  ceiling under representative replay.

Promote a Rust kernel only if parity is complete and the same workload improves
p99.9 or CPU/RSS by at least 25%, while recovering at least 30% of opportunities
locally missed by Go. Otherwise the additional language boundary is negative
value.

### Delivery Sequence

1. **Days 1–5:** public adapters, five-day shadow run, after-cost report, golden
   corpus, and a written kill/proceed decision.
2. **Days 6–9:** Go fixed-point, book, VWAP, and decision parity.
3. **Days 10–14:** Go public WebSockets, continuity handling, bounded queues,
   and replay performance evidence.
4. **Days 15–19:** PostgreSQL state, outbox, locks, nonce ownership, and restart
   convergence.
5. **Days 20–27:** private signing, submission, unknown-outcome reconciliation,
   and exact-owned cancellation.
6. **Days 28–32:** fault injection, soak, hardened container release, and capped
   canary evidence.

These are estimates for one experienced developer assisted by agents, not a
calendar promise. A defensible paired-execution MVP is approximately three to
five weeks *after* Gate 0 passes. Failing Gate 0 should terminate execution
development rather than trigger a language rewrite.

### Limitations and Open Questions

- No language benchmark can establish trading expectancy. The five-day corpus
  is the first meaningful falsification, not proof of durable alpha.
- The current Go image measurement covers a Stage 0 scaffold, not full venue
  adapters, telemetry, or database drivers.
- Hyperliquid Go signing effort remains an estimate until the golden-vector
  spike passes against official Python and Rust behavior.
- Rust delivery and token-cost multipliers are planning estimates and must be
  replaced with tracked edit-to-green, compile-loop, CI, and review data.
- Venue APIs, limits, fee schedules, and SDK behavior can change. Pin versions,
  retain contract captures, and run scheduled conformance tests.
- Geographic availability and customer acquisition are business and legal
  questions, not execution-runtime requirements. They require a separate
  evidence-based go/no-go review.

### Source Registry

Venue and protocol evidence:

- [Lighter SDK repositories](https://apidocs.lighter.xyz/docs/repos)
- [Lighter Go reference implementation](https://github.com/elliottech/lighter-go)
- [Lighter account types and latency](https://apidocs.lighter.xyz/docs/account-types)
- [Lighter WebSocket reference](https://apidocs.lighter.xyz/docs/websocket-reference)
- [Lighter trading and nonces](https://apidocs.lighter.xyz/docs/trading)
- [Lighter API keys](https://apidocs.lighter.xyz/docs/api-keys)
- [Lighter rate limits](https://apidocs.lighter.xyz/docs/rate-limits)
- [Hyperliquid Rust SDK](https://github.com/hyperliquid-dex/hyperliquid-rust-sdk)
- [Hyperliquid WebSocket API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket)
- [Hyperliquid signing](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing)
- [Hyperliquid nonces and API wallets](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets)
- [Hyperliquid API servers](https://hyperliquid.gitbook.io/hyperliquid-docs/hypercore/api-servers)
- [Hyperliquid latency guidance](https://hyperliquid.gitbook.io/Hyperliquid-docs/for-developers/api/optimizing-latency)

Runtime and operations evidence:

- [Go garbage-collection guide](https://go.dev/doc/gc-guide)
- [Go race detector](https://go.dev/doc/articles/race_detector)
- [Go fuzzing](https://go.dev/doc/security/fuzz/)
- [Go memory model](https://go.dev/ref/mem)
- [Cargo build performance](https://doc.rust-lang.org/cargo/guide/build-performance.html)
- [Tokio channels](https://tokio.rs/tokio/tutorial/channels)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL advisory locks](https://www.postgresql.org/docs/current/functions-admin.html)
- [pgvector](https://github.com/pgvector/pgvector)
- [Docker build attestations](https://docs.docker.com/build/metadata/attestations/)
- [Docker networking](https://docs.docker.com/engine/network/)
- [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)

### Final Decision Record

**Status:** Accepted for the first production implementation.

**Decision:** Python evidence layer plus Go production modular monolith,
PostgreSQL authoritative state, pgvector offline only, and no Rust production
dependency until the measured Gate 4 threshold is met.

**Next action:** execute Gate 0. Do not implement private trading methods until
the five-day after-cost shadow report returns a written proceed decision.
