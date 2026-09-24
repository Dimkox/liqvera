# Liqvera F3 Evidence Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a deterministic, independently verifiable Liqvera BTC-perpetual snapshot report and evidence bundle from a strictly captured Hyperliquid input, without changing Stage A behavior or adding payment/API authority.

**Architecture:** Add a fourth Python distribution, `mee-evidence-report`, that consumes a byte-preserved nested `mee-readonly-frozen-package/v1`, companion source evidence, and the existing read-only reconstruction/VWAP kernel. The public-capture distribution gains a separate fixed Hyperliquid evidence-capture entry point; the new distribution owns report construction, canonical JSON, deterministic ZIP publication, and an archive-first offline verifier. Root JSON Schemas remain the contract source of truth and byte-identical packaged copies make production validation work from an installed wheel without repository or network access.

**Tech Stack:** Python 3.12+, stdlib `hashlib`, `json`, `decimal`, `fractions`, `zipfile`, `tempfile`, `os`, `pathlib`, existing pytest 9.1.1, `mee-contracts==0.1.0`, `mee-readonly-analyzer==0.1.0`, and the existing public-capture `httpx==0.28.1`; no new runtime dependency, service, database, queue, wallet, SDK, UI, or deployment layer.

**Spec:** `docs/planning/LIQVERA_FACTORY_TZ.md` §§2–8, 14–16; `docs/adr/0002-liqvera-report-payment-boundary.md`; completed F2 evidence at `engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md`; immutable manual mapping review at `docs/a2-mapping-review.md`.

## Global Constraints

- Preserve `mee-readonly-frozen-package/v1`, the three existing Stage A distributions, fixture `make demo`, one-shot images, and `INSUFFICIENT_EVIDENCE` behavior byte-for-byte unless a test proves an additive F3 entry point does not alter them. Never add a writer, atomic publication helper, network import, or report builder to `mee-readonly-analyzer`.
- Add `packages/evidence-report/` as `mee-evidence-report==0.1.0`, namespace `mee_evidence_report`, depending exactly on `mee-contracts==0.1.0` and `mee-readonly-analyzer==0.1.0`. It must not import `mee_public_capture`, test helpers, HTTP clients, wallets, databases, or payment code.
- Live capture uses only `POST https://api.hyperliquid.xyz/info`, metadata first and L2 second, with exact request bytes `b'{"type":"metaAndAssetCtxs"}'` and `b'{"type":"l2Book","coin":"BTC"}'`. Their discovery SHA-256 values are respectively `9a26c1b41f6b8d71dc6345fcb0591dec99008431f3ecab38f249ad285b510cff` and `74e1560af7031d150e32c06ab991dd688096266396d5f0cf9d1ad8e02238e2a5`; implementation tests recompute these literals.
- The capture transport sets `trust_env=False`, follows no redirects, sends no cookies/auth/user headers, requests `Accept-Encoding: identity`, refuses any redirect/content encoding/fallback, applies one total deadline per response, bounds each response at 2 MiB, and retains exact request and response entity bytes plus status, content type, verified origin, UTC wall times, monotonic start/header/complete times, and elapsed/drift evidence. No user-supplied URL, path, coin, body, headers, or mapping is accepted.
- Live identity combines fresh `metaAndAssetCtxs` bytes with the inherited human review at immutable commit `8734907d489168a8a6567b93bc85920001fefd85`, whose exact `docs/a2-mapping-review.md` SHA-256 is `cd1360e92e350c0579fedc98d5f2d90c9d776c5e1dd340307d8934164dc9bfa9`. Automated metadata parsing must never be described as human review. If independent review does not accept that retained evidence as sufficient for the exact report mapping, return `IDENTITY_UNVERIFIED` with `LIVE_IDENTITY_REVIEW_REQUIRED`; do not produce live-ready status.
- The F3 semantic mapping is `hyperliquid:BTC:perpetual`, base `BTC`, quote `USD`, settlement `USDC`, payoff `linear`, request unit `BTC`, displayed size unit `coin`, multiplier `1`, and quantity step `10^-szDecimals` (`0.00001` when `szDecimals=5`). The report label `perpetual` is a versioned normalization of source `perp`/review `LINEAR_PERPETUAL`/`BASE_UNITS`; payment asset MUSD is unrelated. Price policy remains `price_decimals=1`, `max_price_significant_digits=5`; no report claims every exchange order minimum or executable trade.
- Separate `source_age_ms = observed_at - source_at`, checked inclusively in `[-1000, 5000]`, from `build_age_ms = created_at - source_at`, recorded without the 5000 ms freshness cap. Metadata age is at most 86,400,000 ms and mapping validity is inclusive. No synthetic `started + 1` timestamp may enter F3 evidence.
- Resolve the spec/core zero-size boundary fail-closed: negative and zero book sizes are `INVALID_DATASET` because the retained `BookLevel` contract admits only positive sizes; do not silently drop or repair a zero level. Record this bounded ruling in the implementation continuity entry.
- `canonical-json/v1` means UTF-8, keys sorted by Unicode code point, compact separators, `ensure_ascii=False`, no BOM, exactly one final LF, and a recursive ban on Python `float`, nonfinite `Decimal`, duplicate JSON keys, and unsupported object types. Exact rationals use reduced integer strings and positive denominators. Display uses 28 significant decimal digits and `ROUND_HALF_EVEN`; exact assertions use `Fraction`, never rendered text.
- `package_sha256` is SHA-256 of the exact nested `sealed-input/manifest.json` bytes, not its internal `manifest_sha256`. `report_sha256` is SHA-256 of final canonical `report.json` bytes and never appears inside that report. `bundle_sha256` is SHA-256 of final ZIP bytes, is returned externally, and is never embedded in the ZIP.
- Bundles use a single deterministic `ZIP_STORED` profile: sorted ASCII allowlisted member paths; fixed DOS timestamp `(1980,1,1,0,0,0)`, Unix creator, regular-file mode `0o100644`, no directory entries, comments, extras, encryption, data descriptors, ZIP64, symlinks, or nonregular members; at most 10 MiB final bytes. All member-count/path/per-member/uncompressed-total bounds are constants and tested at exact boundaries.
- Publication uses a unique same-filesystem staging file, `flush`/`fsync`, production verifier readback, no-clobber final creation, final-file readback, and parent-directory `fsync`. Never overwrite or delete a published artifact. A failed build removes only its own unpublished staging file; rollback preserves already published immutable bundles.
- The offline verifier opens no network socket and needs no wallet or database. It preflights the complete central directory before reading member bodies or extracting: absolute/drive/dot/dot-dot paths, backslashes, NUL, duplicates, Unicode NFC/casefold collisions, symlinks/nonregular modes, encryption, compression, ZIP64, comments, extras, data descriptors, count/size limits, malformed/truncated entries, and CRC failures all reject. Extraction, when needed by the legacy reader, occurs only after structure, allowlist, manifest, declared lengths, and hashes pass, into a private temporary directory.
- Stable CLI exits are `0=VERIFIED`, `1=REJECTED`, `2=USAGE_ERROR`, `3=INTERNAL_ERROR`. It prints exactly one canonical JSON result line using a stable reason-precedence table; expected corrupt input is exit 1, never an internal traceback. Production validation loads only packaged schemas whose bytes are asserted equal to root contracts; it never imports `tests/contracts/mezo_evidence_support.py`, follows schema URLs, or trusts schemas from the bundle.
- Execute exactly the 39 existing `owner="F3"` records from `schemas/mezo-evidence/v1/vectors.json` through production code: 4 sweep, 34 dataset-rejection, and 1 artifact vector. The source file is currently SHA-256 `606a4a2a406c71456aa0ade984f613c10bdef46a6ac020a953b8d3b6386717cc`; tests select by owner and assert the literal count/kind split so drift is explicit. Keep all 156 F2 `runtime_status` values literally `NOT_RUN`. Record F3 executions in a separate closed, implementation-SHA/vector-SHA-bound result artifact.
- A02 and A03 may receive F3 evidence when all their F3 vectors pass. A05/A06/A07 receive only their scoped F3 evidence. A04 remains `NOT_RUN` as an atomic acceptance row even though its two insufficient-depth subcases execute. Existing vectors do not cover A08/A09, so add explicit F3 tamper/replay machine obligations and tests without rewriting F2 vector status.
- A real live capture is a separate opt-in acceptance action after offline review. Discovery observed a credential-free response, `szDecimals=5`, and 20 bid/20 ask levels, but those observations and request hashes are discovery-only, not acceptance. External failure is `BLOCKED_EXTERNAL`; no fixture fallback and no inferred live pass.
- F3 does not add or change an HTTP service, gateway, PostgreSQL, capability, quote, x402, settlement, payment, UI, Compose stack, deployment, release, tag, or push. Preserve `PAY_TO_MISSING`, `FINALITY_RULE_UNVERIFIED`, funded-buyer/signature/receipt/SDK identity blockers, `BLOCKED_TRIVY_HEALTHCHECK_POLICY`, A13–A14 `BLOCKED_EXTERNAL`, and shadow-only authority.
- One write owner changes product files for this plan. Read-only discovery and reviews may run in parallel; review fixes return to the same writer. Every coherent task records RED/GREEN commands, adds exact graph bindings for every tracked file, updates `handoff.md` in the same commit when state/evidence changes, and commits only a passing default tree.

