# Liqvera Complete Local MVP Implementation Plan

> **For agentic workers:** Execute the independent slices in isolated worktrees and integrate through one owner. The owner explicitly deferred verification and bug-fixing until after the MVP and factory update, so this plan records interfaces and implementation only.

**Goal:** Complete one locally runnable browser scenario from a BTC perpetual calculation request through an explicitly simulated unlock to report viewing and evidence download.

**Architecture:** Keep the existing fixture-only report builder as the analytics core. Add a SQLite-backed local demo flow, a Python standard-library HTTP server, and a dependency-free browser UI under a separate `/demo/*` namespace. The demo never exposes fixture output through canonical chargeable `/v1/*` states and never claims x402, wallet, testnet, settlement, or receipt completion.

**Tech Stack:** Python 3.12 standard library, SQLite, existing `mee-evidence-report`, HTML, CSS, browser JavaScript.

**Spec:** `docs/planning/LIQVERA_FACTORY_TZ.md`, narrowed by the owner's request for a theoretical local MVP before factory integration and verification.

## Global Constraints

- All tracked project artifacts and user-facing product copy are English.
- The only instrument is `hyperliquid:BTC:perpetual`; quantity is BTC and side is `BUY` or `SELL`.
- Every generated report stays `SIMULATED`, `UNVERIFIED`, non-chargeable, and `execution_authority=NONE`.
- Demo quote state is `OFFERED`, `EXPIRED`, or `UNLOCKED`; do not reuse canonical `READY`, `PAYMENT_PENDING`, or `PAID`.
- A simulated unlock must say `NO TRANSFER`; it creates no x402 header, signature, receipt, transaction hash, or chain claim.
- Keep the canonical F2 OpenAPI, schemas, vectors, and state graphs byte-for-byte unchanged.
- Persist only the SHA-256 of a 256-bit browser capability, never the capability itself.
- Store immutable artifacts under `.mvp/store/artifacts/<report_id>/` and local state at `.mvp/store/ledger.sqlite3`.
- Refuse cross-capability reads and changed-body idempotency reuse.
- Use one immutable fixture package for local demo builds and one unique output directory per report.
- Do not access wallets, RPC, facilitator, exchange mutation APIs, PostgreSQL, Docker, or external networks.
- Factory integration, graph bindings, broad tests, review, and defect repair are explicitly deferred to the next phase.

## Frozen Local Demo API

| Method | Path | Result |
| --- | --- | --- |
| `GET` | `/demo/capabilities` | Fixture/demo limitations and fixed non-chargeable price display |
| `POST` | `/demo/runs` | Build or replay a scoped idempotent simulated report and return its preview |
| `GET` | `/demo/runs/{run_id}` | Recover the scoped preview and unlock status |
| `POST` | `/demo/runs/{run_id}/confirm-simulated` | Explicitly record a no-transfer local unlock |
| `GET` | `/demo/runs/{run_id}/report` | Return the report only after simulated unlock |
| `GET` | `/demo/runs/{run_id}/evidence` | Return the ZIP only after simulated unlock |

All stateful calls require `Authorization: Bearer <64 lowercase hex characters>`. `POST /demo/runs` also requires `Idempotency-Key`. The request body is exactly `instrument_id`, `side`, `quantity_base`, and `expected_payer`; the payer is display-only in this demo and is not authenticated by a wallet.

## Task 1: Durable local demo flow

**Files:**

- Create `packages/evidence-report/migrations/001_local_demo.sql`
- Create `packages/evidence-report/src/mee_evidence_report/local_store.py`
- Create `packages/evidence-report/src/mee_evidence_report/local_flow.py`
- Modify `packages/evidence-report/src/mee_evidence_report/__init__.py`

**Produces:**

- `LocalDemoStore(database_path: Path, artifact_root: Path)`
- `LocalDemoFlow(store: LocalDemoStore, package_root: Path)`
- `create_run(capability: str, idempotency_key: str, body: dict[str, object]) -> dict[str, object]`
- `get_run(capability: str, run_id: UUID) -> dict[str, object]`
- `confirm_simulated(capability: str, run_id: UUID, action_key: str) -> dict[str, object]`
- `get_report(capability: str, run_id: UUID) -> bytes`
- `get_evidence(capability: str, run_id: UUID) -> bytes`

- [x] Create the SQLite schema with access scopes, requests, reports, demo quotes, simulated grants, and append-only demo events.
- [x] Implement capability hashing, scoped idempotency, transactional artifact metadata, and restart-safe lookups.
- [x] Build through `build_simulated_report`, publish through `write_mvp_artifact`, and read back both digests before committing the run.
- [x] Implement one idempotent simulated unlock per scoped action key without payment-shaped fields.
- [x] Commit the slice without running tests or broad verification.

## Task 2: Local HTTP adapter

**Files:**

- Create `scripts/run-mvp-web.py`

**Consumes:** Task 1 `LocalDemoStore` and `LocalDemoFlow`.

**Produces:** `ThreadingHTTPServer` on `127.0.0.1:8765` by default, serving the frozen demo API and `web/` assets.

- [x] Initialize `.mvp/store/package` once from the existing fixture capture API without accepting user paths.
- [x] Serve static files only from the repository `web/` directory with fixed content types and no directory traversal.
- [x] Implement strict JSON body size, exact field sets, capability/idempotency headers, stable JSON errors, and no-store responses.
- [x] Map demo conflicts/rejections to local HTTP statuses without claiming canonical F2 conformance.
- [x] Stream entitled ZIP bytes only from the store-selected allowlisted artifact path.
- [x] Commit the slice without running tests or broad verification.

## Task 3: Browser experience

**Files:**

- Create `web/index.html`
- Create `web/styles.css`
- Create `web/app.js`

**Consumes:** the frozen `/demo/*` API.

- [x] Build a single English page with permanent `SIMULATED`, `UNVERIFIED`, `NO TRANSFER`, fixture, and read-only analytics labels.
- [x] Collect side, exact BTC quantity, and an illustrative expected payer address.
- [x] Generate a 256-bit capability and idempotency key in the browser and retain them in `sessionStorage` with the active run ID.
- [x] Show preview, snapshot timestamp, historical/fixture limitations, and a clearly simulated confirmation step.
- [x] After confirmation, render VWAP, worst price, notional, consumed levels, limitations, and SHA-256 values; enable JSON and ZIP downloads.
- [x] Recover the active run on reload without rebuilding or reconfirming it.
- [x] Commit the slice without browser automation or verification.

## Task 4: One-command local product wiring

**Files:**

- Modify `Makefile`
- Modify `README.md`
- Modify `engineering/changes/2026-09-24-mezo-evidence/tasks.md`
- Modify `handoff.md`

- [x] Add `make mvp-web` with the four local package source roots on `PYTHONPATH`.
- [x] Document `http://127.0.0.1:8765`, the full browser flow, environment overrides, output locations, and stop behavior.
- [x] State that `make mvp` remains the CLI artifact demo and `make mvp-web` is the interactive local product demo.
- [x] Record implemented files and explicit deferrals without changing F2 acceptance status or claiming canonical F3–F7 completion.
- [x] Commit the integrated MVP state. Do not update factory/graph or run verification in this phase.

## Deferred Phase

After this implementation, update the factory and graph to recognize the new package, server, web assets, and migrations. Then run tests, schema/API compatibility checks, browser automation, concurrency/security review, and bug-fixing. Only after those pass may work proceed toward live-public capture, PostgreSQL, the TypeScript/Express gateway, official x402 SDK integration, Mezo Testnet settlement, a real receipt, offline verifier hardening, Compose, or release.
