# A1 Pair Domain Parity Tape Design

Date: 2026-07-26
Status: draft for written review
Scope: credential-free normalized pair-domain parity only

## Decision

The first golden corpus is a self-contained canonical NDJSON tape for the
normalized pair evaluator:

```text
VenueMarket + BookEvidence + PairInput -> PairEvaluation
```

Its acceptance label is `pair-domain parity`. It is not end-to-end golden
parity, a raw-feed replay, a lifecycle simulation, or evidence of alpha.

The binding arithmetic profile is:

```text
exact-rational-render28-half-even/v1
```

The first committed corpus freezes these identifiers:

```text
corpus_id = shadow-pair-domain-golden-v1
format_version = mee-a1-ndjson/v1
domain_schema_version = pair-domain/v1
evaluator_version = pair-evaluator/v1
arithmetic_profile = exact-rational-render28-half-even/v1
reason_code_version = pair-reasons/v2
hash_profile = sha256-domain-separated/v1
canonicalization_version = mee-canonical-json/v1
selection_policy_version = synthetic-conformance/v1
candidate_universe_id = synthetic-pair-domain-v1
cost_model_version = displayed-taker-entry-cost/v1
```

Python remains the reference evaluator. Go must reproduce the canonical input
and output bytes exactly before it can own this domain slice. The obsolete
Stage A statement that all values in this slice use fixed point scaled by
`1e8` must be corrected. A future optimized Go fixed-point implementation is
allowed only after it proves equality against this rational reference corpus.

Raw venue bytes, PostgreSQL, compression, collectors, WebSockets, credentials,
account state, signing, orders, and cancellation remain outside A1.

## What A1 Proves

A verified A1 replay proves only that:

- the tape is canonical and its externally anchored hash chain is intact;
- the normalized input satisfies the versioned A1 schema;
- Python reconstructs the intended immutable domain objects;
- the reference evaluator regenerates the stored result byte for byte;
- another runtime can reproduce quantity, displayed-depth VWAP, quality
  decisions, entry-cost arithmetic, and rejection reasons exactly.

A1 does not prove:

- raw venue payload normalization;
- snapshot/delta reconstruction or absence of market-data loss;
- fill probability, queue position, partial-fill convergence, or hedge timing;
- opportunity frequency, duration, capacity, or adverse selection;
- funding, exit costs, lifecycle PnL, margin safety, or liquidation safety;
- positive expectancy or business viability.

Future contracts are named separately:

- A2: raw-wire normalization parity;
- A3: stateful book reconstruction, reconnect, gap, duplicate, and
  out-of-order replay;
- A4: causal lifecycle and after-cost economic evidence.

No A1 result may be presented as completion of the full Gate 1 or as a live
trading authorization.

## Required Task 0 Hardening

A1 must not freeze known defects as golden behavior. The following changes are
prerequisites to generating the first accepted corpus.

### Receive-time causality

`evaluate_book_pair` must reject a book whose
`received_timestamp_ms > evaluated_at_ms`. The new stable quality reason is:

```text
BOOK_RECEIVED_AFTER_EVALUATION
```

This reason is evaluated for both legs and participates in the normative
quality-reason order. It prevents replay look-ahead.

The `quality` family order in `pair-reasons/v2` is:

```text
VALID
BOOT_EPOCH_MISMATCH
CONTINUITY_GAP_OPEN
BOOK_FROM_INACTIVE_CONNECTION
BOOK_RECEIVED_AFTER_EVALUATION
BOOK_STALE
SOURCE_TIME_SKEW
RECEIVE_TIME_SKEW
RECORDER_CLOCK_ERROR
WALL_MONOTONIC_DRIFT
```

The rule does not require venue exchange time to be less than recorder receive
time because those clocks are not guaranteed to share an epoch-quality
estimate. Existing future exchange timestamps remain a recorder-clock error.

Boundary vectors must cover:

- receive time exactly equal to evaluation time: allowed;
- receive time one millisecond after evaluation time: rejected;
- future exchange timestamp: recorder-clock rejection;
- simultaneous causality, staleness, and skew failures: every applicable reason
  returned once in normative order.

### Reviewed market mapping

The free-form `equivalence_evidence` string is insufficient for an accepted A1
case. Task 0 introduces an immutable versioned mapping record with:

