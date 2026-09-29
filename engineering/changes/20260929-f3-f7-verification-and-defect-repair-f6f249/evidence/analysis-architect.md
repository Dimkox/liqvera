# Architecture analysis — F3–F7 verification and defect repair

Route: `f6f2495b4648`
Base: `f07562eee1a33df74768e9fa4a3b074783d8c59e`
Role: read-only architecture analysis
Decision gate: `scope_and_design_approval` is required before implementation;
`migration_or_external_write_approval` is separately required before any
migration execution or external write.

## Recommendation

Treat this as a dependency-ordered evidence program, not one omnibus defect
fix. First characterize build/resource closure without changing behavior. The
first implementation slice after a green preflight must be the canonical F3
offline installed-artifact path:

```text
fixture capture/package
  -> strict sealed-input inspection
  -> exact canonical report
  -> atomic report + bounded deterministic bundle
  -> installed offline verifier
  -> tamper/replay rejection
```

Do not start PostgreSQL, gateway settlement, browser payment, Compose runtime,
or F7 acceptance implementation until this slice is green. F4 consumes F3
artifact bytes and digests; F5 consumes F4 state and locking; F6 consumes the
stable F4/F5 API; F7 can only aggregate evidence produced by F3–F6.

## Current evidence boundary

- F2 contracts are statically verified, but every canonical F3–F7 runtime
  acceptance vector remains `NOT_RUN`; A13–A14 remain `BLOCKED_EXTERNAL`.
- `tests/evidence_report/` covers the deliberately limited fixture MVP
  (`builder.py`, `bundle.py`, and `cli.py`). It does not exercise canonical
  `sealed_input.py`, `report.py`, `evidence_bundle.py`, `evidence_cli.py`,
  `schema_validation.py`, or `service.py`.
- The evidence-report wheel declares canonical build, verify, report-service,
  and demo entry points and force-includes schemas/migrations/assets, but the
  installed canonical entry points and resources have not been executed.
- Gateway and web packages have `build`/`typecheck` scripts but no test script
  and no `*.test.ts` or `*.spec.ts` files. Therefore a successful TypeScript
  build would prove syntax/type/resource closure only, not ledger, HTTP,
  payment, browser, or recovery semantics.
- The gateway migration contains the intended uniqueness, append-only,
  transition, receipt, entitlement, and replay constraints, but no integration
  test has applied it to PostgreSQL.
- The production gateway is fail-closed by construction: authorization
  identity and finality policies are hard-coded unresolved, and payment
  readiness also requires `PAY_TO`. Mocked payment tests must inject test
  ports/policies; they must not replace or weaken these production defaults.
- The acceptance runner records A07, A13, A14, A29, and A30 as live cases. In
  offline mode they must remain `BLOCKED_EXTERNAL`; a lower-level mock test
  for the same behavior is useful evidence but is not a live acceptance PASS.
- Fixture Compose still attaches capture, gateway, and edge templates to
  non-internal egress networks. A fixture code path may make no request, but
  that is not proof of network denial. Do not start the stack as an “offline”
  test until a test-only egress-denial boundary is demonstrated.

## Scope boundary

### In scope after scope approval

- Deterministic local builds, typechecks, graph checks, wheel/resource
  inspection, and locally cached lockfile installation.
- Fixture-only F3 execution and loopback-only internal-service tests.
- F4 integration against a fresh disposable local PostgreSQL instance, but
  only after the separate migration approval is recorded.
- F5 settlement, RPC, facilitator, crash, timeout, and finality behavior using
  injected in-process fakes only.
- F6 browser behavior using a fake injected wallet and fake local API, plus
  static Compose/image/security validation.
- F7 offline acceptance commands with sanitized local evidence and honest
  `NOT_RUN` / `BLOCKED_EXTERNAL` rows.
- Minimal defect repairs proven by a failing regression test first. One write
  owner changes application code; each repair stays within the phase that
  exposed it.

### Explicitly out of scope

- Hyperliquid live capture or any other external HTTP/RPC probe.
- Facilitator `/supported`, `/verify`, `/settle`, Mezo RPC, explorer, or wallet
  calls.
- Wallet connection/signature, test BTC/MUSD acquisition, testnet transfer,
  A13/A14, mainnet, or any real payment authorization.
- Exchange credentials, order submission/cancellation, trading, custody, or
  any exchange mutation.
- Applying a migration to any persistent/shared database; production or
  user-data backfill; destructive SQL.
