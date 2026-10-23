# Liqvera

**Market reports you can verify.**

Understand BTC market depth before you act. Liqvera turns public order-book snapshots into clear, downloadable reports with the evidence behind every calculation.

[Open the demo](https://liqvera.site) · [Watch the demo](docs/competition/pitch.mp4) · [Documentation](docs/README.md) · [Commit history](https://github.com/Dimkox/liqvera/commits/main/)

## Mezo integration

[![Verify Liqvera](https://github.com/Dimkox/liqvera/actions/workflows/verify.yml/badge.svg)](https://github.com/Dimkox/liqvera/actions/workflows/verify.yml)

**Mezo Testnet · chain 31611.** MUSD purchases and the DEX comparison are deployed on [liqvera.site](https://liqvera.site). The October 23 wallet-free preview includes Mezo block 16321216, raw calls and offline-reproducible evidence. [Deployment and verification](docs/security/2026-10-23-mezo-dex-deployment.md).

| Contract | Testnet address | Use |
| --- | --- | --- |
| MUSD | [0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503](https://explorer.test.mezo.org/address/0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503) | Pay: 0.01 test MUSD per report |
| Permit2 | [0x000000000022D473030F116dDEE9F6B43aC78BA3](https://explorer.test.mezo.org/address/0x000000000022D473030F116dDEE9F6B43aC78BA3) | Wallet authorization |
| x402 exact proxy | [0x402085c248EeA27D92E8b30b2C58ed07f9E20001](https://explorer.test.mezo.org/address/0x402085c248EeA27D92E8b30b2C58ed07f9E20001) | MUSD settlement |
| DEX Router | [0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9](https://explorer.test.mezo.org/address/0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9) | Read: fixed-block quotes |
| PoolFactory | [0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A](https://explorer.test.mezo.org/address/0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A) | Read: captured pool fee |
| MUSD/BTC pool | [0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9](https://explorer.test.mezo.org/address/0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9) | Read: reserves and quote cross-check |
| BTC token | [0x7b7C000000000000000000000000000000000000](https://explorer.test.mezo.org/address/0x7b7C000000000000000000000000000000000000) | Read: pool identity and decimals |

Payment: browser → Permit2/EIP-2612 signature → facilitator → exact proxy → MUSD Transfer to the configured merchant → gateway checks canonical receipt and confirmations → report delivery. See the [browser](apps/mezo-web/src/x402.ts) and [gateway](apps/mezo-gateway/src/adapters/x402.ts) adapters. The public merchant is [0xd7F52d1Ddb5dC8678191f14E439Fc5DB67541535](https://explorer.test.mezo.org/address/0xd7F52d1Ddb5dC8678191f14E439Fc5DB67541535), supplied through `LIQVERA_PAY_TO`, with no built-in payment default.

| Historical successful 0.01 MUSD payment | UTC |
| --- | --- |
| [0x53808fff…117c](https://explorer.test.mezo.org/tx/0x53808fffb9f83d7946fcc0494d1c90491e8d83813d2795bb9ceb0957ed61117c) | 2026-10-13 13:13:09 |
| [0x4a04dc72…8455](https://explorer.test.mezo.org/tx/0x4a04dc72c9f4b9051262b5c14db18369b9140d3012f7b02c3c8d3c6952778455) | 2026-10-01 01:37:33 |
| [0xc5344f48…cb6f](https://explorer.test.mezo.org/tx/0xc5344f48b973d10f5925912e8c5f0b8c69ecdfe4e01ee15209f81771b0cccb6f) | 2026-10-01 00:12:04 |

**One-minute inspection:**

1. Open [liqvera.site](https://liqvera.site) and its wallet-free preview.
2. Inspect a [retained Mezo SELL capture](evidence/mezo-testnet/2026-10-23-dex-sell-native.json); its raw calls identify the exact block. The browser comparison appears on reports built with the extension enabled.
3. Open a payment above and inspect the MUSD Transfer: `10000000000000000` atomic units, or 0.01 MUSD.
4. Download the [preview evidence ZIP](https://liqvera.site/demo/snapshots/d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753/evidence.zip), [install the local packages](docs/mezo-integration.md#reproduce-from-source), then run `liqvera-evidence-verify evidence.zip` → `INTEGRITY_REPRODUCED`.
5. Check the [protocol evidence and limitations](docs/mezo-integration.md). The [Trove risk CLI preview](docs/mezo-trove-risk.md) adds borrower reports and offline ZIP verification in this branch; the gated API and browser are implemented in source, including a sealed native example; deployment and paid end-to-end acceptance remain separate. No registry contract is deployed.

Mezo quotes use exact arithmetic, the captured on-chain fee and no gas. Hyperliquid is a perpetual market; Mezo is spot. Testnet liquidity is not representative of executable Mainnet prices. [ABI and source provenance](packages/mezo-protocol/README.md#testnet-analytics-provenance-2026-10-23).

## From an order size to a clear answer

A headline price tells you where the market is. Liqvera shows how a hypothetical buy or sell would fill against the available liquidity: the average price, filled quantity, worst price and price impact.

Built for analysts, researchers and developers, each report combines public Hyperliquid BTC perpetual market data with exact arithmetic and portable evidence. Explore the result in your browser, export it for analysis or reproduce the calculations independently.

| What you get | Why it matters |
| --- | --- |
| Market-depth analysis | See how order size changes the calculated fill and price impact |
| Timestamped source snapshot | Know which market data the report uses |
| Downloadable JSON | Bring structured results into your own tools |
| Evidence ZIP | Keep the source inputs, report and integrity hashes together |
| Offline verification | Check the evidence and reproduce the calculations locally |
| MUSD payments through x402 | Purchase access to an individual report with your wallet |

## MUSD funding

After preparing a report, check the selected wallet’s MUSD balance, exact shortfall and estimated purchase budget. Download a block-bound funding check or open the official Mezo Borrow application after reviewing its separate loan risks. Return to the same quote and check again before confirming payment. This extension is available on the public Testnet demo. See [Wave 1 changes and evidence](docs/competition/wave1-musd-funding.md).

## Try Liqvera

**[Explore the public demo →](https://liqvera.site)**

View the timestamped sample report without connecting a wallet. To request your own:

1. **Connect your wallet** using a browser extension or WalletConnect on your phone.
2. **Choose buy or sell and a BTC quantity** to prepare a fresh report and review its price.
3. **Confirm the purchase** in your wallet on Mezo Testnet.
4. **Read, download and verify** your report. Confirmed access lets you retrieve the same report again without another payment, within its retention period.

The public demo runs on **Mezo Testnet (31611)**. Each report costs **0.01 test MUSD**. WalletConnect supports mobile pairing and QR connections; you can manage or disconnect your session from the app.

Reports describe a hypothetical sweep of the captured order book. Liqvera is a read-only analytics product: calculations cover the available snapshot depth and exclude fees and funding.

## Built for verifiable delivery

Liqvera connects market capture, report generation and MUSD payment in one web application. Payment access is bound to the exact report and evidence hashes. The offline verifier checks bundle integrity and recomputes results from the included inputs.

**Stack:** TypeScript · Python · PostgreSQL · Reown AppKit / WalletConnect · x402 · Docker Compose.

| Component | Source |
| --- | --- |
| Web application | [apps/mezo-web](apps/mezo-web) |
| API and payment gateway | [apps/mezo-gateway](apps/mezo-gateway) |
| Public market capture | [services/evidence-capture](services/evidence-capture) |
| Report generation and verification | [services/evidence-report](services/evidence-report) |
| API contract | [OpenAPI specification](schemas/mezo-evidence/v1/openapi.json) |

To run the project, clone the repository and follow the [startup guide](docs/runbooks/startup-shutdown.md). The [Testnet guide](docs/runbooks/testnet-demo.md) covers wallet checkout and deployment; the [validation guide](docs/validation.md) provides build and test commands.

## Source, history and versions

Development is tracked publicly in Git. Use the links below to inspect changes, identify a version or review the evidence behind a build.

- **[Commit history](https://github.com/Dimkox/liqvera/commits/main/)** — dated changes and exact commit identifiers.
- **[Releases](https://github.com/Dimkox/liqvera/releases)** — published release notes and assets.
- **[Version tags](https://github.com/Dimkox/liqvera/tags)** — named source versions.
- **[Compare revisions](https://github.com/Dimkox/liqvera/compare)** — review differences between commits, branches or tags.
- **[Published DEX verification](docs/security/2026-10-23-mezo-dex-deployment.md)** — deployed source e80474e: 1021 Python tests + 85 subtests, 107 browser tests; gateway 74 local passes (13 database tests skipped in hosted CI).
- **[DEX deployment package refresh](docs/security/2026-10-23-runtime-package-refresh.md)** — pinned musl/nginx fixes and candidate validation.
- **[Current validation evidence](docs/security/2026-10-21-getzilla-successor.md)** — passing Liqvera audit, failed tool self-check, exact deployment evidence and verification limits.

[Product specification](docs/specification.md) · [Architecture](docs/architecture.md) · [Security policy](SECURITY.md) · [Buildathon presentation](docs/competition/README.md)

Built by **[Dimkox](https://github.com/Dimkox)** for the [Mezo ecosystem](https://mezo.org/).
