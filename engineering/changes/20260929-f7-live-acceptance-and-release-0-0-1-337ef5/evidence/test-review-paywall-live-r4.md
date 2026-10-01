# Independent test review R4 — signed v2 grant and web integrity fixes

Status: **PASS**

Reviewed commit: `87d8ac45b11910f871e303cf1115fde5dcda36c6`
Reviewed tree: `3300e6cfef7c5a70bcd0eb05cfdc23249f167698`
Route: `337ef5ec16a0` / evidence kind `test_review`
Prior review: `test-review-paywall-live-r3.md` (`FAIL`)

## Prior findings

### T1 closed — bounded multi-payer authority and durable reservations

The ambient `demoAnyPayer` widening has been replaced by a signed Ed25519 v2
grant envelope. Tests cover the exact canonical signed payload, pinned key ID,
bad signature, duplicate-key/malformed envelope, noncanonical payload, maximum
24-hour lifetime, unchanged v1 buyer binding, and a full v2 verification bound
to the quote payer.

Migration 006 adds immutable grant authority and reservation ledgers with exact
submission/total/per-payer bounds. The PostgreSQL test covers one atomic winner
under twenty pools, a second distinct payer after restart, exhaustion before a
third payer, durable availability projection, and append-only reservations.
Gateway readiness now queries the v2 authority budget instead of hiding the
shared digest after the first sale. Migration checksum/installer inventories
are updated and contract-tested through 001–006.

### T2 closed — preview assets are byte-digest bound

`verifyHistoricalAssets` hashes both the exact report bytes and ZIP bytes
before parsing or rendering. Tests verify the checked-in assets against the
declared digests and independently mutate each byte stream to prove rejection.
The canonical F3 suite continues to exercise offline bundle reconstruction and
tamper rejection.

### T3 closed — wallet behavior is exercised, not source-matched

Tests invoke `switchToMezo` through mock EIP-1193 providers and assert exact
switch parameters, the 4902 add-chain fallback with pinned Mezo Matsnet values,
post-operation chain revalidation, preservation of user rejection, and failure
when the provider remains on the wrong chain. A separate executable test proves
late provider selection removes the old listeners, binds the selected provider,
updates state, and disposes cleanly.

## Commands and observed results

```text
npm test                                      # apps/mezo-gateway
51 passed, 7 skipped

npm test                                      # apps/mezo-web
26 passed

npm run typecheck                             # apps/mezo-web
PASS

npm exec vite build -- --configLoader runner --outDir <fresh-temp-dir>
PASS; 476 modules transformed, production assets emitted

.venv/bin/pytest -q \
  tests/contracts/test_signed_grant_authority.py \
  tests/operations/test_f6_static.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/contracts/test_live_grant_consumption.py \
  tests/installer/test_contracts.py
21 passed
```

The repository-local web `dist` and Vite temp directories were root-owned, so
the default in-place build failed with `EACCES`. Re-running the same production
build with Vite's runner config loader and a fresh temporary output directory
passed. This isolates the failure to checkout residue rather than source code.

No `TEST_DATABASE_URL` / `TEST_DATABASE_DISPOSABLE=1` authority was present.
Therefore the seven explicitly gated PostgreSQL tests, including the new
twenty-pool v2 reservation test, are `NOT_RUN` in this review. Their executable
coverage was inspected but is not represented as fresh runtime database
evidence. A release claim requiring current real-PostgreSQL proof must retain
that limitation or supply a separate fingerprint-bound run.

## Regression evidence retained

- v1 grant remains one-shot, buyer-bound, and fail-closed after expiry.
- v2 reservations precede settlement and preserve UNKNOWN/reconcile-only
  semantics; replay cannot resettle.
- transient receipt RPC absence preserves `PAID` and does not trigger a new
  settlement.
- private grant-file link, permission, size, replacement, and bounded-read
  tests pass.
- live report offline rebuild, raw/mapping digest binding, and ZIP tamper tests
  pass.
- Compose payment-disable override, isolated database proxy, secret topology,
  CSP and resource bounds pass static rendering tests.

## Verdict

PASS for test coverage and observed non-PostgreSQL verification at the exact
commit/tree above. No open test finding remains from R3. The disposable
PostgreSQL execution limitation is explicit and must not be silently promoted
to a current-run PASS.
