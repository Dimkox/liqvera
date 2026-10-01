# Code review — final re-review at 95d438b

## Reviewed state

- Commit: `95d438bad1e6bb56a74498c609585546c314cb38`
- Tree: `419edfbc6ba05109fa63e4be522087475f68ca1c`
- Comparison base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Review scope: live Hyperliquid sealed identity/offline verification, Mezo testnet one-shot grant/paywall, signed-v2 grant authority, migration 006, and preservation of the published installer v0.0.2 contract.

## Outcome

**PASS.** The two Important findings from the review of `87d8ac4` are closed, and no new Critical or Important defects were found in the resulting diff or surrounding implementation.

## Prior finding closure

### I-1 — Published installer v0.0.2 was mutated: closed

The installer source set, manifest, release schema, builder, verifier, and installer tests again define v0.0.2 as migrations `001`–`005`. Migration `006_signed_grant_authority.sql` remains an independent forward migration and is no longer injected into the already-published v0.0.2 archive contract.

As an additional immutability check, the installer-related diff between the pre-signed-v2 state `229183e` and this reviewed commit is empty. Tests now explicitly assert that the published v0.0.2 migration set remains `001`–`005` even when migration 006 exists in the repository.

### I-2 — `LIQVERA_TESTNET_DEMO_ANY_PAYER` did not gate signed-v2 grants: closed

The parsed configuration value is now propagated from `main.ts` into live composition as `allowAnyPayer`. Signed-v2 grants are rejected with `LIVE_GRANT_ANY_PAYER_NOT_ENABLED` unless that value is explicitly `true`; an approved, correctly signed v2 grant therefore cannot activate the any-payer path under the default configuration. The focused test covers both rejection without the flag and acceptance with the flag.

## Strengths

- The signed-v2 trust root is release-controlled: the issuer key id and Ed25519 public key are pinned in the checked-in allowlist, and unapproved issuer material is rejected before signature acceptance.
- Tests cover approved, unapproved, and tampered signed-v2 fixtures.
- Canonical serialization, duplicate-key rejection, exact runtime/payment identity binding, and bounded grant lifetime remain intact.
- Migration 006 is additive and preserves the append-only authority/reservation model; the database-backed reservation path serializes against the authority row and enforces count, aggregate, and per-payer limits.
- The v1 one-shot, buyer-bound path remains available and unchanged in semantics.

## Findings

### Critical

None.

### Important

None.

### Minor

None.

## Verification evidence

- `npm --prefix apps/mezo-gateway test` — PASS: 51 passed, 7 skipped. The skips explicitly require a disposable PostgreSQL URL.
- `.venv/bin/pytest -q tests/contracts/test_signed_grant_authority.py tests/installer/test_contracts.py tests/installer/test_archive_verifier.py tests/installer/test_compose_install.py tests/installer/test_lifecycle.py` — PASS: 99 passed.
- Installer comparison against `229183e` for installer/build/verifier paths — no diff.

## Declined to judge

- No real Mezo payment or external deployment was executed as part of this read-only code review.
- The PostgreSQL integration cases requiring a disposable database were not exercised in this review; their skips are explicit and do not conceal unit-test failures.
- Product positioning, market fit, and visual design are outside this code-review scope.

## Readiness

The reviewed tree is ready to satisfy the route's `code_review` requirement. This decision is valid only for commit `95d438bad1e6bb56a74498c609585546c314cb38` / tree `419edfbc6ba05109fa63e4be522087475f68ca1c`; any repository change makes the receipt stale.
