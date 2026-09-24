# Security

[Repository README](README.md) · [Roadmap](docs/ROADMAP.md) · [Architecture invariants](docs/architecture.md) · [Technical strategy](docs/research/TECHNICAL_STRATEGY.md) · [Repository audit](docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md)

## Secrets

Never commit wallet keys, API secrets, authentication tokens, seed phrases, or exported account sessions. Use agent/API wallets without withdrawal rights where the venue supports them. Rotate any credential exposed in chat, logs, terminal history, screenshots or Git history.

Run a full-history secret scan before enabling branch protection, sharing an archive or publishing any repository snapshot. Scanning only the current tree is insufficient.

Research collectors, competitor inventories and public-data services must not acquire runtime trading authority merely because they share a repository.

## Trading safety status

Live trading is not approved. The current adapters lack fully demonstrated restart-safe idempotency and complete source-of-truth reconciliation after uncertain network outcomes. A timeout must be treated as `UNKNOWN`, not as proof of rejection, until the venue is queried and private events are reconciled.

Required before live use:

- persistent client-order identity;
- verified private streams and REST/source-of-truth reconciliation;
- event deduplication and sequence handling;
- persisted two-leg state transitions;
- authoritative cumulative-fill accounting;
- residual exposure limits and emergency hedging;
- risk reservation and kill switch;
- venue precision, multiplier and minimum checks at the final boundary;
- restart, event-reordering and fault-injection tests;
- explicit operator arming and minimal-capital canary evidence.

## Credential boundary

Initial production design must fail closed:

- withdrawal permission is prohibited;
- separate subaccounts/API keys are preferred;
- CEX keys require IP restriction where supported;
- secrets are encrypted at rest and never logged;
- user/tenant scope is present in every credential and execution lookup;
- revocation is supported without deleting the audit trail;
- a research statement or partner program never changes credential permissions.

## Product and legal boundary

The repository does not promise risk-free yield or authorize distribution in a jurisdiction. Automated strategies, derivatives marketing, user-key custody and profit-share models require separate review.

Strategic and product-market-fit conclusions are maintained in [`docs/research/MASTER_RESEARCH.md`](docs/research/MASTER_RESEARCH.md) and [`docs/research/PMF_CRITICAL_REVIEW.md`](docs/research/PMF_CRITICAL_REVIEW.md). Runtime safety always overrides growth or monetization assumptions.
