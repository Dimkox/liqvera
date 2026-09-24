# Stage-A-v2 Strategy Economics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, exact, read-only Stage-A-v2 analyzer that reconstructs public Hyperliquid/Lighter evidence, simulates basis convergence and realized funding under complete costs and capital constraints, and emits a typed evidence-linked decision without any execution capability.

**Architecture:** M5 is implemented only in the separately installable `mee_contracts` and `mee_readonly_analyzer` distributions established by M1-M4. Immutable frozen evidence enters through an `EvidenceReader`; reconstruction, VWAP, costs, episodes, capital, strategies, portfolio, decision, report, and replay form one deterministic `AnalysisRun` graph. Every unresolved economic parameter is a required field of an owner-approved, hash-bound configuration document; omission, an unapproved hash, or a value outside the typed contract fails closed.

**Tech Stack:** Python 3.12, standard-library frozen dataclasses/enums/Decimal/Fraction/hashlib/json, unittest, PostgreSQL 16/17 evidence-reader integration, separately installed wheels, Claw self-hosted CI.

## Global Constraints

- Requirements: `PROD-001` through `PROD-014`, `ARCH-001` through `ARCH-009`, `DATA-003` through `DATA-010`, `DATA-016`, `DATA-020`, `DATA-023`, `STRAT-001` through `STRAT-010`, `GRAPH-001` through `GRAPH-012`, `CI-001` through `CI-007`, and `SEC-001` through `SEC-006` from `docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md`.
- M0-M4 acceptance receipts are prerequisites. Do not implement this plan while the architecture approval, distribution, evidence topology, frozen-package, analyzer-role, PostgreSQL matrix, or execution-absence gates are incomplete.
- Scope is public Hyperliquid and Lighter evidence for BTC, ETH, and SOL markets. SOL is a market asset only; no Solana-chain module, RPC, program, Jupiter, Jito, or Raydium dependency is permitted.
- Binding acquisition is seven calendar days with at least five complete UTC days, at least `0.95` strict healthy minutes, verified mappings, and at least 20 independent completed episodes.
- Binding economics require total net P&L `> 0`, median episode net P&L `> 0`, USD 1,000 net `> 0`, USD 5,000 net `>= 0`, survival at symmetric 300 ms and 500 ms delays, survival under both owner-approved frozen fee cases, largest-episode contribution `< 0.25`, and realized funding cashflows for a funding-specific continuation reason.
- Decisions are exactly `INVALID_DATASET`, `INSUFFICIENT_EVIDENCE`, `STOP`, and `EXTEND_LONGER_SHADOW`, in that precedence. There is no `GO`, `NO_GO`, `KILL`, or live-canary decision.
- `EXTEND_LONGER_SHADOW` freezes the extension target at 7-14 complete UTC days and at least 100 independent completed lifecycles. It does not authorize trading.
- All money, price, quantity, fee, funding, basis, cost, and P&L arithmetic uses `Fraction` internally and canonical exact decimal rendering at boundaries. Floats, booleans-as-integers, non-finite decimals, and ambient decimal-context dependence are rejected.
- Final replay reads only a hash-verified frozen package, uses no network or host clock, does not mutate `CaptureRun`, and produces byte-identical canonical output in two fresh processes.
- Grid, DCA, Infinity Grid, maker-fill claims, live/private/account adapters, signers, orders, cancels, transfers, withdrawals, n8n, asset-specific live bots, and Solana-chain strategies remain unreachable from source imports, installed files, dependencies, entry points, images, CI, and deployment.
- Do not invent unresolved economics. The fields listed in Task 1 are mandatory, have no defaults, and require an owner approval record binding the exact configuration SHA-256 before binding evidence begins.
- Tests are `unittest.TestCase` tests. Focused commands use `python3 -B -m unittest ... -v`; authoritative evidence is produced only by exact-SHA Claw jobs.
- Every task updates `config/traceability/stage-a-v2.yaml` and `handoff.md` in the same coherent commit and links requirement IDs, tests, Claw gate, evidence nodes, and rollback.

---

## Owner-Approved Binding Verdict Granularity

On 2026-08-11 the owner selected **Option A — frozen-universe deterministic
portfolio aggregate** as the only Stage-A-v2 binding rule. The configuration
schema must encode the closed value
`FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE`; any other, missing, legacy, or unknown
value fails with `BINDING_VERDICT_GRANULARITY_UNAPPROVED`. Tests, verdict reason
codes, report aggregation, and traceability implement this rule consistently:

- Before acquisition, the owner-approved manifest freezes
  every admitted `(strategy, asset, direction)` cell and deterministic capital
  weight. A cell may be excluded only by that pre-window manifest or because
  its economic mapping was not approved before acquisition; observed P&L,
  delays, fees, capacity, concentration, or other binding-window results can
  never exclude or reweight it. Every admitted cell must have complete required
  non-economic evidence: in-scope complete-day coverage, strict-health
  evidence, verified mapping, both frozen fee cases, and realized settlement
  evidence when it supports a funding-specific reason. A missing requirement
  yields the applicable `INVALID_DATASET` or `INSUFFICIENT_EVIDENCE` for the
  run, never evaluation over the remaining cells. The existing minimum 20
  independent episodes applies to the binding dataset aggregate unless a
  separately approved per-cell minimum is frozen before acquisition. All
  completed and failed attempts enter the portfolio with frozen weights. The
  economic predicates bind that aggregate; per-cell economics are mandatory
  reconciled report slices but cannot independently produce `STOP` or permit
  post-observation selection.

Tests prove that post-acquisition removal/reweighting
changes the configuration hash and invalidates the run, cell order cannot
change canonical portfolio bytes, missing/invalid cells obey decision
precedence, and per-cell report slices reconcile exactly to aggregate weights,
attempts, costs, and P&L. A negative cell stays in aggregate inputs and an
insufficient admitted cell cannot be silently dropped.

## File Structure

