# VOOI: index of static reverse-engineering findings

Snapshot date: **2026-08-10**. Analysis is limited to official public surfaces, documentation, and pinned revisions of `vooi-app` repositories; authentication, wallet connection, trading, and financial operations were not performed.

## Report contents

1. [`architecture/01-client-surfaces-and-clients.md`](architecture/01-client-surfaces-and-clients.md) — Ultra, Pro, Light, Telegram Mini App, MCP, and four official programmatic clients.
2. [`architecture/02-api-and-auth.md`](architecture/02-api-and-auth.md) — reconstructed interaction model, API surface, SSE, onboarding/signing, transfer/withdraw, and venue abstraction.
3. [`architecture/03-risks-and-integration.md`](architecture/03-risks-and-integration.md) — confidence boundaries, risks, and a safe integration path for Multi-Exchange Engine.

## Main finding

VOOI provides a unified API-first execution layer over several perp venues, but its generated SDK combines public market-data reads, private state, trading, account parameter changes, broker approval, transfers, and withdrawals. A potential Multi-Exchange Engine adapter must therefore start only with a separate read-only shadow boundary and an explicit route allowlist. All mutation/funds-moving paths in the current research package are marked `forbidden` or `strictly_forbidden`.

The complete machine-readable map is in `data/api-surface-*.csv`; the client inventory and pinned SHAs are in `clients.lock.json`.
