# Liqvera F3–F7 Code Completion Plan

> **For agentic workers:** Implement independent slices in isolated worktrees and integrate through one owner. The owner explicitly deferred execution, tests, reviews, and defect repair; this phase completes code and configuration surfaces only.

**Goal:** Materialize every remaining canonical Liqvera component from live evidence construction through testnet payment delivery, production UI, operations, acceptance tooling, and factory bindings.

**Architecture:** Python owns capture, exact analytics, immutable evidence, verification, and internal report services. A TypeScript/Express gateway owns the public F2 API, PostgreSQL ledger, and official x402 boundary. A separate TypeScript browser app owns wallet interaction, while isolated Compose and acceptance tooling provide the deployable and auditable shell.

**Tech Stack:** Python 3.12, TypeScript 5, Express, PostgreSQL, official `@x402/*` 2.16.0 packages, HTML/CSS, Vite, Docker Compose, Caddy.

**Spec:** `docs/planning/LIQVERA_FACTORY_TZ.md`, ADR-0002, and the frozen F2 schemas under `schemas/mezo-evidence/v1/`.

## Global Constraints

- Keep all project artifacts and product copy in English.
- Preserve shadow-only/read-only exchange behavior and `execution_authority=NONE`.
- Authorize only Mezo Testnet chain `31611`, CAIP-2 `eip155:31611`, MUSD `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`, 18 decimals, and price `10000000000000000` atomic units.
- Mainnet, exchange writes, merchant private keys, custody, refunds, and fabricated receipts remain forbidden.
- Payment readiness stays false until `PAY_TO`, canonical authorization identity, facilitator compatibility, and a reviewed finality policy are all present.
- No fixture or `SIMULATED` report may produce a canonical chargeable quote.
- Preserve exact decimal strings and integer atomic units; never route monetary values through JavaScript `Number` or Python `float`.
- Do not log capabilities, payment signatures, cookies, database secrets, or raw authorization payloads.
- Unknown settlement means `PAYMENT_UNCERTAIN`; never resubmit or offer a second payment.
- This phase creates code only. Do not run test suites, live captures, facilitator calls, RPC writes, payments, containers, acceptance, deployment, release, or push.

## Task 0: Pin the official Mezo protocol sources

**Owns:** `packages/mezo-protocol/**`.

Vendor the integration-relevant official material from `mezo-org/musd` and
record the exact `mezo-org/mezod` and `mezo-org/documentation` revisions. The
package must include upstream provenance and GPL-3.0 notice, the exact Matsnet
MUSD deployment artifact/ABI, a small typed read-only export for chain/network,
token, event and EIP-2612 metadata, and a machine-readable source lock. Pin:

- `mezo-org/musd` commit `aa25fd6defbe6c1385940e183ea7a0a3df4533d8`;
- `mezo-org/mezod` commit `a5b390c80408b23f7579ffef0e0a1f5c336ad624`;
- `mezo-org/documentation` commit `222891407f85e419b4c6c323f8392f08887d0f8a`.

The gateway and browser packages consume this local protocol package instead
of duplicating the MUSD address, decimals, Transfer topic, or permit metadata.
Do not import minting, borrowing, liquidation, or administrative behavior into
Liqvera; payment integration is limited to read-only metadata and user-signed
MUSD transfer authorization through the official x402 SDK.

## Task 1: Canonical F3 capture, report, bundle, verifier, and services

**Owns:**

- F3 schemas under `schemas/mezo-evidence/v1/`
- `packages/public-capture/src/mee_public_capture/evidence_*.py` and packaging entrypoints
- canonical additions under `packages/evidence-report/src/mee_evidence_report/`
- package resources/entrypoints in `packages/evidence-report/pyproject.toml`
- `services/evidence-capture/` and `services/evidence-report/`

Implement fixed Hyperliquid metadata/L2 capture with retained exact bytes and timings; strict sealed-input inspection; live/fixture policy; exact report assembly; deterministic bounded bundle; archive-first offline verifier; atomic publication; internal capture/report services. Keep the existing fixture demo compatibility functions. Live identity remains fail-closed until separately reviewed evidence authorizes it.

