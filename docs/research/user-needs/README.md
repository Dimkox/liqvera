# User-needs research index and market-demand synthesis

Snapshot: **2026-08-18**  
Status: **cross-forum synthesis and falsification input; not runtime truth and not automatic roadmap authority**

[Research index](../README.md) · [Master research](../MASTER_RESEARCH.md) · [Critical PMF review](../PMF_CRITICAL_REVIEW.md) · [Source ledger](../SOURCE_LEDGER.md) · [Roadmap](../../ROADMAP.md) · [Repository README](../../../README.md)

This file is the canonical repository entry point for user needs, Jobs to Be Done, market demand, product packaging hypotheses, and validation criteria for Multi-Exchange Engine. It deliberately separates market evidence from implemented capabilities.

## Research-to-runtime rule

A complaint, social post, GitHub issue, forum thread, paid bounty, competitor feature, or technically attractive idea does **not** prove that Multi-Exchange Engine implements a capability or should build it.

When sources conflict, use this order:

1. runtime code and tests for what exists;
2. accepted ADRs and `SECURITY.md` for allowed boundaries;
3. `docs/ROADMAP.md` for approved implementation order;
4. this synthesis for product discovery and falsification;
5. raw social inputs for follow-up only.

The current product remains Stage A public capture and read-only analysis. Nothing in this document authorizes live trading, user-capital deployment, custody, withdrawals, or automatic paired execution.

---

# Executive decision

The market does not need another generic multi-exchange terminal, funding scanner, Telegram Mini App, or “AI arbitrage bot.” Exchange connectivity, dashboards, alerts, strategy templates, and basic opportunity discovery are already crowded or commoditized.

The recurring operational gap is narrower and more valuable:

> Traders and trading-system builders need authoritative evidence about market data, orders, fills, positions, and residual exposure when several venues, APIs, and asynchronous event streams disagree.

The best current product interpretation is therefore:

> **Multi-Exchange Engine is a self-hosted cross-venue execution-evidence and integrity layer.**

The practical product sequence is:

1. **MEE Evidence** — prove data quality, instrument equivalence, executable economics, and why a candidate signal was accepted or rejected;
2. **MEE Observer** — read-only detection of local-versus-exchange divergence, stale streams, missing fills, duplicate events, and restart/reconnect failures;
3. **MEE Integrity** — only after paid validation, deterministic order-state convergence, cumulative-fill accounting, residual-exposure control, and paired execution.

This sequence aligns the current Stage A boundary with the strongest observed pains without pretending that P1/P2 execution capabilities already exist.

---

# Evidence method and confidence

## Evidence classes

1. **Input hypothesis** — owner-supplied or social-source notes preserved without treating them as settled truth.
2. **Primary technical evidence** — official documentation, source code, reproducible issue reports, logs, and API-change notices.
3. **Cross-forum synthesis** — recurring patterns across issue trackers, practitioner discussions, forums, and interviews.
4. **Buyer evidence** — payment, deposit, procurement, capital allocation, paid pilot, or an existing budget line.
5. **Roadmap candidate** — pain that passes the promotion rule at the end of this document.

## Important limitation

Reddit and general forums are useful for discovering language, distrust, workarounds, and recurring questions. They are weak evidence for willingness to pay and often lack complete logs. The strongest evidence in this synthesis comes from production-style GitHub issues with timestamps and event sequences, official API changes, and paid connector bounties.

No requirement is promoted solely because it appeared on Reddit, X, Discord, Telegram, or a marketing page. Direct customer interviews and paid pilots remain necessary.

---

# Ranked market pains

The ranking combines severity, recurrence, willingness-to-pay proxy, and fit with MEE. It is an analytical priority score, not a population-wide survey result.

