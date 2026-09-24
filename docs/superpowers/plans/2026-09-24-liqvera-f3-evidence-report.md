# Liqvera F3 Fixture MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one fixture-only CLI that turns an existing frozen Stage A package into an explicit `SIMULATED`, non-chargeable report and a reproducible prototype ZIP.

**Architecture:** Add a small `mee-evidence-report` distribution beside the read-only analyzer. It reuses the existing frozen-package reader, reconstruction, and exact sweep kernel; it does not add capture, a verifier, or a service. The CLI emits schema-shaped canonical `report.json` and a simple deterministic ZIP containing that report plus the unchanged `sealed-input/` tree.

**Tech Stack:** Python 3.12+, stdlib (`argparse`, `json`, `hashlib`, `zipfile`), `mee-contracts==0.1.0`, `mee-readonly-analyzer==0.1.0`, pytest.

**Spec:** `docs/planning/LIQVERA_FACTORY_TZ.md` (F3 direction), narrowed by the user-approved fixture MVP scope in this plan.

## Global Constraints

- Preserve all existing F2 schemas, vectors, statuses, evidence, and closure bytes.
- Accept only an existing `mee-readonly-frozen-package/v1` directory produced by fixture tests.
- Every successful report says `snapshot_status: SIMULATED`, `source_mode: fixture`, `execution_authority: NONE`, and includes a `SIMULATED_SOURCE` reason.
- Reports and bundles are prototypes: unverified, non-chargeable, unsuitable for untrusted input, and not F3 runtime acceptance.
- Use the existing `reconstruct_books` and `sweep_depth`; do not duplicate order-book arithmetic.
- BUY walks asks; SELL walks bids. Compute impact exactly as `BUY=(vwap/best_ask-1)*10000` and `SELL=(1-vwap/best_bid)*10000` using `Fraction`.
- Render canonical JSON as UTF-8, sorted compact keys, and exactly one trailing LF; display decimals use precision 28 and `ROUND_HALF_EVEN`.
- Do not access the network, wallets, databases, environment credentials, payment code, or exchange mutation APIs.
- Refuse to overwrite an existing output path and never modify the input package.
- One implementation owner commits each green task with the handoff current.

## Review Focus

- Quantity exceeds fixture depth: return `DEPTH_INSUFFICIENT` and create no report or ZIP.
- SELL accidentally consumes asks or BUY consumes bids: exact expected fractions must expose the error.
- Equivalent runs differ because of time or ZIP metadata: fixed fixture context and fixed member metadata must yield identical bytes.
- Input contains an unexpected file kind or changes during the run: fail closed; never follow symlinks or include a partial tree.
- Output is mistaken for trusted/live/chargeable evidence: CLI help, report limitations, and handoff must state the prototype boundary.

## Delivery DAG

`Task 1 -> Task 2 -> Task 3`. Task 1 owns the pure report interface, Task 2 owns the CLI/bundle interface, and Task 3 owns boundary regression evidence. No task may claim live or verifier completion.

---

### Task 1: Exact simulated report kernel

**Files:**
- Create: `packages/evidence-report/pyproject.toml`
- Create: `packages/evidence-report/src/mee_evidence_report/__init__.py`
- Create: `packages/evidence-report/src/mee_evidence_report/canonical.py`
- Create: `packages/evidence-report/src/mee_evidence_report/report.py`
- Create: `tests/evidence_report/test_report.py`

**Interfaces:**
- Consumes: `FrozenPackageEvidenceReader`, `reconstruct_books`, `Side`, `sweep_depth`, and `ExactDecimal` from the existing Stage A packages.
- Produces: `build_simulated_report(package_root: Path, *, side: Side, quantity: ExactDecimal, context: FixtureBuildContext) -> BuiltReport` and `canonical_json_bytes(document: Mapping[str, object]) -> bytes`.

