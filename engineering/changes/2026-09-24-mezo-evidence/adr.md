# Draft ADR — Liqvera report and payment boundary

Status: proposed; not accepted until F1 review.

## Decision

Keep capture, identity validation, exact analytics, report construction, and
offline verification in Python. Add a TypeScript/Express gateway solely for
the official x402 EVM SDK, browser delivery, and public HTTP API. Use
PostgreSQL for durable quote/payment/entitlement state and immutable files for
report bytes. Permit only Mezo Testnet `eip155:31611`.

## Rationale

This reuses the tested analytical core, avoids reimplementing exact arithmetic
or payment cryptography, and isolates public-data, offline-analysis, and
payment authorities. It also makes mainnet and exchange mutation absent by
construction instead of relying on operator convention.

## Consequences

- Two runtimes and their lockfiles must be maintained.
- Contracts must be machine-readable and frozen before gateway implementation.
- PostgreSQL migrations and recovery logic become release-critical.
- A missing merchant address or external testnet capability blocks payment
  readiness but not report development.

## Rejected alternatives

- Rewriting analytics in TypeScript: duplicates exact and provenance logic.
- Adding x402 directly to Python: diverges from the approved official SDK boundary.
- In-memory payment state: cannot guarantee recovery or prevent duplicate settlement.
- Mainnet-configurable deployment: outside the authorized release boundary.
