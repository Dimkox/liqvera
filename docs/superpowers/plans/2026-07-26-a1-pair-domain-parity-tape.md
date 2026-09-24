# A1 Pair Domain Parity Tape Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the normalized pair evaluator, then build a bounded,
canonical, hash-chained NDJSON corpus and deterministic replay boundary for
exact Python-to-Go pair-domain parity.

**Architecture:** Task 0 first removes look-ahead, unreviewed contract mapping,
unsupported payoff, and opaque cost inputs from accepted evaluations. A1 then
separates canonical encoding, strict schema, chain identity, domain projection,
and streaming replay so each boundary can fail closed and be reviewed
independently.

**Tech Stack:** Python 3.12+, standard library only, immutable dataclasses,
`Decimal`, `Fraction`, `hashlib.sha256`, `json`, `unittest`, NDJSON.

## Global Constraints

- Scope is `normalized_entry_pair_evaluation` and the acceptance label is
  `pair-domain parity`.
- No raw venue bytes, PostgreSQL, compression, collectors, WebSockets,
  credentials, account state, signing, orders, cancellation, or deployment.
- Binding evaluator profile is `pair-evaluator/v1`.
- Binding arithmetic profile is
  `exact-rational-render28-half-even/v1`.
- Binding reason profile is `pair-reasons/v2`.
- Binding format is `mee-a1-ndjson/v1`; unknown versions fail closed.
- All financial values cross the tape boundary as canonical coefficient and
  exponent strings; JSON floats are forbidden.
- Eligibility decisions use exact rational arithmetic. Only non-terminating
  output rendering uses 28 significant digits and `ROUND_HALF_EVEN`.
- Every parser limit is a trusted code constant, never a value read from tape.
- A replay without a caller-supplied terminal hash is only
  `SELF_CONSISTENT`; it cannot return `VERIFIED`.
- Production Python lines remain at most 88 characters.
- Each task uses TDD, updates `handoff.md` and `docs/agent-handoff.md`, passes
  the full Python suite, `compileall`, line scan, and `git diff --check`, and
  ends in a separate commit.
- No task may claim alpha, lifecycle profitability, business viability, or
  authorization for live execution.

---

## File Responsibility Map

Task 0 domain hardening:

```text
multi_exchange_engine/shadow/reasons.py
  Stable shadow reason family and normative order.

multi_exchange_engine/shadow/quality.py
  Public-book causality and quality decisions.

multi_exchange_engine/shadow/provenance.py
  Reviewed market mapping and versioned entry-cost evidence.

multi_exchange_engine/shadow/pair.py
  Pure pair evaluator and per-leg entry-cost attribution.

multi_exchange_engine/shadow/quantity.py
multi_exchange_engine/shadow/vwap.py
  Existing exact arithmetic consumers of the shared shadow reasons.
```

A1 tape:

```text
multi_exchange_engine/shadow/tape_codec.py
  Canonical Decimal and restricted canonical JSON.

multi_exchange_engine/shadow/tape_schema.py
  Strict record shapes, recursive unknown-field rejection, semantic limits.

multi_exchange_engine/shadow/tape_domain.py
  PairInput and PairEvaluation canonical projections and reconstruction.

multi_exchange_engine/shadow/tape_chain.py
  Domain-separated case IDs, record hashes, manifest/case/trailer chain.

multi_exchange_engine/shadow/tape_replay.py
  Bounded streaming validation, evaluation, comparison, and replay result.

scripts/generate-shadow-golden-a1.py
  Deterministic valid corpus and terminal-anchor generator.
```

The codec never imports the evaluator. The evaluator never imports tape,
filesystem, network, PostgreSQL, execution, signer, or credential modules.

---

### Task 1: Stable Reasons and Receive-Time Causality

**Files:**

- Create: `multi_exchange_engine/shadow/reasons.py`
- Modify: `multi_exchange_engine/shadow/quality.py`
- Modify: `multi_exchange_engine/shadow/quantity.py`
- Modify: `multi_exchange_engine/shadow/vwap.py`
- Modify: `multi_exchange_engine/shadow/pair.py`
- Modify: `tests/shadow/test_quality.py`
- Create: `tests/shadow/test_reasons.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `ShadowRejectCode` and `SHADOW_REASON_ORDER` in
  `shadow.reasons`.
- Produces: `QualityCode.BOOK_RECEIVED_AFTER_EVALUATION`.
- Preserves: imports of `ShadowRejectCode` from `shadow.quantity` by
  re-exporting the imported name during this checkpoint.
- Consumes: existing immutable `BookEvidence` and `QualityThresholds`.

- [ ] **Step 1: Write failing reason-order and causality tests**

Add:

```python
from mee_contracts.shadow.reasons import (
    SHADOW_REASON_ORDER,
    ShadowRejectCode,
)


def test_shadow_reason_order_is_the_v2_contract() -> None:
    assert SHADOW_REASON_ORDER == (
        ShadowRejectCode.MARKET_MAPPING_REJECTED,
        ShadowRejectCode.UNSUPPORTED_PAYOFF,
        ShadowRejectCode.COST_MODEL_INCOMPLETE,
        ShadowRejectCode.TARGET_OVERSHOOT,
        ShadowRejectCode.QUANTITY_UNSUPPORTED,
        ShadowRejectCode.DEPTH_INSUFFICIENT,
        ShadowRejectCode.NON_POSITIVE_AFTER_COSTS,
    )
