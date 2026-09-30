# Independent data review — live paywall

Status: **FAIL**
Review base: `e3df6833e8916d01f55028e63d4db1632a805a75`
Reviewed head: `c7422080cc8ba827ca92a78600953d62161855bb`
Scope: migrations 001–005; live-grant readiness and consumption; transactions,
locks, idempotency, `UNKNOWN` recovery, and receipt finality.

## Blocking finding

### DATA-001 — a losing one-shot-grant contender is stranded outside recovery

Severity: **HIGH** (blocks data-review approval)

`Gateway.read()` checks only the static `blockers()` before accepting payment
authorization (`apps/mezo-gateway/src/application/gateway.ts:82-103`). It does
not use the new database-backed `currentBlockers()` check used by readiness,
capabilities, and request creation. Therefore two quotes created while the grant
is unspent can both enter payment processing. The first `markSubmitting()` call
atomically consumes the grant; the second receives `false` from
`consumeLiveGrant()` (`apps/mezo-gateway/src/adapters/postgres.ts:117-132`).

That `false` is reported as `QUOTE_EXPIRED` even when the quote is not expired,
and the preceding `beginAttempt()` transaction has already persisted the losing
attempt as `VERIFIED` and its quote as `PAYMENT_PENDING`. Reconciliation leases
only `SUBMITTING` and `UNKNOWN`, so the losing row has no convergence path. This
is fail-closed for external settlement, but it is not a valid durable terminal
or recoverable state and the client receives a materially false classification.

Required repair:

- apply the dynamic consumption check at the payment boundary as well as at
  readiness/create; and
- make the consume result typed (consumed, expired, already consumed, invalid
  state/identity), atomically transition a losing attempt/quote to a truthful
  recoverable or terminal state, and return the corresponding public error;
- add a concurrency regression covering two already-created quotes using the
  same grant, asserting one `SUBMITTING` maximum, zero settlement for the loser,
  and no stranded `VERIFIED/PAYMENT_PENDING` rows after restart/reconciliation.

## Migration and invariant assessment

- No schema change is required for the proposed live-grant file composition.
  Existing migration 003 provides unique `grant_digest`, unique `grant_id`, and
  unique `payment_attempt_id`; its append-only trigger preserves the budget
  evidence. Migrations 004–005 retain receipt provenance and the `>=12`
  confirmation constraint. Thus 001–005 are sufficient **once DATA-001 is
  repaired in application transaction/state handling**.
- Grant consumption and `VERIFIED -> SUBMITTING` occur in one database
  transaction under quote and attempt row locks. A rollback removes both the
  consumption row and transition; `ON CONFLICT DO NOTHING` prevents duplicate
  consumption across processes/restarts.
- Post-submit behavior remains confirmation-only: external settlement follows
  the committed `SUBMITTING` boundary, exceptions persist `UNKNOWN`, and the
  reconciliation worker leases only `SUBMITTING`/`UNKNOWN` with `FOR UPDATE SKIP
  LOCKED`. No reviewed path retries `settle()`.
- Receipt publication remains one transaction covering chain event, receipt,
  entitlement, attempt `CONFIRMED`, quote `PAID`, and audit event. Database
  uniqueness plus append-only triggers preserve final receipt identity; the
  migration-005 constraint enforces at least twelve recorded confirmations.
- The new readiness/capabilities lookup correctly reports an already consumed
  configured grant as `EXTERNAL_GRANT_REQUIRED`. It is an indexed primary-key
  lookup and adds no material lock or query-plan risk. Its read is advisory only;
  correctness continues to depend on the atomic insert at `markSubmitting()`.

## Verification evidence

Command run at the reviewed head:

```text
npm test --prefix apps/mezo-gateway -- --test-name-pattern='live grant|twenty pools|expiry becomes'
```

Result: 42 passed, 0 failed, 6 skipped. The skipped cases include all disposable
PostgreSQL tests because no explicitly disposable local PostgreSQL URL was
configured. The passing fake-store test proves one-shot uniqueness, and the
existing PostgreSQL test source covers concurrent pools, restart, rollback, and
append-only consumption, but neither test exercises the cross-quote losing
state described in DATA-001.

## Decision

Do not record a passing `data_review` receipt for this tree. Re-review the repair
on a new exact head and run the new cross-quote concurrency regression; run the
disposable PostgreSQL suite when its approved isolated target is available.