## Review Focus

1. A malicious ZIP whose central directory looks small but contains duplicate, colliding, encrypted, ZIP64, data-descriptor, symlink, nonregular, traversing, backslash, oversized, or CRC-bad members must be rejected before extraction or unbounded reads (Task 5).
2. Canonical report and manifest bytes must remain identical across locale, timezone, hash seed, checkout path, and rebuild; non-ASCII JSON remains UTF-8 while floats, non-reduced rationals, negative zero, and extra final newlines fail (Tasks 1, 3, and 4).
3. Fresh L2 with stale/unverified metadata, a plausible but unbound mapping, wrong returned coin, zero-size level, or inherited fictitious hash must never become `VALID_FOR_SNAPSHOT_CALCULATION` (Tasks 2, 3, and 6).
4. Atomic publication faults before/after verification, fsync, and final create must never expose a partial file, overwrite an existing digest, delete a prior bundle, or report success without readback (Task 4).
5. An installed verifier outside the checkout, with sockets denied and no root schemas/test imports, must produce the same digest/result for the clean bundle and every meaningful tamper must produce exit 1 with the stable first reason (Tasks 5 and 6).

---

## Execution State, Dependency DAG, and File Map

Planning status: **in review**. F2 remains closed at implementation
`3729bdc131ca4ac971ab04e735da2e113d68ad71`; this plan authorizes no F3 code
until human review approves it. No active Grok route exists at authoring time;
run `python3 scripts/grok_status.py` before execution and follow a route if one
appears without inventing receipts when absent.

```text
Task 1 contract gate
├── Task 2 fixed capture lane ──┐
└── Task 3 pure report kernel ──┼── Task 4 bundle + publication
                               └── Task 5 archive-first verifier
Tasks 4 + 5 ─────────────────────── Task 6 vectors + installed/offline acceptance
Tasks 2 + 6 + identity human gate ─ Task 7 opt-in live evidence + closure
```

Tasks 2 and 3 are interface-independent after Task 1 and are parallel-safe for
read-only analysis/review. Under the repository one-write-owner rule, the same
writer implements their commits (in either order) or integrates isolated
patches without concurrent shared-tree writers. Task 4 requires both. Task 5
may be reviewed in parallel with Task 4 after its bundle profile is frozen, but
its implementation commit follows Task 4. Task 6 is the offline release gate;
Task 7 never starts before its approvals and may end `BLOCKED_EXTERNAL`.

