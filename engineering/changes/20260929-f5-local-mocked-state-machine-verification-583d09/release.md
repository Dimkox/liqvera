# Release plan — F5 local mocked state-machine verification

## Deployment

None. This route produces local verification evidence only.

## Feature flags / staged rollout

None; unresolved production identity/finality blockers and fixture fail-closed
behavior remain intact.

## Metrics and alerts

No production changes. Tests assert call traces and visible state.

## Go/no-go criteria

Go for independent review only when focused gateway checks and pinned PR
verification pass on a clean tree. No-go for payment readiness, deployment, or
release; all frozen acceptance vectors remain `NOT_RUN`.
