# Liqvera

**Market reports you can verify.**

Understand BTC market depth before you act. Liqvera turns public order-book snapshots into clear, downloadable reports with the evidence behind every calculation.

[Open the demo](https://liqvera.site) · [Watch the demo](docs/competition/pitch.mp4) · [Documentation](docs/README.md) · [Commit history](https://github.com/Dimkox/liqvera/commits/main/)

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
- **[Validation evidence](docs/security/2026-10-21-wave1-deployment.md)** — deployed version, security checks and the scope of functional verification.

[Product specification](docs/specification.md) · [Architecture](docs/architecture.md) · [Security policy](SECURITY.md) · [Buildathon presentation](docs/competition/README.md)

Built by **[Dimkox](https://github.com/Dimkox)** for the [Mezo ecosystem](https://mezo.org/).
