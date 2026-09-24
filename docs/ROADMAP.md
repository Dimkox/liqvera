# Liqvera — roadmap

The current Liqvera buildathon plan is in the [specification, phases F0–F7](planning/LIQVERA_FACTORY_TZ.md). F0 is complete; F1 baseline verification is next. The upstream Multi-Exchange Engine technical roadmap is retained below; the former MEE names refer to inherited research directions.

[Repository README](../README.md) · [Master Plan pointer](../MASTER_PLAN.md) · [Accepted Python ADR](adr/0001-python-universal-arbitrage-core.md) · [Master research](research/MASTER_RESEARCH.md) · [Critical PMF review](research/PMF_CRITICAL_REVIEW.md) · [Canonical market demand and JTBD](research/user-needs/README.md)

This roadmap defines implementation gates. It does not assume that the project has broad product-market fit. The generic consumer terminal thesis remains unproven; technical work must first falsify the economic, buyer-demand and safety assumptions.

The canonical [`research/user-needs/README.md`](research/user-needs/README.md) ranks market pains and packaging hypotheses. It is a discovery input, not implementation authority: no pain, ICP, product name, pricing hypothesis or competitor incident becomes a runtime requirement without passing the promotion rule, security review and explicit roadmap or ADR approval.

## P-1 — product and economic falsification

- use the canonical market-demand synthesis as the starting hypothesis map, not as proof of PMF;
- test small quant/prop teams and trading-product/connector developers as the first external ICPs;
- keep internal proprietary validation distinct from external willingness to pay;
- validate **MEE Evidence** first with public/read-only evidence packages and paid or deposit-backed pilots;
- validate a future **MEE Observer** only as a self-hosted read-only local-versus-venue reconciliation surface before any order submission scope;
- treat **MEE Integrity** as later packaging for P1/P2 capabilities, not as an implemented Stage A feature;
- conduct customer-discovery interviews around past incidents and real artifacts rather than pitching a generic terminal;
- require logs, order exports, installations, deposits, paid pilots, capital allocation or removal of an existing component as commitment evidence;
- run landing/onboarding tests before consumer UI development;
- define conservative revenue, acquisition, support, security and retained-usage assumptions;
- record explicit go and kill criteria;
- reject praise, likes, wait-list signups and hypothetical intent as sufficient demand evidence.

P-1 target evidence:

- at least 15 qualified interviews;
- at least 8 teams provide real or sanitized incident artifacts;
- at least 5 complete an evidence pilot or install a read-only observer;
- at least 3 pay or place a meaningful deposit;
- at least 2 renew or continue after the first cycle;
- a repeated failure or evidence class is demonstrated across at least two venues;
- the result changes a customer decision, reduces incident-analysis time or replaces an existing workflow.

Exit condition: either a measurable proprietary-economics or paying-buyer wedge exists, or the repository remains an internal research/execution project. Curiosity without commitment is a failed external-product result.

## P0 — trustworthy read-only baseline

P0 is the implementation foundation for the `MEE Evidence` hypothesis. The packaging name does not expand the Stage A capability boundary.

- deterministic CI;
- current venue metadata and order books;
- canonical economic instrument and quantity mapping;
- authoritative contract-multiplier evidence, including `kSHIB` before any cross-venue use;
- freshness, sequence and crossed-book rejection;
- full-depth executable VWAP;
- normalized fee and funding-period model;
- durable raw observations and scanner metrics;
- reproducible preflight/simulation evidence where a venue or chain exposes it;
- opportunity decay at realistic processing/venue latency;
- full entry, exit, partner/builder-fee and rebalance-cost accounting;
- failed-attempt economics, including paid fees, retries, opportunity decay and infrastructure allocation rather than successful-path accounting only;
- machine-readable `PASS`, `REJECT` or `UNCERTAIN` verdicts with stable reason codes;
- a human-readable evidence report that traces each conclusion to sealed inputs without claiming live execution.

Exit condition: a recorded opportunity can be reproduced from stored inputs, missing or stale data produces no signal, and the observed edge survives conservative executable-cost assumptions including failed attempts. At least one target user must use the evidence to make a real strategy, threshold, capital or connector decision before treating the report as a product wedge.

## P1 — single-venue execution safety

