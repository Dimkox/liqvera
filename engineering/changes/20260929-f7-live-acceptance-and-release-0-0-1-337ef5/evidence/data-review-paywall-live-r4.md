# Independent data review R4 — signed v2 grant authority

Status: **PASS**
Reviewed commit: `87d8ac45b11910f871e303cf1115fde5dcda36c6`
Reviewed tree: `3300e6cfef7c5a70bcd0eb05cfdc23249f167698`
Prior finding: `DATA-002` in `data-review-paywall-live-r3.md`

## Verdict

`DATA-002` is closed. Signed v2 authority now has a durable, bounded reservation
model that agrees with readiness and survives process restart. Migration 006 is
additive and append-only, while the existing v1 one-shot path remains unchanged.
No blocking data finding remains in the reviewed scope.

## DATA-002 closure

- A v2 grant exposes its digest and parsed authority to the gateway. Readiness
  calls `Ledger.grantAvailable()` instead of hiding the consumed state. The
  query requires an activated, currently valid authority with both remaining
  submission count and remaining total amount.
- Startup activates the verified signed authority before initializing payment.
  The authority row binds grant ID/digest, canonical policy digest, signing key
  ID, signature digest, validity interval, payee, per-payment amount, maximum
  submissions, total amount, and per-payer policy. A conflicting activation
  cannot silently replace existing authority.
- `markSubmitting()` locks the authority row `FOR UPDATE`, reads the reservation
  count and total under that lock, and inserts the next ordinal reservation in
  the same transaction that crosses `VERIFIED -> SUBMITTING`. Concurrent
  contenders therefore serialize on one durable budget. A failed transaction
  rolls back both reservation and state transition.
- Exhaustion returns the existing typed `GRANT_CONSUMED` outcome. The losing
  attempt becomes `REJECTED`, its quote returns to `READY`, and an audit event
  is written atomically; external settlement is not called.
- Reservations are unique by `(grant_digest, ordinal)`, payment attempt, and
  `(grant_digest, payer)`. Together with `max_per_payer = 1`, this enforces one
  reservation per payer as well as the aggregate count and amount bounds.
- Restart does not reset authority or budget: availability and reservation use
  PostgreSQL rows, not in-process counters. The gateway re-activation is
  idempotent for the same signed authority.

## Migration and compatibility assessment

- Migration 006 only creates `live_grant_authorities` and
  `live_grant_reservations`; it contains no destructive DDL or backfill. Its
  SHA-256 is
  `92e346b3fa49699b20d9edca9814d17bde4fb96046e71071c68b0c47326ef18a`
  and matches the pinned migration policy.
- Both new tables reject update/delete through the existing
  `forbid_audit_mutation()` trigger. Spent reservations are permanent evidence.
- Database constraints independently bound maximum submissions to 1..1000,
  require `max_total = amount_per * max_submissions`, require one payment per
  payer, and limit authority lifetime to 24 hours.
- v1 parsing, payer binding, readiness lookup, and
  `live_grant_consumptions` remain intact. V1 attempts do not enter the v2
  authority branch, so migration 006 does not reinterpret or replace historical
  one-shot rows.
- Receipt persistence, `UNKNOWN` confirm-only recovery, and paid-entitlement
  revalidation are unchanged by the reservation migration.

## Verification evidence

Commands executed at the reviewed commit/tree:

```text
npm test --prefix apps/mezo-gateway
```

Result: **51 passed, 0 failed, 7 skipped**. Build and TypeScript compilation
passed. The seven skips are the explicitly disposable PostgreSQL cases,
including the new v2 concurrency/restart/append-only integration test, because
no approved disposable database URL was configured.

```text
.venv/bin/python -m pytest -q \
  tests/contracts/test_signed_grant_authority.py \
  tests/contracts/test_live_grant_consumption.py
```

Result: **4 passed**.

The gated PostgreSQL test source covers twenty concurrent adapters, exactly one
winner for a reservation, a second reservation after adapter restart, budget
exhaustion, a rejected third attempt, exact persisted row count, and append-only
deletion rejection. Transaction and schema inspection support those invariants;
the real PostgreSQL execution remains an explicit environment limitation and
should be retained as release evidence only after an authorized disposable run.

## Decision

Data review passes for commit
`87d8ac45b11910f871e303cf1115fde5dcda36c6` / tree
`3300e6cfef7c5a70bcd0eb05cfdc23249f167698`. Record a passing route receipt
only while this exact repository/spec binding remains current.
