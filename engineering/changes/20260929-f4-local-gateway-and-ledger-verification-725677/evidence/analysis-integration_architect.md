# F4 gateway/report-service integration analysis

Route: `725677143509`
Role: `integration_architect` (read-only analysis)
Scope: local gateway ↔ report-service adapter, timeout/retry/idempotency,
artifact-loss handling, and lost cleanup-response recovery. No external service
or persistent shared environment was used.

## Executive finding

The boundary is intentionally fail-closed, but it has one deterministic
recovery defect: the report service documents and implements an already-absent
artifact as a successful idempotent DELETE response with `deleted:false`, while
the gateway accepts only `deleted:true`. If the first successful delete response
is lost, every retry confirms absence but the ledger remains `AVAILABLE`
forever. This should be repaired in the adapter and covered by a local contract
test before broader F4 verification.

Artifact-loss recovery is not implemented by design. A failed immutable
readback changes the artifact to `RECOVERY`, globally blocks new sales, and the
scheduled recovery adapter always returns false. That is a safe incident state,
not a working recovery path. F4 tests should characterize it without pretending
that a fresh snapshot can restore the old digest.

## Boundary inventory

- `HttpReportService.build` sends one bounded POST with a caller abort signal
  and a 15-second adapter timeout. There is no adapter retry.
- The Python service has its own 15-second build budget and returns an existing
  immutable artifact for the same report ID and identical request.
- The build worker leases at most four requests for 20 seconds and calls the
  service once. Failures terminally mark the request `REJECTED` or
  `BUILD_FAILED`; lease expiry also terminally marks it `BUILD_FAILED`.
- `HttpReportService.cleanup` sends one bounded DELETE with a 2-second timeout.
  Retention holds row locks while making this call, and updates the ledger only
  after adapter success.
- The Python DELETE is filesystem-idempotent: first success normally returns
  `deleted:true`; a retry after deletion returns `deleted:false`.
- `HttpReportService.recover` is an explicit stub returning false. It correctly
  refuses to create replacement evidence from a new market snapshot.

## Findings

### F4-INT-001 — lost cleanup response cannot converge (must fix)

Evidence:

- `packages/evidence-report/.../service.py:247-248` returns HTTP 200 for both
  deletion outcomes and reports whether files existed.
- `services/evidence-report/README.md:49-51` explicitly says `deleted:false`
  is the recovery result after a lost response.
- `apps/mezo-gateway/src/adapters/report-service.ts:34-39` returns true only
  when `body.deleted === true`.
- `apps/mezo-gateway/src/workers/retention.ts:15-17` advances the ledger to
  `DELETED` only when the adapter returns true.

Failure sequence:

1. Ledger row is `AVAILABLE`, quote is safely eligible for unpaid cleanup.
2. Report service removes the exact artifact and emits `deleted:true`.
3. The response is lost or the client aborts before consuming it; the database
   transaction rolls back and the ledger still says `AVAILABLE`.
4. Every later DELETE returns HTTP 200 with `deleted:false`.
5. The adapter returns false forever, so the ledger never converges to
   `DELETED` and the audit event is never recorded.

Bounded repair: treat a structurally exact HTTP-200 response with matching
`report_id` and a boolean `deleted` field as confirmed absence. Both boolean
values authorize the same ledger transition. Do not accept missing/non-boolean
values, mismatched IDs, non-2xx responses, timeouts, or parse failures. Update
the gateway README, whose current statement that only `deleted:true` is
expected conflicts with the service contract.

### F4-INT-002 — artifact recovery is a deliberate permanent incident state

On a paid delivery read failure, `Gateway.read` marks `storage_state='RECOVERY'`,
appends `ARTIFACT_INTEGRITY_FAILURE`, and returns an integrity error. Readiness
and sales health then fail globally. The retention worker repeatedly calls
`recover`, but the HTTP adapter always returns false.

This is safe because rebuilding from current market data would violate the
committed digest. It is incomplete operationally: there is no sealed-input
recovery API, retry schedule/backoff metadata, recovery-attempt audit event, or
operator terminal state. For this tranche, tests should prove:

- a missing/tampered report or bundle moves the ledger to `RECOVERY`;
- it blocks new sales and never causes settlement or fresh report construction;
- a false recovery result never changes the row to `AVAILABLE`;
- even if a test double claims recovery success, both immutable files must pass
  digest/size readback before `AVAILABLE` is restored;
- failed post-recovery readback leaves the row `RECOVERY`.

A real recovery endpoint is a separate design: it must consume retained sealed
input, reproduce the exact stored report and bundle hashes, publish atomically,
and never capture fresh data. Do not add a migration merely to make this F4
verification green.

### F4-INT-003 — equal client/server build deadlines create an orphan window

The Python service enforces a 15-second budget while both the build worker abort
signal and `boundedJson` timeout are also 15 seconds. A publication completed at
the service deadline can therefore be committed on disk while the gateway loses
the response and terminally marks the request `BUILD_FAILED`. The existing
same-ID service behavior could reconcile such a loss, but the worker does not
retry a terminal request.

