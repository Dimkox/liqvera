# Testnet demonstration script (operator draft)

This script is for a future authorized `live-public + mezo-testnet` run. Do not narrate an unperformed step as completed. Before recording, confirm A01–A30 evidence against the final clean commit, payment readiness, a dedicated funded test buyer, distinct merchant receiver, reviewed finality rule and safe environment configuration. Stop if any gate fails.

1. Show the repository commit, provenance, architecture and the current acceptance result. State that the report is read-only analytics on a Hyperliquid BTC **linear perpetual** snapshot, not a spot purchase or executable trade.
2. Select BUY or SELL and enter an exact BTC quantity. Show live public-source mode, snapshot timestamp, available-depth limitation, validation status and test MUSD access price. Do not call a fixture report live.
3. Show the unpaid 402 response and its payment terms without revealing a capability or wallet signature. Connect the dedicated buyer wallet on Mezo Testnet, verify chain `31611`, MUSD token, amount `0.01` test MUSD (`10000000000000000` atomic units), and the approved merchant address. Explicitly confirm the limited testnet payment.
4. After canonical confirmation, show the same immutable report, receipt, transaction hash, block and log index. Download the evidence bundle and run the offline verifier without network access. Explain that hash and recalculation checks establish reproducibility relative to the retained inputs, not an exchange signature or a trading guarantee.
5. Reload and retrieve the same report and bundle. Show one settlement and no second payment. Demonstrate wallet cancel, wrong chain, wallet switch and recovery only if their corresponding A30 assertions have passed.
6. End with the complete result's omissions and blockers. If live source, facilitator, RPC, funding or finality evidence is unavailable, stop and record `BLOCKED_EXTERNAL` for the affected cases. A failed local assertion is `FAIL`.

The local `make mvp-web` fixture prototype may be shown separately as **SIMULATED — NO TRANSFER**. It does not satisfy the live payment demonstration or replace A13–A14.
