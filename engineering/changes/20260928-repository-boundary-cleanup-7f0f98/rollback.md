# Rollback plan — Repository boundary cleanup

## Trigger conditions

- Product-path digest changes outside approved repository-boundary metadata.
- Graph or conformance references dangle after deletion.
- Product verification loses a required check or depends on agent tooling.
- Optional tooling cannot prove exact source and integrity.

## Application rollback

Revert cleanup commits in reverse order. Restore retired source and inventory
from base commit `0c2cb97f8048f7da8bd193634f4502f24b0e541e`; do not rewrite
history or substitute a floating dependency.

## Data recovery / forward-fix

None. No DDL, backfill, data write, or external mutation is permitted. Never
execute the deleted Stage-0 down migration as part of rollback.

## Verification after rollback

Re-run the recorded baseline checks, verify protected path hashes, and confirm
all product/payment/acceptance statuses remain unchanged.
