# Liqvera product specification

## Purpose and supported scope

Liqvera produces verifiable public-market reports for Hyperliquid BTC linear perpetual snapshots. A report contains source identity and timestamps, available depth, requested BUY/SELL base quantity, exact filled quantity, notional, VWAP, worst price and price impact. It records quality checks, limitations, input hashes, algorithm identity and package versions. No fees, funding or net P&L are calculated.

## User flow

1. A visitor can inspect the immutable historical live preview without a wallet. It is labelled with its capture time.
2. The full browser flow discovers a wallet, validates chain 31611 and scopes a fresh quote to its payer. Account/network changes invalidate unsafe in-flight browser state.
3. The gateway creates a report request. Public source failure yields SOURCE_UNAVAILABLE, without fixture fallback.
4. Completed immutable artifacts determine the quote. A valid testnet authority permits an exact 0.01 test-MUSD x402 payment with sponsored gas; ordinary startup has no such authority.
5. Confirmed entitlement allows repeated delivery of the same JSON and evidence ZIP without resettlement. Reload and recovery use existing request/quote identity.
6. The recipient can verify an exported canonical ZIP offline and optionally compare an independently trusted report digest.

## Public API

The machine-readable contract is [OpenAPI](../schemas/mezo-evidence/v1/openapi.json). Health is `/healthz`; readiness is `/readyz`; capabilities are `/v1/capabilities`. Quote creation is `POST /v1/report-quotes`; request and quote polling use their UUID paths. Report JSON is `GET /v1/reports/{report_id}` and its ZIP is `/evidence` beneath that path. Input sizes, decimal syntax, payer scope, origin, rate and authorization checks are enforced before application work.

Internal services use separate endpoints and network boundaries. [Capture service](../services/evidence-capture/README.md) and [report service](../services/evidence-report/README.md) document their configuration.

## Payment authority

Only Mezo Testnet 31611 and the pinned MUSD metadata are supported. The server verifies Permit2/EIP-2612 authorization, canonical identity and at least twelve confirmations. Signed v2 grants bind reviewed source, plan, database and a bounded budget; v1 remains single-submit. Activation is not implied by deployment, a test, an environment flag alone or this document. Expired/exhausted/unknown authority cannot submit again. Ambiguous settlement consumes the attempt and allows confirmation only.

## Artifacts and operations

New component packages are version 0.2.0 with Liqvera CLI/import names and schema namespace. Historical assets remain immutable and need their matching verifier version. SQL migration bytes remain pinned. Containers run with non-root identities, restricted capabilities, read-only roots, resource limits and private volumes. The fixture profile cannot contact the payment network.

The Linux operator v0.0.2 supports verified installation, start/stop/status/logs and explicit uninstall. Update and rollback remain fail-closed because coherent backup/restore integration is incomplete. Installer contract tests are not proof of clean-host installation.

## Acceptance status

The source release v0.0.5 contains the full application and historical paid-delivery evidence. The historical aggregate is 9 PASS and 21 NOT_RUN; no overall acceptance PASS is claimed. Current local evidence and known CVEs are recorded in [handoff](../handoff.md) and [security audit](security/2026-10-12-baseline.md). Release/deployment requires new exact-source, image, migration, recovery and live-authority review.
