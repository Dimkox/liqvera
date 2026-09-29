# Architect analysis — smallest F5 fake-only vertical

Route: `583d09e0cf44`
Scope inspected: frozen F2 state contract, gateway payment orchestration,
reconciliation worker, payment port, and PostgreSQL adapter.
Constraint: in-process fakes and temporary local files only; no PostgreSQL,
migration, wallet, RPC, facilitator, transfer, shared environment, deployment,
release, exchange, or live execution.

## Recommendation

Build one Node test vertical around the real `Gateway.read` orchestration and
real frozen `states.json`, with a deterministic in-memory ledger double,
scripted `PaymentPort`, and a temporary-file `ArtifactStore`. Reuse the same
fixture in direct `reconcileOne` tests. Do not instantiate `OfficialX402`,
`MezoReceiptReader`, `Pool`, or an HTTP server.

This is the smallest honest vertical because it executes the production
application decisions that decide whether `settle` is called, whether a body
is released, and whether recovery calls `confirm` rather than `settle`.
Testing `StateMachines.next` alone would be insufficient: it validates named
guards but does not execute effects such as `prohibit_resubmit`, uniqueness,
atomic entitlement, or delivery withholding. Conversely, creating a second
test-only settlement implementation would prove the fake rather than the
gateway.

Suggested files:

- `apps/mezo-gateway/test/state-machine.test.ts`: all F5 traces and assertions;
- optionally `apps/mezo-gateway/test/helpers/memory-ledger.ts` if the fixture
  makes the test unreadable;
- at most one small production pure helper for receipt/entitlement binding,
  called by both `Ledger.confirm` and the fake-only tests. Do not duplicate the
  binding predicate in the fake.

The in-memory ledger should implement only the methods touched by the tested
paths (`quote`, `beginAttempt`, `markSubmitting`, `unknown`, `confirm`,
`manualReview`, `confirmation`, `recordDelivery`, `quoteForAttempt`, and the
bounded lease operation needed by `reconcileOne`). It should record an ordered
event trace and enforce canonical authorization uniqueness and one active or
uncertain attempt per quote. It is a test double, not a new runtime store.

## Minimum scenario matrix

Each row must assert final quote state, attempt state, entitlement/body
presence, ordered calls, and exact `settle` call count.

| Scenario | Scripted boundary | Required result |
| --- | --- | --- |
| Canonical duplicate use | Two quotes present the same canonical authorization identity (different header encoding is allowed in the fixture) | First attempt owns the identity; second returns `AUTHORIZATION_REUSED`; second quote receives no entitlement/body; total `settle` calls remain one |
| Failure before submit | Artifact read fails after `beginAttempt` but before `markSubmitting` | No `settle`; stale `VERIFIED` recovery closes the attempt and restores unexpired quote to `READY` (or `EXPIRED` if the scripted deadline passed) |
| Unknown outcome with tx hint | `settle` returns a tx hash and confirmation is temporarily absent | Attempt `UNKNOWN`, quote `PAYMENT_UNCERTAIN`, body withheld, artifact retained, no second `settle` |
| Unknown outcome without tx hint | `settle` throws before a trustworthy tx hash exists | Same fail-closed state and retry prohibition; recovery uses `confirm`/correlation only and never invents a status endpoint |
| Reconciliation succeeds | `reconcileOne` later returns one matching final confirmation | Existing attempt becomes `CONFIRMED`; quote becomes `PAID`; exactly one digest-bound entitlement is created; `settle` count stays one |
| Reconciliation exhausted | Ten bounded confirmation checks stay unresolved | Attempt and quote become `MANUAL_REVIEW`; no entitlement/body and no resubmission |
| Receipt mismatch | Confirmation changes each binding field in turn: quote, attempt, report id/digest, network, chain, asset, amount, payer, or receiver | No entitlement/body; attempt and quote enter `MANUAL_REVIEW`; no additional `settle` |
| Finality absent | Confirmation fake reports no canonical/final receipt | Remain uncertain; no entitlement/body |
| Entitlement recovery | Initial response is lost after atomic confirmation; subsequent report and bundle reads omit a payment signature | Same immutable bytes and receipt are returned; zero additional `verify`/`settle` calls |
| Reorganization | `revalidate` becomes false or reports an RPC/canonical-block conflict after payment | Quote and attempt move to `MANUAL_REVIEW`; both report and bundle are withheld; no resubmission |
| Authoritative recovery after review | A later authoritative confirmation matches the retained authorization and immutable digest | Existing entitlement is restored to usable `PAID`/`CONFIRMED`; no duplicate chain event, receipt, entitlement, or settlement |