| Path | Responsibility / owner task |
| --- | --- |
| `schemas/mezo-evidence/v1/capture-context.schema.json` | Closed wall/monotonic/request/response evidence; Task 1 |
| `schemas/mezo-evidence/v1/bundle-manifest.schema.json` | Closed outer member/digest manifest; Task 1 |
| `schemas/mezo-evidence/v1/verifier-reasons.schema.json` | Stable verifier reason registry and precedence; Task 1 |
| `schemas/mezo-evidence/v1/verifier-result.schema.json` | Closed one-line verifier result; Task 1 |
| `schemas/mezo-evidence/v1/runtime-results.schema.json` | Separate SHA-bound F3 vector/A08/A09 results; Task 1 |
| `schemas/mezo-evidence/v1/reasons.schema.json` | Adds `LIVE_IDENTITY_REVIEW_REQUIRED` as a stable specific F3 reason; Task 1 |
| `schemas/mezo-evidence/v1/report.schema.json` | Split source age from uncapped build age; Task 1 |
| `tests/contracts/test_mezo_f3_contracts.py` | New contract closure/cross-reference tests; Task 1 |
| `packages/public-capture/src/mee_public_capture/evidence_capture.py` | Fixed two-request bounded transport and evidence model; Task 2 |
| `packages/public-capture/src/mee_public_capture/evidence_cli.py` | Additive F3 capture CLI; Task 2 |
| `packages/public-capture/src/mee_public_capture/package.py` | Additive explicit-mapping/observed-time inputs only; legacy defaults unchanged; Task 2 |
| `packages/public-capture/pyproject.toml` | Adds `mee-evidence-capture` entry point; Task 2 |
| `tests/public_capture/test_evidence_capture.py` | Exact transport, timing, bytes, failure/no-fallback tests; Task 2 |
| `packages/evidence-report/pyproject.toml` | Fourth distribution and package data; Task 3 |
| `packages/evidence-report/src/mee_evidence_report/{__init__,model,canonical,schemas,sealed_input,policy,builder}.py` | Pure F3 model, validation, exact calculation, report builder; Task 3 |
| `packages/evidence-report/src/mee_evidence_report/schemas/*.json` | Byte-identical offline copies of required root schemas; Task 3 |
| `tests/evidence_report/{__init__,fixtures,test_canonical,test_policy,test_builder}.py` | Pure-kernel TDD; Task 3 |
| `packages/evidence-report/src/mee_evidence_report/bundle.py` | Deterministic ZIP and atomic no-clobber publisher; Task 4 |
| `packages/evidence-report/src/mee_evidence_report/build_cli.py` | Offline capture-to-bundle CLI using a frozen build-context document; Task 4 |
| `tests/evidence_report/test_bundle.py` | Exact archive bytes/metadata and fault injection; Task 4 |
| `packages/evidence-report/src/mee_evidence_report/{verifier,cli}.py` | Archive-first verifier and stable CLI; Task 5 |
| `tests/evidence_report/{archive_factory,test_verifier,test_cli}.py` | Crafted archive/preflight/reason/exit tests; Task 5 |
| `scripts/build-f3-distributions.py` | Separate four-wheel F3 build, leaving Stage A build unchanged; Task 6 |
| `tests/evidence_report/{test_runtime_vectors,test_a08_a09}.py` | Exactly 39 production vector calls and tamper/replay obligations; Task 6 |
| `tests/installed/test_evidence_report_installed_boundary.py` | No-index outside-checkout socket-denied wheel verification; Task 6 |
| `engineering/changes/2026-09-24-mezo-evidence/evidence/f3-runtime-results.json` | Closed F3 run results bound to implementation/vector/schema SHA; Task 6 |
| `engineering/changes/2026-09-24-mezo-evidence/evidence/f3-evidence-report.md` | Commands, hashes, blockers, review and live outcome; Tasks 6–7 |
| `architecture/architecture.yaml` | Nodes, dependency edges, and exact file bindings; every task |
| `README.md`, `handoff.md`, `engineering/changes/2026-09-24-mezo-evidence/tasks.md` | Honest stage continuity; every material task |

The implementation adds pytest discovery path `tests/evidence_report` and
Ruff coverage for both the new package and tests. Do not add the new wheel to
`tools/conformance/distributions.py`: its existing three-distribution invariant
is Stage A compatibility evidence. `scripts/build-f3-distributions.py` builds
the three Stage A wheels through the existing helper and then builds exactly
`mee-evidence-report`; it records all four digests.

Add graph nodes `contract:mezo-evidence-f3`, `module:mee-evidence-report`,
`module:mee-evidence-capture`, `test:mezo-evidence-f3`, and
`evidence:mezo-evidence-f3`, with only actual lifecycle states. Bind every new
schema as `SCHEMA_MANIFEST`, every source/pyproject/script as its existing
source/config class, every test as `TEST_SOURCE`, and evidence/docs as
`DOCUMENTATION`. Add dependency edges capture→contract, report→contract,
report→readonly-analyzer, test→capture/report, and evidence→test with the
repository-required non-proof marker. Preserve all seven inherited conflicts.

Common verification after each implementation task's focused GREEN:

```bash
git diff --check
PATH="$PWD/.venv/bin:$PATH" ruff check packages/evidence-report tests/evidence_report
PATH="$PWD/.venv/bin:$PATH" make graph
```

Run `make verify` and bare pytest at Tasks 1, 3, 6, every review repair, and
final closure; Tasks 2/4/5 may use their complete focused suites plus graph and
Ruff before their coherent commit, then Task 6 supplies whole-tree evidence.
Any unexpected default-suite failure returns to the same writer before review.

## Task 1: Freeze F3 contracts, result separation, and semantic gates

**Files:** Create the five new root schemas and
`tests/contracts/test_mezo_f3_contracts.py`; modify `report.schema.json`,
`reasons.schema.json`,
`test_mezo_resources.py`, graph, handoff, and change-package tasks.

**Interfaces:** The new documents define `mee-evidence-capture-context/v1`,
`mee-evidence-bundle-manifest/v1`, `mee-evidence-verifier-result/v1`, and
`mee-evidence-runtime-results/v1`. `verifier-reasons.schema.json` is a closed
string enum whose array order is the CLI precedence order. The outer manifest
lists every ZIP member except itself and carries `manifest_sha256`, computed
from the exact canonical manifest with that field absent.

- [ ] **Step 1: Write contract RED tests.** Start with imports of the existing
  bounded F2 validator, then assert all new schema files load, self-validate,
  reject extra properties, resolve only local registered refs, and accept one
  literal valid example each. Add report tests proving `source_age_ms` is
  required and bounded at `-1000`/`5000`, `build_age_ms=15000` is valid, and
  `build_age_ms < -1000` is invalid.

```python
def test_report_separates_source_freshness_from_build_latency():
    report = deepcopy(REPORT)
    report["source"]["source_age_ms"] = 5000
    report["source"]["build_age_ms"] = 15000
    c.validate(c.load("report.schema.json"), report, document="report.schema.json")


def test_f3_runtime_results_do_not_mutate_f2_statuses():
    vectors = c.load("vectors.json")["vectors"]
    assert len(vectors) == 156
    assert {row["runtime_status"] for row in vectors} == {"NOT_RUN"}
    assert len([row for row in vectors if row["owner"] == "F3"]) == 39
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/contracts/test_mezo_f3_contracts.py \
  tests/contracts/test_mezo_resources.py -q
```

Expected: missing schema/source-age assertions fail; retain exact output.