## Task 2: Canonical F4/F5 gateway and ledger

**Owns:** `apps/mezo-gateway/**`.

Implement:

- exact package pins and TypeScript build configuration;
- domain state machines matching F2;
- strict request decoding, capability hashing, scoped idempotency, and closed presenters;
- PostgreSQL migrations for requests, artifacts, quotes, attempts, receipts, chain events, entitlements, delivery, reconciliation, and append-only audit;
- report-service and immutable-artifact adapters;
- official x402 adapter boundary, canonical authorization identity gate, Mezo receipt/MUSD transfer reader, and reviewed-finality gate;
- create/status/402/payment/delivery/evidence application flows;
- reconciliation and retention workers;
- Express routes for every frozen F2 endpoint;
- CORS, security headers, no-store, body/rate limits, request IDs, metrics, and log redaction.

When external bindings remain unresolved, the code must compile toward a fail-closed `payment_ready=false` path rather than fake settlement.

## Task 3: Canonical F6 browser application

**Owns:** `apps/mezo-web/**`.

Implement a Vite/TypeScript single-page application that:

- generates and retains a 256-bit capability in `sessionStorage`;
- calls the frozen `/v1/*` API and polls bounded 202 states;
- connects an injected EIP-1193 wallet and requires chain `31611`;
- shows exact quote terms, snapshot limitations, expiry, retention, and recipient;
- invokes the official x402 browser adapter without hand-built signing payloads;
- handles cancel, wrong chain, wallet switch, reload, expiry, uncertain settlement, and paid recovery;
- renders report/receipt and validated explorer links only after entitlement;
- downloads the evidence bundle under the same entitlement;
- permanently labels testnet and read-only analytics boundaries.

Keep the existing `/demo/*` fixture UI separate.

## Task 4: F6 deployment and operations surface

**Owns:** `deploy/mezo-evidence/**` and `docs/runbooks/**`.

Create hardened Dockerfiles, Compose fixture/live profiles, isolated networks and volumes, PostgreSQL, capture, report, gateway, web, and Caddy edge services. Add safe environment examples and secret-file conventions. Add startup/shutdown, testnet demo, payment recovery, artifact recovery, backup/restore, incident, and observability runbooks. No artifact directory may be mounted into the public static service.

## Task 5: F7 acceptance and competition tooling

**Owns:**

- `tools/mezo_acceptance/**`
- `scripts/run-mezo-acceptance.py`
- `schemas/mezo-evidence/v1/acceptance-result.schema.json`
- `docs/competition/**`

Implement a result-producing A01–A30 runner with offline/live modes, exact repository identity, environment/command/exit metadata, sanitized evidence, explicit omissions, and `BLOCKED_EXTERNAL` for unauthorized live work. Add honest demo/submission/description documents. Do not create PASS evidence files before execution.

## Task 6: Factory, graph, packaging, and repository integration

**Owns shared integration files after Tasks 1–5 merge:**

- `architecture/**`
- `tools/graph_checker/**`
- root `pyproject.toml`, `Makefile`, and build/artifact scripts
- `README.md`, `handoff.md`, and change task records

Add runtime profiles and exact inventory bindings for evidence report, capture/report services, gateway, web, migrations, deployment, acceptance tooling, tests, and plans. Package schema/migration resources inside wheels and bundle web assets into their owning application artifacts. Preserve the existing Stage A three-wheel factory; add separate Liqvera Python, gateway, web, image, Compose, and acceptance targets. Record that code exists but execution and acceptance remain pending.

## Deferred Verification Phase

After Task 6, run factory/build/typecheck/tests/graph/browser/Compose/security/fault/live acceptance in dependency order, then repair defects. Until that phase completes, F3–F7 remain `IMPLEMENTED_UNVERIFIED`; all existing vector and acceptance statuses remain unchanged, payment stays disabled, and no release or deployment is authorized.
