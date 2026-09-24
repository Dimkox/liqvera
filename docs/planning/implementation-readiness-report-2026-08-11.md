---
stepsCompleted:
  - step-01-document-discovery
  - step-02-prd-analysis
  - step-03-epic-coverage-validation
  - step-04-ux-alignment
  - step-05-epic-quality-review
  - step-06-final-assessment
inputDocuments:
  - docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md
  - docs/superpowers/plans/2026-08-11-unified-graph-migration-program.md
  - docs/superpowers/plans/2026-08-11-m0-m3-canonical-distributions-and-graph.md
  - docs/superpowers/plans/2026-08-11-m4-evidence-runs-and-frozen-data.md
  - docs/superpowers/plans/2026-08-11-m5-stage-a-v2-strategy-economics.md
  - docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md
  - docs/planning/epics.md
date: 2026-08-11
project: Multi-Exchange Engine Unified Strategy Evidence Graph
---

# Implementation Readiness Assessment Report

**Date:** 2026-08-11
**Project:** Multi-Exchange Engine Unified Strategy Evidence Graph

## Document Discovery

### PRD Files Found

**Whole Documents:** none.

**Sharded Documents:** none.

The approved architecture/specification and the complete requirements inventory
inside `docs/planning/epics.md` are the selected requirement authorities for
this brownfield internal-research project. No standalone PRD is selected.

### Architecture Files Found

**Selected whole architecture contract:**

- `docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md`

**Selected implementation projections:**

- `docs/superpowers/plans/2026-08-11-unified-graph-migration-program.md`
- `docs/superpowers/plans/2026-08-11-m0-m3-canonical-distributions-and-graph.md`
- `docs/superpowers/plans/2026-08-11-m4-evidence-runs-and-frozen-data.md`
- `docs/superpowers/plans/2026-08-11-m5-stage-a-v2-strategy-economics.md`
- `docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md`

**Sharded Documents:** none.

### Epics and Stories Files Found

**Whole Documents:**

- `docs/planning/epics.md` (selected)

**Sharded Documents:** none.

### UX Design Files Found

**Whole Documents:** none.

**Sharded Documents:** none.

No UX document is required: Stage A is an internal operator/research hypothesis
test, and customer/retail surfaces are explicitly outside the approved scope.

### Discovery Issues

- No whole/sharded duplicate formats were found.
- The absence of a standalone PRD is recorded; stable product, data, strategy,
  architecture, graph, CI, security, and operations requirements are carried by
  the selected approved specification and `epics.md` inventory.
- The absence of UX artifacts is intentional and scope-aligned.

## PRD Analysis

There is no standalone PRD. The selected complete requirements authority is extracted
in full below from `docs/planning/epics.md`.

### Functional Requirements

