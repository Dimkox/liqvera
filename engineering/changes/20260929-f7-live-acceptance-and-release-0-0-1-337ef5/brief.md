# F7 live acceptance and release 0.0.1

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f7-live-acceptance-and-release-0-0-1-337ef5`
Created: 2026-09-29T12:02:35+00:00
Risk: high
Complexity: high-risk
Domains: security, data

## Problem

Repair and complete Liqvera F7 acceptance, then perform a controlled live-public and Mezo Testnet demonstration and publish release 0.0.1. First repair the A01-A30 runner semantic validation, evidence immutability, exact final Git binding, local A30 classification, and deterministic local fault plan. Then execute all locally eligible acceptance cases on a clean commit; execute only approved public read probes and Mezo Testnet payment with test funds through the configured wallet/RPC/facilitator; keep mainnet, custody, exchange mutations, private market venues, real funds, and unrelated external writes forbidden. When required verification and independent reviews pass, update README and version metadata to 0.0.1, build release artifacts, push the authorized main branch and v0.0.1 tag to Dimkox/liqvera, and create GitHub Release v0.0.1 with truthful NOT_RUN/BLOCKED limitations.

## Outcome

Produce a trustworthy, immutable A01–A30 acceptance record bound to one exact
clean release commit, then—only through separately approved phases—perform
bounded public reads, at most one human-confirmed 0.01 test-MUSD submission,
construct Liqvera product release `0.0.1`, and publish the exact approved commit,
tag, checksummed assets, and truthful limitations.

## Scope

### In scope

- P0: semantic runner/evidence/final-Git-binding repair, local A30 split, and
  deterministic fault/mutation tests.
- P1: execute locally eligible acceptance cases out of tree on the reviewed
  clean candidate; missing real prerequisites remain `NOT_RUN`.
- P2: separately granted, exact-origin public reads only.
- P3: implement and independently review production authorization identity,
  finality, gateway/browser x402 wiring; then one separately granted Mezo
  Testnet payment envelope with human-held wallet, exact 0.01 test MUSD, one
  maximum submission, and an explicit numeric test-BTC gas cap.
- P4: root Liqvera `VERSION=0.0.1`, release manifest, deterministic artifacts,
  checksums, extraction/install checks, and truthful release notes; component
  package/API versions remain `0.1.0`.
- P5: separately granted fast-forward `main`, annotated `v0.0.1`, and GitHub
  Release publication/read-back for `Dimkox/liqvera` only.

### Out of scope

- Mainnet, real/user funds, custody, private keys/seeds, token approval,
  withdrawals, exchange/private-market mutation, trading, production deploy,
  unrelated repositories/settings/workflows, force push, mutable tags, or
  hidden retries.
- Component-version downgrade/migration from `0.1.0`.
- Treating `NOT_RUN`/`BLOCKED_EXTERNAL` as PASS or claiming F7 complete when
  the canonical result is incomplete.

## Constraints

- Backward compatibility: preserve inherited `mee-*` contracts and component
  `0.1.0`; root product release identity is separate.
- Data/privacy: never read or retain secret values; only sanitized public
  transaction identity may enter evidence.
- Performance: bounded attempts, timeouts, response sizes, evidence sizes, and
  one-payment submission budget.
- Operational: current decision is NO-GO. Each later phase requires prior green
  evidence and its own current, identity-bound human grant.
