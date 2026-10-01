# Independent test review R3 — public demo and v0.0.4 follow-up

Status: **FAIL**

Reviewed commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`  
Reviewed tree: `75151ba8b154b72fd77d3df844beb4d3eca89dac`  
Route: `337ef5ec16a0` / required evidence kind `test_review`  
Role: route-selected independent `test_reviewer`

## Findings

### T1 — P0: reusable any-payer demo behavior is neither implemented coherently nor tested end to end

The new mode describes its grant as reusable across independently guarded
quotes and hides `liveGrantDigest` from readiness after the first sale.
However, `OfficialX402.verify()` still stores the same grant byte digest and
the same grant UUID in every authorization correlation. `Ledger.markSubmitting`
still inserts those values into `live_grant_consumptions`, whose digest and
grant ID are unique. Consequently the first payment consumes the grant and a
second judge/payment reaches `GRANT_CONSUMED` before settlement even though
readiness continues to advertise the demo as payable.

The added tests cover a different quote payer, extended expiry, and one verify
call only. No test performs two distinct any-payer quotes through durable grant
consumption and proves the intended outcome. This leaves the principal public
demo behavior unprotected and, on inspection, internally contradictory.

Required closure: define the intended bounded multi-payment authority in the
grant/ledger contract, retain an auditable per-payment exactly-once key, and
add a database-backed test for two distinct payers plus replay/concurrency
rejection. If the grant is intentionally one-shot, remove the reusable/any-
judge claim and expose consumed readiness honestly.

### T2 — P1: historical preview tests do not verify the declared immutable asset digests

`historical-demo.ts` declares `reportSha256` and `bundleSha256`, but production
code and `historical-demo.test.mjs` never use them to hash either published
asset. The test named `historical live report validates exact immutable
identity` checks selected JSON fields and report ID only; it does not verify
the exact `report.json` bytes, the ZIP bytes, or an offline bundle rebuild.
Both files can therefore be replaced while preserving the checked fields and
the suite still passes.

Required closure: hash the checked-in/public JSON and ZIP bytes against the
declared constants, run the offline verifier against the bundle/report digest,
and add byte-tamper regressions. Either enforce equivalent integrity in the UI
or describe the hashes as build/release evidence rather than runtime validation.

### T3 — P1: new wallet add-chain behavior is checked by source regex, not behavior

The new test for the EIP-4902 fallback reads `wallet.ts` and asserts string
fragments. It never invokes `switchToMezo` with a mock provider, so it cannot
detect wrong RPC/explorer/native-currency parameters, incorrect call order,
failure to re-check the chain, or accidentally swallowing non-4902 errors.

Required closure: add behavioral provider tests for successful switch,
4902 → exact add-chain → chain revalidation, user rejection, arbitrary errors,
and a wallet that remains on the wrong chain.

## Commands and evidence

```text
npm test                                      # apps/mezo-gateway
51 passed, 6 skipped (disposable PostgreSQL gate)

npm test                                      # apps/mezo-web
25 passed

npm run build                                 # apps/mezo-web
FAIL: EACCES opening node_modules/.vite-temp/vite.config...mjs

.venv/bin/pytest -q tests/operations/test_f6_static.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/contracts/test_live_grant_consumption.py
14 passed
```

The web build failure appears tied to checkout-local `node_modules` ownership,
not proven source behavior, but it means this review does not provide a fresh
successful production web build for the exact tree. The six PostgreSQL tests
remain explicitly skipped without a disposable database URL; in particular,
no current database execution disproves T1.

## Positive coverage retained

- UNKNOWN/reconcile-only and no-resettlement regressions pass.
- A transient paid-entitlement revalidation failure preserves `PAID` and does
  not settle again.
- Default payer binding remains covered; demo verification binds the quote
  payer for one payment.
- Grantless startup, grant lifetime bounds, live capture/offline report rebuild,
  private grant-file races, Compose topology, disabled-payment override, CSP,
  and resource/secret static checks pass.
- EIP-6963 selection ordering, fallback, and late provider discovery have
  executable unit coverage.

## Verdict

Do not record a passing `test_review` receipt for this fingerprint. T1 is a
release-blocking contradiction in the newly advertised paywall behavior; T2
and T3 are material coverage gaps, and the exact production web build was not
reproduced in this review environment.