- FR1 (`PROD-001`): Stage A determines whether reproducible Hyperliquid/Lighter strategies survive executable depth, costs, delay, data quality, and capital constraints.
- FR2 (`PROD-002`): Stage A decisions are exactly `STOP`, `EXTEND_LONGER_SHADOW`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET`.
- FR3 (`PROD-003`): Stage A can complete honestly without a positive strategy result.
- FR4 (`PROD-004`): Research, documentation, a green test, or a positive simulation cannot authorize live trading.
- FR5 (`PROD-005`): Strategy outputs are explainable from immutable input evidence, configuration, and code identity.
- FR6 (`PROD-006`): The primary actor is an internal operator/researcher whose outcome is a reproducible evidence package and typed continued-shadow decision.
- FR7 (`PROD-007`): Acquisition spans seven calendar days and binding evidence requires at least five complete UTC days.
- FR8 (`PROD-008`): Primary venues are Hyperliquid and Lighter and primary assets are BTC, ETH, and SOL; Solana-chain runtime remains quarantined.
- FR9 (`PROD-009`): A binding dataset requires at least 95% strict healthy minutes, verified mappings, and at least 20 independent episodes.
- FR10 (`PROD-010`): Continuation requires positive total and median net P&L, 300/500 ms survival, positive USD 1,000 net, nonnegative USD 5,000 net, both fee cases, and less than 25% largest-episode concentration.
- FR11 (`PROD-011`): A funding continuation reason requires realized funding cashflows; forecasts cannot satisfy it.
- FR12 (`PROD-012`): `EXTEND_LONGER_SHADOW` targets 7-14 complete UTC days and at least 100 independent lifecycles and never means `GO`.
- FR13 (`PROD-013`): The historical USD 10, PUMP/DOGE, KILL/EXTEND contract is superseded provenance only.
- FR14 (`PROD-014`): External demand, willingness to pay, revenue, and production profitability remain unsupported falsifiable hypotheses requiring separate actors, metrics, evidence, and approval.
- FR15 (`DATA-001`): Raw evidence is immutable, append-only, and bound to exact run, epoch, sequence, ingest, schema, decoder, collector, and payload identities.
- FR16 (`DATA-002`): Public Capture records wire/control/quality evidence and does not own books, opportunities, economics, strategies, or verdicts.
- FR17 (`DATA-003`): Analyzer input is exposed through deterministic read-only PostgreSQL views and an equivalent immutable frozen-package reader.
- FR18 (`DATA-004`): Final replay belongs to `AnalysisRun`, reads a verified frozen package, has no network/host clock, never mutates capture, and is byte-identical across fresh processes.
- FR19 (`DATA-005`): Economic arithmetic uses exact decimal, fixed-point, or rational values and rejects ambiguous/non-finite floats.
- FR20 (`DATA-006`): Economic identity includes payoff, multiplier, settlement/collateral, units, venue ID, validity, and provenance; ticker equality is insufficient.
- FR21 (`DATA-007`): A reconstructed book requires an authoritative snapshot, continuous venue-valid sequencing, valid positive levels, ordering, and non-crossed spread.
- FR22 (`DATA-008`): Gaps, regressions, reconnects, unsupported transitions, or malformed payloads close an epoch until a new valid snapshot.
- FR23 (`DATA-009`): Executable economics uses full-depth VWAP on both legs for entry and exit; missing depth rejects.
- FR24 (`DATA-010`): Every derived checkpoint, opportunity, simulation, report, and decision traces to raw evidence and configuration hashes.
- FR25 (`DATA-011`): Every capture session has one immutable unpartitioned `CaptureRun` root, and every capture-owned evidence object gets one unpartitioned registry row bound to that root before payload admission to any day partition.
- FR26 (`DATA-012`): Typed evidence edges use foreign keys for both endpoints and reject dangling, incompatible, or unauthorized cross-run links.
- FR27 (`DATA-013`): Logical evidence keys are globally unique within their declared scope through an unpartitioned authority; partition-local indexes and application-side pre-checks are never the cross-dataset uniqueness authority.
- FR28 (`DATA-014`): One constrained writer atomically enforces root, registry, edge, logical-key, hash, and append-only invariants without DML bypass.
- FR29 (`DATA-015`): Capture terminalization records closure/counts/bounds/hash, and frozen receipts bind the exact sealed root and node set.
- FR30 (`DATA-016`): Frozen validation parses envelopes, recomputes hashes, verifies identity/order/time/counts/duplicates, and closes over pre-seal replay, lifecycle, soak, decoder, and connection evidence. Post-package analyzer replay belongs only to `AnalysisRun`, cannot enter or reopen `CaptureRun`, and any mismatch or missing closure yields `INVALID_DATASET`.
- FR31 (`DATA-017`): Raw evidence cannot be retained away until a retrievable independently verified frozen receipt exists; retention has its own root.
- FR32 (`DATA-018`): `derived_from` and `supersedes` form an acyclic DAG with at most one direct successor per lineage; competing successors block.
- FR33 (`DATA-019`): Capture sealing serializes against admission and rejects every post-seal capture write; separate `AnalysisRun` writes never mutate or append nodes under `CaptureRun`.
- FR34 (`DATA-020`): Hashed effective evidence time is canonical; audit/insertion time is nonsemantic and cannot affect replay or economics.
- FR35 (`DATA-021`): Digest-pinned PostgreSQL 16/17 jobs run full migrations, schema, grants, writer, concurrency, seal-race, view, and frozen-reader suites from clean databases.
- FR36 (`DATA-022`): Analyzer has only required CONNECT/USAGE/view SELECT and no mutation, writer execution, ownership, or inheritance path.
- FR37 (`DATA-023`): Every analysis has a separate immutable `AnalysisRun` bound to capture, frozen receipt, analyzer/code, configuration, derived closure, and terminal hash.
- FR38 (`DATA-024`): Every retention operation has a separate immutable `RetentionAction` bound to capture and frozen receipt without mutating either run.
- FR39 (`DATA-025`): Cross-root edges use typed versioned contracts; Capture, Analysis, package-receipt, and Retention roots have distinct logical-key scopes, registries, writer privileges, and terminal state machines, and edges never imply ownership transfer or reopen a sealed root.
- FR40 (`STRAT-001`): Active strategies consume immutable reconstructed evidence and emit shadow simulations, never order commands.
- FR41 (`STRAT-002`): Basis convergence evaluates independent delayed full-cost entry and exit on executable books.
- FR42 (`STRAT-003`): Realized funding carry separates forecasts from settlement cashflows and attributes sign, schedule, entry, exit, basis, and holding costs.
- FR43 (`STRAT-004`): Paired-basis trailing is diagnostic and cannot cause extension or conceal failure of the binding aggregate or required admitted-cell evidence; an economically negative cell alone is not an independent verdict under the owner-selected aggregate rule.
- FR44 (`STRAT-005`): Strategy, inventory, exit, execution, and portfolio policies remain separate contracts.
- FR45 (`STRAT-006`): Grid, DCA, Infinity Grid, Solana strategies, maker-fill claims, and legacy asset bots remain quarantined.
- FR46 (`STRAT-007`): Quarantined material is provenance/research only and requires a separate approved manifest and evidence gate for promotion.
- FR47 (`STRAT-008`): Parameters, thresholds, costs, and baselines freeze before acquisition; post-hoc tuning is diagnostic only.
- FR48 (`STRAT-009`): Independent episodes, capital locks, deterministic priority, and concentration reporting prevent duplicate economics.
- FR49 (`STRAT-010`): Failed attempts, residual neutralization, rebalance, fees, delay decay, and infrastructure costs are attributable.
- FR1 (`PROD-001`) -> Epic 4: Stage A typed decision from reproducible strategy evidence.
- FR2 (`PROD-002`) -> Epic 4: Closed four-value decision contract.
- FR3 (`PROD-003`) -> Epic 4: Honest completion without a positive result.
- FR4 (`PROD-004`) -> Epic 4: No live-trading authorization from Stage A.
- FR5 (`PROD-005`) -> Epic 4: Explainable outputs bound to evidence, configuration, and code.
- FR6 (`PROD-006`) -> Epic 4: Internal operator/researcher outcome.
- FR7 (`PROD-007`) -> Epic 4: Seven-day acquisition and five-complete-day binding evidence.
- FR8 (`PROD-008`) -> Epic 4: Binding venues/assets and Solana quarantine.
- FR9 (`PROD-009`) -> Epic 4: Dataset sufficiency thresholds.
- FR10 (`PROD-010`) -> Epic 4: Binding continuation economics.
- FR11 (`PROD-011`) -> Epic 4: Realized-funding continuation requirement.
- FR12 (`PROD-012`) -> Epic 4: Longer-shadow target without GO semantics.
- FR13 (`PROD-013`) -> Epic 4: Superseded historical contract provenance.
- FR14 (`PROD-014`) -> Epic 4: Separate falsifiable external hypotheses.
- FR15 (`DATA-001`) -> Epic 1: Immutable raw evidence identity.
- FR16 (`DATA-002`) -> Epic 1: Public Capture ownership boundary.
- FR17 (`DATA-003`) -> Epic 1: Equivalent deterministic readers.
- FR18 (`DATA-004`) -> Epic 4: Final deterministic AnalysisRun replay.
- FR19 (`DATA-005`) -> Epic 2: Exact economic arithmetic.
- FR20 (`DATA-006`) -> Epic 2: Exact economic instrument identity.
- FR21 (`DATA-007`) -> Epic 2: Fail-closed reconstructed books.
- FR22 (`DATA-008`) -> Epic 2: Epoch closure and recovery.
- FR23 (`DATA-009`) -> Epic 2: Full-depth two-leg lifecycle economics.
- FR24 (`DATA-010`) -> Epic 4: Complete derived-output provenance.
- FR25 (`DATA-011`) -> Epic 1: CaptureRun and evidence registry authority.
- FR26 (`DATA-012`) -> Epic 1: Typed evidence edges with endpoint integrity.
- FR27 (`DATA-013`) -> Epic 1: Global logical-key uniqueness.
- FR28 (`DATA-014`) -> Epic 1: Constrained atomic capture writer.
- FR29 (`DATA-015`) -> Epic 1: Capture seal and frozen receipt identity.
- FR30 (`DATA-016`) -> Epic 1: Semantic frozen validation and capture closure.
- FR31 (`DATA-017`) -> Epic 1: Receipt-gated retention.
- FR32 (`DATA-018`) -> Epic 1: Acyclic derivation and supersession lineage.
- FR33 (`DATA-019`) -> Epic 1: Seal/admission serialization and run isolation.
- FR34 (`DATA-020`) -> Epic 1: Canonical evidence time.
- FR35 (`DATA-021`) -> Epic 1: PostgreSQL 16/17 evidence-contract verification.
- FR36 (`DATA-022`) -> Epic 1: Analyzer least-privilege reader role.
- FR37 (`DATA-023`) -> Epic 4: Immutable AnalysisRun root and terminal hash.
- FR38 (`DATA-024`) -> Epic 1: Immutable RetentionAction root.
- FR39 (`DATA-025`) -> Epic 1: Typed cross-root contracts and distinct ownership.
- FR40 (`STRAT-001`) -> Epic 3: Shadow-only strategy outputs.
- FR41 (`STRAT-002`) -> Epic 3: Delayed full-cost basis convergence.
- FR42 (`STRAT-003`) -> Epic 3: Realized funding carry.
- FR43 (`STRAT-004`) -> Epic 3: Non-binding paired-basis trailing diagnostic.
- FR44 (`STRAT-005`) -> Epic 3: Separate strategy/inventory/exit/execution/portfolio policies.
- FR45 (`STRAT-006`) -> Epic 3: Quarantined unsupported strategy families.
- FR46 (`STRAT-007`) -> Epic 3: Approved promotion gate for quarantined material.
- FR47 (`STRAT-008`) -> Epic 3: Pre-acquisition parameter freeze.
- FR48 (`STRAT-009`) -> Epic 3: Independent episodes, capital locks, and concentration.
- FR49 (`STRAT-010`) -> Epic 3: Complete attempt and cost attribution.

**Total FRs: 98.**

### Non-Functional Requirements

- NFR1 (`ARCH-001`): One modular monorepo owns three separate distributions/namespaces and eliminates both legacy `multi_exchange_engine` owners.
- NFR2 (`ARCH-002`): Capture and Analyzer have separate metadata, dependencies, artifacts, entry points, and capability validation.
- NFR3 (`ARCH-003`): Execution capability is absent from every Stage A runtime and artifact boundary.
- NFR4 (`ARCH-004`): Only pure `mee_contracts` is shared; application layers never import each other.
- NFR5 (`ARCH-005`): Venue adapters expose capability-specific public, account, trading, and RFQ contracts.
- NFR6 (`ARCH-006`): PostgreSQL is durable evidence authority and verified frozen packages are final replay authority under AnalysisRun.
- NFR7 (`ARCH-007`): Telegram, web, and reports are projections, never execution authority.
- NFR8 (`ARCH-008`): Every executable entry point, module, configuration, and workflow has one canonical manifest owner.
- NFR9 (`ARCH-009`): `mee_contracts` installs and tests independently with no application, adapter, storage, network, database, or workflow dependency.
- NFR10 (`ARCH-GO-001`): Go invariants are `TEST_ONLY_EXECUTABLE_SPEC` from M0 until Python conformance is approved.
- NFR11 (`ARCH-GO-002`): Go references are not retired merely because similarly named Python code exists.
- NFR12 (`ARCH-GO-003`): Conformance maps each invariant to contract, Python implementation, negative tests, Claw receipt, and review.
- NFR13 (`ARCH-GO-004`): Go source/binaries/layers/modules/dependencies are excluded from every Stage A artifact from M0.
- NFR14 (`ARCH-GO-005`): Conformance controls retirement but never makes Go deployable; Git preserves provenance.
- NFR15 (`GRAPH-001`): Every active requirement traces through contract, code/dataflow, test/eval, Claw gate, artifact, deployment boundary, evidence, and rollback.
- NFR16 (`GRAPH-002`): Runtime dependencies form a DAG; application-layer cycles block commit.
- NFR17 (`GRAPH-003`): Evidence is append-only and corrections supersede with provenance rather than rewrite.
- NFR18 (`GRAPH-004`): Release graph binds source, locks, configs, tests, scans, digests, promotion, deployment, health, and rollback.
- NFR19 (`GRAPH-005`): No active code, config, workflow, document, state, migration, test, or artifact may be orphaned.
- NFR20 (`GRAPH-006`): A checker validates completeness, ownership, reachability, acyclicity, compatibility, and allowed edges.
- NFR21 (`GRAPH-007`): Checker failure blocks commit and merge without bypass.
- NFR22 (`GRAPH-008`): Nodes have versioned lifecycle states and optional migrating/quarantined classification with fail-closed transitions.
- NFR23 (`GRAPH-009`): Pre-commit requires prospective paths; realized receipts are required only at applicable phases.
- NFR24 (`GRAPH-010`): Merge/release/promotion/deploy require immutable phase receipts; placeholder or copied receipts are forbidden.
- NFR25 (`GRAPH-011`): Migration has one active owner; replaced owners are unreachable, expiring, rollback-bound, and never dual-active.
- NFR26 (`GRAPH-012`): Product traceability connects actor/outcome/requirement/criterion/metric/contract/dataflow/test/gate/artifact/evidence; hypotheses remain separate and falsifiable.
- NFR27 (`CI-001`): All test, validation, build, scan, and promotion gates run only on Claw.
- NFR28 (`CI-002`): No GitHub-hosted runner is automatic or required.
- NFR29 (`CI-003`): Trusted validation is default-branch controlled, exact same-repository PR SHA, read-only, and credential-free after checkout.
- NFR30 (`CI-004`): Workspaces, environments, databases, evidence, and temporary files are isolated per run and deterministically cleaned.
- NFR31 (`CI-005`): PR validation has no deploy, promotion, registry, private API, credential, or trading authority.
- NFR32 (`CI-006`): Actions, images, PostgreSQL, scanners, and build inputs are pinned.
- NFR33 (`CI-007`): Release receipts require same-SHA dependency, graph, contract, tests, deterministic AnalysisRun replay, SBOM, vulnerability, and artifact-identity gates.
- NFR34 (`CI-008`): PR validation runs in a disposable sandbox isolated from host Docker, production routes/data, credentials, and deployment.
- NFR35 (`SEC-001`): Capture contains no signer, wallet, credential, private/account selector, order, cancel, transfer, or withdrawal capability.
- NFR36 (`SEC-002`): Analyzer cannot mutate capture and final replay has no venue network client.
- NFR37 (`SEC-003`): Stage A artifacts package no trading adapter, live bot, n8n workflow, or execution library.
- NFR38 (`SEC-004`): Secrets never enter source, logs, manifests, artifacts, or error representations.
- NFR39 (`SEC-005`): Static/dependency/negative/artifact checks and independent review prove capability boundaries.
- NFR40 (`SEC-006`): Missing provenance, fee, mapping, capability, or contract evidence fails closed.
- NFR41 (`SEC-007`): Boundary proof inspects installed manifests/imports/dependencies/entry points/layers/symbols/network surface/grants and negative mutation tests.
- NFR42 (`OPS-001`): App-stack consumes only exact promoted digests with verified final release receipt and configuration hash.
- NFR43 (`OPS-002`): Deployment uses an isolated immutable app-stack checkout and never touches dirty `/home/operator/app-stack`.
- NFR44 (`OPS-003`): Deployment targets only Compose project `mee-a2` and cannot mutate n8n or unrelated services.
- NFR45 (`OPS-004`): Start requires deployment authorization, exact revision, approved run, registry, clock, DB contract, and candidate receipt; the deployment boundary additionally verifies that this exact candidate is enclosed by the realized final release receipt.
- NFR46 (`OPS-005`): Deployment captures health, readiness, soak, image/config identity, and current-run PostgreSQL evidence.
- NFR47 (`OPS-006`): Rollback uses exact prior digest and preserves append-only evidence.
- NFR48 (`OPS-007`): Automatic push deployment is forbidden.
- NFR49 (`OPS-008`): Deployment is blocked until app-stack includes DB fix `3ce7e1f` or an independently reviewed equivalent whose migration, role, table-partition, writer, and frozen-reader evidence is bound to the exact app-stack SHA.

**Total NFRs: 49.**

### Additional Requirements

- AR1: This is a brownfield migration from audited engine base `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99`; no starter template is used.
- AR2: Architecture approval is anchored at `a0cdbbf78a38f0bd429a45c810a5c34862a18ef1`; implementation cannot reinterpret it.
- AR3: PR #21 head `7fe6918690f8bc1da5826c67e3619de4126e4f54` is salvaged blob-by-blob with provenance and is never whole-branch merged.
- AR4: The binding verdict rule is owner-approved `FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE`; admitted cells and deterministic capital weights freeze before acquisition and cannot be removed or reweighted from observed economics. Every completed and failed attempt from every admitted cell enters the aggregate. Missing required evidence for any admitted cell makes the run `INVALID_DATASET` or `INSUFFICIENT_EVIDENCE`, never an aggregate over survivors. Binding economic predicates apply only to the aggregate; per-cell economics are mandatory non-binding reconciled report slices. The minimum 20 independent episodes applies to the aggregate unless a separate per-cell minimum is owner-approved before acquisition.
- AR5: Exact implementation order is M0 policy, M6 Task 1 trusted controller, M1-M3 distributions/boundaries, M4 evidence, M5 analysis, then M6 Tasks 2-5 release/app-stack.
- AR6: Release causality is mandatory: candidate receipt -> exact app-stack DB receipt -> human-authorized promotion request binding both -> realized promotion receipt -> final release receipt binding that realized promotion -> separate deployment authorization consuming the final receipt. No phase can be parallelized past or substituted for its predecessor.
- AR7: App-stack changes are reviewed in its repository from isolated exact archives; PR #42-equivalent authentication repair precedes PR #39-equivalent no-push deployment control.
- AR8: Every story must own one coherent graph-connected slice, use RED/GREEN checks, identify an independent verifier, update `handoff.md`, and have rollback/replacement evidence.
- AR9: Local diagnostics never satisfy merge/release evidence; authoritative validation is exact-SHA Claw-only.
- AR10: No implementation, build, promotion, deployment, n8n, private API, or live trading begins from this requirements-extraction step.
- AR11: Claw is the authoritative full multi-project test/integration environment. Within isolated per-project, run, attempt, network, database, artifact, and credential namespaces, agents may apply and roll back migrations, containers, candidate artifacts, and test configuration in real time. Every mutation must be receipt-bound and deterministically cleaned or rolled back; this authority never reaches production, private venue APIs, n8n, live trading, unrelated projects, or dirty `/home/operator/app-stack`.

**Total additional requirements: 11.**

### PRD Completeness Assessment

Requirements authority is complete for the approved internal Stage-A scope: stable
product/data/strategy IDs, closed decision semantics, exact evidence contracts,
architecture/capability boundaries, graph/CI/security/operations constraints, and
brownfield sequencing are present. A standalone retail/customer PRD and UX contract
are intentionally absent; external demand/revenue remain separate unsupported
hypotheses and do not constitute implementation authority.

## Epic Coverage Validation

### Coverage Matrix

| FR | Stable ID | Requirement | Epic and Story Coverage | Status |
| --- | --- | --- | --- | --- |
| FR1 | `PROD-001` | Stage A determines whether reproducible Hyperliquid/Lighter strategies survive executable depth, costs, delay, data quality, and capital constraints. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR2 | `PROD-002` | Stage A decisions are exactly `STOP`, `EXTEND_LONGER_SHADOW`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET`. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR3 | `PROD-003` | Stage A can complete honestly without a positive strategy result. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR4 | `PROD-004` | Research, documentation, a green test, or a positive simulation cannot authorize live trading. | Epic 4; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR5 | `PROD-005` | Strategy outputs are explainable from immutable input evidence, configuration, and code identity. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence; Story 4.3: Reproduce a byte-identical report and analysis replay receipt | COVERED |
| FR6 | `PROD-006` | The primary actor is an internal operator/researcher whose outcome is a reproducible evidence package and typed continued-shadow decision. | Epic 4; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR7 | `PROD-007` | Acquisition spans seven calendar days and binding evidence requires at least five complete UTC days. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR8 | `PROD-008` | Primary venues are Hyperliquid and Lighter and primary assets are BTC, ETH, and SOL; Solana-chain runtime remains quarantined. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR9 | `PROD-009` | A binding dataset requires at least 95% strict healthy minutes, verified mappings, and at least 20 independent episodes. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR10 | `PROD-010` | Continuation requires positive total and median net P&L, 300/500 ms survival, positive USD 1,000 net, nonnegative USD 5,000 net, both fee cases, and less than 25% largest-episode concentration. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR11 | `PROD-011` | A funding continuation reason requires realized funding cashflows; forecasts cannot satisfy it. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence | COVERED |
| FR12 | `PROD-012` | `EXTEND_LONGER_SHADOW` targets 7-14 complete UTC days and at least 100 independent lifecycles and never means `GO`. | Epic 4; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR13 | `PROD-013` | The historical USD 10, PUMP/DOGE, KILL/EXTEND contract is superseded provenance only. | Epic 4; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR14 | `PROD-014` | External demand, willingness to pay, revenue, and production profitability remain unsupported falsifiable hypotheses requiring separate actors, metrics, evidence, and approval. | Epic 4; Story 4.4: Limit the decision to the internal Stage-A hypothesis | COVERED |
| FR15 | `DATA-001` | Raw evidence is immutable, append-only, and bound to exact run, epoch, sequence, ingest, schema, decoder, collector, and payload identities. | Epic 1; Story 1.4: Register immutable CaptureRun and evidence before partition admission | COVERED |
| FR16 | `DATA-002` | Public Capture records wire/control/quality evidence and does not own books, opportunities, economics, strategies, or verdicts. | Epic 1; Story 1.3: Launch capability-isolated Public Capture from the canonical distribution | COVERED |
| FR17 | `DATA-003` | Analyzer input is exposed through deterministic read-only PostgreSQL views and an equivalent immutable frozen-package reader. | Epic 1; Story 1.8: Read capture evidence through a deterministic least-privilege PostgreSQL contract; Story 1.9: Export and semantically validate an immutable frozen package; Story 2.2: Deterministically reconstruct fail-closed venue books | COVERED |
| FR18 | `DATA-004` | Final replay belongs to `AnalysisRun`, reads a verified frozen package, has no network/host clock, never mutates capture, and is byte-identical across fresh processes. | Epic 4; Story 4.1: Create and seal an immutable AnalysisRun in isolation; Story 4.3: Reproduce a byte-identical report and analysis replay receipt | COVERED |
| FR19 | `DATA-005` | Economic arithmetic uses exact decimal, fixed-point, or rational values and rejects ambiguous/non-finite floats. | Epic 2; Story 2.1: Map instruments by exact economic identity; Story 2.2: Deterministically reconstruct fail-closed venue books; Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP | COVERED |
| FR20 | `DATA-006` | Economic identity includes payoff, multiplier, settlement/collateral, units, venue ID, validity, and provenance; ticker equality is insufficient. | Epic 2; Story 2.1: Map instruments by exact economic identity; Story 2.2: Deterministically reconstruct fail-closed venue books; Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP | COVERED |
| FR21 | `DATA-007` | A reconstructed book requires an authoritative snapshot, continuous venue-valid sequencing, valid positive levels, ordering, and non-crossed spread. | Epic 2; Story 2.2: Deterministically reconstruct fail-closed venue books; Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP | COVERED |
| FR22 | `DATA-008` | Gaps, regressions, reconnects, unsupported transitions, or malformed payloads close an epoch until a new valid snapshot. | Epic 2; Story 2.2: Deterministically reconstruct fail-closed venue books; Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP | COVERED |
| FR23 | `DATA-009` | Executable economics uses full-depth VWAP on both legs for entry and exit; missing depth rejects. | Epic 2; Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP | COVERED |
| FR24 | `DATA-010` | Every derived checkpoint, opportunity, simulation, report, and decision traces to raw evidence and configuration hashes. | Epic 4; Story 4.1: Create and seal an immutable AnalysisRun in isolation; Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence; Story 4.3: Reproduce a byte-identical report and analysis replay receipt | COVERED |
| FR25 | `DATA-011` | Every capture session has one immutable unpartitioned `CaptureRun` root, and every capture-owned evidence object gets one unpartitioned registry row bound to that root before payload admission to any day partition. | Epic 1; Story 1.4: Register immutable CaptureRun and evidence before partition admission | COVERED |
| FR26 | `DATA-012` | Typed evidence edges use foreign keys for both endpoints and reject dangling, incompatible, or unauthorized cross-run links. | Epic 1; Story 1.5: Link evidence through typed edges and global logical keys | COVERED |
| FR27 | `DATA-013` | Logical evidence keys are globally unique within their declared scope through an unpartitioned authority; partition-local indexes and application-side pre-checks are never the cross-dataset uniqueness authority. | Epic 1; Story 1.5: Link evidence through typed edges and global logical keys | COVERED |
| FR28 | `DATA-014` | One constrained writer atomically enforces root, registry, edge, logical-key, hash, and append-only invariants without DML bypass. | Epic 1; Story 1.6: Write capture evidence only through an atomic constrained writer | COVERED |
| FR29 | `DATA-015` | Capture terminalization records closure/counts/bounds/hash, and frozen receipts bind the exact sealed root and node set. | Epic 1; Story 1.7: Seal CaptureRun race-safely and record terminal identity; Story 1.9: Export and semantically validate an immutable frozen package | COVERED |
| FR30 | `DATA-016` | Frozen validation parses envelopes, recomputes hashes, verifies identity/order/time/counts/duplicates, and closes over pre-seal replay, lifecycle, soak, decoder, and connection evidence. Post-package analyzer replay belongs only to `AnalysisRun`, cannot enter or reopen `CaptureRun`, and any mismatch or missing closure yields `INVALID_DATASET`. | Epic 1; Story 1.7: Seal CaptureRun race-safely and record terminal identity; Story 1.9: Export and semantically validate an immutable frozen package | COVERED |
| FR31 | `DATA-017` | Raw evidence cannot be retained away until a retrievable independently verified frozen receipt exists; retention has its own root. | Epic 1; Story 1.9: Export and semantically validate an immutable frozen package; Story 1.10: Allow retention only through a verified FrozenPackageReceipt | COVERED |
| FR32 | `DATA-018` | `derived_from` and `supersedes` form an acyclic DAG with at most one direct successor per lineage; competing successors block. | Epic 1; Story 1.5: Link evidence through typed edges and global logical keys | COVERED |
| FR33 | `DATA-019` | Capture sealing serializes against admission and rejects every post-seal capture write; separate `AnalysisRun` writes never mutate or append nodes under `CaptureRun`. | Epic 1; Story 1.7: Seal CaptureRun race-safely and record terminal identity | COVERED |
| FR34 | `DATA-020` | Hashed effective evidence time is canonical; audit/insertion time is nonsemantic and cannot affect replay or economics. | Epic 1; Story 1.6: Write capture evidence only through an atomic constrained writer | COVERED |
| FR35 | `DATA-021` | Digest-pinned PostgreSQL 16/17 jobs run full migrations, schema, grants, writer, concurrency, seal-race, view, and frozen-reader suites from clean databases. | Epic 1; Story 1.8: Read capture evidence through a deterministic least-privilege PostgreSQL contract | COVERED |
| FR36 | `DATA-022` | Analyzer has only required CONNECT/USAGE/view SELECT and no mutation, writer execution, ownership, or inheritance path. | Epic 1; Story 1.8: Read capture evidence through a deterministic least-privilege PostgreSQL contract | COVERED |
| FR37 | `DATA-023` | Every analysis has a separate immutable `AnalysisRun` bound to capture, frozen receipt, analyzer/code, configuration, derived closure, and terminal hash. | Epic 4; Story 4.1: Create and seal an immutable AnalysisRun in isolation; Story 4.3: Reproduce a byte-identical report and analysis replay receipt | COVERED |
| FR38 | `DATA-024` | Every retention operation has a separate immutable `RetentionAction` bound to capture and frozen receipt without mutating either run. | Epic 1; Story 1.10: Allow retention only through a verified FrozenPackageReceipt | COVERED |
| FR39 | `DATA-025` | Cross-root edges use typed versioned contracts; Capture, Analysis, package-receipt, and Retention roots have distinct logical-key scopes, registries, writer privileges, and terminal state machines, and edges never imply ownership transfer or reopen a sealed root. | Epic 1; Story 1.5: Link evidence through typed edges and global logical keys; Story 1.7: Seal CaptureRun race-safely and record terminal identity; Story 1.10: Allow retention only through a verified FrozenPackageReceipt | COVERED |
| FR40 | `STRAT-001` | Active strategies consume immutable reconstructed evidence and emit shadow simulations, never order commands. | Epic 3; Story 3.1: Freeze the admitted strategy universe and separate policy contracts; Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger; Story 3.4: Evaluate the executable basis-convergence lifecycle; Story 3.5: Evaluate realized-funding carry from actual settlements; Story 3.7: Build the frozen-universe portfolio aggregate without masking; Story 3.8: Prove quarantine of unsupported strategy runtime | COVERED |
| FR41 | `STRAT-002` | Basis convergence evaluates independent delayed full-cost entry and exit on executable books. | Epic 3; Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger; Story 3.4: Evaluate the executable basis-convergence lifecycle | COVERED |
| FR42 | `STRAT-003` | Realized funding carry separates forecasts from settlement cashflows and attributes sign, schedule, entry, exit, basis, and holding costs. | Epic 3; Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger; Story 3.5: Evaluate realized-funding carry from actual settlements | COVERED |
| FR43 | `STRAT-004` | Paired-basis trailing is diagnostic and cannot cause extension or conceal failure of the binding aggregate or required admitted-cell evidence; an economically negative cell alone is not an independent verdict under the owner-selected aggregate rule. | Epic 3; Story 3.6: Compare paired-basis trailing only as a diagnostic | COVERED |
| FR44 | `STRAT-005` | Strategy, inventory, exit, execution, and portfolio policies remain separate contracts. | Epic 3; Story 3.1: Freeze the admitted strategy universe and separate policy contracts; Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger; Story 3.4: Evaluate the executable basis-convergence lifecycle; Story 3.5: Evaluate realized-funding carry from actual settlements; Story 3.6: Compare paired-basis trailing only as a diagnostic | COVERED |
| FR45 | `STRAT-006` | Grid, DCA, Infinity Grid, Solana strategies, maker-fill claims, and legacy asset bots remain quarantined. | Epic 3; Story 3.8: Prove quarantine of unsupported strategy runtime | COVERED |
| FR46 | `STRAT-007` | Quarantined material is provenance/research only and requires a separate approved manifest and evidence gate for promotion. | Epic 3; Story 3.8: Prove quarantine of unsupported strategy runtime | COVERED |
| FR47 | `STRAT-008` | Parameters, thresholds, costs, and baselines freeze before acquisition; post-hoc tuning is diagnostic only. | Epic 3; Story 3.1: Freeze the admitted strategy universe and separate policy contracts; Story 3.6: Compare paired-basis trailing only as a diagnostic; Story 3.7: Build the frozen-universe portfolio aggregate without masking | COVERED |
| FR48 | `STRAT-009` | Independent episodes, capital locks, deterministic priority, and concentration reporting prevent duplicate economics. | Epic 3; Story 3.3: Identify independent episodes and lock virtual capital; Story 3.4: Evaluate the executable basis-convergence lifecycle; Story 3.5: Evaluate realized-funding carry from actual settlements; Story 3.7: Build the frozen-universe portfolio aggregate without masking | COVERED |
| FR49 | `STRAT-010` | Failed attempts, residual neutralization, rebalance, fees, delay decay, and infrastructure costs are attributable. | Epic 3; Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger; Story 3.3: Identify independent episodes and lock virtual capital; Story 3.4: Evaluate the executable basis-convergence lifecycle; Story 3.5: Evaluate realized-funding carry from actual settlements; Story 3.6: Compare paired-basis trailing only as a diagnostic; Story 3.7: Build the frozen-universe portfolio aggregate without masking | COVERED |