- [ ] **Step 1: Add RED tests from a real frozen fixture.**

  Create the package with `tests.readonly_analyzer.package_factory.write_sufficient_package`. Assert exact BUY and SELL requested quantity, filled quantity, notional, VWAP, worst price, consumed levels, best-price impact, and schema-shaped top-level keys. Add rejection cases for zero/negative quantity, insufficient depth, a missing/invalid Stage A package, multiple books, and a non-fixture context.

- [ ] **Step 2: Prove RED.**

  Run: `pytest -q tests/evidence_report/test_report.py`

  Expected: collection or import failure because `mee_evidence_report` does not exist.

- [ ] **Step 3: Implement the minimal pure builder.**

  Define frozen `FixtureBuildContext` and `BuiltReport` dataclasses. Require caller-supplied deterministic IDs/timestamps only in the fixture context. Read and reconstruct once, require exactly one approved Hyperliquid BTC book, call the existing sweep kernel, compute impact with `Fraction`, and render rational values as reduced `{numerator, denominator}` objects. Copy identity/source/reproducibility facts from the frozen package; do not invent live identity or payment facts.

  Fill all current `report.schema.json` top-level sections, with `quality.snapshot_status="SIMULATED"`, `quality.reason_codes=["SIMULATED_SOURCE"]`, an explicit limitation `"Fixture-only prototype; not independently verified or chargeable."`, and all boundary booleans false. Use the repository test schema helper only in tests; runtime code must not ship a schema engine.

- [ ] **Step 4: Make canonical output deterministic.**

  Reject floats, non-string keys, and non-UTF-8/NFC strings in the report model. Serialize with `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)` plus one LF. Format display values from exact fractions at decimal precision 28 with `ROUND_HALF_EVEN`; precision is not a CLI option.

- [ ] **Step 5: Prove GREEN and commit.**

  Run: `pytest -q tests/evidence_report/test_report.py tests/readonly_analyzer/test_vwap.py tests/readonly_analyzer/test_frozen_package.py`

  Expected: PASS, including exact BUY/SELL and insufficient-depth cases.

  Commit: `feat: add simulated evidence report kernel`

---

### Task 2: Fixture CLI and deterministic prototype ZIP

**Files:**
- Create: `packages/evidence-report/src/mee_evidence_report/bundle.py`
- Create: `packages/evidence-report/src/mee_evidence_report/cli.py`
- Create: `packages/evidence-report/src/mee_evidence_report/__main__.py`
- Modify: `packages/evidence-report/pyproject.toml`
- Create: `tests/evidence_report/test_cli_bundle.py`

**Interfaces:**
- Consumes: Task 1 `build_simulated_report` and `canonical_json_bytes`.
- Produces: `build_prototype_bundle(package_root: Path, report_bytes: bytes) -> bytes` and console entry point `mee-evidence-report = mee_evidence_report.cli:main`.

- [ ] **Step 1: Add RED CLI/bundle tests.**

  Invoke `main()` with `--package`, `--side {BUY,SELL}`, `--quantity`, `--report-id`, `--created-at`, and `--output`. Assert exit 0, no stdout ambiguity, and a new ZIP containing `report.json` plus every declared regular frozen-package member under `sealed-input/`. Assert sorted names, `ZIP_STORED`, DOS timestamp `1980-01-01T00:00:00`, fixed regular-file mode, empty archive comment, and identical archive SHA-256 across two output paths.

  Add exit-2 cases for a relative/non-directory package, symlink member, existing output, invalid quantity/side/timestamp/UUID, insufficient depth, and any option suggesting `live`, `valid`, `verified`, or `chargeable` output. Assert failures create no output and leave input bytes unchanged.

- [ ] **Step 2: Prove RED.**

  Run: `pytest -q tests/evidence_report/test_cli_bundle.py`

  Expected: import failure for `mee_evidence_report.bundle` and `mee_evidence_report.cli`.

