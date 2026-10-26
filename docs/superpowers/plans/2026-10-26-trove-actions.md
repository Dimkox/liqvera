# Trove Actions Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete report-bound wallet actions with safe previews and durable evidence.

**Architecture:** Extend the current EIP-1193 transaction module. Separate pure
arithmetic and browser evidence persistence from the DOM panel. Main passes the
verified delivery hash. One implementation owner; independent read-only review.

**Tech Stack:** TypeScript, ethers, node:test, Python artifact checks.

**Spec:** docs/superpowers/specs/2026-10-26-trove-actions-design.md

## Global Constraints

- No x402 changes, server signing, immutable report changes or new contracts.
- English UI/docs, Liqvera identifiers, Mezo Testnet chain 31611 only.
- bigint atomic quantities and WAD ratios; verified ABI provenance.
- Source, merge, deployment and wallet acceptance are distinct evidence phases.

## Review Focus

- Out-of-order previews and changed terms cannot reach signing.
- Pending/unknown outcomes survive remount/reload and cross-tab submission.
- Max satisfies gas, minimum debt and ICR/TCR limits at exact rounding boundaries.
- Receipt success survives refresh/storage errors without automatic resubmission.
- Exported evidence binds original delivery hash and distinguishes predictions.

### Task 1: Exact state, limits and protocol preparation

Files: packages/mezo-protocol/src/index.ts; apps/mezo-web/src/trove-math.ts;
apps/mezo-web/src/trove-transactions.ts; test/trove-rescue.test.mjs;
test/trove-transactions.test.mjs and test provider utility.
Interfaces: readTroveState(provider, account, blockTag), computeLimits(state,
balances), computeRescue(state, targetIcr), prepareTroveAction(provider, account,
action), submitTroveAction(provider, prepared, isCurrent).

- [ ] Write and run failing pure arithmetic and fixed-block transaction tests.
- [ ] Implement exact math, verified ABI reads, simulation, gas and borrow guards.
- [ ] Verify focused tests, protocol typecheck and browser typecheck; update handoff; commit.

### Task 2: Durable evidence and receipt recovery

Files: apps/mezo-web/src/trove-action-receipts.ts;
schemas/liqvera-trove-action-v1.schema.json; test/trove-action-receipts.test.mjs.
Interfaces: create/load/save report-bound receipts, unresolved borrower guards,
validated polling and JSON export consumed by the panel.

- [ ] Write and run failing pending/reload/storage/receipt validation tests.
- [ ] Implement record validation, persistent intents, receipt-only recovery and export.
- [ ] Verify focused tests and schema artifact checks; update handoff; commit.

### Task 3: Report action panel

Files: apps/mezo-web/src/trove-protection-panel.ts; src/main.ts; src/style.css
(if required); test/trove-protection-panel.test.mjs.
Interfaces: mountTroveProtection receives report SHA-256 as delivery metadata.
Consumes Task 1 preparation/state and Task 2 records.

- [ ] Write and run failing UI behavior tests for second click, rescue, Max,
  stale previews, pending locks, action log and storage fallback.
- [ ] Implement three forms, rescue, previews, explicit confirmation and recovery.
- [ ] Run all browser tests/build, relevant Python/provenance/schema tests and docs.
- [ ] Update README/handoff, exact completed test counts; commit.

### Task 4: Review, merge and delivery

- [ ] Obtain independent read-only review of actual diff; fix findings with regressions.
- [ ] Run complete product gate and inspect results. Open PR and await all CI checks.
- [ ] Merge authorized PR after green CI; verify post-merge CI.
- [ ] Deploy only reviewed web image using existing runbook; verify live bundle/health.
- [ ] If a usable wallet connection is available, execute authorized Testnet deposit
  and repayment through the buttons; retain actual receipts and document real hashes.