### Missing Requirements

None. Every functional requirement is claimed by exactly one epic and is implemented by at least one story acceptance-criteria slice.

### Coverage Statistics

- Total requirements-authority FRs: 49.
- FRs mapped to an epic: 49.
- FRs referenced by story acceptance criteria: 49.
- Missing FRs: 0.
- Coverage: 100.00%.

Coverage is complete at stable-ID, epic-owner, and story-acceptance levels.

## UX Alignment Assessment

### UX Document Status

Not found; intentionally not required for the approved Stage-A scope.

### Alignment Issues

None. The primary actor is an internal operator/researcher consuming canonical
machine-readable evidence, receipts, and deterministic reports. Telegram, web,
mobile, customer-facing, and retail surfaces are explicitly non-authoritative
and out of scope. Reports are projections and cannot become execution authority.

### Warnings

No missing-UX warning applies to Stage A because no interactive/customer UI is
implied by the selected requirements. Any future retail/operator UI, Telegram,
web, or mobile surface requires a separate actor/outcome, UX contract, metrics,
architecture review, and approval; it cannot be inferred from current reports.

## Epic Quality Review

### Epic Structure

- **Epic 1:** user outcome is a trustworthy public evidence package. It is
  independently useful before reconstruction or strategy analysis.
- **Epic 2:** user outcome is deterministic market reconstruction and executable
  four-leg measurement. It consumes only Epic 1 outputs and makes no strategy
  viability claim.
