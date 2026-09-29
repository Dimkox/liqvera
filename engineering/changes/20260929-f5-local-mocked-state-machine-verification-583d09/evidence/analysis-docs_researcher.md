# F5 canonical contract and local-mock boundary analysis

Route: `583d09e0cf44`
Change: `20260929-f5-local-mocked-state-machine-verification-583d09`
Role: route-selected `docs_researcher` (read-only analysis; this report is the only write)

## Ruling

The bounded route can characterize and repair the F5 orchestration/state-machine
boundary with deterministic in-process fakes. It cannot establish payment
readiness, x402 scheme correctness, Mezo receipt finality, PostgreSQL durability,
testnet settlement, or any A01-A30 acceptance result. All 156 frozen vectors must
remain `runtime_status: NOT_RUN`; A13 and A14 remain externally blocked until a
separately approved real testnet run supplies exact transaction evidence.

The authoritative ordering used here is the canonical specification, frozen
`states.json` and `vectors.json`, OpenAPI, runbooks, then implementation. The
route's explicit exclusion of a persistent store means local tests may use a
stateful fake ledger, but must not claim the database uniqueness, transaction,
locking, restart, or retention guarantees described by the canonical contract.

## Exact local mocked obligations

| Route concern | Canonical behavior to prove locally | Contract anchors | Closest frozen vectors (remain `NOT_RUN`) |
| --- | --- | --- | --- |
| Duplicate use | A canonical authorization can create at most one attempt; reuse for the same or another quote returns `AUTHORIZATION_REUSED`/409, creates no entitlement, and performs no settlement. Differently encoded forms require one canonical identity, not raw-payload hashing. | TZ sections 11-12; `states.json` quote `authorization_unique`; unique authorization identity; OpenAPI report 409 | `reused-authorization`, `reencoded-authorization` (A11) |
| Definitive pre-submit failure | A durable `RECEIVED`/`VERIFIED` attempt that provably never crossed submission becomes `REJECTED`; its quote returns to `READY`, or becomes `EXPIRED` when expiry already passed. No settlement, receipt, or entitlement is created. | quote `definitive_pre_submit_rejection[_after_expiry]`; attempt `definitely_not_submitted` / `expired_before_submit`; `recoverUnsubmitted` | `crash-after-durable-attempt-before-submit`, `expired-before-submitting` (A17/A20) |
| Unknown outcome | Any failure after the durable `SUBMITTING` boundary produces attempt `UNKNOWN` and quote `PAYMENT_UNCERTAIN`, HTTP 202, no paid bytes, and retained correlation/artifact state. Absence of a tx hash or multiple similar transfers is never proof of failure or confirmation. | TZ section 11; payment-recovery runbook; quote `outcome_unknown`; attempt `timeout_or_crash`; OpenAPI report/quote 202 | `verify-without-confirmation`, `timeout-without-hash`, `ambiguous-identical-transfers`, `crash-after-broadcast`, `unknown-retained-after-expiry` (A19/A20/A24) |
| Retry prohibition | Only the initial path may call `settle`, and only after durable `SUBMITTING`. HTTP replay, reconciliation, unknown/manual-review recovery, repeat paid reads, and bundle reads make zero additional settle calls. | transition effect `one_settle_call_after_commit`; UNKNOWN and MANUAL_REVIEW have no submit edge; delivery effect `no_settlement`; payment-recovery runbook | every F5 recovery vector asserts `additional_settlement_calls: 0`; especially `crash-after-broadcast`, `historical-paid-repeat-read`, `review-withholds-repeat-read` |
| Receipt mismatch | A receipt that disagrees on quote/report/digest/attempt/network/chain/asset/amount/payer/payee or chain event identity cannot entitle or deliver. Inconsistent evidence moves both attempt and quote to `MANUAL_REVIEW`, retains artifacts, and prohibits resubmission. | TZ sections 11-12; quote `inconsistent_receipt`; attempt/quote chain inconsistency edges; `Ledger.confirm` binding checks | `ambiguous-identical-transfers`, `crash-after-chain-before-commit`, `review-withholds-repeat-read` |
| Reorganization/RPC inconsistency | A previously confirmed attempt and paid quote are demoted to `MANUAL_REVIEW`; current and repeat delivery return 202 without report/bundle bytes, and no new transfer is initiated. | quote/attempt `chain_inconsistency`; F5 delivery invariant; payment-recovery runbook | `review-withholds-repeat-read`; F4 access vectors `quote-review-*`, `attempt-review-*`, `finality-unverified-*` express the HTTP boundary |
| Finality | Verify/settle success alone never creates an entitlement. Confirmation must be final and bound to exactly one authorization-specific Transfer before the atomic confirmation path; non-final confirmation returns/retains 202. Each paid read revalidates current finality. | TZ steps 4-8; `states.json` confirmation guards and `delivery_requires_current_confirmation`; OpenAPI report 200/202 | `verify-without-confirmation`, `crash-after-chain-before-commit`, `historical-paid-repeat-read`, `review-withholds-repeat-read` |
| Entitlement atomicity and replay | Receipt, chain event, confirmed attempt, paid quote, and exact report-digest entitlement become visible together. Before that commit no paid bytes are returned. After it, repeat report and evidence reads reuse the original digest/receipt with no new settlement. | TZ steps 7-8; `atomic_entitlement_commit`; delivery guards; OpenAPI report/evidence 200; artifact-recovery runbook | `crash-after-chain-before-commit`, `lost-http-response-after-commit`, `historical-paid-repeat-read` (A14/A17/A18) |
| Bounded reconciliation | UNKNOWN may become CONFIRMED only from authoritative confirmation; otherwise bounded exhaustion becomes MANUAL_REVIEW. Recovery never guesses from payer/amount/time and never invents a facilitator status endpoint. | TZ recovery paragraph; UNKNOWN edges; payment-recovery steps 2-5; `reconcileOne` | `timeout-without-hash`, `ambiguous-identical-transfers`, `crash-after-broadcast` |

