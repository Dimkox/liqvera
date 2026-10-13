# Liqvera

### Market reports you can verify.

**Understand BTC market depth. Explore the numbers. Verify the result.**

[Open Liqvera](https://liqvera.site) · [Documentation](docs/README.md) · [Demo video](docs/competition/pitch.mp4)

Built for [Mezo](https://mezo.org/) and [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

## From market data to a clear report

Liqvera turns public Hyperliquid BTC order-book data into market-depth reports. Choose a buy or sell side and an order size to see how that order would fill against the available liquidity: average price, filled quantity and price impact.

Every report comes with the source snapshot and calculations behind it. Read the result in your browser, download the JSON or keep the evidence ZIP to reproduce the calculations independently.

## What you can do

- **Explore market depth** — see how order size affects execution price and available liquidity.
- **Inspect the evidence** — follow the report back to its market snapshot and inputs.
- **Keep your reports** — download structured JSON and a portable evidence ZIP.
- **Verify independently** — reproduce the calculations offline with the Liqvera verifier.
- **Pay per report** — connect a Mezo wallet and use MUSD through x402.

## Try Liqvera

Open **[liqvera.site](https://liqvera.site)** and select **Show latest live report** to explore a sample without connecting a wallet.

To request your own report, connect an EVM wallet, choose the order parameters and confirm the report purchase. Use a browser wallet extension on a computer, or open **liqvera.site** in your wallet's built-in browser on your phone. If several wallets are detected, select yours from **Wallet provider**. Your wallet must support **Mezo Testnet** for payment; reports cost **0.01 test MUSD**.

## The code

Liqvera combines a TypeScript web application and API with Python services for market capture, report generation and independent verification.

| Component | Role |
| --- | --- |
| Web application | Wallet connection, report requests and interactive results |
| API gateway | Quotes, payments and report delivery |
| Market capture | Public Hyperliquid order-book snapshots |
| Report engine | Exact calculations and downloadable evidence |
| Offline verifier | Evidence integrity checks and reproducible calculations |
| PostgreSQL | Payment and report-access state |

See the [architecture](docs/architecture.md) for how the components connect, the [startup guide](docs/runbooks/startup-shutdown.md) to run the code, and the [validation guide](docs/validation.md) for tests.

## Explore further

[Product specification](docs/specification.md) · [Testnet guide](docs/runbooks/testnet-demo.md) · [Security](SECURITY.md) · [Buildathon presentation](docs/competition/README.md)

Created by **[Dimkox](https://github.com/Dimkox)**.