- `docker compose up` against the live profile, deployment, publication,
  release, tag, push, PR merge, or cloud purchase.
- Changing F2 schemas/state meanings merely to make the implementation pass.
- Resolving `PAY_TO_MISSING`, `AUTHORIZATION_IDENTITY_UNVERIFIED`, or
  `FINALITY_RULE_UNVERIFIED` with placeholder configuration or test policy.

Dependency/package downloads are read-only acquisition, not product
acceptance. Prefer an existing verified cache. If a required lockfile artifact
is unavailable without network access, record a dependency-acquisition blocker
rather than silently updating a lock or installing `latest`.

## Dependency-ordered phases

### Phase 0 — clean characterization and build closure

Purpose: establish whether the integrated tree can be built before repairing
runtime behavior.

Order:

1. Record HEAD/tree/tooling-pin identities and the clean baseline. Run
   diff/secret/graph/static contract checks without creating a pass receipt for
   later changed code.
2. Build the four Python distributions into a temporary output, inspect wheel
   contents, metadata, entry points, schema assets, migration, demo assets, and
   dependency closure. Install into an isolated environment and import each
   package without the source checkout on `PYTHONPATH`.
3. Build `@liqvera/mezo-protocol` first, then gateway typecheck/build and
   resource copy, then web typecheck/build. Use exact lockfiles and disabled
   lifecycle scripts. A compile pass is not a runtime pass.
4. Render Compose configuration only; do not start services. Confirm all
   required variables/secrets fail closed and no product artifact is mounted
   into the public static service.

Exit: all build products are attributable to the current tree; installed
resources resolve without source-checkout fallback; graph and frozen contracts
remain unchanged.

If Phase 0 fails, the first implementation slice becomes the smallest
build/resource-closure repair that reproduces that failure. Stop afterward,
rerun Phase 0, and do not combine it with F3 behavior changes.

### Phase 1A — canonical F3 offline artifact path (first behavioral slice)

Use one deterministic fixture package and fixed request identity/time/commit.
Through the installed wheel, build the report and bundle, verify them offline
with the expected report digest, rebuild independently, and compare exact
bytes/digests. Add negative tests for duplicate JSON keys, floats/nonfinite
values, invalid Unicode, stale/crossed/wrong-identity/depth inputs, symlinks,
path traversal, duplicate/archive-bomb members, member/total limits, changed
input during read, existing output, partial publication, and report/bundle
corruption.

Required assertions:

- fixture output is `SIMULATED`, non-chargeable, and
  `execution_authority=NONE`;
- BUY/SELL and rational values match F2 vectors without float conversion;
- report bytes are canonical and do not contain their own digest;
- verifier recalculates from sealed input and rejects any byte/manifest
  mismatch;
- a synthetic attempt to feed fixture bytes as `live-public` fails closed and
  performs no network call;
- no failure leaves a READY or partially published artifact.

Exit: A02–A06 and A08–A09 have runtime evidence at the offline layer. A07
remains live `BLOCKED_EXTERNAL` even if its no-fallback behavior is covered by
a mock/negative test.

### Phase 1B — F3 loopback services

Exercise capture and report HTTP services only on loopback/in-process
transports, with temporary roots and synthetic token files. Verify body/header
limits, authentication, four-build bound, duplicate report ID behavior,
deadlines, atomic publication, cleanup/recovery, readiness, environment
separation, and redaction. Keep source mode `fixture`; assert no socket attempts
to non-loopback destinations.

Exit: F4 can depend on stable artifact metadata, bytes, and report-service
errors.

### Phase 2 — F4 gateway and disposable PostgreSQL, no settlement

This phase is gated by recorded migration approval. Apply
`001_ledger.sql` only to a fresh disposable local PostgreSQL database with no
external route or retained user data. Verify schema before/after, foreign keys,
unique indexes, append-only triggers, transition triggers, lock order,
statement timeouts, and teardown. There is no backfill; dropping the disposable
database is test cleanup, not a production rollback strategy.

Use injected report/artifact/payment ports and the real database to test:

- scope capability isolation and non-enumerating errors;
- strict body/header/CORS/cache/rate limits;
- canonical idempotency and different-body `409`;
- 20 parallel repeats of one request/quote;
- report/bundle readback before quote readiness;
- unpaid `402` without paid bytes;
- artifact missing before payment blocks the attempt;
- fixture reports never become chargeable;
- restart-safe build leasing and bounded workers.

The payment fake may construct deterministic requirements but must reject
`settle`; no x402 transport or RPC object may contact the network.