```text
mapping_id
mapping_version
decision = APPROVED
evidence_sha256
evidence_reference
valid_from_ms
valid_until_ms
reviewed_contract_multiplier
displayed_size_unit
```

The mapping record is bound to one venue, symbol, economic identity, price
rule, quantity step, contract multiplier, minimum quantity, and minimum
notional. `evidence_sha256` is lowercase hexadecimal. The reference is an
ASCII repository, memory, or public-document identifier; replay does not fetch
it.

The normalized active `VenueMarket` contract carries `displayed_size_unit`.
There is no default: discovery adapters or synthetic fixtures must provide the
unit explicitly, and mapping validation compares it byte for byte.

An accepted pair requires:

- two distinct venues;
- identical reviewed `InstrumentIdentity` values;
- two approved mapping records valid at the evaluation time;
- exact equality between the reviewed and active contract multipliers;
- matching symbol, size unit, price rule, lot, and minima;
- distinct mapping IDs and nonempty mapping versions.

`valid_until_ms` is either a nonnegative timestamp or `null`. Missing, not-yet
valid, expired, rejected, or inconsistent mapping evidence fails before
quantity arithmetic.

### Linear payoff boundary

The current entry formulas are linear:

```text
notional = native_quantity * price * contract_multiplier
gross_capture = sell_notional - buy_notional
```

Task 0 therefore accepts only:

```text
product_kind = PERPETUAL
payoff_kind = LINEAR
```

Inverse, quanto, option-like, or unknown payoff contracts fail closed with a
stable domain rejection. Payoff-aware formulas require a new evaluator version
and are not added to A1.

### Versioned entry-cost provenance

Unproven fee and cost constants cannot make an accepted entry-economics case.
Task 0 replaces opaque rates with an immutable entry-cost model.

Each venue leg records:

```text
venue
liquidity_role = TAKER
fee_rate_bps
fee_currency
fee_tier
fee_scenario
schedule_as_of_ms
schedule_sha256
rounding_rule
minimum_fee_quote
```

The A1 `displayed-taker-entry-cost/v1` profile accepts only values already
denominated in the pair quote currency. Cross-currency conversion is outside
this profile. Any other currency, required conversion, unknown rate, or unknown
conversion value yields `COST_MODEL_INCOMPLETE`. A later cost profile must add
the conversion rate, observation time, and evidence hash before accepting
cross-currency values.

Additional costs are typed components:

```text
component_type
amount_quote
currency
model_version
as_of_ms
evidence_sha256
```

The output exposes buy fee, sell fee, additional cost, total fee cost, gross
capture, and net capture separately. `eligible` remains an entry-only result;
the tape projection names it `entry_eligible` and includes:

```text
eligibility_scope = DISPLAYED_TAKER_ENTRY_ONLY
```

No lifecycle or business interpretation is permitted.

### Arithmetic and reason-code versions

Task 0 makes the following identifiers normative:

```text
evaluator_version = pair-evaluator/v1
arithmetic_profile = exact-rational-render28-half-even/v1
reason_code_version = pair-reasons/v2
```

All comparisons affecting eligibility use exact rational arithmetic. Only
non-terminating display values are rounded to 28 significant digits with
`ROUND_HALF_EVEN` inside the existing independent Decimal context.

Parser, schema, and chain failures are `TapeError` values. They are not
converted into `PairEvaluation` rejection reasons.

The `shadow` family order in `pair-reasons/v2` is:

```text
MARKET_MAPPING_REJECTED
UNSUPPORTED_PAYOFF
COST_MODEL_INCOMPLETE
TARGET_OVERSHOOT
QUANTITY_UNSUPPORTED
DEPTH_INSUFFICIENT
NON_POSITIVE_AFTER_COSTS
```

The legacy aggregate `QUALITY_REJECTED` code is not serialized in A1. Exact
quality-family reasons are persisted instead.

## Corpus Records

The tape contains exactly one manifest, one or more cases, and one trailer:

```text
manifest
case
case
...
trailer
```

Every physical line contains one canonical JSON object followed by one LF.

### Manifest

The manifest is record index zero and contains:

```text
type = manifest
record_index = 0
prev_hash = 64 zeroes
corpus_id
scope = normalized_entry_pair_evaluation
format_version
domain_schema_version
evaluator_version
arithmetic_profile
reason_code_version
hash_profile
canonicalization_version
selection_policy_version
candidate_universe_id
cost_model_version
reference_commit
record_hash
```

