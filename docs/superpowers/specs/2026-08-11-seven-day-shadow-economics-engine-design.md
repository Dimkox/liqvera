# Seven-Day Shadow Economics Engine — Design

**Date:** 2026-08-11  
**Status:** approved design; implementation not started  
**Repository:** `Dimkox/multi-exchange-engine`  
**Safety boundary:** public data, shadow analysis, no credentials, no orders, no withdrawals

[Repository README](../../../README.md) · [Roadmap](../../ROADMAP.md) · [A2 architecture](../../architecture.md) · [Research index](../../research/README.md) · [User-needs research](../../research/user-needs/README.md) · [Security](../../../SECURITY.md)

## 1. Decision

The next project increment is a seven-day falsification sprint named **Shadow Economics Engine**.

The sprint answers one question:

> Do reproducible Hyperliquid↔Lighter price/basis or funding opportunities survive executable depth, full-cycle costs, realistic independent leg delay, capital constraints, and strict data-quality gates?

The sprint does not authorize live trading. It must be capable of returning `NO_GO` or `INSUFFICIENT_EVIDENCE` without pressure to manufacture a positive result.

The chosen architecture is:

```text
Hyperliquid public feeds ─┐
                          ├─> A2 immutable evidence layer
Lighter public feeds ─────┘          │
                                     ├─> read-only PostgreSQL evidence view
                                     │      └─> live preview
                                     │
                                     └─> frozen evidence package
                                            └─> deterministic final replay
                                                     │
                                                     └─> Shadow Economics Analyzer
```

A2 remains an evidence producer. It does not reconstruct normalized books, calculate VWAP, detect opportunities, estimate profitability, or gain private/trading capabilities.

The Shadow Economics Analyzer is a separate read-only component. It owns reconstruction, quality gates, economic mappings, scenario simulation, portfolio diagnostics, reports, and verdicts.

## 2. Sprint objective and non-goals

### 2.1 Objective

Within seven calendar days:

1. begin or continue credential-free Hyperliquid and Lighter evidence capture;
2. obtain at least five complete UTC data days if operational conditions permit;
3. reconstruct reproducible L2 books for BTC, ETH, and SOL;
4. calculate two independent strategy families:
   - price/basis convergence;
   - funding carry;
5. evaluate the frozen scenario matrix defined below;
6. produce a hash-bound deterministic report with per-strategy and overall verdicts;
7. record exactly why a verdict is `GO`, `NO_GO`, or `INSUFFICIENT_EVIDENCE`.

### 2.2 Non-goals

The sprint must not:

- submit, cancel, or amend an order;
- use an exchange account, wallet, API key, signer, nonce, private stream, or withdrawal permission;
- infer order-to-fill latency from public market-data latency;
- build a Telegram Mini App;
- build a custom Solana program, flash-loan strategy, validator, or liquidity aggregator;
- add Bybit, MEXC, Variational execution, Extended, Reya, or Ostium;
- claim customer demand or product-market fit;
- optimize thresholds after seeing the final dataset;
- call a maker-fill simulation evidence for a tradable strategy;
- change A2 from public evidence capture into an economics service.

## 3. Frozen experiment parameters

These parameters are fixed before final evidence collection. Final reports may show sensitivity tables, but the primary verdict may not select a more favorable parameter after the fact.

### 3.1 Venues and assets

```text
venues: Hyperliquid, Lighter
assets: BTC, ETH, SOL
product: linear perpetuals only
```

Ticker equality is not equivalence evidence. Each pair requires a versioned economic mapping.

### 3.2 Strategy families

The analyzer produces independent reports for:

1. **Price/basis convergence** — executable entry and executable exit on both venues; funding is not mixed into price edge.
2. **Funding carry** — realized venue funding cashflows, entry/exit cost, basis movement, and holding cost; forecast and realized funding remain separate.

The strategy families use separate virtual portfolios. A combined portfolio is diagnostic only.

### 3.3 Notional ladder

```text
USD 100
USD 500
USD 1,000
USD 5,000
USD 10,000
```

Interpretation:

- USD 100 and USD 500: sanity and retail-depth checks;
- USD 1,000 and USD 5,000: primary verdict sizes;
- USD 10,000: capacity and VWAP-degradation sensitivity.

### 3.4 Entry-edge matrix

For price/basis:

```text
net entry edge thresholds: 0, 2, 5, 10, 20 bps
primary thresholds: 5 and 10 bps
```

For funding:

```text
expected net carry after full round trip: 0, 2, 5, 10, 20 bps
primary thresholds: 5 and 10 bps
```

The signal uses information available at the virtual entry time. Realized outcome uses subsequent venue evidence.

### 3.5 Price/basis exits

Every eligible entry is evaluated through both exit families.

Fixed time horizons:

```text
1 minute
5 minutes
15 minutes
60 minutes
```

Convergence exits:

```text
relative convergence: 50%, 75%, 90%
absolute remaining spread: 1, 2, 5 bps
primary exit: 75% convergence or 60-minute maximum holding time
```

Every exit consumes executable depth on both venues and pays exit costs.

### 3.6 Funding holding models

Rolling horizons:

```text
1 hour
4 hours
8 hours
24 hours
```

Settlement-aware horizons:

```text
1 realized settlement
2 realized settlements
24-hour maximum holding time
```

The accounting source of truth is the realized funding settlement event and resulting cashflow. Hourly, eight-hour-equivalent, and annualized rates are display/screening values only.

If a realized settlement cannot be unambiguously supported by public evidence, that virtual trade is excluded from the strict funding verdict.

### 3.7 Fee cases

Two fee cases are mandatory.

**Operator case**

- manually supplied versioned maker/taker values;
- source, scope, and verification date required;
- no private API access by A2 or the analyzer;
- missing confirmation produces `INSUFFICIENT_INPUT` for operator-case output.

**Conservative product case**

- public/default venue fee schedule;
- explicit builder/partner-fee assumption;
- conservative fallback where a value is uncertain;
- source and effective date bound into configuration.

The primary verdict requires both fee cases to pass. If the operator case is unavailable, no overall `GO` may be issued; the product case may still be reported.

### 3.8 Execution model

Primary execution model:

```text
taker leg on Hyperliquid + taker leg on Lighter
parallel submission, independent venue delay
```

Diagnostic execution models:

- maker-first plus taker hedge;
- sequential taker execution as a worst case.

Maker-first output cannot issue `GO` until measured queue position, fill probability, time-to-fill, cancel latency, and adverse-selection evidence exist.

### 3.9 Delay scenarios

The analyzer must not apply a scalar bps haircut to a price observed at signal time. Each leg uses the first valid reconstructed book no earlier than its independent delay.

Symmetric scenarios:

```text
100/100 ms
300/300 ms
500/500 ms
1000/1000 ms
```

Asymmetric scenarios:

```text
100/500 ms
500/100 ms
300/1000 ms
1000/300 ms
```

Definitions remain separate:

- `market_data_age`: receive timestamp minus reliable venue source timestamp;
- `public_network_rtt`: read-only request or ping RTT;
- `execution_delay_assumption`: frozen scenario above.

Neither market-data age nor public RTT may be labelled order-to-fill latency.

### 3.10 Opportunity episodes

An independent episode starts when strict net edge crosses upward through a configured threshold.

It ends when:

- edge falls below threshold;
- strict quality becomes invalid;
- mapping becomes invalid;
- the relevant virtual position exits.

A new independent episode requires 60 continuous seconds outside the signal.

The simulator permits at most one active position for each:

```text
asset × strategy × direction × size
```

Signals observed while that position is open are stored as observations, not counted as new trades. Capital cannot be reused until exit.

### 3.11 Capital scenarios

Economics matrix:

- each size, threshold, delay, fee case, and exit rule is a separate counterfactual;
- results across counterfactual scenarios are never summed.

Portfolio diagnostic capital matrix:

```text
USD 5,000
USD 10,000
USD 20,000
USD 50,000
```

Primary portfolio case:

```text
total capital: USD 20,000
venue allocation: 50/50
leverage: 2x
free margin reserve: at least 50%
```

Sensitivities:

```text
venue allocation: 60/40 and 40/60
leverage: 1x, 2x, 3x
```

A strategy that becomes attractive only at 3x does not receive `GO`.

No instantaneous rebalance exists. P&L remains on its venue. An entry is blocked when either venue lacks margin. Rebalance is a separate diagnostic event with explicit delay and cost, and is excluded from the primary seven-day portfolio verdict unless a verified route is configured.