- [ ] **Step 3: Implement closed schema shapes.** The capture context contains
  exactly `schema`, `source_mode`, `origin`, `instrument_id`, `meta`, `l2book`,
  and `mapping_review`. Each exchange record contains exact request/response
  member path, SHA-256, byte length, status, content type, UTC
  `started_at`/`headers_at`/`completed_at`, integer monotonic nanoseconds for
  the same three events, `elapsed_ns`, and (for L2) `source_at` plus
  `source_age_ms`. Require `source_mode` live-public/fixture and forbid a live
  record with fixture provenance. Mapping review binds immutable commit, path,
  exact bytes digest, policy version, review instant, and inclusive validity.

  The bundle manifest contains exact profile constants, `report_sha256`,
  `package_sha256`, and sorted unique members `{path,length,sha256}`; it has no
  `bundle_sha256`. The result schema pairs status and exits exactly:
  VERIFIED/0, REJECTED/1, USAGE_ERROR/2, INTERNAL_ERROR/3, with unique ordered
  reasons and nullable verified digests only where the status permits.
  Runtime results require implementation SHA/tree, vector file SHA, schema
  fingerprint, environment, command, exact selected count/kind split,
  per-vector `{id,outcome,reason}`, A08/A09 obligations, and explicit
  `acceptance_status` values; they prohibit PASS for A04.

  Add `LIVE_IDENTITY_REVIEW_REQUIRED` to the existing public reason registry
  so an insufficient retained human review remains more specific than a
  generic service error; pair it with `IDENTITY_UNVERIFIED`, never with VALID.

- [ ] **Step 4: Freeze stable verifier reasons.** Include at least:
  `ARGUMENT_INVALID`, `ARCHIVE_OPEN_FAILED`, `ARCHIVE_SIZE_EXCEEDED`,
  `MEMBER_COUNT_EXCEEDED`, `MEMBER_PATH_INVALID`, `MEMBER_DUPLICATE`,
  `MEMBER_COLLISION`, `MEMBER_TYPE_FORBIDDEN`, `MEMBER_ENCRYPTED`,
  `MEMBER_COMPRESSION_FORBIDDEN`, `MEMBER_ZIP64_FORBIDDEN`,
  `MEMBER_COMMENT_FORBIDDEN`, `MEMBER_EXTRA_FORBIDDEN`,
  `MEMBER_DESCRIPTOR_FORBIDDEN`, `MEMBER_SIZE_EXCEEDED`,
  `TOTAL_SIZE_EXCEEDED`, `MEMBER_SET_MISMATCH`, `MEMBER_CRC_MISMATCH`,
  `MANIFEST_NON_CANONICAL`, `MANIFEST_INVALID`, `MANIFEST_HASH_MISMATCH`,
  `MEMBER_LENGTH_MISMATCH`, `MEMBER_HASH_MISMATCH`, `SEALED_INPUT_INVALID`,
  `CAPTURE_CONTEXT_INVALID`, `IDENTITY_UNVERIFIED`, `REPORT_INVALID`,
  `REPORT_HASH_MISMATCH`, `CALCULATION_MISMATCH`,
  `REPRODUCIBILITY_MISMATCH`, and `INTERNAL_ERROR`. The listed order is the
  deterministic first-reason precedence; tests reject duplicates/reordering
  between registry and packaged result logic.

- [ ] **Step 5: Run GREEN and contract/full checks.** Run the RED command,
  all F2 contract modules, `make verify`, and bare pytest. Confirm the source
  report schema still rejects self-digests/payment fields and all 156 F2
  vectors remain NOT_RUN.

- [ ] **Step 6: Update continuity and commit.** Mark only F3 contract planning
  execution started after approval; do not imply a report exists.

```bash
git add schemas/mezo-evidence/v1 tests/contracts/test_mezo_f3_contracts.py \
  tests/contracts/test_mezo_resources.py architecture/architecture.yaml \
  handoff.md engineering/changes/2026-09-24-mezo-evidence/tasks.md
git commit -m "feat: define Liqvera F3 evidence contracts"
```

**Review gate:** Independent contract/edge review must approve the digest
ownership, source/build age distinction, schema closure, reason precedence,
and runtime-result separation before Task 4 consumes the contracts.

## Task 2: Add fixed public capture with real source and identity evidence

**Files:** Create `evidence_capture.py`, `evidence_cli.py`, and
`test_evidence_capture.py`; modify public-capture package metadata and only the
additive call surface in `package.py`; update graph/handoff.

**Interfaces:** `capture_hyperliquid(*, output: Path, clock: CaptureClock,
transport: FixedInfoTransport) -> CapturedEvidence`; production supplies the
clock/transport internally, while tests inject them. `FixedInfoTransport.post`
accepts only an internal `Literal["meta","l2book"]`; it does not accept URL or
body. `CapturedEvidence` contains exact member bytes plus a schema-valid
context. `write_f3_capture(root, evidence, *, run_id)` creates
`sealed-input/` and `source-evidence/` without changing `write_frozen_package`'s
legacy root layout/canonical bytes for existing callers.

- [ ] **Step 1: Write transport and legacy RED tests.** Use an injected fake
  transport to assert the exact two calls/order/body hashes, fixed origin and
  headers, one attempt each, real clock events, and byte-identical stored
  responses. Add refusal cases for 3xx, non-200, non-JSON content type,
  content encoding, >2 MiB stream, timeout, malformed metadata, wrong coin,
  missing BTC, and L2 failure after metadata; assert no fixture call and no
  published root. Re-run existing package/runtime tests and hash fixture output
  before/after the additive path.

```python
def test_capture_uses_exact_fixed_requests_without_fallback(tmp_path):
    captured = capture_hyperliquid(output=tmp_path / "capture", clock=clock, transport=fake)
    assert fake.calls == [
        ("meta", b'{"type":"metaAndAssetCtxs"}'),
        ("l2book", b'{"type":"l2Book","coin":"BTC"}'),
    ]
    assert captured.l2book.response_bytes is fake.l2_bytes
    assert captured.context["l2book"]["source_age_ms"] == 5000
```

- [ ] **Step 2: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/public_capture/test_evidence_capture.py \
  tests/public_capture/test_runtime_package.py -q
