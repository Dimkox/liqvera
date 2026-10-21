# Wave 1: MUSD funding for report checkout

Implementation date: 2026-10-21. Comparison baseline: `f1d3bffc46fa1459908fdff865fcfbfc831b7f7f` (main, 2026-10-14). Track 2: Access and Distribution for MUSD/MEZO.

Deployment update, 2026-10-21: source `9ca9ceda79fbce07b9b9bfb1dcc174d4c300b863` is now published at https://liqvera.site. On claw, the complete Python run passed 951 tests and 85 subtests, and all 71 gateway tests passed, including the 13 disposable-PostgreSQL cases. Web tests and both network builds passed. The [separate rollout record](../security/2026-10-21-wave1-deployment.md) includes rollback, backup restoration, exact-image scans and the published browser check. No new loan, quote or payment was submitted. The implementation-session evidence below remains historical and unchanged.

## User-visible change

A prepared, unpaid report now has a **MUSD funding for this report** panel in the same checkout. The selected payer can check their MUSD balance, see the exact shortfall and estimated number of purchases at the quoted price, and download a block-bound funding observation. When the balance is insufficient, a separate acknowledgment enables the official borrowing application for the selected Mezo network. The user returns to the same saved quote and explicitly checks again. An adequate balance removes the borrowing action. Returning or reading never starts payment.

This extends MUSD access in the existing product. It is an assisted external Mezo Borrow flow, not an embedded loan contract or evidence that a loan was opened. Mezo's documented minimum borrowed debt is 1,800 MUSD plus a 200 MUSD gas deposit, before other applicable fees. This is not a 0.01-MUSD loan or a recommendation to borrow for one report. Interest, collateral and liquidation terms remain in the official application.

## What existed before the wave

- Baseline main already included BTC reports, the verifier, x402 purchases and AppKit/WalletConnect.
- `feat/mezo-borrow-treasury-20261013` points to `7130bb55`, an ancestor of main, with no additional committed Borrow feature.
- A recovered local `liqvera-mezo-finance.zip` from October 13 already contained an uncommitted Assisted Borrow module, panel and tests. Its balance/shortfall, expiry/payer guards and acknowledgment design are reused, not claimed as work first created during Wave 1.
- The recovered treasury planner/Earn guidance is excluded from this change.

## Work completed during Wave 1

- Integrated the prepared Borrow slice into the actual `main.ts` checkout and its selected provider, wallet state, quote and payment guard.
- Added `readFundingObservation`: chain/account validation, explicit block-number `balanceOf`, canonical block-hash recheck and final identity check, with a shared ten-second operation deadline.
- Added exact integer report-budget calculation and downloadable JSON bound to the quote ID, network, asset, payer, block number/hash, observed time, balance, required amount and shortfall.
- Invalidated results after account/network/provider/quote/payment-state changes and after 30 seconds. Revoked obsolete object URLs. Malformed or failed reads never become a zero balance.
- Updated Borrow destinations to the paths verified in current official documentation. Testnet never routes to Mainnet.
- Added tests for block changes, identity races, malformed metadata, one-wei shortfall, invalid input, shared deadline, Mainnet isolation, download invalidation and DOM integration.

These are concrete source changes after the published baseline. Whether the extension meets the competition's significance criterion remains the judges' decision. Reuse is disclosed rather than represented as entirely new development.

## Reproduce

Use Node 22.14+ (the recorded local run used Node 24.19.0) and Python 3.12:

```bash
make liqvera-web
npm test --prefix apps/mezo-web
LIQVERA_NETWORK=mainnet npm run build --prefix apps/mezo-web
make liqvera-gateway
npm test --prefix apps/mezo-gateway
npm audit --prefix apps/mezo-web
npm audit --prefix apps/mezo-gateway
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.lock
.venv/bin/pip install --no-deps --no-build-isolation -e .
make verify PYTHON=.venv/bin/python
.venv/bin/python scripts/check-docs.py
```

Raw local results and source hashes are under [the October 21 evidence directory](2026-10-21-funding/verification.json). Tests use synthetic balances and API responses. The exported observations in test evidence are synthetic and must not be used as chain/payment evidence.

### Original implementation-session results

- Web: 102 passed; Testnet and Mainnet production builds passed.
- Gateway: 58 passed, 13 PostgreSQL cases skipped because no disposable database was available.
- Python: 947 passed, 85 subtests passed; four Compose configuration tests failed because Docker is unavailable. The full `make verify` result is therefore not PASS. The exact test names are retained in verification.json and the raw log.
- Artifact scanner passed; npm audits reported zero advisories for both package closures.
- Actual entrypoint passed the synthetic JSDOM check. To repeat that optional check, install `jsdom@26.1.0` and `esbuild@0.28.2` in a temporary directory, copy `dom-smoke.mjs` alongside its node_modules, and run it from the repository root. The script does not contact a live gateway or blockchain.

## Safety and verification boundaries

No gateway, SQL migration, authorization, nonce, settlement/finality or entitlement logic changes. The panel calls only `eth_accounts`, `eth_chainId`, `eth_getBlockByNumber` and `eth_call`; it never requests signatures, approvals, transfers or a loan. Existing confirm-only payment recovery remains authoritative. A wallet-reported funding observation is not an independently authenticated chain proof, a reservation of funds, a payment receipt or a guarantee of future purchases.

The independent read-only code/security reviewer approved the final code after the shared deadline fix, with 53 targeted tests and TypeScript passing. Live wallet/RPC interoperability, physical mobile handoff, external loan behavior, deployment and paid delivery were explicitly outside that review. Package audits do not constitute a complete deployment-image audit.

## Original implementation-session publication and live acceptance

The existing AKINDO product is [Liqvera](https://app.akindo.io/communities/GLX6zWqv4hW7EP41/products/Drk1AoWNguaZnWMB), submitted to Wave 1. Its existing submission comment was observed dated October 15; no duplicate entry is required or created.

This session has not deployed the new code, opened a loan, signed a report purchase or verified a new paid delivery. The previous operator deployment is not mounted here, and its hostname does not resolve in this environment. Direct public-site checks returned HTTP 403 from this environment, which does not establish the site's service health. The browser cannot reach the local development port, so the full-entrypoint check used JSDOM rather than claiming a real-browser test.

The public AKINDO page lists proof transaction `0x53808fffb9f83d7946fcc0494d1c90491e8d83813d2795bb9ceb0957ed61117c`. Its current chain receipt/date was not independently retrieved here; it is not counted as a new payment by this implementation session. Historical acceptance and previous deployment audits retain their original scope.

The AKINDO browser is signed out, so product/submission edits remain unapplied. [Prepared updates](wave1-akindo-update.md) describe source availability separately from deployment. Deadline: October 26, 2026, 15:00 UTC / 18:00 Moscow.

## Sources checked

- [AKINDO buildathon and Track 2](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).
- [Official borrowing guide, minimum debt and network-specific routes](https://mezo.org/docs/users/borrow/mint-musd/).
- [Official x402 network/token metadata](https://mezo.org/docs/developers/getting-started/musd-payments-x402/).
- [Terms supplied by the owner](https://docs.google.com/document/d/1oY1hzzub2l_jHdovmsAaE3YBuRJh0_UQXxL1Zd2g3pE/edit). Direct document retrieval was unavailable; the official event page independently states that existing products need an in-event extension. No new terms were accepted.