### 3.12 Capital prioritization

When eligible opportunities compete for limited portfolio capital, ordering is deterministic:

1. strict opportunities only;
2. higher expected net bps;
3. higher executable capacity;
4. lower data age/skew;
5. lower expected holding time;
6. stable asset tie-break: BTC, ETH, SOL;
7. stable strategy/direction/configuration identifier bytes.

No adaptive model or post-hoc score fitting is allowed in this sprint.

## 4. Evidence and dataset architecture

### 4.1 A2 responsibility

A2 owns:

- exact venue-native public application frames;
- initial discovery/control evidence;
- connection epochs;
- sequence/nonce continuity observations;
- raw batch hashes;
- decoder/schema versions;
- immutable lifecycle evidence;
- quality-minute evidence already within its approved boundary;
- frozen run and universe identity.

A2 does not own:

- normalized order books;
- economic opportunities;
- VWAP;
- simulated fills;
- P&L;
- portfolio state;
- product verdicts.

### 4.2 Analyzer input contract

```python
class EvidenceReader(Protocol):
    def read_manifest(self) -> DatasetManifest: ...
    def iter_control_evidence(self) -> Iterator[ControlEvidence]: ...
    def iter_raw_batches(self) -> Iterator[RawBatch]: ...
    def iter_quality_minutes(self) -> Iterator[QualityMinute]: ...
    def read_mapping_snapshot(self) -> MappingSnapshot: ...
    def read_fee_configs(self) -> FeeConfigBundle: ...
```

Two implementations are required:

1. `PostgresEvidenceReader` — read-only live preview against A2 evidence views;
2. `FrozenPackageEvidenceReader` — final replay from immutable exported files.

All downstream components depend only on `EvidenceReader` values, never on source-specific SQL or filesystem layout.

### 4.3 Raw frame identity

Every raw frame must preserve or derive the following immutable identity:

```text
run_id
venue
market/channel routing evidence
boot_id
connection_epoch
batch_sequence
frame_index
ingest_index
source_timestamp when present
receive_timestamp
sequence_or_nonce when present
payload_length
payload_sha256
raw_payload
decoder_version
ingest/schema version
```

Raw payload bytes are source evidence. Reconstructed or normalized records never replace them.

### 4.4 Frozen package

The final replay package contains at minimum:

```text
manifest.json
raw_batches/
control_evidence/
quality_minutes/
mapping_snapshot.json
fee_configs/
funding_evidence/
checksums.sha256
```

The package manifest binds:

```text
run_id
start_utc
end_utc
venues
markets
channels
raw batch/frame counts
quality-minute counts
schema version
decoder version
mapping version
fee-config versions
collector commit SHA
analyzer commit SHA
configuration hash
file hashes
manifest hash
```

Any changed, missing, duplicated, or unrecognized member makes final replay fail closed.

### 4.5 Derived checkpoints

A2 does not persist normalized L2 checkpoints. The analyzer may emit derived, hash-bound checkpoints into its own report artifact set:

- one per UTC second when a valid book exists;
- on strict-quality state change;
- at opportunity episode start/end;
- at each simulated entry/exit/settlement.

Derived checkpoints always cite the source raw-frame/batch range and mapping/configuration versions.

## 5. Analyzer component design

### 5.1 Package boundary

Recommended package layout:

```text
src/multi_exchange_engine/shadow_economics/
    __init__.py
    model.py
    config.py
    evidence.py
    frozen_package.py
    reconstruction/
        common.py
        hyperliquid.py
        lighter.py
    mapping.py
    quality.py
    vwap.py
    fees.py
    funding.py
    episodes.py
    price_strategy.py
    funding_strategy.py
    portfolio.py
    verdict.py
    report.py
    cli.py
```

The analyzer package must not import signer, account, private-stream, order-submission, cancellation, transfer, or withdrawal modules.

### 5.2 Reconstructors

A venue reconstructor:

1. accepts only validated venue-native semantic observations plus raw provenance;
2. requires an authoritative snapshot before deltas;
3. applies only valid continuous sequence/nonce transitions;
4. closes its current epoch on gap, source regression, unsupported event, or connection close;
5. cannot resume from a gap without a new valid snapshot;
6. validates all levels before publication;
7. emits immutable `ReconstructedBook` objects with full source provenance.

Book invariants:

- positive finite prices and quantities;
- bids strictly ordered descending after venue-defined aggregation;
- asks strictly ordered ascending;
- no crossed book;
- exact Decimal/fixed-point arithmetic;
- no extrapolation beyond visible depth;
- deterministic duplicate-level handling according to venue semantics.

### 5.3 Economic mapping registry

Each BTC, ETH, and SOL mapping version contains:

```text
canonical base asset
venue symbol and market ID
product/payoff kind
contract multiplier
displayed size unit
price and quantity scales
quote and settlement assets
index/oracle references
mark methodology reference
funding sign convention and schedule
tick/step/minimum rules
source evidence hashes
validity window
review identity
```

Strict admission requires:

- linear perpetual payoff;
- exact multiplier and displayed-size interpretation;
- explicit quote/settlement treatment;
- verified funding sign convention;
- versioned source evidence;
- runtime index divergence at or below 10 bps.

Divergence sensitivity:

```text
≤5 bps: strict subset report
≤10 bps: primary strict gate
10–25 bps: diagnostic only
>25 bps: pair unhealthy
```

Mark and index divergences are stored separately.

### 5.4 Canonical quantity and residual delta

For a target USD notional:

```text
target canonical base quantity
= target USD / common reference index at signal time
```

Each venue quantity is derived from canonical base quantity, exact contract multiplier, and venue quantity step. Rounding is toward lower exposure.

The analyzer stores:

- target USD;
- target canonical base quantity;
- venue-native quantities;
- actual base quantities;
- actual per-leg notionals;
- rounding loss;
- residual canonical delta;
- estimated residual-neutralization cost.

Strict gate:

```text
absolute residual delta after rounding
≤ 0.25% of target canonical base quantity
```

### 5.5 Quality evaluator

Primary strict requirements:

```text
both sessions healthy
snapshot established
continuity valid
books non-crossed
full requested depth available
book age ≤500 ms on each venue
receive-time skew ≤250 ms
mapping verified
index divergence ≤10 bps
rounding residual ≤0.25%
timestamps valid
required fee evidence present
```

Diagnostic mode permits:

```text
book age ≤1000 ms
receive-time skew ≤500 ms
index divergence ≤25 bps
```

Diagnostic results never contribute to `GO`.

### 5.6 VWAP engine

The VWAP engine:

- sweeps authoritative displayed levels only;
- uses exact arithmetic;
- returns `INSUFFICIENT_DEPTH` rather than top-of-book fallback;
- preserves actual quantity, actual notional, VWAP, worst level, and source checkpoint;
- calculates both entry and exit independently;
- supports each configured notional ladder value;
- rejects a scenario if either leg lacks depth at its delayed execution time.

### 5.7 Fee and failure-cost engine

Costs are versioned evidence, never unlabelled scalars.

Required cost components:

- entry taker fees per leg;
- exit taker fees per leg;
- builder/partner fee assumptions;
- residual hedge cost;
- explicit rebalance cost where configured;
- paid failure/rejection fees where venue semantics support them;
- diagnostic infrastructure allocation;
- opportunity decay from delay through actual delayed books.

The report separates:

- gross edge;
- entry costs;
- exit costs;
- carry/funding;
- basis P&L;
- residual/rebalance/failure costs;
- net P&L.

### 5.8 Price/basis simulator

For each strict episode and counterfactual scenario:

1. identify direction from delayed executable books, not signal-time last price;
2. calculate both delayed taker entries;
3. reject if either leg is invalid or insufficient;
4. lock scenario capital;
5. evaluate every fixed-time and convergence exit;
6. consume delayed executable books for both exits;
7. account for all configured costs;
8. emit immutable `PriceTradeSimulation` and episode summary.

No simulated trade may reuse capital before its exit.

### 5.9 Funding simulator

The funding simulator preserves ex-ante and ex-post information separately.

Ex-ante:

- forecast/public funding observation known at entry;
- expected settlement schedule;
- expected round-trip cost;
- expected net carry threshold.

Ex-post:

- realized venue settlement events;
- notional at each settlement;
- signed per-leg cashflow;
- actual basis movement;
- executable exit;
- final net P&L;
- forecast error.

No annualized or normalized display rate enters realized cash accounting.

### 5.10 Portfolio diagnostic

Price and funding strategies have separate primary virtual portfolios.

