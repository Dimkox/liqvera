# Liqvera F2 Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze independently testable F2 API, report, state, and vector contracts without implementing the F3 report builder, F4 gateway/ledger, or F5 settlement.

**Architecture:** Publish OpenAPI 3.1 JSON and closed JSON Schema 2020-12 documents under `schemas/mezo-evidence/v1/`. Offline Python contract tests validate local references, examples, state invariants, and exact vectors using the existing arithmetic kernel. Future runtime assertions remain explicit machine-readable obligations, never passing runtime evidence.

**Tech Stack:** Python 3.12+, existing pytest 9.1.1, Python stdlib `json`, `re`, `datetime`, `decimal`, `fractions`, existing `mee_contracts.exact` and `mee_readonly_analyzer.vwap`; no new dependency, service, framework, database, or SDK installation.

**Spec:** `docs/planning/LIQVERA_FACTORY_TZ.md`, especially §§6–12, 14–16; `docs/adr/0002-liqvera-report-payment-boundary.md`; `engineering/changes/2026-09-24-mezo-evidence/`; F1 lock `docs/compatibility/mezo-evidence-v1.json`.

## Global Constraints

- “New schema: `mee-evidence-report/v1`.” Preserve all existing Stage A schemas, verdicts, exact arithmetic, inherited `mee-*` names, and shadow-only authority.
- “Prices, quantities, and monetary values must not pass through JavaScript `Number` or Python `float`.” Rational values are closed `{numerator:string, denominator:string}` objects with reduced fractions and positive denominators. Display uses `ROUND_HALF_EVEN`, precision 28 significant digits, independently of canonical exact values.
- “Only the first permits a live chargeable quote”: the snapshot statuses are `VALID_FOR_SNAPSHOT_CALCULATION`, `REJECTED`, `SIMULATED`.
- “0.01 test MUSD = 10000000000000000 atomic units”; network `eip155:31611`, chain ID `31611`, decimals `18`, asset `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`. Preserve the lock's address spelling for asset display; compare validated address bytes where appropriate.
- “A quote lives for 120 seconds after the report is ready.” Source age maximum is 5000 ms; future skew maximum is 1000 ms; metadata maximum age is 24 hours, inside its validity interval.
- “Quote expiry prohibits starting a new payment but does not cancel one already started/confirmed.” Unknown payment cannot become unpaid or initiate another settlement.
- “The gateway is the ledger's only writer.” F2 describes ledger uniqueness and state guards but creates no gateway, migrations, report builder, signing code, or payment network calls.
- “JSON body ≤16 KiB, decoded payment payload ≤16 KiB, bundle ≤10 MiB, at most 4 concurrent builds, and 5 new quotes per minute per access scope”; build deadline 15 seconds and at most two upstream attempts.
- “Use `Cache-Control: private, no-store` for quote/payment/report responses”; capabilities and payment headers never appear in URLs, examples containing real secrets, or logs.
- English artifacts and commits. Mainnet, live exchange mutation, custody, merchant signing keys, and release/deployment remain excluded.
- Every coherent task updates `handoff.md`, records its actual RED/GREEN result, adds exact graph inventory bindings for every new file, passes `make verify`, and commits. Never commit a failing default suite. Do not overwrite user changes.
- F2 tests certify contract consistency only. Runtime A02–A06 and A10–A20 remain `NOT_RUN` in F2 evidence; preserve the existing acceptance matrix's more specific `BLOCKED_EXTERNAL` for A13–A14. No runtime acceptance becomes PASS from vectors or mocked transitions.
- `PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED` remain blockers. Authorization identity/replay semantics require the selected SDK's F5 evidence; no guessed nonce, invented facilitator status API, confirmation count, merchant address, or fictitious successful payment.

## Review Focus

1. Two syntactically different decimal/address strings must canonicalize to one idempotent body; non-ASCII digits, floats, exponent notation, overflow, and overprecision must fail closed (Task 2).
2. A PREPARING report request must have a usable status location without exposing a chargeable quote or paid fields; sibling-scope requests must not reveal resource existence (Tasks 3 and 5).
3. Expiry, crash, or ambiguous identical Transfer logs must preserve one in-flight settlement and prevent a second charge, including after `MANUAL_REVIEW` (Tasks 4 and 5).
4. A syntactically valid report with incomplete provenance, altered exact arithmetic, or an extra digest field must not gain chargeable status merely by passing JSON shape validation (Tasks 3 and 6).
5. Unsupported schema keywords, remote/path-escaping references, and unvalidated examples must fail the contract checker instead of silently weakening the contract (Tasks 1 and 6).

---

## Execution and file map

Status: authored for plan review; no F2 implementation or approval claimed.
The current branch is `feat/mezo-evidence-f2-contracts`, stacked on F1 at
`d2d7923`. Read the spec, this plan, `AGENTS.md`, README, architecture,
handoff, security, roadmap, and active route before execution. No route exists
at authoring time: do not invent one or receipts. If a route appears, follow
its allowed agents. Use one implementation owner at a time, with independent
task review before proceeding. Read-only reviews may run in parallel.

| Path | Responsibility / owner task |
| --- | --- |
| `schemas/mezo-evidence/v1/primitives.schema.json` | IDs, decimal/address/rational/time primitives; Task 1 |
| `schemas/mezo-evidence/v1/reasons.schema.json` | Versioned public reason enum; Task 2 |
| `schemas/mezo-evidence/v1/error.schema.json` | Closed safe public error envelope; Task 2 |
| `schemas/mezo-evidence/v1/quote-request.schema.json` | Four-field submitted request; Task 2 |
| `schemas/mezo-evidence/v1/report.schema.json` | Immutable analytical report; Task 3 |
| `schemas/mezo-evidence/v1/resources.schema.json` | Preview, request status, quote, terms, receipt, capabilities, health; Task 3 |
| `schemas/mezo-evidence/v1/states.json` | Versioned report-request, quote, attempt, delivery graphs and guards; Task 4 |
| `schemas/mezo-evidence/v1/states.schema.json` | Closed structure of state graph document; Task 4 |
| `schemas/mezo-evidence/v1/openapi.json` | HTTP 3.1 contract referencing these schemas; Task 5 |
| `schemas/mezo-evidence/v1/vectors.schema.json` | Closed discriminated vector records; Task 6 |
| `schemas/mezo-evidence/v1/vectors.json` | Exact literals, rejects, auth, atomic units, recovery obligations; Task 6 |
| `tests/contracts/mezo_evidence_support.py` | Test-only bounded validator/reference resolver; Task 1 |
| `tests/contracts/test_mezo_primitives.py` | Validator rejection and primitive boundaries; Task 1 |
| `tests/contracts/test_mezo_requests.py` | Request/reason/normalization contract; Task 2 |
| `tests/contracts/test_mezo_resources.py` | Report/preview separation and resources; Task 3 |
| `tests/contracts/test_mezo_states.py` | Graph reachability and forbidden transitions; Task 4 |
| `tests/contracts/test_mezo_openapi.py` | Endpoint, security, header and example consistency; Task 5 |
| `tests/contracts/test_mezo_vectors.py` | Literal exactness, vector semantics and future obligations; Task 6 |
| `engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md` | Final SHA-bound contract evidence and omitted runtime work; Task 6 |
| `architecture/architecture.yaml` | Nodes and exact bindings added with each task |
| `handoff.md`, `engineering/changes/2026-09-24-mezo-evidence/tasks.md` | Honest per-task continuity |

