# Independent data review R2 — live paywall

Status: **PASS**
Review base: `e3df6833e8916d01f55028e63d4db1632a805a75`
Reviewed head: `a45f0c01587584f94467b557962b74d9a894a65a`
Prior finding: `DATA-001` in `data-review-paywall-live.md`

## Verdict

`DATA-001` is resolved. A contender that loses the one-shot grant race can no
longer remain stranded as `VERIFIED/PAYMENT_PENDING`, and a grant already known
to be consumed is rejected before payment requirements or external
authorization verification. Migrations 001–005 remain sufficient and unchanged.

## DATA-001 closure evidence

- `Gateway.read()` now calls the database-backed `currentBlockers()` both at
  entry to the `READY` payment path and immediately before `verify()`. A consumed
  grant therefore prevents 402 requirements and external verification. The
  focused state-machine regression asserts readiness 503,
  `EXTERNAL_GRANT_REQUIRED`, zero `requirements()` calls, and zero `verify()`
  calls.
- The database race remains closed by the authoritative insert into
  `live_grant_consumptions`, not by the advisory readiness read. Quote and
  attempt rows are locked, and the unique grant insert occurs in the same
  transaction as the state transition.
- `markSubmitting()` now returns a typed result. If the unique insert loses,
  the same transaction changes the attempt from `VERIFIED` to `REJECTED`,
  reopens the quote from `PAYMENT_PENDING` to `READY`, and appends a
  `GRANT_ALREADY_CONSUMED` audit event. The gateway returns
  `PAYMENT_NOT_READY`; it does not call `settle()` and does not misclassify the
  outcome as quote expiry.
- A crash cannot expose a partial loser transition: grant insert, attempt
  rejection, quote reopening, and audit insertion share the existing Ledger
  transaction. Rollback restores the pre-call state and cannot leave a durable
  partial combination.
- The remaining race between the second advisory blocker read and
  `markSubmitting()` is therefore safe: exactly one transaction may consume the
  grant, while every loser terminates as `REJECTED` with a reusable `READY`
  quote. Reconciliation correctly remains limited to possible post-submit
  outcomes (`SUBMITTING` and `UNKNOWN`).

## Schema, migration, and finality assessment

- No migration file changed between the review base and reviewed head. The
  current SHA-256 values still match the pinned migration policy:
  `001=bc127e55...`, `002=981f4821...`, `003=bbedff61...`,
  `004=96bba00d...`, `005=e99e5cff...`.
- Migration 003 already supplies the required unique grant digest, grant ID,
  and payment-attempt bindings plus append-only enforcement. No additional
  column, index, or backfill is needed for the repaired state transition.
- Migrations 004–005 and the existing receipt transaction still preserve
  provenance and enforce at least twelve confirmations before durable receipt
  insertion. The repair does not weaken `UNKNOWN` confirm-only recovery or add
  a settlement retry path.
- The dynamic consumption query is a primary-key lookup on `grant_digest`; it
  introduces no material scan, lock, backfill, or downtime risk.

## Verification run

At the exact reviewed head:

```text
npm test --prefix apps/mezo-gateway
```

Result: **45 passed, 0 failed, 6 skipped**. The six skips are the explicitly
disposable PostgreSQL integration cases because no approved disposable database
URL was configured. Build and TypeScript compilation passed as part of the
command.

```text
.venv/bin/python -m pytest -q tests/contracts/test_live_grant_consumption.py
```

Result: **2 passed**.

## Residual note

The exact two-precreated-quote loser transition is established by transaction
inspection rather than a running PostgreSQL regression in this environment.
The existing PostgreSQL concurrency/rollback test is present but was skipped
without an approved disposable target. This is a verification-environment
limitation, not a correctness blocker for this review; it should be exercised
on the next authorized disposable PostgreSQL run.

## Decision

Data review passes for head `a45f0c01587584f94467b557962b74d9a894a65a`.
The report may be recorded as `data_review=pass` only while its repository and
spec bindings remain current.