```

Add quality vectors where one or both snapshots have
`received_timestamp_ms = evaluated_at_ms + 1`. Require
`BOOK_RECEIVED_AFTER_EVALUATION`, including a case that simultaneously produces
staleness/skew/clock reasons and compares the full declared order.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_reasons tests.shadow.test_quality -v
```

Expected: import failure for `shadow.reasons` and missing
`BOOK_RECEIVED_AFTER_EVALUATION`.

- [ ] **Step 3: Add the stable reason module**

Create:

```python
"""Stable normalized-pair shadow rejection reasons."""

from enum import StrEnum


class ShadowRejectCode(StrEnum):
    """Versioned pair-domain rejection codes."""

    MARKET_MAPPING_REJECTED = "MARKET_MAPPING_REJECTED"
    UNSUPPORTED_PAYOFF = "UNSUPPORTED_PAYOFF"
    COST_MODEL_INCOMPLETE = "COST_MODEL_INCOMPLETE"
    TARGET_OVERSHOOT = "TARGET_OVERSHOOT"
    QUANTITY_UNSUPPORTED = "QUANTITY_UNSUPPORTED"
    DEPTH_INSUFFICIENT = "DEPTH_INSUFFICIENT"
    NON_POSITIVE_AFTER_COSTS = "NON_POSITIVE_AFTER_COSTS"


SHADOW_REASON_ORDER = tuple(ShadowRejectCode)
```

Remove the enum declaration from `quantity.py` and import it there. Import it
directly from `shadow.reasons` in `vwap.py` and `pair.py`.

- [ ] **Step 4: Add causal quality rejection**

Insert `BOOK_RECEIVED_AFTER_EVALUATION` after
`BOOK_FROM_INACTIVE_CONNECTION` in `QualityCode`.

In `evaluate_book_pair`, add both legs without early return:

```python
if (
    left.snapshot.received_timestamp_ms > evaluated_at_ms
    or right.snapshot.received_timestamp_ms > evaluated_at_ms
):
    rejected.add(QualityCode.BOOK_RECEIVED_AFTER_EVALUATION)
```

Do not add `exchange_timestamp_ms <= received_timestamp_ms`; the clocks do not
share a proven offset model. Preserve the existing future-exchange-time
recorder-clock rejection.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
python -B -m unittest tests.shadow.test_reasons tests.shadow.test_quality -v
python -B -m unittest discover -s tests -t . -v
python -B -m compileall -q multi_exchange_engine tests
rg -n ".{89}" multi_exchange_engine tests
git diff --check
```

Update both handoffs with the reason version, exact test counts, causality
boundary, and next task. Commit:

```powershell
git add multi_exchange_engine/shadow/reasons.py `
  multi_exchange_engine/shadow/quality.py `
  multi_exchange_engine/shadow/quantity.py `
  multi_exchange_engine/shadow/vwap.py `
  multi_exchange_engine/shadow/pair.py `
  tests/shadow/test_quality.py tests/shadow/test_reasons.py `
  handoff.md docs/agent-handoff.md
git commit -m "feat: reject future-received shadow books"
```

---

### Task 2: Reviewed Market Mapping and Linear Payoff Boundary

**Files:**

- Create: `multi_exchange_engine/shadow/provenance.py`
- Modify: `multi_exchange_engine/domain/market.py`
- Modify: `multi_exchange_engine/exchange/public_hyperliquid.py`
- Modify: `multi_exchange_engine/exchange/public_lighter.py`
- Modify: `multi_exchange_engine/shadow/pair.py`
- Modify: `tests/domain/test_market_catalog.py`
- Modify: relevant `tests/exchange/test_*.py` market constructors
- Modify: `tests/shadow/test_quantity.py`
- Modify: `tests/shadow/test_vwap.py`
- Create: `tests/shadow/test_provenance.py`
- Modify: `tests/shadow/test_pair.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `MappingDecision`, `MarketMappingEvidence`,
  `validate_mapping_pair`.
- Modifies: `VenueMarket` adds required `displayed_size_unit`.
- Modifies: public discovery mapping inputs to provide that unit explicitly.
- Modifies: `PairInput` adds optional `buy_mapping` and `sell_mapping`, where
  `None` is evaluable missing evidence and not a tape-schema failure.
- Produces early reasons: `MARKET_MAPPING_REJECTED`,
  `UNSUPPORTED_PAYOFF`.
- Consumes: immutable `VenueMarket`, `InstrumentIdentity`, and evaluation time.

- [ ] **Step 1: Write failing mapping evidence tests**

The test fixture must construct:

```python
MarketMappingEvidence(
    mapping_id="mapping-buy-token-usd-v1",
    mapping_version="mapping/v1",
    decision=MappingDecision.APPROVED,
    venue="BUY",
    symbol="TOKEN-PERP",
    identity=IDENTITY,
    evidence_sha256="a" * 64,
    evidence_reference="repo:docs/mappings/token-usd-v1",
    valid_from_ms=1,
    valid_until_ms=None,
    reviewed_contract_multiplier=Decimal("10"),
    displayed_size_unit="contracts",
    quantity_step=Decimal("0.01"),
    price_tick=Decimal("0.01"),
    price_decimals=None,
    max_price_significant_digits=None,
    min_quantity=None,
    min_notional=Decimal("1"),
)
```

Tests must prove:

