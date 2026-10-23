# Liqvera product specification

## Purpose and supported scope

Liqvera produces verifiable public-market reports for Hyperliquid BTC linear perpetual snapshots. A report contains source identity and timestamps, available depth, requested BUY/SELL base quantity, exact filled quantity, notional, VWAP, worst price and price impact. It records quality checks, limitations, input hashes, algorithm identity and package versions. No fees, funding or net P&L are calculated.

## User flow

1. A visitor can inspect the immutable historical live preview without a wallet. It is labelled with its capture time.
2. The full browser flow discovers a wallet and scopes a fresh quote to its payer. Preparing evidence and a quote does not require the wallet to switch networks. Payment requires the configured Mezo chain (31611 Testnet or 31612 Mainnet), with account and network revalidated before signing. Account/network changes invalidate unsafe in-flight browser state.
3. The gateway creates a report request. Public source failure yields SOURCE_UNAVAILABLE, without fixture fallback.
4. Completed immutable artifacts determine the quote. Explicit merchant mode permits an exact 0.01 MUSD x402 purchase with sponsored gas only after the buyer authorizes it in their wallet. Default grant mode also requires bounded operator authority.
5. Confirmed entitlement allows repeated delivery of the same JSON and evidence ZIP without resettlement. Reload and recovery use existing request/quote identity.
6. The recipient can verify an exported canonical ZIP offline and optionally compare an independently trusted report digest.

## Public API

The machine-readable contract is [OpenAPI](../schemas/mezo-evidence/v1/openapi.json). Health is `/healthz`; readiness is `/readyz`; capabilities are `/v1/capabilities`. Quote creation is `POST /v1/report-quotes`; request and quote polling use their UUID paths. Report JSON is `GET /v1/reports/{report_id}` and its ZIP is `/evidence` beneath that path. Input sizes, decimal syntax, payer scope, origin, rate and authorization checks are enforced before application work.

Internal services use separate endpoints and network boundaries. [Capture service](../services/evidence-capture/README.md) and [report service](../services/evidence-report/README.md) document their configuration.

## Payment authority

Explicit network selection supports Mezo Testnet 31611 and Mainnet 31612 with their corresponding pinned MUSD assets. The default is Testnet; Mainnet requires a matching browser build, runtime configuration and separate ledger. See [Mainnet configuration](mainnet.md). The server verifies Permit2/EIP-2612 authorization, canonical identity and at least twelve confirmations. Merchant mode requires a fixed recipient, fresh per-purchase wallet signatures and durable cross-quote nonce uniqueness. It rejects fixture and mixed grant configuration. Default grant mode retains signed v2 source/plan/database/budget bindings and single-submit v1 grants. Merchant startup requires the reviewed migration and nonce index. Configuration alone cannot replace a wallet signature. Expired or reused authorization cannot submit again. Ambiguous settlement consumes the attempt and allows confirmation only.

## Artifacts and operations

New component packages are version 0.2.0 with Liqvera CLI/import names and schema namespace. Historical assets remain immutable and need their matching verifier version. SQL migration bytes remain pinned. Containers run with non-root identities, restricted capabilities, read-only roots, resource limits and private volumes. The fixture profile cannot contact the payment network.

Docker Compose runs the web, gateway, capture, report, PostgreSQL and edge services. The same application supports isolated fixture validation and public Testnet operation; see the [startup guide](runbooks/startup-shutdown.md).

## Acceptance status

The source release v0.0.5 contains the full application and historical paid-delivery evidence. The historical aggregate is 9 PASS and 21 NOT_RUN; no overall acceptance PASS is claimed. Current local evidence and known CVEs are recorded in [handoff](../handoff.md) and [security audit](security/2026-10-12-baseline.md). Release/deployment requires new exact-source, image, migration, recovery and payment-mode review.

## Mezo Testnet evidence products

The additive API 1.1 Testnet extension includes fixed-block MUSD/BTC DEX depth and
borrower Trove risk. All contract calls use an explicit block; report arithmetic and
queue links are reproduced from raw evidence offline. DEX reserves, fee, token
decimals and router results are captured rather than assumed. Trove debt includes
principal and interest without double-counting pending rewards. Inactive positions
and unknown queue ranks remain explicit. Read-only risk output is not financial advice.

The `trove_risk` product binds a nonzero EIP-55 borrower and the payer in a closed
request. Both services gate new creation; disabling it keeps existing delivery and
payment recovery. The 0.01 MUSD settlement guards remain shared. Historical examples
are pinned by full report and ZIP hashes. Source readiness, hosted CI, paid acceptance
and deployment are separate claims. No new Mainnet behavior is part of this extension.

The browser source adds self-custody Testnet actions alongside a delivered Trove
report: deposit BTC or repay MUSD through BorrowerOperations after current-state
reads, fresh HintHelpers/SortedTroves hints and `eth_call` simulation. A matching DEX
report can plan a BTC sale with automatic slices capped at an editable 1% estimated
impact each and editable 1% default `minOut` slippage. Each slice is re-quoted through
the Router, uses an exact approval when needed, and requires a separate wallet action.
No private keys enter Liqvera. These changes are source-only, have not been deployed
or live-wallet accepted, and do not change the report API, payment, or recovery guards.
