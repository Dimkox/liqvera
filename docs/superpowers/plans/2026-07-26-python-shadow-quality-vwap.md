# Python Shadow Quality and VWAP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the deterministic Python Gate 0 reference for public-book
quality, common executable quantity, depth VWAP, and paired entry economics.

**Architecture:** Wrap venue-native `OrderBookSnapshot` values in immutable
evidence carrying process/connection/clock continuity. Reject invalid pairs
before any arithmetic. Calculate one exact canonical quantity across different
contract multipliers/lots, sweep displayed depth without extrapolation, and
return a fail-closed paired shadow evaluation suitable for future golden tapes.

**Tech Stack:** Python 3.12+, standard library, exact `Decimal`, `unittest`.

## Global Constraints

- This is a public-data shadow reference only: no account, credential, signer,
  order, cancellation, execution, or private venue dependency.
- All price, quantity, notional, rate, fee, bps, and capture values use exact
  `Decimal`; floats are rejected.
- Quality is evaluated before quantity, VWAP, fees, or economics.
- Never pair books from different process boot IDs.
- Default Stage A limits are configuration values, not hidden behavior:
  Hyperliquid age 750 ms, Lighter age 200 ms, source and receive skew 250 ms,
  recorder clock error 25 ms, wall/monotonic drift 50 ms.
- A continuity gap, stale book, excessive skew, clock failure, malformed
  evidence, unsupported quantity, or insufficient displayed depth returns a
  stable rejection code and never an extrapolated price.
- Common quantity is expressed in canonical underlying units. Venue-native
  quantities derive through the reviewed `contract_multiplier`.
- Both venue minimum quantities and minimum notionals apply. Any leg exceeding
  the research target by more than the configured 200 bps is rejected.
- Input books and levels are immutable and must not be changed by evaluation.
- Pair economics in this checkpoint cover displayed taker entry only:
  buy/sell VWAP, gross capture, explicit entry fees, and explicit extra cost.
  They are not a lifecycle PnL or a trading signal.
- Production Python lines remain at most 88 characters. The full Python suite,
  `compileall`, and `git diff --check` must pass after each task.

---

### Task 1: Deterministic Public Book Quality Gate

**Files:**

- Create: `multi_exchange_engine/shadow/__init__.py`
- Create: `multi_exchange_engine/shadow/quality.py`
- Create: `tests/shadow/__init__.py`
- Create: `tests/shadow/test_quality.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```python
class QualityCode(StrEnum):
    VALID = "VALID"
    BOOT_EPOCH_MISMATCH = "BOOT_EPOCH_MISMATCH"
    CONTINUITY_GAP_OPEN = "CONTINUITY_GAP_OPEN"
    BOOK_FROM_INACTIVE_CONNECTION = "BOOK_FROM_INACTIVE_CONNECTION"
    BOOK_STALE = "BOOK_STALE"
    SOURCE_TIME_SKEW = "SOURCE_TIME_SKEW"
    RECEIVE_TIME_SKEW = "RECEIVE_TIME_SKEW"
    RECORDER_CLOCK_ERROR = "RECORDER_CLOCK_ERROR"
    WALL_MONOTONIC_DRIFT = "WALL_MONOTONIC_DRIFT"


@dataclass(frozen=True, slots=True)
class BookEvidence:
    snapshot: OrderBookSnapshot
    boot_id: str
    connection_epoch: str
    connection_active: bool
    continuity_valid: bool
    recorder_clock_error_ms: int
    wall_monotonic_drift_ms: int
    raw_sha256: str


@dataclass(frozen=True, slots=True)
class QualityThresholds:
    max_age_ms_by_venue: Mapping[str, int]
    max_source_skew_ms: int
    max_receive_skew_ms: int
    max_clock_error_ms: int
    max_wall_monotonic_drift_ms: int


@dataclass(frozen=True, slots=True)
class BookPairQuality:
    valid: bool
    codes: tuple[QualityCode, ...]


def evaluate_book_pair(
    *,
    evaluated_at_ms: int,
    left: BookEvidence,
    right: BookEvidence,
    thresholds: QualityThresholds,
) -> BookPairQuality:
    ...
```

- [ ] **Step 1: Write failing evidence and quality tests**

Create fixtures with exact `OrderBookSnapshot` values. Tests must prove:

```python
def test_accepts_fresh_continuous_pair_from_one_boot():
    result = evaluate_book_pair(
        evaluated_at_ms=10_200,
        left=evidence("HYPERLIQUID", source_ms=10_000, receive_ms=10_100),
        right=evidence("LIGHTER", source_ms=10_050, receive_ms=10_120),
        thresholds=thresholds(),
    )
    assert result == BookPairQuality(True, (QualityCode.VALID,))