- **Epic 3:** user outcome is frozen shadow-strategy evidence with complete
  costs/capital. It consumes only Epics 1-2 and emits no verdict/order command.
- **Epic 4:** user outcome is the reproducible typed Stage-A decision plus its
  exact test release/rollout evidence. It consumes Epics 1-3 outputs.

All epic titles and goals are actor/outcome focused. Dependency direction is
strictly Epic 1 -> Epic 2 -> Epic 3 -> Epic 4; no circular or later-epic
dependency exists.

### Story Quality and Sizing

- 31 stories are sequentially numbered: Epic 1 has 10, Epic 2 has 3, Epic 3
  has 8, and Epic 4 has 10.
- Every story has `As an` / `I want` / `So that` and balanced independently
  testable Given/When/Then/And scenarios, including negative/fail-closed cases.
- Trusted source bootstrap and disposable sandbox/cleanup are separate stories.
  The explicit mention of later self-validation is a phase gate: Story 1.1
  independently delivers exact source identity and remains safely fail closed.
- Release schema, candidate build, app-stack DB receipt, promotion/finalization,
  rollout/observation, and rollback/recovery are separately owned stories.
- Counterfactual cost/residual handling remains one coherent ledger slice; basis,
  funding, episodes, trailing, aggregate, and quarantine are separate stories.
