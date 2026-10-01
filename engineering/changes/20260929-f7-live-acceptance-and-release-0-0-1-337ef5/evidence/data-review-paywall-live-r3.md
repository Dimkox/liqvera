# Independent data review R3 — public testnet demo persistence

Status: **FAIL**
Reviewed commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`
Reviewed tree: `75151ba8b154b72fd77d3df844beb4d3eca89dac`
Scope: schema compatibility, grant consumption, quote/attempt state, entitlement
revalidation, and persistence evidence added after R2.

## Blocking finding

### DATA-002 — demo-any-payer readiness contradicts the one-shot grant ledger

Severity: **HIGH** (blocks data-review approval)

The opt-in public demo makes `OfficialX402.liveGrantDigest` return `undefined`
when `demoAnyPayer` is enabled (`apps/mezo-gateway/src/adapters/x402.ts`). This
intentionally removes the configured grant from `Gateway.currentBlockers()` and
is documented in code as making demo authority reusable across independently
guarded quotes.

The durable payment path remains one-shot, however. `verify()` still copies the
same grant byte digest and `grant_id` into every authorization correlation, and
`Ledger.markSubmitting()` still inserts those values into
`live_grant_consumptions`. Migration 003 has unique constraints on both
`grant_digest` and `grant_id`. Consequently:

1. the first quote consumes the grant and may settle;
2. readiness and capabilities continue to advertise payment ready because the
   consumption lookup has been disabled for demo mode;
3. a later payer can receive payment requirements and pass external
   verification/native-balance observation;
4. only `markSubmitting()` discovers the durable conflict, rejects the attempt,
   reopens the quote, and returns `PAYMENT_NOT_READY`.

No duplicate settlement is created—the database remains fail-closed—but the
published readiness/state projection is false after the first payment and the
claimed reusable demo authority does not exist. This is a persistence contract
regression, not merely a UI issue. The current tests cover arbitrary-payer
verification and the ordinary consumed-grant projection separately, but do not
exercise a consumed grant while `demoAnyPayer=true`.

Required repair: choose and encode one coherent model.

- If a demo grant remains one-submit, expose its digest to
  `currentBlockers()` and return `EXTERNAL_GRANT_REQUIRED` immediately after
  durable consumption, including in any-payer mode.
- If the intended authority is reusable, introduce a separately reviewed grant
  schema/version and durable bounded budget keyed to the intended unit (for
  example per authorization/quote/payer plus an explicit total cap). Do not
  reuse a grant that still declares `maximum_settlement_submissions=1`, and do
  not remove the authoritative database consumption check.
- Add a real state-path regression: consume one demo grant, restart the adapter,
  then assert readiness and a second quote match the selected contract without
  a false-ready interval or an unbounded settlement path.

## Other reviewed persistence behavior

- No SQL migration file changed. Migrations 001–005 and their pinned checksums
  remain internally consistent and preserve append-only grant, audit, chain,
  receipt, and entitlement evidence.
- The R2 loser transition remains atomic: a unique-consumption loser becomes
  `REJECTED`, its quote returns to `READY`, and the audit row is written in the
  same transaction. No stranded `VERIFIED/PAYMENT_PENDING` state was
  reintroduced.
- The transient RPC revalidation repair is sound. A missing read-only
  observation now returns `PAYMENT_UNCERTAIN` without mutating durable
  `PAID`/`CONFIRMED` state or resubmitting. An observed receipt mismatch still
  returns `false` and enters `MANUAL_REVIEW` through the existing gateway path.
- Authorization identity uniqueness, quote row locking, `SUBMITTING` before
  external settlement, and `UNKNOWN` confirm-only reconciliation remain intact.

## Verification

Commands executed at the exact reviewed commit/tree:

```text
npm test --prefix apps/mezo-gateway
```

Result: **51 passed, 0 failed, 6 skipped**. The skipped tests require an
explicitly disposable PostgreSQL URL.

```text
.venv/bin/python -m pytest -q tests/operations/test_f6_static.py
```

Result: **5 passed**.

These green suites do not close DATA-002 because no test combines demo-any-payer
mode with an already persisted migration-003 consumption row.

## Decision

Do not record a passing `data_review` receipt for this tree. Record this review
as failed, repair the authority/persistence mismatch, and re-review the exact
new commit and tree.
