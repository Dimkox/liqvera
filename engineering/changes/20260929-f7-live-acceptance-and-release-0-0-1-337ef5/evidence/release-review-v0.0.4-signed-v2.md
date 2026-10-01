# Release review — v0.0.4 signed-v2 candidate

Reviewed commit: `87d8ac45b11910f871e303cf1115fde5dcda36c6`

Reviewed tree: `3300e6cfef7c5a70bcd0eb05cfdc23249f167698`

Decision: **FAIL / NO-GO for publication**

## Blocking findings

### RELEASE-BLOCKER — current go/no-go text still claims publication is complete

`engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/release.md:23-30` now correctly distinguishes deployed paid candidate `0f3e745`, subsequently deployed browser hotfix `cba005b`, and later review repairs that are not deployed. It also correctly says the v0.0.4 push, tag, and GitHub Release remain pending.

The same document's unscoped `## Go/no-go criteria` says `Publication is complete` at line 66. That statement conflicts with the current v0.0.4 state and can be read as authorization to mutate or reuse historical release assets. It belongs to the historical v0.0.1 section, not current release readiness.

Required correction: scope the completed-publication/no-more-payment paragraph explicitly to historical v0.0.1, and add current v0.0.4 go/no-go text that says publication is pending and that signed-v2 deployment/payment evidence does not exist for this exact head.

### RELEASE-BLOCKER — rollback omits forward-only migration 006 and its durable authority budget

Signed-v2 adds `006_signed_live_grant_authority.sql`, immutable authority metadata, and append-only reservations. The rollback plan documents forward-only migrations 003 and 004 only. It does not instruct operators to retain the migration-006 tables, authority identity, reservations, spent ordinals, per-payer uniqueness, count/amount budgets, or UNKNOWN reservations across an application rollback.

This omission is material: deleting or rewinding migration-006 state could restore already-spent signed authority and permit additional settlements after rollback.

Required correction: state that migration 006 is forward-only; its authority and reservation rows are audit, replay-prevention, and budget evidence; UNKNOWN reservations remain permanently spent; rollback disables new sales through the checked-in grantless override and never deletes, rewinds, or recreates authority budget. Describe forward-fix expectations when application code is rolled back below migration 006.

## Closed prior finding

The earlier deployment-history contradiction is repaired. The release plan now truthfully distinguishes:

- the paid deployed candidate `0f3e745d41022c33fbb075c9816b35b1c6a3cabe`;
- deployed and smoke-tested browser hotfix `cba005b1c07aafadb4dd15743b7184143143dcf5`;
- later review repairs, including this exact head, which are not claimed as deployed;
- already-published v0.0.2/v0.0.3 milestones;
- pending v0.0.4 push, tag, and GitHub Release.

README, handoff, root VERSION `0.0.4`, and acceptance-v0.0.4 remain consistent with that distinction. No fresh deployment or payment is claimed for signed-v2 head `87d8ac4`.

## Signed-v2 release assessment

- v1 remains exact-buyer and one-shot.
- v2 requires duplicate-free canonical payload bytes, Ed25519 verification against a configured raw public key, matching key fingerprint, exact runtime/payment/database bindings, bounded 24-hour validity, count and total budgets, and one reservation per payer.
- The private issuer key is not present in repository/runtime inputs; the runtime consumes a public key.
- Compose passes the public key only through the live gateway environment; the grantless override resets the gateway environment and therefore removes grant activation and public-key activation together.
- The exact head is not deployed, and no signed-v2 live settlement evidence is claimed. Historical paid E2E evidence remains bound to its older candidate and authority model.

## Verification sampled

- Exact commit/tree and clean product state confirmed before report creation.
- `git diff --check cba005b..87d8ac4` — PASS.
- Focused Python contract/operations/installer tests — **11 passed**.
- Focused gateway grant/authority/reservation/migration invocation — **51 passed, 7 skipped, 0 failed**.
- The seven skipped cases require an explicitly disposable PostgreSQL URL; handoff separately records their completed disposable-PostgreSQL run, but this review did not recreate it.
- No external call, secret read, deployment, payment, push, tag, or GitHub Release was performed.

## Route closure

At review time route status still reports stale verification, review receipts, and human gates after repository changes. This FAIL receipt is bound to the reviewed fingerprint and does not authorize deployment or publication.

Publication remains NO-GO until both release/rollback documentation blockers are repaired and the resulting exact commit completes fingerprint-bound verification, all independent reviews, and required human gates.
