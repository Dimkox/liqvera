# Five-day Stage A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and run a credential-free falsifier that can return only
`KILL` or `EXTEND` after five complete data days for the `$10` total-capital
Hyperliquid/Lighter hypothesis.

**Architecture:** A separate `cmd/falsifier` binary and `internal/stagea/*`
dependency graph consume public Hyperliquid and Lighter L2, persist immutable
evidence in PostgreSQL, evaluate delayed taker-only lifecycles, and expose a
GET-only operator API. Variational is a low-frequency observer and never enters
primary economics. Existing execution, ownership, reconciliation, RFQ, account,
credential, and Telegram code remains outside the binary graph.

**Tech Stack:** Go 1.26.5, `github.com/coder/websocket v1.8.15`,
`github.com/jackc/pgx/v5 v5.10.0`, PostgreSQL 18, standard-library HTTP, existing
fixed-point `internal/fixed`, Docker, GitHub Actions.

The current Windows host has no Go toolchain. Every `go` command below runs in
the pinned Docker builder or on Claw; the equivalent Docker `verify` target is
the local checkpoint until an isolated worktree is created with owner consent.

## Global Constraints

- Binding specification: `docs/five-day-stage-a-spec.md` at commit `a173359`.
- Five complete UTC data days may produce only `KILL` or `EXTEND`; never `GO`.
- Hyperliquid and Lighter are primary public L2; Variational is observer-only.
- No private endpoints, accounts, balances, keys, signing, trading SDK, order,
  cancel, transfer, withdrawal, RFQ acceptance, Telegram, referral, or wallet
  code may enter `cmd/falsifier`'s dependency closure.
- Claw containers must not attempt direct outbound Internet access. Discover
  the existing proxy/network contract under `/home/operator/app-stack` read-only
  and attach Stage A to that contract without copying credentials or modifying
  `app-stack`, `glider.conf`, its containers, or its tracked/untracked files.
  Startup and CI fail closed when the required network contract is absent.
- Stage A uses `$10/$25/$50` per-leg research notionals. `$10` is the only
  product-relevant boundary; `$25/$50` are stress diagnostics.
- Stage A admits at most provisional PUMP and DOGE mappings. Lifecycle evidence
  stays blocked until both venue mappings are formally verified.
- Hyperliquid maximum book age is 750 ms; Lighter maximum book age is 200 ms;
  cross-venue skew is 250 ms; recorder clock error is 25 ms.
- All monetary, price, quantity, rate, and bps values use fixed-point integers
  scaled by `1e8`. JSON decimals are strings; unknown decimals are `null`.
- Stale, gapped, misaligned, incomplete, insufficient-depth, or provisional
  evidence fails closed and is persisted as a rejection.
- n8n may orchestrate internal GET-only health and operator checks, but it is
  never an evidence, persistence, market-data, or decision authority; the
  deterministic Go falsifier remains authoritative.
- Every significant task ends with full relevant verification, an independent
  task review, a handoff update when state changes, and one coherent commit.

---

### Task 1: Stage A model, strict public configuration, and capital gate

**Files:**
- Create: `internal/stagea/model/types.go`
- Create: `internal/stagea/model/reasons.go`
- Create: `internal/stagea/config/config.go`
- Create: `internal/stagea/config/config_test.go`
- Create: `internal/stagea/feasibility/capital.go`
- Create: `internal/stagea/feasibility/capital_test.go`
- Create: `config/stage-a.env.example`
- Create: `config/stage-a-instruments.json`
- Modify: `docs/agent-handoff.md`

**Interfaces:**
- Produces `model.Venue`, `model.Instrument`, `model.ResearchProfile`,
  `model.Rejection`, and stable rejection codes used by every later task.
- Produces `config.Load() (Config, error)` reading only public Stage A settings.
- Produces `feasibility.Evaluate(Profile, CostReserve) Assessment`.

Shared model types are defined here so later packages do not create competing
DTOs:

```go
type Contract struct {
    Venue             Venue
    MarketID          string
    VenueSymbol       string
    CanonicalID       string
    ContractMultiplier fixed.Value
    TickSize          fixed.Value
    LotSize           fixed.Value
    MinBase           fixed.Value
    MinQuoteUSD       fixed.Value
    MappingState      string
    EvidenceHash      string
}

type Run struct {
    ID, ConfigHash, FormulaHash string
    StartedAt, PlannedEndAt     time.Time
    State                       string
}

type ProfileEvidence struct {
    PerLegNotionalUSD, Quantity, BuyNotionalUSD, SellNotionalUSD fixed.Value
    BuyVWAP, SellVWAP, RawDivergenceBPS, ModeledNetCaptureUSD    fixed.Value
    CapitalSupported                                             bool
    Codes                                                        []ReasonCode
}

type EvaluationSample struct {
    ID, RunID, CanonicalID, BootID, LeftBatchID, RightBatchID string
    EvaluatedAt                                               time.Time
    Profiles                                                  []ProfileEvidence
    QualityCodes                                              []ReasonCode
}

type LifecycleEvidence struct {
    ID, RunID, CanonicalID, Direction, IndependenceGroupID string
    OpenedAt, ClosedAt                                    time.Time
    Entry, Delayed, Stress, Exit                          EvaluationSample
    StandardNetCaptureUSD, PremiumNetCaptureUSD           fixed.Value
    Codes                                                 []ReasonCode
}

type ReferenceSample struct {
    ID, RunID, CanonicalID, SourceSymbol, PayloadHash string
    SourceUpdatedAt, ObservedAt                       time.Time
    Bid, Ask, Volume24HUSD, OpenInterestUSD           *fixed.Value
    Stale                                              bool
}

type StageDecision struct {
    ID, RunID, Decision, ReportHash, DataHash string
    DecidedAt                                 time.Time
    Codes                                     []ReasonCode
}

type LifecycleEvent struct {
    Type string
    Evidence LifecycleEvidence
}
```

- [ ] **Step 1: Write failing configuration tests**

Add table tests proving the config accepts only these environment names:

```text
DATABASE_URL
HTTP_ADDR
STAGE_A_HYPERLIQUID_WS_URL
STAGE_A_LIGHTER_WS_URL
STAGE_A_VARIATIONAL_HTTP_URL
STAGE_A_INSTRUMENT_MANIFEST
STAGE_A_RAW_RETENTION_DAYS
STAGE_A_EVIDENCE_RETENTION_DAYS
STAGE_A_HL_MAX_AGE_MS
STAGE_A_LIGHTER_MAX_AGE_MS
STAGE_A_MAX_SKEW_MS
STAGE_A_MAX_CLOCK_ERROR_MS
```

The test must set each of `PRIVATE_KEY`, `SECRET`, `API_KEY`, `TOKEN`, `WALLET`,
`MNEMONIC`, and `ACCOUNT_INDEX` and verify `config.Load()` returns a credential
contract violation. Defaults must be 7/30 retention days and 750/200/250/25 ms
quality thresholds.

`config/stage-a-instruments.json` contains exactly PUMP and DOGE mappings for
Hyperliquid and Lighter with `mapping_state:"provisional"`, venue market IDs,
units, tick/lot/minimum fields, and empty evidence hashes. A test proves that
empty evidence keeps lifecycle admission blocked.

- [ ] **Step 2: Run the red configuration test**

Run:

```bash
docker build --target verify -t multi-exchange-engine:stage-a-red .
```

Expected: FAIL because `internal/stagea/config` does not exist.

- [ ] **Step 3: Write failing capital tests**

Use this exact public contract:

```go
type Profile struct {
    TotalCapitalUSD    fixed.Value
    PerVenueCapitalUSD fixed.Value
    Leverage           fixed.Value
    PerLegNotionalUSD  fixed.Value
}

type CostReserve struct {
    EntryFeeUSD     fixed.Value
    ExitFeeUSD      fixed.Value
    StressReserveUSD fixed.Value
}

type Assessment struct {
    RequiredMarginUSD fixed.Value
    MarginHeadroomUSD fixed.Value
    CapitalSupported  bool
    Codes             []model.ReasonCode
}

func Evaluate(Profile, CostReserve) Assessment
```

Tests must prove `$10` per leg with `$5` venue capital at exactly `2x` and any
positive fee/reserve returns `ZERO_MARGIN_HEADROOM`; `$25/$50` at `2x` return
`CAPITAL_NOTIONAL_UNSUPPORTED`; no assessment silently increases leverage.

- [ ] **Step 4: Implement the minimum model, config, and capital code**

Define the stable codes required by the specification, including:

```go
const (
    MappingUnverified       ReasonCode = "INSTRUMENT_MAPPING_UNVERIFIED"
    ContractUnverified      ReasonCode = "CONTRACT_EQUIVALENCE_UNVERIFIED"
    PrimaryBookMissing      ReasonCode = "PRIMARY_BOOK_MISSING"
    BookStale               ReasonCode = "BOOK_STALE"
    CrossVenueSkewExceeded  ReasonCode = "CROSS_VENUE_SKEW_EXCEEDED"
    SequenceGapOpen         ReasonCode = "SEQUENCE_GAP_OPEN"
    BookInvalid             ReasonCode = "BOOK_INVALID"
    DepthInsufficient       ReasonCode = "DEPTH_INSUFFICIENT"
    QuantityMismatch        ReasonCode = "QUANTITY_MISMATCH_EXCEEDED"
    VenueMinimumNotMet      ReasonCode = "VENUE_MINIMUM_NOT_MET"
    CapitalUnsupported      ReasonCode = "CAPITAL_NOTIONAL_UNSUPPORTED"
    ZeroMarginHeadroom      ReasonCode = "ZERO_MARGIN_HEADROOM"
    FeeModelIncomplete      ReasonCode = "FEE_MODEL_INCOMPLETE"
    EntryBelowFloor         ReasonCode = "ENTRY_DIVERGENCE_BELOW_FLOOR"
    ExitEvidenceMissing     ReasonCode = "EXIT_EVIDENCE_MISSING"
    StressNonPositive       ReasonCode = "STRESS_CHANGE_NON_POSITIVE"
    LifecycleNotIndependent ReasonCode = "LIFECYCLE_NOT_INDEPENDENT"
)
```

`config.Load` must not import or delegate to the existing credential-bearing
`internal/config` package.

- [ ] **Step 5: Verify green and commit**

Run the full verify image and confirm zero failures:

```bash
docker build --target verify -t multi-exchange-engine:stage-a-task1 .
```

Commit:

```bash
git add internal/stagea config/stage-a.env.example config/stage-a-instruments.json docs/agent-handoff.md
git commit -m "feat: add Stage A capital and public config gates"
```

---

### Task 2: Deterministic book reconstruction, clock epochs, and quality gates

**Files:**
- Create: `internal/stagea/feed/contracts.go`
- Create: `internal/stagea/book/state.go`
- Create: `internal/stagea/book/state_test.go`
- Create: `internal/stagea/quality/gate.go`
- Create: `internal/stagea/quality/gate_test.go`
- Create: `internal/stagea/testdata/books/*.json`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```go
type FrameConsumer interface {
    Consume(context.Context, Frame) error
}

type PublicL2Source interface {
    Venue() model.Venue
    Run(context.Context, model.Instrument, FrameConsumer) error
}

type Frame struct {
    Venue           model.Venue
    Instrument      string
    BootID          string
    ConnectionEpoch string
    Kind             Kind
    SourceTime       time.Time
    ReceiveWallTime  time.Time
    ReceiveMonoNS    int64
    Sequence         *uint64
    BeginSequence    *uint64
    RawSHA256        [32]byte
    Book             BookUpdate
}
```

- [ ] **Step 1: Write failing snapshot/delta tests**

Tests must cover:

- complete snapshot replaces state;
- Lighter delta changes only named levels and removes a zero-size level;
- `begin_nonce != previous nonce` opens `SEQUENCE_GAP_OPEN`;
- deltas remain rejected until a fresh complete snapshot;
- a Hyperliquid non-monotonic source time opens a gap;
- crossed, unsorted, empty, non-positive, or duplicate-price books are invalid;
- reconnect changes connection epoch and cannot pair with the old epoch.

- [ ] **Step 2: Verify the tests fail for missing implementation**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-task2-red .
```

Expected: FAIL in `internal/stagea/book` and `internal/stagea/quality`.

- [ ] **Step 3: Implement immutable snapshots and continuity state**

Expose:

```go
func NewState() *State
func (s *State) Apply(frame feed.Frame) (Snapshot, error)
func (s Snapshot) Valid() bool
```

Copy input levels before storing them. Sort bids descending and asks ascending
only after rejecting duplicate prices; never repair a crossed or malformed
book. A failed delta must not mutate the previous good state.

- [ ] **Step 4: Implement quality evaluation**

Expose:

```go
type Thresholds struct {
    HyperliquidMaxAge time.Duration
    LighterMaxAge     time.Duration
    MaxSkew           time.Duration
    MaxClockError     time.Duration
}

