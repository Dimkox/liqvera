# Release plan — F3 offline artifact verification repair

## Deployment

None. This change produces repository-local tests, a contract repair, and
verification evidence only.

## Feature flags / staged rollout

Not applicable. Fixture output remains simulated and payment readiness remains
false; no live authority is introduced.

## Metrics and alerts

Record focused/full test results, artifact hashes, rejection reason codes, and
fingerprint-bound review receipts. No runtime alert is added.

## Go/no-go criteria

Go only when the offline installed vertical and all negative regressions are
green and route-selected reviews pass. No-go for deployment, release, live
capture, payment, shared database use, or F4-F7 completion claims.
