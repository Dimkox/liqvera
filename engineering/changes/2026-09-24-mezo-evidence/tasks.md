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
- [ ] Review and approve the F2 plan before implementation.
- [ ] Freeze OpenAPI, JSON Schemas, reason codes, and state graphs.
- [ ] Add exact BUY/SELL vectors and invalid-input contract tests.
- [ ] Add payment atomic-unit and idempotency vectors.

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