```text
packages/contracts/src/mee_contracts/
  exact.py                 exact input validation and Fraction rendering
  identity.py              versioned economic identity
  strategy.py              strategy/configuration value contracts
  economics.py             fills, costs, episodes, capital and P&L records
  decision.py              decision and reason enums

packages/readonly-analyzer/src/mee_readonly_analyzer/
  config.py                strict owner-approved configuration loader
  reconstruction/common.py reconstruction epoch state machine
  reconstruction/hyperliquid.py
  reconstruction/lighter.py
  vwap.py                  full-depth executable sweeps
  costs.py                 complete lifecycle cost attribution
  episodes.py              independent episode tracker
  capital.py               deterministic virtual capital locks
  delays.py                independent delayed leg lookup and residuals
  strategies/basis_convergence.py
  strategies/realized_funding.py
  diagnostics/paired_basis_trailing.py
  portfolio.py             deterministic aggregation/concentration
  verdict.py               strict precedence and typed reasons
  report.py                canonical report projection
  replay.py                network/clock-free frozen replay
  cli.py                   frozen-package-only entry point

config/stage-a-v2/
  scenario.schema.json          closed schema for economic parameters
  strategy-manifest.schema.json closed schema for primary/diagnostic strategies
  fee-cases.schema.json         closed schema for verified taker fee evidence
  README.md                     owner materialization and approval procedure

tests/fixtures/stage-a-v2/
  scenario-valid.json           non-binding test fixture
  strategy-manifest-valid.json  non-binding test fixture
  fee-cases-valid.json          non-binding test fixture
  approval-valid.json           fixture-only approval

tests/contracts/
tests/readonly_analyzer/
tests/architecture/
scripts/check-stage-a-v2-boundary.py
config/traceability/stage-a-v2.yaml
```

### Task 1: Freeze exact contracts, economic identity, and owner-approved configuration

**Requirements:** DATA-005, DATA-006, STRAT-005, STRAT-008, PROD-005.

**Files:**
- Modify: `packages/contracts/src/mee_contracts/exact.py`
- Create: `packages/contracts/src/mee_contracts/identity.py`
- Create: `packages/contracts/src/mee_contracts/strategy.py`
- Modify: `packages/readonly-analyzer/src/mee_readonly_analyzer/config.py`
- Create: `config/stage-a-v2/scenario.schema.json`
- Create: `config/stage-a-v2/strategy-manifest.schema.json`
- Create: `config/stage-a-v2/fee-cases.schema.json`
- Create: `config/stage-a-v2/README.md`
- Create: `tests/fixtures/stage-a-v2/{scenario-valid,strategy-manifest-valid,fee-cases-valid,approval-valid}.json`
- Create: `tests/contracts/test_exact.py`
- Create: `tests/contracts/test_identity.py`
- Create: `tests/readonly_analyzer/test_config.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: M2 exact/canonical encoding contract and M4 immutable evidence IDs.
- Produces: `EconomicIdentity`, `StrategyConfig`, `ApprovedConfig`, closed
  schemas, and `load_approved_config()` for every later task. It does not
  produce a binding experiment configuration before the owner gate.

```python
@dataclass(frozen=True, slots=True)
class EconomicIdentity:
    underlying: str
    product_kind: str
    payoff_kind: str
    multiplier: Fraction
    quote_asset: str
    settlement_asset: str
    collateral_asset: str
    price_unit: str
    quantity_unit: str
    venue_market_id: str
    valid_from_ns: int
    valid_until_ns: int | None
    source_evidence_ids: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class OwnerApproval:
    approval_id: str
    approver: str
    approved_config_sha256: str
    approved_before_ns: int

@dataclass(frozen=True, slots=True)
class StrategyConfig:
    schema_id: str
    binding_verdict_granularity: Literal["FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE"]
    acquisition_days: int
    minimum_complete_utc_days: int
    minimum_healthy_fraction: Fraction
    episode_cooldown_ns: int
    basis_denominator: Literal["LONG_ENTRY_VWAP", "SHORT_ENTRY_VWAP", "MIDPOINT"]
    basis_entry_bps: tuple[Fraction, ...]
    basis_exit_rule: BasisExitRule
    funding_schedule_rules: tuple[FundingScheduleRule, ...]
    capital_policy: CapitalPolicy
    residual_policy: ResidualPolicy
    trailing_policy: TrailingPolicy
    infrastructure_cost_policy: InfrastructureCostPolicy
    fee_case_ids: tuple[str, str]
    approval: OwnerApproval

def load_approved_config(path: Path, approval_path: Path) -> ApprovedConfig: ...
```

Required fields with no defaults are: the closed binding-verdict granularity,
pre-window admitted cell universe and deterministic capital weights, basis
denominator/sign convention, entry thresholds, exit rule, episode cooldown,
funding schedule/sign/currency conversion, total virtual capital, per-venue
allocation, leverage/margin convention, minimum free margin, lock priority,
residual threshold/venue/timeout/missing-depth rule, trailing
activation/watermark/trail/minimum hold/maximum hold/tie/missing-book rules,
infrastructure allocation, rebalance trigger, and two fee-case evidence records.
JSON `null`, absent keys, extra keys, unapproved hashes, and approval timestamps
at or after binding acquisition start reject.

- [ ] **Step 1: Write exact and omission tests**

```python
class ApprovedConfigTests(unittest.TestCase):
    def test_every_unresolved_parameter_is_required(self) -> None:
        document = json.loads(SCENARIO_FIXTURE.read_text(encoding="utf-8"))
        for field_path in REQUIRED_PARAMETER_PATHS:
            with self.subTest(field_path=field_path):
                mutated = delete_path(copy.deepcopy(document), field_path)
                with self.assertRaisesRegex(ConfigError, "REQUIRED_FIELD_MISSING"):
                    load_documents(mutated, APPROVAL_DOCUMENT)

    def test_exact_approved_hash_is_binding(self) -> None:
        approval = replace(APPROVAL_DOCUMENT, approved_config_sha256="0" * 64)
        with self.assertRaisesRegex(ConfigError, "CONFIG_NOT_OWNER_APPROVED"):
            load_documents(SCENARIO_DOCUMENT, approval)

    def test_float_nonfinite_and_bool_aliases_reject(self) -> None:
        for value in (0.95, "NaN", True):
            with self.subTest(value=value):
                document = with_path(SCENARIO_DOCUMENT, "minimum_healthy_fraction", value)
                with self.assertRaises(ConfigError):
                    load_documents(document, APPROVAL_DOCUMENT)
