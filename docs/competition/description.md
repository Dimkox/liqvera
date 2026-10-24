# Liqvera — Market reports you can verify

October 23 deployed update: the Mezo DEX extension adds captured reserves and fees, Pool/Router quote agreement, exact comparison with Hyperliquid, and offline-reproducible ZIP evidence. The comparison is deployed with immutable JSON/ZIP URLs and verified in published Chrome checks. Historical payments are retained as payment evidence; the owner deferred a fresh signed purchase. [Deployment record](../security/2026-10-23-mezo-trove-deployment.md). [Implementation and verification instructions](../mezo-integration.md). The [rechecked official deadline](2026-10-23-event-facts.json) is October 26 at **15:00 UTC**; internal target 11:00 UTC, code freeze 08:00 UTC.


Liqvera compares public Hyperliquid BTC perpetual depth with fixed-block Mezo Testnet MUSD/BTC spot-pool quotes, using exact market-depth calculations. Inspect a hypothetical buy or sell, including filled quantity, VWAP and price impact, then download the JSON and portable evidence ZIP. The offline verifier checks integrity and reproduces the calculations.

The public demo at https://liqvera.site uses Mezo Testnet. Connect a browser wallet or use WalletConnect on your phone, request a fresh report and confirm access for 0.01 test MUSD through x402. Payment is bound to the report's exact hashes; confirmed delivery can be retrieved without paying again. A timestamped public preview is available without a wallet.

TypeScript powers the browser and gateway, Python handles capture and verification, and PostgreSQL preserves payment and delivery state. Market data access is public and read-only. The deployed browser offers optional Mezo spot swaps and Trove updates prepared for explicit user wallet signatures. Liqvera does not place perpetual orders or promise execution.

**Business model:** 0.01 MUSD per report; X MUSD per day for monitoring; B2B API for agents and protocols (pricing TBD). Target users are MUSD borrowers and trading bots.

The deployed preview passes public Chrome checks and network-disabled ZIP reproduction. Historical MUSD payments provide payment evidence at the owner’s request; no new signed purchase or live wallet transaction is claimed. See the [current deployment record](../security/2026-10-24-wallet-actions-deployment.md) for exact images, CI, scanner results and acceptance scope.

## October 23 Trove product update

The same [Testnet application](https://liqvera.site) now includes **Trove risk**:
borrower debt/collateral, exact ICR, theoretical MCR crossing, price scenarios and a
proven redemption position. The borrower defaults to the connected wallet address.
Open **Trove risk → Show sealed Trove example** for a wallet-free historical native
snapshot, or prepare a fresh borrower report through the existing 0.01 MUSD x402 flow.

A public native request reached READY at block 16324977; unchanged replay, input and
access boundaries, and the unpaid 402 response were verified. Its own operator-exported
ZIP reproduces offline. No fresh wallet signature or paid Trove settlement is claimed.
The owner selected the three already verified historical payment transactions.

[Deployment and scoped evidence](../security/2026-10-23-mezo-trove-deployment.md) records
main CI with 1101 Python tests + 85 subtests, 98 gateway tests without database skips
and 130 browser tests. [Published mobile/desktop views](2026-10-23-mezo-trove/published/result.json)
show the new panel without overflow. Mainnet, borrowing/redemption and a registry
contract are outside this update. The October 13 video remains a dated preparation
cut; the current screenshots and deck document the new features. This update does
not assert a new Akindo account submission.