```

Expected: the new module/entry point is absent; existing legacy tests remain
green when run alone.

- [ ] **Step 3: Implement the fixed transport and timing model.** Use one
  `httpx.Client(trust_env=False, follow_redirects=False, timeout=<bounded>)`
  with an empty cookie jar and exact headers `Content-Type: application/json`,
  `Accept: application/json`, `Accept-Encoding: identity`, plus a fixed
  non-secret User-Agent. Stream raw identity bytes into a bounded buffer;
  reject redirects before reading a redirect target and reject unexpected
  encoding/content type/status. Record UTC from integer nanoseconds and
  monotonic nanoseconds immediately before send, at headers, and after final
  byte. Validate monotonic order and wall/monotonic drift; never derive receive
  time from exchange time. Enforce one absolute end-to-end deadline across
  connect/TLS/headers/all body chunks (not only an idle per-read timeout), using
  the already proven POSIX main-thread timer pattern with handler/timer restoration;
  unsupported contexts fail before network I/O.

- [ ] **Step 4: Create the F3 mapping companion fail-closed.** Retain the exact
  metadata response and exact manual-review Markdown bytes. Locate one BTC
  metadata entry with `szDecimals=5`; derive `quantity_step="0.00001"` and bind
  it to the immutable review hash/reference. Build the nested mapping using
  USDC settlement, coin units, multiplier 1, and the explicit normalization
  version. Do not claim metadata itself reviewed those semantics. If the
  immutable review file/hash/commit policy or expected fields do not match,
  emit `IDENTITY_UNVERIFIED`/`LIVE_IDENTITY_REVIEW_REQUIRED` and do not write a
  valid live sealed input. Any legacy `"a" * 64`, `reviewed/v1`, USD settlement,
  `0.001` step, or fabricated approval fails F3 tests.

- [ ] **Step 5: Add only the additive CLI.** `mee-evidence-capture --output
  ABSOLUTE_NEW_DIRECTORY` accepts no URL/coin/mapping/header option and refuses
  an existing target. Exit 0 publishes a complete capture directory; exit 1
  reports a stable safe reason; exit 2 is usage. Existing `mee-public-capture`
  and Stage A config remain unchanged.

- [ ] **Step 6: Run GREEN and compatibility checks; commit.** Run focused
  tests, all `tests/public_capture`, `make demo`, graph, Ruff, and diff check.
  No live network call is part of default tests.

```bash
git add packages/public-capture tests/public_capture/test_evidence_capture.py \
  architecture/architecture.yaml handoff.md
git commit -m "feat: capture fixed Hyperliquid report evidence"
```

**Review gate:** Security review inspects transport construction, bounded
reads, redirect/proxy/cookie/auth refusal, exact retained bytes, filesystem
publication, and absence of fallback. Identity review separately decides
whether the inherited human review is sufficient; code cannot self-approve it.

## Task 3: Build the pure exact report kernel and offline schema package

**Files:** Create the evidence-report distribution, `model.py`, `canonical.py`,
`schemas.py`, `sealed_input.py`, `policy.py`, `builder.py`, packaged schemas,
and the four initial test modules; modify root build/test config and graph.

**Interfaces:**

```python
def canonical_json_bytes(value: object) -> bytes: ...
def strict_json_bytes(payload: bytes) -> object: ...
def rational_document(value: Fraction) -> dict[str, str]: ...
def display_fraction(value: Fraction, *, significant_digits: int = 28) -> str: ...
def inspect_sealed_input(root: Path, limits: SealedInputLimits) -> SealedInput: ...
def evaluate_dataset(input: ReportInput) -> PolicyDecision: ...
def build_report(input: ReportInput, context: BuildContext) -> BuiltReport: ...
```

`BuildContext` freezes `report_id`, request, created UTC instant, engine commit,
package versions, algorithm/policy/serialization versions, and lockfile
digests. Production code never calls `uuid4`, `time.time`, Git, or package
metadata during serialization; the caller supplies all nondeterminism once.

- [ ] **Step 1: Write canonical/model RED tests.** Test UTF-8 non-ASCII,
  sorted compact keys, one LF, bool/null/string/integer/list/object support,
  rejection of every float including finite values, NaN/Infinity Decimal,
  duplicate keys/BOM/invalid UTF-8/two newlines, and reduced rational signs.
  Parameterize HALF_EVEN ties, nonterminating 1/3, negative values, zero, very
  large/small exact values, and the four F2 sweep displays.

- [ ] **Step 2: Run canonical RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/evidence_report/test_canonical.py -q
```

Expected: import failure for the unimplemented distribution.

- [ ] **Step 3: Implement canonical/model code and packaged schemas.** Include
  byte-identical copies of `primitives`, `quote-request`, `reasons`, `report`,
  and all five F3 schemas. Use `importlib.resources` only; validate schema-copy
  equality and SHA at tests/build time. Implement a production-bounded schema
  validator inside `schemas.py` for the exact used Draft 2020-12 subset, or
  share production code placed in this package; never import the F2 test
  helper. Unknown keywords/refs and any network URL resolution fail closed.

- [ ] **Step 4: Write sealed-input/policy/builder RED tests.** Cover exact
  nested manifest byte hashing; strict canonical manifest and keys; declared
  length enforcement ignored by the legacy reader; required member set;
  symlink/backslash/extra members; bounded reads; raw L2/context hash linkage;
  fresh/stale/future/metadata-validity boundaries; wrong requested/returned
  identity; crossed/locked/unsorted/duplicate/negative/zero/nonfinite levels;
  wrong unit/multiplier/evidence; outage; fixture status; exact BUY/SELL;
  insufficient depth; and report schema validation. Assert rejection yields a
  typed `PolicyDecision` and no report bytes.

```python
def test_build_age_does_not_replace_source_freshness(valid_input, context):
    valid_input = replace(valid_input, source_age_ms=5000)
    context = replace(context, created_at_ms=valid_input.source_at_ms + 15000)
    built = build_report(valid_input, context)
    assert built.document["source"]["source_age_ms"] == 5000
    assert built.document["source"]["build_age_ms"] == 15000
```

- [ ] **Step 5: Run policy/builder RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/evidence_report/test_policy.py tests/evidence_report/test_builder.py -q
```

- [ ] **Step 6: Implement strict input admission and exact report assembly.**
  Preflight the directory before invoking `FrozenPackageEvidenceReader`; the
  companion closes its known length/key/path/read bounds while the legacy
  reader continues unchanged. Reuse `reconstruct_books`,
  `bind_reconstructed_books`, and `sweep_depth`; calculate impact as exact
  `Fraction` from the relevant best level. A valid fixture produces
  `SIMULATED` with `SIMULATED_SOURCE`, never live chargeability. Invalid data
  produces no report. Live produces `VALID_FOR_SNAPSHOT_CALCULATION` only when
  every source, timing, identity, mapping, and arithmetic gate passes.

  Project the independent existing Stage A verdict without changing it.
  Populate exact input-file hashes, package versions, lockfile digests, engine
  commit, calculation/policy/serialization versions, limitations, and
  `execution_authority=NONE`. Hash only final report bytes. Deterministically
  rebuilding the same `ReportInput`/`BuildContext` must return identical
  document, bytes, and digest.

- [ ] **Step 7: Run GREEN/full verification and commit.** Update root pytest,
  Ruff, and mypy package discovery, but leave Stage A distribution helper and
  its three-wheel tests unchanged. Run the four new modules, analyzer/capture
  regressions, `make verify`, bare pytest, graph, Ruff, mypy, and diff check.

```bash
git add packages/evidence-report tests/evidence_report pyproject.toml \
  architecture/architecture.yaml handoff.md decisions.md
