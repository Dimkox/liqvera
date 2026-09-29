# Rollback plan — F3 offline artifact verification repair

## Trigger conditions

Acceptance contract incompatibility, loss of deterministic artifact bytes,
partial target visibility, overwrite of an existing UUID, weakened rejection,
or any network/database/external operation.

## Application rollback

Revert the schema/test commit and any separate canonical runtime repair commit.
Do not run or revert a migration because this tranche has none.

## Data recovery / forward-fix

Remove only invocation-owned temporary staging output. Preserve any already
published complete immutable target and recover by readback or a new UUID;
never mutate its files in place. There is no persistent-store recovery.

## Verification after rollback

Run the focused pre-change evidence-report and contract suites plus the full PR
verifier, and confirm the original fixture path and F2 schemas remain green.