- No story requires an implementation supplied only by a future story. Each can
  complete with previous story outputs or independently fail closed.

### Database and Entity Timing

- CaptureRun/registry appears only when capture admission first needs it.
- Typed edges/global keys, writer, seal, views, frozen receipt, and
  RetentionAction are added by their first consuming stories, not upfront.
- AnalysisRun and its separate writer/state machine appear only in Epic 4.
- PostgreSQL 16/17 clean migration/down-migration, grants, concurrency, and
  post-seal denial evidence are embedded at the relevant slices.

### Brownfield and Architecture Compliance

- No starter template is specified; this is the audited brownfield migration.
- Both legacy Python namespace owners are removed through canonical installed
  distributions; Go remains test-only executable specification.
- PR #21 reuse is blob-by-blob with source/rewrite provenance and installed
  tests; whole-branch merge and duplicate owners are forbidden.
- Capture, Analyzer, and pure Contracts capability boundaries remain physical,
  not feature flags. Private/trading/n8n/live capabilities are absent.
- `FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE`, four-value decision precedence, and
  no-retail/no-GO semantics are explicit and testable.

### File Churn Assessment

Shared traceability manifests and `handoff.md` are intentionally updated across
stories because AR8 requires each coherent commit to leave a connected graph and
record owner/verifier/rollback evidence. This overlap is a deliberate per-commit
feedback and orphan-prevention loop, not repeated ownership of core runtime code.
Runtime/data/strategy/release implementations remain separated by bounded context.

