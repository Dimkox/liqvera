# 02 — Runtime and exchange-adapter architecture

## CLI wiring

`src/index.ts` uses Commander and registers market/account/trade/outcome/arb,
wallet, funds, strategy, risk, history, settings, backtest, portfolio, alerts
and setup flows. Global machine-facing controls include `--json`, `--fields`,
`--ndjson` and `--dry-run`.

The process deliberately loads `~/.perp/.env` rather than a project-local
`.env`, then resolves wallets through several tiers (explicit flags, OWS,
exchange env vars, active wallets and legacy key files).

## Exchange abstraction

The common `ExchangeAdapter` contract combines four classes of operations:

1. Market data: markets, orderbook, recent trades, funding, klines.
2. Account reads: balance, positions, orders, history, funding payments.
3. Trading mutations: market/limit/edit/cancel/cancel-all.
4. Risk mutations: leverage and stop orders.

That abstraction is operationally convenient, but it is too broad to import
unchanged into a read-only engine.

## Built-in registry

| exchange | alias | chain | public surface observed in source |
|---|---|---|---|
| Pacifica | `pac` | Solana | `https://api.pacifica.fi/api/v1/info/prices` |
| Hyperliquid | `hl` | EVM/HyperEVM | `https://api.hyperliquid.xyz/info` |
| Lighter | `lt` | Ethereum | `https://mainnet.zklighter.elliot.ai` |
| Aster | `ast` | BNB | public reads are implemented through `AsterAdapter`; no shared URL constant in `src/api/public/urls.ts` |

Hyperliquid and Lighter also have testnet URL switching in shared public API
configuration. Pacifica has no public testnet API in that shared mapping.

## Hyperliquid Outcome (HIP-4)

Version 0.13.0 adds a separate outcome-market surface. The changelog describes
fully collateralized USDH-quoted binary/range contracts, an
`OutcomeAdapter`-style abstraction and `perp outcome` commands for listing,
reading books/positions/orders and placing/canceling orders.

This is a distinct asset class from standard leveraged perps and should not be
collapsed into normal perp position semantics in a downstream engine.

## Post-release main hardening

Current `main` is newer than the 0.13.0 release and contains a numeric
validation audit. Recent commits explicitly convert NaN/non-finite venue data
from silent fallbacks into typed errors across trade validation, Lighter,
rebalance and observability paths. This matters when comparing the npm release
tarball with Git `main`: they can differ materially even while package.json
still says `0.13.0`.
