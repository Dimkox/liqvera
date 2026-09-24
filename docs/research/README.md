# Research index

Snapshot: **2026-08-18**

This directory is the strategic research entry point for Multi-Exchange Engine. It contains market, competitor, product-market-fit, architecture and source-evidence material. Research is intentionally separate from runtime documentation: a research claim is not proof that a runtime capability exists.

## Read in this order

1. [`user-needs/README.md`](user-needs/README.md) — **canonical market-demand and Jobs-to-Be-Done synthesis**: ranked pains, ICPs, product wedges, pricing, interview questions, sources, and go/kill criteria.
2. [`MASTER_RESEARCH.md`](MASTER_RESEARCH.md) — project history, strategic pivots, full conclusions, priorities, risks and decision log.
3. [`KakaoTalk / South Korea launch gate`](MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18) — current platform-policy, Korean regulatory, privacy, architecture, unresolved-evidence and launch decision.
4. [`PMF_CRITICAL_REVIEW.md`](PMF_CRITICAL_REVIEW.md) — adversarial review of whether this should be a product at all.
5. [`COMPETITIVE_CODE_INTELLIGENCE.md`](COMPETITIVE_CODE_INTELLIGENCE.md) — code/SDK/GitHub evidence on direct and infrastructure competitors.
6. [`TECHNICAL_STRATEGY.md`](TECHNICAL_STRATEGY.md) — surviving architecture thesis, execution invariants, build-vs-buy, kill gates and validation order.
7. [`SOURCE_LEDGER.md`](SOURCE_LEDGER.md) — source registry and confidence policy, including the dated Kakao/Korea primary-source set.
8. [`REPOSITORY_CONNECTIVITY_AUDIT.md`](REPOSITORY_CONNECTIVITY_AUDIT.md) — documentation graph, legacy/orphan policy and navigation rules.

## User-needs evidence

- [`user-needs/README.md`](user-needs/README.md) — maintained cross-forum synthesis. It consolidates production issue evidence, market hypotheses, buyer-evidence gaps, and the validation package for `MEE Evidence`, `MEE Observer`, and later `MEE Integrity`.
- [`user-needs/X_TWITTER_PAINS_INPUT_2026-08-10.md`](user-needs/X_TWITTER_PAINS_INPUT_2026-08-10.md) — complete owner-supplied X/Twitter pain map preserved as an **unvalidated discovery input**.
- [`user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md`](user-needs/TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md) — verified extraction from the supplied `mr.ponder` Teletype articles, checked against official Solana, Jupiter and Jito documentation.

The synthesis ranks authoritative reconciliation, partial-fill and residual-exposure handling, stale-stream detection, full-cycle executable economics, connector/API drift, incident replay, instrument equivalence, and fail-closed controls above generic UI or scanner work.

It does **not** prove willingness to pay for the complete product. Paid pilots, customer evidence, and roadmap approval remain required. The X/Twitter and other social notes remain hypothesis sources; they cannot override runtime code, tests, ADRs, `SECURITY.md`, or `docs/ROADMAP.md`.

## KakaoTalk and South Korea boundary

The dated [KakaoTalk / South Korea launch gate](MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18) is mandatory reading before any Korean localization, Kakao Developers app, KakaoTalk Channel, chatbot, Kakao Login, Korean campaign, exchange/referral link or Korean consumer onboarding work.

Current research decision:

- no Telegram-style trading mini-app assumption for KakaoTalk;
- no Kakao Developers integration for virtual-asset transactions, storage or deposits;
- no exchange account linking, private API keys, orders, custody, withdrawals, personalized signals, futures promotion or referral monetization through Kakao;
- the fastest defensible discovery surface is a standalone Korean mobile web/PWA limited to delayed public evidence and education;
- a KakaoTalk Channel may be evaluated only as support/education/status infrastructure after written Kakao classification and Korean legal review;
- Stage A remains public capture and read-only analysis only.

This is a fail-closed research gate. Missing written evidence means `NO_GO`, not implied permission.

## Required reading by task type

Any agent making one of the following decisions must start from [`user-needs/README.md`](user-needs/README.md):

- PMF and product packaging;
- ICP and buyer selection;
- pricing and paid-pilot design;
- landing pages and advertising claims;
- venue or connector priority;
- observer/reconciliation scope;
- execution-integrity requirements;
- consumer, prosumer, internal, or B2B product direction.

For South Korea or Kakao-related work, the agent must also read the [Kakao/Korea launch gate](MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18), then check the [source ledger](SOURCE_LEDGER.md), [roadmap](../ROADMAP.md), [accepted ADR](../adr/0001-python-universal-arbitrage-core.md), and [security policy](../../SECURITY.md) before changing implementation scope.

## Back to maintained implementation docs

- [Repository README](../../README.md) — implemented capabilities and explicit non-capabilities.
- [Master Plan pointer](../../MASTER_PLAN.md) — maintained planning entry point.
- [Documentation index](../README.md) — repository-wide documentation map.
- [Architecture](../architecture.md) — current implementation architecture.
- [Roadmap](../ROADMAP.md) — current implementation sequence and exit criteria.
- [Cleanup audit](../CLEANUP_AUDIT.md) — current safety findings and blockers.
- [Security](../../SECURITY.md) — secret handling and live-trading restrictions.

## Strategic conclusion

The original thesis — “another mobile/Telegram frontend for perp DEXs” — is not a durable differentiator. The surviving market hypothesis is narrower and harder:

> Build a safety-first cross-venue evidence and reconciliation core, prove executable economics in shadow mode, validate a read-only observer with paying technical users, and only then decide whether execution packaging is internal, prosumer, or B2B.

South Korea may still be a discovery segment, but KakaoTalk is not an authorization shortcut. A direct Kakao crypto trading surface is currently rejected; only a separately hosted, public/read-only Korean discovery surface is eligible for validation while written platform and legal clearances remain unresolved.

## Research-to-runtime rule

Runtime truth wins over research. If a document in this directory says a venue, feature or strategy is possible but current code/tests/ADRs say it is not implemented, it is **not implemented**.

Every research file should link back here and to the relevant maintained implementation document. Every maintained top-level entry point should link to the canonical user-needs synthesis so strategic evidence is discoverable by any repository-aware agent.