git commit -m "feat: build exact Liqvera evidence reports"
```

**Review gate:** Independent exactness review checks fraction/display math,
canonical bytes, schema validation, identity provenance, Stage A projection,
and every path that could turn REJECTED/SIMULATED into VALID.

## Task 4: Create deterministic bundles and atomic no-clobber publication

**Files:** Create `bundle.py`, `build_cli.py`, and `test_bundle.py`; update
package entry points, graph, and handoff.

**Interfaces:**

```python
def assemble_bundle_members(capture_root: Path, report: BuiltReport,
                            algorithm: AlgorithmDescriptor) -> BundleMembers: ...
def bundle_bytes(members: BundleMembers) -> bytes: ...
def publish_verified_bundle(destination: Path, members: BundleMembers,
                            verify: Callable[[Path], VerifierResult]) -> PublishedBundle: ...
```

`BundleMembers` owns immutable bytes, not open paths. The allowlist is exactly
the nested sealed-input members, six source-evidence members, one algorithm
descriptor, `report.json`, and outer `manifest.json`; no directory entries.

- [ ] **Step 1: Write deterministic/archive RED tests.** Build twice under
  different temp roots, timezones, locales, and `PYTHONHASHSEED`; assert exact
  ZIP bytes/digest. Inspect every `ZipInfo` for sorted path, ZIP_STORED, fixed
  time/mode/creator, zero flags/comments/extras, no descriptor/ZIP64, exact CRC,
  and <=10 MiB. Assert nested sealed-input files are byte-for-byte equal to the
  captured originals and outer manifest excludes only itself from members,
  contains its canonical self-hash, and never contains `bundle_sha256`.

- [ ] **Step 2: Write publication RED tests.** Inject faults at staging write,
  file fsync, verifier rejection, no-clobber create, final readback, and parent
  fsync. Assert no visible partial destination, no overwrite, prior bundles
  preserved, only owned staging cleaned, and success only after the final
  digest matches verified readback.

- [ ] **Step 3: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/evidence_report/test_bundle.py -q
```

- [ ] **Step 4: Implement deterministic assembly.** Use an in-memory bounded
  member map and explicit `ZipInfo`; never `ZipFile.write` host files because
  it leaks host metadata. Build canonical algorithm descriptor bytes from the
  frozen build context. Validate member paths/lengths/hashes before ZIP
  construction and reject any output above the final 10 MiB bound.

- [ ] **Step 5: Implement atomic publication.** Create the staging file with
  `O_CREAT|O_EXCL`, restrictive mode, and an unpredictable name in the exact
  destination directory. Verify that staged file through the production
  verifier callback, fsync, and publish with an atomic no-replace primitive;
  where the platform lacks one, use hard-link no-clobber plus unlink of the
  owned staging path on the same filesystem. Re-open/hash final bytes, fsync
  final and parent, and return its external digest. Existing destination is a
  stable conflict, never success.

- [ ] **Step 6: Add the offline build CLI.** `mee-evidence-build --capture
  ABSOLUTE_CAPTURE --build-context ABSOLUTE_CANONICAL_JSON --output
  ABSOLUTE_NEW_BUNDLE` accepts a closed build-context document and invokes the
  production builder/publisher. It refuses existing outputs and does not fetch
  Git/package/time/network state; the retained context makes replay exact.
  Invalid input returns a safe nonzero result without a partial artifact.

- [ ] **Step 7: Run GREEN, focused regressions, common checks, and commit.**

```bash
git add packages/evidence-report/src/mee_evidence_report/bundle.py \
  packages/evidence-report/src/mee_evidence_report/build_cli.py \
  packages/evidence-report/pyproject.toml \
  tests/evidence_report/test_bundle.py architecture/architecture.yaml handoff.md
git commit -m "feat: publish deterministic Liqvera evidence bundles"
```

**Review gate:** Filesystem/security review checks all fault injection and
platform semantics, especially no-clobber publication and cleanup ownership.

## Task 5: Implement archive-first offline verification and stable CLI

**Files:** Create `verifier.py`, `cli.py`, `archive_factory.py`,
`test_verifier.py`, and `test_cli.py`; extend package entry points; update
graph/handoff.

**Interfaces:** `verify_bundle(path: Path) -> VerifierResult` never raises for
untrusted bundle rejection. Internal programming/environment faults map to
INTERNAL_ERROR. Console script `mee-evidence-verify BUNDLE` writes one
canonical result line to stdout and no traceback/extra stdout.

- [ ] **Step 1: Build malicious archives and RED matrix.** The test-only
  archive factory creates each forbidden central-directory condition without
  reusing production bundle code: traversal (`../`, absolute, dot, drive),
  backslash, NUL, duplicate raw name, NFC collision, casefold collision,
  directory/symlink/device modes, encrypted flag, DEFLATED member, ZIP64,
  archive/member comments/extras, data descriptor, member/count/total/final
  size over exact bounds, undeclared/missing members, length/hash mismatch,
  bad CRC, truncated local data, and malformed EOCD. Instrument member reads
  and temp creation to prove preflight rejects before extraction/body reads.

- [ ] **Step 2: Add semantic tamper RED tests.** Mutate and, where relevant,
  coherently rehash each raw request, metadata response, L2 response, mapping
  review, capture context, algorithm descriptor, report, nested manifest,
  outer manifest, package/report digest, and exact calculation. Assert a clean
  rebuild verifies and every meaningful mutation returns REJECTED with the
  stable earliest reason.