- [ ] **Step 3: Implement deterministic assembly.**

  Walk the already validated package without following symlinks; require regular files only and compare the relative set to the frozen manifest. Read each member once, prefix it with `sealed-input/`, add canonical `report.json`, sort all archive names, and write `ZIP_STORED` entries with fixed timestamp/mode/system metadata. This is deterministic packaging, not hardened hostile-archive verification.

- [ ] **Step 4: Implement the explicit fixture CLI.**

  Parse only the six fixed inputs above. Resolve the package/output paths, require the package to exist and output not to exist, build fully in memory, then create the output with exclusive mode. Print one English success line containing `SIMULATED`, `PROTOTYPE`, `UNVERIFIED`, `NON-CHARGEABLE`, and the archive SHA-256. Errors go to stderr without tracebacks and return 2.

- [ ] **Step 5: Prove GREEN and commit.**

  Run: `pytest -q tests/evidence_report/test_cli_bundle.py tests/evidence_report/test_report.py`

  Expected: PASS; two identical fixture invocations produce byte-identical archives.

  Commit: `feat: add fixture evidence bundle CLI`

---

### Task 3: MVP boundary verification and handoff

**Files:**
- Create: `tests/evidence_report/test_mvp_boundary.py`
- Modify: `engineering/changes/2026-09-24-mezo-evidence/tasks.md`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: the complete Task 2 CLI and archive bytes.
- Produces: focused regression evidence and an honest next-action record; no acceptance receipt.

- [ ] **Step 1: Add boundary regression tests.**

  Assert production modules contain no imports for HTTP clients, sockets, wallets, databases, gateway/payment packages, or test helpers. Assert the emitted report contains no claim of live capture, verification, execution, settlement, fees, funding, PnL, or payment eligibility. Assert input file hashes are unchanged and the bundle can be rebuilt from the same fixture/context outside the first output directory.

- [ ] **Step 2: Run the focused MVP suite.**

  Run: `pytest -q tests/evidence_report tests/readonly_analyzer/test_vwap.py tests/readonly_analyzer/test_frozen_package.py tests/readonly_analyzer/test_reconstruction_hyperliquid.py`

  Expected: PASS with no network or external service.

- [ ] **Step 3: Run Stage A regressions and packaging smoke test.**

  Run: `pytest -q tests/contracts tests/readonly_analyzer`

  Run: `python -m build --wheel packages/evidence-report`

  Expected: PASS and one `mee_evidence_report-0.1.0-py3-none-any.whl`. Do not add it to the existing Stage A three-wheel build invariant.

- [ ] **Step 4: Record the exact result.**

  Update `tasks.md` and `handoff.md` with commands, counts, commit/tree identity, remaining blockers, and the next action. State that the ZIP is a fixture prototype without a hardened verifier and that no F2 vector status or acceptance matrix changed.

- [ ] **Step 5: Inspect, review, and commit.**

  Run: `git diff --check && git status --short`

  Have an independent reviewer inspect the actual diff for arithmetic reuse, deterministic bytes, and overclaiming. Fix findings through the same write owner, rerun the affected checks, then commit: `docs: record F3 fixture MVP evidence`.

## Explicit Deferrals

- Hardened offline verifier, hostile-ZIP preflight, trust anchors, signed provenance, and production runtime schema validation.
- Live Hyperliquid capture, freshness/timing policy, source identity approval, and human review artifacts.
- A08/A09 tamper/replay obligations, the 39 F3 runtime vectors, runtime-results manifests, and acceptance claims.
- HTTP gateway, capability authorization, quote/payment/x402 state, database/ledger, UI, deployment, and Compose.
- Factory integration, architecture-graph policy expansion, product release, tag, push, and GitHub release.

Those deferrals are blockers, not implied work. Completing this MVP does not close canonical F3, satisfy the F4 dependency, authorize payment, or make a bundle safe to verify from an untrusted party.