- both approved mappings valid at `evaluated_at_ms` accept;
- missing/wrong type, rejected decision, not-yet-valid, expired, mismatched
  identity/symbol/venue/multiplier/step/price rule/minima reject with
  `MARKET_MAPPING_REJECTED`;
- absent buy or sell mapping rejects with `MARKET_MAPPING_REJECTED`;
- missing, empty, or mismatched active-market size unit rejects before
  quantity arithmetic;
- empty IDs/version/reference, malformed SHA, bool timestamps, float numeric
  fields, and inconsistent validity ranges fail during construction;
- `PERPETUAL` plus `LINEAR` accepts;
- inverse, quanto, option-like, unknown payoff, and non-perpetual products
  reject with `UNSUPPORTED_PAYOFF`;
- mapping and market inputs remain unchanged.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_provenance tests.shadow.test_pair -v
```

Expected: import failure for `shadow.provenance`.

- [ ] **Step 3: Implement immutable mapping evidence**

Create:

```python
class MappingDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class MarketMappingEvidence:
    mapping_id: str
    mapping_version: str
    decision: MappingDecision
    venue: str
    symbol: str
    identity: InstrumentIdentity
    evidence_sha256: str
    evidence_reference: str
    valid_from_ms: int
    valid_until_ms: int | None
    reviewed_contract_multiplier: Decimal
    displayed_size_unit: str
    quantity_step: Decimal
    price_tick: Decimal | None
    price_decimals: int | None
    max_price_significant_digits: int | None
    min_quantity: Decimal | None
    min_notional: Decimal

```

Add `displayed_size_unit: str` as a required nonempty field of `VenueMarket`.
Update both public mapping contracts and every repository constructor to supply
it explicitly; do not add a default that would turn missing evidence into
`"contracts"`.

`__post_init__` validates exact types, finite positive Decimals, lowercase
64-digit SHA, printable unescaped ASCII identifiers/references, and
`valid_until_ms >= valid_from_ms` when present.

Add this exact public method signature to `MarketMappingEvidence`:

```python
def valid_for(
    self,
    market: VenueMarket,
    evaluated_at_ms: int,
) -> bool
```

Its implementation compares every duplicated reviewed market field and the
complete identity, requires `APPROVED`, and checks the closed validity interval.
It returns false instead of repairing or coercing data.

- [ ] **Step 4: Gate pair evaluation before quantity**

Modify `PairInput`:

```python
buy_mapping: MarketMappingEvidence | None
sell_mapping: MarketMappingEvidence | None
```

After quality passes and basic types are validated, apply:

```python
if not validate_mapping_pair(
    evaluated_at_ms=value.evaluated_at_ms,
    buy_market=value.buy_market,
    buy_mapping=value.buy_mapping,
    sell_market=value.sell_market,
    sell_mapping=value.sell_mapping,
):
    return _rejected((ShadowRejectCode.MARKET_MAPPING_REJECTED,))

if (
    value.buy_market.identity.product_kind != "PERPETUAL"
    or value.buy_market.identity.payoff_kind != "LINEAR"
):
    return _rejected((ShadowRejectCode.UNSUPPORTED_PAYOFF,))
```

The sell identity is already required to equal the buy identity. Mapping and
payoff failures return before quantity, depth, or economics.

- [ ] **Step 5: Verify and commit**

Run the focused and full checks from Task 1, replacing the focused command
with:

```powershell
python -B -m unittest tests.shadow.test_provenance tests.shadow.test_pair -v
```

Update both handoffs and commit:

```powershell
git add multi_exchange_engine/shadow/provenance.py `
  multi_exchange_engine/domain/market.py `
  multi_exchange_engine/exchange/public_hyperliquid.py `
  multi_exchange_engine/exchange/public_lighter.py `
  multi_exchange_engine/shadow/pair.py `
  tests/domain/test_market_catalog.py tests/exchange `
  tests/shadow/test_quantity.py tests/shadow/test_vwap.py `
  tests/shadow/test_provenance.py tests/shadow/test_pair.py `
  handoff.md docs/agent-handoff.md
git commit -m "feat: require reviewed linear market mappings"
```

---

### Task 3: Versioned Entry-Cost Provenance and Per-Leg Attribution

**Files:**

- Modify: `multi_exchange_engine/shadow/provenance.py`
- Modify: `multi_exchange_engine/shadow/pair.py`
- Modify: `tests/shadow/test_provenance.py`
- Modify: `tests/shadow/test_pair.py`
- Modify: `docs/five-day-stage-a-spec.md`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `LiquidityRole`, `FeeRoundingRule`, `FeeEvidence`,
  `CostComponent`, `EntryCostModel`, `ExactEntryCosts`.
- Modifies: `PairInput` replaces raw fee/cost fields with `entry_cost_model`.
- Modifies: `PairEvaluation` adds buy, sell, and additional cost attribution.
- Produces early reason: `COST_MODEL_INCOMPLETE`.
- Preserves: total `fee_cost_quote` as buy fee plus sell fee.

- [ ] **Step 1: Write failing cost-model tests**

Create complete evidence:

```python
FeeEvidence(
    venue="BUY",
    liquidity_role=LiquidityRole.TAKER,
    fee_rate_bps=Decimal("10"),
    fee_currency="USD",
    fee_tier="STANDARD",
    fee_scenario="DOCUMENTED",
    schedule_as_of_ms=10_000,
    schedule_sha256="b" * 64,
    rounding_rule=FeeRoundingRule.EXACT_QUOTE,
    minimum_fee_quote=Decimal("0"),
)
```

Tests must prove:

- complete buy/sell taker evidence calculates exact fees independently;
- minimum fee is applied per synthetic leg order;
- typed additional components sum exactly;
- output exposes buy fee, sell fee, total fee, additional cost, and net;
- unknown `fee_rate_bps`, schedule hash/as-of, rounding rule, amount, currency,
  or model version rejects with `COST_MODEL_INCOMPLETE`;
- maker evidence, wrong venue/currency, future schedule, unsupported model
  version, float, negative, and non-finite values reject;
- a documented zero is valid; `null` is unknown and never converted to zero;
- positive, zero, and negative net results preserve existing eligibility
  semantics and exact rational comparisons.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_provenance tests.shadow.test_pair -v
```

