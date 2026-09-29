# F4 contract and documentation analysis

Role: route-selected `docs_researcher` (read-only analysis except this report)
Route: `725677143509`
Candidate HEAD inspected: `c30b0ffbda6cbae37b9dec16da2dec1346b0248b`

## Sources inspected

- Canonical product contract: `docs/planning/LIQVERA_FACTORY_TZ.md`, especially sections 9–15 and acceptance cases A10, A15, A16, A21, A22.
- Frozen HTTP/state/vector contracts: `schemas/mezo-evidence/v1/openapi.json`, `states.json`, `resources.schema.json`, and `vectors.json`.
- Contract characterization: `tests/contracts/test_mezo_openapi.py`, `test_mezo_vectors.py`, `test_mezo_states.py`, and `tests/conformance/test_repository_boundary.py`.
- Runtime-facing claims and recovery guidance: root `README.md`, `apps/mezo-gateway/README.md`, `services/evidence-report/README.md`, and `docs/runbooks/{artifact-recovery,payment-recovery,startup-shutdown,backup-restore}.md`.
- Relevant implementation used only to compare the documented contract: gateway routes, report-service adapter, retention worker, package scripts, and migration inventory.

## Contract obligations for the bounded F4 tranche

The safe local F4 verification tranche must demonstrate all of the following without enabling settlement or contacting an external service:

1. The exact gateway lock installs, TypeScript typechecks, and the distributable build contains the frozen schemas and migration resources.
2. The public routes and response codes remain the OpenAPI surface: health/readiness/capabilities; quote creation and status; protected report and evidence reads. Request correlation, closed bodies, exact UUID/idempotency syntax, 16 KiB request limits, and stable error resources remain enforced.
3. Capability isolation is fail-closed: missing capability is 401; a sibling scope, guessed ID, report hash, or public transaction hash cannot disclose resource existence or paid bytes.
4. Quote creation is durable and scoped by `(scope_hash, idempotency_key)`. Same normalized body returns the same logical object; a changed body returns 409; different scopes do not alias. At least 20 simultaneous repeats produce one logical request/build/quote.
5. A quote becomes chargeable only after immutable report and bundle bytes are read back and their digests and schemas verify. Fixture reports remain non-chargeable and payment readiness remains false.
6. Missing bytes before payment produce no chargeable quote. Missing/corrupt bytes after entitlement enter recovery/incident handling, withhold paid bytes, close new sales as required, and never demand another payment.
7. Unpaid retention waits at least 15 minutes after expiry, excludes every non-rejected payment attempt and entitlement, and preserves ledger/scope/dedup rows. Cleanup is performed only through the authenticated report service while the ledger decision is locked.
8. A cleanup retry after a lost successful response is idempotently terminal: both report-service success forms, `deleted:true` and already-absent `deleted:false`, allow the gateway to mark the artifact `DELETED`. Conflicts and storage failures must not do so.
9. The original migration applies to a disposable PostgreSQL instance and its database constraints/immutability triggers are exercised. No shared database, network payment, wallet, chain, exchange, deployment, or release activity belongs to this tranche.

The frozen vector catalog contains **88 F4-owned vectors**, all currently `NOT_RUN`: 53 invalid-request, 8 idempotency, 25 access, and 2 artifact vectors. Static Python tests validate their shape and modeled semantics, but do not establish that the TypeScript gateway produces those outcomes.

## Exact gaps and defects

### P0 — lost cleanup-response recovery contradicts the documented service contract

`services/evidence-report/README.md` defines both of these as HTTP 200 cleanup success:

- first successful deletion: `{ "report_id": "…", "deleted": true }`;
- retry after the response was lost and the directory is already absent: `{ "report_id": "…", "deleted": false }`.

It explicitly says the second form supports recovery after a lost response. However, `HttpReportService.cleanup()` returns true only for `body.deleted === true`. `retainAndRecover()` advances the ledger artifact to `DELETED` only when that boolean is true. Therefore a deletion that completed before its HTTP response was lost is retried forever with the ledger still reporting `AVAILABLE`. This is a real cross-component contract defect, not a documentation preference. Characterize the two success forms and non-success/error forms before repairing the adapter.

`apps/mezo-gateway/README.md` currently repeats the narrower, incorrect claim that cleanup expects only `deleted:true`; it must be corrected with the implementation so both sides describe one recovery contract.

### P0 — no executable gateway/API/PostgreSQL test surface

`apps/mezo-gateway/package.json` has only `build`, `typecheck`, `start`, and `migrate`; it has no test script or test dependency. Repository tests reference the migration hash and statically inspect the canonical schemas/vectors, but no test imports or runs `Gateway`, `createApp`, `Ledger`, `retainAndRecover`, or the HTTP report adapter. Consequently the following current claims are unproved at runtime:

- route/OpenAPI agreement and error/status/media/header behavior;
- capability isolation and no paid-body leakage;
- canonical request normalization and idempotency conflict behavior;
- 20-way database concurrency;
- migration constraints and immutable audit behavior;
- pre-payment artifact readback and post-payment integrity recovery;
- cleanup selection guards and lost-response recovery.

The minimum useful harness is a gateway-owned TypeScript test command plus disposable PostgreSQL and local fake report/artifact adapters. It should not mutate the frozen vector catalog merely to record a run; test output/change evidence should carry runtime results.

### P1 — current README claims must be refreshed after verification

The root README and gateway README deliberately label F4 as `IMPLEMENTED_UNVERIFIED`, state that gateway targets were not executed, and say all 156 vectors remain `NOT_RUN`. Those are honest baseline claims for F4 and must remain until evidence exists. Once this tranche passes, update only the claims actually established: local exact-lock build/typecheck and fixture/disposable-PostgreSQL F4 cases. Do not convert local fake-adapter results into F5 settlement, live Mezo, deployment, release, or vector-file acceptance claims.

The root README also groups F3 with F4–F7 as unverified even though the immediately preceding branch work produced F3 evidence. The final README refresh should distinguish verified F3 from locally verified F4 and still-blocked F5–F7; this does not authorize altering F2 vector `runtime_status` values.

### P1 — acceptance ownership must not drift into F5

The canonical stage table gives F4 gateway/ledger/capability/quote and protected delivery without real settlement; F5 owns canonical authorization identity, settlement, on-chain finality, entitlement, and reconciliation. Some F4-owned access vectors model paid/uncertain/manual-review states, but local F4 tests may seed those states only to prove access and artifact guards. They must not claim SDK correctness, canonical authorization identity, a confirmed Transfer, or successful live reconciliation.

## Compatibility and change constraints

- Do **not** edit `apps/mezo-gateway/migrations/001_ledger.sql`: its SHA-256 is pinned as `bc127e55c876961112acd35c3abdfac01827769d6156ddba2f42856d070c75b3b`. If a real schema repair is unavoidable, use a forward-only `002_*` migration and obtain the route-required data review; the observed cleanup defect requires no schema change.
- Do **not** rewrite `schemas/mezo-evidence/v1/vectors.json`: its SHA-256 is pinned as `606a4a2a406c71456aa0ade984f613c10bdef46a6ac020a953b8d3b6386717cc`. Preserve all 88 F4 obligations and their ownership.
- Keep `schemas/mezo-evidence/v1/openapi.json`, response/resource schemas, and `states.json` as the machine-readable contract. A runtime repair must conform to them; silently changing the contract to match implementation is not acceptable.
- Preserve inherited `mee-*` package and API identifiers, `/v1/*` paths, exact error vocabulary, and the official x402 2.16.0 dependency boundary.
- Preserve fail-closed blockers for payment identity/finality and fixture chargeability. `PAY_TO` alone must never make payment ready; no test helper or environment switch may bypass these blockers.
- Preserve the gateway as sole PostgreSQL writer and read-only artifact consumer; the report service remains sole artifact writer/deleter. Never add direct gateway filesystem deletion as a shortcut.
- Preserve capability hashing/scope binding, append-only audit records, ledger/dedup retention, and artifact identity. Rollback after durable state is a forward repair, not migration rollback or database replacement.
- Keep external I/O absent from this verification: fake report/payment/RPC boundaries and loopback-only HTTP are sufficient; no facilitator, chain, wallet, exchange, shared database, Compose deployment, or release is evidence for this tranche.

## Recommended acceptance mapping

| Priority | Test group | Canonical obligation |
| --- | --- | --- |
| P0 | exact-lock typecheck/build and copied-resource checks | F4 exit artifact; frozen contracts present |
| P0 | disposable migration plus constraints/triggers | §12 ledger authority and uniqueness/immutability |
| P0 | API invalid-input/capability/status tests | A16, A21 and 53 invalid-request vectors |
| P0 | 20-way same-key and changed-body races | A15, A16 and 8 idempotency vectors |
| P0 | artifact readback/tamper/loss tests | A22 and 2 artifact vectors |
| P0 | cleanup first-call, lost-response retry, conflict/error tests | documented idempotent retention boundary |
| P1 | seeded unpaid/paid/uncertain/manual-review read guards | A10, A14, A24 access behavior only; no F5 claim |
| P1 | README/gateway README refresh bound to actual evidence | no overclaiming beyond local F4 verification |

## Conclusion

The contract is sufficiently specific to implement the bounded local verification without new product decisions. The first repair target is the `deleted:false` lost-response path. The larger evidence gap is the absence of an executable gateway test harness: current static schema/vector tests are valuable compatibility guards but cannot verify the TypeScript/Express/PostgreSQL boundary they specify.