`reference_commit` is the lowercase 40-character Git commit containing the
reference evaluator used to regenerate the corpus. It is provenance, not a
replacement for the normative evaluator version.

### Case

Each case contains:

```text
type
record_index
prev_hash
case_id
case_metadata
input
expected
record_hash
```

`case_metadata` contains:

```text
tick_id
direction
fixture_origin = SYNTHETIC | CAPTURED_NORMALIZED
inclusion_reason
candidate_universe_id
selection_policy_version
```

The input contains:

- evaluation time;
- both complete `VenueMarket` values;
- both approved mapping records;
- both complete `BookEvidence` values and authoritative ordered levels;
- quality thresholds;
- per-leg quote target and overshoot semantics;
- typed fee evidence and additional cost components.

`raw_sha256` is projected as `source_payload_sha256`. It is only a provenance
assertion because A1 intentionally does not contain or retrieve raw bytes.

The expected projection contains:

- `entry_eligible`;
- `eligibility_scope`;
- ordered typed reasons;
- common canonical and native quantities;
- buy and sell displayed-depth quotes;
- raw divergence;
- gross capture;
- buy fee, sell fee, total fee, additional cost, and net capture.

Reasons are objects, not unqualified strings:

```json
{"family":"quality","code":"BOOK_STALE"}
{"family":"shadow","code":"DEPTH_INSUFFICIENT"}
```

The normative reason order is versioned. Quality reasons follow their declared
contract order. A single shadow reason follows only after quality passes.

Output invariants are:

- early quality/domain rejection: quantity, depth, and economics are `null`;
- quantity or depth rejection: later fields are `null`;
- after-cost rejection: quantity, depth, and economics are present;
- accepted entry: reasons are empty and every required output is present.

### Trailer

The trailer is the final record and contains:

```text
type = trailer
record_index
prev_hash
case_count
manifest_hash
record_hash
```

Bytes after the trailer, a missing trailer, a wrong count, an index gap, a
duplicate case ID, or EOF without a final LF are errors.

The trailer `record_hash` is the terminal hash.

## Canonical Decimal Contract

Financial values are JSON strings. JSON floating-point numbers are forbidden.

The canonical grammar is:

```text
0
-?[1-9][0-9]*e(0|-?[1-9][0-9]*)
```

Rules:

- zero is exactly `0`;
- negative zero is forbidden;
- nonzero values always include `e` and an exponent;
- `+` is never written;
- coefficient and exponent have no leading zeroes;
- the coefficient has no trailing zeroes;
- values are derived from Decimal coefficient, sign, and exponent without
  ambient-context arithmetic.

Examples:

```text
Decimal("0.00")   -> "0"
Decimal("10.00")  -> "1e1"
Decimal("1.2300") -> "123e-2"
Decimal("-0.005") -> "-5e-3"
```

Accepted values are finite, have at most 128 significant digits, and have a
canonical exponent in `[-1000, 1000]`.

Expected output is compared as canonical JSON bytes. Python Decimal equality
alone is insufficient because it treats different encodings such as `10.0`
and `10.00` as equal.

## Canonical JSON Contract

A1 uses a deliberately restricted RFC 8785-like JSON subset:

- UTF-8 without BOM;
- ASCII schema keys and ASCII string values;
- no blank lines or CRLF;
- one object per line and one mandatory final LF;
- object keys sorted by ASCII byte order;
- arrays preserve semantic order;
- no insignificant whitespace;
- lowercase `true`, `false`, and `null`;
- duplicate object keys rejected before ordinary decoding;
- unknown fields rejected recursively;
- financial values represented only by canonical Decimal strings;
- integers encoded in minimal base ten without `+` or leading zeroes.

Identifiers and references may use printable ASCII except control characters,
double quotes, and backslashes. Hashes are lowercase hexadecimal.

After duplicate-aware parsing and strict schema validation, the decoder
re-encodes each record. The record is accepted only if the re-encoded bytes
equal the input bytes before the LF.

Only schema-declared integer fields may use JSON integers. Their allowed range
is `-(2^53 - 1)` through `2^53 - 1`; fields that are semantically nonnegative
apply the narrower nonnegative range.

## Identity and Hash Chain

The hash profile is:

```text
sha256-domain-separated/v1
```

Hash calculations use raw canonical UTF-8 bytes.

For every record:

```text
record_hash =
  SHA256(
    "MEE-A1-RECORD-v1\0"
    || canonical_json(record_without_record_hash)
  )
```

For every case:

```text
case_id =
  SHA256(
    "MEE-A1-INPUT-v1\0"
    || canonical_json(input)
  )
```

The expected output and chain envelope do not participate in `case_id`.
`case_id` must be unique inside one corpus.

Every record after the manifest contains the previous record hash. The trailer
contains the manifest hash and becomes the terminal hash.

The internal chain proves only self-consistency. Verified replay additionally
requires a caller-supplied expected terminal hash. The committed fixture pins
that value in:

```text
tests/fixtures/shadow-golden-v1.terminal.sha256
```

Git history anchors the tape and terminal-hash file against accidental
rewrites. This is not claimed to resist a malicious rewrite of repository
history.

Replay reports:

```text
SELF_CONSISTENT
VERIFIED
```

`VERIFIED` is impossible without an external expected terminal hash.

## Resource Limits

Limits belong to the trusted parser profile, not to the tape:

```text
maximum tape bytes:          256 MiB
maximum line bytes:            8 MiB
maximum cases:                10,000
maximum levels per side:       5,000
maximum JSON depth:               16
maximum string bytes:          1,024
maximum replay workers:             8
maximum Decimal digits:          128
Decimal exponent range:  -1000..1000
```

The reader is streaming and bounded. It checks line size before JSON decoding
and never loads the full tape. It rejects a premature trailer and stops reading
after the trailer only to verify immediate EOF.

These are versioned parser constants. Raising them requires an explicit design
and resource review.

## Components

The implementation is split by responsibility:

```text
shadow/tape_codec.py
  canonical JSON and Decimal encode/decode

shadow/tape_schema.py
  versioned record structures and recursive validation

shadow/tape_chain.py
  record indices, case IDs, hashes, trailer, external anchor

shadow/tape_domain.py
  immutable domain construction and canonical projection

shadow/tape_replay.py
  bounded streaming orchestration and ReplayResult
```

The dependency flow is:

```text
BoundedByteReader
  -> line and UTF-8 checks
  -> duplicate-aware JSON parser
  -> strict schema and semantic bounds
  -> chain, index, and case-ID verifier
  -> immutable domain mapper
  -> evaluate_pair/v1
  -> canonical output projection
  -> byte-exact expected comparison
  -> trailer, count, EOF, and external-anchor verification
  -> ReplayResult
```

The codec does not import the evaluator. The evaluator does not import tape,
filesystem, PostgreSQL, network, exchange-private, or credential modules.

## Stable Tape Errors

The initial tape error family is:

```text
INVALID_UTF8
BOM_FORBIDDEN
LINE_TOO_LARGE
TAPE_TOO_LARGE
FINAL_LF_MISSING
INVALID_JSON
DUPLICATE_JSON_KEY
NON_CANONICAL_JSON
UNKNOWN_FIELD
SCHEMA_UNSUPPORTED
EVALUATOR_UNSUPPORTED
ARITHMETIC_PROFILE_UNSUPPORTED
REASON_CODE_VERSION_UNSUPPORTED
HASH_PROFILE_UNSUPPORTED
LIMIT_EXCEEDED
DECIMAL_INVALID
INDEX_GAP
DUPLICATE_CASE
CASE_ID_MISMATCH
HASH_MISMATCH
CHAIN_BROKEN
OUTPUT_MISMATCH
TRAILER_MISSING
TRAILER_NOT_FINAL
COUNT_MISMATCH
EXTERNAL_ANCHOR_MISMATCH
```

Replay stops on the first tape error and reports its record index when known.
It never returns a partial PASS.

Domain rejections stored as expected outputs are not tape errors.

## Corpus Composition

The first committed valid corpus is small enough to inspect and contains:

- both trade directions;
- exact threshold and threshold-plus-one causality, age, skew, and clock cases;
- every quality and shadow rejection reason;
- positive, zero, and negative after-cost entry results;
- target and overshoot boundaries;
- venue minimum quantity and notional boundaries;
- different contract multipliers, lots, and partial final levels;
- insufficient displayed depth;
- `$10`, `$25`, and `$50` per-leg target profiles;
- Standard and Premium fee scenarios;
- explicit rejection of inverse payoff;
- missing, stale, and mismatched mapping evidence;
- incomplete cost provenance;
- synthetic candidate-universe inclusion and rejection cases.

