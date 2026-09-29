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

Current: **NO-GO** for another payment, push, tag, or GitHub Release. One
authorized Mezo Testnet settlement already occurred and is retained as scoped
A13/A14 evidence; it does not authorize a retry or publication.

P0 GO requires scope approval plus green repair tests/verifier/reviews. P1 GO
requires valid immutable local result and reviewed omissions. P2/P3/P5 each
require their own exact short-lived grant. P3 additionally requires reviewed
production wiring and numeric buyer-native gas-spend cap. P4 requires exact clean commit, complete
manifest/checksums, artifact extraction/install validation, scans and all five
reviews. Any FAIL blocks release. An INCOMPLETE release requires explicit owner
acceptance and cannot claim completed F7/payment readiness.

## Release-preparation evidence

Root `VERSION` is `0.0.1`; component versions remain `0.1.0` and root workspace
metadata remains `0.1.0.dev0`. The retained live result SHA-256 is
`53830fe2249e2754f3c0eeaab8d5292849b2ef55bd5f5c2ae51be7e081457e61`;
only A13/A14 are accepted from it because its overall status is FAIL. The
corrected offline candidate SHA-256 is
`4799bce919b3c7d2882ad0f67dee51e7945909664fe81dd95f120afced5d84d6`
and is INCOMPLETE with no FAIL rows. See
`evidence/acceptance-release-candidate.md`.

`release-artifact-manifest.json` and `release-notes-v0.0.1.md` are preparation
inputs. They intentionally mark the final release commit/tree, source archive,
`SHA256SUMS`, verifier/reviews, and publication as pending. Build from the final
reviewed clean commit, replace every pending field with observed values, verify
extraction and hashes in a fresh directory, then obtain the separate publication
approval. Do not tag or publish the current preparation commit.
