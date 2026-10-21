# Prepared update to the existing Liqvera entry

These drafts have not been applied to AKINDO. Keep the existing product and submission. Publish the source link and actual deployment status together; do not describe the new UI as live until it is deployed and checked.

## Submission comment addition

Wave 1 source update — October 21, 2026. Liqvera now integrates MUSD funding assistance into the existing report checkout: the same payer can check their MUSD balance at an explicit block, see the exact shortfall and estimated report-purchase budget, export the observation, and open official Mezo Borrow with a separate risk acknowledgment. Returning keeps the original quote and requires an explicit balance refresh and separate payment confirmation. The exported check is a wallet-reported observation, not a loan or payment receipt.

The published baseline is f1d3bffc46fa1459908fdff865fcfbfc831b7f7f (October 14). We reused an uncommitted October 13 Assisted Borrow preparation and disclose that provenance. Wave 1 work adds canonical checkout integration, block/hash checks, exact purchase-budget export, stale-context guards and validation. Treasury/Earn is excluded. This extends Track 2 access to MUSD through the existing Mezo ecosystem rather than adding a separate product.

Source branch: feat/wave1-musd-access-20261021 in https://github.com/Dimkox/liqvera. Detailed delta and reproducible evidence: docs/competition/wave1-musd-funding.md and docs/competition/2026-10-21-funding/verification.json in that branch.

Validation: 102 browser-module tests pass; both network builds pass; independent code/security review has no remaining findings. Gateway: 58 pass, 13 PostgreSQL cases skipped. Python: 947 pass and 85 subtests pass; four Compose configuration tests are blocked by the absence of Docker in this environment. Both npm dependency audits report zero advisories. The full application entrypoint passes a synthetic JSDOM integration check. This is not real-wallet acceptance or a complete deployment-image audit.

Deployment of this extension is pending operator access. No loan, report payment or new paid delivery was signed or verified in this session. Historical proof transactions remain historical; they do not demonstrate this extension's live acceptance.

## Product page addition

### Wave 1 extension: MUSD funding in the same checkout

The October 21 source update adds a MUSD funding panel next to the prepared report. Check the selected payer's balance and exact shortfall, estimate how many reports the balance covers at the quoted price, and download a funding observation with network, token and block references. If funds are insufficient, an acknowledged link opens the official Mezo Borrow application on the same network. Return to the same saved quote and refresh the balance before confirming payment separately.

Borrowing has its own minimum debt, interest, fees and BTC liquidation risks. This is funding assistance, not an embedded loan, an automatic purchase or a recommendation to borrow for one report. Testnet and Mainnet stay separate. Source implementation and tests are available in feat/wave1-musd-access-20261021; deployment and new wallet-authorized paid acceptance are pending. The original October 13 preparation is disclosed in the technical evidence.