```

- age is checked against the configured venue-specific limit;
- Hyperliquid at 751 ms and Lighter at 201 ms are stale;
- source skew 251 ms and receive skew 251 ms are separate rejections;
- different boot IDs reject the pair;
- an inactive connection or open continuity gap rejects the pair;
- clock error 26 ms and absolute wall/monotonic drift 51 ms reject;
- multiple codes are returned once each in enum declaration order;
- empty IDs, negative clock magnitudes, non-hex/non-64-character SHA-256,
  missing/unknown venue age limit, bool-as-int, and float thresholds fail
  closed during construction or evaluation.

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```powershell
python -m unittest tests.shadow.test_quality -v
```

Expected: import failure because `multi_exchange_engine.shadow.quality` does
not exist.

- [ ] **Step 3: Implement immutable evidence validation**

`BookEvidence.__post_init__` must validate non-empty IDs, boolean flags, exact
nonnegative integer clock magnitudes, and a lowercase or uppercase 64-digit
hex SHA-256. It must not mutate the nested frozen snapshot.

`QualityThresholds.__post_init__` must copy the input mapping into an immutable
`MappingProxyType`, require a non-empty venue map, reject bool/float values,
and require every threshold to be a nonnegative integer.

- [ ] **Step 4: Implement deterministic pair evaluation**

Evaluate all gates without early return so persisted evidence contains every
blocking code. Age is `evaluated_at_ms - exchange_timestamp_ms`; a future
exchange timestamp is a clock failure. Source skew compares exchange
timestamps and receive skew compares received timestamps. Return
`(QualityCode.VALID,)` only when no blocking code exists.

- [ ] **Step 5: Verify, update continuity, and commit**

Run:

```powershell
python -m unittest tests.shadow.test_quality -v
python -m unittest discover -s tests -t . -v
python -m compileall -q multi_exchange_engine tests
git diff --check
```

Record the quality contract, exact test count, verification, safety boundary,
and next action in both handoffs. Stage only the files listed for Task 1 and
commit:

```powershell
git commit -m "feat: add deterministic public book quality gate"
```

---

### Task 2: Common Quantity, Executable VWAP, and Paired Entry Economics

**Files:**

- Create: `multi_exchange_engine/shadow/quantity.py`
- Create: `multi_exchange_engine/shadow/vwap.py`
- Create: `multi_exchange_engine/shadow/pair.py`
- Create: `tests/shadow/test_quantity.py`
- Create: `tests/shadow/test_vwap.py`
- Create: `tests/shadow/test_pair.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

```python
class ShadowRejectCode(StrEnum):
    QUALITY_REJECTED = "QUALITY_REJECTED"
    TARGET_OVERSHOOT = "TARGET_OVERSHOOT"
    QUANTITY_UNSUPPORTED = "QUANTITY_UNSUPPORTED"
    DEPTH_INSUFFICIENT = "DEPTH_INSUFFICIENT"
    NON_POSITIVE_AFTER_COSTS = "NON_POSITIVE_AFTER_COSTS"


@dataclass(frozen=True, slots=True)
class CommonQuantity:
    canonical_quantity: Decimal
    buy_venue_quantity: Decimal
    sell_venue_quantity: Decimal
    common_lot: Decimal


def common_quantity(
    *,
    target_notional: Decimal,
    buy_market: VenueMarket,
    buy_price: Decimal,
    sell_market: VenueMarket,
    sell_price: Decimal,
    max_overshoot_bps: Decimal,
) -> CommonQuantity:
    ...


@dataclass(frozen=True, slots=True)
class DepthQuote:
    canonical_quantity: Decimal
    venue_quantity: Decimal
    actual_notional: Decimal
    vwap: Decimal
    worst_price: Decimal
    consumed_level_count: int


def sweep(
    *,
    levels: Sequence[BookLevel],
    market: VenueMarket,
    canonical_quantity: Decimal,
) -> DepthQuote:
    ...


@dataclass(frozen=True, slots=True)
class PairInput:
    evaluated_at_ms: int
    buy_evidence: BookEvidence
    sell_evidence: BookEvidence
    quality_thresholds: QualityThresholds
    buy_market: VenueMarket
    sell_market: VenueMarket
    target_notional: Decimal
    max_overshoot_bps: Decimal
    buy_fee_bps: Decimal
    sell_fee_bps: Decimal
    extra_cost_quote: Decimal


@dataclass(frozen=True, slots=True)
class PairEvaluation:
    eligible: bool
    rejection_codes: tuple[QualityCode | ShadowRejectCode, ...]
    quantity: CommonQuantity | None
    buy: DepthQuote | None
    sell: DepthQuote | None
    raw_divergence_bps: Decimal | None
    gross_capture_quote: Decimal | None
    fee_cost_quote: Decimal | None
    net_capture_quote: Decimal | None


def evaluate_pair(value: PairInput) -> PairEvaluation:
    ...
```

