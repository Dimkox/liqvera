# ADR-0001: Python universal arbitrage core

Date: 2026-07-26
Status: accepted

## Context

The repository contains a Go Stage 0 foundation and a Go-oriented Stage A
plan. The owner has explicitly rejected Go for this project and clarified that
the product is a cross-exchange arbitrage engine:

- Hyperliquid and Lighter are the first venue pair;
- further DEX and CEX venues connect through API adapters;
- the traded asset is selected from verified common markets;
- DOGE, PUMP, PEPE, or any other symbol must not define the core architecture.

Ticker equality cannot establish that two derivatives are hedge-equivalent.
Contract multiplier, quote and settlement assets, product and payoff kind, and
authoritative equivalence evidence must be explicit.

## Decision

The active engine runtime is implemented as a Python modular monolith.

The core is split by capability:

- venue-neutral market and contract identity;
- public market-data adapters;
- account and reconciliation adapters;
- trading adapters;
- RFQ adapters;
- opportunity evaluation;
- risk reservation;
- paired execution saga;
- immutable evidence and audit persistence;
- read-only API and later Telegram projection.

Market discovery is dynamic. A market enters the common universe only when at
least two distinct venues expose the same normalized economic identity and
each mapping has explicit equivalence evidence.

Shadow public-data evaluation remains the first execution gate. This ADR does
not authorize exchange mutations, live orders, credential use, or capital use.

## Migration boundary

Existing Go code remains historical reference until Python equivalents pass
their tests. Reusable invariants include exact decimal arithmetic, exact order
ownership, reconciliation before retry, durable event evidence, and
fail-closed unknown states. Venue-specific and asset-specific assumptions are
not ported.

Removal of superseded Go runtime files is a separate reviewed commit after
Python parity exists.