```

- [ ] **Step 2: Run the focused RED test on Claw**

Run:

```bash
python3 -B -m unittest tests.contracts.test_exact tests.contracts.test_identity tests.readonly_analyzer.test_config -v
```

Expected: FAIL because the existing M1 distributions do not yet export
`EconomicIdentity`, `StrategyConfig`, `ApprovedConfig`, or strict Stage-A-v2
loading; the pre-existing M0-M4 suite remains green. A missing distribution is
an invalid prerequisite, not the expected RED.

- [ ] **Step 3: Implement strict exact conversion and identity validation**

```python
def require_fraction(value: object, field: str) -> Fraction:
    if type(value) is not str:
        raise ExactValueError(f"{field}: CANONICAL_DECIMAL_STRING_REQUIRED")
    decimal = Decimal(value)
    if not decimal.is_finite() or decimal.is_signed() and decimal.is_zero():
        raise ExactValueError(f"{field}: FINITE_CANONICAL_VALUE_REQUIRED")
    return fraction_from_decimal(decimal)

def identities_match(left: EconomicIdentity, right: EconomicIdentity) -> bool:
    return (
        left.underlying,
        left.product_kind,
        left.payoff_kind,
        left.multiplier,
        left.quote_asset,
        left.settlement_asset,
        left.collateral_asset,
        left.price_unit,
        left.quantity_unit,
    ) == (
        right.underlying,
        right.product_kind,
        right.payoff_kind,
        right.multiplier,
        right.quote_asset,
        right.settlement_asset,
        right.collateral_asset,
        right.price_unit,
        right.quantity_unit,
    )
```

- [ ] **Step 4: Implement closed-schema configuration loading and approval binding**

Parse JSON with duplicate-key rejection and `parse_float`/`parse_constant` rejection. Compare `sha256(canonical_config_bytes).hexdigest()` to `OwnerApproval.approved_config_sha256`; do not create a default configuration in Python.

Create only schemas, documentation, and explicitly non-binding test fixtures in
this task. The three binding JSON documents are materialized in the Owner
Approval Gate below after every economic value and verdict granularity are
approved; their exact combined hash is then recorded as a new reviewed commit.

- [ ] **Step 5: Run GREEN tests and installed-contract check**

```bash
python3 -B -m unittest tests.contracts.test_exact tests.contracts.test_identity tests.readonly_analyzer.test_config -v
python3 -m pip install --no-deps ./packages/contracts ./packages/readonly-analyzer
python3 -m pip check
```

Expected: PASS; mutation cases emit stable errors; both distributions import from their installed wheels.

- [ ] **Step 6: Update traceability and handoff**

Add DATA-005/006 and STRAT-008 nodes with `implements`, `validated_by`, `gated_by`, `evidenced_by`, and `rolled_back_by` edges. Record that binding acquisition is blocked until the owner approval hash exists.

- [ ] **Step 7: Commit the coherent unit**

```bash
git add packages/contracts packages/readonly-analyzer/src/mee_readonly_analyzer/config.py config/stage-a-v2 tests/contracts tests/readonly_analyzer/test_config.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(contracts): freeze Stage A v2 economic configuration"
```

### Task 2: Reconstruct fail-closed venue books

**Requirements:** DATA-007, DATA-008, DATA-020, PROD-005.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/common.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/hyperliquid.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction/lighter.py`
- Create: `tests/readonly_analyzer/test_reconstruction_common.py`
- Create: `tests/readonly_analyzer/test_reconstruction_hyperliquid.py`
- Create: `tests/readonly_analyzer/test_reconstruction_lighter.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: `EvidenceReader.iter_raw_envelopes() -> Iterator[RawPublicEnvelope]` from M4 and `EconomicIdentity` from Task 1.
- Produces: deterministic `ReconstructionEvent` streams for Task 3 and every strategy.

```python
@dataclass(frozen=True, slots=True)
class ReconstructedBook:
    venue: Venue
    market_id: str
    epoch_id: str
    sequence: int
    effective_at_ns: int
    bids: tuple[PriceLevel, ...]
    asks: tuple[PriceLevel, ...]
    source_evidence_ids: tuple[str, ...]

def reconstruct(records: Iterable[RawPublicEnvelope]) -> tuple[ReconstructionEvent, ...]: ...
```

- [ ] **Step 1: Write venue state-machine tests**

```python
class ReconstructionTests(unittest.TestCase):
    def test_gap_closes_epoch_until_new_snapshot(self) -> None:
        events = reconstruct((snapshot(10), delta(11), delta(13), delta(14), snapshot(20)))
        self.assertEqual(kinds(events), ("BOOK", "BOOK", "EPOCH_CLOSED", "IGNORED", "BOOK"))
        self.assertEqual(events[2].reason, ReconstructionReason.SEQUENCE_GAP)

    def test_audit_time_cannot_change_output(self) -> None:
        left = reconstruct(with_audit_times(FIXTURE, (1, 2, 3)))
        right = reconstruct(with_audit_times(FIXTURE, (9, 8, 7)))
        self.assertEqual(canonical_semantic_bytes(left), canonical_semantic_bytes(right))
```

Cover authoritative snapshot, valid delta, gap, regression, duplicate, reconnect, malformed positive/finite levels, ordering, crossed spread, unsupported transition, and recovery only after a new snapshot.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_reconstruction_common tests.readonly_analyzer.test_reconstruction_hyperliquid tests.readonly_analyzer.test_reconstruction_lighter -v
```

Expected: FAIL importing reconstruction modules.

- [ ] **Step 3: Implement the epoch state machine and venue transitions**

Use only effective evidence time and canonical sequence/nonce. Emit one typed closure event on the first invalid transition and ignore deltas until a new authoritative snapshot.

