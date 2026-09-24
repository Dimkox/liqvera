# Product Charter — Private Solana Intelligence & Execution Terminal

**Version:** 1.0  
**Date:** 2026-08-06  
**Status:** Frozen (G0)  
**Owner:** single private operator (no multi-tenant SaaS in MVP)

---

## 1. Mission

Build a **private**, policy-constrained terminal that:

1. Ingests Solana mainnet events near real-time.
2. Decodes Pump.fun / PumpSwap, Raydium, Meteora, Orca, Jupiter routes and standard SPL / Token-2022 operations.
3. Reconstructs human-readable actions: buy, sell, transfer, open/close position, pool migration, liquidity change.
4. Builds **Wallet DNA**, PnL, behavioral classification and **Copy Score**.
5. Hard-separates reproducible low-frequency trading from HFT, arbitrage, market making, LP and suspicious synthetic activity.
6. Forces the path **Observe → Shadow → Paper → Live** before any signed transaction.
7. Executes only through `quote → simulation → risk decision → sign → submit → reconcile`.
8. Isolates manual positions, copy strategies, research and future cross-venue strategies into independent portfolios.
9. Explains every latency stage and every accept / skip / block decision.
10. Keeps private keys **outside** the database, `.env`, logs and UI.

## 2. Product layers

```text
On-chain Intelligence
        ↓
Strategy Classification & Copyability
        ↓
Shadow / Paper Verification
        ↓
Policy-constrained Execution
```

Competitive edge is **not** “more volume tools”. It is:

1. Saying **“this cannot be copied safely”**.
2. Showing achievable **follower** PnL, not leader screenshots.
3. Separating capital and lots per strategy.
4. Explaining risk / score / latency **before** trade.
5. Physically isolating the signer from analytics and UI.

## 3. Modes of admission

| Mode   | Sign | Submit | Money risk | Purpose                |
|--------|------|--------|------------|------------------------|
| Observe| no   | no     | none       | collect & analyse      |
| Shadow | no   | no     | none       | compute reaction only  |
| Paper  | no   | no     | virtual    | portfolio & rules      |
| Live   | yes  | yes    | real       | after all gates G0–G6  |

Promotion is one-way until gates pass; demotion is always allowed. Critical health/risk events force `PAUSED` without auto-closing positions unless an explicit emergency rule is set.

## 4. MVP in scope

- Solana mainnet **read-only** ingest.
- History + live for selected tokens, pools, wallets.
- Normalized swaps and positions.
- Token page: price, liquidity, volume, holders, creator/funder graph, risk flags.
- Wallet page: realized/unrealized PnL, win rate, expectancy, drawdown, timeline, Wallet DNA.
- Classification + hard `NON_COPYABLE` for HFT / arb / opaque routes.
- Copy Score with component explanations.
- Shadow Mode and event-time replay.
- Paper portfolio.
- Live **spot** swaps for **one** own portfolio after gates.
- Jupiter Swap V2 primary; Raydium direct as research/fallback.
- TP/SL, partial exit, trailing, time stop, liquidity stop.
- Private Web UI behind Tailscale/WireGuard.
- Notifications without signing capability.

## 5. Explicit non-goals (MVP)

The product must **not** implement or encourage:

- synthetic / wash volume;
- fake “human-like” activity;
- artificial holder inflation;
- profile farming / mass profile creation;
- hidden supply distribution across linked wallets;
- coordinated token launch + subwallet accumulation;
- clone-token workflows;
- coordinated mass-dump tooling;
- bypassing wallet connectivity graphs;
- custody of third-party funds;
- public multi-tenant SaaS / billing.

Defensive **detectors** of the above patterns are in scope. Historical replay and management of **own** portfolios are in scope.

## 6. Critical trust boundaries

| Component   | May read keys | May sign | May submit | May create OrderIntent |
|-------------|---------------|----------|------------|------------------------|
| ingest      | no            | no       | no         | no                     |
| analytics   | no            | no       | no         | no                     |
| strategy    | no            | no       | no         | **yes**                |
| risk        | no            | no       | no         | approve/reject only    |
| execution   | no            | no       | builds/sim | no                     |
| **signer**  | **yes**       | **yes**  | no (returns signed payload) | no |
| reconciler  | no            | no       | no         | no                     |
| UI          | no            | no       | no         | no (requests only)     |

Signer is the **only** process allowed to access key material. It signs only allowlisted serialized payloads under policy.

## 7. Architecture choice (MVP)

**Modular monolith** (not microservices):

- one Rust workspace;
- one backend process with internal module boundaries;
- separate **signer** process;
- separate frontend;
- PostgreSQL + TimescaleDB;
- Redis for cache / locks / short queues;
- Docker Compose on existing Ubuntu host;
- NATS / ClickHouse only after proven load.

## 8. Cross-venue (later, Wave F)

After Solana G7 only: Hyperliquid, Lighter, Variational, selected CEX via canonical venue interfaces. Native atomic arbitrage is a **separate** contour — never “copy arb”.

## 9. Success criterion for first release

The terminal covers the useful operational surface of DogWifTools / GMGN-class tools, but makes it **reproducible, measurable, and gate-enforced**, and is ready to attach Hyperliquid / Lighter / Variational / CEX later without rewriting the risk/execution core.

## 10. References

Full executable backlog: `TODO.md` / `docs/TODO.md` (2026-08-06).  
Gates: G0–G9 in TODO §12.  
First 20 atomic commits: TODO §14.
