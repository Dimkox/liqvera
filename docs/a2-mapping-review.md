# A2 manual perpetual mapping review

Review instant: `2026-07-27T14:07:38Z`

Decision policy: `MANUAL_OFFICIAL_CONTRACT_SEMANTICS/v1`

This review admits economic contract equivalence for capture and later
cross-venue analysis. It does not claim that the two marks, oracle inputs,
funding payments, liquidation rules, or executable prices are identical.

## Evidence snapshot

- Hyperliquid request:
  `POST https://api.hyperliquid.xyz/info`
  with `{"type":"metaAndAssetCtxs"}`.
- Hyperliquid response SHA-256:
  `1073a06fbac3f087e90b0a961f8427fbe30bf8cd5d74194c6edb30975016dc27`.
- Lighter request:
  `GET https://mainnet.zklighter.elliot.ai/api/v1/orderBooks`.
- Lighter response SHA-256:
  `3e213aca41ba636436fe71a31be760def3133a0b1eabfcdc26fcac920fd9a62c`.

The official Hyperliquid contract specification defines the standard product
as a linear perpetual representing one unit of the underlying. Its common
case uses a USDT-denominated oracle while USDC carries margin and PnL without
an FX conversion. HYPE is a documented USDC-oracle exception.

The official Lighter metadata defines each selected market as an active
perpetual, exposes minimum base/quote amounts and size/price precision, and
the WebSocket schema exposes order/trade size in base units and USD amounts.
Lighter perpetual accounts use USDC settlement balances.

## Accepted mappings

Membership was not selected by volume. The reviewed set was chosen before
runtime liquidity ranking and then checked against both current catalogs.

| Base | HL index / size dp | Lighter ID / size dp | Lighter minimum base | Quote reference |
|---|---:|---:|---:|---|
| BTC | 0 / 5 | 1 / 5 | 0.00020 | HL USDT oracle; Lighter USD index |
| ETH | 1 / 4 | 0 / 4 | 0.0050 | HL USDT oracle; Lighter USD index |
| SOL | 5 / 2 | 2 / 3 | 0.050 | HL USDT oracle; Lighter USD index |
| XRP | 25 / 0 | 7 / 0 | 20 | HL USDT oracle; Lighter USD index |
| HYPE | 159 / 2 | 24 / 2 | 0.50 | Both USD/USDC-oriented references |
| BNB | 7 / 3 | 25 / 2 | 0.02 | HL USDT oracle; Lighter USD index |
| ARB | 11 / 1 | 50 / 1 | 20.0 | HL USDT oracle; Lighter USD index |
| OP | 9 / 1 | 55 / 1 | 10.0 | HL USDT oracle; Lighter USD index |
| BCH | 26 / 3 | 58 / 3 | 0.010 | HL USDT oracle; Lighter USD index |
| ADA | 65 / 0 | 39 / 1 | 10.0 | HL USDT oracle; Lighter USD index |
| DOGE | 12 / 0 | 3 / 0 | 10 | HL USDT oracle; Lighter USD index |
| JUP | 90 / 0 | 26 / 1 | 15.0 | HL USDT oracle; Lighter USD index |

Every accepted record uses:

- USD valuation;
- USDC settlement;
- linear perpetual payoff;
- one base unit per displayed contract unit;
- `EXPLICIT_ORACLE_STABLECOIN_BASIS/v1`.

## Critical boundary

The mapping is suitable for raw-data collection, not sufficient for a trade.
The Hyperliquid USDT-oracle/USDC-PnL quanto convention and Lighter's USD index
can create basis even when both tickers and displayed prices look identical.
Funding, fees, minimum notionals, book depth, latency, withdrawals and
position reconciliation remain unproven. Runtime must reject stale registry
records, join current market IDs, collect positive venue-reported volume, and
rank only after manual membership has been fixed.

Sources:

- [Hyperliquid contract specifications](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications)
- [Hyperliquid perpetual metadata API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint/perpetuals)
- [Lighter orderBooks metadata](https://apidocs.lighter.xyz/reference/orderbooks)
- [Lighter WebSocket schema](https://apidocs.lighter.xyz/docs/websocket-reference)
- [Lighter USDC perpetual collateral](https://apidocs.lighter.xyz/docs/deposits-transfers-and-withdrawals)