Tests should assert state, HTTP code, paid-body absence/presence, exact settle-call
count, entitlement count/digest, and retained correlation independently. A test
that merely calls `StateMachines.next()` proves graph interpretation, not gateway
or recovery behavior.

## Mandatory fail-closed boundaries

- `unresolvedIdentity` and `unresolvedFinality` remain deliberate production
  blockers. Test fakes may be reviewed *test doubles* injected directly; no
  environment switch may turn the production placeholders into approval.
- No facilitator HTTP, Mezo RPC, wallet, signing, transfer, shared PostgreSQL,
  migration, deployment, release, exchange, or live-public request is permitted.
- No mock may be presented as proof of canonical authorization identity,
  nonce/replay-domain semantics, MUSD Transfer binding, canonical blocks, or a
  finality rule. Those are the unresolved F5 blockers in `states.json`, the
  gateway README, and the testnet-demo runbook.
- Do not edit expected results or change `runtime_status` in frozen vectors to
  make the tests pass. Runtime tests may cite vector IDs as traceability only.
- Do not mark A11-A12 or A14-A24 PASS in the acceptance result. The acceptance
  runner and schema distinguish executable evidence from a plan; mocks are a
  lower test level. A13 requires sanitized real transaction/block/log evidence,
  and A14's acceptance evidence is explicitly bound to passing A13.
- Do not claim persistence, concurrency, crash/restart durability, replay
  retention, or atomic database commit from an in-memory fake. Those require
  disposable PostgreSQL or later controlled integration evidence and are
  outside this route.

## Test gaps and likely contract defects

1. `apps/mezo-gateway/test/` currently contains only the F4 PostgreSQL and
   report-service suites. No executable gateway-owned test invokes
   `Gateway.read`, `Ledger.beginAttempt` through confirmation, `reconcileOne`,
   `recoverUnsubmitted`, `StateMachines`, `OfficialX402`, or
   `MezoReceiptReader`. Python contract tests validate frozen documents, not the
   TypeScript runtime.
2. The receipt-mismatch path appears inconsistent with the frozen graph.
   `Ledger.confirm` rejects a mismatched receipt with `PAYMENT_REJECTED`, but
   `Gateway.read` converts every non-`MANUAL_REVIEW` confirmation failure to
   `PAYMENT_UNCERTAIN` after leaving the attempt UNKNOWN. The contract's
   `inconsistent_receipt` transition requires quote and attempt
   `MANUAL_REVIEW`, artifact retention, and resubmit prohibition. A failing
   regression should lock this behavior before repair.
3. Reorganization/current-finality handling has no runtime test. The paid-read
   path calls `revalidate`, then `manualReview` on false or RPC manual-review
   errors, but no test proves both report and bundle bytes are withheld, both
   states are demoted, and settle count remains unchanged.
4. Pre-submit recovery has no runtime test for the paired quote/attempt result,
   expiry branch, zero settle calls, or bounded batch behavior. Likewise,
   reconciliation has no tests for confirmation, ten-attempt exhaustion,
   exceptions, backoff, and the absence of settlement calls.
5. Duplicate authorization handling is presently demonstrated only as a SQL
   uniqueness design and frozen-vector expectation. The local fake must model
   canonical identity uniqueness explicitly, while the final claim must say
   that real DB uniqueness was not exercised by this route.
6. Entitlement tests must cover partial-failure visibility. The fake should
   prove the application never returns paid bytes before its atomic-confirm
   operation succeeds, but cannot establish real PostgreSQL transaction
   atomicity or restart recovery.
7. The local slice should include report and evidence reads. The evidence route
   may never accept a payment signature or initiate settlement; after paid
   state it still requires current confirmation, matching entitlement, and
   intact artifact bytes.

## Stale or easily overstated documentation

- `apps/mezo-gateway/README.md` still says **F4 LOCALLY VERIFIED / REVIEW
  PENDING**, while `handoff.md` records F4 independent re-reviews PASS and the
  F4 durable package ready. The root README likewise says F4 verification is in
  progress/review pending. These status lines should be refreshed when the
  coordinator next updates repository state; they do not affect this F5 test
  design.
- The gateway README says the adapter uses official SDK verification and
  settlement, but the same section correctly states that unresolved identity
  and finality policies keep it disabled. Any F5 summary must preserve the
  second statement and must not shorten this to “x402 payment verified.”
- `engineering/changes/2026-09-24-mezo-evidence/tasks.md` accurately calls F5
  `IMPLEMENTED_UNVERIFIED` and leaves mocked replay/timeout/crash/duplicate
  tests open. Completing this route may close only that local mocked-test item,
  not the separately approved controlled-testnet-payment item.
- The runbooks describe future reviewed recovery paths and approved RPC/policy
  use. Local fake execution does not prove those operational mechanisms exist
  or are approved.

## Suggested evidence wording after a green route

“F5's local orchestration boundary passed deterministic in-process fault tests
for duplicate canonical authorization use, definitive pre-submit rejection,
unknown outcomes, no-resubmit recovery, receipt mismatch, reorganization,
finality gating, and entitlement reuse. No persistent database, facilitator,
RPC, wallet, transfer, testnet payment, deployment, or acceptance vector was
executed. Production authorization identity and finality remain unresolved;
all frozen vectors remain NOT_RUN and A13-A14 remain blocked.”