Expected: missing fee/cost evidence interfaces or unexpected old
`PairInput` signature.

- [ ] **Step 3: Implement cost evidence**

Add:

```python
class LiquidityRole(StrEnum):
    TAKER = "TAKER"


class FeeRoundingRule(StrEnum):
    EXACT_QUOTE = "EXACT_QUOTE"


@dataclass(frozen=True, slots=True)
class FeeEvidence:
    venue: str
    liquidity_role: LiquidityRole
    fee_rate_bps: Decimal | None
    fee_currency: str | None
    fee_tier: str | None
    fee_scenario: str | None
    schedule_as_of_ms: int | None
    schedule_sha256: str | None
    rounding_rule: FeeRoundingRule | None
    minimum_fee_quote: Decimal | None


@dataclass(frozen=True, slots=True)
class CostComponent:
    component_type: str
    amount_quote: Decimal | None
    currency: str | None
    model_version: str | None
    as_of_ms: int | None
    evidence_sha256: str | None


@dataclass(frozen=True, slots=True)
class EntryCostModel:
    model_version: str
    buy_fee: FeeEvidence
    sell_fee: FeeEvidence
    additional_costs: tuple[CostComponent, ...]


@dataclass(frozen=True, slots=True)
class ExactEntryCosts:
    buy_fee_quote: Fraction
    sell_fee_quote: Fraction
    additional_cost_quote: Fraction
```

Implement the public function with this exact signature:

```python
def calculate_entry_costs(
    *,
    model: EntryCostModel,
    evaluated_at_ms: int,
    quote_currency: str,
    buy_venue: str,
    sell_venue: str,
    buy_notional: Fraction,
    sell_notional: Fraction,
) -> ExactEntryCosts | None
```

Only `displayed-taker-entry-cost/v1`, `TAKER`, and `EXACT_QUOTE` are accepted.
This version is quote-currency-only: it has no conversion path. All evidence
must be complete, nonfuture, already denominated in the pair quote currency,
and bound to the correct venue. Any conversion requirement rejects with
`COST_MODEL_INCOMPLETE`. Fee calculation is:

```python
rate_fee = notional * fraction_from_decimal(rate_bps) / Fraction(10_000)
fee = max(rate_fee, fraction_from_decimal(minimum_fee_quote))
```

Return `None` for incomplete or unsupported evidence.

- [ ] **Step 4: Replace opaque pair cost inputs**

Replace in `PairInput`:

```python
buy_fee_bps: Decimal
sell_fee_bps: Decimal
extra_cost_quote: Decimal
```

with:

```python
entry_cost_model: EntryCostModel
```

Extend `PairEvaluation`:

```python
buy_fee_cost_quote: Decimal | None
sell_fee_cost_quote: Decimal | None
fee_cost_quote: Decimal | None
additional_cost_quote: Decimal | None
```

After depth and notional gates, calculate costs. A `None` result returns the
early `COST_MODEL_INCOMPLETE` shape with no economics. Otherwise use exact
Fractions for gross, fee total, additional cost, net, and eligibility.

Update every constructor path, including `_rejected`, so field-shape
invariants remain explicit.

- [ ] **Step 5: Correct the Stage A arithmetic statement**

Replace:

```text
All decimals use the existing fixed-point scale `1e8` and string-only JSON
boundaries.
```

with:

```text
The normalized pair reference uses
`exact-rational-render28-half-even/v1`: eligibility comparisons remain exact
and only non-terminating display outputs round to 28 significant digits with
ROUND_HALF_EVEN. Tape JSON uses canonical Decimal strings. A production
fixed-point optimization is accepted only after byte-exact parity with the
reference corpus.
```

- [ ] **Step 6: Verify and commit**

Run focused and full checks. Update both handoffs with the cost model version,
per-leg attribution, Stage A correction, and exact counts. Commit:

```powershell
git add multi_exchange_engine/shadow/provenance.py `
  multi_exchange_engine/shadow/pair.py `
  tests/shadow/test_provenance.py tests/shadow/test_pair.py `
  docs/five-day-stage-a-spec.md handoff.md docs/agent-handoff.md
git commit -m "feat: version shadow entry cost evidence"
```

---

### Task 4: Canonical Decimal and Restricted JSON Codec

**Files:**

- Create: `multi_exchange_engine/shadow/tape_codec.py`
- Create: `tests/shadow/test_tape_codec.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `TapeErrorCode`, `TapeError`, `TapeLimits`, `A1_LIMITS`.
- Produces: `encode_decimal`, `decode_decimal`, `encode_canonical_json`,
  `decode_canonical_json_line`.
- Consumes no evaluator or tape schema.

- [ ] **Step 1: Write failing Decimal codec tests**

Required exact vectors:

```python
{
    Decimal("0.00"): "0",
    Decimal("10.00"): "1e1",
    Decimal("1.2300"): "123e-2",
    Decimal("-0.005"): "-5e-3",
}
```

Tests also reject:

- negative zero text;
- coefficient trailing zero;
- `+`, uppercase `E`, missing exponent, exponent `-0`, exponent leading zero;
- float, NaN, Infinity;
- more than 128 significant digits;
- canonical exponent outside `[-1000, 1000]`;
- hostile ambient Decimal contexts changing bytes.

- [ ] **Step 2: Write failing JSON codec tests**

Tests require:

- sorted ASCII keys, no whitespace, UTF-8 without BOM;
- minimal integers and allowed range;
- arrays preserve order;
- duplicate keys rejected before normal decoding;
- CRLF, blank line, BOM, non-ASCII/unescaped string, JSON float, NaN,
  unknown primitive type, and noncanonical input rejected;
- decode then encode equals the original line bytes exactly.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_tape_codec -v
```

Expected: import failure for `shadow.tape_codec`.

- [ ] **Step 4: Implement exact Decimal strings**

Create these constants and types:

```python
MAX_DECIMAL_DIGITS = 128
MIN_DECIMAL_EXPONENT = -1000
MAX_DECIMAL_EXPONENT = 1000


class TapeErrorCode(StrEnum):
    INVALID_UTF8 = "INVALID_UTF8"
    BOM_FORBIDDEN = "BOM_FORBIDDEN"
    LINE_TOO_LARGE = "LINE_TOO_LARGE"
    TAPE_TOO_LARGE = "TAPE_TOO_LARGE"
    FINAL_LF_MISSING = "FINAL_LF_MISSING"
    INVALID_JSON = "INVALID_JSON"
    DUPLICATE_JSON_KEY = "DUPLICATE_JSON_KEY"
    NON_CANONICAL_JSON = "NON_CANONICAL_JSON"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    SCHEMA_UNSUPPORTED = "SCHEMA_UNSUPPORTED"
    EVALUATOR_UNSUPPORTED = "EVALUATOR_UNSUPPORTED"
    ARITHMETIC_PROFILE_UNSUPPORTED = "ARITHMETIC_PROFILE_UNSUPPORTED"
    REASON_CODE_VERSION_UNSUPPORTED = (
        "REASON_CODE_VERSION_UNSUPPORTED"
    )
    HASH_PROFILE_UNSUPPORTED = "HASH_PROFILE_UNSUPPORTED"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    DECIMAL_INVALID = "DECIMAL_INVALID"
    INDEX_GAP = "INDEX_GAP"
    DUPLICATE_CASE = "DUPLICATE_CASE"
    CASE_ID_MISMATCH = "CASE_ID_MISMATCH"
    HASH_MISMATCH = "HASH_MISMATCH"
    CHAIN_BROKEN = "CHAIN_BROKEN"
    OUTPUT_MISMATCH = "OUTPUT_MISMATCH"
    TRAILER_MISSING = "TRAILER_MISSING"
    TRAILER_NOT_FINAL = "TRAILER_NOT_FINAL"
    COUNT_MISMATCH = "COUNT_MISMATCH"
    EXTERNAL_ANCHOR_MISMATCH = "EXTERNAL_ANCHOR_MISMATCH"


class TapeError(ValueError):
    def __init__(
        self,
        code: TapeErrorCode,
        *,
        record_index: int | None = None,
    ) -> None:
        self.code = code
        self.record_index = record_index
        super().__init__(code.value)
```

`encode_decimal` must use `Decimal.as_tuple()`, remove coefficient trailing
zeroes while incrementing the exponent, and never call context-sensitive
`normalize`.

`decode_decimal` must require byte-equivalent re-encoding:

```python
value = Decimal(text)
if encode_decimal(value) != text:
    raise TapeError(TapeErrorCode.DECIMAL_INVALID)
return value
```

- [ ] **Step 5: Implement restricted canonical JSON**

Add trusted limits:

```python
@dataclass(frozen=True, slots=True)
class TapeLimits:
    max_tape_bytes: int
    max_line_bytes: int
    max_cases: int
    max_levels_per_side: int
    max_json_depth: int
    max_string_bytes: int
    max_workers: int


A1_LIMITS = TapeLimits(
    max_tape_bytes=256 * 1024 * 1024,
    max_line_bytes=8 * 1024 * 1024,
    max_cases=10_000,
    max_levels_per_side=5_000,
    max_json_depth=16,
    max_string_bytes=1_024,
    max_workers=8,
)
```

Use `json.loads` with:

- `object_pairs_hook` that rejects duplicate keys;
- `parse_float` and `parse_constant` callbacks that raise `INVALID_JSON`;
- post-parse recursive checks for depth, safe integers, printable ASCII
  strings, and supported primitive/container types.

Encode with sorted keys and compact separators. Reject if the result differs
from the supplied bytes:

```python
canonical = encode_canonical_json(decoded)
if canonical != line:
    raise TapeError(TapeErrorCode.NON_CANONICAL_JSON)
```

- [ ] **Step 6: Verify and commit**

Run:

```powershell
python -B -m unittest tests.shadow.test_tape_codec -v
python -B -m unittest discover -s tests -t . -v
python -B -m compileall -q multi_exchange_engine tests
rg -n ".{89}" multi_exchange_engine tests
git diff --check
```

Update handoffs and commit:

```powershell
git add multi_exchange_engine/shadow/tape_codec.py `
  tests/shadow/test_tape_codec.py handoff.md docs/agent-handoff.md
git commit -m "feat: add canonical A1 tape codec"
```

