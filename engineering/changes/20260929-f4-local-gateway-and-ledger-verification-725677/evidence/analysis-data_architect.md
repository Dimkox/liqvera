# F4 data architecture analysis

Route: `725677143509`
Source inspected: branch `feat/f3-f7-verification`, HEAD at analysis time `c30b0ff`
Disposition: **no migration required; preserve `001_ledger.sql` byte-for-byte**

## Evidence and ruling

`apps/mezo-gateway/migrations/001_ledger.sql` has SHA-256
`bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b`, exactly the
value pinned by `tests/conformance/test_repository_boundary.py`. The working
file also matches the committed blob. The scoped F4 defect can be repaired in
the report-service/gateway cleanup contract and tested against a fresh
disposable database; it does not require a table, constraint, index, trigger,
or data rewrite.

Do not edit the applied `001_ledger.sql`. If a later, separately approved
finding truly requires a schema change, add a forward-only `002_*.sql` and
retain the migration checksum ledger. No such finding exists in this scope.

## Confirmed defect: lost cleanup response is not recoverable

The retention worker selects only expired, unpaid `AVAILABLE` artifacts, calls
the private report service, and marks the ledger `DELETED` only when
`cleanup()` returns true (`apps/mezo-gateway/src/workers/retention.ts:7-17`).
The gateway adapter accepts only the exact response
`{"report_id": id, "deleted": true}`
(`apps/mezo-gateway/src/adapters/report-service.ts:34-39`). The report service
returns the boolean from `delete_published()`
(`packages/evidence-report/src/mee_evidence_report/service.py:224-248`), while
`delete_published()` returns false when the directory is already absent
(`evidence_bundle.py:251-274`).

Therefore this sequence is permanent:

1. report service deletes the files;
2. its successful HTTP response is lost;
3. the database transaction rolls back or never reaches the `DELETED` update;
4. every retry observes an absent directory and returns `deleted:false`;
5. the ledger remains `AVAILABLE` forever although storage is absent.

This violates idempotent reconciliation and produces an unbounded retry loop.
It is not a schema defect. The repair should make the private delete operation
idempotently acknowledge the desired end state for a valid selected report ID
(including already absent), while continuing to reject links, unexpected
members, invalid identifiers, authentication failures, and storage errors.
Regression coverage must explicitly simulate deletion followed by response
loss and prove that the next retry advances the ledger to `DELETED` without
removing any ledger/dedup row.

## Ledger invariants to preserve

- `access_scopes` and `(scope_hash, idempotency_key)` remain durable replay and
  tenant-scope boundaries. Retention must never delete either scope or request
  rows.
- `report_id` is unique across requests, artifacts, and quotes; artifact and
  entitlement foreign keys bind the exact report digest and scope.
- Request, quote, and payment transitions remain trigger-enforced; immutable
  quote terms, request identity, artifact identity, authorization identity,
  transaction association, receipts, chain events, reconciliation events, and
  audit events must not be weakened.
- One non-rejected payment attempt per quote and global authorization identity
  uniqueness remain the replay barriers.
- Receipt, chain event, entitlement, confirmed attempt, and paid quote remain
  one database transaction. Recovery must never resubmit settlement.
- Expired unpaid cleanup may change only `artifacts.storage_state` to `DELETED`
  and append its audit event. It must exclude all non-rejected payment attempts
  and every entitlement.
- Storage absence is not permission to delete ledger identity. Rollback after
  payment state exists is stop-new-sales plus forward repair, never table drop
  or restoration over newer authorization records.

## Concurrency and locking assessment

The main concurrency mechanisms are coherent for the intended small local
deployment:

- request creation uses the unique `(scope_hash,idempotency_key)` constraint,
  conflict-ignore insertion, and `FOR UPDATE` readback; concurrent identical
  bodies converge, while a different body returns `IDEMPOTENCY_CONFLICT`;