| Rank | Pain / Job to Be Done | Classification | Severity | Evidence strength | MEE fit |
|---:|---|---|---:|---:|---:|
| 1 | Recover authoritative order and position state after timeout, reconnect, restart, or event loss | `PARTIALLY_CONFIRMED` buyer pain | Critical | Very high | Very high |
| 2 | Handle partial, late, duplicate, and cancel-race fills without accidental directional exposure | `PARTIALLY_CONFIRMED` buyer pain | Critical | Very high | Very high |
| 3 | Detect live-but-stalled or stale public/private streams, not merely connected sockets | `CONFIRMED_DEVELOPER_PAIN` | Critical | Very high | Very high |
| 4 | Replace displayed spread with full-cycle executable economics | `PARTIALLY_CONFIRMED` | High | High | Very high |
| 5 | Reduce connector maintenance, API drift, and venue-semantic incompatibility | `CONFIRMED_BUYER_PAIN` for connector work | High | Very high | High |
| 6 | Reconstruct incidents from durable evidence instead of manually correlating logs | `PARTIALLY_CONFIRMED` | High | High | Very high |
| 7 | Prove economic instrument equivalence across venues before calling positions a hedge | `PARTIALLY_CONFIRMED` | High | Medium-high | Very high |
| 8 | Fail closed with kill switches, health gates, and explicit manual-intervention states | `PARTIALLY_CONFIRMED` | High | High | High |
| 9 | Replay realistic full-depth, latency, gap, and fill scenarios using the same contracts as production | `CONFIRMED_DEVELOPER_PAIN` | Medium-high | Medium-high | High |
| 10 | Reduce collateral fragmentation and rebalancing friction | `ANECDOTAL / PARTIALLY_CONFIRMED` | High | Medium | Low for first product |

The first five pains should drive discovery. The tenth is real but expands custody, private API, withdrawal, bridge, security, and regulatory scope too early.

---

# Detailed Jobs to Be Done

## 1. Authoritative reconciliation after ambiguous outcomes

### User segment

Small quant teams, proprietary desks, bot vendors, and self-hosted power users operating one or more private venue connections.

### Triggering context

- submission timeout after the request may already have reached the venue;
- WebSocket reconnect or delayed private stream;
- restart with open orders or partially filled positions;
- HTTP 429/5xx and uncertain retry behavior;
- local event loss or reordering;
- REST and WebSocket state disagreement.

### Failure pattern

A system converts “no response” into `FAILED`, retries, and later receives a fill for the original order. This can create duplicate orders or reverse a position.

Primary examples:

- Hyperliquid order reported failed, then filled milliseconds later, followed by a retry and duplicate order: <https://github.com/hummingbot/hummingbot/issues/7294>
- Funding-rate arbitrage close reported failed, then executed twice: <https://github.com/hummingbot/hummingbot/issues/7295>
- Strategy remains alive but does not resume after Hyperliquid WebSocket reconnect: <https://github.com/hummingbot/hummingbot/issues/8250>
- Controllers lose orders and stop after reconnect: <https://github.com/hummingbot/hummingbot/issues/7230>
- Ghost orders and exchange/local position divergence: <https://github.com/hummingbot/hummingbot/issues/7032>

### Current workaround

Teams write venue-specific retry logic, inspect exchange history manually, restart processes, reconcile balances, and disable automation during incidents.

### Required capability

- persistent client-order identity;
- explicit `UNKNOWN` / `RECONCILING` state;
- authoritative REST/source-of-truth query before retry;
- deterministic restart recovery;
- idempotent event application;
- append-only evidence and operator-visible manual intervention.

### Cheapest validation

Offer a read-only incident reconstruction pilot. Ask teams for one real timeout/restart incident and measure whether MEE reconstructs the timeline faster and more accurately than their current process.

---

## 2. Partial fills, cancel/fill races, and residual exposure

### Triggering context

- maker order fills while cancellation is in flight;
- market order completes below requested quantity;
- hedge remainder is below venue minimum;
- late fill arrives after the strategy believes the leg is complete;
- duplicate completion events or repeated closing orders.

Primary examples:

- maker fill during cancellation, no taker hedge created: <https://github.com/hummingbot/hummingbot/issues/7139>
- MEXC market close stuck at 11.3/11.83 while the strategy waits indefinitely: <https://github.com/hummingbot/hummingbot/issues/7129>
- partial fill below taker minimum stops cross-exchange market making: <https://github.com/hummingbot/hummingbot/issues/5984>
- duplicate order-created events break persistence: <https://github.com/hummingbot/hummingbot/issues/8264>
- failed close path opens or leaves unintended positions: <https://github.com/hummingbot/hummingbot/issues/6831>

### Required capability