Tests live in the already-collected `tests/contracts/`, so neither Makefile
nor pytest discovery needs widening. Use `import mezo_evidence_support as c`
from neighboring test files (pytest's existing prepend import mode). New helper
code stays out of production packages.

Add nodes `contract:mezo-evidence-v1` (`Contract`, owner `contracts`),
`test:mezo-evidence-contracts` (`TestOrEval`, owner `contracts`), both lifecycle
`IMPLEMENTED`, requirements `[]`, describing implemented contracts only.
Add an edge from contract to test with `kind: validated_by`. Bind each new
`schemas/mezo-evidence/v1/*.json` separately to the contract node with
`path_class: SCHEMA_MANIFEST`; each new test/helper separately to the test node
with `TEST_SOURCE`. Evidence/docs bind to `document:graph-authority-handoff`
with `DOCUMENTATION`. Do not replace exact bindings with a catch-all glob or
modify unrelated seven declared conflicts. Stage new files before running the
tracked-file graph checker, then inspect staged scope before commit.

Common task verification (run after its focused GREEN and before its commit):

```bash
git diff --check
PATH="$PWD/.venv/bin:$PATH" make graph
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest -q
```

`make verify` and bare pytest both must be green. Record failures honestly;
do not hide the pre-existing Trivy policy failure if a Grok profile runs.
Do not repeatedly rerun unchanged checks after documentation-only edits.

## Task 1: Closed primitive schemas and a bounded contract checker

**Files:** Create `primitives.schema.json`, `mezo_evidence_support.py`, and
`test_mezo_primitives.py` at the mapped paths; modify graph and handoff.

**Interfaces:** The helper exports `ROOT: Path`, `load(name: str) -> dict`,
`validate(schema: dict, value: object, *, document: str) -> None`,
`assert_schema(schema: dict, *, document: str) -> None`,
`resolve(ref: str, *, document: str) -> tuple[dict, str]`, and
`ContractError(ValueError)`. `load` reads strict JSON below ROOT. `validate`
raises `ContractError` on rejection; returns None on acceptance. The document
parameter is the relative JSON filename used to resolve local references.

- [ ] **Step 1: Write rejection tests before helper behavior.** Name the break:
  accepting unknown schema keywords or dangling references makes a malformed
  contract appear validated. Use a minimal callable shell whose bodies raise
  `ContractError("unsupported contract")`, so the initial RED is an assertion
  failure on valid input, not an import/collection error.

```python
import pytest
import mezo_evidence_support as c

def test_rational_validates_exact_string_components():
    try:
        c.validate({"$ref": "primitives.schema.json#/$defs/rational"},
                   {"numerator": "300100", "denominator": "3"},
                   document="primitives.schema.json")
    except c.ContractError as error:
        pytest.fail(f"valid rational rejected: {error}")

@pytest.mark.parametrize("value", [
    {"numerator": 300100, "denominator": "3"},
    {"numerator": "300100", "denominator": "0"},
    {"numerator": "1", "denominator": "3", "decimal": "0.333"},
])
def test_rational_rejects_ambiguous_or_extra_values(value):
    with pytest.raises(c.ContractError):
        c.validate({"$ref": "primitives.schema.json#/$defs/rational"}, value,
                   document="primitives.schema.json")
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_primitives.py -q
```

Expected: valid rational assertion fails. Retain the exact exit/result.

- [ ] **Step 3: Implement the bounded checker and primitive JSON.** This is
  test infrastructure, not a general JSON Schema engine or production input
  validator. Support only the following used keywords and reject any unknown
  one during `assert_schema`: `$schema`, `$id`, `$defs`, `$ref`, `title`,
  `description`, `type`, `const`, `enum`, `properties`, `required`,
  `additionalProperties`, `items`, `minItems`, `maxItems`, `uniqueItems`,
  `minLength`, `maxLength`, `pattern`, `format`, `minimum`, `maximum`, `oneOf`.
  Annotations never substitute for validation. Disallow `$ref` siblings except
  title/description. Restrict schema types to object/array/string/integer/boolean/null;
  reject booleans as integers. Require `additionalProperties:false` for every
  object and `items` for every array. Validate each `oneOf` independently and
  require exactly one matching branch. Detect reference cycles with a recursion
  stack, allowing repeated acyclic references. Resolve JSON Pointer `~0`/`~1`.
  Only relative references to regular files inside ROOT or same-document
  fragments are allowed; reject absolute paths, URLs, percent encoding,
  traversal and escaping symlinks. Never fetch `$schema` or `$id` URLs.

  Strict JSON loading rejects duplicate keys and NaN/Infinity. String patterns
  use `re.fullmatch`; specify `^[0-9]` instead of Unicode `\d`. Formats are
  `uuid` (canonical lower-case hyphenated UUID), `date-time` (valid UTC calendar
  instant ending `Z`), and `uri` (absolute HTTPS, no credentials); unknown
  formats reject. Validate schema keyword types and bounds before instances.
  Add negative tests for each used keyword, escaped/dangling references,
  reference cycles, duplicate JSON keys, boolean integer, February 30, extra
  properties, omitted required values, ambiguous `oneOf`, and unknown format.

  Primitive definitions, each under `$defs`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:liqvera:mezo-evidence:v1:primitives",
  "$defs": {
    "id": {"type":"string","format":"uuid"},
    "sha256": {"type":"string","pattern":"^[0-9a-f]{64}$"},
    "timestamp": {"type":"string","format":"date-time"},
    "quantity_input": {"type":"string","maxLength":32,"pattern":"^[+]?[0-9]+([.][0-9]{1,8})?$"},
    "quantity": {"type":"string","maxLength":32,"pattern":"^(0|[1-9][0-9]*)([.][0-9]{0,7}[1-9])?$"},
    "address_input": {"type":"string","pattern":"^0x[0-9a-fA-F]{40}$"},
    "address": {"type":"string","pattern":"^0x[0-9a-f]{40}$"},
    "atomic_amount": {"type":"string","pattern":"^[1-9][0-9]*$","maxLength":78},
    "display_decimal": {"type":"string","pattern":"^-?(0|[1-9][0-9]*)([.][0-9]+)?$"},
    "rational": {
      "type":"object","additionalProperties":false,
      "required":["numerator","denominator"],
      "properties": {
        "numerator":{"type":"string","pattern":"^-?(0|[1-9][0-9]*)$"},
        "denominator":{"type":"string","pattern":"^[1-9][0-9]*$"}
      }
    }
  }
}
```

Shape validation does not prove positivity/range/canonical reduced fractions;
Task 2 and Task 6 add semantic checks. This explicit two-layer boundary avoids
pretending JSON Schema alone enforces arithmetic or provenance.

- [ ] **Step 4: Run focused GREEN, common verification, and update continuity.**
  Add graph nodes/bindings from the file map. Record the bounded keyword set
  and dependency decision in handoff; no runtime acceptance changes.

- [ ] **Step 5: Commit the independently usable contract foundation.**

```bash
git add schemas/mezo-evidence/v1/primitives.schema.json tests/contracts/mezo_evidence_support.py tests/contracts/test_mezo_primitives.py architecture/architecture.yaml handoff.md
git commit -m "feat: define Liqvera F2 primitive contracts"
```

## Task 2: Requests, canonical normalization and versioned public errors

**Files:** Create `quote-request.schema.json`, `reasons.schema.json`,
`error.schema.json`, `test_mezo_requests.py`; extend helper, graph, handoff.

**Interfaces:** Consumes Task 1. Add test-only
`canonical_body(body: dict) -> dict` and `canonical_bytes(body: dict) -> bytes`.
The four returned fields are exactly `instrument_id`, `side`, `quantity_base`,
`expected_payer`. These are an executable specification for F4, not a gateway.
Publish instrument ID `hyperliquid:BTC:perpetual` as a case-sensitive public
identifier; internal venue symbol remains `BTC`, internal product kind `perp`.

- [ ] **Step 1: Write the failing canonicalization/error tests.** Add a helper
  shell raising `ContractError("normalization not available")`; wrap the valid
  call in `pytest.fail` as in Task 1 to get a deliberate assertion RED.

```python
def test_same_body_has_one_canonical_representation():
    raw = {"instrument_id": "hyperliquid:BTC:perpetual", "side": "BUY",
           "quantity_base": "0.15000000",
           "expected_payer": "0x" + "AB" * 20}
    try:
        actual = c.canonical_body(raw)
    except c.ContractError as error:
        pytest.fail(f"valid request rejected: {error}")
    assert actual == {"instrument_id": "hyperliquid:BTC:perpetual", "side": "BUY",
                      "quantity_base": "0.15", "expected_payer": "0x" + "ab" * 20}
    assert c.canonical_bytes(raw) == c.canonical_bytes(actual)
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_requests.py -q
```

Expected: the canonicalization assertion fails, not test collection.

- [ ] **Step 3: Implement the request schema and canonical test oracle.**
  Request is a closed object, all four fields required; instrument has the
  exact constant above, side enum `BUY`/`SELL`, quantity references
  `quantity_input`, payer references `address_input`. No client source, URL,
  mapping, filepath, chain, price, payTo, or digest fields are accepted.

```python
from mee_contracts.exact import ExactDecimal, ExactError

