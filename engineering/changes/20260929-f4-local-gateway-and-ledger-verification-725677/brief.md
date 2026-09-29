# F4 local gateway and ledger verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f4-local-gateway-and-ledger-verification-725677`
Created: 2026-09-29T08:16:51+00:00
Risk: medium
Complexity: standard
Domains: api, data

## Problem

Verify and repair the Liqvera F4 local gateway and ledger boundary using disposable local fixtures only: build and typecheck the gateway, exercise API contract behavior, concurrent report creation, idempotency, artifact-loss reconciliation, and the lost cleanup-response recovery path. Use only ephemeral local state; no shared environment, external service, deployment, release, wallet, chain, exchange, or live execution.

## Outcome

The pinned gateway compiles and its local F4 boundary is executable against a
disposable PostgreSQL database. Concurrent identical creates converge on one
scoped request identity, and an expired unpaid artifact converges to `DELETED`
after either a first successful cleanup or a retry that authoritatively reports
the exact report is already absent. Malformed, mismatched, failed, or ambiguous
cleanup responses remain fail closed. No payment or external boundary is
enabled.

## Scope

### In scope

- Repair the two reproduced TypeScript compile errors without dependency or
  lockfile upgrades.
- Add a gateway-owned Node test harness using the existing toolchain.
- Characterize the internal cleanup HTTP contract, including both valid HTTP
  200 boolean results and all negative response classes.
- Apply and rerun the tracked `001_ledger.sql` through the gateway migrator on
  a uniquely identified disposable PostgreSQL instance.
- Add one forward-only `002_*` migration that replaces the shared immutable
  identity trigger function with table-specific nested guards. Exercise both a
  fresh `001 -> 002` install and an upgrade from an already applied 001 state.
- Prove database idempotency and scope isolation with at least 20 concurrent
  same-scope/key requests, plus lost cleanup-response ledger convergence.
- Characterize artifact-loss recovery as a fail-closed incident state.
- Refresh claims only for checks actually executed in this tranche.

### Out of scope

- Editing or replacing `001_ledger.sql`, adding any migration beyond the
  explicitly approved trigger-function repair `002_*`, changing the frozen F2
  vector catalog, or performing a backfill.
- Facilitator, RPC, wallet, chain, exchange, live capture, shared database,
  Compose deployment, release, push, or any external mutation.
- F5 authorization identity, settlement, confirmation, entitlement, or live
  reconciliation; F6 UI/deployment; broad F7 acceptance.
- Dependency upgrades, audit remediation, build-response retry design, or a
  production sealed-input recovery endpoint without a reproduced defect and
  separately approved scope.

## Constraints

- Backward compatibility: preserve inherited `mee-*` names, `/v1/*` routes,
  frozen schemas, public reason codes, and the x402 2.16.0 boundary.
- Data/privacy: synthetic fixtures and invocation-owned ephemeral PostgreSQL
  only; do not read `.env`, credentials, shared data, or production dumps.
- Performance: exercise at least 20 concurrent creates; keep cleanup batches
  bounded to ten with the existing two-second per-call timeout.
- Operational: preserve shadow-only and payment-disabled gates; the gateway
  remains the sole ledger writer and the report service the sole artifact
  deleter.
