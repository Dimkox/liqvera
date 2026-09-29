# F5 data and state invariants analysis

Route: `583d09e0cf44`
Role: `data_architect`
Disposition: bounded local characterization is appropriate; **no migration or persistent store is required**.

## Authority and existing boundaries

- The frozen state contract is `schemas/mezo-evidence/v1/states.json`. It owns the transition vocabulary, uniqueness rules, delivery guards, and the explicit unresolved F5 bindings.
- The existing runtime realization is split across `apps/mezo-gateway/src/application/gateway.ts`, `src/adapters/postgres.ts`, `src/adapters/mezo-rpc.ts`, and `src/workers/reconciliation.ts`.
- `apps/mezo-gateway/migrations/001_ledger.sql` plus the already accepted forward repair `002_fix_immutable_ledger_identity.sql` establish the persistent model. This F5 tranche must not edit, apply, or claim additional migration evidence.
- `tests/contracts/test_mezo_vectors.py` currently characterizes the expected F5 vectors without exercising the TypeScript runtime. New coverage should narrow that gap with in-process fakes and temporary files only; it must not relabel the 156 frozen vectors or A11–A24 as live acceptance.

## Required invariants

### Atomicity

1. `beginAttempt` must atomically insert one attempt keyed by canonical `authorization_identity`, advance it to `VERIFIED`, advance the quote to `PAYMENT_PENDING`, and append the audit event. A failure at any point leaves none of those effects committed.
2. The durable `SUBMITTING` boundary must precede the sole `settle` call. Once crossed, every timeout, exception, crash-equivalent, or absent confirmation becomes `UNKNOWN`/`PAYMENT_UNCERTAIN`; it is never interpreted as proof of non-submission.
3. Confirmation is one atomic unit: canonical chain event, immutable receipt, entitlement, attempt `CONFIRMED`, quote `PAID`, and audit record either all commit or none do. The persistent implementation already groups these in `Ledger.confirm`.
4. Entitlement identity is the tuple `(quote_id, report_id, report_sha256, payment_attempt_id)` and must continue to match the immutable quoted digest. Delivery must re-check paid/confirmed/current-finality/storage guards and must not rely on a formerly valid receipt alone.

### Replay and duplicate use

1. Canonically equivalent encodings must map to one `authorization_identity`; the database uniqueness constraint is only as good as the identity policy supplied to it. Local fakes therefore need an explicit canonical identity value rather than deduplicating raw headers.
2. A used identity remains consumed after `REJECTED`, `UNKNOWN`, `MANUAL_REVIEW`, confirmation, expiry, or artifact deletion. No local cleanup helper may erase its dedup association.
3. At most one non-rejected attempt exists per quote. A quote in `PAYMENT_PENDING`, `PAYMENT_UNCERTAIN`, `PAID`, or `MANUAL_REVIEW` cannot start another payment attempt.
4. HTTP/read replay after a committed entitlement reuses that entitlement and performs zero additional settlement calls.

### Failure and recovery

1. A failure before the durable submit boundary may close the attempt as `REJECTED` and return the still-valid quote to `READY`, or expire it if its deadline passed. This requires authoritative proof that submission did not occur.
2. A failure at or after `SUBMITTING`, including no transaction hash, must go to `UNKNOWN`; recovery and reconciliation call only `confirm`, never `settle`.
3. Ambiguous or multiple matching transfers are not confirmation. They remain uncertain and eventually require manual review.
4. A receipt mismatch (quote, report, digest, attempt, network, chain, asset, amount, payer, payee, transaction/log association) creates no chain event, receipt, or entitlement. It stays fail-closed and is reconciled or escalated.
5. Confirmation after quote expiry is valid only for an attempt that crossed the submit boundary before expiry. Expiry blocks new submissions; it does not discard an uncertain attempt.

### Finality and reorganization

1. A successful transaction receipt is not finality. Confirmation additionally requires canonical chain ID, canonical block/hash agreement, exactly one authorization-bound MUSD transfer, and the selected finality policy returning true.
2. A missing receipt or non-final receipt returns no confirmation; malformed, conflicting, removed-log, wrong-chain, or changed-block evidence is uncertainty/manual-review evidence, not rejection and not entitlement.
3. Every paid read revalidates the stored receipt against current chain evidence. A reorg or RPC conflict moves both quote and attempt to `MANUAL_REVIEW`, retains the immutable entitlement/history, and withholds report and bundle bodies without a new settlement.
4. This tranche must keep `unresolvedIdentity.reviewed=false`, `unresolvedFinality.reviewed=false`, and `payment_ready=false`. Fake policies prove state handling only; they cannot resolve the product's identity/finality gate.

