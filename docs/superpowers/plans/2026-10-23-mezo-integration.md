# Mezo Testnet integration implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task. One application implementation owner; independent read-only review before completion.

**Goal:** Extend the existing paid market report with reproducible fixed-block Mezo DEX analytics, then add borrower risk reports and competition documentation.

**Architecture:** Keep the existing capture/report/gateway/web product and x402 payment boundary. Store raw fixed-block RPC observations and verified ABI provenance in bounded evidence; derive every numeric report field offline using integer/Fraction arithmetic. Existing reports remain verifiable.

**Tech Stack:** Existing Python packages, TypeScript gateway/browser, JSON Schema, PostgreSQL and GitHub Actions.

**Spec:** Owner's 2026-10-23 Mezo integration specification, alongside `docs/specification.md`.

## Global constraints

- Testnet 31611 only for all new chain interaction. No payment, grant, deployment or publication operations.
- Contract calls use one explicit captured block, never `latest`. Initial block discovery/header retrieval are metadata reads explicitly required by the specification.
- No invented addresses or ABI. Proxy ABI and implementation ABI are distinct provenance records.
- Preserve payment state, SQL migration bytes, published assets and historical sealed evidence.
- Integer/Fraction arithmetic must reproduce the verified contract's operation order, including fee rounding.
- Hash integrity and RPC-result consistency are not independent chain authentication. Do not claim offline proof of canonical chain inclusion.
- Keep optional Getzilla external; use checkout `e86027f5962401b62a750f4a0d804029b52ae397` without installing framework policy into Liqvera.

## Review focus

- Hostile duplicate/malformed call records, mismatched block/address/calldata and understated fee must fail closed.
- Exact-out buy must use the minimum input satisfying the contract's integer exact-input quote; test adjacent inputs.
- Offline archive verification cannot establish authenticity if an attacker rewrites every hash; retain independently trusted report digest support.
- Trove redemption ordering is not automatically liquidation ordering; confirm list direction, eligibility and protocol-specific semantics.
- Legacy bundles must rebuild byte-identically; unavailable live Mezo reads must never use synthetic fallback.

## Task 0: Protocol provenance

- [ ] Download Pool, Router, PoolFactory, TroveManager, SortedTroves and PriceFeed verified ABI; distinguish proxy implementations.
- [ ] Record retrieval URLs, UTC timestamps and SHA-256 without modifying historical MUSD provenance.
- [ ] Validate required signatures, sources, Testnet addresses and fixed-block fee/token decimals.
- [ ] Add offline provenance checks and documentation; independent review; commit with handoff.

## Task 1: DEX capture, arithmetic and evidence

- [ ] Add failing integer AMM vectors for fee truncation, minimal exact-out, zero reserves and insufficient liquidity.
- [ ] Implement bounded fixed-block adapter with injectable transport and raw calls/header capture; reject inconsistent responses.
- [ ] Extend optional report and ZIP members, strict schemas and offline reconstruction together; test tampering with and without recomputed hashes.
- [ ] Record real Testnet golden observations; compare router/pool quotes at the same block.
- [ ] Extend gateway presenter and browser comparison with legacy fallback and explicit caveats.
- [ ] Verify Python/Node/artifact checks, obtain independent read-only review, update handoff and commit.

## Task 2: Judge verification materials

- [ ] Add sourced Testnet contract and historical payment links immediately below README hero.
- [ ] Document exact installed offline-verifier command, payment flow and limitations; distinguish implemented/deployed status.
- [ ] Verify Akindo deadline, existing transaction metadata, docs links/address pins and update competition deck/script.
- [ ] Fresh wallet purchases require a human signer and are never simulated as paid acceptance.

## Task 3: Trove analytics

- [ ] Verify implementation ABI, MCR/CCR, pricing and redemption semantics from pinned source and fixed-block calls.
- [ ] Test exact risk formulas, inactive cases, traversal limits and hostile neighbor changes before implementation.
- [ ] Add capture/evidence/recalculation, schema product, address validation, gateway routing and browser tab.
- [ ] Measure real read-only build latency and ICR agreement; preserve payment guards; independent review and commit.

## Task 5: Regression and acceptance

- [ ] Inventory existing payment negatives and CI before adding missing coverage; avoid duplicate workflows.
- [ ] Add one offline product-test command and A31/A32 evidence-backed acceptance cases.
- [ ] Run full checks including disposable PostgreSQL; record exact counts and hosted CI separately.
- [ ] Generate new immutable demo assets with pinned hashes; preserve every historical artifact.

## Optional registry

Deferred until Tasks 1–3 pass. Contract deployment and anchor transactions need separately scoped authorization and signer access.
