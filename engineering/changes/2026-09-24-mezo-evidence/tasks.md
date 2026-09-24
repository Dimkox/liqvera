# Tasks — Liqvera Mezo Evidence

## F0 — public snapshot

- [x] Public repository, provenance, and anonymous clone exist.
- [x] Brand and canonical specification are present.

## F1 — baseline and compatibility

- [x] Capture initial baseline commands and failures.
- [x] Probe Hyperliquid, Mezo RPC, MUSD, facilitator, and npm registry read-only.
- [x] Write and approve the F1 design.
- [x] Author the task-by-task F1 implementation plan.
- [x] Repair architecture inventory for publication files.
- [x] Make salvage evidence reproducible from a public clone without overstating provenance.
- [x] Create a pinned isolated Python development environment.
- [x] Run complete baseline verification and classify every residual failure.
- [x] Record the narrow accepted ADR and compatibility lock.
- [x] Update `handoff.md` and commit F1 independently.
- [x] Repair final-review wire framing/deadline finding and refresh SHA-bound evidence.

F1 status: **complete-with-blockers**. Evidence is in
`evidence/f1-verification.md`, bound to implementation commit
`37d3e2cf3c64ef2c5d260bccf64e4f107e3f2c25`.
`make verify` passes; `grok_verify` still fails with
`BLOCKED_TRIVY_HEALTHCHECK_POLICY`. The compatibility package is complete
but payment readiness remains false: `PAY_TO_MISSING` and
`FINALITY_RULE_UNVERIFIED`. No F2–F7 completion is implied.
The renewed suite passes 641 tests and 85 subtests; independent re-review
found no remaining Critical or Important issue.

## F2 — contracts

- [x] Author the [F2 implementation plan](../../../docs/superpowers/plans/2026-09-24-liqvera-f2-contracts.md) for review.
- [x] Complete scoped independent plan re-review at `50f16225c23f5fde046b483321f86bb7d6bbf4f1`: all ten findings addressed; no new Critical or Important issue.
- [x] Obtain human review and approval of the F2 plan before implementation.
- [x] Integrate the six isolated artifact slices and Task 1/3 scoped review repairs.
- [x] Add exact schema/test/evidence graph bindings and clarify the 202 recovery body.
- [ ] Freeze OpenAPI, JSON Schemas, reason codes, and state graphs.
- [ ] Add exact BUY/SELL vectors and invalid-input contract tests.
- [ ] Add payment atomic-unit and idempotency vectors.
- [x] Integrate Task 6 on-disk vector-envelope repair and fix state-schema self-validation.
- [ ] Complete scoped repair re-review and whole-branch independent review.
- [x] Pass integrated graph, focused tests, Ruff, `make verify` and bare pytest; classify Grok's inherited Trivy failure.
- [x] Complete independent whole-branch review of integration commit `644cb702ae879b9d7c8acac1039eb8c5bf37d2aa` and implement its consolidated repair.
- [x] Verify the consolidated repair: 368 focused tests; 1009 tests and 85 subtests in both full runs; graph/Ruff pass, only inherited Trivy fails Grok.
- [ ] Pass independent scoped re-review before F2 closure.

F2 status: **consolidated repair implemented; scoped re-review pending**. The owner approved the repaired
plan and parallel task implementation; shared-file integration has one owner.
The artifacts above exist, but final freeze and acceptance await independent
review. Integration passed 329 focused tests and two full 970-test/85-subtest
runs; only the inherited Trivy policy blocks Grok. Tasks 1 and 3 passed scoped repair re-review; Task 2 was
approved, Task 4's shared-file findings are addressed by integration, and
Task 5's approved Minor wording is corrected. Whole-branch review then found
endpoint/oracle, fixture/quote eligibility, numeric and readiness consistency
gaps; the consolidated repair implements those corrections and exact timestamp
comparisons without adding runtime behavior. The evidence draft awaits scoped
re-review. Runtime vectors remain `NOT_RUN`, A13–A14
remain `BLOCKED_EXTERNAL`, and no receipt, payment or release is authorized.

## F3 — evidence report

- [ ] Replace synthetic timing and placeholder live identity evidence.
- [ ] Implement report builder, canonical serialization, manifest, and bundle.
- [ ] Implement hardened offline verifier and tamper tests.

## F4 — API and ledger

- [ ] Add gateway, migrations, capability authorization, and quote creation.
- [ ] Add protected unpaid 402 flow without real settlement.
- [ ] Add integration, concurrency, and artifact-loss tests.

## F5 — x402 settlement

- [ ] Add pinned SDK adapter and runtime readiness checks.
- [ ] Add durable verify/settle/reconciliation/entitlement state transitions.
- [ ] Pass mocked replay, timeout, crash, and duplicate-attempt tests.
- [ ] Run separately approved controlled testnet payment.

## F6 — UI and operations

- [ ] Implement one-page English testnet flow.
- [ ] Add isolated Compose, limits, observability, and runbooks.
- [ ] Test cancel, wrong network, wallet switch, reload, and recovery.

## F7 — acceptance

- [ ] Run full verification and independent reviews.
- [ ] Complete A01–A30 evidence report against the final commit.
- [ ] Prepare demo script and competition materials without unsupported claims.
