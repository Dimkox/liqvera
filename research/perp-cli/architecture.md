# perp-cli: static reverse-engineering results index

Snapshot date: **2026-08-10**. Because the authoritative implementation is already
published as TypeScript source, the analysis focuses on distribution provenance,
runtime wiring, signing boundaries, and separation of read-only/mutation/funds,
rather than decompilation.

## Report contents

1. [`architecture/01-packaging-and-surfaces.md`](architecture/01-packaging-and-surfaces.md) — source repo, npm, bin entry points, agent skill, mirrors/indexes.
2. [`architecture/02-runtime-and-adapters.md`](architecture/02-runtime-and-adapters.md) — CLI runtime, `ExchangeAdapter`, 4 DEX, public endpoints and outcome surface.
3. [`architecture/03-auth-mcp-and-risk.md`](architecture/03-auth-mcp-and-risk.md) — private-key/OWS/agent resolution, MCP role, trade/funds mutations and integration boundaries.

## Main finding

`perp-cli` is a convenient unified execution layer, but its core adapter contract
combines public market reads, account state, order mutations, and leverage/risk
operations. The CLI adds bridge/rebalance/funds and long-running
strategies on top. For Multi-Exchange Engine, the safe reuse boundary is types,
normalization, and a separate read-only market-data layer. The full adapter/CLI
must not be connected to a shadow-only runtime without an explicit policy split.
