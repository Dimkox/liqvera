# VOOI: static reverse-engineering findings

Snapshot date: **2026-08-10**
Method: analysis of official web surfaces, documentation, and public repositories
of the `vooi-app` organization; without authenticated requests or execution of trading
code.

## 1. Client surface map

### VOOI Ultra

`https://ultra.vooi.io/` is the current primary product. At the time of inspection, the live
footer showed `VOOI Ultra Beta v1.0.1`. The interface includes:

- a single long/short position;
- hedge placement;
- positions, orders, order history, and trade history;
- separate arbitrage positions/history;
- an API-token console and MCP onboarding;
- public market pages and Arbitrage Desk.

The public changelog records `Arbitrage Desk v1.0.0` dated 2026-07-23, while
the live terminal already showed `v1.0.1`. This is a typical sign that the footer and
changelog are updated independently.

### VOOI Pro

`https://pro.vooi.io/` remains operational and shows `VOOI Pro v1.12.0`.
The terminal has a market/limit/stop-limit form, chart/orderbook, positions, orders, and
history. Official release notes date v1.12.0 to 2025-12-18. The product appears
to be the previous professional branch, rather than the primary new API-first
surface.

### VOOI Light

`https://app.vooi.io/` shows `VOOI Light v2.5.0`, but explicitly states that
VOOI Light shut down. Migration/sign-in, staking, send, and claim
surfaces remain. For a new integration, Light should be treated as a historical source,
rather than an active trading target.

### Telegram Mini App

Official entry point: `https://t.me/VooiAppBot/vooi`. This is a Telegram WebApp,
not an APK. Release notes report the launch of a mini-app version of the trading terminal on
2024-10-01. No publicly verifiable separate source repository for the Mini App was
found.

### VOOI Perps MCP

Remote Streamable HTTP endpoint:

```text
https://perps-api.vooi.io/mcp
```

The official `vooi-app/mcp` contains only configuration examples and an MIT
license. This repository contains no MCP server implementation. Onboarding
through Ultra requires a Bearer token and offers configurations for Claude, Codex,
Cursor, and other MCP clients.

## 2. Official public programmatic clients

### `vooi-app/vooi-signals-bot-example`

Pinned commit:

```text
bb81ee0d5e48246f63b25f39a552622cc23af97d
```

Architecture:

1. Telegram ingestion.
2. Message parsing and LLM-assisted signal parsing.
3. Normalization/market resolution.
4. VOOI REST calls through async `httpx.AsyncClient`.
5. SSE listener.
6. PostgreSQL/Alembic persistence.
7. Order lifecycle, reconciliation, TP/SL and safety watchers.
8. Audit/alerting.

Observed client properties:

- default base URL `https://perps-api.vooi.io`;
- `Authorization: Bearer ...`;
- JSON request/response boundary;
- retry for 429 and selected 5xx responses;
- `Retry-After` plus exponential backoff;
- correlation identifiers;
- Authorization redaction in logs;
- separate configuration of risk/circuit-breaker parameters.

This is the most illustrative Python reference for the transaction lifecycle, but it
can place real orders and must not be imported into the shadow-only
runtime.

### `vooi-app/vooi-funding-bot-example`

Pinned commit:

```text
c3ceab29e80bb26fd6bde128280cb5da5428f3f1
```

A Python client for delta-neutral funding arbitrage. The repository includes:

- a large MVP coordinator;
- SSE module;
- strategy, risk, position, reporting and execution boundaries;
- read-only `probe` package;
- Docker packaging and tests;
- dry-run configuration.

The license is MIT with an additional trading disclaimer. The repository itself warns
that the bot can place real orders and recommends starting with
`BOT_DRY_RUN=true`.

### `vooi-app/vooi-mm-bot-example`

Pinned commit:

```text
879d15c677e9840dfe4164e3e700bf54c72d5082
```

TypeScript/Node.js >=18 market-making client:

- generated SDK from `@hey-api/openapi-ts`;
- explicit Bearer Authorization header;
- market resolver;
- SSE reconnect/backoff;
- two-sided maker quotes on the primary leg;
- hedge leg;
- margin preflight;
- shutdown cleanup;
- read-only `check` and `markets` commands.

The pinned revision dropped Bun and switched to Node/`tsx`: the commit message
states that the VOOI API edge rejected requests from the Bun HTTP stack, while Node
worked. This is an observation about a specific version, not a universal claim about
all future Bun releases.

### `vooi-app/mcp`

Pinned commit:

```text
9a5fc1aba5411a0c6e29822628b5ea834889caa7
```

README/config repository. It documents the remote MCP URL and Bearer header but
contains no server code, tool handlers, or exchange adapters.

