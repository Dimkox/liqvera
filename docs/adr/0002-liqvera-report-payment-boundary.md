# ADR-0002 — Liqvera report and payment boundary

Status: accepted
Date: 2026-09-24
Scope: the approved F1 architecture boundary, not F2 contracts or release approval.

## Decision

- Python owns public capture, identity validation, exact analytics, report
  construction, and offline verification.
- A future TypeScript/Express gateway owns only browser delivery, the public
  HTTP API, and the official x402 SDK boundary. It does not implement analytics
  or mutate report bytes.
- PostgreSQL is the future authoritative payment and entitlement ledger;
  the gateway is its sole writer. Immutable files remain authoritative for
  artifact bytes and are published by atomic rename.
- Mezo Testnet `eip155:31611` is the only authorized payment network.
- Mainnet, custody, live exchange mutation, merchant private keys, user
  secrets, and exchange credentials are excluded from this product boundary.
  The existing shadow-only safety gate remains in force.

## Rationale

Reuse the tested Python analytical core and exact arithmetic. Isolate public
capture, offline computation, and payment authority. Use the official x402
SDK at a bounded gateway and durable ledger state for recovery.

## Consequences and limits

Two runtimes and their dependency locks will need maintenance. F2 must define
and review API payloads, JSON Schemas, reason codes, state graphs, database
contracts, and test vectors before gateway implementation. This ADR accepts
none of those detailed contracts and does not claim that the gateway,
ledger, new report builder, or payment flow already exists.

The F1 public compatibility result is `COMPATIBILITY_PASS_PAYMENT_BLOCKED`.
`PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED` keep payment readiness false.
Compatibility does not authorize a signature, settlement, deployment, or
release. F1 is complete-with-blockers, including
`BLOCKED_TRIVY_HEALTHCHECK_POLICY`; its exact verification results are in
[F1 evidence](../../engineering/changes/2026-09-24-mezo-evidence/evidence/f1-verification.md).

Before payment state exists, new stateless components can be reverted. Once
payment state exists, preserve the ledger and immutable artifacts, disable
new quote creation, and recover by forward fix; no destructive rollback.

## Rejected alternatives

- Rewriting analytics in TypeScript duplicates exactness and provenance logic.
- Adding x402 directly to Python diverges from the approved SDK boundary.
- In-memory payment state cannot provide the required durable recovery.
- Mainnet-configurable deployment exceeds the authorized network boundary.