- [ ] **Step 4: Run GREEN plus A2 semantic regressions**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_reconstruction_common tests.readonly_analyzer.test_reconstruction_hyperliquid tests.readonly_analyzer.test_reconstruction_lighter tests.a2.test_hyperliquid_semantics tests.a2.test_lighter_semantics -v
```

Expected: PASS with byte-identical streams under audit-time mutation.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/reconstruction tests/readonly_analyzer/test_reconstruction_* config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): reconstruct public books fail closed"
```

### Task 3: Price all four lifecycle legs with full-depth VWAP

**Requirements:** DATA-005, DATA-009, PROD-001, STRAT-002.

**Files:**
- Create: `packages/contracts/src/mee_contracts/economics.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/vwap.py`
- Create: `tests/contracts/test_economics.py`
- Create: `tests/readonly_analyzer/test_vwap.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: `ReconstructedBook`, `EconomicIdentity`, canonical quantity.
- Produces: `ExecutableFill` for entry-long, entry-short, exit-long, and exit-short.

```python
@dataclass(frozen=True, slots=True)
class ExecutableFill:
    side: Side
    canonical_quantity: Fraction
    venue_quantity: Fraction
    notional_quote: Fraction
    vwap: Fraction
    worst_price: Fraction
    consumed_levels: int

def sweep_depth(book: ReconstructedBook, side: Side, canonical_quantity: Fraction, identity: EconomicIdentity) -> ExecutableFill: ...
```

- [ ] **Step 1: Write exact sweep and rejection tests**

Test partial final level, bid/ask ordering, multiplier normalization, large/tiny rationals, insufficient depth, invalid tail, crossed book, and immutable input. Assert no top-of-book fallback.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.contracts.test_economics tests.readonly_analyzer.test_vwap -v
```

Expected: FAIL importing `ExecutableFill` or `sweep_depth`.

- [ ] **Step 3: Implement exact full-depth sweep**

Accumulate `Fraction` price × venue quantity until the exact canonical target is met; otherwise raise `DepthRejected(DEPTH_INSUFFICIENT)`.

- [ ] **Step 4: Run GREEN and legacy VWAP conformance**

```bash
python3 -B -m unittest tests.contracts.test_economics tests.readonly_analyzer.test_vwap tests.shadow.test_vwap tests.shadow.test_quantity -v
```

Expected: PASS; existing A1 exact vectors remain unchanged.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/contracts/src/mee_contracts/economics.py packages/readonly-analyzer/src/mee_readonly_analyzer/vwap.py tests/contracts/test_economics.py tests/readonly_analyzer/test_vwap.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): calculate executable lifecycle VWAP"
```

### Task 4: Attribute fees, funding, delay decay, residuals, rebalance, failures, and infrastructure

**Requirements:** STRAT-003, STRAT-008, STRAT-010, PROD-010, PROD-011.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/costs.py`
- Create: `tests/readonly_analyzer/test_costs.py`
- Modify: `packages/contracts/src/mee_contracts/economics.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: four `ExecutableFill` records, two approved taker fee cases, realized settlement records, and owner-approved cost policies.
- Produces: `EpisodeCosts` and `EpisodePnl`.

```python
@dataclass(frozen=True, slots=True)
class EpisodeCosts:
    entry_fees: Fraction
    exit_fees: Fraction
    realized_funding_cashflow: Fraction
    holding_cost: Fraction
    delay_decay: Fraction
    failed_attempt_cost: Fraction
    residual_neutralization_cost: Fraction
    rebalance_cost: Fraction
    infrastructure_allocation: Fraction

def calculate_episode_pnl(entry: PairedFill, exit: PairedFill, costs: EpisodeCosts) -> EpisodePnl: ...
```

- [ ] **Step 1: Write complete-attribution tests**

```python
class CostTests(unittest.TestCase):
    def test_net_identity_contains_every_cost(self) -> None:
        result = calculate_episode_pnl(ENTRY, EXIT, COSTS)
        self.assertEqual(result.net_quote, result.gross_quote + COSTS.realized_funding_cashflow - sum(COSTS.debits))

    def test_unknown_fee_is_not_zero(self) -> None:
        with self.assertRaisesRegex(CostEvidenceError, "FEE_CASE_INCOMPLETE"):
            price_fee(FILL, incomplete_fee_case())
```

Also test minimum fee per synthetic order, validity windows, rounding rules, funding currency conversion evidence, failed fills, rebalance triggers, and exact negative P&L.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_costs -v
```

Expected: FAIL importing `calculate_episode_pnl`.

- [ ] **Step 3: Implement the auditable P&L identity**

Do not net forecasts into cashflow. Store forecast funding only as an ex-ante metric; only signed settlement evidence populates `realized_funding_cashflow`.

- [ ] **Step 4: Run GREEN and provenance regressions**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_costs tests.shadow.test_provenance -v
```

Expected: PASS; every successful and failed attempt has a cost ledger.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/contracts/src/mee_contracts/economics.py packages/readonly-analyzer/src/mee_readonly_analyzer/costs.py tests/readonly_analyzer/test_costs.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): attribute complete episode economics"
```

### Task 5: Count independent episodes and lock virtual capital

**Requirements:** STRAT-009, STRAT-010, PROD-009.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/episodes.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/capital.py`
- Create: `tests/readonly_analyzer/test_episodes.py`
- Create: `tests/readonly_analyzer/test_capital.py`
- Modify: `packages/contracts/src/mee_contracts/economics.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: ordered strategy checkpoints and approved cooldown/capital policy.
- Produces: independent `CompletedEpisode` records and immutable `CapitalEvent` ledger.

```python
class EpisodeTracker:
    def observe(self, checkpoint: StrategyCheckpoint) -> tuple[EpisodeEvent, ...]: ...
    def seal(self, end_ns: int) -> tuple[CompletedEpisode, ...]: ...

class VirtualCapitalLedger:
    def try_lock(self, request: CapitalRequest) -> CapitalDecision: ...
    def release(self, episode_key: EpisodeKey, effective_at_ns: int) -> CapitalRelease: ...
```

- [ ] **Step 1: Write independence and contention tests**

