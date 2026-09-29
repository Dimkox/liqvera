# Rollback plan — F5 local mocked state-machine verification

## Trigger conditions

Focused/full verification regression, public response change, resettlement,
entitlement visibility after mismatch, or any migration/vector modification.

## Application rollback

Revert the narrow orchestration classification and its tests/docs as one
coherent change. Shadow-only production blockers remain unchanged.

## Data recovery / forward-fix

No persistent data is touched. Temporary test directories are removed by the
test runner. A deployed ledger with payment state would require forward repair,
but deployment is outside this route.

## Verification after rollback

Run gateway exact-lock build/typecheck/tests and pinned PR verification.
