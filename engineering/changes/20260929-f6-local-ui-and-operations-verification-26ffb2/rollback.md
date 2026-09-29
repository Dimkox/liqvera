# Rollback plan — F6 local UI and operations verification

## Trigger conditions

- Browser regression, changed public API or saved-flow format, second payment
  opportunity, fixture/live topology crossover, public metrics exposure,
  weakened CSP, failed focused/full verification, or review finding.

## Application rollback

Revert the coherent F6 browser/test/config/documentation implementation commit.
Restore the preceding web sources, Compose/Caddy/gateway operational binding,
and runbooks together; then rerun the pre-F6 web build/typecheck and static
Compose render. Production has no enabled payment adapter, so no live payment
state is created by this route.

## Data recovery / forward-fix

No schema, storage version, database, container, or persistent volume change is
authorized, so there is no data rollback or backfill. Existing version-1
session records remain readable. If implementation discovers that a migration,
container-created schema/volume, or external write is necessary, stop before
the action and request a new exact approval.

## Verification after rollback

- Exact-lock web typecheck and build pass.
- Both fixture and live Compose profiles resolve statically to the pre-change
  topology without starting services.
- Production x402 remains unregistered; no endpoint, schema, frozen vector, or
  payment-readiness claim changed.
- Repository status shows no unintended generated, secret, or runtime files.
