# Release plan — F6 local UI and operations verification

## Deployment

None. This route produces local browser/static verification and repository
repairs only. It does not push, deploy, publish, start the live profile, or cut
a release.

## Feature flags / staged rollout

No feature flag or rollout. Production's absent x402 adapter is preserved.
Fixture remains simulated, non-chargeable, and loopback-only. Any later runtime
container verification or deployment is a separate approved change.

## Metrics and alerts

Validate that existing bounded metrics can be scraped only across a private
operations network and that Caddy/host expose no metrics route. Validate stable
safe labels and documented alerts statically. No collector, dashboard, alert
installation, or external telemetry write is introduced.

## Go/no-go criteria

Repository implementation may proceed only after recorded
`scope_and_design_approval`. Completion additionally requires focused browser
and static operations checks, exact-lock build/typecheck, pinned PR verification,
all route-selected independent reviews, and current fingerprint-bound receipts.
This is not a deployment/release go decision. `migration_or_external_write`
remains not applicable and unexercised; needing it is an immediate stop.
