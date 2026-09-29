# Data architecture analysis — F3–F7 verification and defect repair

Route: `f6f2495b4648`
Base commit: `f07562eee1a33df74768e9fa4a3b074783d8c59e`
Role: read-only `data_architect` analysis
Date: 2026-09-29

## Result

The data verification phase should use only throwaway PostgreSQL databases,
temporary SQLite files, temporary artifact/capture roots, and in-process mocked
payment/RPC/report-service ports. It must not contact a facilitator, chain RPC,
exchange, shared database, deployed Compose project, or persistent volume.

The current change has a **no-migration default**. Verification and ordinary
TypeScript/Python defect repairs do not justify changing either committed
migration. If a database invariant cannot be repaired without DDL, do not edit
`001_ledger.sql` in place: its SHA-256 is recorded by `gateway_migrations`, so
an edit would deliberately break every database that already applied it. Add a
forward-only `002_*.sql` only after the route's
`migration_or_external_write_approval` gate, with explicit lock, compatibility,
and forward-recovery evidence.

No database, container, network service, or migration was run during this
analysis. All observations below are static evidence and proposed tests, not
runtime acceptance.

## Sources of truth and ownership

| Data | Source of truth | Writer | Recovery/replay rule |
| --- | --- | --- | --- |
| Quote, payment attempt, chain event, receipt, entitlement, delivery and audit state | PostgreSQL gateway ledger | Gateway only | Preserve ambiguous and confirmed state; never infer unpaid or resettle from a timeout |
| Published report and bundle bytes | Immutable artifact directory, bound by recorded SHA-256/size | Report service only | Recover only from retained sealed input and only to the original digest; current recovery adapter deliberately returns false |
| Raw capture evidence | Per-capture sealed directories | Capture service only | Never replace live failure with fixture data; retain inputs needed for artifact recovery |
| Local browser demo state | SQLite `user_version=1` database | `LocalDemoFlow` only | Fixture-only, simulated unlock, no payment or canonical F2 state |
| F2 expected semantics | `states.json`, `vectors.json`, OpenAPI and schemas | Contract artifacts | They are oracles, not runtime evidence; all 156 vectors remain `runtime_status=NOT_RUN` at the base commit |

Base-commit identities to bind in before/after evidence:

| Artifact | SHA-256 |
| --- | --- |
| `apps/mezo-gateway/migrations/001_ledger.sql` | `bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b` |
| `packages/evidence-report/migrations/001_local_demo.sql` | `d8c7cac0d725214d42edb9ecd8a70c52d4610974fe0cb69a40f383beef77d3da` |
| `schemas/mezo-evidence/v1/states.json` | `142b29782d2f9169a3351af3150e5cb9ee66d1412a04ce060f0bf2739908c9fc` |
| `schemas/mezo-evidence/v1/vectors.json` | `606a4a2a406c71456aa0ade984f613c10bdef46a6ac020a953b8d3b6386717cc` |

## Current coverage gaps and likely defect targets

### P0 — runtime data behavior is untested

There are no gateway test/spec files in `apps/mezo-gateway` and no repository
tests that execute `Ledger`, the migration runner, the gateway workers, or the
PostgreSQL schema. The eight idempotency, fifteen recovery, and three artifact
vectors are exercised only by a Python policy oracle; they do not touch the
TypeScript implementation. Likewise, current `tests/evidence_report/` covers
the earlier MVP builder/CLI, not `LocalDemoStore`, `LocalDemoFlow`, the canonical
F3 artifact publisher/deleter, or the internal report service.

This is the primary evidence gap. Typecheck/build success cannot close F4/F5
data acceptance.

### P0 — lost cleanup response is not actually recoverable

The report service intentionally returns
`{"report_id":"…","deleted":false}` when an authorized cleanup retry finds the
directory already absent. Its README says this supports recovery after a lost
response. `HttpReportService.cleanup`, however, returns true only for
`deleted===true`; the retention worker therefore never changes the ledger
artifact from `AVAILABLE` to `DELETED` after the classic sequence “delete
committed, response lost, retry observes absent.” It retries forever and leaves
filesystem/ledger state inconsistent.

This is fail-closed rather than a paid-data leak, but it is a concrete recovery
defect. Add a failing test for the lost-response sequence before repair. The
repair must accept only an authenticated, exact-report-id response whose
semantics explicitly prove “deleted or already absent”; it must not treat an
arbitrary false/error response as deletion authority.