- authoritative cumulative-fill accounting;
- hedge based on filled quantity, not requested quantity;
- deterministic cancel/fill race resolution;
- residual-exposure budget and minimum-size handling;
- idempotent hedge requests;
- emergency hedge and explicit unhedgeable-dust state.

### Willingness-to-pay interpretation

Severity is directly tied to capital risk, but public evidence does not establish a market price. Paid pilots must test whether teams will buy a separate integrity layer rather than keep this logic in-house.

---

## 3. Connected is not current

### Triggering context

A socket reconnects or remains open, logs a successful subscription, but no valid current data reaches the strategy.

Primary examples:

- Hyperliquid reconnect logs appear successful while the strategy remains stalled: <https://github.com/hummingbot/hummingbot/issues/8250>
- Docker controller continues using data during disconnect, then stops after reconnect: <https://github.com/hummingbot/hummingbot/issues/7230>
- repeated Lighter 429 errors affect private WebSocket and candle polling: <https://github.com/hummingbot/hummingbot/issues/8309>
- Lighter private stream authentication failure despite basic authenticated access: <https://github.com/hummingbot/hummingbot/issues/8308>
- MEXC user stream repeatedly disconnects: <https://github.com/hummingbot/hummingbot/issues/7730>
- missing KuCoin perpetual trade updates: <https://github.com/hummingbot/hummingbot/issues/7482>

### Required capability

Treat health as a vector, not a Boolean:

- transport connected;
- subscription acknowledged;
- last valid message age;
- source and receive timestamp age;
- sequence continuity;
- expected heartbeat cadence;
- snapshot/recovery state;
- private-stream activity;
- REST/WS divergence;
- clock-error evidence.

Fail closed: stale, gapped, crossed, or unreproducible data produces no signal and cannot arm execution.

---

## 4. Full-cycle executable economics

### User problem

Most scanners present a top-of-book or last-price spread. The trader needs to know whether an opportunity survives actual size, both entries, both exits, fees, funding, latency, partial fills, failure attempts, and rebalancing.

### Required calculation

- verified instrument mapping;
- full-depth executable VWAP on both sides;
- maker/taker and builder/partner fees;
- entry and exit costs;
- funding amount and period normalization;
- latency-decay curve;
- maximum executable capacity;
- residual hedge allowance;
- failed-attempt economics;
- rebalance and infrastructure allocation.

### Product result

Do not return only a number. Return a typed verdict:

```text
PASS
REJECT: STALE_BOOK
REJECT: INSUFFICIENT_DEPTH
REJECT: CONTRACT_NOT_EQUIVALENT
REJECT: FEES_EXCEED_EDGE
REJECT: LATENCY_DECAY
REJECT: INSUFFICIENT_CAPACITY
UNCERTAIN: FUNDING_WINDOW_MISMATCH
```

Every verdict should be reproducible from a sealed evidence package.

### Current status

This is a Stage A/P0 target, not a claim about completed analyzer functionality. Current code can seal and read a frozen package; it does not yet justify marketing a production-grade net-edge report.

---

## 5. Connector maintenance and API drift

### Structural problem

A unified API reduces syntax differences but does not remove venue semantics:

- position and margin modes;
- reduce-only behavior;
- order-state transitions;
- contract multipliers and quantity units;
- nonce and sequence rules;
- signing and timestamp rules;
- private-stream authentication;
- rate limits;
- API migrations and deprecations.

Primary examples:

- Binance user-stream API deprecation: <https://github.com/hummingbot/hummingbot/issues/8035>
- KuCoin perpetual API migration changes execution and stream formats: <https://github.com/hummingbot/hummingbot/issues/8256>
- margin-mode mismatch after successful connector initialization: <https://github.com/hummingbot/hummingbot/issues/8224>
- stale balance recognition due to venue event semantics: <https://github.com/hummingbot/hummingbot/issues/7827>

### Direct willingness-to-pay proxy

Hummingbot connector bounties provide explicit budget evidence:

- EVEDEX connector, developer portion 3,000 USDC: <https://github.com/hummingbot/hummingbot/issues/7810>
- GRVT perpetual connector, 3,000 USDC: <https://github.com/hummingbot/hummingbot/issues/8046>
- Architect perpetual connector, 3,000 USDC: <https://github.com/hummingbot/hummingbot/issues/7919>
- Decibel perpetual connector, 4,000 USDC: <https://github.com/hummingbot/hummingbot/issues/8028>
- Backpack spot and perpetual connectors, 3,000 USDC: <https://github.com/hummingbot/hummingbot/issues/7899>
- Aevo perpetual connector, 3,000 USDC: <https://github.com/hummingbot/hummingbot/issues/7894>

