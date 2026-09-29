# Rollback plan — F4 local gateway and ledger verification

## Trigger conditions

- Cleanup accepts any non-200, malformed, mismatched, or non-boolean response.
- An eligible retry fails to converge, or an ineligible/paid artifact is
  selected.
- Idempotency produces duplicate request/report identity or cross-scope alias.
- Migration/vector/lockfile bytes change, payment readiness opens, or any
  external/shared system is contacted.

## Application rollback

Before durable payment state, revert the TypeScript adapter/test-harness commit
and keep F4 unverified. Do not delete or rewrite ledger data as rollback.

## Data recovery / forward-fix

Migration 001 remains unchanged and every verification database is disposable.
Migration 002 is forward-only: after application, rollback means disable new
sales and deploy a reviewed corrective `CREATE OR REPLACE FUNCTION`, never
restore 001's broken function or delete ledger data. For affected `AVAILABLE`
rows whose storage is already absent, reconcile using authoritative exact-ID
cleanup evidence while preserving scopes, requests, quotes, dedup rows, and
audit history.

## Verification after rollback

Re-run compile/typecheck, strict cleanup negative cases, migration checksum,
idempotency races, and ledger invariant queries. Confirm payment boundaries
remain closed and the disposable database is removed.