## Safe test doubles

Use deterministic, in-process components with call counters and scripted outcomes:

- `FakeLedger`: an in-memory map for quote/attempt/receipt/entitlement state. Its public operations should emulate transaction atomicity by cloning state and committing only on success. Inject a failpoint before each confirmation write to prove no partial entitlement.
- `FakePaymentPort`: scripts `verify`, `settle`, `confirm`, and `revalidate`; records each call. It must assert `settleCalls <= 1` and provide separately scripted pre-submit rejection, thrown/unknown outcome, matching confirmation, receipt mismatch, and reorg paths.
- `FakeAuthorizationPolicy`: reviewed only inside the test instance, emits a fixed canonical identity for raw-encoding variants, and binds exactly one scripted transfer. Do not change exported production policy defaults.
- `FakeFinalityPolicy`: reviewed only inside the test instance, returns a scripted boolean or conflict. Its version should be visibly test-only (for example `TEST_ONLY/v1`).
- `ScriptedReadonlyRpc`: returns fixed chain ID, receipt, canonical block, transaction, and logs; no URL, socket, RPC client, wallet, signing key, or wall-clock dependency.
- `TempArtifactStore`: writes immutable report/bundle bytes below a per-test temporary directory, verifies their SHA-256 on every read, and is removed by the test harness. It must never use the repository's `.mvp`, deployment volumes, or shared service paths.
- A fake clock should control quote expiry and confirmation time. Avoid `Date.now()`/`new Date()` in expected-state decisions so boundary tests are deterministic.

The minimal executable slice should test the application boundary and pure state contract. It may structurally satisfy the existing TypeScript ports; it should not instantiate `Pool`, `OfficialX402`, `MezoReadonlyRpc`, scheduler timers, or the real facilitator transport.

## High-value test matrix

| Scenario | Required terminal observation |
| --- | --- |
| raw encodings with one canonical identity | second use rejected; one attempt; zero second settle |
| verified/pre-submit crash with authoritative no-broadcast proof | attempt `REJECTED`; quote `READY` or `EXPIRED`; zero settle |
| settle throws or confirmation absent after `SUBMITTING` | attempt `UNKNOWN`; quote `PAYMENT_UNCERTAIN`; exactly one settle |
| repeated read/reconciliation of unknown | zero additional settle; only confirmation checks |
| receipt field mismatch or multiple matching logs | no entitlement/body; uncertain then bounded manual review |
| atomic confirmation failpoint at every write boundary | no partially visible chain event/receipt/entitlement/paid state |
| valid final confirmation | one entitlement bound to exact report digest; paid body permitted |
| receipt becomes non-canonical/reorganized | both states `MANUAL_REVIEW`; entitlement retained; body withheld |
| repeat paid read with current finality | same entitlement/body; settlement count remains one |

## Risks and rulings

- The production gateway currently has no approved authorization-identity or finality implementation. Therefore a green fake-only suite is characterization evidence, not payment readiness.
- `Gateway.read` treats all failures after `markSubmitting` as uncertain. A future definitive pre-submit rejection path must prove that no broadcast occurred before it may use the `REJECTED -> READY/EXPIRED` recovery semantics; a generic thrown error is insufficient.
- `MezoReceiptReader` creates `confirmed_at` from the local wall clock. The local suite should use a deterministic fake receipt rather than asserting that timestamp; any later production policy should define whether chain time or observation time is authoritative.
- The retention contract requires ledger/scope/dedup retention for at least 30 days, through authorization validity, and until replay impossibility is proven. That rule is not fully demonstrated by a temp-only tranche and remains persistent-store acceptance debt.

## Recommendation

Proceed with a test-first, fake-only F5 vertical slice. Keep SQL, migration files, production policy defaults, network adapters, and deployment configuration byte-identical. Treat any discovered runtime defect as eligible for a minimal TypeScript repair only if it can be reproduced entirely through these deterministic doubles and preserves fail-closed behavior.