Exit: F4 API/ledger semantics are green, including A10, A15–A16, A21, and the
pre-payment branch of A22. No payment receipt or entitlement is claimed.

### Phase 3 — F5 mocked settlement and recovery

With the Phase 2 database, inject deterministic fake x402, authorization,
finality, and RPC ports. Cover invalid signature/network/token/amount/
receiver/payer, replay-domain identity, authorization reuse, settle rejection,
timeout before/after tx hash, crash before submit/after broadcast/after chain
success, lost HTTP response, expiry during settlement, ambiguous matching
transfers, reorg/inconsistent RPC, reconciliation backoff/manual review,
artifact loss after confirmation, and repeat retrieval.

At least 20 concurrent payment attempts must prove one active logical attempt
and at most one call to the fake `settle`. A timeout or uncertainty remains
`UNKNOWN`/`PAYMENT_UNCERTAIN`; recovery may confirm or escalate, but may never
invoke `settle` again. Entitlement/receipt/artifact digest must commit in one
database transaction before paid bytes are returned.

Exit: mocked A11–A12, A17–A20, A22–A25 and the settlement portion of A15 have
evidence. A13–A14 remain `BLOCKED_EXTERNAL`. Production identity/finality
objects remain unresolved and payment readiness remains false.

### Phase 4 — F6 browser and deployment shell

Build and test the browser against a fake local API and fake EIP-1193 provider:
cancel, wrong chain, rejected network switch, wallet/account switch, reload,
expiry, 202 polling bounds, uncertain settlement, paid recovery, repeated
download, capability storage, URL/log leakage, and no implicit signing.

Validate Dockerfiles and rendered fixture/live Compose separately. Inspect
non-root users, read-only mounts, secret-file ownership, capability drops,
healthchecks, port binding, network membership, volume ownership, log
redaction, CSP/CORS/TLS configuration, and absence of paid bundles from the
web image. Container builds may follow static checks. Starting a fixture stack
requires a test boundary that demonstrably denies all external egress; the
live profile remains forbidden.

Exit: mocked browser recovery is green, but A30 remains live
`BLOCKED_EXTERNAL` under the current acceptance inventory. A26 may pass only
with observed network-denial evidence, not from YAML inspection alone.

### Phase 5 — F7 offline acceptance and closure

Create an explicit offline command plan from the already-green phase tests.
Run it against a clean final commit and new output path. Every row records
command, environment names, exit code, hashes, observations, and omissions.
Do not transform a unit/mock result into live evidence.

Expected final offline report:

- locally executable non-live cases may PASS when their asserted layer is
  explicit and evidence exists;
- A07, A13, A14, A29, and A30 remain `BLOCKED_EXTERNAL` in offline mode under
  the current runner classification;
- missing commands remain `NOT_RUN`, never silent skips or PASS;
- overall status remains `INCOMPLETE` while live rows are blocked.

Then run the route-selected verification on the final tree and all five
independent reviews. Persist reports first, rerun final verification, and bind
fresh receipts to the tree containing those reports. This route does not
deploy, publish, or release.

## Load-bearing invariants

1. **Source authority:** fixture and live-public identities never mix; live
   mode cannot fall back to fixture data or nominal mapping evidence.
2. **Exactness:** market quantities/prices remain exact decimal/rational
   strings; MUSD stays the integer atomic string `10000000000000000`.
3. **Immutable evidence:** report/bundle bytes are content-addressed, published
   atomically, read back before sale, never overwritten under one report ID,
   and verified before delivery.
4. **Authority separation:** Python owns capture/analytics/report bytes;
   gateway owns ledger/payment delivery; browser owns user interaction only.
5. **Fail-closed payment:** unresolved identity, finality, facilitator,
   merchant receiver, chain, asset, or artifact makes payment readiness false.
6. **No premature delivery:** `verify=true`, facilitator success, HTTP 200, or
   a matching Transfer does not create entitlement. Confirmed finality and one
   atomic ledger commit precede paid bytes.
7. **At-most-once settlement:** authorization identity is unique; the durable
   `SUBMITTING` boundary precedes the sole settlement call; reconciliation is
   read-only and never settles again.
8. **Unknown is durable:** timeout/crash/ambiguity becomes
   `PAYMENT_UNCERTAIN`/`UNKNOWN` or `MANUAL_REVIEW`, never unpaid, rejected, or
   permission to request another payment.