### P1 — schema protection and adapter exactness need characterization

- Receipts and chain/reconciliation/audit events have database immutability
  triggers. Entitlements have uniqueness/FKs but no update/delete guard. The
  current code has no entitlement deletion path, so indefinite retention is
  safe, but a direct regression by the sole writer is not blocked at the
  database boundary. Characterize the expected policy before deciding whether
  code-only tests suffice or a new forward migration is required.
- `confirmation()` converts PostgreSQL `bigint` `block_number` to JavaScript
  `Number`; the JSON schema has no maximum. Test the exact supported boundary
  or retain it as an exact decimal/integer string until schema-safe conversion.
- Artifact scalar identity (digest/size) is duplicated inside `metadata` JSON.
  Inserts currently originate from one `Artifact` object and identity triggers
  prevent later edits, but tests should prove scalar and metadata copies cannot
  diverge through supported writes.
- `ImmutableArtifacts` validates a directory path and later opens a
  path-derived child; it is not descriptor-relative. The normal architecture
  gives the gateway a read-only mount and cleanup excludes paid artifacts, but
  hostile replacement/symlink races should be exercised in a temporary root.
  Any failure must return `ARTIFACT_INTEGRITY_FAILURE`, never external bytes.

These are test/design findings. Except for the lost-response cleanup mismatch,
they are not yet reproduced defects.

## PostgreSQL schema invariants

The real PostgreSQL suite must prove the schema, application transaction, and
mock-port behavior together.

### Identity and uniqueness

- One `report_request` per `(scope_hash, idempotency_key)`; same canonical body
  returns the same request/quote, a changed body returns 409, and the same key
  in another scope is independent.
- One globally unique canonical `authorization_identity`; different wire
  encodings of the same authorization cannot create another attempt.
- At most one non-rejected attempt per quote via `one_active_attempt`.
- One chain event per `(chain_id, tx_hash, log_index)` and one chain event per
  payment attempt.
- One receipt and entitlement per payment attempt/quote, bound to the exact
  `report_id`, `scope_hash`, and `report_sha256`.
- Quote constants remain exact: `eip155:31611`, chain `31611`, pinned test MUSD,
  atomic amount `10000000000000000`, nonzero distinct payer/payee.

### State and atomicity

- Every permitted transition matches `states.json`; every other direct update
  fails. State `version` increments exactly once per transition.
- `SUBMITTING` and `SUBMIT_COMMITTED` are durable before the sole mocked settle
  call. No recovery or HTTP replay path invokes settle again.
- Chain event, receipt, entitlement, attempt `CONFIRMED`, quote `PAID`, and the
  entitlement audit event commit atomically. Fault injection after every SQL
  boundary must leave either none of them or all of them.
- A confirmed transaction after quote expiry still binds the original report.
  Expiry prevents only a new payment start.
- A timeout/no hash, ambiguous matching transfers, RPC conflict, or crash after
  submit remains `UNKNOWN`/`PAYMENT_UNCERTAIN` or enters `MANUAL_REVIEW`; it
  never becomes READY/unpaid and never produces a second settlement.
- A stale `RECEIVED`/`VERIFIED` attempt may return the quote to READY/EXPIRED
  only with authoritative no-submit semantics; stale `SUBMITTING` may not.
- Paid delivery is recorded only while quote=PAID, attempt=CONFIRMED,
  entitlement is unexpired and digest/scope bindings match.

### Retention and immutability

- Updates/deletes of audit, reconciliation, receipt and chain-event rows fail.
- Quote terms, report/request identity, artifact digest/size/metadata,
  authorization identity/correlation and a non-null transaction association
  cannot be changed.
- Ledger/scope/dedup rows are never deleted by current retention work. They are
  retained indefinitely, which satisfies the 30-day and authorization-validity
  minimum until a separately reviewed deletion policy exists.
- Unpaid artifact deletion is eligible only after quote expiry plus 15 minutes,
  only with `storage_state=AVAILABLE`, no entitlement, and no payment attempt
  except REJECTED. `SUBMITTING`, `UNKNOWN`, `MANUAL_REVIEW`, PAID, and entitled
  reports must never be selected.
- Paid artifact corruption sets `RECOVERY`, appends an audit event, withholds
  the body, closes new sales, and performs zero settlement calls. Current
  `recover=false` keeps it blocked rather than rebuilding from fresh data.