---

### Task 5: Strict Tape Schema and Domain Projection

**Files:**

- Create: `multi_exchange_engine/shadow/tape_schema.py`
- Create: `multi_exchange_engine/shadow/tape_domain.py`
- Create: `tests/shadow/test_tape_schema.py`
- Create: `tests/shadow/test_tape_domain.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `ManifestRecord`, `CaseMetadata`, `CaseRecord`, `TrailerRecord`.
- Produces: `manifest_from_mapping`, `case_from_mapping`,
  `trailer_from_mapping`.
- Produces: `pair_input_to_mapping`, `pair_input_from_mapping`,
  `pair_evaluation_to_mapping`.
- Consumes: Task 0 provenance and Task 4 codec.

- [ ] **Step 1: Write failing strict-schema tests**

Freeze constants:

```python
CORPUS_ID = "shadow-pair-domain-golden-v1"
SCOPE = "normalized_entry_pair_evaluation"
FORMAT_VERSION = "mee-a1-ndjson/v1"
DOMAIN_SCHEMA_VERSION = "pair-domain/v1"
EVALUATOR_VERSION = "pair-evaluator/v1"
ARITHMETIC_PROFILE = "exact-rational-render28-half-even/v1"
REASON_CODE_VERSION = "pair-reasons/v2"
HASH_PROFILE = "sha256-domain-separated/v1"
CANONICALIZATION_VERSION = "mee-canonical-json/v1"
SELECTION_POLICY_VERSION = "synthetic-conformance/v1"
CANDIDATE_UNIVERSE_ID = "synthetic-pair-domain-v1"
COST_MODEL_VERSION = "displayed-taker-entry-cost/v1"
```

Tests reject unknown or missing fields recursively in manifest, case metadata,
market, mapping, evidence, book level, thresholds, cost model, evaluation, and
trailer. Tests also reject wrong constants, more than 5,000 levels, invalid
typed reasons, wrong output nullability, and inconsistent venue/direction.

- [ ] **Step 2: Write failing domain round-trip tests**

For accepted, quality-rejected, mapping-rejected, depth-rejected, and
after-cost-rejected values:

```python
mapping = pair_input_to_mapping(value)
restored = pair_input_from_mapping(mapping)
assert restored == value
assert pair_evaluation_to_mapping(evaluate_pair(restored)) == expected
```

Also prove:

- Decimal projections use `encode_decimal`;
- `raw_sha256` projects as `source_payload_sha256`;
- reasons project as `{family, code}` in normative order;
- projection names `eligible` as `entry_eligible` and adds
  `DISPLAYED_TAKER_ENTRY_ONLY`;
- constructor errors fail as tape/schema errors, not evaluator PASS.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_tape_schema `
  tests.shadow.test_tape_domain -v
```

Expected: missing tape schema/domain modules.

- [ ] **Step 4: Implement strict record dataclasses**

Create frozen records:

```python
@dataclass(frozen=True, slots=True)
class ManifestRecord:
    record_index: int
    prev_hash: str
    corpus_id: str
    scope: str
    format_version: str
    domain_schema_version: str
    evaluator_version: str
    arithmetic_profile: str
    reason_code_version: str
    hash_profile: str
    canonicalization_version: str
    selection_policy_version: str
    candidate_universe_id: str
    cost_model_version: str
    reference_commit: str
    record_hash: str


@dataclass(frozen=True, slots=True)
class CaseMetadata:
    tick_id: str
    direction: str
    fixture_origin: str
    inclusion_reason: str
    candidate_universe_id: str
    selection_policy_version: str


@dataclass(frozen=True, slots=True)
class CaseRecord:
    record_index: int
    prev_hash: str
    case_id: str
    metadata: CaseMetadata
    input: Mapping[str, object]
    expected: Mapping[str, object]
    record_hash: str


@dataclass(frozen=True, slots=True)
class TrailerRecord:
    record_index: int
    prev_hash: str
    case_count: int
    manifest_hash: str
    record_hash: str
```

Use exact-key helpers:

```python
def require_fields(
    value: Mapping[str, object],
    expected: frozenset[str],
) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise TapeError(TapeErrorCode.UNKNOWN_FIELD)
```

Version mismatches map to their specific Task 4 error codes.

- [ ] **Step 5: Implement domain projection**

Use explicit field-by-field functions. Do not use `dataclasses.asdict`, because
it loses type and version control.

The evaluation projection must enforce:

```python
if entry_eligible:
    assert reasons == []
    assert all(required_output is not None)
elif reasons_are_early:
    assert all(quantity_depth_economics_are_none)
elif reasons == NON_POSITIVE_AFTER_COSTS:
    assert all(quantity_depth_economics_are_present)
```

Mapping reconstruction must create immutable tuples for levels and additional
costs, and immutable `QualityThresholds`.

- [ ] **Step 6: Verify and commit**

Run focused and full checks, update handoffs, and commit:

```powershell
git add multi_exchange_engine/shadow/tape_schema.py `
  multi_exchange_engine/shadow/tape_domain.py `
  tests/shadow/test_tape_schema.py tests/shadow/test_tape_domain.py `
  handoff.md docs/agent-handoff.md
git commit -m "feat: define strict A1 tape schema"
```

---

