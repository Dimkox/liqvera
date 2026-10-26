# Liqvera

**Market reports you can verify.**

Understand BTC liquidity and Mezo MUSD borrower risk. Liqvera turns public market and protocol snapshots into downloadable reports with the evidence behind every calculation.

[Open the demo](https://liqvera.site) · [Watch the demo](docs/competition/pitch.mp4) · [Documentation](docs/README.md) · [Commit history](https://github.com/Dimkox/liqvera/commits/main/)

## Live on Mezo testnet

- **Demo video (2:00):** [Watch on YouTube](https://www.youtube.com/watch?v=-j9XZwQ1YxU)
- **openTrove:** [Mezo Testnet transaction](https://explorer.test.mezo.org/tx/0xb8217e58722274bb45c2bcdfcd7e94850078c6c0c576b24cb3203e469993bb78)
- **repayMUSD (Trove protection):** [Mezo Testnet transaction](https://explorer.test.mezo.org/tx/0x1393a6706bc51d5ca16aa054b3fbf60adb5a8cb4911180ff50aae4d03e66180b)
- **Paid Trove report (x402, MUSD):** [Mezo Testnet transaction](https://explorer.test.mezo.org/tx/0x30e9a3a6c73fa85d33d8204d5e2106fcc23eb0d74ce8e58528676ac3a775a0d5)

## Mezo integration

[![Verify Liqvera](https://github.com/Dimkox/liqvera/actions/workflows/verify.yml/badge.svg)](https://github.com/Dimkox/liqvera/actions/workflows/verify.yml)

**Mezo Testnet · chain 31611.** MUSD access, the DEX comparison, Trove risk and wallet-signed Trove/DEX actions are deployed on [liqvera.site](https://liqvera.site) (PR #25). Wallet-free examples include fixed-block native calls and offline-reproducible evidence. [Current deployment and verification](docs/security/2026-10-24-wallet-actions-deployment.md). Transactions are prepared from fresh on-chain state and submitted only when the connected user signs in their wallet; Liqvera never accesses signing keys. The transaction links above document a Trove opening, a MUSD repayment and a paid Trove report.

### Mezo contracts used

| Contract | Testnet address | Use |
| --- | --- | --- |
| MUSD | [0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503](https://explorer.test.mezo.org/address/0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503) | Pay: 0.01 test MUSD per report |
| Permit2 | [0x000000000022D473030F116dDEE9F6B43aC78BA3](https://explorer.test.mezo.org/address/0x000000000022D473030F116dDEE9F6B43aC78BA3) | Wallet authorization |
| x402 exact proxy | [0x402085c248EeA27D92E8b30b2C58ed07f9E20001](https://explorer.test.mezo.org/address/0x402085c248EeA27D92E8b30b2C58ed07f9E20001) | MUSD settlement |
| DEX Router | [0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9](https://explorer.test.mezo.org/address/0x9a1ff7FE3a0F69959A3fBa1F1e5ee18e1A9CD7E9) | Quotes and user-signed spot swaps |
| PoolFactory | [0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A](https://explorer.test.mezo.org/address/0x4947243CC818b627A5D06d14C4eCe7398A23Ce1A) | Read: captured pool fee |
| MUSD/BTC pool | [0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9](https://explorer.test.mezo.org/address/0xd16A5Df82120ED8D626a1a15232bFcE2366d6AA9) | Read: reserves and quote cross-check |
| BTC token | [0x7b7C000000000000000000000000000000000000](https://explorer.test.mezo.org/address/0x7b7C000000000000000000000000000000000000) | Pool identity; exact user-signed approvals |
| TroveManager | [0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0](https://explorer.test.mezo.org/address/0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0) | Read: borrower debt, collateral and ratios |
| BorrowerOperations | [0xCdF7028ceAB81fA0C6971208e83fa7872994beE5](https://explorer.test.mezo.org/address/0xCdF7028ceAB81fA0C6971208e83fa7872994beE5) | Wallet-signed BTC deposit and MUSD repayment |
| HintHelpers | [0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6](https://explorer.test.mezo.org/address/0x4e4cBA3779d56386ED43631b4dCD6d8EacEcBCF6) | Read: fresh Trove insertion hints |
| SortedTroves | [0x722E4D24FD6Ff8b0AC679450F3D91294607268fA](https://explorer.test.mezo.org/address/0x722E4D24FD6Ff8b0AC679450F3D91294607268fA) | Read: fresh insertion hints and redemption ordering |
| PriceFeed | [0x86bCF0841622a5dAC14A313a15f96A95421b9366](https://explorer.test.mezo.org/address/0x86bCF0841622a5dAC14A313a15f96A95421b9366) | Read: fixed-block BTC price |

Payment: browser → Permit2/EIP-2612 signature → facilitator → exact proxy → MUSD Transfer to the configured merchant → gateway checks canonical receipt and confirmations → report delivery. See the [browser](apps/mezo-web/src/x402.ts) and [gateway](apps/mezo-gateway/src/adapters/x402.ts) adapters. The public merchant is [0xd7F52d1Ddb5dC8678191f14E439Fc5DB67541535](https://explorer.test.mezo.org/address/0xd7F52d1Ddb5dC8678191f14E439Fc5DB67541535), supplied through `LIQVERA_PAY_TO`, with no built-in payment default.

| Historical successful 0.01 MUSD payment | UTC |
| --- | --- |
| [0x53808fff…117c](https://explorer.test.mezo.org/tx/0x53808fffb9f83d7946fcc0494d1c90491e8d83813d2795bb9ceb0957ed61117c) | 2026-10-13 13:13:09 |
| [0x4a04dc72…8455](https://explorer.test.mezo.org/tx/0x4a04dc72c9f4b9051262b5c14db18369b9140d3012f7b02c3c8d3c6952778455) | 2026-10-01 01:37:33 |
| [0xc5344f48…cb6f](https://explorer.test.mezo.org/tx/0xc5344f48b973d10f5925912e8c5f0b8c69ecdfe4e01ee15209f81771b0cccb6f) | 2026-10-01 00:12:04 |

**One-minute inspection:**

1. Open [liqvera.site](https://liqvera.site) and its wallet-free preview.
2. Open the DEX comparison, then the **Trove risk** tab → **Show sealed Trove example**. Follow the captured block and contract links in the explorer.
3. Open a payment above and inspect the MUSD Transfer: `10000000000000000` atomic units, or 0.01 MUSD.
4. Download the [preview evidence ZIP](https://liqvera.site/demo/snapshots/d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753/evidence.zip), [install the local packages](docs/mezo-integration.md#reproduce-from-source), then run `liqvera-evidence-verify evidence.zip` → `INTEGRITY_REPRODUCED`.
5. Inspect the [Trove risk report and free CLI](docs/mezo-trove-risk.md): borrower debt, collateral, ICR, MCR crossing and proven redemption position. Fresh web preparation and the x402 paywall are verified; historical transfers remain the payment proof. No registry contract is deployed.

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

Market reports describe a hypothetical sweep of available depth. Mezo pool fees are captured and applied; Hyperliquid fees, funding and gas are excluded. Optional Mezo spot swaps and Trove protection transactions are prepared in the browser and submitted only after the user signs in a wallet. Liqvera does not trade perpetuals or custody keys; risk output is not financial advice.

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

## Run the offline checks

Prepare dependencies as described in [validation](docs/validation.md), then:

```sh
make test
```

**1111 Python tests + 85 subtests, 104 gateway tests and 151 browser tests.**
The command checks these totals against its completed results, including a new
disposable PostgreSQL ledger. Native RPC tests remain opt-in; no wallet payment is
part of this gate.
<!-- liqvera-test-counts: {"python":1111,"python_subtests":85,"gateway":104,"web":151} -->

[Published Trove verification](docs/security/2026-10-23-mezo-trove-deployment.md) includes native preparation, the unpaid x402 boundary, independent review and exact image/CI bindings.

## Source, history and versions

Development is tracked publicly in Git. Use the links below to inspect changes, identify a version or review the evidence behind a build.

- **[Commit history](https://github.com/Dimkox/liqvera/commits/main/)** — dated changes and exact commit identifiers.
- **[Releases](https://github.com/Dimkox/liqvera/releases)** — published release notes and assets.
- **[Version tags](https://github.com/Dimkox/liqvera/tags)** — named source versions.
- **[Compare revisions](https://github.com/Dimkox/liqvera/compare)** — review differences between commits, branches or tags.
- **[Earlier DEX deployment](docs/security/2026-10-23-mezo-dex-deployment.md)** — source e80474e: 1021 Python tests + 85 subtests, 107 browser tests; gateway 74 local passes (13 database tests skipped in hosted CI).
- **[DEX deployment package refresh](docs/security/2026-10-23-runtime-package-refresh.md)** — pinned musl/nginx fixes and candidate validation.
- **[Current validation evidence](docs/security/2026-10-26-getzilla-audit.md)** — Getzilla 2.3.1 source audit of main: selected checks pass, production `packages/` linted separately, one Low Bandit configuration gap.
- **[Earlier validation evidence](docs/security/2026-10-21-getzilla-successor.md)** — passing Liqvera audit, failed tool self-check, exact deployment evidence and verification limits.

[Product specification](docs/specification.md) · [Architecture](docs/architecture.md) · [Security policy](SECURITY.md) · [Buildathon presentation](docs/competition/README.md)

Built by **[Dimkox](https://github.com/Dimkox)** for the [Mezo ecosystem](https://mezo.org/).