This proves that connector creation has a budget. It does not yet prove recurring demand for MEE. The differentiated offer should be conformance and ongoing regression evidence, not simply another adapter.

---

## 6. Incident replay and auditability

### Job

> When an execution incident occurs, reconstruct the exact sequence across local strategy state, public data, private events, REST state, and persistent records without manually joining several logs.

### Proposed output

```text
14:02:10.121 order submitted
14:02:10.287 local timeout
14:02:10.303 venue accepted order
14:02:10.354 local retry initiated
14:02:10.401 original order partially filled
14:02:10.429 duplicate order accepted
14:02:10.610 residual exposure = +0.84 BTC
root cause: retry before authoritative reconciliation
```

### First product opportunity

A concierge incident-audit service can precede automated execution. It has lower security and custody risk, uses read-only evidence, and gives buyers a concrete result.

---

## 7. Economic instrument equivalence

Ticker equality does not prove hedge equivalence. A cross-venue pair needs evidence for:

- base and quote assets;
- product and payoff kind;
- settlement asset;
- contract multiplier;
- displayed size unit;
- quantity and price rules;
- funding interval;
- mark/index methodology;
- relevant margin and liquidation asymmetry.

The existing `mee_contracts.market` direction is strategically useful because it separates normalized economic identity from venue representation and requires equivalence evidence. The product should expose a readable `VERIFIED`, `REJECTED`, or `UNCERTAIN` report rather than internal dataclasses.

---

## 8. Fail-closed controls

Required later-stage controls include:

- risk reservation before first submission;
- maximum residual exposure;
- venue/account health gates;
- stale-reconciliation cutoff;
- exact order ownership;
- emergency hedge;
- strategy and account kill switches;
- no blind retry;
- explicit `MANUAL_INTERVENTION` state.

These controls are roadmap candidates, not live authorization.

---

## 9. Realistic replay and backtesting

Historical data, OHLCV backtests, and full-depth datasets already exist. Raw replay is not a sufficient moat.

MEE should differentiate through:

- identical contracts for live capture and replay;
- sequence-gap and staleness injection;
- latency distributions rather than a single fixed delay;
- partial, late, and duplicate fill simulation;
- full-cycle cost accounting;
- reproducible opportunity decisions and reason codes.

---

## 10. Capital fragmentation and rebalancing

The pain is credible: collateral is split across venues, idle capital grows, and withdrawals or bridges create latency and operational risk.

It is not a first-product recommendation because it expands into private balances, transfer permissions, custody-like responsibilities, chain risk, withdrawal controls, and regulatory review. Keep it as a measured later hypothesis.

---

# Competitor and substitute map

| Category | Representative substitutes | What is commoditized | Remaining operational pain |
|---|---|---|---|
| Unified exchange APIs | CCXT and venue SDKs | REST/WS method normalization and broad venue coverage | semantic drift, order convergence, failure behavior, conformance |
| Open-source bot frameworks | Hummingbot, Freqtrade, OctoBot | strategy scaffolding, connectors, basic backtesting, UI/Telegram control | production reliability across venues, state divergence, incident diagnosis |
| Retail terminals and bots | exchange-native apps, GoodCrypto-like products, grid/DCA platforms | dashboards, alerts, manual order entry, simple automation | trust, keys, execution correctness, full-cycle economics |
| Portfolio tracking | exchange dashboards, local-first trackers such as rotki | read-only portfolio views | authoritative execution timeline and cross-venue order ownership |
| Historical-data and replay tools | data vendors and HFT backtest frameworks | raw tick/L2 data and generic replay | evidence-bound live/replay parity and failure-mode simulation |
| Internal desk infrastructure | custom OMS, risk, reconciliation, monitoring | none; rebuilt repeatedly | engineering cost, adapter maintenance, auditability, deterministic recovery |

## Conclusion

“Supports N exchanges” is not a durable differentiator. The wedge must be reliability, evidence, and deterministic cross-venue state handling.

---