def canonical_body(body: dict) -> dict:
    validate(load("quote-request.schema.json"), body,
             document="quote-request.schema.json")
    try:
        quantity = ExactDecimal.parse(body["quantity_base"])
    except (ExactError, TypeError) as error:
        raise ContractError("INVALID_INPUT") from error
    if quantity.scaled <= 0:
        raise ContractError("INVALID_INPUT")
    payer = body["expected_payer"].lower()
    if len(bytes.fromhex(payer[2:])) != 20 or int(payer[2:], 16) == 0:
        raise ContractError("INVALID_INPUT")
    return {"instrument_id": body["instrument_id"], "side": body["side"],
            "quantity_base": str(quantity), "expected_payer": payer}

def canonical_bytes(body: dict) -> bytes:
    return json.dumps(canonical_body(body), sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

Address is lower-case only after validating its 20 bytes; no duplicate submitted
address is retained. Valid `+0.15`, `00.15000000` normalize to `0.15`, consistent
with the existing ExactDecimal parser. Reject zero/negative, float `0.15`,
`NaN`, `Infinity`, `1e-2`, whitespace, empty, Unicode digits, `0.150000000`,
overflow `92233720368.54775808`, bool/null, malformed/zero address, lower-case
side `buy`, or wrong-case instrument. Test the maximum valid
`92233720368.54775807` and smallest positive `0.00000001` without rounding.

The reason schema is a string enum with `$id`
`urn:liqvera:mezo-evidence:v1:reasons`. Its values and response contexts are:

| Codes | HTTP context |
| --- | --- |
| `INVALID_INPUT`, `INVALID_DATASET`, `STALE_SOURCE`, `CLOCK_SKEW`, `IDENTITY_UNVERIFIED`, `IDENTITY_MISMATCH`, `CROSSED_BOOK`, `DEPTH_INSUFFICIENT`, `UNSUPPORTED_INSTRUMENT`, `SIMULATED_SOURCE` | 422 |
| `SOURCE_UNAVAILABLE`, `STORAGE_UNAVAILABLE`, `PAYMENT_SERVICE_UNAVAILABLE`, `PAYMENT_NOT_READY`, `PAY_TO_MISSING`, `FINALITY_RULE_UNVERIFIED`, `AUTHORIZATION_IDENTITY_UNVERIFIED`, `ARTIFACT_INTEGRITY_FAILURE` | 503 |
| `UNAUTHORIZED` | 401 |
| `NOT_FOUND` | 404 |
| `IDEMPOTENCY_CONFLICT`, `INVALID_STATE`, `PAYMENT_REJECTED`, `AUTHORIZATION_REUSED` | 409 |
| `QUOTE_EXPIRED`, `RETENTION_EXPIRED` | 410 |
| `RATE_LIMITED` | 429 |
| `PAYMENT_REQUIRED` | 402 |
| `PAYMENT_UNCERTAIN`, `MANUAL_REVIEW` | 202 recovery status, not paid success |

The closed error envelope requires `schema` constant `mee-evidence-error/v1`,
`request_id` UUID, `code` reason reference, and `message` string (1–256 chars).
No stack, path, wallet, raw payment bytes, or arbitrary `details` object.
Use stable codes for behavior; prose is display-only. Required HTTP context
does not mean every endpoint advertises every error.

- [ ] **Step 4: Add parameterized boundary cases, run GREEN and common checks.**
  Mutate a request with every forbidden client-controlled field; reject each.
  Validate every error code as an example and reject unknown code/version/extra
  field. Record canonicalization and error-version decisions in handoff.

- [ ] **Step 5: Commit.**

```bash
git add schemas/mezo-evidence/v1/quote-request.schema.json schemas/mezo-evidence/v1/reasons.schema.json schemas/mezo-evidence/v1/error.schema.json tests/contracts/mezo_evidence_support.py tests/contracts/test_mezo_requests.py architecture/architecture.yaml handoff.md
git commit -m "feat: freeze Liqvera request and error contracts"
```

## Task 3: Report, preview, immutable terms and safe resource schemas

**Files:** Create `report.schema.json`, `resources.schema.json`,
`test_mezo_resources.py`; modify graph and handoff.

**Interfaces:** Consumes primitives/request/reasons. `resources.schema.json`
exports `$defs/{preview,terms,quote,request_status,receipt,paid_report,capabilities,health,readiness}`.
`report.schema.json` describes the body hashed by F3; its own digest is absent.
All nested objects are closed, with required fields unless explicitly optional.
Use local references, not inline copies of request/rational/reason primitives.

- [ ] **Step 1: Write the paid-field leakage test.** Add a literal preview
  fixture in this test module; do not derive it from the schema under test.

```python
PREVIEW = {
    "instrument_id": "hyperliquid:BTC:perpetual", "side": "BUY",
    "quantity_base": "0.15", "snapshot_at": "2026-09-24T12:00:00Z",
    "snapshot_status": "VALID_FOR_SNAPSHOT_CALCULATION",
    "limitations": ["Calculation over the available snapshot depth."],
    "price_musd": "0.01", "expires_at": "2026-09-24T12:02:00Z"
}

def test_preview_rejects_paid_calculation():
    schema = {"$ref": "resources.schema.json#/$defs/preview"}
    try:
        c.validate(schema, PREVIEW, document="resources.schema.json")
    except c.ContractError as error:
        pytest.fail(f"valid preview rejected: {error}")
    for key in ("vwap", "notional_quote", "report", "input_files", "path", "bundle"):
        with pytest.raises(c.ContractError):
            c.validate(schema, {**PREVIEW, key: "private"},
                       document="resources.schema.json")
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_resources.py -q
```

Expected: the missing resource contract rejects a valid preview with an
assertion failure. The helper must translate missing contract files to
`ContractError`, not expose an uncaught file exception.

- [ ] **Step 3: Implement report schema using this complete field map.**
  Unqualified strings below have `minLength:1`; arrays define `items` and
  bounded sizes. `Rational` means the primitive rational; `Quantity` is the
  canonical quantity string. Timestamps use UTC `Z`; durations/ages are integer
  milliseconds. Numbers here are counts/times only, never market values.

| Required report field | Closed shape / constraint |
| --- | --- |
| `schema` | constant `mee-evidence-report/v1` |
| `report_id` | UUID |
| `identity` | `venue="hyperliquid"`, `instrument_id="hyperliquid:BTC:perpetual"`, `product_kind="perpetual"`, `payoff_kind="linear"`, `base_asset="BTC"`, `quote_asset="USD"`, `settlement_asset` nonempty string, `quantity_unit="BTC"`, `displayed_size_unit="coin"`, `contract_multiplier="1"`, `mapping_version` string, `evidence` array of `{reference: HTTPS URI, sha256: SHA256}` with at least one item |
| `request` | `side` BUY/SELL, `quantity_base` Quantity; no payer/capability/payment information |
| `source` | `source_mode` live-public/fixture, `started_at`, `observed_at`, `source_at`, `created_at` timestamps; `build_age_ms` integer -1000..5000; `payload_sha256`, `package_sha256`; `available_bid_levels`, `available_ask_levels` integers 1..20 |
| `calculation` | `requested_quantity`, `filled_quantity` Quantity; `notional_quote`, `vwap`, `worst_price`, `price_impact_bps` Rational; `consumed_levels` integer 1..20; `display` closed object with those four rational field names as display_decimal strings; `display_precision=28`, `display_rounding="ROUND_HALF_EVEN"` |
| `quality` | `snapshot_status` enum of all three spec statuses; `reason_codes` array of reason enum; `checks` array of `{name:string, result:PASS/REJECT/UNCERTAIN}`; `limitations` nonempty string array; optional `stage_a` preserves the exact original serialized object: `schema="mee-stage-a-decision/v1"`, `package_schema="mee-readonly-frozen-package/v1"`, `capture_run_id` UUID or null, `decision` enum INVALID_DATASET/INSUFFICIENT_EVIDENCE/STOP/EXTEND_LONGER_SHADOW, `reasons` nonempty array using the existing `StageAReasonCode` enum from `packages/contracts/src/mee_contracts/decision.py`; limitations explain its independent meaning |
| `reproducibility` | `engine_commit` 40 lower-case hex, `package_versions` nonempty array `{name:string, version:string}`, `lockfile_digests` nonempty array `{path:relative safe path, sha256:SHA256}`, `calculation_version="snapshot-sweep/v1"`, `policy_version="snapshot-policy/v1"`, `serialization_version="canonical-json/v1"`, `input_files` nonempty array `{path:relative safe path, sha256:SHA256}` |
| `boundaries` | `execution_authority="NONE"`, `fees_calculated=false`, `funding_calculated=false`, `net_pnl_calculated=false`, `execution_promise=false`, `calculation_label="hypothetical snapshot sweep"` |

Safe relative artifact paths are slash-separated ASCII segments of letters,
digits, underscore, hyphen and period, with no empty/`.`/`..` segment, leading
slash, backslash or drive prefix. Add explicit semantic path tests. Settlement
asset is evidence-bound, not inferred from a ticker or frozen to a guessed
value in F2. Negative/rejected requests use free errors and need no fabricated
full calculation. A schema-valid report is not necessarily eligible for sale:
F3 semantic validation must reject mismatched source/status, unavailable or
fictitious evidence, false arithmetic, and out-of-policy timing.

- [ ] **Step 4: Implement resource definitions from this field map.**

| Definition | Required fields and bounds |
| --- | --- |
| `preview` | Exactly the eight keys in PREVIEW; side/instrument/quantity primitives; snapshot status as report enum; price constant `0.01` |
| `terms` | `version="mee-evidence-terms/v1"`, `network="eip155:31611"`, `chain_id=31611`, `asset` fixed lock MUSD address, `decimals=18`, `amount_atomic="10000000000000000"`, `price_musd="0.01"`, `pay_to` canonical nonzero address, `expected_payer` canonical nonzero address, `expires_at` timestamp |
| `quote` | `schema="mee-evidence-quote/v1"`, `request_id`, `report_request_id`, `quote_id`, `report_id` UUIDs, `report_sha256`, `bundle_sha256`, `state` READY/PAYMENT_PENDING/PAYMENT_UNCERTAIN/PAID/EXPIRED/MANUAL_REVIEW, `preview`, `terms`, `retention` `{paid_days:integer minimum 7, unpaid_grace_seconds:integer minimum 900, ledger_days:integer minimum 30}` |
| `request_status` | `schema="mee-evidence-request-status/v1"`, `request_id`, `report_request_id` UUIDs, `state` PREPARING/READY/REJECTED/BUILD_FAILED; optional `quote_id` UUID (only READY), optional `reason` reason enum (only REJECTED/BUILD_FAILED); `status_location` relative path pattern `/v1/report-requests/{UUID}` |
| `receipt` | `schema="mee-evidence-receipt/v1"`, `quote_id`, `report_id`, `payment_attempt_id` UUIDs, `report_sha256`, `network`, `chain_id`, `asset`, `amount_atomic` constants as terms, `payer`, `pay_to` addresses, `tx_hash`, `block_hash` 0x+64 lower hex, `block_number`, `log_index` nonnegative integers, `confirmed_at` timestamp, `finality_policy_version` string |
| `paid_report` | `schema="mee-evidence-delivery/v1"`, `request_id` UUID, `report` report reference, `receipt` receipt reference |
| `capabilities` | `schema="mee-evidence-capabilities/v1"`, `request_id`, `instrument_id`, `instrument_label="Hyperliquid BTC linear perpetual"`, `network`, `asset`, `decimals`, `price_musd`, `amount_atomic`, `source_mode` fixture/live-public, `limitations` string array, `payment_ready` boolean, `blockers` reason array |
| `health` | `schema="mee-evidence-health/v1"`, `request_id`, `status="alive"` |
| `readiness` | `schema="mee-evidence-readiness/v1"`, `request_id`, `ready` boolean, `storage_ready` boolean, `configuration_ready` boolean, `integration_ready` boolean, `payment_ready` boolean, `blockers` reason array |

Publish no access-scope hash, capability, authorization signature, internal
path, raw proof, or payer duplicate representation. A request status response
contains no quote terms until verified artifact readback. Report/digest/receipt
cross-field equality is tested semantically, not asserted to follow from JSON
shape. Define examples for every `$defs` resource and mutate each required
field away plus one extra field to verify closure. Synthetic examples may
use nonzero repeat-byte addresses but must be explicitly fixture data and
must never populate merchant configuration.

- [ ] **Step 5: Run focused GREEN and common checks; commit.** Record the added
  read-only report-request status resource as a bounded resolution of the
  spec's 202 status-location requirement, and the display/provenance boundary.

```bash
git add schemas/mezo-evidence/v1/report.schema.json schemas/mezo-evidence/v1/resources.schema.json tests/contracts/test_mezo_resources.py architecture/architecture.yaml handoff.md
git commit -m "feat: define Liqvera report and resource schemas"
```

## Task 4: Separate request, quote and payment-attempt state graphs

**Files:** Create `states.json`, `states.schema.json`, `test_mezo_states.py`;
modify graph and handoff. All graph simulation remains test-only.

**Interfaces:** `states.json` is `{schema:"mee-evidence-states/v1", machines:[],
bindings:{}, uniqueness:[]}`. Each machine is `{name, initial, states,
transitions}`; each transition is `{from,event,to,guards:[string],effects:[string]}`.
All records are closed. Tests consume these exact field names. Missing
transitions are prohibited; a guard list is conjunction, never an implicit OR.

- [ ] **Step 1: Write tests for forbidden paths and reachable late confirmation.**

```python
def test_unknown_cannot_restart_settlement():
    path = c.ROOT / "states.json"
    assert path.is_file(), "payment state contract is missing"
    graph = c.load("states.json")
    machine = next(m for m in graph["machines"] if m["name"] == "payment_attempt")
    outgoing = {t["to"] for t in machine["transitions"] if t["from"] == "UNKNOWN"}
    assert outgoing == {"CONFIRMED", "MANUAL_REVIEW"}
    assert all(t["to"] not in {"RECEIVED", "VERIFIED", "SUBMITTING"}
               for t in machine["transitions"] if t["from"] == "MANUAL_REVIEW")
```

Name the break: allowing UNKNOWN→SUBMITTING admits a duplicate charge. Add a
small reachability traversal to prove no path from UNKNOWN/MANUAL_REVIEW back
to a submitting state. This is graph-model evidence, not database behavior.

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_states.py -q
```

Expected: explicit missing-contract assertion fails.

- [ ] **Step 3: Encode graph transitions and guards exactly.**

| Machine | Transition / event | Required guards and effects |
| --- | --- | --- |
| report_request | PREPARING→READY / artifact_verified | semantic_report_valid, live_source, immutable_publish_complete, report_and_bundle_readback_verified; issue_one_quote, bind_scope_and_digest |
| report_request | PREPARING→REJECTED / data_rejected | specific_public_reason; no_quote |
| report_request | PREPARING→BUILD_FAILED / build_failed | bounded_failure; no_quote |
| quote | initial READY | created only by artifact_verified; initial creation is not PREPARING |
| quote | READY→PAYMENT_PENDING / authorization_accepted | not_expired, scope_matches, payer_matches, terms_match, artifact_readback_verified, payment_bindings_verified, no_active_attempt, authorization_unique; persist_attempt_before_submit |
| quote | READY→EXPIRED / deadline_passed | no_active_attempt; block_new_payment |
| quote | PAYMENT_PENDING→PAYMENT_UNCERTAIN / outcome_unknown | attempt_may_have_submitted; retain_artifacts, prohibit_resubmit |
| quote | PAYMENT_PENDING→PAID / payment_confirmed | final_receipt_bound_to_authorization, atomic_entitlement_commit; deliver_original_digest |
| quote | PAYMENT_UNCERTAIN→PAID / reconciled_confirmation | final_receipt_bound_to_authorization, atomic_entitlement_commit; deliver_original_digest |
| quote | PAYMENT_PENDING→READY / definitive_pre_submit_rejection | no_broadcast_proven, not_expired; close_attempt |
| quote | PAYMENT_PENDING→EXPIRED / definitive_pre_submit_rejection_after_expiry | no_broadcast_proven; close_attempt |
| quote | PAYMENT_PENDING→MANUAL_REVIEW / inconsistent_receipt | uncertainty_requires_review; retain_artifacts, prohibit_resubmit |
| quote | PAYMENT_UNCERTAIN→MANUAL_REVIEW / reconciliation_exhausted | bounded_reconciliation_exhausted; retain_artifacts, prohibit_resubmit |
| quote | PAID→MANUAL_REVIEW / chain_inconsistency | reorg_or_rpc_conflict; retain_artifacts, prohibit_resubmit, withhold_unverified_delivery |
| quote | MANUAL_REVIEW→PAID / authoritative_confirmation | final_receipt_bound_to_authorization, atomic_entitlement_commit; deliver_original_digest |
| payment_attempt | initial RECEIVED | unique_authorization_quote_association |
| payment_attempt | RECEIVED→VERIFIED / verification_succeeded | payer_terms_deadline_nonce_valid, payment_bindings_verified |
| payment_attempt | RECEIVED→REJECTED / verification_rejected | no_submission; withhold_entitlement |
| payment_attempt | VERIFIED→SUBMITTING / submit_committed | attempt_durable, quote_not_expired, no_other_active_attempt; one_settle_call_after_commit |
| payment_attempt | VERIFIED→REJECTED / expired_before_submit | no_submission, quote_expired; withhold_entitlement |
| payment_attempt | SUBMITTING→CONFIRMED / receipt_confirmed | final_receipt_bound_to_authorization; atomic_entitlement_commit |
| payment_attempt | SUBMITTING→UNKNOWN / timeout_or_crash | outcome_not_authoritative; prohibit_resubmit |
| payment_attempt | SUBMITTING→REJECTED / definitely_not_submitted | authoritative_no_broadcast_proof; withhold_entitlement |
| payment_attempt | UNKNOWN→CONFIRMED / reconciled_confirmation | final_receipt_bound_to_authorization; atomic_entitlement_commit |
| payment_attempt | UNKNOWN→MANUAL_REVIEW / unresolved | bounded_reconciliation_exhausted; prohibit_resubmit |
| payment_attempt | CONFIRMED→MANUAL_REVIEW / chain_inconsistency | reorg_or_rpc_conflict; prohibit_resubmit |
| payment_attempt | MANUAL_REVIEW→CONFIRMED / authoritative_confirmation | final_receipt_bound_to_authorization; atomic_entitlement_commit |
| delivery | initial NOT_ATTEMPTED; NOT_ATTEMPTED→ATTEMPTED / delivery_started; ATTEMPTED→ATTEMPTED / read_retried | entitlement_matches_digest, storage_integrity_verified; no_settlement |

No state claims the client received bytes. PAID repeat reads leave payment
state unchanged. A fixture may produce a SIMULATED report but never a READY
chargeable quote in this graph. Runtime finality/identity bindings are required
guards; the F2 fixtures cannot satisfy them.

```json
{
  "finality": {
    "status": "UNRESOLVED", "code": "FINALITY_RULE_UNVERIFIED",
    "owner": "F5", "required_before": "payment_bindings_verified"
  },
  "authorization_identity": {
    "status": "UNRESOLVED", "code": "AUTHORIZATION_IDENTITY_UNVERIFIED",
    "owner": "F5", "required_before": "payment_bindings_verified",
    "requirements": ["canonical scheme-specific identity", "nonce semantics",
                     "replay domain", "quote association", "chain correlation"]
  }
}
```

Put the above as `bindings`; the closed schema fixes these unresolved statuses
for F2. No nullable guessed confirmation count or raw-payload-hash dedup key.
`uniqueness` lists closed records `{entity, fields:[string], invariant:string}`
for report_request `(access_scope,idempotency_key)`, payment_attempt
`(authorization_identity)`, chain_event `(chain_id,tx_hash,log_index)`,
entitlement `(quote_id,report_id,report_sha256)`, and active attempt per quote.
This freezes obligations, not an SQL schema or a working constraint.
Define `not_expired`/`quote_not_expired` as `now < expires_at`; equality is
expired. A submitted attempt can confirm at or after equality. Bindings with
either unresolved status force `payment_ready=false`; compatibility PASS
does not satisfy `payment_bindings_verified`.

- [ ] **Step 4: Test graph semantics and run GREEN/common checks.** Check all
  endpoints are declared, duplicate event/from pairs reject, required states
  reachable, quote READY requires readback, expiry cannot move pending/unknown
  to EXPIRED, and confirmation after expiry lacks `not_expired` guards.
  Create a mutated in-memory graph adding UNKNOWN→SUBMITTING and assert the
  graph invariant checker rejects it. Walk request/quote transitions jointly:
  invalid report→no quote; successful artifact readback→one READY quote.

- [ ] **Step 5: Commit.**

```bash
git add schemas/mezo-evidence/v1/states.json schemas/mezo-evidence/v1/states.schema.json tests/contracts/test_mezo_states.py architecture/architecture.yaml handoff.md
git commit -m "feat: freeze Liqvera quote and payment state contracts"
```

## Task 5: OpenAPI 3.1 endpoints, capability policy and x402 boundary

**Files:** Create `openapi.json`, `test_mezo_openapi.py`; modify graph/handoff.

**Interfaces:** OpenAPI `3.1.0`, info version `1.0.0`; JSON Schema dialect
2020-12; references relative to this directory. No server URL implies deployed
service. Each operation has a unique `operationId`, safe `request_id` responses,
explicit responses below, and examples validated by the bounded checker.

- [ ] **Step 1: Write the unauthorized-body and operation contract tests.**

```python
def test_paid_body_is_only_the_entitled_report_response():
    assert (c.ROOT / "openapi.json").is_file(), "HTTP contract is missing"
    api = c.load("openapi.json")
    operation = api["paths"]["/v1/reports/{report_id}"]["get"]
    assert operation["security"] == [{"CapabilityBearer": []}]
    responses = operation["responses"]
    paid = responses["200"]["content"]["application/json"]["schema"]
    assert paid == {"$ref": "resources.schema.json#/$defs/paid_report"}
    required = responses["402"]
    assert "PAYMENT-REQUIRED" in required["headers"]
    assert required["content"]["application/json"]["schema"] == {
        "$ref": "error.schema.json"}
    assert "PAYMENT-RESPONSE" in responses["200"]["headers"]
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_openapi.py -q
```

Expected: missing HTTP contract assertion.

- [ ] **Step 3: Implement the endpoint matrix.** Every path parameter is a
  required UUID. Body content is `application/json`; the one POST body is
  required. `securitySchemes.CapabilityBearer={type:"http",scheme:"bearer"}`.
  Missing/malformed bearer returns 401; any authenticated other scope or
  absent resource returns indistinguishable 404 with the same envelope shape.
  Capability minimum entropy is 256 bits, persisted only as a hash by F4.
  A valid capability does not establish payer authenticity. Do not encode real
  capabilities or signatures as OpenAPI examples.

| Method / path; operationId | Success / response definition | Other codes |
| --- | --- | --- |
| GET `/healthz`; `getHealth` | 200 health, no auth | none |
| GET `/readyz`; `getReadiness` | 200 readiness, no auth | 503 readiness |
| GET `/v1/capabilities`; `getCapabilities` | 200 capabilities, no auth | 503 error |
| POST `/v1/report-quotes`; `createReportQuote` | 201 quote, 202 request_status | 401,409,422,429,503 error |
| GET `/v1/report-requests/{report_request_id}`; `getReportRequest` | 200 request_status (terminal), 202 request_status (PREPARING) | 401,404,429,503 error |
| GET `/v1/report-quotes/{quote_id}`; `getReportQuote` | 200 quote, 202 quote (pending/uncertain/manual review) | 401,404,410,429,503 error |
| GET `/v1/reports/{report_id}`; `getReport` | 200 paid_report, 202 error recovery | 401,402,404,409,410,429,503 error |
| GET `/v1/reports/{report_id}/evidence`; `getEvidence` | 200 `application/zip` binary string schema | 401,402,404,410,429,503 error |

The ZIP schema is `{"type":"string","description":"ZIP archive bytes"}`
under media type `application/zip`; do not introduce an unsupported `binary`
format into the bounded JSON Schema checker. The HTTP byte-stream/size checks
belong to F4, not validation of a JSON string pretending to be a ZIP archive.

Only health/readiness/capabilities use `security:[]`; all remaining operations
require CapabilityBearer. POST requires `Idempotency-Key`, bounded 1–128
printable ASCII `[A-Za-z0-9._:-]+`; creation canonicalizes the four body fields
from Task 2. The key namespace is the access scope. A repeated key/body returns
the same logical request/quote; PREPARING repeats return 202 and the same
`Location`. Body mismatch returns 409 without capture or settlement. Scope
is not part of the body, and another scope's same key is isolated.

The added request-status route resolves asynchronous builds without fabricating
a quote_id or an unready quote. POST 202 has `Location` pointing to that route;
POST 201 has `Location` pointing to the actual quote. Query/body fields cannot
override price, source, receiver, scope, or report identity.

Every quote/request/report/evidence response, including errors, has header
`Cache-Control` schema constant `private, no-store`. Rate-limit 429 carries
`Retry-After` integer-seconds string. 402 `PAYMENT-REQUIRED` and 200
`PAYMENT-RESPONSE` are SDK-produced opaque base64 header strings, not a new
JSON payment protocol. Only `getReport` accepts optional `PAYMENT-SIGNATURE`,
with decoded maximum 16384 bytes documented as an F5 check. Evidence GET uses
the existing entitlement; its 402 explains that payment must use the report
route and contains the same SDK requirements, but accepts no signature and
starts no settlement. The 402 error body never contains report fields.

Bind the header family in extensions:

```json
{
  "x-liqvera-payment": {
    "protocol_version": 2,
    "scheme": "exact",
    "sdk_family_version": "2.16.0",
    "requirements_header": "PAYMENT-REQUIRED",
    "authorization_header": "PAYMENT-SIGNATURE",
    "receipt_header": "PAYMENT-RESPONSE",
    "authorization_identity_status": "UNRESOLVED_F5",
    "finality_status": "FINALITY_RULE_UNVERIFIED"
  }
}
```

No x402 payload body is handwritten or treated as pinned SDK wire evidence.
F5 must validate those actual decoded payloads using the pinned official SDK.

- [ ] **Step 4: Exercise all operations and examples.** Resolve every schema,
  check request/response examples, unique operation IDs, UUID path parameters,
  required Idempotency-Key, bearer policy, 202 Location consistency, and cache
  headers. Test same-schema unauthed/missing/sibling-scope error examples,
  guessed UUID/public tx hash not granting access, and preview rejecting paid
  fields. Assert exact endpoint behavior projections; do not write grep tests
  against prose or claim an HTTP server was run. Run focused GREEN/common checks.

- [ ] **Step 5: Commit.**

```bash
git add schemas/mezo-evidence/v1/openapi.json tests/contracts/test_mezo_openapi.py architecture/architecture.yaml handoff.md
git commit -m "feat: define Liqvera OpenAPI capability and payment boundary"
```

## Task 6: Exact vectors, future runtime assertions and complete verification

**Files:** Create `vectors.schema.json`, `vectors.json`,
`test_mezo_vectors.py`, `evidence/f2-contracts.md`; modify graph, handoff,
tasks. Update README only now to describe the implemented F2 contracts and
remaining F3–F7 work; no release or deployment claim.

**Interfaces:** Vector document is closed `{schema:"mee-evidence-vectors/v1",
vectors:[record]}`. Each record is a closed discriminated `oneOf` variant with
`id` nonempty unique string, `kind`, `owner` F3/F4/F5, `acceptance_ids` string
array, `runtime_status="NOT_RUN"`, `input`, `expected`, and
`future_assertions` nonempty array of stable assertion names. Kind-specific
input/expected objects are closed; no arbitrary JSON escape hatch. Use kinds
`sweep`, `invalid_request`, `dataset_rejection`, `idempotency`, `payment`,
`access`, `recovery`. Actual schemas describe every key in the literal records.

- [ ] **Step 1: Add the hand-derived vector test before writing vectors.**

```python
from fractions import Fraction

def test_sell_nonterminating_vector_is_exact():
    assert (c.ROOT / "vectors.json").is_file(), "exact vectors are missing"
    records = {v["id"]: v for v in c.load("vectors.json")["vectors"]}
    value = records["sell-two-levels"]["expected"]
    assert value["notional_quote"] == {"numerator": "14995", "denominator": "1"}
    assert value["vwap"] == {"numerator": "299900", "denominator": "3"}
    assert value["price_impact_bps"] == {"numerator": "10", "denominator": "3"}
    assert value["worst_price"] == {"numerator": "99900", "denominator": "1"}
    assert value["consumed_levels"] == 2
    assert records["sell-two-levels"]["runtime_status"] == "NOT_RUN"
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_vectors.py -q
```

Expected: missing vectors assertion. Each additional vector family gets its
own assertion RED before implementing that family.

- [ ] **Step 3: Encode exact sweeps and invalid request vectors.** BUY fixture
  has asks `[100000,0.10],[100100,0.10]`, bids `[99900,0.10],[99800,0.10]`.
  SELL fixture has bids `[100000,0.10],[99900,0.10]`, asks
  `[100100,0.10],[100200,0.10]`; both books are uncrossed. Store all level
  values as strings. Do not put bid=ask=100000 in one purported valid book.

| ID / side / canonical quantity | Notional | VWAP | Worst | Levels | Impact bps |
| --- | --- | --- | --- | ---: | --- |
| `buy-two-levels` BUY 0.15 | 15005/1 | 300100/3 | 100100/1 | 2 | 10/3 |
| `sell-two-levels` SELL 0.15 | 14995/1 | 299900/3 | 99900/1 | 2 | 10/3 |
| `sell-one-level` SELL 0.1 | 10000/1 | 100000/1 | 100000/1 | 1 | 0/1 |
| `sell-exact-depth` SELL 0.2 | 19990/1 | 99950/1 | 99900/1 | 2 | 5/1 |

Every rational is the two-string object, not slash notation in JSON. Filled
quantity equals requested quantity. Literal displays: BUY VWAP
`100033.3333333333333333333333`, SELL VWAP
`99966.66666666666666666666667`, impact `3.333333333333333333333333333`.
Add HALF_EVEN tie examples 1.0000000000000000000000000005→1 and
1.0000000000000000000000000015→1.000000000000000000000000002,
with exact rational numerators/denominators retained. Fix display trailing-zero
normalization in tests; use fixed-point formatting, never exponent strings.

```json
{
  "id": "sell-two-levels", "kind": "sweep", "owner": "F3",
  "acceptance_ids": ["A03"], "runtime_status": "NOT_RUN",
  "input": {
    "side": "SELL", "quantity_base": "0.15", "source_mode": "fixture",
    "bids": [["100000", "0.10"], ["99900", "0.10"]],
    "asks": [["100100", "0.10"], ["100200", "0.10"]]
  },
  "expected": {
    "notional_quote": {"numerator": "14995", "denominator": "1"},
    "vwap": {"numerator": "299900", "denominator": "3"},
    "worst_price": {"numerator": "99900", "denominator": "1"},
    "price_impact_bps": {"numerator": "10", "denominator": "3"},
    "filled_quantity": "0.15", "consumed_levels": 2,
    "snapshot_status": "SIMULATED", "chargeable_quote": false
  },
  "future_assertions": ["report_builder_matches_exact_sweep", "fixture_is_not_live_sale"]
}
```

Use actual `reconstruct_books`, `bind_reconstructed_books`, and `sweep_depth`
with synthetic retained mapping fixtures patterned on
`tests/readonly_analyzer/test_vwap.py`. Test exact results against literals;
do not compute expected values with the implementation under test. Fixture
hashes come from actual synthetic retained bytes and are labeled SIMULATED;
they are not live provenance. Check rational reduction and positive denominator
with `Fraction`; compare existing kernel outputs, then hand-derived impact
formulas. Leave existing kernel source untouched. The kernel's passing
characterization is not new report-builder acceptance.

Invalid request family includes every Task 2 case; BUY/SELL `0.21` exceeds
depth, yields `DEPTH_INSUFFICIENT`, no partial sale/quote/settlement. Dataset
vectors include age 5000/5001 ms, future 1000/1001 ms, metadata 86400000/86400001
ms and just inside/outside validity, crossed/locked, unsorted/duplicate levels,
negative size, zero/nonfinite price, wrong instrument, wrong unit/multiplier,
missing/fictitious source hash, and live upstream outage with no fixture
fallback. Record exact expected code: stale→STALE_SOURCE; future→CLOCK_SKEW;
crossed/locked→CROSSED_BOOK; malformed book→INVALID_DATASET;
wrong requested instrument→UNSUPPORTED_INSTRUMENT; wrong returned identity→
IDENTITY_MISMATCH; missing/stale/unverifiable identity provenance or unsupported
unit/multiplier→IDENTITY_UNVERIFIED; outage→SOURCE_UNAVAILABLE.
Boundary successes are shape/policy obligations only until F3 implements them.

Store deliberately malformed request bodies in `invalid_request.input` as
`request_json` (a UTF-8 JSON text string), so the vector document remains strict
JSON while preserving the precise rejected wire bytes. The closed expected
object is `{http_status:422, code:"INVALID_INPUT", chargeable_quote:false,
settlement_calls:0}` for malformed quantities and body shape; unsupported
instrument uses its specific code. Example:

```json
{
  "id": "quantity-json-number", "kind": "invalid_request", "owner": "F4",
  "acceptance_ids": ["A04"], "runtime_status": "NOT_RUN",
  "input": {
    "request_json": "{\"instrument_id\":\"hyperliquid:BTC:perpetual\",\"side\":\"BUY\",\"quantity_base\":0.15,\"expected_payer\":\"0xabababababababababababababababababababab\"}"
  },
  "expected": {"http_status":422,"code":"INVALID_INPUT","chargeable_quote":false,"settlement_calls":0},
  "future_assertions": ["invalid_request_never_creates_quote"]
}
```

For the F2 checker, parse this embedded request with `parse_float=Decimal`;
the request schema rejects its non-string quantity. No binary floating-point
market value is introduced. A malformed JSON body is rejected during strict
parsing. Payment vectors requiring a numeric or malformed wire field use an
embedded `request_json` by the same rule; valid monetary values remain strings.

- [ ] **Step 4: Encode idempotency, authorization and payment obligations.**
  Each row becomes at least one literal vector with explicit input/expected
  counts, response/status, owner and future assertion; no live secrets.

| Family | Inputs / exact expected obligation |
| --- | --- |
| Idempotency F4 | Same synthetic scope/key with `0.15000000` vs `0.15` and mixed-case payer→same logical quote; 20 parallel repeats→one request/build/quote; changed side/quantity/payer/instrument under same key→409, no new action; other scope same key→isolated object, no access to first |
| Atomic F5 | `price_musd="0.01"`, `decimals=18`→`amount_atomic="10000000000000000"`; `eip155:31611`, lock MUSD asset; reject amount ±1, six-decimal `10000`, numeric amount, mainnet 31612, wrong token/network/receiver/payer |
| Auth F4/F5 | Missing bearer→401; wrong scope/guessed ID/public tx hash→404; payer changed after quote→reject; wrong signature, expired/reused authorization→no entitlement/body; alternate encodings of one authorization→one identity/attempt, exact identity binding UNRESOLVED_F5 |
| Recovery F5 | verify success is insufficient; timeout without tx hash→UNKNOWN; several identical Transfers→no inferred confirmation; crash after durable attempt/broadcast/chain success before ledger commit→no second settlement; lost HTTP response after commit→same report/receipt, zero new settlements |
| Expiry F5 | Expired before SUBMITTING→reject new payment; submitted before expiry/confirmed after expiry→original report; UNKNOWN after expiry→retain artifacts, prohibit resubmit; paid historical report→same digest without fresh-market recalculation |
| Artifact F3/F4/F5 | Missing pre-payment bytes→no settlement; corrupted paid bytes→recovery or incident, no additional payment; valid shape but fictitious provenance→no live sale |

Add future assertions such as `twenty_concurrent_retries_one_quote`,
`atomic_amount_matches_all_layers`, `unknown_never_resubmits`,
`late_confirmation_delivers_original`, `sibling_scope_never_reads_body`,
`sdk_identity_deduplicates_reencoding`, `receipt_log_bound_to_authorization`.
The allowed assertion-name registry and owning stage belong in
`vectors.schema.json` and are tested for nonempty references and valid owner.
Do not create xfail tests that simply assert false. The vector payloads are
the downstream RED specifications; F3–F5 must first reproduce their relevant
failure against real runtime behavior before implementation and then record
their own GREEN. F2 runs no misleading skipped acceptance suite.

- [ ] **Step 5: Validate all artifacts and perform mutation self-checks.**
  Schema-check every JSON example/vector; reject unknown fields/versions and
  broken refs. Check reason/state/OpenAPI enums agree, every response schema
  exists, every state guard has a test or owned future assertion, and F1 lock
  constants agree by validated address bytes. Mutate vectors for wrong side,
  altered fraction, missing future assertion, wrong amount, and PASS runtime
  status; each mutation must fail a concrete consistency assertion. Mutate
  preview with report fields and reject it. For canonical report serialization,
  freeze sorted keys, UTF-8, compact separators, `ensure_ascii=False`,
  `allow_nan=False`, exactly one final newline, no own digest in body; record
  the implementation obligation for F3 without building the serializer now.

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py -q
git diff --check
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest -q
PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record
```

Expected: focused/full suites green. Record actual Grok result and any residual
`BLOCKED_TRIVY_HEALTHCHECK_POLICY`; no waiver or fake HEALTHCHECK. No live probe
is needed to establish this offline contract package.

- [ ] **Step 6: Record implementation status and commit.** In
  `evidence/f2-contracts.md`, record source base SHA, exact commands, timestamps,
  exits, counts, environment, RED evidence, excluded runtime obligations,
  blockers and reviewed tree fingerprint. Because a commit cannot include
  its own SHA, bind verification to the pre-commit tree fingerprint and record
  the resulting implementation SHA in a subsequent documentation-only closure
  commit if needed. Never claim stale receipts cover modified contract bytes.
  Update tasks for actual F2 deliverables only. Preserve A13–A14 external
  blockers and all other unrun runtime acceptance rows.

```bash
git add schemas/mezo-evidence/v1/vectors.schema.json schemas/mezo-evidence/v1/vectors.json tests/contracts/test_mezo_vectors.py engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md engineering/changes/2026-09-24-mezo-evidence/tasks.md architecture/architecture.yaml handoff.md README.md
git commit -m "test: freeze Liqvera F2 exact and recovery vectors"
```

Obtain independent whole-branch review after verification, focusing on payment
ambiguity, canonicalization, schema closure, and scope boundaries. Fix findings
through the same write owner and rerun affected checks before commit. If a
route exists, record only real fingerprint-bound receipts of its exact kinds.
This plan does not authorize a push, merge, release, payment, or deployment.
Rollback for F2 is a coherent revert of contract/test changes; no persisted
payment state exists. After future ledger state exists, disable new sales and
forward-recover without deleting ledger/artifacts.

## Author self-review and downstream coverage

- [x] Spec §§6–7: exactness, instrument/timing/provenance, report fields and
  reason codes covered by Tasks 1–3 and 6; actual capture/report work belongs F3.
- [x] Spec §8: hash/serialization boundary frozen in Tasks 3/6; ZIP extraction,
  manifest verification and clean offline replay belong F3, not F2 acceptance.
- [x] Spec §9: endpoints, errors, required key, capability isolation, preview
  and status location covered by Tasks 2/3/5/6; runtime auth belongs F4.
- [x] Spec §§10–12: atomic amount, immutable terms, state/expiry/unknown rules,
  uniqueness, retention and authorization bindings covered by Tasks 3–6;
  finality and SDK replay identity remain explicit F5 blockers.
- [x] Spec §§13–14: UI/operations remain F6; relevant response headers, limits,
  historical-snapshot and fixture labeling are frozen here without UI code.
- [x] Spec §§15–16: A02–A06/A10–A20 obligations have vectors or state/API
  contracts; runtime acceptance remains unrun, with existing external blockers
  retained. F2's intended RED evidence never leaves default verification red.
- [x] Every later helper/interface and field has a producing task; canonical
  body has exactly four keys; report has no own digest; paid receipt binds it.
- [x] Five Review Focus classes have owning task tests. No new runtime layer,
  dependency, migration, Stage A modification, nonce guess, or finality guess.
- [x] Plan scanned for unresolved authoring instructions and incomplete steps.
  Remaining UNRESOLVED values are deliberate, fail-closed F5 bindings.

Plan review/approval is the next step. After approval, execute Tasks 1–6 under
the selected subagent-driven workflow; implementation must not start merely
because this planning document is committed.
