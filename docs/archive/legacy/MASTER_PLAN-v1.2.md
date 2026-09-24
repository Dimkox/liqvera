# Master Project TODO & Research
## Multi-Exchange Execution OS + Private Solana Intelligence Terminal

**Version:** 1.2\
**Date:** August 6, 2026\
**Previous version:** 1.1 (August 6, 2026)\
**Status:** living master document\
**Purpose:** a single source of truth for the project, research, architecture, competitors, and tasks

---

# Changelog 1.1 → 1.2 (August 6, 2026)

- **Two subsystems combined in one product / repository:**
  1. Cross-exchange perpetual execution & risk engine (HL, Lighter, Variational, CEX) — already bootstrapped.
  2. Private Solana Intelligence & Execution Terminal (Observe→Shadow→Paper→Live, Wallet DNA, Copy Score, Anti-Copy) — full backlog in `docs/SOLANA_TERMINAL_TODO.md`.
- Product charter Solana: `docs/solana-product-charter.md`.
- ADR-0001 Solana scope & non-goals: `docs/adr/0001-solana-scope-and-non-goals.md`.
- Solana — **Wave A–E** (core intelligence + gated copy/execution); cross-venue perps — **Wave F** / XVN-* after Solana G7 *or* in parallel on the already completed HL/Lighter adapters.
- Solana non-goals are fixed hard boundaries (no wash volume, holder farming, custody of others' funds, or SaaS).
- Signer isolation is mandatory for any Live mode (Solana and perps).

# Changelog 1.0 → 1.1 (August 6, 2026)

- Verified the strategic hypothesis (product = execution OS, not frontend).
- Confirmed Lighter integration in Wallet in Telegram (April 2026).
- Recorded official Lighter Standard / Premium / Plus latency/fee tiers.
- Completed an architectural audit of VOOI funding-bot-example and perp-cli.
- Confirmed the existence of kSHIB on Hyperliquid; **the multiplier is confirmed by live meta (1 unit = 1000 SHIB, szDecimals=0)**.
- Clarified Variational status (SDK exists, full trading API is gated).
- Updated sections 5, 6, 12, 13, 16, and 20.
- Added Decision D-009.
- Marked completed research items.

---

# 0. Brief conclusion

The project is a **unified Multi-Exchange Execution OS** with two operational subsystems in one repository:

### Subsystem A — Solana Intelligence & Gated Execution (Wave A–E)

A private analytics and trading terminal:

- near-real-time ingest Solana mainnet;
- decode Pump.fun / Raydium / Meteora / Orca / Jupiter / SPL;
- Wallet DNA, Token Risk, strategy classification, **Copy Score**, hard **NON_COPYABLE**;
- **Observe → Shadow → Paper → Live** modes without skipping steps;
- isolated signer; Jupiter V2 primary;
- private Web UI (VPN).

Full backlog: [`docs/SOLANA_TERMINAL_TODO.md`](docs/SOLANA_TERMINAL_TODO.md).\
Charter: [`docs/solana-product-charter.md`](docs/solana-product-charter.md).  
ADR: [`docs/adr/0001-solana-scope-and-non-goals.md`](docs/adr/0001-solana-scope-and-non-goals.md).

### Subsystem B — Cross-exchange Perp Execution (already in code + Wave F)

> **Execution and risk engine for delta-neutral trading between DEX and CEX.**

Venues:

- Hyperliquid — adapter + market data + trading (dry-run/live path) **complete**;
- Lighter — market data + trading adapter **complete**; HL↔Lighter shadow scanner **complete**;
- Variational — after the official API;
- Bybit / MEXC / HTX — CEX hedge legs;
- Extended — later DEX.

The moat is **not** connector count (commoditized), but:

- two-leg execution + reconciliation + partial fill + residual hedge;
- instrument normalization (kSHIB = 1000 SHIB);
- net P&L after all fees/latency;
- for Solana, refusing to copy non-copyable strategies and reporting honest follower PnL.

**Status (August 6, 2026):** the execution-OS hypothesis is confirmed; HL/Lighter bootstrap is in the repo; the Solana backlog is included in the same MASTER_PLAN as the primary product surface for intelligence + copy.

---

# 1. Project background

## 1.1. Original idea

The original idea:

- mobile access to perp DEX without official apps;
- Telegram Mini App instead of Kotlin/Android;
- worldwide distribution;
- priority for tier-2/3 GEO;
- monetization through builder fees and referrals;
- initial venues: Extended, Reya, Ostium.

Reasons for choosing a Telegram Mini App:

- cheaper than native development;
- no Google Play review required;
- rapid updates;
- a direct funnel from Telegram;
- convenient push notifications through the bot;
- less dependence on app-store restrictions.

## 1.2. Initial technical foundation

Extensive technical research was conducted:

### Extended

- Starknet;
- SNIP-12;
- Poseidon;
- Stark curve;
- builder fee;
- referral program;
- official Python SDK;
- Rust crypto library;
- JS WASM wrapper;
- test vectors;
- quantization;
- expiration;
- signed i64 conversion;
- builder fee in the order hash.

### Reya

- EIP-712;
- ABI-encoded order inputs;
- packed nonce;
- separate cancellation signature;
- remote config due to the Evolution migration.

### Ostium

- Arbitrum contracts;
- Python SDK;
- RWA perps;
- specific limit/stop behavior.

## 1.3. Existing Hyperliquid bot

It later emerged that a working bot already existed:

- connected to Hyperliquid;
- an adapted clone of an HTX futures grid bot;
- generated more than $10,000 in the owner's trading volume;
- sees dynamic markets;
- sees `DOGE-USDC`;
- sees `kSHIB`;
- has partial trading capability.

This changed the priorities.

Hyperliquid became the following rather than a new integration:

- the initial adapter;
- a test venue;
- a source of a real order lifecycle;
- a refactoring testbed;
- the first leg of future arbitrage.

---

# 2. Why we changed strategy

## 2.1. A mobile client was no longer unique

During the research, the following appeared or were discovered:

- official mobile apps;
- Hyperliquid clients;
- Lighter mobile;
- Wallet in Telegram with Lighter;
- Liquid;
- goodcryptoX;
- Dexari;
- Apex Mini App;
- other specialized clients.

Therefore, “DEX on your phone” is an insufficient offering.

## 2.2. Lighter is already integrated into Telegram

A critical competitive fact (confirmed August 6, 2026):

- Lighter has been available inside Wallet in Telegram since April 2, 2026;
- 50+ markets, up to 50x leverage, native experience;
- the mere fact of “Lighter in Telegram” is no longer an advantage.

Therefore, Lighter should be an execution venue, not the center of marketing.

## 2.3. Multi-DEX aggregation already exists

Products discovered and audited:

- Liquid (Paradigm-backed);
- goodcryptoX;
- VOOI (unified API + open-source funding bot);
- perp-cli (hypurrquant);
- Hummingbot;
- PD AIO SDK;
- other frameworks.

Therefore, “one interface for several perp DEX” is also an insufficient offering.

## 2.4. Funding scanners are already commoditized

GitHub has a large number of:

- funding scanners;
- Telegram alerts;
- arbitrage dashboards;
- exchange adapters;
- basic bots.

Therefore, a scanner is a feature, not a moat.

## 2.5. The main difficulty is execution correctness

Research into Hummingbot and other projects showed a real failure mode:

```text
close order sent
→ failure event
→ fill event
→ retry
→ duplicate close
→ reversed exposure
```

(Documented race condition in Hummingbot Hyperliquid perpetual, issue #7295.)

Thus, the hardest and most valuable part of the product is:

- not spotting a spread;
- not sending a REST request;
- but correctly determining the state after timeout, reject, late fill, and restart.

---

# 3. Current product definition

## 3.1. What we are building

> **An execution OS for trading perp instruments across multiple DEX and CEX.**

The Telegram Mini App is:

- a control panel;
- a portfolio interface;
- an opportunities screen;
- a notification system;
- a means of confirming actions.

The backend is the actual product.

## 3.2. Core modes

### Unified portfolio

- balances;
- positions;
- funding;
- realized/unrealized P&L;
- margin;
- venue health.

### Funding arbitrage

- long on one venue;
- short on another;
- net funding after fees and exit cost.

### Price/basis arbitrage

- executable VWAP comparison;
- simultaneous or hedge-first execution;
- closing on convergence.

### DEX ↔ CEX hedge

- DEX as the opportunity source;
- CEX as the liquid hedge leg.

### RFQ arbitrage

After the Variational API:

```text
Variational RFQ
→ compare hedge VWAP
→ accept quote
→ immediate hedge
```

---



## 3.0. Unified product (v1.2)

One `multi-exchange-engine` repository serves:

| Subsystem | Stack (MVP) | Live mode |
|--------|------------|------------|
| Solana intelligence + copy | Rust modular monolith + isolated signer + TS UI | only after G0–G6 |
| Perp cross-venue (HL/Lighter/…) | Python adapters (already present) → unified venue traits later | dry-run → Paper → tiny Live |

Shared principles:

- risk/execution correctness > UI;
- Observe/Shadow/Paper before Live;
- signer / keys outside analytics and UI;
- instrument registry + precision quantization;
- reconciliation = source of truth for positions.

Solana non-goals (wash, farming, custody, SaaS) are **hard boundaries**.\
Perp non-goals: do not build a moat around “yet another UI aggregator.”


# 4. Current venue priorities

1. Hyperliquid
2. Lighter
3. Bybit
4. Variational
5. MEXC
6. Extended
7. HTX
8. Reya
9. Ostium

### Hyperliquid

Working code and the owner's trading volume already exist.

### Lighter

- documented API;
- WebSocket;
- API keys (index 0–3 reserved frontend);
- partner attribution;
- Standard / Premium / Plus account model;
- Standard: 0 fees + 200–300 ms latency;
- suitable for funding and opportunities that are not ultra-short-lived.

### Bybit

- strong API;
- good liquidity;
- convenient hedge leg;
- CEX benchmark.

### Variational

- official Python SDK;
- API access gated (Pro not live, waitlist, trading API on the roadmap);
- RFQ model;
- important strategic differentiator.

### MEXC

- many altcoins;
- potential price dislocations;
- useful hedge leg;
- more challenging market quality.

### Extended

- builder fee;
- low competition;
- Stark integration already researched;
- but not the first execution priority.

---

# 5. What has already been verified

## 5.1. For the current project

- Hyperliquid is connected.
- The bot executes trades.
- More than $10,000 of the owner's volume has been traded.
- Market discovery works at least partially.
- `DOGE-USDC` and `kSHIB` are visible.
- The existing code contains HTX/grid legacy elements.
- Refactoring is required before use with user funds.

## 5.2. Lighter (updated August 6)

- an official API exists;
- WebSocket exists;
- API keys exist (up to 256 per account, indexes 0–3 reserved);
- a separate nonce per key exists;
- partner attribution exists;
- a Standard/Premium/Plus account model exists;
- **Standard Account (verified):**
  - Fees: 0 / 0
  - Taker latency: 300 ms
  - Maker / Cancel latency: 200 ms
- Premium: fees + staking discounts + lower latency;
- suitable for funding and opportunities that are not ultra-short-lived.

## 5.3. Variational (updated August 6)

- an official Python SDK exists (`variational-research/variational-sdk-python`);
- API access requires contacting the team;
- RFQ trading model;
- public API / SDK does not equal full trading access;
- Pro not live (waitlist);
- trading API is on the 2026 roadmap;
- reverse engineering a private API must not be the production path.

## 5.4. Competitors (updated August 6)

### VOOI

Audited:

- unified API;
- Lighter + Hyperliquid (+ Aster);
- production-grade open-source funding bot;
- Telegram signals example;
- REST reconciliation;
- SSE wake-up model;
- half-leg / orphan position detection;
- state snapshot + cooldown;
- margin routing;
- live bug fixes.

Fundbot structure: api / execution / position / risk / strategy / reporting.

### perp-cli (hypurrquant)

Audited:

- Hyperliquid + Lighter + Pacifica + Aster;
- dual-leg execution (`arb exec`);
- portfolio / risk / rebalance / bridge;
- client-id deduplication;
- pre-trade validation;
- TWAP / grid / DCA;
- MCP server (18 tools);
- Telegram/Discord alerts;
- a large number of tests;
- evidence of Korean QA;
- Lighter API key index default = 4.

### Hummingbot

A mature infrastructure framework and real race-condition issues (double fill on close retry) were confirmed.

### Closed-source competitors

- Wallet in Telegram + Lighter (live since April 2026);
- Liquid (Paradigm, HL + Lighter + Ostium);
- goodcryptoX (mobile bots for HL + Lighter + CEX);
- Dexari (Hyperliquid mobile).

---

# 6. What needs verification

## 6.1. Current Hyperliquid bot

The following must be proven:

- correct `clientOrderId`;
- idempotency;
- late-fill handling;
- partial fills;
- reduce-only;
- reconnect;
- restart recovery;
- position reconciliation;
- builder/referral fields;
- multiplier handling;
- fee attribution;
- no duplicate order submission.

## 6.2. `kSHIB` (updated August 6 — live meta)

- [x] The market exists on Hyperliquid.
- [x] Contract model = 1 unit of underlying (linear).
- [x] `szDecimals` = **0** (live `meta` on August 6, 2026).
- [x] Canonical: **1 unit kSHIB = 1000 SHIB** (mid ≈ 0.00492 ≈ 1000 × spot SHIB).
- [x] Quantity is integers only.
- [ ] Price / quantity normalization in the Instrument Registry.
- [ ] Matching with Bybit / MEXC / Lighter instruments (1000SHIB / SHIB1000, etc.).

**Status:** the multiplier is confirmed. The market can be included in the shadow scanner after mapping tests. Live paired execution is allowed only after full normalization and cross-venue verification.

## 6.3. Lighter

The following must be tested in practice:

- [ ] testnet/mainnet onboarding;
- [ ] API key lifecycle;
- [ ] nonce behavior;
- [ ] actual order latency (Standard vs Premium);
- [ ] cancel latency;
- [ ] private event ordering;
- [ ] partner fee;
- [ ] restart behavior;
- [ ] rejected transaction behavior;
- [ ] duplicate event behavior.

The official latency figures have already been recorded (see 5.2).

## 6.4. Variational

The following must be obtained:

- [ ] API key;
- [ ] partner contact;
- [ ] sandbox;
- [ ] RFQ endpoint specification;
- [ ] quote expiry;
- [ ] execution confirmation;
- [ ] rate limits;
- [ ] fee model;
- [ ] attribution;
- [ ] GEO rules;
- [ ] commercial terms.

## 6.5. Competitor research

In-depth research is not yet complete for:

- [ ] APK analysis (lawful static only);
- [ ] web bundle analysis;
- [ ] protobuf/GraphQL extraction;
- [ ] API endpoint mapping;
- [ ] CI/CD artifact analysis;
- [ ] Korean forks;
- [ ] Korean Telegram Mini Apps;
- [ ] closed-source architecture indicators.

---

# 7. Competitive conclusions

## 7.1. What is no longer a moat

- Telegram Mini App;
- Lighter integration;
- Hyperliquid integration;
- funding scanner;
- Telegram alerts;
- basic unified portfolio;
- grid;
- DCA;
- TWAP;
- standard CEX adapters.

## 7.2. Potential moat

### Execution correctness

- two-leg state machine;
- idempotency;
- fill reconciliation;
- duplicate protection;
- residual hedge;
- restart recovery.

### Contract normalization

- kSHIB;
- 1000SHIB;
- aliases;
- HIP-3 markets;
- RWA;
- quote differences.

### Real net P&L

- fees;
- slippage;
- funding;
- partner fees;
- builder fees;
- exit;
- rebalance;
- failed hedge cost.

### Variational RFQ

Official early access may provide a temporary advantage.

### Korean distribution

- Korean UX;
- terminology;
- acquisition;
- support;
- onboarding;
- content;
- local partner network.

### Proprietary execution dataset

- opportunity lifetime;
- actual slippage;
- fill probability;
- venue latency;
- reject rates;
- effective capacity.

---

# 8. Build vs Buy

## Existing components that can be reused

- public market data clients;
- standard exchange SDK;
- CEX metadata;
- Telegram notifications;
- charts;
- basic funding history;
- generic wallet libraries;
- logging/metrics stack;
- basic REST clients.

## What can be used as a benchmark

- VOOI examples (funding bot + signals);
- perp-cli;
- Hummingbot;
- PD AIO SDK;
- CCXT;
- Freqtrade.

## What cannot be fully outsourced

- order state machine;
- reconciliation;
- residual hedge;
- risk reservation;
- normalized instrument registry;
- P&L attribution;
- user-level limits;
- kill switch;
- execution history;
- venue scoring.

## VOOI shortcut

A possible fast MVP:

- use the VOOI API for Lighter + Hyperliquid;
- build Korean UX and a strategy layer on top.

Risks:

- dependence on a competitor;
- fee;
- lock-in;
- order flow exposure;
- VOOI may enter Korea itself;
- weak moat.

Recommendation (confirmed August 6):

- benchmark and prototype — yes;
- sole production dependency — no.

---

# 9. Target architecture

```text
Telegram Mini App / Web
        ↓
API Gateway
        ↓
Portfolio / Strategy / Notifications
        ↓
Opportunity Engine
        ↓
Risk Engine
        ↓
Execution Coordinator
        ↓
Exchange Adapters
        ├── Hyperliquid
        ├── Lighter
        ├── Bybit
        ├── Variational
        ├── MEXC
        ├── Extended
        └── HTX
```

## Core services

### Market Data Service

- public WebSocket;
- snapshot + delta;
- sequence;
- checksum;
- stale detection;
- reconnect.

### Instrument Registry

- canonical asset;
- venue symbol;
- multiplier;
- tick;
- step;
- min quantity;
- quote;
- settlement;
- market status.

### Opportunity Engine

- VWAP;
- funding;
- basis;
- capacity;
- opportunity decay;
- net edge.

### Execution Coordinator

- paired execution;
- maker-first;
- simultaneous;
- RFQ-first;
- partial fill;
- residual hedge;
- close.

### Risk Engine

- max notional;
- net delta;
- margin;
- unhedged timeout;
- daily loss;
- venue health;
- kill switch.

### Reconciliation Service

- private stream;
- REST state;
- open orders;
- fills;
- positions;
- unknown-state resolution.

---

# 10. Execution state machine

```text
CREATED
→ PREFLIGHT
→ RISK_RESERVED
→ LEG_A_SENT
→ LEG_B_SENT
→ PARTIALLY_FILLED
→ HEDGING
→ OPEN
→ CLOSING
→ CLOSED
```

Failure states:

```text
UNKNOWN
DEGRADED
FAILED
MANUAL_INTERVENTION
```

Main rule:

```text
request uncertain
→ private events
→ open orders
→ fills
→ position delta
→ retry only after reconciliation
```

---

# 11. Master TODO

## 11.0. Solana Terminal (full backlog)

The executable backlog for the Solana subsystem is in a separate document (same repo):

- **[`docs/SOLANA_TERMINAL_TODO.md`](docs/SOLANA_TERMINAL_TODO.md)** — phases 0–13, P0/SOL/DEC/TOK/WAL/…, gates G0–G9, first 20 commits.
- Charter / ADR: `docs/solana-product-charter.md`, `docs/adr/0001-solana-scope-and-non-goals.md`.

Order: **Wave A (data)** → B (intelligence) → C (Shadow/Paper) → D (execution) → E (ops) → **Wave F (XVN cross-venue, HL/Lighter already partly complete)**.

Do not start Live UI or native arbitrage before the first 20 Solana commits (TODO §14).

Below is the original Master TODO for the perp subsystem (Lighter/HL), which remains in effect.


## P0 — Repository and audit

- [ ] Create a clean repository.
- [ ] Create a file map of the current HTX/Hyperliquid bot.
- [ ] Isolate HTX-specific assumptions.
- [ ] Extract the grid strategy.
- [ ] Extract the Hyperliquid adapter.
- [ ] Capture current behavior in integration tests.
- [ ] Establish the DOGE market test.
- [ ] Establish the kSHIB discovery test.

## P0 — Numeric correctness

- [ ] Switch to Decimal/fixed-point.
- [ ] Ban float for money.
- [ ] Add finite validation.
- [ ] Add tick/step rounding tests.
- [ ] Add min-notional tests.
- [ ] Add multiplier tests.
- [x] Confirm the kSHIB multiplier (live meta: 1 unit = 1000 SHIB, szDecimals=0).

## P0 — Order lifecycle

- [ ] Implement `clientOrderId`.
- [ ] Implement idempotency keys.
- [ ] Store the raw request hash.
- [ ] Store the venue order ID.
- [ ] Store fill IDs.
- [ ] Implement late-fill resolution.
- [ ] Implement duplicate-fill protection.
- [ ] Implement the unknown-state workflow.
- [ ] Implement restart reconciliation.

## P0 — Risk

- [ ] Max order notional.
- [ ] Max venue exposure.
- [ ] Max net delta.
- [ ] Max unhedged duration.
- [ ] Max slippage.
- [ ] Daily loss limit.
- [ ] Venue health.
- [ ] Global kill switch.

## P0 — Lighter market data

- [x] Market metadata client.
- [x] Instrument mapping.
- [x] Public WS.
- [x] Snapshot.
- [x] Delta.
- [x] Sequence-gap recovery.
- [x] Stale detection.
- [x] Reconnect.
- [x] Funding feed.
- [x] Latency metrics.

## P0 — Lighter trading

- [x] Account onboarding. (lookup_account_index helper)
- [x] API key generation/import. (via official SDK / UI; adapter accepts key)
- [x] API key index handling. (default 4+)
- [x] Nonce manager. (SDK optimistic + explicit api_key_index)
- [x] Place limit.
- [x] Place IOC.
- [x] Place market.
- [x] Cancel.
- [x] Cancel all.
- [ ] Private stream. (structure ready; auth WS next)
- [x] Fill storage. (in-memory hooks)
- [x] Position storage. (in-memory hooks)
- [x] Reconciliation. (resolve_order_state)
- [x] Restart recovery. (local state + resolve)

## P0 — Lighter partner attribution

- [ ] Integrator account.
- [ ] User approval.
- [ ] System fee limits.
- [ ] Maker fee config.
- [ ] Taker fee config.
- [ ] Fee disclosure.
- [ ] Revenue reconciliation.
- [ ] Disable fee where edge is too small.

## P0 — Hyperliquid refactor

- [ ] Dynamic instruments.
- [ ] Separate public/private clients.
- [ ] Order gateway.
- [ ] Position reader.
- [ ] Fill listener.
- [ ] Reconciliation.
- [ ] Builder code config.
- [ ] Referral config.
- [ ] HIP-3 alias handling.
- [ ] DOGE tests.
- [ ] kSHIB tests.
- [ ] Remove grid coupling.
- [ ] Remove HTX symbol assumptions.

## P1 — Shadow scanner

- [ ] BTC.
- [ ] ETH.
- [ ] SOL.
- [ ] DOGE.
- [ ] SHIB after normalization.
- [ ] L1 spread.
- [ ] VWAP $100/$500/$1k/$5k.
- [ ] Entry fees.
- [ ] Exit fees.
- [ ] Partner fees.
- [ ] Builder fees.
- [ ] Funding.
- [ ] Slippage buffer.
- [ ] Latency buffer.
- [ ] Rebalance cost.
- [ ] Edge at 100/300/500 ms and 1/5 sec.
- [ ] Maximum executable size.
- [ ] Simulated fills.
- [ ] Minimum 7 days shadow run.
- [ ] Daily report.

## P1 — Live paired execution

- [ ] Manual confirmation.
- [ ] $50–100 per leg.
- [ ] One user.
- [ ] One execution worker.
- [ ] One strategy.
- [ ] Partial-fill handler.
- [ ] Residual hedge.
- [ ] Emergency close.
- [ ] Daily loss limit.
- [ ] 100 complete paired executions.
- [ ] Zero lost fills.
- [ ] Zero unresolved position mismatch.

## P1 — Bybit

- [ ] Public WS.
- [ ] Private WS.
- [ ] Linear perp markets.
- [ ] Order placement.
- [ ] IOC.
- [ ] Position mode.
- [ ] Reduce-only.
- [ ] Funding.
- [ ] Fee tier.
- [ ] API vault.
- [ ] IP whitelist guide.
- [ ] Withdraw disabled validation.
- [ ] Emergency hedge.

## P1 — Variational access

- [ ] Contact team.
- [ ] Request API key.
- [ ] Request sandbox.
- [ ] Request partner/integrator status.
- [ ] Request RFQ docs.
- [ ] Request rate limits.
- [ ] Request fee model.
- [ ] Request attribution model.
- [ ] Request geo policy.
- [ ] Request allowed automation scope.
- [ ] Review official Python SDK.
- [ ] Build read-only adapter.
- [ ] Build RFQ adapter after approval.

## P2 — MEXC

- [ ] Public market data.
- [ ] Private data.
- [ ] Perp order adapter.
- [ ] Funding.
- [ ] Symbol mapping.
- [ ] Altcoin liquidity filters.
- [ ] Fake-depth protection.
- [ ] Delisting risk.
- [ ] Hedge integration.

## P2 — Telegram Mini App

- [ ] Dashboard.
- [ ] Markets.
- [ ] Funding.
- [ ] Opportunities.
- [ ] Positions.
- [ ] Executions.
- [ ] Strategies.
- [ ] Risk.
- [ ] Accounts.
- [ ] Notifications.
- [ ] Korean UI.
- [ ] Korean terminology.
- [ ] Korean onboarding.
- [ ] Korean risk explanations.
- [ ] Telegram init-data verification.
- [ ] Re-auth for trade.
- [ ] Command nonce.
- [ ] Idempotency.
- [ ] Audit log.

---

# 12. Research TODO

## GitHub audit

- [x] Full file-tree audit of the VOOI funding bot (structure + reconciliation patterns).
- [ ] Full file-tree audit VOOI signals bot.
- [x] Full file-tree audit perp-cli (features + dual-leg + safety).
- [ ] Extract state machines (in more detail).
- [ ] Extract error taxonomy.
- [ ] Extract adapter interface.
- [ ] Extract reconciliation logic (deeper into the code).
- [ ] Extract multiplier handling.
- [ ] Run tests where permitted.
- [ ] Audit PD AIO SDK.
- [ ] Audit Korean `funding-arb-engine`.
- [ ] Review Hummingbot funding arb issues (race condition confirmed).
- [ ] Review Freqtrade Telegram architecture.
- [ ] Review CCXT exchange coverage.

## APK and web analysis

Only lawful static analysis of publicly obtainable client artifacts.

- [ ] goodcryptoX APK.
- [ ] Liquid app/web.
- [ ] Dexari APK.
- [ ] Hyperliquid app.
- [ ] Wallet in Telegram web surfaces.
- [ ] Identify endpoints.
- [ ] Identify WebSocket hosts.
- [ ] Identify feature flags.
- [ ] Identify analytics stack.
- [ ] Identify error monitoring.
- [ ] Identify wallet/key model.
- [ ] Identify backend aggregation.

## Korean market

- [ ] Search Korean GitHub repositories.
- [ ] Search Korean Telegram Mini Apps.
- [ ] Search Naver blogs.
- [ ] Search Korean YouTube.
- [ ] Search X Korean crypto.
- [ ] Search DC Inside.
- [ ] Map Korean perp influencers.
- [ ] Map foreign-exchange app user migration.
- [ ] Determine acquisition costs.
- [ ] Determine legal marketing constraints.

---

# 13. Next 30 days

## Week 1 (progress as of August 6)

- [x] Audit current competitive landscape (hypothesis verified).
- [x] Confirm Lighter in Telegram + latency tiers.
- [x] Clone/review VOOI funding bot + perp-cli.
- [ ] Audit current bot (file map).
- [x] Confirm `kSHIB` multiplier (live meta: 1 unit = 1000 SHIB, szDecimals=0).
- [ ] Contact Variational.
- [ ] Create Lighter account/test setup.

## Week 2

- Implement Lighter metadata.
- Implement Lighter public WS.
- Build normalized order book.
- Add latency metrics.
- Refactor Hyperliquid market data.
- Add DOGE/SHIB mapping tests.

## Week 3

- Implement Lighter signing.
- Implement nonce manager.
- Implement test orders.
- Implement private stream.
- Implement fill storage.
- Implement reconciliation.

## Week 4

- Build Hyperliquid ↔ Lighter shadow scanner.
- Run BTC/ETH/SOL/DOGE.
- Start 7-day dataset.
- Produce daily net-edge reports.
- Decide whether Standard Lighter latency is acceptable.

### 30-day deliverable

```text
Working Hyperliquid adapter
+ working Lighter adapter
+ shadow scanner
+ verified opportunity dataset
+ Variational access status
```

---

# 14. Next 90 days

## Month 2

- Complete shadow mode.
- Implement paired execution.
- Run small canary trades.
- Implement residual hedge.
- Implement kill switch.
- Add Bybit market data and trading.
- Start Korean landing and closed beta.

## Month 3

- Run 100 paired executions.
- Add Bybit as hedge venue.
- Implement funding strategy.
- Add Korean Mini App beta.
- Add Variational read-only or RFQ depending on access.
- Evaluate MEXC.
- Decide production architecture.

### 90-day deliverable

```text
Production-capable two-leg engine
+ Hyperliquid
+ Lighter
+ Bybit hedge
+ Korean closed beta
+ measured execution quality
```

---

# 15. Decision Log

### D-010 (2026-08-06) — Unified repository: Solana Terminal + Perp Execution OS

**Decision:** Solana Intelligence & Execution Terminal is **not** a separate product/repo.\
The entire backlog (`docs/SOLANA_TERMINAL_TODO.md`) and charter/ADR are incorporated into `multi-exchange-engine`.\
Perp adapters (HL, Lighter) remain Wave F / XVN and are already partly implemented.\
Solana Live only after G0–G6; cross-venue Live — G8–G9.

**Reason:** one risk/execution mindset, one operator, avoiding split-brain.


## D-001: Telegram Mini App instead of Android-first

**Decision:** Telegram-first, web-compatible backend.  
**Reason:** distribution, updates, Google Play risk.  
**Status:** accepted.

## D-002: Product is execution engine, not frontend

**Decision:** backend execution OS is core.  
**Reason:** mobile and multi-DEX frontends already exist.  
**Status:** accepted (verified August 6).

## D-003: Hyperliquid is base adapter

**Decision:** refactor existing bot rather than rewrite immediately.  
**Reason:** working code and live volume.  
**Status:** accepted.

## D-004: Lighter is first new venue

**Decision:** integrate Lighter before Extended/Reya/Ostium.  
**Reason:** API maturity, partner attribution, arbitrage pairing.  
**Status:** accepted.

## D-005: Variational only through official access

**Decision:** no production reverse engineering of private trading endpoints.  
**Reason:** fragility, terms risk, security.  
**Status:** accepted (confirmed still gated).

## D-006: Bybit before MEXC

**Decision:** Bybit first CEX hedge venue.  
**Reason:** API quality and liquidity.  
**Status:** accepted.

## D-007: Shadow mode before live arbitrage

**Decision:** at least 7–14 days.  
**Reason:** visible spread is not executable profit.  
**Status:** accepted.

## D-008: No automatic withdrawals in MVP

**Decision:** withdraw permission prohibited.  
**Reason:** credential and custody risk.  
**Status:** accepted.

## D-009: VOOI / perp-cli as benchmark only (NEW)

**Decision:** use as a reference and test-case source, not as a production dependency.\
**Reason:** lock-in, fee, order-flow exposure, risk of a competitor entering Korea.\
**Status:** accepted (August 6, 2026).

---

# 16. Open Questions

## Product

- Who is the first user: a retail farmer, a semi-pro trader, or an internal strategy?
- Is a manual terminal needed, or only strategies?
- What is the payment model: subscription, partner fee, builder fee, or profit share?
- What is the minimum deposit?

## Technical

- What language is the current bot written in?
- Can it be safely refactored without a rewrite?
- What is the exact `kSHIB` multiplier? → **1 unit = 1000 SHIB, szDecimals=0** (confirmed August 6).
- Is Standard Lighter latency (300 ms taker) sufficient for the target opportunities?
- Is Premium Lighter needed?
- Which venue events may arrive out of order?
- What is the source of truth for each adapter?

## Variational

- Will they provide an API key?
- Is there a sandbox?
- Is multi-venue hedging permitted?
- Can executable RFQs be obtained?
- How does quote expiry work?
- Is there a partner fee?

## Korea

- What is the legal classification of the frontend/execution service?
- Can derivatives be advertised?
- What GEO rules are needed?
- How sufficient is Telegram for acquisition?
- Is a Kakao/Naver acquisition layer needed?
- Is there demand for a self-hosted API-key bot?

## Business

- Is 1 bps enough?
- What is the CAC?
- What is the volume retention?
- What is the average capital?
- How much does support cost?
- What is the platform dependency risk?

---

# 17. Go / No-Go criteria

## Gate 1: Lighter adapter

Go if:

- market data is stable;
- 100 test order lifecycles;
- zero unknown unresolved state;
- restart recovery works.

## Gate 2: Shadow economics

Go if:

- opportunities persist after realistic latency (including 200–300 ms Standard Lighter);
- net edge is positive after all fees;
- capacity is sufficient.

No-Go if profit exists only at the last price or with zero latency.

## Gate 3: Live canary

Go if:

- zero lost fills;
- residual hedging works;
- slippage matches the model;
- daily loss is controlled.

## Gate 4: Korean beta

Go if:

- onboarding is understandable;
- users connect accounts;
- a manual paired trade completes;
- there are no critical security incidents.

## Gate 5: Variational

Full integration only with official API access.

---

# 18. Definition of Done MVP

- [ ] Hyperliquid and Lighter implement a shared adapter interface.
- [ ] DOGE is mapped correctly.
- [x] kSHIB multiplier confirmed (1 unit = 1000 SHIB, szDecimals=0); mapping + cross-venue verification still required.
- [ ] Local order books exist.
- [ ] A funding scanner exists.
- [ ] Executable VWAP exists.
- [ ] Shadow mode has collected at least 7 days.
- [ ] A two-leg state machine exists.
- [ ] Partial-fill handling exists.
- [ ] Residual hedging exists.
- [ ] Reconciliation exists.
- [ ] A kill switch exists.
- [ ] 100 small paired executions completed.
- [ ] Lost fills = 0.
- [ ] Unresolved position mismatch = 0.
- [ ] Bybit is available as a hedge leg.
- [ ] Telegram Mini App shows the portfolio and opportunities.
- [ ] Korean locale works.
- [ ] Variational is displayed only in the available mode.
- [ ] All fees are disclosed to the user.
- [ ] Withdrawal permissions are not used.

---

# 19. Source and repository queue

## Primary code sources

- `vooi-app/vooi-funding-bot-example` (audited structure)
- `vooi-app/vooi-signals-bot-example`
- `hypurrquant/perp-cli` (audited features)
- `hummingbot/hummingbot`
- `variational-research/variational-sdk-python`
- `0xarkstar/PD-AIO-SDK`
- `ccxt/ccxt`
- `freqtrade/freqtrade`

## Existing project references

- `x10xchange/python_sdk`
- `x10xchange/rust-crypto-lib-base`
- `x10xchange/stark-crypto-wrapper-js`
- `Reya-Labs/reya-python-sdk`
- `your-quantguy/perp-dex-tools`
- `buddies2705/awesome-perp-dex`

## Follow-up Korean/long-tail audit

- `rhwhdgks/funding-arb-engine`
- `Nicolas-Formenton/delta-hedge`
- `aferist777/spwa-v1`
- `pa111111/funding-scout-oss`
- `NikitaPirate/fundingpulse`
- `mkzung/drift-funding-monitor`

---

# 20. Research status

## Completed

- initial market map;
- Extended/Reya/Ostium technical research;
- Hyperliquid project status discovery;
- Lighter priority decision;
- Variational SDK discovery;
- VOOI discovery + architectural audit (structure, reconciliation, half-leg handling);
- perp-cli discovery + feature audit (dual-leg, safety, MCP);
- Hummingbot failure-mode discovery (race condition confirmed);
- Korean product positioning review;
- **Lighter Standard/Premium latency & fee tiers (official docs)**;
- **Wallet in Telegram + Lighter integration (live since Apr 2026)**;
- **Strategic hypothesis verification (August 6, 2026)**;
- **kSHIB existence on Hyperliquid confirmed**;
- **kSHIB multiplier confirmed (1 unit = 1000 SHIB, szDecimals=0)**.

## In progress

- APK/bundle acquisition;
- static client analysis;
- GitHub/CI deep audit (state machines, error taxonomy);
- API/WS/protobuf mapping;
- architecture comparison;
- code reuse/license review.

## Pending

- final competitor matrix;
- closed-source endpoint map;
- Korean local app repository map;
- production architecture comparison;
- comprehensive license matrix;
- execution state-machine comparison (detailed extraction);
- Variational outreach result.

---

# 21. Final strategic statement

The project should not compete as:

- yet another mobile terminal;
- yet another Hyperliquid client;
- yet another Lighter Mini App;
- yet another funding scanner.

The project should compete as:

> **A Korean-first cross-exchange execution company that can safely open, monitor, and close delta-neutral positions between DEX and CEX.**

Telegram is the control channel.

Lighter, Hyperliquid, Variational, Bybit, and MEXC are venues.

The actual product:

- state machine;
- risk engine;
- reconciliation;
- normalization;
- execution data;
- distribution.