- [ ] **Step 1: Write failing common-quantity tests**

Tests use arbitrary verified markets rather than an asset allowlist. Cover:

- decimal lot LCM across canonical lots `0.1` and `0.25` equals `0.5`;
- different reviewed contract multipliers produce aligned venue quantities;
- target notional, venue `min_quantity`, and `min_notional` all raise the
  canonical requirement before upward common-lot rounding;
- different identities or the same venue reject as unsupported;
- both resulting venue quantities are exact multiples of their venue steps;
- either leg above `target * (1 + max_overshoot_bps / 10_000)` raises a typed
  `QuantityRejected(TARGET_OVERSHOOT)`;
- zero/negative/float/non-finite inputs raise
  `QuantityRejected(QUANTITY_UNSUPPORTED)`;
- input `VenueMarket` objects remain unchanged.

- [ ] **Step 2: Verify quantity RED and implement minimum arithmetic**

Run:

```powershell
python -m unittest tests.shadow.test_quantity -v
```

Expected: import failure because `shadow.quantity` is absent.

Use integer `math.lcm` after scaling the two finite Decimal canonical lots to
their common decimal exponent. Round upward only with `ROUND_CEILING`.
Determine required canonical quantity as the maximum of:

```python
target_notional / buy_price
target_notional / sell_price
buy_market.min_quantity * buy_market.contract_multiplier
sell_market.min_quantity * sell_market.contract_multiplier
buy_market.min_notional / buy_price
sell_market.min_notional / sell_price
```

Treat absent `min_quantity` as zero. Recheck venue step alignment, minimums,
and overshoot after rounding.

- [ ] **Step 3: Write failing executable-depth tests**

Tests must prove:

- asks supplied low-to-high and bids supplied high-to-low both sweep in the
  supplied authoritative order;
- a partial final level is consumed exactly;
- quote notional includes the reviewed contract multiplier;
- VWAP is `actual_notional / canonical_quantity`;
- worst price and consumed level count are exact;
- insufficient displayed depth raises
  `DepthRejected(DEPTH_INSUFFICIENT)` with no extrapolated result;
- empty, nonpositive, float, non-finite, or misaligned quantities fail closed;
- the input level sequence is not mutated.

- [ ] **Step 4: Verify VWAP RED and implement the sweep**

Run:

```powershell
python -m unittest tests.shadow.test_vwap -v
```

Expected: import failure because `shadow.vwap` is absent.

Consume venue-native level quantities until
`canonical_quantity / contract_multiplier` is filled. The returned quote must
use the requested canonical quantity exactly.

- [ ] **Step 5: Write failing paired-evaluation tests**

Tests must cover both directions by swapping books/markets. Prove:

- invalid quality returns all quality codes and leaves quantity/quotes/economics
  `None`;
- quantity and depth errors map to one stable shadow rejection code;
- actual displayed-depth buy/sell notionals drive gross capture;
- either actual notional below target or above the configured overshoot limit
  is a fail-closed quantity rejection after the depth sweep;
- entry fees equal
  `buy_notional * buy_fee_bps / 10_000` plus
  `sell_notional * sell_fee_bps / 10_000`;
- extra cost is subtracted explicitly;
- raw divergence is
  `(sell_vwap - buy_vwap) * 10_000 / buy_vwap`;
- positive net capture is eligible with no rejection codes;
- zero or negative net capture is ineligible with
  `NON_POSITIVE_AFTER_COSTS`;
- float, negative fee, or negative extra-cost input fails closed;
- book venue/symbol must match its `VenueMarket`, both venues must be distinct,
  and both markets must have the same reviewed identity;
- evaluation is deterministic and does not mutate either book.

- [ ] **Step 6: Verify pair RED and implement fail-closed orchestration**

Run:

```powershell
python -m unittest tests.shadow.test_pair -v
```

Expected: import failure because `shadow.pair` is absent.

Call `evaluate_book_pair` first. Do not call quantity or sweep after quality
failure. Map only typed quantity/depth rejections; unexpected programming
errors must propagate rather than being mislabeled as market rejection.

- [ ] **Step 7: Run full verification, update continuity, and commit**

Run:

```powershell
python -m unittest tests.shadow.test_quantity -v
python -m unittest tests.shadow.test_vwap -v
python -m unittest tests.shadow.test_pair -v
python -m unittest discover -s tests -t . -v
python -m compileall -q multi_exchange_engine tests
git diff --check
```

Record exact test counts, formulas, explicit limitations, and next action
(golden tape serialization/replay) in both handoffs. Stage only the files
listed for Task 2 and commit:

```powershell
git commit -m "feat: evaluate executable paired shadow entry"
```