- [ ] **Step 3: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/evidence_report/test_verifier.py tests/evidence_report/test_cli.py -q
```

- [ ] **Step 4: Implement two-phase verification.** First bound the outer file
  and parse/preflight every central-directory record without extraction. Then
  read bounded bytes, force CRC verification, validate exact allowlist,
  canonical outer manifest/self-hash/member length/hash, and only then write
  the byte-verified nested sealed input to a mode-0700 private temp directory.
  Validate nested package/context/report/algorithm using packaged schemas and
  production strict readers; reconstruct/bind/recalculate exact values and
  compare the entire canonical report and digest. Verify package/report hashes
  under their defined ownership and compute the external bundle hash last.

- [ ] **Step 5: Implement stable results/exits.** Collect detected reasons but
  order/deduplicate them by the frozen registry. CLI misuse returns canonical
  USAGE_ERROR/2, corrupt input REJECTED/1, clean VERIFIED/0, and unexpected
  internal fault INTERNAL_ERROR/3 with no sensitive path or exception text.
  Socket creation is never attempted by imports or verification.

- [ ] **Step 6: Run GREEN, focused security checks, and commit.** Run verifier,
  CLI, bundle, builder tests, socket-denial test in-process, graph, Ruff, and
  diff check. Run Bandit if available through the existing Grok profile but do
  not create a receipt on an absent route.

```bash
git add packages/evidence-report/src/mee_evidence_report/verifier.py \
  packages/evidence-report/src/mee_evidence_report/cli.py \
  packages/evidence-report/pyproject.toml tests/evidence_report/archive_factory.py \
  tests/evidence_report/test_verifier.py tests/evidence_report/test_cli.py \
  architecture/architecture.yaml handoff.md
git commit -m "feat: verify Liqvera evidence bundles offline"
```

**Review gate:** Independent adversarial archive review and security review
both approve the actual diff. Any verifier code change invalidates both and
requires focused re-review.

## Task 6: Execute F3 vectors, A08/A09 obligations, and installed-wheel proof

**Files:** Create the separate build script, runtime-vector/A08-A09/installed
tests, runtime result JSON, and F3 evidence Markdown; modify root configs,
graph, README/handoff/tasks.

**Interfaces:** A production adapter in `test_runtime_vectors.py` decodes each
F3 vector literal and invokes only `mee_evidence_report` functions. It does not
call or copy `dataset_reason`, `check_sweep`, `bound_book`, or any oracle from
`tests/contracts/test_mezo_vectors.py`. `f3-runtime-results.json` is generated
from actual parametrized outcomes and validated before commit.

- [ ] **Step 1: Write the exact selection RED.** Assert vectors file SHA,
  total 156/all NOT_RUN, owner F3 count 39, and kind split
  `{sweep:4,dataset_rejection:34,artifact:1}`. Parameterize 39 production calls
  by ID. Assert A02/A03 exact outputs, A05's 24 cases, A06's 8 cases, A07's
  injected outage/no fallback, four fixture sweeps, and fictitious provenance.
  Tag the two insufficient-depth executions as F3 subcase evidence while the
  results document keeps A04 NOT_RUN.

- [ ] **Step 2: Add A08/A09 machine obligations.** Create a closed local list
  whose IDs cover every semantic tamper and archive class from Task 5, plus a
  clean deterministic rebuild/recalculation with sockets denied. Assert no
  existing F2 vector is edited and the new result schema records A08/A09 as F3
  scoped evidence, not final clean-machine acceptance unless the installed
  test below passes.

- [ ] **Step 3: Run RED.**

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/evidence_report/test_runtime_vectors.py \
  tests/evidence_report/test_a08_a09.py -q
```

Expected: missing production adapter/results cause named failures; no F2
runtime status changes.

- [ ] **Step 4: Implement vector fixtures and pass exactly 39.** Translate
  literal dataset/sweep inputs into captured bytes/context through test-only
  deterministic fixture construction, then invoke production policy/builder
  and verifier. Do not loosen production input shapes to accommodate vectors.
  Recompute the vectors SHA and fail loudly if it differs from the planned
  value until a reviewed contract change explains the drift.

- [ ] **Step 5: Prove the installed boundary.** `build-f3-distributions.py`
  creates the original three wheels through the existing path and the new
  wheel separately. In fresh build/install environments outside the checkout,
  install with `--no-index --find-links`; run Python `-I` from an unrelated
  directory and deny `socket.socket`/`create_connection`. Verify one clean
  bundle and one tampered bundle using the console script with root schemas,
  source checkout, test modules, network, wallet, and DB unavailable. Inspect
  dependencies/namespaces/entry points: the new wheel may expose only namespace
  `mee_evidence_report` and console entries `mee-evidence-build` and
  `mee-evidence-verify`, with exact contracts/analyzer dependencies and no
  capture/network/payment symbols.

- [ ] **Step 6: Run GREEN and final offline verification.** Required commands:

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/evidence_report -q
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/installed/test_evidence_report_installed_boundary.py -q
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest -q
PATH="$PWD/.venv/bin:$PATH" ruff check packages/evidence-report tests/evidence_report \
  packages/public-capture/src/mee_public_capture/evidence_capture.py \
  packages/public-capture/src/mee_public_capture/evidence_cli.py
PATH="$PWD/.venv/bin:$PATH" mypy -p mee_evidence_report
PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record
trivy config --exit-code 1 .
git diff --check
PATH="$PWD/.venv/bin:$PATH" make graph
```

The expected Grok/Trivy disposition remains exactly two inherited LOW DS-0026
one-shot Dockerfile findings unless current output proves otherwise. Any new
failure is not inherited and blocks review.

- [ ] **Step 7: Commit the verified implementation.** Stage product/test/graph
  files and continuity prose, inspect the index, and commit the exact tree that
  passed Step 6. Do not put a guessed future commit SHA into the runtime result.

```bash
git add scripts/build-f3-distributions.py tests/evidence_report \
  tests/installed/test_evidence_report_installed_boundary.py pyproject.toml \
  architecture/architecture.yaml README.md handoff.md \
  engineering/changes/2026-09-24-mezo-evidence/tasks.md
git commit -m "test: verify Liqvera F3 evidence reports offline"
```

- [ ] **Step 8: Bind evidence to the exact implementation SHA.** On the clean
  implementation commit, rerun the evidence-producing focused command and
  write actual commands, UTC times, environment, exits/counts, vector SHA,
  implementation SHA/tree, schema/package fingerprints, A08/A09 outcomes,
  blockers, omissions, and rollback into the closed runtime result and F3
  evidence Markdown. Keep required records NOT_RUN/BLOCKED and live acceptance
  absent. Validate both documents, run diff/graph checks, and commit them as a
  documentation/evidence-only child of the implementation; this avoids an
  impossible self-referential commit hash.

```bash
git add architecture/architecture.yaml \
  engineering/changes/2026-09-24-mezo-evidence/evidence/f3-runtime-results.json \
  engineering/changes/2026-09-24-mezo-evidence/evidence/f3-evidence-report.md \
  handoff.md engineering/changes/2026-09-24-mezo-evidence/tasks.md
