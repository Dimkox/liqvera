# Rollback plan — F6 local UI and operations verification

## Trigger conditions

- Browser regression, changed public API or saved-flow format, second payment
  opportunity, fixture/live topology crossover, public metrics exposure,
  weakened CSP, failed focused/full verification, or review finding.

## Application rollback

Use a selective forward fix. Never restore the known-unsafe pre-F6 fixture
egress attachments, process-local/uncollectible metrics binding, a public
metrics route, or the missing/weakened CSP. Those safety repairs remain the
minimum baseline even if another part of F6 regresses.

The browser policy seam and its call sites may be selectively reverted only if
they cause a confirmed regression and the preceding inline behavior is first
re-characterized as preserving the same payer binding, durable guard,
same-idempotency recovery, and no-resettlement invariants. Test-only files and
documentation may be reverted independently when they are the defect source.
Do not revert Compose, Caddy, and gateway metrics changes as a single bundle
with unrelated browser behavior. Production has no enabled payment adapter, so
this route creates no live payment state.

## Data recovery / forward-fix

No schema, storage version, database, container, or persistent volume change is
authorized, so there is no data rollback or backfill. Existing version-1
session records remain readable. If implementation discovers that a migration,
container-created schema/volume, or external write is necessary, stop before
the action and request a new exact approval.

## Verification after rollback

- The available web typecheck/tests pass and recovery/payment-guard
  characterization remains green; exact-lock build evidence is required when
  its locally unavailable dependency artifact is present.
- Both fixture and live Compose profiles resolve statically without starting
  services. Fixture has no external-egress membership; live-only egress stays
  profile-specific.
- Metrics remain private to the internal operations network with no host/Caddy
  route, and the restrictive CSP remains present without `unsafe-inline`.
- Production x402 remains unregistered; no endpoint, schema, frozen vector, or
  payment-readiness claim changed.
- Repository status shows no unintended generated, secret, or runtime files.