Portfolio state includes:

- venue cash/equity allocation;
- reserved margin;
- free-margin reserve;
- open positions;
- realized/unrealized P&L by venue;
- blocked opportunities and blocking reason;
- capital-hours;
- idle capital;
- utilization;
- optional rebalance diagnostic events.

The combined strategy portfolio is non-binding diagnostic output.

### 5.11 Verdict engine

Per-strategy verdicts:

- `GO`;
- `NO_GO`;
- `INSUFFICIENT_EVIDENCE`;
- `INVALID_DATASET` for integrity/configuration failure.

Evidence gate:

```text
at least 5 complete UTC data days
at least 95% strict healthy minutes
for BTC, ETH, SOL on both venues
```

If coverage fails, the relevant overall verdict is `INSUFFICIENT_EVIDENCE`, not `NO_GO`.

A strategy receives `GO` only if all are true for the primary 5/10 bps thresholds and primary USD 1,000/USD 5,000 sizes as applicable:

1. at least 20 independent eligible episodes;
2. total net P&L is positive;
3. median net P&L is positive;
4. result remains positive at 300 ms and 500 ms symmetric delay;
5. USD 1,000 result is positive;
6. USD 5,000 result is non-negative;
7. operator and conservative product fee cases pass;
8. no single trade contributes more than 25% of total P&L;
9. for funding, ex-post realized funding P&L is positive.

`NO_GO` requires sufficient valid evidence and failure to meet the primary strategy gate. A diagnostic or maker-only positive result cannot prevent `NO_GO`.

Overall verdict:

- `GO` if at least one primary strategy receives `GO`;
- `NO_GO` if both primary strategies have sufficient evidence and neither receives `GO`;
- `INSUFFICIENT_EVIDENCE` if no strategy receives `GO` and at least one primary strategy lacks mandatory evidence;
- `INVALID_DATASET` if frozen-package validation or deterministic replay fails.

## 6. Operating modes

### 6.1 Live preview

Live preview:

- reads committed A2 evidence through a read-only PostgreSQL role/view;
- processes only durable batches;
- displays coverage, continuity, books, mapping status, and preliminary scenarios;
- identifies collector/analyzer defects early;
- cannot publish a binding verdict;
- clearly labels all results `PREVIEW`.

### 6.2 Final replay

Final replay:

- starts from an empty analyzer state;
- reads a frozen evidence package;
- verifies every manifest and member hash;
- verifies exact supported schema, decoder, mapping, fee, and analyzer configuration versions;
- streams batches in canonical order;
- emits canonical JSON and Markdown reports;
- is run twice in fresh processes;
- requires byte-identical canonical outputs and matching terminal hash;
- is the only verdict authority.

## 7. Report artifacts

Recommended output structure:

```text
outputs/shadow-economics/<run_id>/
    dataset-manifest.json
    analyzer-config.json
    mapping-snapshot.json
    coverage.json
    quality-rejections.json
    reconstructed-checkpoints.ndjson.gz
    price-episodes.ndjson.gz
    funding-episodes.ndjson.gz
    price-matrix.json
    funding-matrix.json
    portfolio-diagnostics.json
    latency-diagnostics.json
    fee-and-failure-costs.json
    verdict.json
    report.md
    checksums.sha256
```

`verdict.json` is canonical and machine-readable. `report.md` is a projection.

The report must show:

- strict coverage per stream;
- invalid/gap/reconnect/stale counts;
- opportunity counts by threshold and asset;
- executable capacity by size;
- survival at every delay scenario;
- gross-to-net cost waterfall;
- fixed-horizon and convergence exits;
- funding forecast error and realized cashflows;
- total, median, mean, worst trade, drawdown, win rate, holding time, capital-hours;
- portfolio utilization and blocked opportunities;
- concentration of P&L;
- exact gate pass/fail reasons;
- diagnostic-versus-strict delta;
- dataset/configuration/commit identities.

## 8. Error handling and fail-closed behavior

Final replay exits nonzero and emits no verdict on:

- bad manifest or file hash;
- missing, duplicate, or reordered raw batch identity;
- unsupported schema/decoder/configuration version;
- mapping version mismatch;
- duplicate frame identity with differing payload;
- inability to establish an authoritative snapshot;
- impossible venue sequence/nonce transition;
- non-deterministic second replay;
- missing required fee evidence;
- ambiguous realized funding evidence;
- arithmetic non-finite value or precision-bound violation;
- derived record without complete raw provenance.