git commit -m "docs: bind Liqvera F3 offline evidence"
```

- [ ] **Step 9: Run independent whole-F3 reviews in parallel.** Code review
  checks production boundaries and exactness; security review checks capture,
  archive, temp and atomic publication; edge review attacks time/numeric/path
  limits; acceptance review checks exactly 39 executions, A04 status, A08/A09,
  installed proof, unchanged Stage A/F2, exact implementation SHA/tree, and
  the evidence-only binding commit. All reviewers inspect the same implementation
  bytes. Consolidate findings; the sole writer applies one fix wave, reruns
  affected/full checks, regenerates the exact-SHA evidence, and reviewers
  re-review the final diff. Do not self-approve.

## Task 7: Run opt-in live-source acceptance and close F3 honestly

**Files:** Update only evidence/continuity/result artifacts unless a reviewed
live finding requires returning to the same writer for a tested code repair.

**Interfaces:** Live acceptance produces a new capture directory and bundle in
an ignored/operator-selected evidence area. Published repository evidence
contains hashes, sizes, sanitized timestamps/status, commands, and reason
codes—not entire volatile payloads, headers, credentials, or user data.

- [ ] **Step 1: Confirm human/live gates.** Independent review must explicitly
  accept or reject the inherited mapping review for BTC perpetual semantics.
  Confirm the action is read-only, credential-free, uses the fixed official
  origin, and writes only a new local artifact. If not approved/sufficient,
  record `LIVE_IDENTITY_REVIEW_REQUIRED` and `IDENTITY_UNVERIFIED`; F3 fixture
  work remains valid but live-source validation is blocked.

- [ ] **Step 2: Run the separate live capture when authorized.** Use the
  installed capture entry point with a unique absolute output directory; then
  invoke the installed builder/publisher and socket-denied verifier. Record
  command, UTC start/end, exact code SHA, request/body digests, response member
  digests/lengths/status/content types, timing fields, source age, metadata BTC
  identity, report/package/bundle digests, verifier result, and omissions.
  Never substitute discovery probes or fixture bytes.

```bash
mee-evidence-capture --output "$ABSOLUTE_NEW_F3_CAPTURE"
mee-evidence-build --capture "$ABSOLUTE_NEW_F3_CAPTURE" \
  --build-context "$ABSOLUTE_F3_BUILD_CONTEXT" \
  --output "$ABSOLUTE_NEW_F3_BUNDLE"
mee-evidence-verify "$ABSOLUTE_NEW_F3_BUNDLE"
```

The operator supplies the three explicit absolute paths; scripts must refuse
empty, relative, existing, or broad workspace/root targets. If Hyperliquid is
unavailable, record `BLOCKED_EXTERNAL` with the actual safe reason and do not
retry through a proxy or fixture.

- [ ] **Step 3: Re-run deterministic verification on retained live bytes.**
  With network denied, rebuild twice from the retained capture and frozen
  build context; both bundles and verifier results must match exactly. Confirm
  20-level wording says “available snapshot depth,” not complete book or
  execution promise.

- [ ] **Step 4: Close with exact SHA-bound evidence.** Commit any live evidence
  record separately from the already reviewed implementation. Then create a
  documentation-only closure commit that binds the reviewed implementation
  SHA/tree/fingerprint, result JSON SHA, review scopes/outcomes, live outcome
  or named blocker, unchanged payments/Trivy status, and next action F4. Run
  diff/link/fence/graph checks for closure; do not relabel a documentation
  commit as the verified implementation.

```bash
git add engineering/changes/2026-09-24-mezo-evidence/evidence/f3-evidence-report.md \
  engineering/changes/2026-09-24-mezo-evidence/evidence/f3-runtime-results.json \
  README.md handoff.md engineering/changes/2026-09-24-mezo-evidence/tasks.md \
  architecture/architecture.yaml
git commit -m "docs: close Liqvera F3 evidence report phase"
```

**Closure rule:** F3 is complete only when offline implementation/review is
green and the live gate is either verified with retained SHA-bound evidence or
explicitly recorded as a named blocker consistent with the canonical stage
exit. No F4–F7, payment, deployment, release, or push follows automatically.

## Rollback and Forward Recovery

- Before publication, revert the coherent F3 commits and remove only their
  unpublished temp artifacts. Existing Stage A packages and F2 contracts stay
  authoritative.
- After a bundle is published, never mutate or delete it as rollback. Disable
  selection of its digest, preserve it for audit, fix forward under a new
  implementation/version and report/bundle digest, and record the superseding
  reason.
- A bad live identity decision invalidates live-ready status and future quote
  eligibility; it does not rewrite historical bytes. Mark the result
  `IDENTITY_UNVERIFIED`, retain evidence, and require a new reviewed mapping.
- A verifier vulnerability blocks bundle acceptance and downstream F4 quote
  creation. Patch the same distribution, rerun every A08/A09/installed test,
  re-review, and bind new SHA evidence before resuming.

## Author Self-Review Checklist

- [x] Every F3 canonical-spec requirement maps to Tasks 1–7; F4/F5/F6/F7 work
  is explicitly deferred.
- [x] The plan preserves the old sealed package and three-wheel Stage A path;
  the new writer/verifier lives in a fourth distribution.
- [x] Digest ownership is non-circular and explicit for inner manifest,
  package, report, outer manifest, and final bundle.
- [x] The exact 39-vector selection and A04 exception are explicit; A08/A09 are
  additive and all 156 F2 statuses remain NOT_RUN.
- [x] Production schema validation is installed offline and does not import a
  test helper or fetch `$id` URLs.
- [x] Source freshness, build age, metadata age, inclusive validity, zero-size
  rejection, and identity-review human gate are unambiguous.
- [x] Archive preflight precedes extraction/body reads and covers all requested
  path/type/size/compression/encryption/ZIP64/comment/extra/CRC cases.
- [x] Each task has RED, GREEN, files, interfaces, commit, dependencies, review
  gate, rollback implications, and command-level verification.
- [x] Discovery live observations are labeled discovery-only; external outage
  cannot silently pass or use a fixture.
- [x] The prohibited-instruction scan is clean; interface names and digest
  fields are consistent across tasks.
