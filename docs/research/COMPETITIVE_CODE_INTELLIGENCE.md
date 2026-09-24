# Competitive Code Intelligence

Snapshot: **2026-08-10**

[Research index](README.md) · [PMF review](PMF_CRITICAL_REVIEW.md) · [Repository README](../../README.md)

## Purpose

This document records code-level competitive evidence rather than marketing claims. The focus is public repositories, SDKs, commit history, tests, issue trackers and observable architecture.

The core question is not “who has a landing page?”, but:

> Who has public evidence of real execution logic, reconciliation, venue adapters, automation and production bug history?

## Threat ranking

| Rank | Project | Code threat | Product threat | Why it matters |
|---:|---|---:|---:|---|
| 1 | VOOI | 9/10 | 9/10 | Unified perp API, Hyperliquid + Lighter, funding bot, Telegram signals, transfers |
| 2 | hypurrquant/perp-cli | 10/10 | 6/10 | Open multi-DEX execution, funding arb, rebalance, risk and large test surface |
| 3 | Hummingbot | 10/10 | 7/10 | Mature CEX/DEX connector and strategy infrastructure with real production failure history |
| 4 | goodcryptoX | 4/10 public evidence | 9/10 | Mature consumer multi-exchange app with bots and DEX/CEX coverage |
| 5 | Liquid | 2/10 public evidence | 9/10 | Funded mobile multi-perp aggregator |
| 6 | Wallet in Telegram + Lighter | 1/10 public evidence | 10/10 distribution | Native Telegram distribution makes “Lighter in Telegram” non-differentiated |
| 7 | PD AIO SDK | 8/10 if adapters hold up | 5/10 | Unified TypeScript abstraction across many perp DEXs |
| 8 | Variational official SDK | 6/10 | 8/10 future | Official gated API lowers future integration cost |
| 9 | CCXT/Freqtrade | 9/10 infrastructure | 5/10 direct | Commodity CEX integration and bot primitives |
| 10 | Dexari | 1/10 public code | 7/10 | Strong mobile Hyperliquid UX |

The ranking is strategic, not a claim of exact market share.

---

# 1. VOOI

## What the public code proves

The `vooi-app` GitHub organization exposes examples around a unified perpetual execution layer. Public material indicates support around venues such as Hyperliquid and Lighter and demonstrates more than a trivial REST wrapper.

The important evidence is architectural:

- funding-arbitrage example;
- Telegram signals example;
- REST reconciliation;
- streaming/SSE wake-up;
- heartbeat and reconnect handling;
- fill watchers;
- survivor monitoring;
- client order identifiers;
- margin routing;
- fixes for live market/alias edge cases.

A particularly useful pattern is:

```text
stream event wakes worker
→ authoritative REST/state confirmation
→ execution decision
```

This is a good design benchmark because a low-latency event stream is not automatically trusted as the sole source of truth.

## Why VOOI is dangerous

VOOI overlaps directly with the surviving thesis:

- unified execution;
- Hyperliquid + Lighter;
- automation;
- funding workflows;
- Telegram ingestion;
- builder-facing API.

The project therefore cannot claim “we unify Lighter and Hyperliquid” as a moat.

## Remaining differentiation opportunity

Potential gaps remain in:

- Korean-first distribution;
- CEX hedge venues integrated into the same risk engine;
- Variational RFQ;
- end-user net-P&L transparency;
- proprietary execution-quality dataset;
- explicit fail-closed reconciliation semantics.

---

# 2. hypurrquant/perp-cli

## Why it matters

`hypurrquant/perp-cli` is a stronger engineering benchmark than its CLI packaging suggests.

Publicly visible capabilities include multi-DEX trading workflows, portfolio/risk views, funding-arbitrage operations, transfers/rebalancing, alerts and MCP/tooling patterns.

The key evidence is the test and bug-fix surface rather than the README alone:

- adapter-specific parsing;
- numeric validation;
- dry-run gates;
- normalized response envelopes;
- restart-safe behavior;
- market/book validation;
- balance/position sanity checks;
- Lighter-specific handling;
- substantial test coverage.

## Korean signal

The repository contains Korean-language QA/reporting traces. This does not prove Korean user adoption, but it weakens any assumption that a Korean-localized execution tool is uncontested by technically capable teams.

## Strategic use

Treat perp-cli as a benchmark for:

- adapter registry design;
- normalized schema;
- error taxonomy;
- dry-run behavior;
- cross-venue command semantics;
- test matrix;
- rebalance workflows.

Do not copy architecture blindly; compare it against this repository's stronger fail-closed requirements.

---

# 3. Hummingbot

Hummingbot is important because it proves both maturity and failure complexity.

It has long-running exchange connectors, strategy/controller abstractions and production usage across CEX and DEX workflows.

The most valuable evidence is a class of real order-lifecycle bugs where exchange events arrive in an order the strategy did not expect.

Representative failure shape:

```text
close order submitted
→ failure/reject-like event observed
→ fill arrives later
→ strategy retries
→ duplicate close
→ accidental reversed exposure
```

This is exactly why this project must not implement:

```text
request failed => send again
```

Instead:

```text
request outcome uncertain
→ inspect private stream
→ inspect open orders
→ inspect fills
→ inspect position delta
→ resolve authoritative state
→ only then decide whether retry is valid
```

Hummingbot demonstrates that the difficult part is not connecting an exchange. It is remaining correct under asynchronous, contradictory and delayed state.

---

