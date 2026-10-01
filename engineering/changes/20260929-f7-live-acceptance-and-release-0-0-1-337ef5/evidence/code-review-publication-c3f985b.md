# Code review — publication fingerprint at c3f985b

## Reviewed state

- Commit: `c3f985bd8df743d6c2c0a186dcf99c69329f6b13`
- Tree: `709a56736807b06424bb5450b893687e9d23eacf`
- Deployed parent: `dcdc7ae6086007d1ccaab8bc563c137c0e099feb`
- Deployed parent tree: `2459af5d0202a7d8e63ce44548d1f70fa0221ab6`
- Scope: final publication-fingerprint review of the post-deployment evidence and release documentation.

## Outcome

**PASS.** The delta from the independently reviewed and deployed parent is documentation/evidence only, with no application, migration, installer, test, build, or configuration drift. The material live-acceptance claims added by this commit agree with the retained artifacts and read-only database state inspected during this review.

## Code-drift assessment

The complete `dcdc7ae..c3f985b` delta contains only:

- `README.md`
- `handoff.md`
- `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/evidence/acceptance-v0.0.4.md`
- `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release.md`

An exclusion diff over those four paths returned no remaining changes. The deployed code is therefore byte-identical to parent commit `dcdc7ae` / tree `2459af5d`, whose application implementation was already independently reviewed.

## Evidence consistency

- The retained readiness document records `ready=true`, `payment_ready=true`, and no blockers.
- The retained historical report and ZIP hash exactly to the two SHA-256 values documented in this commit.
- The paid delivery records report `c956cd81-5ec2-439b-909b-4a9d8474cce3`, source time `2026-10-01T01:37:22.535Z`, engine commit `dcdc7ae`, quote `b15c2a5a-6343-4cbf-b26d-f538ae73dbc8`, transaction `0x4a04dc72c9f4b9051262b5c14db18369b9140d3012f7b02c3c8d3c6952778455`, block `15882012`, and 23 confirmations, matching the checked-in evidence.
- The delivery receipt binds report digest `da6515c2435b64ed8054a90d05d7087f7e52a3482aa3f0705d122caf83c70748`. The retained ZIP hashes to `051a3be6c5099eb140caf10d14e880febae0919fc6c8074fafcca2705882d473` and passes the repository offline verifier against that report digest.
- The retained submit result is `PAYMENT_UNCERTAIN`, while the subsequent delivery contains the canonical paid receipt. This supports the documented confirm-only recovery path without representing a second submission.
- Read-only PostgreSQL inspection shows one v2 authority with 20 submissions, `200000000000000000` maximum total atomic amount, one per payer, a 23-hour validity window, and exactly one reservation for `10000000000000000`; those values match the release evidence.
- The pre-migration custom-format PostgreSQL dump is structurally readable by `pg_restore --list`, and the live schema contains one `live_grant_authorities` table and one authority row.
- Remote inspection found no `v0.0.4` tag or GitHub Release, consistent with the repeated statement that publication remains pending.

## Findings

### Critical

None.

### Important

None.

### Minor

None.

## Verification performed

- Exact commit/tree and parent/tree identity checked with Git.
- Full parent-to-head name/status and content delta inspected.
- `git diff --check dcdc7ae..c3f985b` passed.
- Historical artifact SHA-256 values recomputed.
- Paid ZIP SHA-256 recomputed and offline verification passed.
- Paid delivery and receipt identities were machine-read from retained JSON.
- Authority limits and reservation count/amount were queried read-only from PostgreSQL.
- Pre-migration dump catalog was parsed successfully inside the PostgreSQL container.
- Remote main/tag and GitHub Release state were inspected read-only.

## Declined to judge

- This review did not submit another payment, mutate the deployment, query a private signing key, or reproduce the headless-browser session.
- The claim of exactly one signer invocation is supported by the single retained submit result, one database reservation, and one canonical receipt, but cannot prove the absence of an invocation that produced no durable local or remote record.
- Market fit and visual-design quality are outside this code-review scope.

## Readiness

The reviewed tree is ready to satisfy the route's final `code_review` requirement for publication preparation. This decision applies only to commit `c3f985bd8df743d6c2c0a186dcf99c69329f6b13` / tree `709a56736807b06424bb5450b893687e9d23eacf`; any repository change invalidates the receipt.
