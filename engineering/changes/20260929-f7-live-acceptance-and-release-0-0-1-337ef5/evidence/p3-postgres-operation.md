# Isolated PostgreSQL migration and behavior evidence

Date: 2026-09-29. Target identity:
`docker://liqvera-f7-postgres/database/liqvera_f4_test_fdae49d`.
No database URL, password, container credential, or other secret is retained.

The user explicitly approved this one isolated disposable target and reported:

- the first migrator run applied migrations 001–004;
- the second migrator run was idempotent by exact recorded checksum;
- `npm --prefix apps/mezo-gateway run test:postgres` passed 6/6;
- twenty separate pools racing `markSubmitting` produced exactly one winner;
- a restarted adapter could not consume the same grant again;
- injected rollback left the attempt `VERIFIED` with no durable consumption;
- append-only update and delete attempts were rejected.

This closes the local disposable-PostgreSQL behavioral proof only. It is not a
grant for another database, RPC/facilitator call, wallet operation, or payment.
