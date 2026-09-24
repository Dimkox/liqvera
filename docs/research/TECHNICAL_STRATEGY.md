# Technical Strategy After Research

Snapshot: **2026-08-10**

[Research index](README.md) · [Current ADR](../adr/0001-python-universal-arbitrage-core.md) · [Roadmap](../ROADMAP.md)

## Scope

This is strategic guidance, not proof of implemented runtime capability. The accepted runtime direction is the Python modular monolith in ADR-0001. Existing Go code remains a historical/reference implementation until Python parity is demonstrated and superseded files are removed through a reviewed change.

## Surviving technical thesis

The project should optimize for **state correctness under asynchronous exchange behavior**, not for adapter count or UI breadth.

Core value chain:

```text
raw venue evidence
→ normalized economic identity
→ executable market state
→ opportunity falsification
→ risk reservation
→ execution saga
→ authoritative reconciliation
→ residual hedge
→ net P&L attribution
```

If any step cannot be made deterministic enough to explain after restart, the system should fail closed.

---

## 1. Runtime shape

Accepted direction:

- Python modular monolith;
- capability-specific adapters;
- PostgreSQL as authoritative durable state/evidence store;
- shadow/read-only first;
- Telegram/web as projections, not execution authority;
- no live execution until explicit later arming gate.

Capability boundaries:

```text
market data adapter
account/reconciliation adapter
trading adapter
RFQ adapter
```

Do not force RFQ venues such as Variational into a CLOB-shaped interface.

---

## 2. Economic identity before symbol equality

A common market is not established because two venue strings look similar.

Required identity fields include:

- canonical underlying asset;
- instrument/payoff kind;
- contract multiplier;
- quote asset;
- settlement/collateral asset;
- linear/inverse semantics;
- quantity unit;
- price unit;
- venue market ID;
- evidence source/version.

Examples such as `kSHIB`, `1000SHIB`, aliases and RWA contracts make this mandatory.

Fail closed when equivalence is uncertain.

---

## 3. Market data invariants

Each venue path should support, where applicable:

1. snapshot;
2. incremental updates;
3. sequence validation;
4. crossed-book rejection;
5. freshness policy;
6. reconnect/resubscribe;
7. deterministic replay from stored evidence.

An opportunity must be reproducible from stored input state.

Do not calculate arbitrage from last trade or headline best bid/ask alone. Use executable depth/VWAP for the configured base exposure.

---

## 4. Opportunity model

Net opportunity must include:

- buy/sell executable VWAP;
- venue trading fees;
- builder/partner/integrator fees;
- expected exit cost;
- funding by actual venue interval/sign convention;
- latency/slippage buffer;
- rebalance cost;
- capacity;
- data age;
- contract multiplier normalization.

Store opportunity decay at multiple horizons, e.g. 100/300/500/1000 ms and longer where useful.

The scanner's job is primarily to **falsify fake edge**.

---

## 5. Order state machine

Never collapse submission into a boolean success/failure.

Suggested semantic states:

```text
CREATED
PREFLIGHT_OK
RISK_RESERVED
SUBMITTING
PENDING
UNKNOWN
PARTIALLY_FILLED
RECONCILING
HEDGING
OPEN
CLOSING
CLOSED
FAILED
MANUAL_INTERVENTION
```

Critical rule:

```text
network/API failure != proof order was not accepted
```

Unknown outcome blocks blind retry.

---

## 6. Reconciliation algorithm

When submission outcome is uncertain:

```text
private order/fill events
+ open orders
+ fills/trade history
+ position delta
+ venue-specific authoritative query
→ resolve state
```

Only after authoritative resolution may the engine retry, hedge or escalate.

Convert real public failure cases from mature projects such as Hummingbot into regression/chaos scenarios.

---

## 7. Paired execution

Possible strategy modes:

- simultaneous primary legs;
- maker-first + hedge-on-fill;
- liquid-venue-first;
- RFQ-first + immediate hedge.

No universal order exists; strategy decides based on venue characteristics.

Execution group must persist:

- intended canonical base quantity;
- each venue's native quantity;
- client/venue order IDs;
- cumulative authoritative fills;
- residual canonical delta;
- hedge actions;
- timestamps;
- risk reservation;
- final P&L.

---

## 8. Residual hedge