# Initial ICP

## ICP 1 — small quant or proprietary trading team

Profile:

- 2–10 people;
- operates 2–8 venues;
- already has strategies and engineers;
- uses exchange SDKs, CCXT, Hummingbot, or custom adapters;
- can provide logs and order exports;
- feels connector, reconciliation, and incident-response cost.

Primary JTBD:

> Keep keys and strategy code under our control while obtaining one authoritative, replayable view of orders, fills, positions, venue health, and residual exposure.

Why first:

- severity is tied to capital and engineering time;
- technical buyer understands the problem;
- self-hosted/read-only deployment reduces trust friction;
- potential contract value is materially higher than mass retail.

## ICP 2 — trading-product or connector developer

Profile:

- bot platform, signal product, wallet, terminal, execution API, or exchange-integration team;
- maintains multiple venue-specific implementations;
- needs conformance, regression, reconciliation, and incident evidence.

Primary JTBD:

> Delete venue-specific order-state and failure-recovery logic from product code without giving up deterministic behavior or self-hosted control.

## Secondary ICP — self-hosted prosumer

Technically capable trader already using a VPS and restricted API permissions. Lower price and higher support burden make this a second-stage segment.

## Excluded initial ICP — mass retail

Mass retail has low willingness to pay, high support demand, return expectations, key-security concerns, churn, and regulatory/reputation risk. Do not use it to validate execution infrastructure.

---

# Product wedges

## Wedge A — MEE Evidence

Promise:

> Your scanner found a spread. MEE proves whether the observation and economics were valid.

Initial scope:

- public data only;
- Hyperliquid and Lighter first;
- sealed capture package;
- freshness and continuity verdict;
- reviewed instrument mapping;
- executable-depth and cost report when P0 implementation supports it;
- evidence hash and typed reject reasons.

Why first:

- closest to Stage A;
- no trade keys or custody;
- easy to demonstrate and falsify;
- produces evidence needed by later products.

Main risk:

A scanner or raw-data product is commodity. The result must be a reproducible verdict, not another list of spreads.

## Wedge B — MEE Observer

Promise:

> Detect when your bot and the venue disagree before the strategy retries or compounds the error.

Initial scope:

- self-hosted read-only private access;
- local event ingestion;
- authoritative exchange-state polling;
- ghost/missing order detection;
- late/duplicate fill detection;
- stream-health vector;
- incident package and alert.

Why second:

It validates reconciliation value without placing orders.

## Wedge C — MEE Integrity

Promise:

> Every order converges to one authoritative state; every residual exposure is known and bounded.

Later scope:

- submission state machine;
- persistent ownership and idempotency;
- cumulative fills;
- residual hedge;
- restart recovery;
- manual intervention;
- paired execution.

Risk:

Highest security, operational, and legal burden. Do not build before paid observer/evidence validation.

## Optional B2B wedge — Connector Conformance Lab

Promise:

> Prove a venue connector survives production failure modes before customer capital does.

Test catalog:

- reconnect and resubscribe;
- stale stream and sequence gap;
- timeout before acknowledgement;
- late and duplicate events;
- partial fills;
- cancel/fill race;
- restart recovery;
- rate-limit exhaustion;
- position/margin-mode mismatch;
- API deprecation and schema drift.

Risk:

Avoid becoming an unscalable custom-development agency. Standardize scenarios, evidence format, and recurring regression monitoring.

---

# What not to build now

1. **Generic multi-exchange terminal.** Existing exchange apps and terminals already cover the visible workflow; key setup and switching cost remain high.
2. **Generic funding scanner.** Free and bundled alternatives exist; discovery without reliable execution is weak willingness-to-pay evidence.
3. **“AI trading bot.”** AI branding does not solve state convergence, stale streams, or partial fills and increases scam-category distrust.
4. **Passive or risk-free arbitrage product.** Market-neutral is not risk-free; marketing returns before evidence creates reputational and regulatory risk.
5. **Telegram Mini App as the product.** Telegram may distribute alerts or onboarding, but it is not the core value.
6. **Hosted retail autopilot.** Do not begin with customer trade keys, capital, or performance expectations.
7. **Many connectors before conformance.** One pair must pass data, mapping, replay, reconnect, fill, and reconciliation gates before adding the next.
8. **Automatic withdrawals or rebalancing.** Explicitly outside the current safety boundary.

