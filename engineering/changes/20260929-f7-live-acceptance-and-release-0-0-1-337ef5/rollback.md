# Rollback plan — F7 live acceptance and release 0.0.1

## Trigger conditions

Any failed test/case, stale identity/grant, secret exposure, wrong external
target/envelope, UNKNOWN payment, inconsistent receipt/reorg, remote movement,
or artifact/tag/release mismatch.

## Application rollback

Before payment: stop and revert/forward-fix locally. After any payment state:
disable new sales and forward-fix; never drop/rewind ledger, erase dedup/audit,
replace immutable artifacts, or ask the buyer to pay again.

## Data recovery / forward-fix

UNKNOWN preserves quote/attempt/artifacts and permits exact confirm-only
reconciliation to confirmed or manual review. Suspected secret exposure stops
publication and requires human rotation outside the agent boundary.

Partial publication is additive: if main pushed but tag/release failed, verify
the pushed SHA and resume only the missing approved step. Never force-push or
move a published tag. An incorrect published release is superseded by a new
version after a fresh full gate; it is not silently replaced.

## Verification after rollback

Recreate a clean candidate, rerun all affected phases/reviews/verifier, generate
a fresh out-of-tree result and artifacts, and obtain new digest-bound grants.