Expected market/data invalidity rejects the affected interval or scenario with typed reason codes. It does not crash the entire replay unless integrity or determinism is compromised.

## 9. Testing strategy

### 9.1 Unit tests

- exact quantity/multiplier conversion;
- round-down venue sizing;
- residual gate;
- full-depth VWAP;
- no top-of-book fallback;
- fee/cost attribution;
- funding sign and settlement cashflow;
- episode clustering and cooldown;
- convergence exits;
- capital locks and prioritization;
- verdict gates;
- canonical serialization.

### 9.2 Venue reconstruction tests

- snapshot plus valid deltas;
- delta before snapshot;
- gap and recovery snapshot;
- duplicate and out-of-order events;
- source-time regression;
- reconnect/new epoch;
- malformed/non-finite/crossed book;
- exact raw provenance linkage.

### 9.3 Fault and mutation tests

- hash tamper;
- batch deletion/duplication/reorder;
- mapping mutation;
- fee config mutation;
- decoder version drift;
- funding event ambiguity;
- stale/skew/index-divergence boundaries;
- partial depth;
- deterministic tie-breaks;
- hostile Decimal context;
- forced worker/event ordering variation.

### 9.4 Deterministic replay tests

- same frozen package in two fresh processes;
- byte-identical canonical JSON;
- identical terminal hash;
- bounded memory per raw batch;
- no network access during final replay;
- no clock dependence beyond frozen evidence/configuration.

### 9.5 Boundary tests

Static and runtime tests must prove the analyzer has no:

- signer or private-key import;
- private/account WebSocket subscription;
- order/cancel/transfer/withdraw method;
- venue credential environment variable;
- direct exchange network client in final replay;
- ability to mutate A2 evidence tables.

## 10. Agent workstreams

Implementation begins only after this written specification is reviewed.

### 10.1 Architect

Owns:

- component contracts;
- evidence/verdict schemas;
- dependency direction;
- A2/analyzer boundary;
- ADR compatibility;
- final architecture review.

May not implement venue/economics logic before interface review.

### 10.2 Evidence/data engineer

Owns:

- read-only A2 views;
- `EvidenceReader` implementations;
- frozen-package format and export;
- integrity/hash verification;
- bounded batch streaming.

May not add normalized economics to A2.

### 10.3 Quant/economics analyst

Owns:

- fee evidence/configuration;
- funding conventions and settlement accounting;
- price/funding formulas;
- fixed scenario matrix;
- verdict mathematics;
- review of report interpretation.

May not tune thresholds after final data inspection.

### 10.4 Backend programmer

Owns:

- reconstructors;
- quality evaluator;
- VWAP;
- episode engine;
- price/funding simulators;
- portfolio simulator;
- CLI/report integration.

Uses TDD and exact arithmetic boundaries.

### 10.5 QA/adversarial agent

Owns:

- specification tests;
- venue payload mutations;
- gap/reconnect/staleness tests;
- deterministic replay tests;
- report gate verification;
- failure-to-verdict traceability.

Must develop negative tests independently of the implementation agent.

### 10.6 Security/boundary reviewer

Owns:

- public-only dependency scan;
- credential/private capability audit;
- filesystem/network boundary;
- frozen-package tamper model;
- live-trading prohibition review.

### 10.7 Product/research analyst

Owns a parallel non-blocking lane:

- user-needs synthesis;
- interviews/validation design;
- no feature promotion without evidence gate.

This role does not change the seven-day technical scenario matrix.

### 10.8 Coordinator/integrator

Owns:

- workstream dependency order;
- coherent commits;
- `handoff.md` updates;
- verification evidence;
- conflict resolution;
- final sprint report.

## 11. Seven-day delivery sequence

### Day 1 — contract freeze and evidence readiness

- approve this design;
- write executable implementation plan;
- create isolated implementation branch/worktree;
- verify current A2 public-only boundary and storage contracts;
- verify capture can start without private capabilities;
- freeze mappings, fee config schemas, scenario matrix, and report schemas;
- start/continue evidence capture as early as possible.

### Day 2 — readers and reconstruction