### Migration runner

- On a fresh database, one advisory-lock owner applies `001_ledger.sql` in one
  transaction and records the exact name/SHA only after success.
- A second run is a no-op; a changed copy of an already recorded migration
  fails checksum verification without DDL.
- Concurrent migrators serialize and produce one migration-ledger row.
- A synthetic failing migration rolls back all of its DDL and does not record
  its checksum. Use only a copied temporary migration directory/test harness;
  never alter the repository file to create the failure.
- Test on the supported PostgreSQL majors selected by the project (at least
  pinned 16 and 17 ephemeral instances). Bound the advisory-lock test itself
  with a harness timeout so a wedged session cannot hang CI.

## SQLite demo invariants

Use a unique temporary directory per test; never open `.mvp/store/ledger.sqlite3`.

- Empty DB migrates to `PRAGMA user_version=1`; reopen is idempotent; any other
  version fails closed without rewriting it.
- Foreign keys are enabled on every connection. Scope/request/report/quote/grant
  uniqueness and append-only `demo_events` triggers reject invalid mutation.
- Only the capability digest is persisted, never the bearer capability.
- Twenty concurrent identical create calls converge to one logical run and one
  immutable artifact; same key/different body conflicts; same key in another
  capability scope is isolated.
- Replaying after a lost response returns the same run/report/quote. Concurrent
  simulated unlock uses one grant/action; changed or cross-quote reuse
  conflicts and always reports `NO TRANSFER`.
- Expiry produces one terminal event and never unlocks. Foreign capability and
  guessed UUID reads return no report bytes.
- Missing, digest-mismatched, symlinked, non-regular and oversized artifacts
  fail closed. The current reader has no explicit byte limit, so add a bounded
  read test and repair if it can allocate an unbounded tampered file.
- Characterize crash after artifact rename but before SQLite commit. Ordinary
  exceptions remove the new directory, but process death can leave an orphan;
  it must never become an entitled run or overwrite another report.

The demo database is intentionally not migrated into PostgreSQL and must never
be used as payment evidence.

## Artifact-store matrix

All cases use temporary roots and synthetic bytes only.

| Case | Required result |
| --- | --- |
| Publish valid report/bundle twice under distinct roots | Byte-identical report and ZIP; exact recorded hashes/sizes/modes |
| Publish same report ID twice | Second publish rejected; original bytes unchanged |
| Crash/fault before rename | No visible ready directory; hidden staging is not readable as published |
| Report or bundle missing, truncated, extended, same-size modified | Read fails integrity; no paid body and no settlement |
| Report directory/file symlink, FIFO/device, unexpected member/subdirectory | Read/delete rejects without traversal or recursive removal |
| Concurrent read versus allowed cleanup/replacement | Either original verified bytes or integrity failure, never bytes outside root |
| Cleanup success response lost, then retry sees absent directory | Ledger reaches `DELETED` exactly once and records one effective cleanup decision |
| Cleanup response malformed/wrong ID/unauthorized/timeout/409/503 | Ledger stays non-DELETED; no unrelated path changes |
| Paid or uncertain report presented to cleanup worker | Not selected; all files and ledger rows retained |
| RECOVERY artifact with current adapter | Remains RECOVERY and sales stay closed; no fresh-snapshot rebuild |

## Safe offline execution matrix

| Phase | Environment | Minimum evidence | External effects |
| --- | --- | --- | --- |
| Static contracts | Repository files only | 156 vectors/schema/state graphs pass; runtime status remains honest until mapped runtime tests execute | None |
| Python unit/fault | `tmp_path`, no sockets except loopback test servers | Canonical F3 bundle tamper, publish/read/delete, report-service authentication/idempotency, SQLite matrix | Temporary files only |
| Gateway unit/fault | Built JS, fake `PaymentPort`, fake RPC/report service, temporary artifact root | 402/no-body, exact terms, no-settle replay, timeout/crash/ambiguous/reorg, redaction | No network; no real signatures or funds |
| PostgreSQL integration | Fresh randomly named DB or disposable container per shard; no host/shared volume | Clean/repeat/checksum migration, constraints/triggers, 20-way races, atomic confirmation, recovery/retention queries | Ephemeral DB only; destroy after captured result |
| Offline E2E | Fixture capture/report/gateway on loopback or isolated fixture Compose project with unique name and anonymous/temp volumes | A02–A06, A08–A12, A15–A25 where mocks suffice; original digest across repeat access | No public ports, egress, chain, facilitator or exchange |
| Acceptance orchestration | `--mode offline`, fresh evidence directory, clean bound tree | Honest PASS/FAIL/NOT_RUN; A07/A13/A14/A29/A30 remain blocked/not-run as applicable | Evidence files only |