Also run a table over every frozen F5 transition with one required guard false.
`StateMachines.next` must reject each with `INVALID_STATE`; this prevents the
scripted fake from silently weakening the frozen graph.

## Required production invariants

The vertical should express these as call-order and negative assertions, not
only final-state assertions:

1. `beginAttempt` and `markSubmitting` occur before the sole `settle` call.
2. Once `SUBMITTING` is durable, all timeout/crash paths become `UNKNOWN`; no
   HTTP replay or reconciliation path calls `settle` again.
3. Receipt validation covers all immutable quote, authorization, chain event,
   and report-digest bindings before entitlement creation.
4. Entitlement creation and `CONFIRMED`/`PAID` publication are one logical
   commit in the fake; inject a failure between them and prove delivery stays
   closed.
5. Every delivery revalidates current finality and exact artifact bytes.
6. A reorg or receipt inconsistency retains evidence, prohibits resubmission,
   and withholds both report and bundle.
7. Repeat authorized delivery uses the retained entitlement and never calls
   `verify`, `beginAttempt`, `markSubmitting`, or `settle`.

Use real report bytes from a temporary directory and compute the expected
SHA-256 in the fixture. Mutation or deletion between confirmation and delivery
must yield `ARTIFACT_INTEGRITY_FAILURE`, not a body. This is local filesystem
evidence only and must not be relabelled as durable artifact recovery.

## Confirmed implementation gaps to characterize first

### 1. Inconsistent receipt does not immediately enter manual review

`Ledger.confirm` rejects mismatched receipt bindings with
`PAYMENT_REJECTED`, but `Gateway.read` only calls `manualReview` when the caught
error code is already `MANUAL_REVIEW`. The catch then records `UNKNOWN` and
returns `PAYMENT_UNCERTAIN`. That contradicts the frozen quote transition
`PAYMENT_PENDING -> MANUAL_REVIEW` on `inconsistent_receipt` and permits ten
ordinary reconciliation cycles before review. The first regression should
demonstrate this current failure; the minimal repair is to classify a
post-submit binding/schema inconsistency as review-required while preserving
the public fail-closed response.

### 2. `MANUAL_REVIEW -> PAID/CONFIRMED` is declared but not operational

The frozen graph declares authoritative recovery from manual review and
`Ledger.confirm` accepts an attempt in `MANUAL_REVIEW`. However:

- `reconcileOne` leases only `SUBMITTING` and `UNKNOWN`, so it never selects a
  reviewed attempt;
- `Gateway.read` rejects a `MANUAL_REVIEW` quote before calling `revalidate`;
- calling `Ledger.confirm` for the already-entitled reviewed attempt attempts
  to insert the existing chain event, receipt, and entitlement again, rather
  than restoring their states.

Therefore the final scenario above should initially fail or be explicitly
reported unsupported. A bounded repair needs a distinct idempotent
authoritative-recovery operation that validates the retained immutable rows
and changes only attempt/quote state. It must not insert replacement receipt
or entitlement rows and must never call `settle`.

## Scope ruling

For this route, implement and verify the in-process vertical and only the
smallest orchestration/pure-validation repairs required by its failing tests.
Do not change migrations or exercise PostgreSQL. If operational recovery
requires adapter changes that cannot be honestly proven without PostgreSQL,
leave that item as a named blocker for a separately approved disposable-DB
route rather than mocking a PASS.

The resulting evidence may claim:

- deterministic application call ordering;
- canonical duplicate rejection in the in-memory model;
- at-most-one mocked settlement call;
- fail-closed unknown/mismatch/reorg behavior;
- mocked entitlement and response-loss recovery.

It may not claim:

- durable uniqueness, atomicity, crash recovery, or locking in PostgreSQL;
- correct SDK authorization identity or finality policy (both remain
  `UNRESOLVED` in `states.json`);
- a successful facilitator, RPC, wallet, transfer, testnet payment, or A13/A14
  acceptance result.

## Verification slice

Run the gateway exact-lock typecheck/build and the new Node test file first,
then the route's pinned PR verifier. Independent reviewers should specifically
check that the fake cannot mint an entitlement without traversing the real
gateway path, and that no test name or documentation upgrades mocked evidence
to payment acceptance.