Positive opportunities alone are forbidden. The corpus contains every
rejection family and both directions to prevent parity tests from hiding
selection assumptions.

Malformed encoding, duplicate keys, unknown fields, tampered hashes, reordered
records, truncated trailers, invalid Decimals, resource-limit violations, and
external-anchor mismatches are generated in codec tests from the valid corpus.
They are not mixed into the valid tape.

## Conformance Tests

Required Python tests:

- encode twice: byte-identical output;
- decode and re-encode: byte-identical input;
- replay twice: identical record results and terminal hash;
- replay under hostile Decimal precision, rounding, exponent bounds, clamp,
  and traps: identical output;
- replay in a fresh process: identical output;
- replay cases in shuffled evaluation order: identical per-case projections;
- replay with one and eight workers: identical projections;
- mutation of any protected byte: deterministic rejection;
- duplicate, reorder, omission, truncation, and appended bytes: rejection;
- unknown version or field: rejection;
- negative zero, noncanonical Decimal, JSON float, exponent bomb, overlong
  line, excessive depth, and excessive levels: rejection;
- domain constructor and evaluator errors never become codec PASS;
- no tape module imports execution, signer, credential, or private transport
  code.

Required later Go conformance:

- identical canonical manifest, cases, expected outputs, and terminal hash;
- exact equality for every output field and typed reason;
- no fallback from an unknown version to a newer or older evaluator;
- fuzzing of JSON, Decimal, chain, and schema boundaries;
- race-built concurrent replay;
- the immutable Python corpus remains the release gate.

## Acceptance Gates

Task 0 is complete only when:

- future receive time rejects causally;
- only reviewed linear mappings enter the evaluator;
- multiplier and size-unit evidence is binding;
- every cost input has typed provenance or fails closed;
- entry costs are attributed per leg;
- the rational arithmetic profile is the only A1 contract;
- the conflicting Stage A `1e8` statement is corrected;
- all existing and new Python tests pass.

A1 Python is complete only when:

- every valid record is canonical by construction;
- every corrupted or noncanonical mutation fails closed;
- the valid corpus regenerates with 100% byte equality;
- hostile-context, fresh-process, and concurrency tests agree;
- the externally anchored terminal hash verifies;
- the full Python suite, compilation, line scan, and Git diff checks pass;
- handoff and persistent memory record the exact versions and terminal hash.

Go pair-domain parity is complete only at 100% case and byte equality. Anything
less is failure, not partial parity.

None of these gates authorize live execution.

## Required Evidence After A1

Before a five-day shadow run can say anything about the business thesis, later
stages must add:

1. raw-event normalization and stateful reconstruction corpus with reconnect,
   duplicate, gap, nonce, clock-step, and out-of-order vectors;
2. unfiltered capture of all candidate ticks, both directions, `$10/$25/$50`,
   Standard/Premium fees, and every rejection;
3. measured opportunity duration, latency, exit depth, exit fees, funding, and
   forced-exit behavior;
4. partial-fill, hedge-delay, adverse-selection, venue-outage, margin, and
   liquidation stress;
5. at least 100 independent closed paired lifecycles and the concentration and
   lower-bound gates defined by the Stage A specification.

A five-day result may produce `KILL` or `EXTEND`. It is not by itself a
business or live-trading `GO`.

## Rejected Alternatives

### Store raw wire bytes in A1

Rejected because collectors and stateful reconstruction do not yet exist.
Mixing that work into A1 would hide the smaller pair-domain contract and delay
Go arithmetic parity. Raw-wire evidence belongs to A2 and A3.

### Start with PostgreSQL

Rejected because the portable corpus must remain independent of database
availability and migrations. PostgreSQL later imports the same verified
records; it does not define their meaning.

### Use current Decimal string rendering

Rejected because Python can treat `10`, `10.0`, and `10.00` as equal while
their bytes and hashes differ. The coefficient/exponent grammar is normative.

### Keep both rational and `1e8` arithmetic profiles

Rejected because two accepted arithmetic contracts would let Python and Go
disagree while each claims conformance. A1 follows the existing exact rational
reference. Optimization is a later measured implementation detail.

### Trust only the internal hash chain

Rejected because a corpus can be rewritten with a newly calculated chain.
Verified replay requires a Git-pinned external terminal hash.