- build claims are serialized across replicas by transaction advisory lock
  `(31611,4)`, bounded to four live leases, and select work with
  `FOR UPDATE SKIP LOCKED`;
- quote/payment mutations consistently lock the quote before the attempt in
  transactional mutation paths;
- reconciliation claims one due attempt with `FOR UPDATE SKIP LOCKED`; its
  claim transaction commits before external confirmation, so it does not hold
  a database lock during network I/O;
- retention locks quote and artifact rows with `SKIP LOCKED`, preventing a
  simultaneous payment transition for the selected quote.

Residual lock risk: retention currently performs up to ten two-second private
HTTP deletes while the database transaction holds quote/artifact row locks.
That can hold a transaction for roughly twenty seconds even though individual
SQL statements have a five-second timeout. This is acceptable only as a
bounded local verification characteristic, not proven production scale. Do
not introduce a `DELETING` state or otherwise change the schema in this tranche
without evidence and a separate migration decision. Tests should prove that a
concurrent payment/entitlement state cannot be cleaned, and should capture lock
wait/deadlock failures as defects.

The partial indexes match the bounded workers: `build_queue` covers preparing
requests and `reconcile_queue` covers due submitting/unknown attempts. The
retention query has no dedicated `(state, expires_at)` quote index; at the
current unmeasured/local volume this is not evidence for a migration. Record
`EXPLAIN (ANALYZE, BUFFERS)` on seeded disposable data before proposing one.

## Disposable PostgreSQL feasibility and test protocol

Docker is available and its local daemon responded (`29.8.1`). No host
`psql`, `initdb`, or `postgres` binary was found, so the reproducible route is a
throwaway PostgreSQL container with:

- a unique random container name, random strong password, loopback-only
  ephemeral published port, and no reused/shared volume;
- readiness polling before migration;
- `npm run migrate` against only that generated database URL;
- a second migration run proving checksum/idempotency;
- 20-way same-key/same-body creation, same-key/different-body conflict,
  cross-scope isolation, four-slot build claiming, lease expiry, and concurrent
  retention/payment exclusion;
- lost cleanup-response simulation proving retry convergence;
- invariant queries for orphan rows, duplicate identities, invalid state
  combinations, and unchanged dedup rows;
- unconditional container removal and a final `docker ps -aq` absence check.

The container itself is the rollback boundary. There is intentionally no
down-migration for this forward-only foundation and no shared/persistent
database may be targeted. Capture the exact image digest, generated container
identity, migration checksum row, test counts, cleanup result, and final
absence proof in verification evidence. Do not print the generated password.

## Validation queries / stop conditions

At minimum, verify after the race suite:

```sql
SELECT scope_hash,idempotency_key,count(*) FROM report_requests
GROUP BY 1,2 HAVING count(*) <> 1;

SELECT authorization_identity,count(*) FROM payment_attempts
GROUP BY 1 HAVING count(*) <> 1;

SELECT q.id FROM quotes q
LEFT JOIN report_requests r ON r.id=q.report_request_id
LEFT JOIN artifacts a ON a.report_id=q.report_id
WHERE r.id IS NULL OR a.report_id IS NULL;

SELECT a.report_id FROM artifacts a
JOIN entitlements e USING (report_id)
WHERE a.storage_state='DELETED';
```

Any row from these queries, any deadlock/statement timeout, any fifth active
build lease, cleanup of a quote with a non-rejected attempt or entitlement,
mutation of migration `001`, migration checksum drift, container cleanup
failure, or connection to a non-disposable database is a hard stop.

## Recommendation to the implementation owner

Add characterization/regression tests first. Repair the smallest contract
surface that makes deletion idempotent and proves the lost-response retry.
Use the existing schema unchanged. Run the gateway build/typecheck and the
disposable PostgreSQL race/invariant suite. Keep payment, external RPC,
facilitator, wallet, exchange, deployment, and release paths disabled.
