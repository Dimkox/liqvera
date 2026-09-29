# Rollback plan — F3-F7 verification and defect repair

## Trigger conditions

Schema incompatibility, loss of deterministic hashes, partial publication,
network/external-write attempt, weakened reason codes, or regression in current
Stage A/F2 tests.

## Application rollback

Revert the tranche commits. Do not revert or run any database migration because
this tranche does not alter a schema or persistent store.

## Data recovery / forward-fix

Delete only invocation-owned temporary artifacts. Published immutable artifacts
are never mutated; a corrected run receives a new identity. No backfill exists.

## Verification after rollback

Run the pre-change focused suites and full PR verifier; confirm fixture hashes
and existing F2 contracts match the base tree.
