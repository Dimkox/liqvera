# Independent final test review R5 — pinned signed-grant issuer

Status: **PASS**

Reviewed commit: `95d438bad1e6bb56a74498c609585546c314cb38`
Reviewed tree: `419edfbc6ba05109fa63e4be522087475f68ca1c`
Route: `337ef5ec16a0` / evidence kind `test_review`

## Final change coverage

The signed v2 grant no longer trusts an arbitrary runtime-supplied public key.
The release-reviewed issuer key ID/public key is pinned in compiled code and in
the human-readable allowlist. Contract tests prove the raw key is exactly 32
bytes, its SHA-256 equals the key ID, the JSON and compiled identities match,
and an unapproved issuer is rejected before signature acceptance.

Gateway tests use an approved signed fixture and cover:

- unchanged v1 buyer-bound behavior;
- v2 rejection unless the explicit any-payer runtime switch is enabled;
- rejection of an unapproved issuer;
- rejection of a tampered signature under the approved issuer;
- exact quote-payer binding for approved v2 authority;
- canonical payload, lifetime, budget and settlement-policy constraints;
- grantless startup, expiry, private-file safety and existing payment-state
  regressions.

Resource-copy behavior includes test fixtures in the compiled test tree. The
published v0.0.2 installer remains intentionally frozen to migrations 001–005;
tests distinguish that immutable release inventory from the current gateway's
additive migration 006 rather than silently rewriting old release identity.

## Commands and observed results

```text
npm test                                      # apps/mezo-gateway
51 passed, 7 skipped

.venv/bin/pytest -q \
  tests/contracts/test_signed_grant_authority.py \
  tests/installer/test_contracts.py \
  tests/installer/test_archive_verifier.py \
  tests/installer/test_compose_install.py \
  tests/installer/test_lifecycle.py
99 passed

npm test                                      # apps/mezo-web
26 passed

npm run typecheck                             # apps/mezo-web
PASS

npm exec vite build -- --configLoader runner --outDir <fresh-temp-dir>
PASS; 476 modules transformed
```

The seven gateway skips require an explicitly disposable PostgreSQL URL. No
`TEST_DATABASE_URL` / `TEST_DATABASE_DISPOSABLE=1` authority was available, so
fresh real-PostgreSQL execution of migrations 001–006 and the twenty-pool v2
reservation race remains `NOT_RUN` in this review. Its executable test was
inspected and the limitation must remain explicit unless separately run against
this fingerprint.

## Verdict

PASS for test adequacy, compilation, web production build, issuer pinning, and
available regression execution at the exact commit/tree above. No open test
finding remains. The disposable PostgreSQL runtime limitation is explicit and
is not promoted to a current-run PASS.
