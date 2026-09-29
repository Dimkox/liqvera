# Data architecture analysis — repository boundary cleanup

Route: `7f0f98e3cdda`
Base commit: `0c2cb97f8048f7da8bd193634f4502f24b0e541e`
Role: read-only `data_architect` analysis
Date: 2026-09-28

## Conclusion

This cleanup can be a **source-boundary retirement with no database migration,
backfill, data rewrite, or runtime DDL** if it preserves the active Liqvera data
surfaces listed below. Removing the obsolete Go source does not require changing
the PostgreSQL gateway ledger, the fixture-only SQLite store, any current JSON
schema/vector, fixture bytes, or the historical import manifest.

The root migration directory has mixed ownership and must not be removed as one
unit:

| Path | Ownership/status | Cleanup ruling |
| --- | --- | --- |
| `migrations/000001_init.up.sql`, `migrations/000001_init.down.sql` | Imported Stage-0 execution schema: tenants, venue credentials, order ownership, execution groups/legs/events, risk reservations, outbox and audit log | Historical Go baseline. It is outside the Liqvera report/payment boundary and may be retired with Go source. Removing the files is not permission to execute the destructive down migration. |
| `migrations/000002_a2_raw_capture.up.sql`, `migrations/000002_a2_raw_capture.down.sql` | Imported Python A2 raw-capture schema, isolated under PostgreSQL schema `a2` | Not a Go migration. Retain unless a separately scoped decision retires the A2/Stage-A data path. |
| `apps/mezo-gateway/migrations/001_ledger.sql` | Post-import Liqvera PostgreSQL payment/entitlement ledger | Active Liqvera product source. Preserve byte-for-byte in this cleanup. |
| `packages/evidence-report/migrations/001_local_demo.sql` | Post-import fixture-only SQLite demo state | Active local demo source, explicitly noncanonical for F2/payment. Preserve byte-for-byte. |

The important distinction is therefore not “root migration versus package
migration,” but schema owner and consumer. `000001` is historical execution
state; `000002` is an independently consumed A2 contract; the gateway and local
demo migrations are Liqvera-owned.

## Evidence

### Provenance and history

- `go.mod`, all 23 tracked `*.go` files, and both `000001_init` files entered
  this repository together in the initial imported baseline commit
  `8734907d489168a8a6567b93bc85920001fefd85`.
- Both `000002_a2_raw_capture` files also came from that import, but their only
  executable repository consumer is Python `scripts/a2-migrate.py`, which reads
  exactly `000002_a2_raw_capture.{up|down}.sql` using `A2_DATABASE_URL`.
- The A2 up migration creates its own `a2` schema and has no reference to the
  `000001` public-schema tables. Its down migration drops only schema `a2`.
- The Liqvera gateway ledger was added later in commit
  `c5cc3ab422329c24c9152e429cdfa77f2692c4a1`. Its build copies
  `apps/mezo-gateway/migrations/` and `src/migrate.ts` applies files from that
  directory with a recorded SHA-256, rejecting changed content after apply.
- The SQLite demo migration was added later in commit
  `dfa8fbb3c4486ec453a6c312664a70f9067c47b9`. `local_store.py` loads it as a
  package resource or source-checkout fallback, and the wheel configuration
  force-includes it.
- No executable consumer of `000001_init` exists outside historical documents
  and graph/provenance inventory. Searches of `apps/`, `packages/`, `services/`,
  `deploy/`, `scripts/`, `tests/`, `Makefile`, and `pyproject.toml` returned no
  `000001_init` reference. The tracked Go code itself does not load migrations
  or use a SQL/PostgreSQL client.
- ADR-0001 explicitly identifies the Go Stage-0 foundation as historical and
  makes its removal a separate reviewed action after Python parity. ADR-0002
  defines the Liqvera PostgreSQL ledger separately and excludes live exchange
  mutation, credentials, custody, and mainnet. The `000001` schema contains
  precisely the retired/excluded trading and credential domains.

The imported migration digests still equal their recorded
`provenance/import-manifest.json` `import_sha256` values at the base commit:

| Path | SHA-256 |
| --- | --- |
| `migrations/000001_init.up.sql` | `9ff0beed5d421af16aada0d790906d274ff9387e76b9d567f48158369cf761f8` |
| `migrations/000001_init.down.sql` | `edf3b77a6ee375995faad52d865163424d94c935035987282b20d73baa822c1f` |
| `migrations/000002_a2_raw_capture.up.sql` | `51fd413e55005752f9d19779a71bfee45a00b9c8e9a7d73320142564fba29244` |
| `migrations/000002_a2_raw_capture.down.sql` | `b373e028f9a291add6c9e10b486901f25ceff294840d353a7c37348b1ca0cf20` |

The post-import Liqvera migrations are intentionally absent from the import
manifest. Their base-commit SHA-256 values are:

| Path | SHA-256 |
| --- | --- |
| `apps/mezo-gateway/migrations/001_ledger.sql` | `bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b` |
| `packages/evidence-report/migrations/001_local_demo.sql` | `d8c7cac0d725214d42edb9ecd8a70c52d4610974fe0cb69a40f383beef77d3da` |

### Why “no data migration” is justified

The before/after runtime schemas are identical when the protected paths remain
unchanged:

1. The gateway continues to apply the same `001_ledger.sql`; no table, index,
   constraint, trigger, or migration checksum changes.
2. The local demo continues to initialize the same SQLite schema with
   `PRAGMA user_version = 1`.