---

# MVP and validation packages

## Evidence pilot

Scope:

- one venue pair;
- BTC, ETH, and SOL where mappings are reviewed;
- 7–14 days of public observations;
- freshness, sequence, depth, fees, funding, latency decay, and capacity;
- reproducible package and rejection reasons.

Customer commitment test:

- paid pilot or deposit;
- access to the customer’s existing signal definitions;
- technical review of results.

## Incident audit pilot

Input:

- bot logs;
- exchange order/fill export;
- configuration;
- timestamps and relevant public data.

Output:

- normalized timeline;
- local/venue divergence;
- root cause hypothesis with confidence;
- maximum observed residual exposure;
- recommended invariant and replay test.

## Read-only observer pilot

Scope:

- one exchange account with withdrawal disabled;
- no order placement;
- compare local bot events with authoritative exchange state;
- alert and persist divergence evidence.

---

# Landing-page hypotheses

## Evidence positioning

**Headline**

> Your scanner found a spread. MEE proves whether it was executable.

**Subheadline**

> Full-depth market evidence, fees, funding, latency, and contract equivalence — preserved in a reproducible package.

**CTA**

> Run a read-only evidence capture

## Reconciliation positioning

**Headline**

> A timeout is not a failed order.

**Subheadline**

> Detect ghost orders, late fills, duplicate events, and local-to-exchange divergence before retrying.

**CTA**

> Submit an execution incident

## Professional-team positioning

**Headline**

> Every fill. One authoritative state.

**Subheadline**

> Self-hosted reconciliation and residual-exposure control for multi-venue trading systems.

**CTA**

> Apply for a paid integrity pilot

## Reusable creative hooks

- `Connected isn’t current.`
- `No proof. No signal.`
- `Prices are screenshots. Execution is economics.`
- `Your bot says canceled. The exchange says filled.`
- `Two orders do not make a hedge.`
- `Bring us an arbitrage signal. We’ll try to disprove it.`

Do not use guaranteed APR, passive income, risk-free arbitrage, or AI-profit claims.

---

# Pricing hypotheses

These are test ranges, not established prices.

| Offer | Price hypothesis | What it tests |
|---|---:|---|
| Evidence or incident pilot | EUR 1,000–3,000 fixed scope | whether teams pay for proof and diagnosis rather than alerts |
| Self-hosted prosumer evidence/observer | EUR 149–399/month | repeat usage with limited support |
| Small-desk integrity layer | EUR 2,000–10,000/month | engineering and capital-risk value, private deployment |
| Connector conformance | EUR 3,000–10,000 initial + EUR 500–2,000/month | development budget plus recurring API-drift monitoring |

Prefer fixed subscription and usage pricing. Do not start with performance fees.

---

# Interview questions that reduce confirmation bias

Ask about past behavior, not opinions:

1. Describe the last incident where your bot and exchange disagreed.
2. Show the logs, order export, or incident ticket.
3. What happens after a submission timeout?
4. What evidence is required before a retry?
5. How do you recover after restart with open orders?
6. How long did the last reconciliation incident take to diagnose?
7. What was the maximum residual exposure?
8. Which connectors consume the most maintenance time?
9. What monitoring, data, or execution tools do you already pay for?
10. What have you built internally because existing products were insufficient?
11. Which data or credentials cannot leave your environment?
12. Would you install a self-hosted read-only observer?
13. Will you provide one real incident for a pilot?
14. Will you pay a deposit now rather than after a finished product exists?
15. Which current component would you delete if MEE worked?

Praise, likes, wait-list signups, and hypothetical intent do not count as commitment.

---

# Go criteria

Continue productization when a discovery round produces all or most of the following:

- at least 15 qualified interviews;
- at least 8 teams provide real logs or order exports;
- at least 5 install an observer or complete an evidence pilot;
- at least 3 pay or place a meaningful deposit;
- at least 2 renew after the first cycle;
- the same failure class is reproduced across at least two venues;
- incident diagnosis time decreases by at least 50%;
- MEE detects real divergence earlier than the customer’s existing process;
- evidence analysis rejects a material share of apparent opportunities for defensible reasons;
- buyers use reports to change capital allocation, strategy thresholds, or connector decisions.

