# Liqvera — Market reports you can verify

October 23 deployed update: the Mezo DEX extension adds captured reserves and fees, Pool/Router quote agreement, exact comparison with Hyperliquid, and offline-reproducible ZIP evidence. The comparison is deployed with immutable JSON/ZIP URLs and verified in published Chrome checks. Historical payments are retained as payment evidence; the owner deferred a fresh signed purchase. [Deployment record](../security/2026-10-23-mezo-dex-deployment.md). [Implementation and verification instructions](../mezo-integration.md). The [rechecked official deadline](2026-10-23-event-facts.json) is October 26 at **15:00 UTC**; internal target 11:00 UTC, code freeze 08:00 UTC.


Liqvera compares public Hyperliquid BTC perpetual depth with fixed-block Mezo Testnet MUSD/BTC spot-pool quotes, using exact market-depth calculations. Inspect a hypothetical buy or sell, including filled quantity, VWAP and price impact, then download the JSON and portable evidence ZIP. The offline verifier checks integrity and reproduces the calculations.

The public demo at https://liqvera.site uses Mezo Testnet. Connect a browser wallet or use WalletConnect on your phone, request a fresh report and confirm access for 0.01 test MUSD through x402. Payment is bound to the report's exact hashes; confirmed delivery can be retrieved without paying again. A timestamped public preview is available without a wallet.

TypeScript powers the browser and gateway, Python handles capture and verification, and PostgreSQL preserves payment and delivery state. Market data access is public and read-only. Liqvera does not place trades or promise execution.

The current deployed preview passes public Chrome checks and network-disabled ZIP reproduction. Historical MUSD payments provide payment evidence at the owner’s request; no new signed purchase is claimed. See the [current deployment record](../security/2026-10-23-mezo-dex-deployment.md) for exact images, inherited verification and acceptance scope.