9. **Scope isolation:** capability/access scope binds every request, quote,
   artifact, entitlement, and delivery; knowing an ID or transaction hash
   grants nothing.
10. **Ledger authority:** PostgreSQL is the sole payment-state writer;
    receipts/audit/chain/reconciliation events are append-only and dedup rows
    outlive authorization validity.
11. **Artifact loss safety:** loss before payment blocks sale; loss after
    payment closes sales and enters recovery/incident without another charge.
12. **Secret/PII hygiene:** no token, capability, authorization, signature,
    wallet secret, database credential, or sensitive header reaches logs,
    artifacts, browser bundles, acceptance output, or command arguments.
13. **Network boundary:** offline tests fail on unexpected non-loopback I/O;
    no mainnet/exchange-mutation path is introduced.
14. **Evidence honesty:** mocked evidence is labeled mocked; blocked live work
    remains blocked; a changed tree invalidates all receipts.
15. **Stage A preservation:** existing verdict semantics remain unchanged and
    `GO` stays impossible where current evidence is insufficient.

## Repair discipline

For each observed defect:

1. retain the exact failing command/output and first incorrect state;
2. add a regression test that fails for that state;
3. repair only the owning phase/component;
4. run the focused test plus all upstream dependency gates;
5. commit the coherent green slice with `handoff.md` updated;
6. do not batch unrelated refactors, dependency upgrades, schema changes, or
   documentation claim changes into the repair.

If implementation contradicts a frozen F2 contract, stop and classify the
conflict. The default is to repair implementation. Changing a contract or
state meaning requires a new explicit design decision and re-review of all
downstream phases.

## Stop conditions

Stop the active phase immediately and do not advance if any of these occurs:

- non-deterministic report/bundle bytes, incorrect exact arithmetic, accepted
  tampering/traversal/bomb input, partial READY publication, or source mutation;
- a fixture report becomes chargeable or live mode succeeds without reviewed
  identity evidence;
- F2 schema/state/API drift is required merely to pass tests;
- idempotency, unique authorization, scope isolation, append-only state, or
  20-way concurrency fails;
- a second settlement is possible, uncertainty becomes unpaid/retryable, or
  paid bytes appear before finality/entitlement commit;
- a wrong chain/token/amount/payer/receiver/mainnet configuration is accepted;
- missing/corrupt paid artifacts cause a second charge or an unverified
  regenerated digest;
- secrets/capabilities/signatures appear in logs, bundles, browser output, or
  acceptance evidence;
- any test performs unexpected external network I/O, requests a real wallet
  signature, needs a real merchant/private key, or targets a non-disposable
  database;
- the migration is destructive, cannot be applied to a fresh database, or
  lacks a forward-recovery path;
- Stage A, graph, package boundary, shadow-only, or existing exact contracts
  regress;
- a required dependency is unpinned, a lockfile must be relaxed, or a failure
  is hidden by lowering coverage/scanner policy, skipping, or relabeling it;
- a technical kill criterion from the canonical specification appears:
  unreliable metadata, unsafe payment-to-entitlement binding, repeat charge,
  paid-artifact leakage, or broken Stage A.

Record the condition as a blocker with evidence. Continue only independent
read-only analysis; do not “work around” a safety invariant.

## Rollback and forward recovery

- Phase 0/1 code is stateless: revert the phase commit and delete only derived
  temporary build/test artifacts.
- Phase 2–4 tests use fresh disposable local state. Tear down that isolated
  state after evidence capture; never use cleanup commands against shared or
  production paths.
- Once a ledger has observed payment state, rollback means disable new quote
  creation and forward-fix while preserving ledger rows and immutable
  artifacts. Never down-migrate, truncate, delete dedup rows, or overwrite
  receipts to make an older binary run.
- UI/Compose rollback may revert static/application code only if it remains
  compatible with preserved API/ledger state. Otherwise roll forward.
- Any rollback tree requires fresh verification and review receipts; prior
  evidence is stale.

## Scope decision for approval

Approve Phases 0 and 1A first. Phase 0 is characterization only. Phase 1A is
the first behavioral implementation slice and the smallest one that proves a
user-relevant Liqvera claim end to end without payment authority: a fixture
market report can be reproduced and rejected when tampered with.

Approval of this scope does **not** approve migration execution, an external
read/write, live capture, payment, wallet interaction, Compose deployment,
release, or push. Phase 2 remains separately gated by
`migration_or_external_write_approval`; all external/live work remains outside
this route unless an exact later grant changes the scope.
