# Liqvera Mezo Evidence

Change ID: `2026-09-24-mezo-evidence`
Created: 2026-09-24T15:46:33Z
Risk: high
Complexity: architectural
Domains: contracts, public market data, exact analytics, HTTP API, payment,
authorization, persistence, frontend, operations

## Route status

No `.grok-stack/runtime/active-route.json` exists in this public clone. This
package was created from the canonical Liqvera specification and explicit user
approval. It contains no fabricated route ID, agent receipt, or review receipt.

## Problem

The public repository contains a read-only Stage A Python baseline but not the
approved Liqvera end-to-end flow. The baseline is not fully reproducible in a
fresh public clone, and payment, API, persistence, evidence-report, and UI
components have not been implemented.

## Outcome

A developer or analyst can buy access to one immutable, independently
recalculable Hyperliquid BTC perpetual snapshot report using 0.01 test MUSD on
Mezo Testnet, without granting exchange authority or exposing paid content
before confirmed settlement.

## Scope

### In scope

- F1–F7 from `docs/planning/LIQVERA_FACTORY_TZ.md`.
- One Hyperliquid BTC linear perpetual snapshot.
- BUY/SELL hypothetical sweep for a BTC quantity.
- Fixture and live-public source modes with truthful labeling.
- Offline-verifiable report bundle.
- Mezo Testnet x402 payment and durable entitlement.
- One-page English testnet UI and isolated Compose stack.

### Out of scope

- Mainnet, live orders, exchange keys, custody, leverage, loans, bridges, or withdrawals.
- Lighter live data, cross-venue arbitrage, funding, fees, or net-P&L claims.
- Hosted production deployment, paid infrastructure, email registration, CRM,
  Telegram, Kakao, subscriptions, or automatic refunds.

## Constraints

- Preserve Python exact arithmetic and Stage A semantics.
- TypeScript serves only the API/browser/x402 boundary.
- Fail closed on identity, source, artifact, authorization, and payment uncertainty.
- No external write or value transfer without a separate operator-confirmed testnet step.
