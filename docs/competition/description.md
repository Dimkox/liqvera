# Liqvera — Market reports you can verify

Liqvera turns public Hyperliquid BTC perpetual order-book snapshots into exact market-depth reports. Inspect a hypothetical buy or sell, including filled quantity, VWAP and price impact, then download the JSON and portable evidence ZIP. The offline verifier checks integrity and reproduces the calculations.

The public demo at https://liqvera.site uses Mezo Testnet. Connect a browser wallet or use WalletConnect on your phone, request a fresh report and confirm access for 0.01 test MUSD through x402. Payment is bound to the report's exact hashes; confirmed delivery can be retrieved without paying again. A timestamped public preview is available without a wallet.

TypeScript powers the browser and gateway, Python handles capture and verification, and PostgreSQL preserves payment and delivery state. Market data access is public and read-only. Liqvera does not place trades or promise execution.

The deployed demo passes public health, fresh-report, payment-challenge and unsigned browser checks. A new paid purchase on this deployment remains to be recorded with a real wallet. See the [deployed WalletConnect verification record](../security/2026-10-13-walletconnect.md) for exact images, security evidence and acceptance scope.
