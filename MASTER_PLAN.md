# Liqvera — planning entry point

Start with the [current Liqvera specification](docs/planning/LIQVERA_FACTORY_TZ.md) and [handoff](handoff.md). Liqvera is built for [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10). Links and research context from the Multi-Exchange Engine technical baseline are retained below.

[Repository README](README.md) · [Documentation index](docs/README.md) · [Research index](docs/research/README.md) · [Market demand and JTBD](docs/research/user-needs/README.md)

This file is a stable navigation entry point. It is not the full current plan and must not be used as evidence that a feature exists.

## Current sources of truth

- [`README.md`](README.md) — current repository status, active/transitional runtime boundary and explicit non-capabilities.
- [`docs/README.md`](docs/README.md) — maintained documentation map.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — active implementation sequence and exit criteria.
- [`docs/adr/0001-python-universal-arbitrage-core.md`](docs/adr/0001-python-universal-arbitrage-core.md) — accepted Python runtime direction.
- [`docs/research/user-needs/README.md`](docs/research/user-needs/README.md) — canonical market-demand and Jobs-to-Be-Done synthesis for pains, ICPs, packaging, pricing hypotheses, interviews and go/kill criteria.
- [`docs/research/README.md`](docs/research/README.md) — strategic research index.
- [`docs/research/MASTER_RESEARCH.md`](docs/research/MASTER_RESEARCH.md) — full project history, pivots, conclusions, validation plan and kill criteria.
- [`docs/research/PMF_CRITICAL_REVIEW.md`](docs/research/PMF_CRITICAL_REVIEW.md) — adversarial product-market-fit review.
- [`docs/research/COMPETITIVE_CODE_INTELLIGENCE.md`](docs/research/COMPETITIVE_CODE_INTELLIGENCE.md) — code-level competitor evidence.
- [`docs/research/TECHNICAL_STRATEGY.md`](docs/research/TECHNICAL_STRATEGY.md) — surviving execution/reconciliation thesis.
- [`docs/research/SOURCE_LEDGER.md`](docs/research/SOURCE_LEDGER.md) — source and confidence registry.
- [`docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md`](docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md) — dead-link, legacy and documentation-graph audit.
- [`docs/CLEANUP_AUDIT.md`](docs/CLEANUP_AUDIT.md) — implementation safety findings and remaining blockers.
- [`SECURITY.md`](SECURITY.md) — secret handling and live-trading restrictions.

## Inherited upstream strategy

The generic “multi-DEX mobile/Telegram terminal” thesis is rejected as insufficiently differentiated. The strongest current market hypothesis is an evidence and integrity sequence:

1. **MEE Evidence** — prove trustworthy public observations, exact instrument equivalence and reproducible shadow economics;
2. **MEE Observer** — validate a future self-hosted read-only local-versus-venue reconciliation surface with paying technical users;
3. **MEE Integrity** — only after P1/P2 implementation and explicit safety gates, converge private order state and bound residual exposure.

Only Stage A public capture and read-only analysis exists today. Packaging names and market findings do not authorize private APIs, order submission, customer capital, live paired execution or withdrawals.

The first external ICP hypotheses are small quant/prop teams and developers of trading products or venue connectors. They must be validated through real incident artifacts, installations, paid pilots or deposits—not praise, wait-list signups or generic interest.

## Planning use rule

Any change to PMF, product packaging, ICP, pricing, connector priority, observer/reconciliation scope or execution-facing claims must begin with [`docs/research/user-needs/README.md`](docs/research/user-needs/README.md), then pass the promotion rules in the roadmap and security policy. Research can change what should be built; it cannot claim that a capability exists or skip an ADR/release gate.

## Historical plan

The original 6 August 2026 planning document is preserved unchanged at [`docs/archive/legacy/MASTER_PLAN-v1.2.md`](docs/archive/legacy/MASTER_PLAN-v1.2.md).

It mixes research, future architecture, Solana-terminal scope and implementation claims. Those claims are historical and must not be treated as current product or runtime truth.

## Conflict rule

When documents disagree, runtime code/tests and accepted ADRs win. Research governs strategic intent; archived plans preserve history only.