### Task 6: Domain-Separated Hash Chain and External Anchor

**Files:**

- Create: `multi_exchange_engine/shadow/tape_chain.py`
- Create: `tests/shadow/test_tape_chain.py`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `case_id_for`, `record_hash_for`, `build_manifest`,
  `build_case`, `build_trailer`, `verify_record_chain`.
- Consumes: canonical JSON and strict record mappings.
- Produces terminal hash from the trailer record.

- [ ] **Step 1: Write failing hash-vector tests**

Use fixed small mappings and assert hard-coded lowercase SHA-256 vectors for:

```text
SHA256("MEE-A1-INPUT-v1\0" || canonical_json(input))
SHA256("MEE-A1-RECORD-v1\0" || canonical_json(record_without_hash))
```

Tests must prove:

- changing input changes `case_id`;
- changing expected output does not change `case_id` but changes record hash;
- changing metadata, previous hash, or index changes record hash;
- identical input cannot appear twice in one corpus;
- manifest uses zero previous hash;
- every index is consecutive;
- trailer binds count and manifest hash;
- reordered, omitted, duplicated, or tampered records reject;
- internally rebuilt chains remain only self-consistent until externally
  anchored.

- [ ] **Step 2: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_tape_chain -v
```

Expected: import failure for `shadow.tape_chain`.

- [ ] **Step 3: Implement domain-separated hashes**

Create:

```python
ZERO_HASH = "0" * 64
INPUT_DOMAIN = b"MEE-A1-INPUT-v1\x00"
RECORD_DOMAIN = b"MEE-A1-RECORD-v1\x00"


def case_id_for(input_mapping: Mapping[str, object]) -> str:
    payload = encode_canonical_json(dict(input_mapping))
    return sha256(INPUT_DOMAIN + payload).hexdigest()


def record_hash_for(record_without_hash: Mapping[str, object]) -> str:
    payload = encode_canonical_json(dict(record_without_hash))
    return sha256(RECORD_DOMAIN + payload).hexdigest()
```

Builders calculate identities; callers never inject them.

- [ ] **Step 4: Implement chain verification**

`verify_record_chain` requires:

- one manifest at index zero;
- one or more cases;
- one final trailer;
- exact index progression;
- exact previous hash;
- unique case IDs;
- recomputed case and record hashes;
- trailer count and manifest hash equality.

It returns the trailer hash but does not label it verified.

- [ ] **Step 5: Verify and commit**

Run focused/full checks, update handoffs, and commit:

```powershell
git add multi_exchange_engine/shadow/tape_chain.py `
  tests/shadow/test_tape_chain.py handoff.md docs/agent-handoff.md
git commit -m "feat: chain A1 tape records"
```

---

### Task 7: Bounded Streaming Replay and Golden Corpus

**Files:**

- Create: `multi_exchange_engine/shadow/tape_replay.py`
- Create: `scripts/generate-shadow-golden-a1.py`
- Create: `tests/shadow/test_tape_replay.py`
- Create: `tests/shadow/test_tape_conformance.py`
- Create: `tests/fixtures/shadow-golden-v1.ndjson`
- Create: `tests/fixtures/shadow-golden-v1.terminal.sha256`
- Modify: `.github/workflows/ci.yml`
- Modify: `handoff.md`
- Modify: `docs/agent-handoff.md`

**Interfaces:**

- Produces: `ReplayStatus`, `ReplayResult`, `replay_tape`.
- Produces: deterministic fixture generator.
- Consumes all prior A1 modules and `evaluate_pair`.

- [ ] **Step 1: Write failing bounded-reader tests**

Tests cover:

- UTF-8 BOM, invalid UTF-8, CRLF, blank lines, missing final LF;
- tape over 256 MiB and line over 8 MiB rejected before JSON decode;
- premature/missing trailer and bytes after trailer;
- more than 10,000 cases;
- no partial result on failure.

Use small trusted `TapeLimits` instances in tests to exercise byte/count
boundaries without allocating hundreds of MiB.

- [ ] **Step 2: Write failing replay tests**

Freeze:

```python
class ReplayStatus(StrEnum):
    SELF_CONSISTENT = "SELF_CONSISTENT"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class ReplayResult:
    status: ReplayStatus
    case_count: int
    terminal_hash: str
```

Tests require:

- no expected anchor returns `SELF_CONSISTENT`;
- matching expected anchor returns `VERIFIED`;
- wrong anchor returns `EXTERNAL_ANCHOR_MISMATCH`;
- recomputed output mismatch returns `OUTPUT_MISMATCH`;
- replay twice returns identical result;
- workers 1 and 8 return identical result;
- workers 0 and 9 reject with `LIMIT_EXCEEDED`;
- shuffled evaluation completion order returns identical per-case projections;
- hostile Decimal context and fresh process return identical terminal hash;
- every valid case matches expected bytes.

- [ ] **Step 3: Run focused tests and verify RED**

Run:

```powershell
python -B -m unittest tests.shadow.test_tape_replay `
  tests.shadow.test_tape_conformance -v
