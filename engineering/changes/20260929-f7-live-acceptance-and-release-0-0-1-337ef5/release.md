# Release plan — F7 live acceptance and release 0.0.1

## Deployment

No hosted deployment. P5 only fast-forwards canonical `main`, creates annotated
`v0.0.1`, and creates/publishes the GitHub Release after exact grants.

## Feature flags / staged rollout

No bypass flag may enable payment. P0–P5 are sequential gates; public reads,
testnet payment, and publication have independent expiring grants. GitHub
Release is created as draft, assets are re-downloaded/rehashed, then a final
owner confirmation permits publication.

## Metrics and alerts

Acceptance inventory/status/evidence digests; commit/tree/fingerprint; exact
settle count; tx/block/log identity; artifact names/sizes/SHA-256; remote main,
tag target, release state, and anonymous download hashes. Raw secrets are never
metrics or evidence.

## Go/no-go criteria

Current: **NO-GO** for public reads, payment, push, tag, or GitHub Release.

P0 GO requires scope approval plus green repair tests/verifier/reviews. P1 GO
requires valid immutable local result and reviewed omissions. P2/P3/P5 each
require their own exact short-lived grant. P3 additionally requires reviewed
production wiring and numeric gas cap. P4 requires exact clean commit, complete
manifest/checksums, artifact extraction/install validation, scans and all five
reviews. Any FAIL blocks release. An INCOMPLETE release requires explicit owner
acceptance and cannot claim completed F7/payment readiness.