3. A2 continues to apply the same isolated `000002` up/down pair through the
   same Python script.
4. Removing `000001` from the source tree does not execute either SQL file and
   no current runtime resolves or applies it. Therefore it cannot lock tables,
   rewrite rows, change a query plan, or require a backfill.
5. Repository handoff states that the F3-F7 services, containers, and
   acceptance paths have not been run or deployed by this project. This
   supports a zero repository-owned production-row assumption, but cannot
   prove that no third party ever applied an old public migration.

The conclusion is deliberately bounded: an external/local database that
previously applied `000001` is not modified by this cleanup. Do not run
`000001_init.down.sql` as part of cleanup. If such a database exists, preserve
it and handle archival/drop under a separate inventory, backup, approval, and
recovery plan.

Because no DDL or DML is executed, this change has no data-volume assumption,
query-plan/index impact, lock/downtime risk, backfill, validation query, or
database stop condition. Verification is source-identity and dependency
closure, not database mutation.

## Data invariants that must survive

### PostgreSQL gateway ledger

- PostgreSQL remains the sole payment/entitlement ledger, and the gateway
  remains its sole writer.
- Migration name and SHA-256 tracking in `gateway_migrations` remains intact;
  checksum drift must continue to fail closed.
- Scope, idempotency, authorization identity, quote/report associations, chain
  events, receipts, entitlements, and delivery/reconciliation/audit history are
  not deleted or rewritten by cleanup.
- Audit, reconciliation, receipt, and chain-event records remain append-only.
- Quote, artifact, request, authorization, and transaction identities remain
  immutable across allowed state transitions.
- Unknown/manual-review/confirmed payment state is retained; deleting ledger
  rows must never make replay possible. After payment state exists, rollback
  is stateless-binary rollback or forward recovery, never destructive database
  rollback.
- Mezo Testnet chain `31611`, the pinned MUSD asset and exact atomic amount
  constraints remain unchanged. Cleanup grants no settlement authority.

### Local SQLite demo

- It remains fixture-only and cannot become canonical F2/payment state.
- Capability bearer values are not persisted; only their digests are stored.
- Scope/idempotency uniqueness, report/quote/grant associations and append-only
  demo events remain unchanged.
- It continues to represent simulated unlock with no transfer.

### A2 and fixtures

- `000002_a2_raw_capture.*`, `scripts/a2-migrate.py`, A2 configuration and any
  current tests/fixtures stay unchanged unless A2 retirement is explicitly
  added to scope.
- Do not remove or regenerate `tests/fixtures/**`, the shadow golden NDJSON or
  its terminal hash as a side effect of removing Go. Python conformance is the
  retained executable specification for relevant invariants.
- Do not mutate `schemas/mezo-evidence/v1/**`; cleanup changes repository
  topology, not the F2 API/state/vector contracts.

### Provenance manifests

- Preserve `provenance/import-manifest.json` unchanged. It is a historical
  record of the 815-file initial import, not a current-tree lockfile. Deleting
  a file in a later reviewed commit does not falsify or require rewriting that
  record; rewriting it would instead destroy the original import evidence.
- Update `PROVENANCE.md` only to distinguish “complete at initial import” from
  later reviewed retirement and to point to Git history/external source for
  removed material. The existing sentence “No baseline file is omitted” is
  valid only in its explicitly stated initial-import context and should not be
  presented as a current-tree inventory after cleanup.
- Remove obsolete paths from the current architecture repository inventory and
  graph bindings when their tracked files are deleted. That current inventory
  is separate from the immutable import manifest.

## Required implementation guardrails and checks

1. Limit data-adjacent deletions to `migrations/000001_init.*` if the cleanup
   elects to retire the Stage-0 schema. Never delete the whole `migrations/`
   directory.
2. Assert the three retained migration surfaces exist and keep their
   base-commit digests, unless a separately reviewed defect forces a change.
3. Assert `scripts/a2-migrate.py` still resolves only `000002_a2_raw_capture`.
4. Assert the gateway build still copies its migration directory and the demo
   wheel still packages `001_local_demo.sql`.
5. Assert no tracked `*.go`/`go.mod` remains if full Go retirement is the
   accepted scope, and that no product artifact or verification command tries
   to compile Go.
6. Run graph/inventory checks after removing the obsolete current-tree
   bindings; keep the provenance manifest bound as a documentation artifact.
7. Run focused local-store tests, F2 contract/state/vector tests, migration
   resource/package tests, and the route's full PR verification. No test may
   apply `000001_init.down.sql` to a database.
8. Inspect the final diff and confirm there are no changes under
   `apps/mezo-gateway/migrations/`, `packages/evidence-report/migrations/`,
   `schemas/mezo-evidence/v1/`, or `tests/fixtures/`, and no content change to
   `provenance/import-manifest.json`.

## Rollback / forward recovery

Rollback is a Git revert of the repository-boundary commit. It restores source
and graph/docs references only; it performs no database restore. No schema
rollback is appropriate because this cleanup applies no schema change.

If final implementation changes any protected migration/schema/fixture or
executes DDL, the “no data migration” conclusion becomes invalid and the
change must return to data review with explicit before/after schema, migration
ordering, lock analysis, backup/restore, validation queries, and forward
recovery evidence.

## Commands used

Read-only evidence included `git status`, `git log -- <paths>`, `git ls-files`,
`git ls-files -s`, `rg` consumer/reference searches, `sha256sum`, and `jq`
selection of import-manifest entries. No database was contacted and no
migration was applied.
