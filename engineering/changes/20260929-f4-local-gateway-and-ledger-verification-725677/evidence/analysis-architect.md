# Architecture analysis — F4 local gateway and ledger verification

Change: `20260929-f4-local-gateway-and-ledger-verification-725677`
Route: `725677143509`
Role: route-selected architect (read-only analysis; this report is the only write)

## Recommendation

Implement one bounded F4 vertical: compile the pinned gateway tree, then exercise the
gateway/ledger/report-service boundary against a fresh PostgreSQL database and in-process
fake ports. The vertical ends at quote readiness, retention cleanup, and artifact recovery
state; it must not enter authorization verification, settlement, chain confirmation, paid
delivery, or any external HTTP/RPC path.

This tranche should make one production repair: treat an authenticated, well-formed cleanup
response for the requested report as a successful idempotent cleanup whether `deleted` is
`true` (removed now) or `false` (already absent). The report service deliberately returns
`false` when the guarded directory is absent (`evidence_bundle.py:271-273`), while the gateway
currently accepts only `deleted === true` (`report-service.ts`). After a successful filesystem
delete whose HTTP response is lost, the current retry therefore leaves the ledger artifact
`AVAILABLE` forever. No schema change is required.

## Smallest coherent vertical

1. **Deterministic build boundary**
   - Install from the existing lockfiles only; build `packages/mezo-protocol` before
     `apps/mezo-gateway` if the file dependency requires it.
   - Run gateway typecheck and production build. Do not update packages or lockfiles merely
     to make the check convenient.

2. **Fresh-database characterization**
   - Apply the existing immutable `001_ledger.sql` through the gateway migrator to an empty,
     randomly identified PostgreSQL database.
   - Re-run migration and prove checksum/idempotency behavior.
   - Exercise constraints and transition triggers actually used by the vertical. Do not edit
     `001_ledger.sql`; any discovered schema defect would require a forward-only `002_*`
     migration and a separately reviewed scope amendment.

3. **Request/build/API vertical with local fakes**
   - Use a real `Ledger` and real `Gateway`, but fake `ReportService`, `ArtifactStore`, and
     `PaymentPort` in-process. The fakes must never open a socket or call settle.
   - Configure the test object as `live-public` only to cross the deliberate fixture sale gate;
     label the harness synthetic and assert the production fixture configuration still returns
     `SIMULATED_SOURCE`.
   - Drive the Express routes where HTTP mapping matters and the application/ledger methods
     where concurrency and fault injection matter.
   - Prove same-scope/same-key/same-body convergence, same-key/different-body `409`, and
     cross-scope isolation. Twenty simultaneous creates must produce one request, one report
     ID, one artifact, and one quote, with no duplicate build claim.

4. **Retention and recovery vertical**
   - Select only an expired, unpaid quote whose artifact is `AVAILABLE`; exclude paid,
     pending, uncertain, manual-review, and any quote with a non-rejected attempt.
   - Inject these cleanup outcomes: delete-now (`true`), already-absent after lost response
     (`false`), timeout/exception, malformed body, mismatched report ID, and unavailable
     cleanup credentials.
   - The first two authoritative outcomes must converge to `DELETED`; all ambiguous outcomes
     must retain `AVAILABLE` and retry later. Record at most one effective
     `UNPAID_ARTIFACT_REMOVED` audit event.
   - For an artifact read failure, prove `RECOVERY` blocks new sales/readiness. Because
     `HttpReportService.recover()` is intentionally unimplemented, prove failure remains
     fail-closed rather than rebuilding from a fresh snapshot.

5. **Contract checks**
   - Validate tested route bodies/statuses against the frozen OpenAPI/resources schemas, not
     hand-written approximations. At minimum cover request creation/polling, quote retrieval,
     `402` without a signature, scope hiding as `404`, idempotency conflict, and storage or
     integrity failure mapping.
   - A `402` test may use fake payment requirements, but it must assert zero `verify`,
     `settle`, `confirm`, and `revalidate` calls.

## Component boundary

```text
loopback test client
        |
        v
Express routes -> Gateway -> Ledger -> disposable PostgreSQL
                      |  \
                      |   +-> temporary artifact reader
                      +-----> in-process report/payment fakes
```

The only process boundary needed for semantic correctness is PostgreSQL. Report-service HTTP
parsing may be covered separately with a loopback-only server if existing adapter tests require
it; the main F4 race suite should inject the port directly and avoid network timing as an
oracle. The Python report-service delete behavior should be characterized with a temporary
artifact root, not by starting the full Compose stack.

## Dependency order

1. Pinned protocol package builds.
2. Gateway typecheck/build passes.
3. Empty PostgreSQL migration and rerun pass.
4. Ledger primitives and transition triggers pass.
5. Request/idempotency/build concurrency passes.
6. Route/OpenAPI mapping passes.
7. Retention lost-response regression is reproduced, repaired, and passes.
8. Artifact-loss fail-closed cases pass.
9. Full repository verifier and route-selected reviews run on the final fingerprint.

This order prevents route tests from hiding compile errors and prevents higher-level API
assertions from being trusted before the actual PostgreSQL semantics are known.

## Required concurrency invariants

- `(scope_hash, idempotency_key)` identifies exactly one immutable canonical request.
- A retry with the same canonical body returns the existing resource and does not consume a
  second rate-budget hit; a different body fails with `IDEMPOTENCY_CONFLICT`.
