# Repository Cleanup Audit

[Repository README](../README.md) · [Roadmap](ROADMAP.md) · [Security](../SECURITY.md) · [Research index](research/README.md) · [Connectivity audit](research/REPOSITORY_CONNECTIVITY_AUDIT.md)

Audit date: 2026-08-06  
Audited baseline: `main` at `442944789a9b515d8e2ec96776b0d79b36257f83`

This file records the implementation cleanup at that baseline. The later documentation/dead-entity pass is recorded separately in [`research/REPOSITORY_CONNECTIVITY_AUDIT.md`](research/REPOSITORY_CONNECTIVITY_AUDIT.md).

## Critical findings addressed by this baseline

1. **Quantity rounding could increase exposure.** `InstrumentRegistry.to_venue_qty()` claimed to floor but used the default `Decimal.quantize()` mode. Halfway values could round up. The cleanup uses `ROUND_DOWN`, honors explicit venue step sizes, and rejects positive quantities that collapse below one step.
2. **Scanner fabricated executable depth.** When VWAP was unavailable, the edge calculator substituted the best bid or ask. Large notionals could therefore appear executable using one top-of-book level. The cleanup requires complete VWAP depth on both legs.
3. **Funding periods were mixed directly into edge.** Raw rates from different venue periods and settlement conventions were subtracted without normalization. Funding remains observable but is excluded from `net_edge_bps` until normalized.
4. **Stale and crossed books were not rejected by the scanner.** The cleanup requires a timezone-aware timestamp, a configurable freshness limit, non-empty sides, and a non-crossed spread.
5. **Order requests accepted invalid live inputs.** Shared contracts now reject non-positive or non-finite quantities and prices, limit orders without prices, and incompatible post-only combinations.
6. **Unit tests depended on live venues.** Hyperliquid and Bybit smoke calls, and Lighter metadata initialization, were mixed into `tests/unit`. Live tests are now explicit opt-in integration tests.
7. **Broken duplicate Hyperliquid implementation.** `adapters/hyperliquid/adapter.py` imported constants that do not exist and was not exported. It is removed.
8. **Speculative private-stream code was exported as production API.** The Lighter experiment used unverified message assumptions and was not wired to reconciliation. It is moved to `experiments/` and removed from package exports.
9. **Documentation contained competing products and duplicate plans.** The duplicate master plan is removed, Solana-terminal documents are archived, and the README states actual implementation status.

## Live-trading blockers not solved by this cleanup

Until all items below are complete, live trading must remain disabled:

- persistent client-order identity across process restarts;
- deterministic venue-native idempotency keys;
- `UNKNOWN` handling for timeout-after-accept scenarios;
- source-of-truth lookup for orders, fills, open orders, and positions;
- authenticated private streams verified against current official schemas;
- deduplication and sequence handling for private events;
- persisted transition graph for two-leg execution;
- preflight risk reservation, residual exposure limits, emergency hedge, and kill switch;
- venue precision, multiplier, tick, step, minimum quantity, and minimum notional enforcement at the final order boundary;
- restart recovery and fault-injection tests;
- account-specific fee tiers and normalized funding intervals;
- full-history secret scanning and branch-protection rules.

## Verification baseline

The cleanup adds deterministic regression tests for round-down quantity conversion, step-size enforcement, invalid order requests, complete-depth VWAP, no top-of-book fallback, exclusion of unnormalized funding, stale and crossed books, and no-network dry-run adapter paths.

CI runs only deterministic unit tests. Live smoke tests require `RUN_LIVE_TESTS=1`.

## Strategic boundary added later

The cleanup baseline does not establish product-market fit. Current product and economic falsification gates are maintained in:

- [`research/PMF_CRITICAL_REVIEW.md`](research/PMF_CRITICAL_REVIEW.md);
- [`research/MASTER_RESEARCH.md`](research/MASTER_RESEARCH.md);
- [`ROADMAP.md`](ROADMAP.md).