# 4. goodcryptoX

goodcryptoX is a major product competitor even though the core execution engine is not public.

Observed/product-documented surface includes combinations of:

- CEX account/API integration;
- DEX/perp support;
- Hyperliquid and other venues;
- grid/DCA/trailing/automation;
- portfolio tooling;
- mobile UX;
- token/revenue-share economics.

The private engine means GitHub evidence is weaker, but the product threat is high.

This repository already contains a separate dated research package on GOOD token mechanics; keep product economics and execution capability distinct.

Strategic lesson: a generic “CEX + DEX + bots in one app” pitch is not unique.

---

# 5. Liquid

Liquid is strategically close to the original multi-perp mobile concept.

Public product information indicates aggregation across multiple perp DEXs with mobile-first positioning, shared position/risk views and investor backing.

Public execution code is not available, so implementation quality cannot be confirmed through GitHub.

Strategic lesson: “mobile multi-DEX terminal” is already an occupied product category.

---

# 6. Wallet in Telegram + Lighter

This is the direct reason the original “Lighter in Telegram” wedge is invalid.

By 2026, Lighter-powered perpetual futures are available through Wallet in Telegram. Regardless of the internal implementation being closed, the distribution fact is enough:

- Telegram-native access is not unique;
- no-install trading is not unique;
- Lighter itself cannot be the consumer differentiator.

Strategic lesson: Telegram should be treated as a control surface/distribution channel, not the core moat.

---

# 7. Variational official SDK

Variational has an official Python SDK under the `variational-research` organization.

The important shift is conceptual:

> Variational is no longer merely “maybe an API later”; it has a real official SDK and gated access.

That turns the problem from pure reverse engineering into a partnership/access problem.

Implications:

- request official credentials/sandbox;
- clarify RFQ lifecycle and expiry;
- clarify automation policy;
- clarify rate limits;
- clarify attribution/partner economics;
- never make unsupported private endpoints a production dependency.

Potential moat is temporary: once access broadens, major aggregators can integrate it too.

---

# 8. PD AIO SDK and adapter commoditization

Unified perp SDK projects such as PD AIO SDK matter even if they are not consumer competitors.

They compress the engineering value of “we integrated N DEXs”.

Before reuse, audit:

- signing correctness;
- venue-version compatibility;
- test coverage;
- secret handling;
- maintenance cadence;
- error semantics;
- license;
- exact market support rather than README claims.

Strategic lesson: adapter count is a weak moat and may become even weaker.

---

# 9. CCXT, Freqtrade and the long tail

CCXT, Freqtrade, Hummingbot, exchange SDKs and hundreds of smaller funding/arbitrage repositories collectively commoditize:

- market data collection;
- basic REST trading;
- standard CEX support;
- Telegram alerts;
- simple strategy scheduling;
- grid/DCA/TWAP primitives;
- generic funding scanning.

Smaller repositories are useful as idea/test sources but should not be assumed production-grade.

---

# 10. What public code says is actually hard

Across projects, the recurring hard areas are:

## Unknown order state

HTTP/WebSocket errors do not reliably prove an order was not accepted.

## Event ordering

Fill, reject, cancel and position updates can arrive late or out of order.

## Partial fills

A two-leg trade can become directional before the second leg catches up.

## Residual hedge

The engine needs canonical base exposure, not raw venue quantities.

## Contract normalization

Symbols such as `kSHIB`, `1000SHIB`, HIP-3 aliases and RWA markets make string matching unsafe.

## Restart recovery

A process restart must not erase execution intent or create duplicate orders.

## Fees and attribution

Builder/partner fees can destroy an apparent edge and must be included before execution.

## Capital fragmentation

Profits shift margin between venues even when portfolio P&L is neutral, creating rebalance pressure.

---

# 11. Competitive implications for this repository

The repository should not optimize for feature checklist parity. It should optimize for **proof of correctness**.

Minimum differentiating invariants:

1. Exact order ownership.
2. No broad cancel as a default safety primitive.
3. Durable execution-group state.
4. Idempotent command boundaries.
5. Authoritative reconciliation before retry.
6. Canonical base-unit exposure.
7. Residual hedge policy.
8. Explicit venue-health states.
9. Fail-closed stale-data behavior.
10. Full net-P&L attribution.
11. Replayable event history.
12. Shadow/live code-path parity where possible.

---

# 12. What to benchmark, not blindly adopt

## From VOOI

- stream-wake + authoritative-confirm pattern;
- unified API ergonomics;
- funding workflows;
- margin-transfer model.

## From perp-cli

- adapter normalization;
- validation/test breadth;
- dry-run gates;
- multi-venue command model.

## From Hummingbot

- connector ecosystem;
- event abstractions;
- most importantly, public failure cases to turn into regression tests.

## From goodcryptoX/Liquid/Wallet

- onboarding and packaging;
- consumer expectations;
- monetization constraints;
- evidence that UI/distribution features alone are easy for larger products to absorb.

---

# 13. Final competitive conclusion

The market is **not empty** and the old tools are not irrelevant dinosaurs. Their continued existence proves that infrastructure demand is durable and simultaneously proves that connectivity alone is not enough.

The defensible project thesis is therefore:

> A safety-first execution/reconciliation core that can demonstrate better operational correctness and better net-edge truth than generic adapters, then package that core for the segment that proves willingness to pay.

If that correctness and economic evidence cannot be demonstrated, the repository should remain an internal research tool rather than be forced into a weak consumer product.
