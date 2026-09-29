# Isolated PostgreSQL migration and behavior evidence

Date: 2026-09-29. No database URL, password, container credential, or other
secret is retained. These facts authorize neither payment nor another target.

## Retained migration-evidence database

Exact target:
`docker://liqvera-f7-postgres/database/liqvera_f4_test_fdae49d`.

- Preflight found `receipts=0` and exact migrations 001–004.
- Approved migration 005 was applied with checksum
  `e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11`.
- A second migrator invocation was idempotent.
- `receipts.confirmations` is PostgreSQL `int4 NOT NULL` with a check requiring
  `confirmations >= 12`.
- The migration ledger contains exact checksums 001–005 listed below.
- The post-operation receipt count remains zero.

An attempted `test:postgres` reuse of this retained database failed because the
suite intentionally expects a fresh database and creates fixed upgrade rows;
this was not a migration failure. The database was not cleaned or repurposed,
so its retained migration evidence remains intact.

## Fresh behavioral-verification database

Separately approved exact target:
`docker://liqvera-f7-postgres/database/liqvera_f4_test_9c86bf9_verify`.

The fresh disposable database ran `test:postgres` 6/6 PASS, including fresh
001–005 migration/idempotency, twenty separate pools with exactly one
`markSubmitting` winner, zero additional winner after adapter restart,
transaction rollback preserving `VERIFIED` with no grant consumption, and
append-only update/delete rejection.

## Exact migration ledger

- `001_ledger.sql`: `bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b`
- `002_fix_immutable_ledger_identity.sql`: `981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb`
- `003_live_grant_consumption.sql`: `bbedff6137a648166b77233c56a466e46247480b404b8829b64f29123109bcf0`
- `004_receipt_confirmation_provenance.sql`: `96bba00d344d81670a4c0f8741186004910e959f374ecd77ce78268d52fd465a`
- `005_receipt_confirmation_count.sql`: `e99e5cffab60c08dfb1cd73d13caf2915f31aec542c26c87b016d0e125a23b11`