### Violations

- **Critical:** none.
- **Major:** none.
- **Minor:** none blocking implementation readiness.

Two independent final reviews (data/DevOps and quant/strategy) returned
`APPROVE` after bootstrap, sizing, aggregate masking, and replay-identity findings
were corrected.

## Summary and Recommendations

### Overall Readiness Status

**READY FOR SPRINT PLANNING.**

The selected architecture, milestone plans, requirements inventory, epic map,
and 31 story acceptance contracts are aligned for Phase 4 sequencing. This
status authorizes planning and story implementation only through the declared
Claw/bootstrap gates. It is not a production, private-API, n8n, or live-trading
authorization.

### Critical Issues Requiring Immediate Action

None. No uncovered FR, architecture contradiction, UX gap, forward dependency,
epic-sized story, receipt cycle, aggregate-masking path, or replay-identity gap
remains in the selected artifacts.

### Recommended Next Steps

1. Generate sprint sequencing from the 31 approved stories, preserving the
   mandatory M0 -> transitional bootstrap -> new-controller self-validation ->
   distributions -> evidence -> economics -> decision -> causal release order.
2. Begin implementation with Story 1.1 only after recording the exact legacy
   default-branch workflow/blob and owner-approved one-time bootstrap scope;
   Stories 1.3+ remain blocked until the new controller self-validation receipt.
3. For every story, use RED/GREEN checks, exact-SHA Claw validation, independent
   verifier ownership, graph/orphan closure, `handoff.md`, immutable receipts,
   and rollback/replacement evidence before commit/merge.
4. Use Claw fully as the isolated multi-project test/integration environment for
   realtime apply/rollback, but never cross project/run namespaces or touch
   production, private venue APIs, n8n, live trading, or dirty
   `/home/operator/app-stack`.
5. Treat `FROZEN_UNIVERSE_PORTFOLIO_AGGREGATE`, Stage-A-v2 thresholds, and the
   four-value verdict as frozen. A semantics change returns to owner approval
   and implementation-readiness review.

### Final Note

This assessment found **0 unresolved issues** across four validation categories:
document authority, functional coverage, UX/scope alignment, and epic/story
quality. Earlier bootstrap, sizing, receipt causality, missing-attempt masking,
and replay-identity findings were corrected before this final status.

**Assessment date:** 2026-08-11
**Assessor:** Codex primary readiness review with independent data/DevOps and
quant/strategy verification.
