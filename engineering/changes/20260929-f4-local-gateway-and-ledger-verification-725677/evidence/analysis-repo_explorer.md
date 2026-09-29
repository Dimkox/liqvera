# Repository exploration: F4 local gateway and ledger

Date: 2026-09-29
Candidate: `c30b0ffbda6cbae37b9dec16da2dec1346b0248b`
Route: `725677143509`

## Outcome

F4 is not buildable from its documented factory target and has no executable
gateway test suite. The SQL foundation applies successfully to a disposable
PostgreSQL 17 database, but a confirmed cross-component cleanup contract defect
can leave an artifact ledger row permanently `AVAILABLE` after the files were
already removed. These are reproducible local defects, not external-service
blockers.

## Reproductions

### 1. Canonical gateway factory fails

Environment: Node `v24.21.0`, npm `11.19.0`; gateway `node_modules` was absent
before the run.

```text
$ make liqvera-gateway
...
apps/mezo-gateway/src/adapters/contracts.ts(9,57): error TS2349
  Type 'typeof import(".../ajv-formats/dist/index")' has no call signatures.
apps/mezo-gateway/src/main.ts(25,168): error TS2345
  ... sourceMode: string ... is not assignable to ... "live-public" | "fixture".
make: *** [Makefile:61: liqvera-gateway] Error 2
```

The factory correctly builds `packages/mezo-protocol` first. A direct
`npm run typecheck` before that prerequisite also reports the expected missing
local-package declarations; that is not a separate product defect. After the
factory builds the protocol package, the two errors above remain authoritative.

Likely minimal repairs:

- normalize the CommonJS `ajv-formats` export before calling it under the
  repository's `NodeNext` configuration;
- give `loadConfig` an explicit return type (or otherwise preserve the narrowed
  `sourceMode` union) so it satisfies `GatewayConfig`.

There is no `test` script in `apps/mezo-gateway/package.json` and no gateway
test/spec file under `apps/mezo-gateway` or the root `tests/` tree. Existing
Python contract tests validate the frozen schemas, not the Express, adapter,
worker, or PostgreSQL behavior.

### 2. Lost cleanup response is not recoverable

The service and gateway disagree on the idempotent success result:

- `packages/evidence-report/src/mee_evidence_report/evidence_bundle.py` returns
  `False` when the exact report directory is already absent.
- `packages/evidence-report/src/mee_evidence_report/service.py` returns that as
  HTTP 200 `{ "report_id": ..., "deleted": false }`.
- `services/evidence-report/README.md` explicitly says this response permits
  recovery after a lost response.
- `apps/mezo-gateway/src/adapters/report-service.ts` treats only
  `deleted === true` as cleanup success.
- `apps/mezo-gateway/src/workers/retention.ts` changes `storage_state` to
  `DELETED` only when the adapter returns true.

Therefore: the first DELETE may remove both files and its response may be lost;
the retry receives `deleted:false`; the gateway refuses to commit `DELETED` and
retries the already completed deletion every 30 seconds while the ledger still
claims `AVAILABLE`. A database commit failure after successful deletion has the
same outcome. The repair should accept a strictly validated matching HTTP 200
response with either boolean value as proof that the exact target is absent,
while still rejecting malformed IDs/bodies and all error responses.

Required regression: a fake internal report service returns `deleted:true` on
the first call whose response is dropped, then `deleted:false`; the second
retention pass must atomically mark only the matching artifact `DELETED` and
append exactly one removal audit event. Add negative cases for mismatched
`report_id`, non-boolean `deleted`, non-2xx, malformed JSON, and timeout.

### 3. Disposable PostgreSQL migration baseline is green

A local `postgres:17-alpine` container was created without a host port, the
tracked `001_ledger.sql` was applied with `psql -v ON_ERROR_STOP=1`, and the
container was removed. Result: exit 0, 12 public tables and 11 non-internal
triggers. This proves the current SQL parses and installs on PostgreSQL 17; it
does not prove the TypeScript migration runner, idempotency races, state
transitions, or rollback/recovery behavior.

No new migration is indicated for the confirmed defects. Do not edit the
already applied `001_ledger.sql`; keep the repair in TypeScript and tests unless
a new schema defect is independently demonstrated.

## Dependency/audit observation

`npm ci --ignore-scripts` completes, but reports 32 advisories: 28 moderate and
4 high. `npm audit --json` confirms those totals; the high findings are
transitive in the current x402/paywall wallet dependency graph, including
`ws`. The root README currently records 29 moderate and 3 high, so that prose
is stale. `npm audit fix --force` proposes a breaking downgrade and must not be
run as an F4 repair. Treat the audit as retained release-risk evidence, not as a
reason to broaden this local F4 tranche into dependency migration.

## Minimum executable verification slice

The implementation owner should add a Node test runner and run it against a
disposable PostgreSQL 17 container, with no RPC/facilitator/payment/network
calls. At minimum cover:

1. clean protocol + gateway build and typecheck;
2. migration runner first apply, second no-op, and checksum mismatch rejection;
3. schema-valid health/readiness/capability and fail-closed fixture responses;
4. capability scope isolation and same-key same-body/different-body behavior;
5. at least 20 concurrent identical creates yielding one request/report ID and
   one scoped budget charge;
6. maximum four build claims and lease/state behavior;
7. artifact-integrity transition to `RECOVERY` without delivery;
8. cleanup success, lost-response/already-absent recovery, malformed cleanup
   response rejection, and exclusion of active/uncertain/paid attempts;
9. database assertions for dedup, foreign keys, append-only rows, immutable
   identities, and permitted/forbidden transitions.

Keep all payment ports as fail-closed fakes and assert zero settle calls. The
container must use an ephemeral local database and be removed with an explicit
absence check.

## Commands executed

```text
npm ci --ignore-scripts                         PASS (32 advisories)
npm run typecheck                               FAIL (pre-protocol: 4 errors)
npm run build                                   FAIL (pre-protocol: 4 errors)
make liqvera-gateway                            FAIL (2 persistent errors)
npm audit --json                                exit 1 by advisory policy; 28 moderate, 4 high
psql -v ON_ERROR_STOP=1 < 001_ledger.sql        PASS on disposable PostgreSQL 17
```

The disposable database container was stopped and removed. Generated
`node_modules`/`dist` directories are ignored build artifacts; no tracked
product file was changed by this exploration.
