# Release plan — F7 live acceptance and release 0.0.1

## Follow-up v0.0.2 candidate

Root product VERSION is now `0.0.2`; component versions remain `0.1.0` and
root workspace metadata remains `0.1.0.dev0`. New A07 sealed evidence plus the
retained A13/A14 and A29 evidence closes the external-case set when projected
across results: 9 PASS, 21 NOT_RUN, zero BLOCKED_EXTERNAL, zero FAIL. This is
still INCOMPLETE and is not a single runner overall PASS. See
`evidence/acceptance-v0.0.2.md`, `release-notes-v0.0.2.md`, and the pending
`release-artifact-manifest-v0.0.2.json`. No v0.0.2 artifact, push, tag, or
GitHub Release exists.

## Deployment

No hosted deployment. P5 only fast-forwards canonical `main`, creates annotated
`v0.0.1`, and creates/publishes the GitHub Release after exact grants.

## Published release

Release `v0.0.1` is published at
`https://github.com/Dimkox/liqvera/releases/tag/v0.0.1` and its tag targets
`a0fd5f0884a3fd1a6663982ea5df387b47528bdd`.

Public asset download verification passed:

- `liqvera-0.0.1.zip`: `a6d8a6adb4350f1bf3f30c719e3f3c0e24527fc2289cb256fa50e2b9cc8ae2d8`
- `RELEASE_NOTES.md`: `f1ddb3fa85a49c9cccc280d0bd8cf66d1f2b0a1428473174813ba3981bf27b7f`
- `release-manifest.json`: `220a53603360adc43c27bd9a711440274239558ba2c1c2da0b0ffbe4cdd7100d`
- `SHA256SUMS`: `b002e6b3bef3d5faa66c7ddbf8b8d07e157c6b76f4db33d0ce8d2c028827ec19`

A29 passed through a credential-disabled anonymous recursive clone: root
VERSION `0.0.1`, kernel VERSION `2.0.19`, submodule
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. No hosted deployment was made.

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

Publication is complete. **NO-GO** remains for another payment or any mutation
of the immutable tag/release/assets. One authorized Mezo Testnet settlement is
retained as scoped A13/A14 evidence and does not authorize a retry.

P0 GO requires scope approval plus green repair tests/verifier/reviews. P1 GO
requires valid immutable local result and reviewed omissions. P2/P3/P5 each
require their own exact short-lived grant. P3 additionally requires reviewed
production wiring and numeric buyer-native gas-spend cap. P4 requires exact clean commit, complete
manifest/checksums, artifact extraction/install validation, scans and all five
reviews. Any FAIL blocks release. An INCOMPLETE release requires explicit owner
acceptance and cannot claim completed F7/payment readiness.

## Release-preparation evidence

For the published v0.0.1 preparation, root `VERSION` was `0.0.1`; component
versions remain `0.1.0` and root workspace
metadata remains `0.1.0.dev0`. The retained live result SHA-256 is
`53830fe2249e2754f3c0eeaab8d5292849b2ef55bd5f5c2ae51be7e081457e61`;
only A13/A14 are accepted from it because its overall status is FAIL. The
corrected offline candidate SHA-256 is
`4799bce919b3c7d2882ad0f67dee51e7945909664fe81dd95f120afced5d84d6`
and is INCOMPLETE with no FAIL rows. See
`evidence/acceptance-release-candidate.md`.

`release-artifact-manifest.json` and `release-notes-v0.0.1.md` remain historical
pre-publication inputs and are not the downloaded release assets. The observed
publication identity and hashes above are authoritative post-release evidence.
The overall acceptance limitation remains truthful: the historical live result
is FAIL outside its passing A13/A14 rows, while the corrected candidate is
INCOMPLETE; all 156 frozen vectors remain NOT_RUN and no hosted deployment,
mainnet, custody, private venue, or exchange mutation is claimed.
