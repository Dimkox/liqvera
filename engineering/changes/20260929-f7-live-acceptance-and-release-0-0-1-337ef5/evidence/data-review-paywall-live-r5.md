# Independent data review R5 — final migration/installer boundary

Status: **PASS**
Reviewed commit: `95d438bad1e6bb56a74498c609585546c314cb38`
Reviewed tree: `419edfbc6ba05109fa63e4be522087475f68ca1c`
Prior passing review: `data-review-paywall-live-r4.md`

## Verdict

`DATA-002` remains closed. The published v0.0.2 installer is correctly restored
to its immutable migration 001–005 contract, while the current live gateway and
migrator retain migration 006 as an independently pinned forward migration.
The installer freeze does not delete, downgrade, or reinterpret live signed-v2
authority data. No blocking data finding remains.

## Persistence invariants revalidated

- Migration 006 remains present at the pinned SHA-256
  `92e346b3fa49699b20d9edca9814d17bde4fb96046e71071c68b0c47326ef18a`
  in the live gateway migration policy.
- Signed-v2 availability still reads durable authority/reservation rows.
  Authority-row locking, bounded ordinal/amount checks, per-payer uniqueness,
  atomic reservation plus `SUBMITTING`, restart persistence, exhaustion, and
  append-only triggers are unchanged from R4.
- V1 remains on the independent one-shot `live_grant_consumptions` path.
- The issuer-pinning repair changes grant admission, not database semantics: an
  unapproved runtime key cannot activate v2 authority, while the approved key
  must match both the compiled allowlist and envelope key ID.

## Installer/live migration separation

- `installer/manifests/v0.0.2.json`, its schema, lifecycle validator, builder,
  verifier, and installer tests again contain exactly migrations 001–005. This
  preserves the already-published v0.0.2 archive and its pinned historical
  runtime images; it does not claim that package can run signed-v2 behavior.
- Migration 006 remains in `apps/mezo-gateway/migrations` and in
  `APPROVED_MIGRATIONS`, so the current live deployment migrator still requires
  and applies the exact 001–006 prefix before starting the signed-v2 gateway.
- No down migration or cleanup was introduced. The rollback contract now
  explicitly preserves authority rows, reservations, ordinals, payer records,
  amount/count debits, and UNKNOWN reservations when application code is rolled
  back.
- A future installable package supporting signed-v2 must use a new package
  identity and migration contract; the v0.0.2 freeze cannot be widened in place.

## Verification evidence

Executed at the reviewed commit/tree:

```text
.venv/bin/python -m pytest -q \
  tests/installer/test_contracts.py \
  tests/contracts/test_signed_grant_authority.py
```

Result: **8 passed**.

```text
npm test --prefix apps/mezo-gateway
```

Result: **51 passed, 0 failed, 7 skipped**. The seven skips remain the explicitly
gated disposable-PostgreSQL tests, including live migration-006 concurrency and
restart execution. No approved disposable database URL was available.

## Decision

Data review passes for commit
`95d438bad1e6bb56a74498c609585546c314cb38` / tree
`419edfbc6ba05109fa63e4be522087475f68ca1c`. Record a passing receipt only while
this exact repository/spec binding remains current.
