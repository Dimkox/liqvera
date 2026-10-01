# Hotfix release review — v0.0.5 preparation

Reviewed commit: `6df3c60a4a58a7a2022ab21c57556c7e36f8c96a`

Reviewed tree: `5546b8945fe40ae6367bb3386e588e548453d70d`

Decision: **FAIL / NO-GO for v0.0.5 publication**

The date-rendering hotfix and live browser smoke are release-worthy, but v0.0.5 has not yet been prepared as a versioned, asset-bound release.

## Blocking findings

### RELEASE-BLOCKER — v0.0.5 identity and assets do not exist

Root VERSION remains `0.0.4`; there is no local or remote `v0.0.5` tag, no GitHub v0.0.5 release, and no staged v0.0.5 source archive, release notes, artifact manifest, `SHA256SUMS`, detached checksum, extraction validation, or reproducibility evidence.

Required correction: advance the root product VERSION to `0.0.5` while preserving component and installer identities, freeze a clean final publication commit, then build and independently validate a closed v0.0.5 source/evidence asset set bound to that exact commit/tree. The installable operator package must remain v0.0.2 unless a separately reviewed installer release is intentionally created.

### RELEASE-BLOCKER — canonical release plan still describes published v0.0.4 as pending

README and handoff correctly record that v0.0.4 is published and that its immutable tag targets `b4461ea3e3385f8bbeaa94194db57e89f3a97a23`. Read-only GitHub inspection confirms a non-draft, non-prerelease v0.0.4 release with the five reviewed assets and exact reviewed digests.

`engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release.md` still says v0.0.4 push, tag, and GitHub Release remain pending in both its deployment/publication section and go/no-go section. This is now false canonical release state.

Required correction: record v0.0.4 publication as complete with immutable tag/source identity and asset hashes, then create a separately scoped v0.0.5 hotfix section stating what is deployed, what exact commit is the publication candidate, and what tag/assets remain pending.

## Passing hotfix evidence

- The defect is bounded to the browser: the removed fresh-path formatter combined ECMA-402 `dateStyle`, `timeStyle`, and `timeZoneName`, which throws in Chromium/Node.
- All four fresh quote/delivery timestamps now use the already reviewed UTC formatter used by the historical preview.
- Web commit `f34464521e85a2798a51a00c2d33cba60e809fbf` / tree `39bddd9cdf4ab3ab8de8cf5c7be58c30cb9b49f3` was deployed by rebuilding/recreating only `web-live`; gateway, PostgreSQL, signed grant, authority reservations, and payment state were not changed.
- A real headless Chrome smoke discovered an EIP-6963 provider, connected to Mezo 31611, created fresh live-public request `dc776db0-ecd9-4d46-8852-0d1fffde0f03` / quote `a9c8de9b-9cb9-4a63-b2ae-c41e1ca0f799`, rendered snapshot/expiry, and reached `Evidence is ready` with no runtime/console exception.
- The smoke stopped before payment: no signature, settlement submission, retry, or new payment occurred.
- Reviewed HEAD is a documentation child of the deployed hotfix and is not falsely claimed as the deployed runtime.

## Version, prior release, and rollback assessment

- v0.0.4 remote tag resolves to reviewed source commit `b4461ea3…`; its published asset sizes/digests match the prior reviewed set.
- README truthfully calls root 0.0.4 published and keeps the installable package at v0.0.2.
- Overall F7 remains INCOMPLETE; no acceptance omission is relabelled.
- Existing grantless rollback remains valid because the hotfix changes only web rendering. Migration-006 authority/reservations, UNKNOWN state, ledger/artifacts, and v0.0.2 installer immutability are unaffected.
- A v0.0.5 rollback should restore the prior v0.0.4 web image/source while preserving the unchanged gateway/database/payment state; it must never move or replace the immutable v0.0.4 tag/assets.

## Verification sampled

- Exact commit/tree and clean product state confirmed before report creation.
- `tests/operations/test_f6_static.py` — **5 passed**.
- Mezo web tests — **27 passed, 0 failed**.
- Production web build — PASS.
- Read-only remote v0.0.4 tag/release/assets inspection — PASS.
- Read-only v0.0.5 lookup — tag/release absent, consistent with not prepared.
- No external mutation, secret read, deployment, payment, push, tag, or release action was performed by this review.

## Required next release step

Repair the canonical release state, bump VERSION to 0.0.5, freeze the final source commit, build and validate exact v0.0.5 assets, and rerun fingerprint-bound verification plus all selected independent reviews. Publication remains NO-GO until that final candidate and its assets pass the applicable human publication gate.
