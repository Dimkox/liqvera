# ADR 0001 — Scope, Non-Goals and Trust Boundaries

**Status:** Accepted  
**Date:** 2026-08-06  
**Deciders:** product owner (private operator)  
**Related:** `docs/product-charter.md`, `TODO.md`

---

## Context

We need a private Solana intelligence and execution terminal. Competitive products (DogWifTools, GMGN-style tools) mix useful operational primitives with dangerous patterns (keys in config, volume gaming, one-click Live). Research and operator experience show that:

- HFT and multi-hop arb wallets are not copyable post-factum.
- Leader PnL ≠ follower PnL under realistic latency and fees.
- Manual and bot lots must not share one accounting contour.
- Simple “safety checkmarks” miss LP control, funder graphs and synthetic activity.

Without a frozen scope, implementation drifts into volume tools, public SaaS or premature Live.

## Decision

1. **Product type:** private single-operator terminal, not SaaS.
2. **Mode ladder is mandatory:** Observe → Shadow → Paper → Live. No Live without G0–G6.
3. **Signer isolation is absolute:** only the signer process may hold or use private keys; analytics, UI, ingest, strategy and risk never see key material.
4. **Non-goals are hard:** wash volume, holder farming, clone-token flows, coordinated dump tooling, third-party custody and multi-tenancy are out of MVP and must not appear as features.
5. **Architecture:** modular monolith (Rust workspace) + separate signer binary + private Web UI behind VPN.
6. **Copyability is a first-class product output:** the system must be able to refuse Live with explicit `NON_COPYABLE` reasons.
7. **Cross-venue (HL / Lighter / Variational / CEX)** is Wave F only, after Solana G7; native arb is a separate contour, not “copy arb”.

## Module ownership (forbidden dependencies)

| Module              | Owns data                         | Must not depend on        |
|---------------------|-----------------------------------|---------------------------|
| `ingest`            | raw slots/tx/notifications        | signer, execution, UI     |
| `decode-*`          | normalized swaps/actions          | signer, risk, UI          |
| `token-intelligence`| token risk features/scores        | signer, execution         |
| `wallet-intelligence`| DNA, PnL, features               | signer, execution         |
| `strategy-classifier`| class, NON_COPYABLE, Copy Score  | signer                    |
| `replay` / Shadow   | shadow runs/orders                | signer                    |
| `portfolio`         | lots, positions, allocations      | signer (reads reports only)|
| `risk-engine`       | RiskDecision                      | signer implementation     |
| `execution`         | OrderIntent → sim → submit path   | direct key access         |
| `signer`            | keys, signatures only             | DB business logic, UI     |
| `reconciler`        | final position truth              | signing                   |
| `web` / API         | presentation                      | keys, raw signing         |

Dependency rule enforced in CI: crates that must not link `signer` or key-handling code will fail the architecture test once workspace crates exist (P0-002).

## Consequences

### Positive

- Clear gate path before real money.
- Reduced blast radius if backend or UI is compromised.
- Honest product messaging (follower vs leader).
- Room to add venues later without rewriting risk core.

### Negative / costs

- Slower path to first Live trade (by design).
- Separate signer process and policy surface to maintain.
- More UI friction (two-step Live, Shadow required).

### Rejected alternatives

| Alternative                         | Why rejected                                      |
|-------------------------------------|---------------------------------------------------|
| Keys in config.json / .env for app  | DogWifTools anti-pattern; high leak risk          |
| One-click Live from wallet page     | Bypasses Shadow/Paper evidence                    |
| Microservices from day one          | Unnecessary ops load for single operator MVP      |
| Public multi-tenant copy marketplace| Out of scope; custody and abuse surface           |
| “Copy” HFT/arb wallets              | Not reproducible; false expectancy                |

## Compliance with TODO gates

This ADR satisfies **G0** items:

- [x] Product charter approved (`docs/product-charter.md`)
- [x] Non-goals fixed
- [x] Signer boundary approved
- [ ] Data contracts versioned — follows in domain crate (P0-002 / contracts in TODO §5)

## References

- TODO.md §1 (scope), §2 (modes), §3 (architecture), §12 (gates)
- Competitive notes: DogWifTools, GMGN (neutral primitives only)
- Prior cross-exchange research (Hyperliquid/Lighter) deferred to Wave F / XVN-*