---

# Kill criteria

Pause, narrow, or repurpose the product if:

- users want only free alerts or spread lists;
- no qualified team will provide even sanitized incident evidence;
- no paid pilot or deposit is obtained;
- every incident is unique and cannot produce reusable invariants;
- customers prefer direct SDKs and estimate connector maintenance as immaterial;
- realistic shadow economics show no repeatable net edge or useful capacity;
- observer findings do not change decisions or prevent incidents;
- private-integration support and security cost exceed plausible revenue;
- the only demand comes from novices expecting guaranteed returns;
- the best use remains internal proprietary research, in which case optimize for internal truth rather than inventing consumer PMF.

---

# Current product recommendation

Use the following external product hierarchy:

```text
MEE Evidence
Proves the quality and reproducibility of market observations and shadow economics.

MEE Observer
Detects local-versus-venue divergence and produces incident evidence without placing orders.

MEE Integrity
Converges order state and bounds residual exposure after paid validation and safety review.
```

Recommended positioning:

> **Most scanners find opportunities. Multi-Exchange Engine tries to disprove them.**

Supporting line:

> **No proof. No signal.**

This is a product-discovery recommendation. Runtime code, tests, ADRs, `SECURITY.md`, and the roadmap remain authoritative for implementation status.

---

# Current source register

## Repository-local strategic inputs

- [`X_TWITTER_PAINS_INPUT_2026-08-10.md`](X_TWITTER_PAINS_INPUT_2026-08-10.md) — raw discovery input; not independently sufficient.
- [`TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md`](TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md) — verified technical extraction and chain-boundary analysis.
- [`../PMF_CRITICAL_REVIEW.md`](../PMF_CRITICAL_REVIEW.md) — adversarial PMF assessment.
- [`../COMPETITIVE_CODE_INTELLIGENCE.md`](../COMPETITIVE_CODE_INTELLIGENCE.md) — competitor code and SDK evidence.
- [`../SOURCE_LEDGER.md`](../SOURCE_LEDGER.md) — maintained external-source registry and confidence policy.

## High-signal production issue set

- Hummingbot #8250 — reconnect succeeds in logs but trading remains stalled.
- Hummingbot #7230 — strategy loses state and stops after network loss.
- Hummingbot #7294 — failure event followed by real fill and duplicate retry.
- Hummingbot #7295 — double close fill in funding arbitrage.
- Hummingbot #7139 — cancel/fill race leaves maker exposure unhedged.
- Hummingbot #7129 — partial market close never converges.
- Hummingbot #5984 — residual fill below taker minimum.
- Hummingbot #7032 — ghost orders and local/exchange position drift.
- Hummingbot #6831 — close action produces wrong position behavior.
- Hummingbot #8264 — duplicate order-created events break persistence.
- Hummingbot #7827 — balance state remains stale for roughly two minutes.
- Hummingbot #8308/#8309 — Lighter private-stream and rate-limit failures.
- Hummingbot #8035/#8256 — external API deprecation and migration burden.

All exact URLs are included in the relevant JTBD sections above and should be recorded in `../SOURCE_LEDGER.md` when promoted into a maintained claim.

---

# Roadmap promotion rule

A pain becomes an implementation requirement only when all of the following are present:

1. named target user and JTBD;
2. repeated independent evidence;
3. material severity or frequency;
4. expensive or failed workaround;
5. credible willingness-to-pay, adoption, or capital-allocation evidence;
6. fit with the execution/evidence thesis;
7. falsifiable acceptance criterion;
8. explicit kill criterion;
9. security and legal review for private APIs, execution, or user funds;
10. explicit roadmap or ADR approval.

## Navigation rule

Any agent making a PMF, packaging, ICP, pricing, landing-page, connector-priority, observer, reconciliation, or execution-roadmap decision must read this file together with:

- [`../../../README.md`](../../../README.md);
- [`../../ROADMAP.md`](../../ROADMAP.md);
- [`../../../SECURITY.md`](../../../SECURITY.md);
- [`../PMF_CRITICAL_REVIEW.md`](../PMF_CRITICAL_REVIEW.md);
- [`../SOURCE_LEDGER.md`](../SOURCE_LEDGER.md).

Research can change what should be built. It cannot claim that a feature already exists.
