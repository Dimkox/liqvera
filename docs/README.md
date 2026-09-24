# Liqvera — documentation

## Product and buildathon

**Market reports you can verify.**

Built for [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

This standalone repository was prepared from a technical snapshot. Start with the [specification](planning/LIQVERA_FACTORY_TZ.md), [current handoff](../handoff.md), and [PROVENANCE](../PROVENANCE.md). The remaining sections of this index describe the inherited technical baseline; they do not establish that the Mezo API or payments are implemented.

[Repository README](../README.md) · [Master Plan pointer](../MASTER_PLAN.md) · [Security](../SECURITY.md) · [Research index](research/README.md) · [Market demand and JTBD](research/user-needs/README.md) · [Kakao/Korea launch gate](research/MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18)

This is the maintained navigation entry point for `docs/`. Documents are grouped by authority and purpose so historical plans are not mistaken for current runtime truth.

## Current implementation truth

- [`ROADMAP.md`](ROADMAP.md) — active implementation sequence, PMF gate and exit criteria.
- [`adr/0001-python-universal-arbitrage-core.md`](adr/0001-python-universal-arbitrage-core.md) — accepted Python runtime direction.
- [`architecture.md`](architecture.md) — retained Go-foundation invariants and active architecture boundary.
- [`CLEANUP_AUDIT.md`](CLEANUP_AUDIT.md) — implementation cleanup baseline and live-trading blockers.
- [`../SECURITY.md`](../SECURITY.md) — credential, execution and legal safety boundary.

## Strategic research

- [`research/README.md`](research/README.md) — research navigation.
- [`research/MASTER_RESEARCH.md`](research/MASTER_RESEARCH.md) — complete project history, pivots, conclusions and validation plan.
- [`KakaoTalk / South Korea launch gate`](research/MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18) — dated platform/compliance architecture decision, unresolved-evidence register and launch checklist.
- [`research/PMF_CRITICAL_REVIEW.md`](research/PMF_CRITICAL_REVIEW.md) — adversarial product-market-fit review.
- [`research/COMPETITIVE_CODE_INTELLIGENCE.md`](research/COMPETITIVE_CODE_INTELLIGENCE.md) — competitor code/SDK evidence.
- [`research/TECHNICAL_STRATEGY.md`](research/TECHNICAL_STRATEGY.md) — surviving execution/reconciliation thesis.
- [`research/SOURCE_LEDGER.md`](research/SOURCE_LEDGER.md) — source and confidence registry, including the Kakao/Korea primary-source set.
- [`research/REPOSITORY_CONNECTIVITY_AUDIT.md`](research/REPOSITORY_CONNECTIVITY_AUDIT.md) — documentation graph and dead-entity classification.

### User-needs and practitioner evidence

- [`research/user-needs/README.md`](research/user-needs/README.md) — **canonical market-demand and Jobs-to-Be-Done synthesis**, including ranked pains, ICPs, product wedges, pricing hypotheses, interview questions, sources, and go/kill criteria.
- [`research/user-needs/X_TWITTER_PAINS_INPUT_2026-08-10.md`](research/user-needs/X_TWITTER_PAINS_INPUT_2026-08-10.md) — complete owner-supplied X/Twitter discovery note; **not validated product evidence** until cross-checked against original posts and independent forums.
- [`research/user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md`](research/user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md) — verified extraction from supplied Solana-arbitrage articles, including smart-contract boundaries, primary-source checks and roadmap decisions.

Any agent changing PMF, packaging, ICP, pricing, connector priority, observer scope, reconciliation scope, product-facing claims, South Korea targeting, Kakao distribution, Korean localization, affiliate/referral behavior or consumer onboarding must read the canonical synthesis and the Kakao/Korea launch gate together with `ROADMAP.md`, `SECURITY.md`, and the accepted ADR. Research is not proof of implementation or legal clearance.

## Deployment and validation

- [`deployment.md`](deployment.md) — retained deployment notes; verify runtime scope before use.
- [`validation.md`](validation.md) — verification evidence and iteration log.
- [`a2-deployment.md`](a2-deployment.md) — A2 public-data collector packaging/deployment boundary.
- [`a2-mapping-review.md`](a2-mapping-review.md) — A2 mapping review.
- [`n8n-stage-a.md`](n8n-stage-a.md) — Stage-A automation notes; not live-trading authority.
- [`five-day-stage-a-spec.md`](five-day-stage-a-spec.md) — historical/working Stage-A specification; compare with current ADR and roadmap before use.

## Handoff and recovery

- [`agent-handoff.md`](agent-handoff.md) — detailed agent/project handoff record.
- [`HISTORY_RECOVERY.md`](HISTORY_RECOVERY.md) — history recovery notes.
- [`planning/`](planning/) — planning artifacts; each file must be interpreted against current roadmap/ADR.

## Compatibility and archive pointers

- [`SOLANA_TERMINAL_TODO.md`](SOLANA_TERMINAL_TODO.md) — compatibility pointer to the archived Solana backlog.
- [`archive/`](archive/) — historical plans and superseded product scopes.

Archive material is preserved for provenance. It is not current product truth.

## Tooling and contributor material

Repository-level `.agents/`, `_bmad/` and related files support contributor/agent workflows. They are not runtime features and are governed separately from product code.

## Truth hierarchy

1. code and tests;
2. accepted ADRs;
3. security restrictions;
4. roadmap;
5. root README and this index;
6. strategic research;
7. archive/history.

When a document lacks a navigation header or its status is unclear, return here and consult the accepted ADR plus the connectivity audit before acting on it.
