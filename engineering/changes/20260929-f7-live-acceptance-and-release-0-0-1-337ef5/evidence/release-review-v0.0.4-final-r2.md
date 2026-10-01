# Final release re-review — v0.0.4 signed-v2 candidate

Reviewed commit: `95d438bad1e6bb56a74498c609585546c314cb38`

Reviewed tree: `419edfbc6ba05109fa63e4be522087475f68ca1c`

Decision: **PASS**

No release-blocking finding remains in this review scope.

## Closed findings

### Versioned go/no-go state is truthful

The release plan now scopes completed publication and immutable assets to historical v0.0.1. It separately states that current v0.0.4 publication is pending, that signed-v2 deployment/payment evidence does not exist for this head, and that historical payment evidence cannot be promoted to this candidate.

Deployment history is also unambiguous: paid acceptance belongs to deployed `0f3e745d41022c33fbb075c9816b35b1c6a3cabe`; browser hotfix `cba005b1c07aafadb4dd15743b7184143143dcf5` was later deployed and smoke-tested without another payment; later review repairs, including reviewed HEAD, are not claimed as deployed.

### Migration-006 rollback is fail-closed and preserves authority budget

The rollback plan now identifies migration 006 as forward-only and requires preservation of every authority row, reservation, spent ordinal, count/amount debit, per-payer uniqueness record, and UNKNOWN reservation. It forbids deletion, rewind, truncation, recreation, budget backfill, down migration, and reservation release.

Rolling application code below migration 006 requires first applying the checked-in grantless override, confirming `EXTERNAL_GRANT_REQUIRED`, retaining schema/data 006, and forward-fixing compatibility. This closes the risk that rollback could make spent signed authority available again.

## Release consistency

- Root VERSION remains the unpublished `0.0.4` candidate.
- README and handoff distinguish published v0.0.1–v0.0.3 history, the v0.0.2 installable package, deployed older v0.0.4 candidates, and the undeployed reviewed head.
- Acceptance-v0.0.4 remains bound to the older paid candidate and is not represented as signed-v2 evidence.
- The pinned signed-v2 issuer trust root contains a public key/fingerprint only; the private-key location is recorded without secret contents, and the key is not committed.
- v1 remains exact-buyer/one-shot; signed v2 remains separately gated and is not enabled by historical authority.
- The grantless live override remains the operational stop path and preserves database/artifact state plus UNKNOWN confirm-only recovery.
- No v0.0.4 artifact, tag, push, GitHub Release, signed-v2 deployment, or signed-v2 payment is claimed.

## Verification sampled

- Exact commit/tree and clean product state confirmed before report creation.
- `git diff --check 87d8ac4..95d438b` — PASS.
- Focused Python signed-authority/operations/installer tests — **13 passed**.
- Focused gateway signed-v2/issuer/grantless/migration invocation — **51 passed, 7 skipped, 0 failed**.
- The skipped gateway cases require an explicitly disposable PostgreSQL URL; this review did not create or mutate a database.
- No external call, secret read, deployment, payment, push, tag, or release mutation was performed.

## Decision boundary

PASS means the release documentation, rollback, version state, deployment distinction, and evidence claims are suitable for this exact candidate. It is not deployment or publication authority. Current release text correctly keeps push, tag, GitHub Release, deployment, and payment NO-GO until fingerprint-bound verification, the remaining independent reviews, and applicable human gates pass.
