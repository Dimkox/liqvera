# Architecture — Liqvera Mezo Evidence

The normative architecture is defined in
`docs/superpowers/specs/2026-09-24-mezo-evidence-design.md`.

## Boundaries

| Component | Authority | Forbidden authority |
| --- | --- | --- |
| Capture | Allowlisted public Hyperliquid reads; unique raw-package writes | DB, payment, wallet, exchange mutation |
| Report service | Read sealed input; exact calculation; write immutable report/bundle | Internet, payment, DB, trading |
| Gateway/UI | Public API, capability auth, x402, ledger, artifact reads | Artifact mutation, exchange mutation, merchant private key |
| PostgreSQL | Payment/entitlement state and audit | Raw evidence storage, exchange state |

## Key decisions

- Python remains the analytical source of truth.
- TypeScript/Express is the x402 integration boundary.
- PostgreSQL is the sole ledger writer.
- Exact market values never pass through binary floating point.
- Only `eip155:31611` is accepted.
- Unknown payment outcomes stop settlement retries and enter reconciliation.

## Risks and mitigations

- Double charge: unique authorization identity, transactional locking, and no blind retry.
- Paid artifact leak: capability auth, no static path, private/no-store caching.
- Fabricated market identity: stored evidence with real hash and explicit validity.
- Public-clone drift: F1 repairs reproducibility before feature work.
- External outage: explicit `BLOCKED_EXTERNAL` evidence; no fixture fallback in live mode.