For PostgreSQL parallelism, run at least:

1. 20 identical `(scope,key,body)` creates: one request/build/quote.
2. 20 conflicting bodies under one `(scope,key)`: one winner, all others 409,
   no extra artifact/quote.
3. 20 payment attempts for one quote, including same canonical identity with
   varied encoding: one active durable attempt and at most one mock settle call.
4. 20 build/reconciliation/retention worker claims: `SKIP LOCKED` prevents
   duplicate work and global build leases never exceed four.

Use deterministic barriers rather than timing sleeps. After each race, query
row counts, state/version, unique identities, audit event sequence, and mock
call count. A passing HTTP result alone is insufficient.

## Migration / no-migration decision boundary

Remain **no migration** when repairs are confined to adapters, workers,
filesystem safety, tests, observability, or stricter application validation and
the existing schema already rejects every invalid durable state.

Require a proposed `002_*.sql` and explicit approval if verification proves a
missing database constraint/index/trigger, changes a column/type/state, or
requires persisted repair metadata. For such a proposal record:

- exact schema before/after and compatibility with the old binary;
- row-volume assumptions and catalog validation queries;
- lock level/duration, statement/lock timeout and index-plan impact;
- whether existing rows can violate the new constraint;
- bounded/resumable backfill or proof that none is needed;
- fail/stop conditions and transaction behavior;
- forward recovery. Do not provide a destructive down migration for payment
  evidence.

Changing `001_ledger.sql` in place is prohibited once any ephemeral or external
database has recorded its current checksum. If the project conclusively elects
to squash before first deployment, that is a separate reviewed release decision,
not an incidental bug repair.

## Rollback and recovery

- Test databases and temporary stores are destroyed only after results and
  relevant sanitized logs/digests are captured. Never use an unresolved path or
  shared Compose project/volume as the deletion target.
- With no migration and no external deployment, rollback is a Git revert of the
  coherent code/test commit; runtime data is untouched.
- If a forward migration is approved and run, do not restore an older ledger or
  run destructive down SQL. Stop new quotes, preserve ledger plus capture and
  artifact volumes, roll back only schema-compatible stateless binaries, and
  forward-fix.
- Unknown/manual-review/confirmed attempts, authorization dedup associations,
  receipts, entitlements, audit events and original artifact digests survive
  every rollback.
- Artifact recovery never recalculates from a fresh market snapshot and never
  requests another payment. Until sealed-input recovery is implemented and
  proves the prior digest, `RECOVERY` remains an incident state.

## Exit criteria for data review

1. Scope/design gate is approved before implementation; the migration/external
   write gate remains closed unless a precise `002` proposal is accepted.
2. Every discovered defect has a deterministic failing regression and minimal
   repair by the single write owner.
3. PostgreSQL 16/17 ephemeral suites and SQLite/artifact temporary-root suites
   pass from a clean final tree; commands and outputs are fingerprint-bound.
4. Runtime tests map each relevant F2 idempotency/recovery/artifact vector to
   actual code. Unexecuted live vectors remain `NOT_RUN` or `BLOCKED_EXTERNAL`.
5. Final diff explicitly confirms whether migration hashes changed. Any change
   invalidates this no-migration analysis and requires renewed data review.
6. Independent data/security reviewers inspect the final SQL, transaction
   boundaries, race results and recovery evidence; the implementer does not
   self-approve.

## Evidence collection

Read-only inspection covered the active route/change package, repository
continuity documents, canonical specification, accepted data/payment boundary,
gateway SQL and migration runner, PostgreSQL adapter/workers, SQLite migration
and flow, artifact publisher/reader/deleter, report service, Compose/runbooks,
F2 state/vector fixtures and current test inventory. Commands used `git`, `rg`,
`sed`, `jq`, `find`, and `sha256sum`. No completion, test pass, database state,
settlement, deployment, or acceptance result is claimed here.
