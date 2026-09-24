# Test plan — Liqvera Mezo Evidence

## Risk-based scenarios

| Priority | Scenario | Required evidence |
| --- | --- | --- |
| P0 | Baseline regression | Full Stage A verification before and after changes |
| P0 | Double settlement/retry | 20-way concurrency plus crash and timeout tests |
| P0 | Paid artifact disclosure | Authorization and response-body assertions |
| P0 | Wrong chain/token/payer/receiver/amount | Fail-closed integration tests |
| P0 | Bundle tampering | Offline verifier non-zero exit and stable reason |
| P1 | Stale/crossed/insufficient-depth snapshot | Specific free rejection reason; no quote |
| P1 | Wallet cancellation/switch/reload | No implicit payment; recoverable UI state |
| P1 | External service outage | `BLOCKED_EXTERNAL` or readiness false |

## Automated checks

- Unit: exact parsing, arithmetic, canonical serialization, state transitions.
- Contract: OpenAPI/JSON Schema, reason codes, headers, atomic units.
- Integration: PostgreSQL constraints, idempotency, locking, entitlement.
- Fault: crash boundaries, facilitator/RPC timeout, ambiguous settlement.
- Security: capability isolation, redaction, archive hardening, network boundaries.
- E2E: fixture generation, unpaid 402, mocked settlement, repeat access.
- Static: Ruff, mypy, TypeScript checks, dependency and architecture graph checks.

## Manual and external checks

- Live-public Hyperliquid capture with preserved raw bytes and timing.
- Mezo Testnet chain/token/facilitator readiness.
- Operator-confirmed A13 payment with buyer distinct from merchant.
- Clean-machine offline verification and README reproduction.