- implement frozen/live `EvidenceReader` contracts;
- implement or adapt frozen-package export/validation;
- implement Hyperliquid and Lighter L2 reconstructors;
- emit deterministic derived checkpoints;
- expose preview coverage and reconstruction health.

### Day 3 — mapping, quality, VWAP

- implement BTC/ETH/SOL mapping snapshots;
- implement index/mark divergence evidence;
- implement strict/diagnostic quality evaluators;
- implement canonical sizing, residual gate, and full-depth VWAP;
- run replay against fixtures and first durable live evidence.

### Day 4 — price/basis analysis

- implement episode clustering;
- implement independent delay legs;
- implement entry and fixed/convergence exit simulations;
- implement cost waterfall;
- produce preliminary price matrix preview.

### Day 5 — funding and portfolio

- implement forecast/realized funding evidence separation;
- implement settlement cashflow accounting;
- implement funding episode simulation;
- implement capital allocation, leverage, reserve, prioritization, and utilization diagnostics.

### Day 6 — determinism, adversarial review, reporting

- finish canonical report artifacts;
- run mutation/fault suite;
- run fresh-process replay equality;
- review public-only boundary;
- fix only specification violations, not economic thresholds;
- prepare freeze procedure.

### Day 7 — freeze and verdict

- close the measurement window available at the deadline;
- export and verify the frozen package;
- run two fresh-process final replays;
- compare canonical bytes and terminal hashes;
- issue `GO`, `NO_GO`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET`;
- record blockers, coverage, and exact next decision.

If five full days or 95% strict coverage are unavailable, the correct output is `INSUFFICIENT_EVIDENCE`. The sprint is still complete if the system proves and reports that result correctly.

## 12. Acceptance criteria

The design increment is complete when:

- this specification is committed and reviewed;
- the implementation plan maps every task to a test and commit boundary.

The seven-day implementation increment is complete when:

1. A2 remains public/read-only and does not import economics/trading logic;
2. the analyzer has no private/trading capability;
3. both evidence readers satisfy the same contract;
4. frozen-package tampering fails closed;
5. BTC, ETH, and SOL mappings are versioned and evidence-bound;
6. L2 reconstruction handles gaps/reconnects deterministically;
7. strict and diagnostic quality outputs are separate;
8. full-depth VWAP has no fallback;
9. all frozen price/funding/capital/delay/fee scenarios are reported;
10. independent episodes and capital locks prevent duplicate opportunity counting;
11. final replay is byte-identical across two fresh processes;
12. the verdict engine applies the frozen coverage and GO gates exactly;
13. no final report calls public RTT or market-data age execution latency;
14. no live order, credential, or withdrawal path exists;
15. `handoff.md` records exact verification evidence and next action.

## 13. Risks and mitigations

### Evidence collection starts too late

Mitigation: begin capture on Day 1 before analyzer completion. A short dataset yields `INSUFFICIENT_EVIDENCE`, not fabricated extrapolation.

### Funding settlement evidence is incomplete

Mitigation: separate funding verdict from price verdict; exclude ambiguous settlements; report the evidence gap explicitly.

### A2 scope creep

Mitigation: retain static public-capability boundary; analyzer owns all normalized/economic logic.

### Dataset volume makes replay slow

Mitigation: stream one bounded raw batch at a time; persist derived checkpoints; benchmark early; optimize without changing arithmetic or ordering.

### Scenario explosion

Mitigation: frozen scenario IDs, deterministic iteration, one shared calculation core, counterfactual matrix outputs rather than duplicated code paths.

### Attractive result depends on maker fills or 3x leverage

Mitigation: maker and 3x outputs remain diagnostic and cannot issue `GO`.

### Operator fee input is unavailable

Mitigation: product-case report continues, but overall `GO` is blocked as `INSUFFICIENT_INPUT` for the operator gate.

### Public timestamps are not comparable

Mitigation: distinguish receive skew, source-time age, and assumed execution delay; source timestamps are used only when their semantics are verified.

## 14. Implementation transition gate

No implementation begins until the repository owner reviews this committed specification.

After approval, the next workflow is:

1. invoke the writing-plans process;
2. create a task-by-task TDD implementation plan;
3. select isolated worktree/branch execution;
4. dispatch role-specific agents only within the contracts above;
5. keep live execution disabled throughout the sprint.