P1 is the earliest technical boundary that could support future `MEE Observer` private-state validation and later integrity controls. It does not authorize order placement merely because reconciliation contracts exist.

- persistent client-order IDs;
- venue-native idempotency mapping;
- `PENDING` / `UNKNOWN` submission semantics;
- private order and fill events;
- REST/source-of-truth reconciliation;
- restart recovery;
- venue precision and minimum validation;
- deterministic dry-run and testnet fault injection;
- late-fill, duplicate-event and failure-before-fill scenarios;
- submission-to-acknowledgement and acknowledgement-to-authoritative-state evidence;
- paid failure-cost attribution where the venue charges for rejected or failed execution;
- read-only divergence reporting before mutation authority;
- no automatic withdrawal permission.

Exit condition: a timeout, event reordering or restart cannot cause an unobserved duplicate order, and every ambiguous state converges to authoritative evidence or explicit manual intervention. Any external observer pilot must remain read-only until a separate release decision arms mutation capability.

## P2 — paired execution and risk

P2 is the technical basis for the future `MEE Integrity` hypothesis. The name must not be used to imply production readiness before these gates pass.

- persisted two-leg state graph;
- risk reservation before the first leg;
- bounded residual exposure;
- authoritative cumulative-fill accounting;
- emergency hedge and kill switch;
- account/venue health gates;
- reconciliation loop and manual-intervention state;
- audit log and operator controls;
- realized net P&L including both entries, exits, fees, funding and hedge cost;
- minimal-capital manual canary before automation.

Exit condition: every partial fill and uncertain outcome converges to a known persisted state or explicit manual intervention, and live canary results remain within the modeled risk/slippage envelope. Product packaging remains conditional on paid demand and legal/security review.

## P3 — additional venues and product surface

Add Bybit live reconciliation, then other CEX/DEX venues one at a time. Variational execution requires official API access and reviewed terms. No adapter is declared complete until it passes the same P1 contract and fault suite.

Possible product surfaces are conditional and evidence-ranked:

- internal proprietary strategy;
- self-hosted `MEE Evidence` tooling;
- self-hosted read-only `MEE Observer`;
- B2B execution/reconciliation API after P1/P2 proof;
- technically capable prosumer packaging after support economics are measured;
- Korean closed beta only after legal and paid-demand evidence;
- Telegram as a distribution or alert surface, not the core product.

A generic consumer terminal, generic funding scanner, “AI trading bot,” guaranteed-return product and mass-market Telegram Mini App are not active requirements.

A Solana atomic executor or custom CPI program is **not** an active requirement. It may enter as an isolated research lane only after:

- P0 evidence and economics are stable;
- a measured routing/execution gap exists versus Jupiter or other maintained infrastructure;
- all legs are composable inside the same Solana execution domain;
- a separate ADR, program-provenance policy and security review are approved;
- the experiment does not claim atomicity for CEX, Hyperliquid, Lighter or other independently sequenced legs.

Own-validator deployment, flash-loan automation, automatic withdrawals, capital rebalancing and a general liquidity aggregator are excluded until separate economic, security and legal evidence exists.

Exit condition: a product surface or chain-specific executor is built only for a workflow with measured usage, willingness to pay or proprietary economic value.

## Global stop conditions

Pause, narrow or repurpose the project if:

- shadow edge disappears after realistic costs and latency;
- executable capacity is economically immaterial;
- order-state convergence cannot be made safe;
- customer tests produce curiosity but no incident artifacts, installation, payment, account connection or capital allocation;
- evidence reports do not change decisions or replace an existing workflow;
- teams regard direct SDK and in-house reconciliation maintenance as immaterial;
- conservative customer acquisition, support and private-integration cost exceeds retained gross revenue;
- the required custody/legal model exceeds the accepted risk boundary;
- the only demand comes from users expecting guaranteed returns;
- the best version is an internal proprietary research system, in which case optimize for internal truth instead of inventing consumer PMF.

Full reasoning:

- [`research/user-needs/README.md`](research/user-needs/README.md)
- [`research/MASTER_RESEARCH.md`](research/MASTER_RESEARCH.md)
- [`research/PMF_CRITICAL_REVIEW.md`](research/PMF_CRITICAL_REVIEW.md)
- [`research/user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md`](research/user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md)
