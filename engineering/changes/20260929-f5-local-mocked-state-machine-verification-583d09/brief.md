# F5 local mocked state-machine verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f5-local-mocked-state-machine-verification-583d09`
Created: 2026-09-29T09:13:06+00:00
Risk: medium
Complexity: standard
Domains: data

## Problem

Verify and repair the Liqvera F5 local mocked state-machine boundary: exercise deterministic duplicate-use rejection, pre-submit failure, unknown outcome, retry prohibition, receipt mismatch, reorganization, finality, entitlement, and recovery transitions with in-process fakes and temporary local files only. No persistent store, migration, wallet, RPC, transfer, shared environment, deployment, release, exchange, or live execution.

## Outcome

The real gateway and reconciliation orchestration are exercised with deterministic
in-process doubles. A receipt-binding rejection after submission immediately
enters manual review, creates no entitlement, releases no bytes, and never
settles again.

## Scope

### In scope

- A Node test vertical around `Gateway.read`, frozen `states.json`,
  `reconcileOne`, and `recoverUnsubmitted`.
- An in-memory ledger, scripted payment port, fake clock/state, and temporary
  artifact files owned only by tests.
- Duplicate canonical authorization use, definitive pre-submit recovery,
  post-submit unknown outcomes, no-resettle reconciliation, receipt mismatch,
  confirmation/entitlement replay, and reorg/finality withholding.
- The smallest orchestration fix for a reproduced post-confirmation
  `PAYMENT_REJECTED` receipt-binding error.
- Accurate F4/F5 README and handoff status.

### Out of scope

- PostgreSQL, migrations, persistent/shared stores, facilitator/RPC/network,
  wallet/signing/transfer, exchange access, deployment, release, and push.
- Production authorization-identity or finality policy approval.
- Claiming `MANUAL_REVIEW` recovery when the current runtime cannot lease or
  idempotently restore that state.
- Changing any frozen vector result; all 156 remain `NOT_RUN`.

## Constraints

- Backward compatibility: preserve HTTP 202 fail-closed responses and all
  public contracts; only internal state classification changes.
- Data/privacy: synthetic identifiers and temporary bytes only.
- Performance: deterministic unit tests; no timers or network waits.
- Operational: shadow-only remains; no live payment readiness is inferred.