Calculate in canonical base units:

```text
residual_delta = canonical_filled_long - canonical_filled_short
```

Never subtract raw venue quantities without multiplier normalization.

Hedge policy must define:

- threshold;
- preferred venue;
- max slippage;
- timeout;
- fallback close behavior;
- manual-intervention boundary.

---

## 9. Lighter strategy

Lighter remains the first new venue after Hyperliquid because it provides official API/SDK paths, public/private data, trading and partner economics.

But Standard-account latency means the initial research should focus on:

- funding spreads;
- basis dislocations lasting longer than sub-100ms;
- shadow capacity;
- actual order/cancel latency measurement.

Do not assume micro-HFT viability.

Partner/integrator fee must be part of net-edge calculation and should be configurable or disabled where it destroys strategy economics.

---

## 10. Hyperliquid strategy

The current bot/history is an asset only after exchange-specific/grid assumptions are separated from reusable behavior.

Required audit targets:

- dynamic market discovery;
- exact order ownership;
- client order IDs;
- signing/key boundaries;
- fill handling;
- restart behavior;
- reduce-only;
- builder/referral attribution;
- HIP-3/alias markets;
- DOGE and `kSHIB` regression tests.

The existing bot should be treated as evidence and reference code, not assumed production-safe.

---

## 11. Variational strategy

Variational is a gated official integration opportunity.

Before coding live execution, obtain:

- API credentials;
- sandbox/test environment;
- RFQ request/accept lifecycle;
- expiry semantics;
- execution confirmation semantics;
- rate limits;
- automation policy;
- fee/partner/referral terms;
- geo restrictions.

RFQ workflow:

```text
request executable quote
→ validate remaining TTL
→ price hedge on other venue
→ reserve risk
→ accept RFQ
→ hedge immediately
→ reconcile both sides
```

No production private-endpoint reverse engineering.

---

## 12. CEX hedge strategy

Bybit remains the preferred first CEX hedge adapter, followed by MEXC.

Credential rules:

```text
READ = on
TRADE = on
WITHDRAW = off
IP whitelist = on where supported
subaccount = preferred
```

Automatic withdrawal/rebalancing is out of MVP scope.

CEX adapters are not a moat; their value is liquidity and execution optionality.

---

## 13. Build vs buy

### Commodity / acceptable to reuse

- official SDKs;
- public market-data plumbing;
- generic CEX adapters where semantics are understood;
- Telegram notification plumbing;
- charting;
- standard metrics/logging;
- generic wallet libraries.

### Benchmark external implementations

- VOOI examples;
- perp-cli;
- Hummingbot;
- CCXT/Freqtrade;
- unified perp SDKs.

### Keep as first-class internal logic

- economic identity registry;
- opportunity falsification;
- execution saga;
- idempotency/ownership;
- reconciliation;
- residual hedge;
- risk reservation;
- venue-health gates;
- P&L attribution;
- evidence/replay model.

---

## 14. Validation order

### Gate A — deterministic read-only evidence

- verified common markets;
- fresh coherent books;
- reproducible VWAP/opportunity calculations;
- stored evidence.

### Gate B — single-venue safety

- idempotent client IDs;
- private fill/order stream;
- unknown-state reconciliation;
- restart recovery;
- fault injection.

### Gate C — paired shadow economics

7–14 days of realistic shadow data with costs and latency decay.

### Gate D — tiny live canary

Only after explicit arming change and review. Measure correctness, not profit.

### Gate E — product packaging

Only after economics and user commitment exist.

---

## 15. Kill gates

Stop or narrow if:

- realistic shadow net edge is absent;
- capacity is economically irrelevant;
- unknown-state reconciliation is not deterministic enough;
- incidents dominate expected return;
- users will not commit keys/capital/payment;
- legal/distribution constraints make target packaging unattractive;
- the most valuable result is clearly internal proprietary execution rather than a consumer product.

---

## 16. Technical definition of success

The engine should be able to answer, after any restart or incident:

1. What did we intend to do?
2. Which exact orders belong to us?
3. What did each venue authoritatively fill?
4. What canonical exposure remains?
5. What risk reservation is active?
6. What action is safe next?
7. What was the true net economic result?

If it cannot answer those seven questions, additional venues/UI features are premature.
