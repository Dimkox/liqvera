# F6 local UI and operations verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f6-local-ui-and-operations-verification-26ffb2`
Created: 2026-09-29T10:03:15+00:00
Risk: high
Complexity: high-risk
Domains: frontend, data

## Problem

Verify and repair the Liqvera F6 local UI and operations boundary using deterministic browser tests, static configuration validation, and disposable local containers only: exercise cancel, wrong-network display, wallet account/chain switch, reload, quote recovery, no-resettlement behavior, fixture-profile isolation, health, resource limits, observability, and runbook accuracy. Preserve shadow-only safety; do not use a real wallet, RPC, facilitator, transfer, shared environment, deployment, release, exchange, live public capture, or testnet/mainnet payment.

## Outcome

The browser recovery boundary is executable and deterministic without a real
wallet or payment system: cancel, wrong-chain, account/chain changes, reload,
quote recovery, paid reuse, and every no-resettlement path are driven through
in-process fakes and observable rendered state. The fixture Compose profile is
statically proven to contain only fixture services, loopback publication, no
external-egress memberships, bounded resources, private metrics access, and
the required CSP. Documentation reports exactly this local evidence and does
not promote payment, deployment, release, or frozen-vector acceptance.

## Scope

### In scope

- Add a web-owned deterministic browser harness with a fake EIP-1193 provider,
  intercepted same-origin API, isolated `sessionStorage`, deterministic
  crypto/timers, and a test-only reviewed-adapter double.
- Introduce only the smallest injectable browser boot/controller seam required
  to test existing behavior; preserve public API payloads and production's
  unregistered x402 adapter.
- Prove cancellation, wrong network/switch, payer-preserving account switch,
  chain switch, reload/recovery, identical idempotent create replay,
  pending/uncertain/manual-review suppression, paid report/evidence reuse, and
  exact zero-or-one adapter invocation as appropriate.
- Correct fixture Compose service network membership so fixture capture,
  gateway, and edge have no external-egress networks; preserve live-only
  egress declarations and validate both resolved profiles statically.
- Make existing bounded metrics observable only over a dedicated internal
  operations boundary, with no host port and no Caddy route; validate safe
  labels and the health/readiness distinction deterministically.
- Add the restrictive edge CSP required by the canonical specification after
  validating the built Vite output needs no unsafe inline script.
- Reconcile runbooks, README, handoff, and acceptance wording with the evidence
  actually produced. All 156 frozen vectors remain `NOT_RUN`.

### Out of scope

- Starting containers or creating a local/shared database, schema, named
  volume, secret store, or external write in this phase.
- A real wallet, RPC, facilitator, x402 production adapter, signature,
  transfer, settlement, testnet/mainnet payment, or live public capture.
- Database/schema/storage migrations, backfills, API or event contract changes.
- Shared environments, deployment, release, push, exchange mutation, live
  services, public metrics exposure, or a new monitoring dependency.
- Relabelling A13/A14/A26/A28/A30 or any frozen vector as PASS. Browser tests
  provide scoped local behavior evidence only; A26 runtime isolation remains
  `NOT_RUN` without a separately approved disposable-container phase.

## Constraints

- Backward compatibility: keep `SavedFlow.version = 1`, existing API bodies,
  capability semantics, and the fail-closed production x402 boundary.
- Data/privacy: never read repository/user secrets; tests use synthetic values
  and must reject unplanned/cross-origin requests and sensitive metric labels.
- Performance: use fake timers and bounded polling; no wall-clock sleeps or
  unbounded browser retry loops.
- Operational: shadow-only remains intact. Fixture edge stays loopback-only;
  metrics stay internal-only; health never implies payment readiness.

## Human decision required

The route requires `scope_and_design_approval` before any product, test,
configuration, or runbook implementation. Approval covers only the exact
fake/static design above. `migration_or_external_write_approval` is not
applicable to this phase and remains unexercised; discovering a need for a
container start, schema/volume creation, real network I/O, or shared-system
write stops the route for a new exact approval.
