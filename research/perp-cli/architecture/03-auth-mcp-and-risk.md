# 03 — Authentication, MCP boundary and integration risk

## Secret resolution

The CLI can resolve signing material through multiple tiers:

- explicit CLI private-key override;
- OWS wallet name / active OWS wallet;
- exchange-specific environment variables;
- generic `PRIVATE_KEY`;
- active wallet metadata;
- legacy `~/.perp/<exchange>.key`.

Source also contains agent-wallet paths for Pacifica, Hyperliquid, Lighter and
Aster. This makes the runtime capable of high-impact authenticated mutations;
a code consumer must not assume that constructing an adapter is read-only.

## MCP

`src/mcp-server.ts` describes itself as advisor mode and states that it does
not execute trades directly, instead returning market/account data and command
suggestions. It also has public market-data fallbacks that do not require
private keys.

This boundary is safer than the full CLI, but it is not equivalent to
anonymous public-only telemetry: some tools can access account data when keys
are configured, and the MCP process sits next to the same wallet/config
environment as the CLI.

External directories have reported different MCP tool counts over time. Do not
hard-code those cached counts; inspect the pinned source or runtime schema.

## Mutation and funds risk classes

The full CLI includes:

- place/edit/cancel/flatten order paths;
- leverage and stop-order mutations;
- funding-arbitrage execution;
- deposit/withdraw/transfer/bridge/rebalance;
- strategy/bot execution and background supervisors;
- wallet and agent approval/setup.

For Multi-Exchange Engine these belong behind a separate execution boundary.

## Recommended integration split

### Allowed first

- public markets / mark/index price;
- public order books;
- public funding rates/history;
- normalized exchange metadata;
- health/read-only capability detection;
- data types and error normalization.

### Review separately

- authenticated account balances/positions/orders;
- user-specific funding and PnL;
- websocket/account event streams.

### Forbidden in shadow-only runtime

- market/limit/stop orders;
- edit/cancel/cancel-all/flatten;
- leverage/margin/account-mode changes;
- agent approval / wallet mutation;
- deposit, withdraw, transfer, bridge, rebalance;
- background strategies that can trade.

## Security posture

The upstream security policy explicitly treats credential leakage, command
injection, unsafe trade defaults, JSON corruption and MCP exposure as in-scope
security issues and recommends sanitized logs without private keys or wallet
addresses. The research scripts follow the same principle: they never read
user wallet/config files and only acquire public source/package artifacts.
