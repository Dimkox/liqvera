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
- [x] Freeze OpenAPI, JSON Schemas, reason codes, and state graphs.
- [x] Add exact BUY/SELL vectors and invalid-input contract tests.
- [x] Add payment atomic-unit and idempotency vectors.
- [x] Integrate Task 6 on-disk vector-envelope repair and fix state-schema self-validation.
- [x] Complete scoped repair re-review and whole-branch independent review.
- [x] Pass integrated graph, focused tests, Ruff, `make verify` and bare pytest; classify Grok's inherited Trivy failure.
- [x] Complete independent whole-branch review of integration commit `644cb702ae879b9d7c8acac1039eb8c5bf37d2aa` and implement its consolidated repair.
- [x] Verify the consolidated repair: 368 focused tests; 1009 tests and 85 subtests in both full runs; graph/Ruff pass, only inherited Trivy fails Grok.
- [x] Pass independent scoped re-review before F2 closure.
- [x] Implement final follow-up: bidirectional reencoding coverage, arbitrary-precision fractional timestamps, and complete readiness truth tables.
- [x] Verify the final follow-up: 445 contract tests; 1086 tests and 85 subtests in both full runs; graph/Ruff pass, only inherited Trivy fails Grok.
- [x] Obtain independent final follow-up re-review; retain draft evidence until all findings are addressed.
- [x] Require a nonempty blocker explanation for false payment readiness in /readyz as well as capabilities.
- [x] Verify the readiness micro-fix: 130 resource tests, 446 F2 tests, 1087 tests plus 85 subtests in both full runs; only inherited Trivy fails Grok.
- [x] Independently re-review the readiness micro-fix before F2 closure.
- [x] Finalize SHA/tree/fingerprint-bound evidence in a documentation-only closure commit.

F2 status: **static contract phase complete**. The owner approved the repaired
plan and parallel task implementation; shared-file integration had one owner.
Code/security/edge/acceptance final independent session reviews all APPROVED
`3729bdc131ca4ac971ab04e735da2e113d68ad71` with no remaining findings. Final
tree `155d7fb44f5953f814f5463c381dde14932a8ab3` and fingerprint
`2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a` are bound
in [F2 evidence](evidence/f2-contracts.md); the earlier integration/repair
counts above are historical, not current receipts. Final results: 130 resource
tests, 446 F2 tests, 1087 tests plus 85 subtests in both full runs;
graph/Ruff/diff pass and Grok exits 1 only for two inherited LOW DS-0026 findings.

The overall change stays `implementing`; F3–F7 remain open and F3 is next.
All 156 vectors and A02–A06/A10–A12/A15–A20 remain `NOT_RUN`; A13–A14 remain
`BLOCKED_EXTERNAL`. Payment readiness is false. Trivy, PAY_TO_MISSING,
FINALITY_RULE_UNVERIFIED, funded buyer and SDK/canonical authorization identity
blockers remain. Closure changes documentation only after the approved
implementation; it claims no payment, deploy, release, push, runtime acceptance
or factory receipt.

## F3 — evidence report

- [x] Narrow the [F3 implementation plan](../../../docs/superpowers/plans/2026-09-24-liqvera-f3-evidence-report.md) to the user-approved fixture MVP.
- [x] Implement the exact BUY/SELL `SIMULATED` report kernel over an existing frozen fixture package.
- [x] Add the fixture-only CLI and deterministic prototype ZIP containing `report.json` plus `sealed-input/`.
- [x] Add `make mvp` and run one local end-to-end fixture smoke test.
- [ ] Harden and verify canonical F3 after the planned factory update.

F3 status: **fixture MVP implemented; canonical F3 remains open**. `make mvp`
produced a schema-shaped `SIMULATED` report and an eight-member deterministic
prototype ZIP. This is unverified, non-chargeable output with execution
authority `NONE`. Hardened verification, runtime schema validation, live
capture, identity approval, A08/A09, runtime results, and acceptance claims are
deferred. The local browser MVP implementation is tracked below; canonical
payment, gateway, and database work, factory/graph integration, deployment,
and release are deferred. F2 closure, all 156 `NOT_RUN`
vector statuses, and existing blockers are unchanged.

### Local browser MVP — implementation slices

- [x] Add `make mvp-web` wiring and document the local browser flow, overrides, storage, and stop behavior.
- [ ] Integrate the isolated SQLite demo flow, HTTP adapter, and browser assets into one tree.
- [ ] Update factory and architecture graph bindings for the integrated files.
- [ ] Verify the integrated runtime and repair defects in the deferred phase.

This docs/wiring commit contains the Makefile target and instructions only;
`scripts/run-mvp-web.py` and its dependencies are pending integration. No
browser smoke test, factory receipt, canonical F3–F7 completion, or runtime
acceptance is claimed. The local demo uses fixture data and an explicitly
simulated `NO TRANSFER` unlock, outside the chargeable `/v1/*` states.

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
