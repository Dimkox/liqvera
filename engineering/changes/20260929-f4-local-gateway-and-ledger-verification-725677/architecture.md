# Architecture — F4 local gateway and ledger verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

The gateway fails TypeScript compilation because the NodeNext view of
`ajv-formats` is not directly callable and `loadConfig` widens `sourceMode` to
`string`. It has no executable gateway test command. The report service
correctly returns HTTP 200 with `deleted:false` when an exact report directory
is already absent, but `HttpReportService.cleanup()` accepts only `true`.
Consequently, loss of the first successful delete response leaves the ledger
permanently `AVAILABLE` although storage is gone.

## Proposed behavior

Add explicit compile-time types/export normalization and a gateway-owned test
harness. Parse the private cleanup response as a closed semantic assertion:
HTTP 200, matching UUID, and a boolean `deleted` means the desired exact-report
absence state is authoritative, regardless of whether removal happened now or
on an earlier attempt. Every other response remains ambiguous and cannot
advance the ledger. Prove the behavior with loopback HTTP and a real disposable
PostgreSQL ledger; do not change the database schema.

## Components and boundaries

```text
Node test process
  ├─ loopback-only scripted HTTP server -> HttpReportService
  └─ Gateway / Ledger / retention worker -> disposable PostgreSQL
       ├─ in-process ReportService fake
       ├─ temporary immutable-artifact fake
       └─ fail-closed PaymentPort fake (settle count must remain zero)
```

PostgreSQL is the only process boundary needed for ledger semantics. The test
must generate and validate its own target identity and must never inherit a
database URL. No report, payment, RPC, wallet, chain, exchange, deployment, or
shared service may be contacted.

## Data flow

1. The migrator applies the immutable migration and records its checksum.
2. Concurrent `createRequest` transactions use the existing
   `(scope_hash,idempotency_key)` uniqueness boundary and row lock.
3. Retention locks only eligible expired/unpaid quote and artifact rows.
4. Cleanup calls the authenticated internal adapter with the exact report ID.
5. Only an authoritative matching boolean response changes storage state to
   `DELETED` and appends the removal audit event; ledger identities remain.
6. Missing/corrupt paid artifacts enter `RECOVERY`; no fresh build or payment
   action is permitted.

## API and event contracts

- Frozen public contract: `schemas/mezo-evidence/v1/openapi.json` and linked
  resource/error schemas; no public payload change.
- Private cleanup contract: `DELETE /internal/v1/reports/{report_id}` returns
  HTTP 200 `{report_id, deleted:boolean}`. Both boolean values confirm absence;
  non-200 and malformed/mismatched responses do not.
- Ledger audit fact: `UNPAID_ARTIFACT_REMOVED` is appended only after confirmed
  absence and at most once for the selected ledger transition.
- Idempotency identity and capability scope are unchanged.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: canonical specification §§9–15 and ADR-0002.
- Applicable canonical example IDs/versions:
- Open or overdue debt IDs:
- Expected governance handoff or receipt impact: verification plus independent
  code, test, and data review receipts are required for the final fingerprint.

## Decisions

- Repair the cleanup semantic at the gateway adapter, not the filesystem or
  migration, because the service already documents an idempotent absence
  response.
- Use Node's built-in test runner and existing TypeScript dependency; do not
  add a test framework or alter the lockfile.
- Preserve `001_ledger.sql` and `vectors.json` byte-for-byte. A discovered
  schema defect would stop this tranche rather than rewrite applied history.
- Keep remote cleanup inside the existing row-lock transaction for this
  bounded repair. A two-phase cleanup state requires a future migration.

## Risks and mitigations

- A permissive cleanup parser could fabricate deletion: require exact ID,
  boolean type, HTTP 200, bounded JSON, and authenticated adapter readiness.
- Tests could hit shared state: generate a unique disposable container/database,
  bind loopback only, pass its URL explicitly, and prove removal afterward.
- A fake could accidentally enable payment: use a fail-closed port and assert
  zero `verify`, `settle`, `confirm`, and `revalidate` calls.
- Existing retention holds locks during HTTP I/O: retain the two-second timeout
  and batch-of-ten bounds; record as residual debt rather than refactor schema.