Test false→true open, continuous qualification as one episode, configured close, incomplete lifecycle exclusion, cooldown, UTC boundary, direction separation, deterministic priority, per-venue fragmentation, minimum free margin, full-lifecycle locks, release-on-terminal only, and no capital reuse while locked.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_episodes tests.readonly_analyzer.test_capital -v
```

Expected: FAIL importing episode/capital modules.

- [ ] **Step 3: Implement one active lifecycle per strategy/asset/direction**

Open only on a false→true entry transition. Keep qualification ticks inside the same lifecycle. Close using the strategy's frozen exit rule. Reject reopen before `episode_cooldown_ns`.

- [ ] **Step 4: Implement deterministic locks**

Sort simultaneous requests by `(effective_at_ns, strategy_rank, asset_rank, direction, episode_id)` from approved config. Lock venue capital through terminalization and record rejected requests as failed-attempt evidence.

- [ ] **Step 5: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_episodes tests.readonly_analyzer.test_capital -v
```

Expected: PASS under reversed input iteration and hostile hash seeds.

- [ ] **Step 6: Update graph/handoff and commit**

```bash
git add packages/contracts/src/mee_contracts/economics.py packages/readonly-analyzer/src/mee_readonly_analyzer/episodes.py packages/readonly-analyzer/src/mee_readonly_analyzer/capital.py tests/readonly_analyzer/test_episodes.py tests/readonly_analyzer/test_capital.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): enforce episodes and virtual capital locks"
```

### Task 6: Model delayed independent legs and residual neutralization

**Requirements:** PROD-001, PROD-010, STRAT-002, STRAT-010.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/delays.py`
- Create: `tests/readonly_analyzer/test_delays.py`
- Modify: `packages/contracts/src/mee_contracts/economics.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: paired intent, reconstructed-book index, approved delay/residual policy.
- Produces: `DelayedPairedFill` and `ResidualOutcome` for both primary strategies and the diagnostic.

```python
def apply_independent_leg_delay(intent: PairedIntent, books: BookIndex, delay: DelayScenario) -> DelayedPairedFill: ...

def neutralize_residual(paired_fill: DelayedPairedFill, books: BookIndex, policy: ResidualPolicy) -> ResidualOutcome: ...
```

- [ ] **Step 1: Write delayed-fill and residual tests**

Test 300/300 and 500/500, first canonical checkpoint at or after each target time, unequal leg depth, missing delayed book, insufficient depth, canonical multiplier-normalized residual, later taker neutralization, timeout, and missing neutralization depth. Assert residual cost includes VWAP, fee, and delay.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_delays -v
```

Expected: FAIL importing delay functions.

- [ ] **Step 3: Implement independent lookup and fail-closed residual handling**

Never synthesize simultaneous fills or probabilistic maker fills. Missing target evidence is a typed failed attempt; unneutralized residual prevents a successful lifecycle.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_delays tests.readonly_analyzer.test_vwap tests.readonly_analyzer.test_costs -v
```

Expected: PASS with complete residual cost lineage.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/contracts/src/mee_contracts/economics.py packages/readonly-analyzer/src/mee_readonly_analyzer/delays.py tests/readonly_analyzer/test_delays.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): model delayed fills and residual costs"
```

### Task 7: Admit executable basis convergence

**Requirements:** STRAT-001, STRAT-002, PROD-001, PROD-010.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/strategies/basis_convergence.py`
- Create: `tests/readonly_analyzer/test_basis_convergence.py`
- Modify: `config/stage-a-v2/strategy-manifest.json`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: approved basis sign/denominator/entry/exit configuration, episodes, capital, delayed fills, and costs.
- Produces: `BasisSimulation` records with price edge and funding reported separately.

```python
def simulate_basis_convergence(episode: CandidateEpisode, books: BookIndex, scenario: BasisScenario) -> BasisSimulation: ...
```

- [ ] **Step 1: Write direction, convergence, and full-cost tests**

Test both venue directions, independently executable entry/exit, relative/absolute/fixed-time exit variants admitted by approved config, divergence, maximum hold, USD 1,000/USD 5,000 cases, both fee cases, 300/500 ms delays, capital rejection, and separate funding field.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_basis_convergence -v
```

Expected: FAIL importing the strategy.

- [ ] **Step 3: Implement the pure simulation**

The function emits observations only. It may not import capture, venue network, account, or execution modules.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_basis_convergence tests.readonly_analyzer.test_delays tests.readonly_analyzer.test_capital -v
```

Expected: PASS; every simulation has complete input/config/evidence hashes.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/strategies/basis_convergence.py tests/readonly_analyzer/test_basis_convergence.py config/stage-a-v2/strategy-manifest.json config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(strategy): admit basis convergence shadow analysis"
```

### Task 8: Admit realized funding carry

**Requirements:** STRAT-003, PROD-011, DATA-010.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/strategies/realized_funding.py`
- Create: `tests/readonly_analyzer/test_realized_funding.py`
- Modify: `config/stage-a-v2/strategy-manifest.json`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: approved venue schedules/signs/conversions, settlement evidence, delayed entry/exit fills, basis movement, and holding cost.
- Produces: `FundingSimulation` with distinct forecast and realized fields.

```python
def simulate_realized_funding(episode: CandidateEpisode, books: BookIndex, settlements: tuple[FundingSettlement, ...], scenario: FundingScenario) -> FundingSimulation: ...
```

- [ ] **Step 1: Write signed-settlement tests**

Test long/short signs on both venues, entry before settlement, exit after settlement, settlement boundary equality, multiple settlements, schedule mismatch, missing conversion evidence, basis loss, holding cost, and forecast-positive/realized-absent insufficiency.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_realized_funding -v
```

Expected: FAIL importing the funding strategy.

- [ ] **Step 3: Implement realized-only verdict economics**

Keep forecast rate and expected cashflow in an ex-ante diagnostic record. Only immutable signed settlement cashflows enter `EpisodeCosts.realized_funding_cashflow`.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_realized_funding tests.readonly_analyzer.test_costs -v
```