```

Expected: missing replay module and fixtures.

- [ ] **Step 4: Implement streaming replay**

Expose this exact public signature:

```python
def replay_tape(
    stream: BinaryIO,
    *,
    expected_terminal_hash: str | None,
    workers: int = 1,
    limits: TapeLimits = A1_LIMITS,
) -> ReplayResult
```

Requirements:

- read bounded binary lines and track total bytes;
- require each physical line to end in LF before stripping it;
- validate canonical JSON, strict schema, index, identity, and chain in order;
- submit case evaluation to a bounded worker pool;
- allow at most `workers * 2` pending case futures;
- compare completed projections in record-index order;
- require trailer and immediate EOF;
- return only after every case succeeds;
- reject `workers < 1` or `workers > limits.max_workers` as
  `LIMIT_EXCEEDED`;
- never mutate inputs or depend on evaluation order.

Worker exceptions become tape failures with the associated record index.

- [ ] **Step 5: Implement deterministic fixture generation**

The generator creates the matrix defined by the design:

- both directions;
- every quality and shadow reason;
- exact threshold and threshold-plus-one cases;
- positive, zero, and negative after-cost values;
- target/overshoot/minimum/depth boundaries;
- different multipliers and lots;
- `$10/$25/$50`;
- Standard/Premium cost evidence;
- inverse payoff and invalid mapping/cost evidence.

The command is:

```powershell
$referenceCommit = git rev-parse HEAD
python -B scripts/generate-shadow-golden-a1.py `
  --reference-commit $referenceCommit `
  --output tests/fixtures/shadow-golden-v1.ndjson `
  --terminal-output `
    tests/fixtures/shadow-golden-v1.terminal.sha256
```

The script writes through a temporary file and atomically replaces only the
two explicit fixture targets after successful self-replay. It accepts no
credentials and performs no network access.

- [ ] **Step 6: Add adversarial conformance mutations**

Programmatically derive mutations from the valid corpus:

- protected-byte change;
- duplicate key;
- unknown field;
- noncanonical Decimal;
- JSON float;
- record reorder, omission, and duplicate;
- wrong case ID, previous hash, record hash, count, manifest hash;
- truncation and appended bytes;
- hostile context and fresh-process replay.
- forced shuffled worker completion order with unchanged record-order output;
- forbidden imports from execution, network, database, and compression modules.

Each mutation asserts one exact `TapeErrorCode`.

- [ ] **Step 7: Pin CI replay**

Add a Python 3.12 CI step:

```yaml
- name: Verify A1 pair-domain golden tape
  shell: pwsh
  run: |
    python -B -m unittest `
      tests.shadow.test_tape_replay `
      tests.shadow.test_tape_conformance -v
    $temporary = Join-Path $env:RUNNER_TEMP "a1-golden"
    New-Item -ItemType Directory -Path $temporary | Out-Null
    $manifest = Get-Content `
      tests/fixtures/shadow-golden-v1.ndjson -TotalCount 1 |
      ConvertFrom-Json
    $referenceCommit = [string]$manifest.reference_commit
    if ($referenceCommit -notmatch "^[0-9a-f]{40}$") {
      throw "committed A1 manifest has invalid reference_commit"
    }
    python -B scripts/generate-shadow-golden-a1.py `
      --reference-commit $referenceCommit `
      --output (Join-Path $temporary "shadow-golden-v1.ndjson") `
      --terminal-output `
        (Join-Path $temporary "shadow-golden-v1.terminal.sha256")
    $pairs = @(
      @(
        "tests/fixtures/shadow-golden-v1.ndjson",
        (Join-Path $temporary "shadow-golden-v1.ndjson")
      ),
      @(
        "tests/fixtures/shadow-golden-v1.terminal.sha256",
        (Join-Path $temporary "shadow-golden-v1.terminal.sha256")
      )
    )
    foreach ($pair in $pairs) {
      $difference = Compare-Object `
        (Get-Content -AsByteStream $pair[0]) `
        (Get-Content -AsByteStream $pair[1]) -SyncWindow 0
      if ($difference) {
        throw "generated A1 fixture differs from committed bytes"
      }
    }
```

Do not upload the tape as a reusable dependency cache and do not add secrets.

- [ ] **Step 8: Run final verification**

Run:

```powershell
python -B -m unittest discover -s tests -t . -v
python -B -m compileall -q multi_exchange_engine tests scripts
rg -n ".{89}" multi_exchange_engine tests scripts
git diff --check
pwsh -NoProfile -File .\scripts\validate-stage-a-n8n.ps1
pwsh -NoProfile -File .\scripts\test-validate-stage-a-n8n-mutations.ps1
```

Run fixture generation a second time into a temporary directory and compare
both fixture files byte for byte with the committed targets.

Update both handoffs with:

- exact corpus versions;
- reference commit;
- case count;
- terminal hash location, not a fabricated value;
- focused/full test counts;
- explicit `pair-domain parity` claim boundary;
- A2/A3 next action.

- [ ] **Step 9: Commit**

Stage only the listed files and commit:

```powershell
git add multi_exchange_engine/shadow/tape_replay.py `
  scripts/generate-shadow-golden-a1.py `
  tests/shadow/test_tape_replay.py `
  tests/shadow/test_tape_conformance.py `
  tests/fixtures/shadow-golden-v1.ndjson `
  tests/fixtures/shadow-golden-v1.terminal.sha256 `
  .github/workflows/ci.yml handoff.md docs/agent-handoff.md
git commit -m "feat: replay A1 pair-domain golden tape"
```

---

## Completion Boundary

This plan is complete only after all seven task commits pass independent spec
and quality review, the worktree is clean, the full verification suite is
green, and the committed terminal anchor verifies.

The next plan is Go pair-domain conformance. Raw-wire collectors and stateful
book reconstruction remain separate A2/A3 plans.