- Cross-scope reuse of a key creates a distinct request and cannot read the sibling scope.
- No more than four build leases are active globally; each request is claimed by at most one
  worker. Expired leases move monotonically to `BUILD_FAILED`, never back to `PREPARING`.
- Publication is atomic in one database transaction: request `READY`, artifact, quote, and
  `ARTIFACT_PUBLISHED` audit evidence either all commit or none do.
- Cleanup selection and its ledger transition serialize with quote/payment transitions. A
  quote that ceases to be eligible while locked must not have its artifact removed.
- Cleanup retries converge: delete-now and already-absent are the same terminal filesystem
  fact. Ambiguous transport/service outcomes are not proof of absence.
- Ledger identities, authorization-dedup rows, audit rows, receipts, and entitlements are never
  removed by this tranche.
- No test invokes `PaymentPort.settle`; a spy assertion must make violation immediately fail.

## Recovery invariants

| Failure window | Required result |
|---|---|
| Build fails before artifact publication | Request becomes terminal `REJECTED` or `BUILD_FAILED` with the mapped reason; no quote/artifact row |
| Artifact exists but ledger publication transaction fails | No partial ledger quote; artifact is not made saleable and the test records the orphan for bounded cleanup policy, not implicit deletion |
| Cleanup succeeds and response arrives | Artifact ledger state becomes `DELETED` once |
| Cleanup succeeds and response is lost | Retry receives authoritative already-absent response and ledger converges to `DELETED` once |
| Cleanup response is malformed, mismatched, unauthorized, times out, or errors | Keep `AVAILABLE`; no removal audit claim |
| Published bytes are missing/corrupt before sale | Do not return `402` and do not call payment ports |
| Paid bytes are missing/corrupt | Move to `RECOVERY`, return integrity/uncertain response, block new sales; do not charge or reconstruct from new market data |
| Recovery adapter returns false | Remain `RECOVERY`; readiness stays closed |

The existing retention worker performs the report-service call while holding a database
transaction and row locks. Keep this for the minimal repair because moving the call outside
the transaction creates a new authorization race and needs a durable cleanup intent/outbox.
Tests must enforce the two-second timeout and bounded batch of ten. A later optimization may
introduce a persisted cleanup state in a forward migration, but it is not needed to establish
F4 correctness here.

## Safe ephemeral test boundary

- Create a uniquely named PostgreSQL 16 container or local cluster for this run only, with a
  random database/user/password, tmpfs/no named persistent volume, and either a private Unix
  socket or a port published only on `127.0.0.1` at an ephemeral host port.
- Resolve and record the exact container/database identity before running destructive cleanup.
  Install an exit trap; stop/remove only that exact identity; finally prove it is absent.
- Never use `DATABASE_URL` inherited from the shell, the normal Compose project name, shared
  volumes, or any existing developer/CI database. Supply the generated URL directly to the
  test process.
- Use temporary directories for artifacts and tokens. Tokens are random test values, never
  printed or committed. No `.env` is read.
- Deny external network in the gateway test process where practical. Allow only the isolated
  PostgreSQL endpoint and optional loopback test server. Fake capture, report, payment,
  facilitator, RPC, wallet, chain, exchange, and deployment ports.
- Do not start `deploy/mezo-evidence/compose.yaml`, expose a public listener, run a deployment,
  push, tag, or release.

## Repair shape

Prefer making the cleanup response contract explicit instead of weakening generic JSON
acceptance:

- Parse a closed response with exact `report_id` and boolean `deleted`.
- Interpret both boolean values as an authoritative terminal absence result; retain the
  boolean as diagnostic data if useful, but return a distinct semantic result such as
  `ABSENT`/`REMOVED` rather than overloading “success”.
- Reject unknown fields if the internal contract is intended to be closed, or at minimum
  ignore them only after the required fields and types match; whichever policy is selected
  must be tested and documented consistently on both sides.
- Do not treat `404`, connection reset, timeout, `5xx`, malformed JSON, or mismatched ID as
  proof of deletion.

A minimal boolean-compatible patch may return `true` for either valid boolean value. A typed
result is architecturally clearer, but widening the port should remain local and must not lead
to unrelated refactoring.

## Non-goals and stop conditions

This tranche does not authorize schema changes, shared database access, live source capture,
facilitator/RPC calls, wallet use, settlement, chain mutation, exchange mutation, Compose
startup, deployment, push, tag, or release. Stop and rescope if correctness requires any of
those actions, a new dependency, modification of applied migration `001_ledger.sql`, or a
production recovery endpoint.

## Acceptance evidence expected

- Exact Node/npm versions, lockfile digests, build and typecheck commands.
- PostgreSQL image/version digest or local server version plus unique ephemeral identity and
  cleanup proof.
- Runtime tests covering 20-way idempotency/build contention, scope isolation, state triggers,
  migration rerun, lost cleanup response, ambiguous cleanup failure, artifact loss, and zero
  payment mutation calls.
- Frozen contract/vector mapping for every exercised F4 case.
- Final `grok_verify.py --mode pr` result and independent code/test/data reviews bound to the
  final repository fingerprint.

## Architectural verdict

**Proceed with the bounded F4 vertical.** The current design has a reproducible P0 recovery
contract mismatch, but it can be repaired without a migration or external action. Preserve the
shadow-only/payment-disabled posture and prove PostgreSQL concurrency with disposable state
rather than substituting mocks for the ledger.