Expected: PASS; missing realized evidence cannot satisfy funding continuation.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/strategies/realized_funding.py tests/readonly_analyzer/test_realized_funding.py config/stage-a-v2/strategy-manifest.json config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(strategy): admit realized funding carry analysis"
```

### Task 9: Add paired-basis trailing as a non-binding diagnostic

**Requirements:** STRAT-004, STRAT-005, §10.3.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/diagnostics/paired_basis_trailing.py`
- Create: `tests/readonly_analyzer/test_paired_basis_trailing.py`
- Modify: `config/stage-a-v2/strategy-manifest.json`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: completed frozen episodes, executable delayed books, approved trailing policy, full exit/residual costs.
- Produces: `TrailingDiagnostic(binding=False)`; no verdict input interface accepts this type.

```python
def run_paired_basis_trailing(episode: CompletedEpisode, books: BookIndex, config: TrailingPolicy) -> TrailingDiagnostic: ...
```

- [ ] **Step 1: Write diagnostic isolation tests**

Test activation, high/low watermark, trail, minimum/maximum hold, independent delayed exits, exact tie rule, missing-book rule, residual neutralization, and complete costs. Compare two runs with opposite trailing results and assert identical binding portfolio metrics and decision bytes.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_paired_basis_trailing -v
```

Expected: FAIL importing the diagnostic.

- [ ] **Step 3: Implement a type-separated diagnostic path**

Set `binding=False` in the frozen type and omit `TrailingDiagnostic` from `PortfolioInput`. Do not simulate maker fills.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_paired_basis_trailing tests.readonly_analyzer.test_basis_convergence -v
```

Expected: PASS; diagnostic changes cannot alter verdict inputs.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/diagnostics/paired_basis_trailing.py tests/readonly_analyzer/test_paired_basis_trailing.py config/stage-a-v2/strategy-manifest.json config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(diagnostics): add nonbinding paired basis trailing"
```

### Task 10: Aggregate the deterministic portfolio and concentration metrics

**Requirements:** STRAT-009, STRAT-010, PROD-010.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/portfolio.py`
- Create: `tests/readonly_analyzer/test_portfolio.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: binding completed basis/funding simulations and capital-event ledger; diagnostics are type-incompatible.
- Produces: canonical `PortfolioMetrics` keyed by strategy, asset, direction, notional, delay, and fee case.

```python
def aggregate_portfolio(simulations: tuple[PrimarySimulation, ...], capital_events: tuple[CapitalEvent, ...]) -> PortfolioMetrics: ...
```

- [ ] **Step 1: Write aggregation and concentration tests**

Test deterministic sorting, total, exact median for odd/even counts, positive P&L denominator, largest episode fraction, failed attempts, zero-positive-P&L handling, each notional/delay/fee slice, and rejection of duplicate episode keys or diagnostic records.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_portfolio -v
```

Expected: FAIL importing `aggregate_portfolio`.

- [ ] **Step 3: Implement exact canonical aggregation**

Sort by immutable episode key before all reductions. Calculate largest contribution as `max(positive_net) / sum(positive_net)`; when no positive episode exists, expose a typed failed total-net predicate rather than divide by zero.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_portfolio tests.readonly_analyzer.test_episodes tests.readonly_analyzer.test_capital -v
```

Expected: PASS under reversed inputs and different `PYTHONHASHSEED` values.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/portfolio.py tests/readonly_analyzer/test_portfolio.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): aggregate deterministic portfolio evidence"
```

### Task 11: Enforce verdict precedence and exact threshold boundaries

**Requirements:** PROD-002, PROD-007 through PROD-012, DATA-016, STRAT-008.

**Files:**
- Create: `packages/contracts/src/mee_contracts/decision.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/verdict.py`
- Create: `tests/contracts/test_decision.py`
- Create: `tests/readonly_analyzer/test_verdict.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: frozen-package validation, AnalysisRun replay validation, coverage/mapping/fee/funding sufficiency, and `PortfolioMetrics`.
- Produces: one `StageADecision` with reasons from one precedence class.

```python
class Decision(StrEnum):
    INVALID_DATASET = "INVALID_DATASET"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    STOP = "STOP"
    EXTEND_LONGER_SHADOW = "EXTEND_LONGER_SHADOW"

def evaluate_stage_a(inputs: DecisionInputs, predicates: FrozenPredicates) -> StageADecision: ...
```

Reason enum must include predicate-specific `INVALID_*`, `INSUFFICIENT_*`, and `STOP_*` members plus `EXTEND_ALL_V2_GATES_PASS`; it must not accept arbitrary strings.

- [ ] **Step 1: Write a complete predicate/precedence table**

```python
class VerdictTests(unittest.TestCase):
    def test_exact_boundaries(self) -> None:
        self.assertIs(evaluate(healthy="0.95").decision, Decision.EXTEND_LONGER_SHADOW)
        self.assertReason(evaluate(net_1000="0"), "STOP_USD_1000_NET_NON_POSITIVE")
        self.assertIs(evaluate(net_5000="0").decision, Decision.EXTEND_LONGER_SHADOW)
        self.assertReason(evaluate(concentration="0.25"), "STOP_CONCENTRATION_NOT_BELOW_25_PERCENT")

    def test_precedence_emits_only_highest_class(self) -> None:
        result = evaluate(invalid_package=True, complete_days=0, total_net="-1")
        self.assertIs(result.decision, Decision.INVALID_DATASET)
        self.assertTrue(all(reason.value.startswith("INVALID_") for reason in result.reasons))
```

Cover each invalid, insufficiency, and stop predicate individually and in combinations. Test seven acquisition days, five complete UTC days, health 0.95, 20 episodes, both verified mappings/fee cases, realized funding, total/median, 1000/5000, 300/500, concentration, and immutable extension target.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.contracts.test_decision tests.readonly_analyzer.test_verdict -v
```

Expected: FAIL importing decision types.

- [ ] **Step 3: Implement explicit ordered predicate groups**

Evaluate all invalid predicates first and return their ordered reasons if any; then insufficiency; then stop; otherwise return only `EXTEND_ALL_V2_GATES_PASS`. Never mix classes.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.contracts.test_decision tests.readonly_analyzer.test_verdict -v
```

Expected: PASS; constructing `GO`, `NO_GO`, `KILL`, `plausible`, or `inconclusive` raises.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/contracts/src/mee_contracts/decision.py packages/readonly-analyzer/src/mee_readonly_analyzer/verdict.py tests/contracts/test_decision.py tests/readonly_analyzer/test_verdict.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(decision): enforce Stage A v2 verdict precedence"
```

