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

The migration is unchanged and the verification database is disposable. If a
deployed ledger ever contains affected `AVAILABLE` rows whose storage is
already absent, disable new sales and forward-fix using authoritative exact-ID
cleanup/reconciliation evidence. Preserve scopes, requests, quotes, dedup rows,
and audit history.

## Verification after rollback

Re-run compile/typecheck, strict cleanup negative cases, migration checksum,
idempotency races, and ledger invariant queries. Confirm payment boundaries
remain closed and the disposable database is removed.