Characterize this with a local delayed test double now. The safe bounded design
is to give the server a strictly smaller work deadline than the caller/lease,
leaving a response margin, and to reconcile uncertain build outcomes using the
same report ID and canonical request. Blind retry with a new report ID is not
equivalent and would orphan evidence. Any retry must remain bounded and must not
turn `REPORT_ALREADY_EXISTS` for a changed request into success.

### F4-INT-004 — report-service conflict/retry semantics are erased

The service can return 409 `BUILD_IN_PROGRESS` (`retryable:true`) or
`REPORT_ALREADY_EXISTS` (`retryable:false`). `HttpReportService.build` does not
accept 409, so `boundedJson` converts both to generic `SOURCE_UNAVAILABLE`.
For accepted 422/503 bodies, recognized codes are always reconstructed with HTTP
status 422, losing the service status and `retryable` bit.

This does not authorize automatic retry. It does prevent the worker from
distinguishing transient same-ID contention from immutable identity conflict.
Contract tests should freeze expected mapping before implementation. A minimal
repair can keep the public reason vocabulary while preserving an internal
retryability classification; do not expose internal service codes through the
public API unless the frozen contract is versioned.

### F4-INT-005 — cleanup is remote I/O inside a ledger transaction

Retention correctly locks quote and artifact rows before the destructive call,
which prevents a concurrent payment transition from racing the eligibility
decision. The tradeoff is a remote call of up to two seconds while locks and a
five-second transaction statement timeout are active. Ten rows are processed
serially, so a batch can hold its transaction substantially longer than five
seconds (the statement timeout does not bound time between SQL statements).

Keep the safety serialization for this tranche. Tests should cover concurrent
retention workers (`SKIP LOCKED`), no cleanup for any entitlement or non-rejected
attempt, and one ledger/audit transition after confirmed absence. A future
two-phase cleanup protocol would need an explicit durable cleanup state and a
forward migration; moving the HTTP call outside the lock without such a state
would reintroduce the payment/deletion race.

## Local-only test architecture

Use two layers, both disposable and loopback-only:

1. **Adapter contract tests without PostgreSQL.** Start a Node loopback HTTP
   server on an ephemeral port, instantiate `HttpReportService`, and script
   exact status/body/delay/disconnect outcomes. Assert method, fixed path,
   bearer header, bounded request body, abort behavior, response size limit,
   strict report ID/hash projection, and cleanup convergence for both
   `deleted:true` and `deleted:false`. Reject malformed JSON, duplicate/missing
   fields, non-boolean `deleted`, mismatched IDs, 409/503, oversized bodies, and
   delayed responses.

2. **Ledger/worker contract tests with ephemeral loopback PostgreSQL.** Apply
   the tracked `001_ledger.sql` to a fresh database; use in-process fakes for
   `ReportService`, `ArtifactStore`, payment, and contracts. Do not contact the
   Python service, facilitator, wallet, RPC, exchange, or shared database.
   Cover:

   - 20 concurrent `createRequest` calls with the same scope/key/body produce
     one request/report identity and one rate-budget insertion;
   - same key with a different normalized body returns
     `IDEMPOTENCY_CONFLICT` and creates no second artifact/quote;
   - build publication is exactly once under competing workers;
   - lost build response reuses the same report ID in the characterization
     double and never publishes changed metadata;
   - cleanup never runs for READY, PAYMENT_PENDING, PAYMENT_UNCERTAIN, PAID, or
     MANUAL_REVIEW, for any non-rejected attempt, or with an entitlement;
   - cleanup `true` and confirmed-absent `false` each yield one `DELETED` row
     and one `UNPAID_ARTIFACT_REMOVED` event; a timeout/error yields neither;
   - two retention workers cannot delete/audit the same row twice;
   - artifact read failure yields durable `RECOVERY`, fails readiness, and does
     not settle, rebuild, or restore availability without exact readback.

If the repository does not yet have a TypeScript test target, add a separate
test tsconfig/output directory or a lightweight Node test runner configuration;
do not place tests under production `src` merely to make `tsc` discover them.
The existing package lock should remain authoritative and no new framework is
required: Node's built-in `node:test` plus local fakes is sufficient.

## Recommended implementation order

1. Add the failing adapter test for lost cleanup response.
2. Change cleanup success interpretation to matching ID + boolean `deleted`.
3. Add strict malformed/error/timeout adapter cases.
4. Add ephemeral-ledger idempotency and retention eligibility/race tests.
5. Add artifact-loss characterization; retain the fail-closed recovery stub.
6. Characterize the build deadline/response-loss window. Only then decide
   whether bounded same-ID build reconciliation belongs in this tranche.

## Non-goals and safety constraints

- No live capture, facilitator, wallet, chain, exchange, or deployment action.
- No payment settlement, even with mocks that accidentally bind real URLs.
- No shared database and no reuse of developer data.
- No deletion outside the report service's exact UUID-owned artifact path.
- No replacement of missing evidence with a fresh snapshot.
- No edit of applied migration `001_ledger.sql`; any later state-machine change
  requires a forward migration and a separately reviewed data decision.