### Task 12: Produce deterministic report and two-process replay evidence

**Requirements:** DATA-004, DATA-010, DATA-020, DATA-023, PROD-005.

**Files:**
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/report.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/replay.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/cli.py`
- Create: `tests/readonly_analyzer/test_report.py`
- Create: `tests/readonly_analyzer/test_replay.py`
- Create: `tests/readonly_analyzer/integration/test_deterministic_process_replay.py`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: verified frozen package, approved config, exact code/artifact identity, and sealed `AnalysisRun` output graph.
- Produces: canonical report bytes, replay receipt, analysis terminal hash.

```python
def canonical_report(run: SealedAnalysisRun) -> bytes: ...

def replay_frozen_package(package: Path, config: Path, approval: Path, output: Path) -> ReplayReceipt: ...
```

- [ ] **Step 1: Write canonical and fresh-process tests**

Assert explicit sorting, canonical rational rendering, package/capture/config/code/AnalysisRun identities, predicate metrics, reasons, lineage, and terminal hash. Run two subprocesses with different `PYTHONHASHSEED`, locale, timezone, audit timestamps, and environment ordering; compare report and receipt bytes.

- [ ] **Step 2: Run RED**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_report tests.readonly_analyzer.test_replay tests.readonly_analyzer.integration.test_deterministic_process_replay -v
```

Expected: FAIL importing report/replay modules.

- [ ] **Step 3: Implement canonical projection and frozen-only CLI**

Use compact ASCII JSON with sorted object keys and explicitly sorted arrays. Exclude host time and audit time from hashes. The CLI accepts only frozen package/config/approval/output paths and has no URL, DSN, credential, or live mode.

- [ ] **Step 4: Run GREEN**

```bash
python3 -B -m unittest tests.readonly_analyzer.test_report tests.readonly_analyzer.test_replay tests.readonly_analyzer.integration.test_deterministic_process_replay -v
```

Expected: PASS with byte-identical outputs and distinct nonsemantic audit metadata outside the terminal hash.

- [ ] **Step 5: Update graph/handoff and commit**

```bash
git add packages/readonly-analyzer/src/mee_readonly_analyzer/report.py packages/readonly-analyzer/src/mee_readonly_analyzer/replay.py packages/readonly-analyzer/src/mee_readonly_analyzer/cli.py tests/readonly_analyzer/test_report.py tests/readonly_analyzer/test_replay.py tests/readonly_analyzer/integration/test_deterministic_process_replay.py config/traceability/stage-a-v2.yaml handoff.md
git commit -m "feat(analyzer): seal deterministic Stage A replay"
```

### Task 13: Prove quarantine, installed-artifact boundaries, and the full Claw gate

**Requirements:** PROD-014, ARCH-002 through ARCH-005, ARCH-009, STRAT-006, STRAT-007, GRAPH-012, CI-001 through CI-007, SEC-001 through SEC-006.

**Files:**
- Create: `scripts/check-stage-a-v2-boundary.py`
- Create: `tests/architecture/test_stage_a_v2_boundary.py`
- Create: `tests/architecture/test_stage_a_v2_quarantine.py`
- Create: `tests/architecture/test_product_hypotheses.py`
- Create: `tests/readonly_analyzer/integration/test_end_to_end_fixture.py`
- Create: `architecture/product-hypotheses.yaml`
- Modify: `.github/workflows/verify-a2-pr-on-claw.yml`
- Modify: `config/traceability/stage-a-v2.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: installed wheel inventories, import graph, dependency metadata, entry points, config, deterministic fixture, graph manifest.
- Produces: exact-SHA Claw receipts proving M5 and Stage-A-v2 acceptance gates.

- [ ] **Step 1: Write negative reachability and product-hypothesis tests**

Scan installed files, AST imports, metadata dependencies, entry points, image layers, configuration keys, and symbols. Reject capture application/writer/network imports and tokens for private/account/order/cancel/amend/transfer/withdraw/signer/wallet/live executor/n8n/grid/DCA/Infinity/maker fill/Solana RPC-program-Jupiter-Jito-Raydium. Allow `SOL` only as an explicit HL/Lighter market enum/config value.

Create four explicit `UNSUPPORTED` Hypothesis nodes for external customer
demand, willingness to pay, operator revenue, and production profitability.
Each must have a separate future Metric/TestOrEval target through
`falsified_by`, must have no `serves`/`intends` edge to the internal Stage A
Outcome, and must be unreachable from a release decision or deployment gate.

```python
def test_unsupported_product_hypotheses_cannot_become_stage_a_outcomes() -> None:
    graph = load_product_graph("architecture/product-hypotheses.yaml")
    expected = {"external-demand", "willingness-to-pay", "operator-revenue", "production-profitability"}
    assert {node.id for node in graph.nodes if node.kind == "Hypothesis"} >= expected
    assert all(graph.has_outgoing(node_id, "falsified_by") for node_id in expected)
    assert all(not graph.reachable(node_id, kind={"Outcome", "ClawGate", "Artifact"}) for node_id in expected)