func Evaluate(now time.Time, left, right book.Snapshot, t Thresholds) Result
```

The result is valid only when both books are complete, continuous, same boot
epoch, within 750/200 ms age, within 250 ms receive-time skew, and within 25 ms
recorder clock error. A wall/monotonic delta divergence above 50 ms terminates
the epoch.

- [ ] **Step 5: Verify deterministic replay and commit**

Run:

```bash
docker build --target verify -t multi-exchange-engine:stage-a-task2 .
```

Run the same fixture replay twice and assert byte-identical serialized
snapshots. Commit:

```bash
git add internal/stagea/feed internal/stagea/book internal/stagea/quality docs/agent-handoff.md
git commit -m "feat: add deterministic public book quality model"
```

---

### Task 3: PostgreSQL Stage A evidence schema, batching, and replay

**Files:**
- Create: `migrations/000002_stage_a.up.sql`
- Create: `migrations/000002_stage_a.down.sql`
- Create: `internal/stagea/postgres/repository.go`
- Create: `internal/stagea/postgres/repository_test.go`
- Create: `internal/stagea/postgres/batch_codec.go`
- Create: `internal/stagea/postgres/batch_codec_test.go`
- Modify: `go.mod`
- Create: `go.sum`
- Modify: `.github/workflows/ci.yml`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```go
type Repository interface {
    StartRun(context.Context, model.Run) error
    AppendRawBatch(context.Context, RawBatch) error
    AppendEvaluation(context.Context, model.EvaluationSample) error
    AppendLifecycle(context.Context, model.LifecycleEvidence) error
    AppendObserverSample(context.Context, model.ReferenceSample) error
    AppendDecision(context.Context, model.StageDecision) error
    ReplayBatches(context.Context, string, func(feed.Frame) error) error
    EnsureDayPartitions(context.Context, time.Time) error
    ApplyRetention(context.Context, time.Time) error
}
```

- [ ] **Step 1: Write failing codec tests**

Encode one-second NDJSON batches with deterministic field order, gzip them,
persist SHA-256 of the uncompressed bytes, then decode and verify exact frame
identity. Corrupting one byte must return `RAW_BATCH_HASH_MISMATCH`.

- [ ] **Step 2: Write failing migration/repository tests**

The migration must create isolated schema `stage_a` and tables:

```text
runs
instrument_mappings
feed_connections
raw_l2_batches
evaluation_samples
quality_minutes
variational_samples
shadow_lifecycles
stage_decisions
```

`raw_l2_batches`, `evaluation_samples`, `variational_samples`,
`shadow_lifecycles`, and `stage_decisions` must reject UPDATE and DELETE through
database triggers. Duplicate `(run_id, venue, instrument, boot_id,
connection_epoch, batch_started_at)` inserts must be idempotent only when the
stored hash matches; a different hash is an error.

Time-series evidence tables are UTC-day partitioned. `EnsureDayPartitions`
creates only validated `YYYYMMDD` partition names. `ApplyRetention` drops whole
closed partitions older than seven complete UTC days for raw batches and 30
complete UTC days for evaluation, observer, and lifecycle evidence; it never
issues row-level UPDATE or DELETE. Mappings, quality summaries, run hashes, and
decisions are not expired. Freeze the clock in tests and assert both sides of
each 7/30-day boundary.

- [ ] **Step 3: Add pinned PostgreSQL dependency and implement repository**

Pin:

```text
github.com/jackc/pgx/v5 v5.10.0
```

Use `pgxpool`. Each append operation is one transaction. Never build SQL with
string interpolation. Store decimal JSON as strings and use database `numeric`
only for indexed summary columns.

- [ ] **Step 4: Add PostgreSQL CI service and run green tests**

GitHub Actions must start PostgreSQL 18 and export a dedicated
`STAGE_A_TEST_DATABASE_URL`. Tests may skip only when that variable is absent;
CI must set it, run the migration up/down smoke, and execute repository tests.

Run locally on Docker/Claw:

```bash
go test -race ./internal/stagea/postgres/...
go test -race ./...
```

- [ ] **Step 5: Commit**

```bash
git add migrations internal/stagea/postgres go.mod go.sum .github/workflows/ci.yml docs/agent-handoff.md
git commit -m "feat: persist immutable Stage A evidence"
```

---

### Task 4: Hyperliquid public full-snapshot collector

**Files:**
- Create: `internal/stagea/venue/hyperliquid/message.go`
- Create: `internal/stagea/venue/hyperliquid/message_test.go`
- Create: `internal/stagea/venue/hyperliquid/source.go`
- Create: `internal/stagea/venue/hyperliquid/source_test.go`
- Create: `internal/stagea/venue/hyperliquid/testdata/*.json`
- Modify: `go.mod`
- Modify: `go.sum`
- Modify: `docs/agent-handoff.md`

**Interfaces:** Implements `feed.PublicL2Source`; emits complete snapshot frames
only and never emits a fabricated sequence.

- [ ] **Step 1: Write failing decoder tests from official payloads**

Fixture shape:

```json
{
  "channel": "l2Book",
  "data": {
    "coin": "PUMP",
    "time": 1754450974231,
    "levels": [
      [{"px":"0.002020","sz":"10000","n":2}],
      [{"px":"0.002021","sz":"12000","n":3}]
    ]
  }
}
```

Prove exact fixed-point parsing, source timestamp conversion, snapshot
completeness, payload hash, rejection of numeric JSON decimals, wrong channels,
extra/missing sides, crossed books, and non-monotonic time.

- [ ] **Step 2: Verify red**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-hl-red .
```

- [ ] **Step 3: Implement decoder and WebSocket source**

Pin `github.com/coder/websocket v1.8.15`. The source may send only:

```json
{"method":"subscribe","subscription":{"type":"l2Book","coin":"PUMP"}}
```

and the corresponding DOGE message. Use an injected dialer and clock. Handle
ping/close, bounded reconnect backoff, a new connection epoch on every dial,
and a gap on disconnect or two seconds of silence. Do not import Hyperliquid
SDKs or call `/exchange`, private channels, user endpoints, or account data.

- [ ] **Step 4: Test against an in-process WebSocket server**

The server must send subscription acknowledgment, two snapshots, a silence
timeout, disconnect, and fresh reconnect snapshot. Assert exact frame order,
epoch transition, and no frame emitted from stale/malformed input.

- [ ] **Step 5: Verify and commit**

```bash
go test -race ./internal/stagea/venue/hyperliquid/...
go test -race ./...
git add internal/stagea/venue/hyperliquid go.mod go.sum docs/agent-handoff.md
git commit -m "feat: collect Hyperliquid public L2 snapshots"
```

---

### Task 5: Lighter public snapshot/delta collector

**Files:**
- Create: `internal/stagea/venue/lighter/message.go`
- Create: `internal/stagea/venue/lighter/message_test.go`
- Create: `internal/stagea/venue/lighter/source.go`
- Create: `internal/stagea/venue/lighter/source_test.go`
- Create: `internal/stagea/venue/lighter/testdata/*.json`
- Modify: `docs/agent-handoff.md`

**Interfaces:** Implements `feed.PublicL2Source`; produces one complete initial
snapshot followed by nonce-bounded deltas.

- [ ] **Step 1: Write failing official-message decoder tests**

Use the exact documented fields:

```json
{
  "channel":"order_book:45",
  "last_updated_at":1774884082309144,
  "offset":1558300,
  "order_book":{
    "code":0,
    "asks":[{"price":"0.002021","size":"12000"}],
    "bids":[{"price":"0.002020","size":"10000"}],
    "offset":1558300,
    "nonce":9182390020,
    "last_updated_at":1774884082309144,
    "begin_nonce":9182389998
  },
  "timestamp":1774884082326,
  "type":"update/order_book"
}
```

Tests must distinguish the subscription full snapshot from later changes,
enforce `begin_nonce == previous nonce`, require increasing offset within an
epoch without requiring continuity, accept a new offset range after reconnect,
and remove zero-size levels.

- [ ] **Step 2: Verify red**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-lighter-red .
```

- [ ] **Step 3: Implement the public source**

The only subscription messages are:

```json
{"type":"subscribe","channel":"order_book/45"}
{"type":"subscribe","channel":"order_book/3"}
```

On nonce mismatch, close the current evidence epoch, discard subsequent deltas,
and resubscribe for a full snapshot. Do not use auth tokens, API keys, account
channels, `sendTx`, `sendTxBatch`, RFQ, transfer, or withdrawal endpoints.

- [ ] **Step 4: Run reconnect/gap race tests**

An in-process WebSocket server must cover duplicate delta, missing nonce,
out-of-order offset, reconnect to a different offset range, and a valid fresh
snapshot. Run tests with `-race`.

- [ ] **Step 5: Verify and commit**

```bash
go test -race ./internal/stagea/venue/lighter/...
go test -race ./...
git add internal/stagea/venue/lighter docs/agent-handoff.md
git commit -m "feat: reconstruct Lighter public L2"
```

---

### Task 6: Common quantity, depth VWAP, and paired evaluation

**Files:**
- Create: `internal/stagea/evaluate/quantity.go`
- Create: `internal/stagea/evaluate/quantity_test.go`
- Create: `internal/stagea/evaluate/vwap.go`
- Create: `internal/stagea/evaluate/vwap_test.go`
- Create: `internal/stagea/evaluate/pair.go`
- Create: `internal/stagea/evaluate/pair_test.go`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```go
type DepthQuote struct {
    Quantity           fixed.Value
    ActualNotionalUSD  fixed.Value
    VWAP                fixed.Value
    WorstPrice          fixed.Value
    ConsumedLevelCount  int
}

func CommonQuantity(target fixed.Value, buy, sell model.Contract) (fixed.Value, error)
func Sweep(levels []book.Level, quantity fixed.Value) (DepthQuote, error)
func EvaluatePair(input PairInput) PairResult
```

- [ ] **Step 1: Write failing common-quantity tests**

Cover PUMP and DOGE fixtures with whole-unit lots, venue minimum quote `$10`,
common contract multiplier, and preset overshoot. Assert rejection when either
leg is below minimum, exceeds target by more than 2%, or normalized mismatch is
greater than one common lot.

- [ ] **Step 2: Write failing VWAP tests**

Prove ask sweep buys low-to-high, bid sweep sells high-to-low, partial last
level is allowed, full requested quantity is required, input levels are not
mutated, and insufficient depth returns `DEPTH_INSUFFICIENT` without an
extrapolated price.

- [ ] **Step 3: Verify red and implement minimum arithmetic**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-evaluate-red .
```

Use only `fixed.Value`; no `float64`, `math/big.Float`, or numeric JSON decimal.
The pair evaluator must run the quality gate before quantity or economics and
persist one blocking rejection code for every failed stage.

- [ ] **Step 4: Verify both directions and all profiles**

Tests must produce buy-HL/sell-Lighter and buy-Lighter/sell-HL results for
`$10/$25/$50`, with actual notionals, common quantity, VWAP, worst price, depth
levels, margin assessment, and raw divergence bps.

- [ ] **Step 5: Verify and commit**

```bash
go test -race ./internal/stagea/evaluate/...
go test -race ./...
git add internal/stagea/evaluate docs/agent-handoff.md
git commit -m "feat: evaluate fixed-point paired market divergence"
```

---

### Task 7: Delayed taker lifecycle, stress, independence, and statistics

**Files:**
- Create: `internal/stagea/lifecycle/engine.go`
- Create: `internal/stagea/lifecycle/engine_test.go`
- Create: `internal/stagea/economics/costs.go`
- Create: `internal/stagea/economics/costs_test.go`
- Create: `internal/stagea/statistics/bootstrap.go`
- Create: `internal/stagea/statistics/bootstrap_test.go`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```go
type Engine interface {
    Observe(model.EvaluationSample) []model.LifecycleEvent
}

type FeeScenario struct {
    HyperliquidTakerRate fixed.Value
    LighterTakerRate     fixed.Value
    EntryFloorBPS        fixed.Value
}

func OneSidedBlockBootstrap(values []Observation, block time.Duration,
    resamples int, seed int64) ConfidenceResult
```

Define the statistics-local types exactly as:

```go
type Observation struct {
    At      time.Time
    Value   fixed.Value
    Day     string
    Market  string
}

type ConfidenceResult struct {
    Mean, Median, Lower95 fixed.Value
    Resamples             int
    Seed                  int64
}
```

- [ ] **Step 1: Write lifecycle state-machine tests**

Freeze exact behavior:

- Standard trigger floor 19 bps; Premium trigger floor 24.6 bps;
- Lighter entry uses first valid evidence after 300 ms plus measured p95
  transport delay;
- Hyperliquid entry uses its first fresh post-decision full snapshot;
- five-second stress uses first valid paired evidence at/after `t0+5s`;
- missing delayed depth rejects the entire lifecycle;
- close when normalized basis is at most 5 bps;
- force-close at 60 minutes;
- no same mapping/direction re-entry until basis remains below 5 bps for 60
  seconds;
- funding is zero in primary economics unless a real funding boundary is
  crossed and is otherwise a separate scenario.

- [ ] **Step 2: Verify red**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-lifecycle-red .
```

- [ ] **Step 3: Implement full entry+exit cost evidence**

Calculate cash changes from four depth sweeps and deduct entry and exit taker
fees on actual leg notionals. Persist Standard, Premium, 10 bps adverse-price,
and five-second delay results separately. Never name a field PnL, profit,
return, ROI, APY, win rate, fill rate, or earnings.

- [ ] **Step 4: Write and pass statistical/concentration tests**

Use deterministic one-hour cluster/block bootstrap with 10,000 resamples and a
stored seed. `EXTEND` requires at least 100 independent closed lifecycles total,
at least 30 per admitted mapping, evidence on at least four of five UTC days,
no day above 35% of samples, no instrument above 50%, and the top ten
lifecycles at no more than 25% of modeled net capture. Calm, normal, and
stressed bins must all be represented using an independent trailing 30-day
volatility baseline. For the `$10` profile, the one-sided 95% lower bound of
mean and the median must both exceed zero, every forced exit must remain
positive, and the result must not depend on funding, maker fills, zero exit
cost, stale data, one market, or one day. A result positive only in the Standard
zero-fee scenario is a robustness `KILL`. Any failed gate returns `KILL`; all
gates passing returns `EXTEND`; no enum or branch may represent `GO`.

- [ ] **Step 5: Verify and commit**

```bash
go test -race ./internal/stagea/lifecycle/... ./internal/stagea/economics/... ./internal/stagea/statistics/...
go test -race ./...
git add internal/stagea/lifecycle internal/stagea/economics internal/stagea/statistics docs/agent-handoff.md
git commit -m "feat: add delayed Stage A lifecycle gates"
```

---

### Task 8: Variational observer with explicit stale exclusion

**Files:**
- Create: `internal/stagea/observer/variational/client.go`
- Create: `internal/stagea/observer/variational/client_test.go`
- Create: `internal/stagea/observer/variational/testdata/*.json`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```go
type ReferenceObserver interface {
    Sample(context.Context, []model.Instrument) ([]model.ReferenceSample, error)
}
```

- [ ] **Step 1: Write failing HTTP decoder/staleness tests**

Use an `httptest.Server` returning `PUMPFUN`, `1000BONK`, and `1000PEPE` rows.
Assert numeric strings remain exact, `quotes.updated_at` is parsed as
`time.Time`, 600 seconds is the maximum valid age, a missing timestamp is
rejected, and every sample sets:

```text
role=reference_observer_only
included_in_primary_pair=false
included_in_vwap=false
included_in_shadow_change=false
```

- [ ] **Step 2: Verify red and implement public GET-only client**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-var-red .
```

The client may call only `/metadata/stats`, no cookies, auth, account, RFQ, or
trading routes. Poll interval is 60 seconds with bounded timeout and jitter.

- [ ] **Step 3: Prove observer cannot affect economics**

Add a compile-time/runtime test that changes every Variational value by 100x
and obtains byte-identical primary pair and lifecycle results.

- [ ] **Step 4: Verify and commit**

```bash
go test -race ./internal/stagea/observer/variational/...
go test -race ./...
git add internal/stagea/observer/variational docs/agent-handoff.md
git commit -m "feat: add Variational reference observer"
```

---

### Task 9: GET-only operator API, falsifier runtime, and negative CI

**Files:**
- Create: `internal/stagea/httpapi/server.go`
- Create: `internal/stagea/httpapi/server_test.go`
- Create: `internal/stagea/runtime/runtime.go`
- Create: `internal/stagea/runtime/runtime_test.go`
- Create: `cmd/falsifier/main.go`
- Create: `scripts/verify-stage-a-read-only.sh`
- Modify: `.github/workflows/ci.yml`
- Modify: `Dockerfile`
- Modify: `README.md`
- Modify: `docs/deployment.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:** The HTTP server receives a read-model interface only. It cannot
receive collectors, repositories with mutation methods, exchange clients, or
execution services.

- [ ] **Step 1: Write failing route/envelope tests**

Required GET routes:

```text
/healthz
/readyz
/v1/meta
/v1/experiment/status
/v1/ops/adapter-runs
/v1/ops/data-quality
/v1/business/operator-revenue
/v1/shadow/lifecycles
/v1/shadow/lifecycles/{id}
/v1/shadow/rejections
/v1/observers/variational/samples
```

Every `/v1/*` response wraps data with mode
`public_data_falsification`, `execution_available:false`,
`recommendation:false`, and UTC RFC3339Nano `generated_at`. Test every route
with POST/PUT/PATCH/DELETE and require 404/405. `/readyz` returns 503 when
storage, migrations, or read models are unavailable; feed/economic failure is
reported in data, not confused with process readiness.

`/v1/business/operator-revenue` is a planned GET-only contract endpoint. It
must report whether the owner-supplied revenue contract is complete (source,
rate, turnover basis, payout terms, collection mechanism, and infrastructure
cost) without inventing a fee rate; an incomplete contract is a fail-closed
operator-revenue `KILL` gate. n8n may read this endpoint but cannot write any
evidence or decision.

- [ ] **Step 2: Verify red and implement read-only API/runtime**

```bash
docker build --target verify -t multi-exchange-engine:stage-a-api-red .
```

The runtime starts PostgreSQL, both primary collectors, one-second batching,
evaluation, lifecycle processing, quality summaries, the 60-second observer,
and HTTP. Shutdown flushes the final batch with its hash and closes the current
connection epoch.

Quality summaries count one-second UTC ticks per admitted venue/mapping.
Report/API fixtures must prove that `99.5%` valid wall-clock coverage is the
minimum for `EXTEND`, that `99.499%` is `KILL`, and that missing ticks are never
silently removed from the denominator.

- [ ] **Step 3: Implement negative dependency and source checks**

`scripts/verify-stage-a-read-only.sh` must fail when:

- `go list -deps ./cmd/falsifier` contains `internal/execution`, `ownership`,
  `risk`, `reconcile`, `TradingExecutor`, or `RFQClient`;
- Stage A imports wallet, Ethereum signing, Telegram, auth, Hyperliquid SDK, or
  Lighter SDK modules;
- `internal/stagea` or `cmd/falsifier` contains credential environment names;
- adapters contain `/exchange`, `sendtx`, `sendtxbatch`, private/account
  channel names, or place/cancel/sign/withdraw/transfer symbols;
- the route table contains mutating methods.

Use a precise allowlist and exclude test fixture strings only when the test is
asserting rejection of that exact forbidden value.

- [ ] **Step 4: Build a dedicated falsifier container target**

The Dockerfile must build `./cmd/falsifier` in a named `falsifier-build` stage
and run it as the existing non-root `10001:10001` user with read-only root
filesystem compatibility. It receives only the Stage A public configuration
and database URL. Apply the dockerfile-generator and dockerfile-validator
skills during this task.

- [ ] **Step 5: Run full verification and commit**

Run fresh:

```bash
gofmt -w cmd/falsifier internal/stagea
go vet ./...
go test -race -cover ./...
bash scripts/verify-stage-a-read-only.sh
docker build --target verify -t multi-exchange-engine:verify .
docker build --target falsifier-production -t multi-exchange-engine:falsifier .
```

Commit:

```bash
git add cmd/falsifier internal/stagea scripts .github Dockerfile README.md docs
git commit -m "feat: assemble credential-free Stage A falsifier"
```

---

### Task 10: Deterministic report, Claw warm-up, and experiment start gate

**Files:**
- Create: `internal/stagea/report/report.go`
- Create: `internal/stagea/report/report_test.go`
- Create: `cmd/stage-a-report/main.go`
- Create: `deploy/stage-a/compose.yaml`
- Create: `deploy/stage-a/env.example`
- Modify: `Dockerfile`
- Modify: `docs/deployment.md`
- Modify: `docs/validation.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:** The report reads immutable evidence and emits JSON plus Markdown
with the same config/formula/data hashes and exactly one decision enum:
`KILL|EXTEND`.

- [ ] **Step 1: Write failing deterministic report tests**

Fixtures must cover capital failure, mapping failure, coverage failure,
statistics failure, and all-gates-pass. The first four return `KILL`; the last
returns `EXTEND`. Two runs over identical evidence must be byte-identical except
for an explicitly injected generated timestamp.

- [ ] **Step 2: Implement report and five-day clock gate**

The run start time is written only after:

- both mappings are verified;
- migrations are current;
- both primary collectors have no open gaps;
- deterministic replay matches stored hashes;
- quality monitors complete a continuous 60-minute warm-up;
- the capital boundary result is recorded.

Implementation and warm-up time do not count toward five complete UTC data
days.

- [ ] **Step 3: Create isolated Claw deployment**

Deploy only under `/home/operator/stage-a-falsifier`; do not modify
`/home/operator/app-stack` or its dirty `glider.conf`. Compose contains a dedicated
PostgreSQL 18 service, named volume, falsifier container, read-only filesystem,
no-new-privileges, dropped capabilities, health checks, log rotation, and no
published database port. Before writing Compose, inspect the existing
`/home/operator/app-stack` egress configuration read-only, document the exact
external Docker network or proxy-file contract, and reuse it without embedding
or copying secrets. No Stage A container may fall back to direct Internet
egress. The Docker build also emits
`/usr/local/bin/stage-a-report` from `./cmd/stage-a-report` in the same pinned Go
builder and copies it into the non-root production image. Document LAN and
Tailscale access separately.

- [ ] **Step 4: Validate warm-up without starting the data clock early**

Run on Claw:

```bash
docker compose -f deploy/stage-a/compose.yaml config
docker compose -f deploy/stage-a/compose.yaml build --pull
docker compose -f deploy/stage-a/compose.yaml up -d
docker compose -f deploy/stage-a/compose.yaml ps
docker compose -f deploy/stage-a/compose.yaml exec -T falsifier /usr/local/bin/stage-a-report --check-warmup
```

Verify one complete hour, zero credential variables, exact mapping evidence,
open-gap count zero, deterministic replay hashes, and correct PUMP/DOGE public
subscriptions. If any gate fails, persist `KILL` or leave the run `planned`; do
not silently restart the five-day clock.

- [ ] **Step 5: Full review and checkpoint**

Run full Go, migration, negative CI, container security, and report tests.
Request broad whole-branch review. Fix every Critical/Important finding through
the subagent review loop. Commit:

```bash
git add internal/stagea/report cmd/stage-a-report deploy Dockerfile docs
git commit -m "ops: gate five-day Stage A collection"
```

After a clean review and verified warm-up, record the exact UTC start/end in
`docs/agent-handoff.md`, Basic Memory, and the append-only `stage_a.runs` row.