```

- [ ] **Step 2: Run boundary RED**

```bash
python3 -B -m unittest tests.architecture.test_stage_a_v2_boundary tests.architecture.test_stage_a_v2_quarantine tests.architecture.test_product_hypotheses tests.readonly_analyzer.integration.test_end_to_end_fixture -v
python3 scripts/check-stage-a-v2-boundary.py
```

Expected: FAIL because the checker/workflow gate is absent.

- [ ] **Step 3: Implement the installed-artifact checker**

Inspect wheel contents and a fresh isolated installation rather than trusting source manifests. Prove `mee_contracts` has no application/network/storage dependency and analyzer has no network, mutation, or execution reachability.

- [ ] **Step 4: Replace conditional legacy discovery with exact installed-distribution commands**

```bash
set -euo pipefail
python3 -m venv "${RUNNER_TEMP}/mee-v2-venv"
python_bin="${RUNNER_TEMP}/mee-v2-venv/bin/python"
"${python_bin}" -m pip install --disable-pip-version-check --no-cache-dir --no-deps ./packages/contracts ./packages/public-capture ./packages/readonly-analyzer
"${python_bin}" -m pip check
"${python_bin}" -B -m unittest discover -s tests/contracts -t . -v
"${python_bin}" -B -m unittest discover -s tests/public_capture -t . -v
"${python_bin}" -B -m unittest discover -s tests/readonly_analyzer -t . -v
"${python_bin}" -B -m unittest discover -s tests/architecture -t . -v
"${python_bin}" scripts/run-a2-postgres-tests.py
"${python_bin}" scripts/check-stage-a-v2-boundary.py
```

Expected GREEN on both digest-pinned PostgreSQL 16 and 17 matrix jobs: every command exits 0; two-process replay bytes match; graph has no orphan/blocking conflict; artifact scan reports zero forbidden reachability.

- [ ] **Step 5: Run focused GREEN before dispatch**

```bash
python3 -B -m unittest tests.architecture.test_stage_a_v2_boundary tests.architecture.test_stage_a_v2_quarantine tests.architecture.test_product_hypotheses tests.readonly_analyzer.integration.test_end_to_end_fixture -v
python3 scripts/check-stage-a-v2-boundary.py
git diff --check
```

Expected: PASS and no `git diff --check` output.

- [ ] **Step 6: Dispatch exact-SHA Claw validation through the existing trusted repository-dispatch workflow**

```bash
target_sha="$(git rev-parse HEAD)"
gh api --method POST "repos/${GITHUB_REPOSITORY}/dispatches" -f event_type=a2-pr-verification -F "client_payload[pr_number]=${PR_NUMBER}" -F "client_payload[target_sha]=${target_sha}"
```

Expected: HTTP 204, followed by successful PostgreSQL 16 and 17 jobs whose receipts name the same `target_sha`. Dispatch requires an owner-controlled open PR; it does not deploy.

- [ ] **Step 7: Update graph/handoff with real receipts and commit**

```bash
git add scripts/check-stage-a-v2-boundary.py tests/architecture tests/readonly_analyzer/integration/test_end_to_end_fixture.py architecture/product-hypotheses.yaml .github/workflows/verify-a2-pr-on-claw.yml config/traceability/stage-a-v2.yaml handoff.md
git commit -m "test(claw): gate Stage A v2 strategy economics"
```

## Owner Approval Gate Before Binding Acquisition

The owner must approve the architecture manifest and the exact SHA-256 of all three `config/stage-a-v2` documents before a binding seven-day window begins. The approval record must name the approver, approval ID, approved hash, and time earlier than the first binding evidence time. Until that record exists, tests use explicit fixtures and the runtime returns `INSUFFICIENT_EVIDENCE` with `INSUFFICIENT_APPROVED_CONFIGURATION`; it never substitutes a default or guessed value.

The approval review must explicitly resolve:

- basis denominator and sign convention;
- entry/exit thresholds and maximum hold;
- episode cooldown and independence rule;
- venue funding schedule, sign, and conversion evidence;
- capital, allocation, leverage/margin, free-margin, and priority policy;
- residual threshold, neutralization venue, timeout, and missing-depth behavior;
- trailing activation, watermark, trail, holds, tie, and missing-book behavior;
- infrastructure allocation and rebalance policy;
- exact verified fee schedules for both frozen fee cases;
- the owner-selected `FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE` binding-verdict rule and its versioned reason-code contract.

Only after those decisions are recorded may the owner-approved binding files be
created as `config/stage-a-v2/{scenario,strategy-manifest,fee-cases}.json` and
committed with the approval record and combined SHA-256. Test fixtures are never
accepted as binding input.

## Falsification and Rollback

- Stop M5 admission if reconstruction cannot unambiguously close/reopen epochs, frozen/PostgreSQL readers disagree, exact arithmetic depends on ambient context, depth is approximated, capital is reused, ticks are double-counted, residual cost is omitted, forecast funding enters realized P&L, diagnostics change verdicts, or two fresh processes differ.
- Stop release if either fee case is incomplete, any required configuration lacks owner approval, any old verdict/reason is constructible, or any forbidden private/live/maker/Solana-chain capability is reachable.
- A failed strategy task is rolled back by removing its active strategy-manifest node and analyzer import while retaining provenance-labelled tests and research. Do not restore legacy runtime owners.
- A corrected config, fee schedule, mapping, report, or analyzer creates a new version/hash and a new `AnalysisRun`; never rewrite a frozen package or reopen `CaptureRun`.
- Analyzer rollback creates a new `AnalysisRun` over the same verified `FrozenPackageReceipt` using the previous compatible artifact and preserves both reports and terminal hashes.
- Schema rollback is blocked unless PostgreSQL 16/17 tests prove sealed roots, terminal hashes, receipts, grants, and reader compatibility remain intact.
- Source rollback is an explicit reviewed Git change through the same Claw gates; never force-reset, deploy automatically, mutate app-stack, or touch unrelated services.

## Final Verification Checklist

- [ ] Every active requirement has approval-to-evidence-to-rollback graph paths.
- [ ] All economic inputs are exact, versioned, hash-bound, owner-approved, and default-free.
- [ ] Entry and exit use full-depth delayed VWAP for both legs.
- [ ] Fees, realized funding, delay, failures, residuals, rebalance, holding, and infrastructure are attributable.
- [ ] Independent episodes and venue-specific capital locks prevent duplicate economics.
- [ ] Only basis convergence and realized funding are primary.
- [ ] Paired-basis trailing is diagnostic and type-excluded from verdict input.
- [ ] Verdict boundaries and precedence match Stage-A-v2 exactly.
- [ ] Two fresh-process reports and replay receipts are byte-identical.
- [ ] Installed artifacts contain no private/live/n8n/grid/DCA/Infinity/Solana-chain/maker capability.
- [ ] Exact-SHA Claw PostgreSQL 16 and 17 receipts are successful and recorded.
- [ ] No deployment or live-trading authority has been introduced.
