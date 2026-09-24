---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md
  - docs/superpowers/plans/2026-08-11-unified-graph-migration-program.md
  - docs/superpowers/plans/2026-08-11-m0-m3-canonical-distributions-and-graph.md
  - docs/superpowers/plans/2026-08-11-m4-evidence-runs-and-frozen-data.md
  - docs/superpowers/plans/2026-08-11-m5-stage-a-v2-strategy-economics.md
  - docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md
---

# Multi-Exchange Engine Unified Strategy Evidence Graph - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the
Multi-Exchange Engine Unified Strategy Evidence Graph, decomposing the approved
product, data, strategy, architecture, graph, CI, security, and operations
requirements into implementable stories.

## Requirements Inventory

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

### NonFunctional Requirements

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

### UX Design Requirements

No UX design contract exists or is required for Stage A. The primary actor uses
operator tooling and deterministic evidence/report artifacts. Telegram, web,
mobile, and customer-facing surfaces remain non-authoritative and out of scope.

### FR Coverage Map

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

## Epic List

### Epic 1: Оператор получает надёжный публичный evidence package

Оператор может запустить публичный capture, получить неизменяемый и целостный
набор evidence, безопасно его запечатать, проверить, заморозить и читать через
эквивалентные read-only интерфейсы без зависимости от будущего анализатора.

**Implementation prerequisite:** Stories 1.1, 1.2 and 1.2A establish the
trusted source controller, disposable sandbox and reversible Claw host
transition. Story 1.3 remains blocked until their authority-NONE gates and
required self-validation evidence complete.

**Implementation prerequisite:** M0 policy/graph authority завершена до Story
1.1. Stories 1.1-1.2 создают и self-validate trusted controller/sandbox и являются
обязательной предпосылкой Stories 1.3-1.10; локальные или исторические runs не
являются receipt evidence.

**FRs covered:** FR15, FR16, FR17, FR25-FR36, FR38, FR39.

### Epic 2: Оператор воспроизводит рынок и измеряет исполнимую cross-venue экономику

Оператор может из проверенного evidence детерминированно восстановить
экономически эквивалентные инструменты и fail-closed книги, а затем измерить
полную исполнимую стоимость входа и выхода по обеим площадкам без заявления о
жизнеспособности стратегии.

**FRs covered:** FR19-FR23.

### Epic 3: Оператор оценивает frozen shadow-стратегии с полными costs и capital constraints

Оператор может прогнать basis и realized-funding shadow-стратегии, увидеть
полные затраты, задержки, неудачные попытки, блокировки капитала, концентрацию
и диагностический paired-basis trailing, не создавая ордеров и не смешивая
карантинные стратегии с binding verdict.

**FRs covered:** FR40-FR49.

### Epic 4: Оператор получает воспроизводимое Stage A решение

Оператор получает запечатанный AnalysisRun, детерминированный replay и отчёт с
одним из четырёх взаимоисключающих решений Stage A, полностью связанным с
исходным evidence, конфигурацией, кодом, exact-SHA Claw gates, release/deploy
границами и rollback evidence; решение никогда не означает разрешение live
trading.

**FRs covered:** FR1-FR14, FR18, FR24, FR37.

## Epic 1: Оператор получает надёжный публичный evidence package

Оператор может запустить публичный capture, получить неизменяемый и целостный
набор evidence, безопасно его запечатать, проверить, заморозить и читать через
эквивалентные read-only интерфейсы без зависимости от будущего анализатора.

### Story 1.1: Bootstrap trusted default-branch PR identity controller

As an внутренний оператор/исследователь,
I want привязать validation к точному open same-repository PR head и trusted default-branch workflow,
So that untrusted payload или branch workflow не могли выбрать проверяемый source.

**Acceptance Criteria:**

**Given** exact frozen Story 1.1 head and a GitHub-authenticated OWNER PR issue comment whose canonical body binds that head/tree, controller/workflow identities, all allowed paths and fixed checks
**When** owner prepares the one-time manual landing exception
**Then** trusted code re-reads the exact unmodified comment by ID, verifies OWNER identity/association and expiry, while the legacy workflow provides no bootstrap evidence and executes no Story 1.1 controller scope
**And** the non-authoritative observation remains `authority=NONE`; Story 1.2 owns atomic single-use consumption and no bootstrap evidence permits Story 1.3, release, promotion or deploy.

**Given** repository dispatch для нового controller
**When** PR identity разрешается через GitHub API
**Then** controller подтверждает exact repository, open PR number/state, exact current head SHA, same-repository head/base и required ancestry/tree identity
**And** arbitrary 40-hex commit, fork head, stale head, payload-only repository claim или PR-local workflow authority отклоняется.

**Given** validated PR identity
**When** source materialизуется
**Then** controller получает exact authenticated archive с token только в step environment, проверяет traversal, links, member policy и exact tree, затем удаляет response/archive credentials
**And** source-materialization observation связывает repository, PR, head SHA/tree, default-branch controller/workflow blob, action/input digests, OWNER approval-comment projection и cleanup intent без выполнения untrusted project commands.

**Given** frozen Story 1.1 changes and exact 57-path review
**When** the owner comment, frozen local verification outputs/hashes, independent source/security YES and graph/governance YES are present
**Then** manual exact source-only landing installs the controller on the default branch with `authority=NONE`, while validation authority remains fail closed until Story 1.2 sandbox/self-validation
**And** traceability связывает NFR15-NFR21, NFR27-NFR33, NFR38-NFR41 и AR5/AR8-AR11; rollback использует exact previous default-branch workflow identity.

### Story 1.2: Выполнять validation в disposable multi-project Claw sandbox

As an внутренний оператор/исследователь,
I want запускать exact materialized source в изолированном rootless sandbox с verified cleanup,
So that Claw можно полноценно использовать для realtime тестов без production, cross-project или credential authority.

**Acceptance Criteria:**

**Given** verified `authority=NONE` source-materialization observation plus a new Phase A
OWNER approval/installation evidence set (PR24 evidence is historical `RETIRED_UNUSED`)
**When** validation запускается
**Then** untrusted source выполняется в unique rootless Podman container/network/workspace с pinned validation image, read-only source, dropped capabilities, no host Docker socket и no production routes/databases
**And** registry/release/deploy/private venue credentials, n8n, live-trading authority и dirty `/home/operator/app-stack` недоступны.

**Given** Claw обслуживает несколько проектов и test iterations
**When** validation накатывает или откатывает migrations, containers, candidate artifacts либо test configuration
**Then** mutable resources получают project/run/attempt identity, isolated database/network/paths/credentials и receipt-bound lifecycle
**And** test mutation не затрагивает unrelated projects, а sandbox policy блокирует unscoped names/routes/mounts.

**Given** validation command завершился success либо failure
**When** cleanup выполняется
**Then** named containers/processes/networks/workspaces удаляются либо подтверждаются absent, validation receipt фиксирует exact inputs/commands/results/output hashes, а отдельный cleanup receipt фиксирует verified outcome
**And** downstream gate требует оба valid receipt hashes и отклоняет failed/unverified cleanup.

**Given** Phase A source-only controller/host-helper install landed with `authority=NONE`
**When** установленный exact Phase A controller валидирует separate minimal Phase B probe PR
**Then** validation, cleanup и self-validation receipts связывают controller SHA/tree/workflow blob, sandbox policy/image, source SHA/tree, nonce consumption и cleanup
**And** отдельный Phase C1 evidence-proposal PR lands immutable external Phase B run URL/hashes с `authority=NONE`; только следующий Phase C2 evidence-admission PR, связанный с уже существующим authenticated C1 merge SHA/tree/API payload и его committer date, может разрешить Story 1.3, не изменяет Phase B/C1 и только тогда фиксирует legacy `SUPERSEDED`/disabled evidence.

**Given** repository workflows и runner labels
**When** policy tests и independent DevOps/security review выполняются
**Then** test/validation/build/scan/promotion используют только `[self-hosted, claw]`, PR gate имеет minimal read-only permissions и no deploy/promotion/private/live authority
**And** traceability связывает NFR15-NFR34, NFR38-NFR41 и AR5/AR8-AR11 с receipts, cleanup и reviewed replacement path.

### Story 1.2A: Claw engine-runner host transition

As an внутренний оператор/исследователь,
I want выполнять owner-approved переход Claw engine runner через root-owned
transaction controller с durable rollback,
So that rootless disposable validation получает dedicated runner identity без
копирования credentials, нарушения app-stack или неавторизованной host mutation.

**Acceptance Criteria:**

**Given** exact reviewed source/tree, D0 manifest and a separate owner D0 approval
**When** deployment controller is installed
**Then** installed bytes, systemd/socket/reconciler identities and recovery
interfaces are independently verified
**And** D0 success grants `authority=NONE` and no D1 or Story 1.3 authority.

**Given** the first owner-approved D1 attempt and the installed policy path
`ci/claw/oci-evidence-approval.json`
**When** the installed verifier reads the root-owned approval copy
**Then** the observed `STAGED_INPUT_VERIFY` path-domain failure is recorded as
pre-nonce, pre-WAL and pre-mutation evidence
**And** physical `--approval` and logical `--approval-policy-path` are corrected
under `OCIAPATH-001..005`, with the logical value closed to the exact
source-relative constant.

**Given** corrected source has direct Claw RED/GREEN evidence and independent
security plus graph YES
**When** it is prepared for landing
**Then** installed manifest hashes, graph inventory, exact source approval paths,
recovery semantics and handoff evidence are exact
**And** source merge still grants no host apply authority.

**Given** corrected source lands
**When** host transition is retried
**Then** a separately approved D0 update, fresh authenticated inventory and a
new exact D1 owner approval are mandatory before `begin`
**And** `finalize` requires a later separate owner confirmation; the expired
failed-attempt approval is never reused and Story 1.3 remains blocked.

### Story 1.3: Запустить capability-isolated Public Capture из canonical distribution

As an внутренний оператор/исследователь,
I want запускать Public Capture из отдельного установленного артефакта с чистым контрактным ядром,
So that сбор публичного evidence физически не может получить торговые, приватные или аналитические полномочия.

**Acceptance Criteria:**

**Given** modular-monorepo layout с отдельно устанавливаемыми `mee_contracts`, `mee_public_capture` и `mee_readonly_analyzer`
**When** собираются и устанавливаются contracts и Public Capture distributions в чистое окружение
**Then** Public Capture запускается только через canonical `mee_public_capture` entry point и импортирует application-код только из собственного namespace и pure `mee_contracts`
**And** `mee_contracts` отдельно устанавливается и проходит contract tests без application, adapter, storage, network, database или workflow dependencies.

**Given** установленный Public Capture artifact и его resolved dependency/import/file/entry-point manifests
**When** выполняется capability-boundary validation
**Then** в артефакте отсутствуют `mee_readonly_analyzer`, legacy `multi_exchange_engine`, Go binaries/layers и любые signer, wallet, credential, private/account, order, cancel, transfer, withdrawal, n8n или execution capabilities
**And** запрещённые imports, symbols, dependency edges, entry points или dormant execution files fail closed с typed boundary reason.

**Given** Public Capture configuration и runtime manifest
**When** оператор выбирает публичные Hyperliquid/Lighter feeds
**Then** runtime допускает только credential-free discovery, public streaming и append-only capture responsibilities
**And** books, opportunities, economics, strategies, portfolio и verdict ownership отсутствуют из reachable runtime graph.

**Given** retained Go reference invariants
**When** conformance/retirement status проверяется
**Then** Go остаётся `TEST_ONLY_EXECUTABLE_SPEC`, исключённым из Stage-A source closure, binaries, dependencies и layers
**And** каждый retirement candidate требует map invariant -> versioned contract -> Python implementation -> negative tests -> exact-SHA Claw receipt -> independent review; отсутствие evidence блокирует retirement, но никогда не делает Go deployable.

**Given** изменения Story 1.3
**When** выполняется её обязательный exact-SHA Claw validation
**Then** focused RED/GREEN tests, installed-artifact boundary tests, dependency-DAG/orphan checks и independent security review завершаются успешно
**And** traceability связывает FR16, NFR1-NFR4, NFR8-NFR21, NFR27-NFR41 и AR1-AR5/AR8-AR11 с canonical owner, тестами, Claw receipt, artifact boundary и rollback/replacement evidence.

### Story 1.4: Зарегистрировать immutable CaptureRun и evidence до partition admission

As an внутренний оператор/исследователь,
I want чтобы каждая capture-сессия и каждый принадлежащий ей evidence-объект сначала получали однозначную unpartitioned identity,
So that partitioned payload нельзя записать без доказуемого владельца и полного пути к исходному запуску.

**Acceptance Criteria:**

**Given** новая публичная capture-сессия с exact collector/config/schema identities
**When** Public Capture открывает сессию
**Then** PostgreSQL создаёт ровно один immutable unpartitioned `CaptureRun` root в состоянии `OPEN` с уникальным `capture_run_id`
**And** повторная регистрация той же session identity либо возвращает тот же согласованный root, либо fail closed при несовпадающем содержимом; молчаливое создание второго root запрещено.

**Given** evidence-объект, принадлежащий открытому `CaptureRun`
**When** объект допускается к хранению
**Then** его immutable unpartitioned registry row с `node_id`, `capture_run_id`, node kind, schema/version и semantic hash существует до вставки payload в любую day partition
**And** foreign-key/constraint authority отвергает partition payload без registry row, с неизвестным run, с несовпадающим owner или с повторно использованным `node_id`.

**Given** зарегистрированный `CaptureRun` или capture node
**When** runtime пытается изменить immutable identity, owner, schema identity или semantic hash прямым DML либо через неразрешённый путь
**Then** операция атомарно отклоняется
**And** Public Capture runtime role не имеет table ownership, direct update/delete, sequence или schema-creation privileges.

**Given** clean digest-pinned PostgreSQL 16 и 17 databases
**When** exact-SHA Claw запускает migration, schema, positive-admission и negative-orphan tests
**Then** обе версии подтверждают unpartitioned root/registry authority и отсутствие partition-only или application-precheck обхода
**And** traceability связывает FR15 и FR25 с NFR6, NFR15-NFR21, NFR27-NFR34, NFR38-NFR41 и AR5/AR8-AR10; rollback migration работает только до durable evidence и отказывается удалять непустые roots без явно проверенного replacement path.

### Story 1.5: Связать evidence типизированными edges и глобальными logical keys

As an внутренний оператор/исследователь,
I want чтобы происхождение, уникальность и замещение каждого evidence-объекта проверялись одной graph authority,
So that в наборе данных не возникали dangling nodes, скрытые дубликаты, циклы или неоднозначные преемники.

**Acceptance Criteria:**

**Given** два зарегистрированных evidence nodes
**When** Public Capture создаёт edge между ними
**Then** edge ссылается foreign keys на оба unpartitioned registry endpoints и указывает versioned edge kind/contract
**And** отсутствующий endpoint, запрещённая комбинация node kinds, несовместимая contract version или неразрешённая cross-run связь fail closed до появления edge.

**Given** node с declared logical-key scope
**When** logical key регистрируется для этого node
**Then** одна unpartitioned authority обеспечивает глобальную уникальность ключа внутри объявленного scope независимо от day partition
**And** дубликат из другой partition, concurrent transaction или application-side precheck отклоняется базой данных и не создаёт payload либо edge.

**Given** `derived_from` или `supersedes` lineage
**When** добавляется новый lineage edge
**Then** graph остаётся acyclic и каждый superseded node имеет не более одного прямого successor в той же semantic lineage
**And** попытка создать цикл либо конкурирующего successor не выбирает победителя автоматически, а создаёт typed blocking conflict evidence или полностью отклоняет атомарную операцию согласно frozen contract.

**Given** будущая необходимость связать Capture, FrozenPackageReceipt, Analysis или Retention roots
**When** edge kind не имеет заранее versioned cross-root contract с разрешёнными endpoint/root types
**Then** ownership transfer, root reopening и неявная cross-root связь запрещены
**And** текущая история публикует расширяемый contract interface, но не создаёт будущие root tables, writers или разрешения раньше возникновения соответствующей capability.

**Given** clean digest-pinned PostgreSQL 16 и 17 databases
**When** exact-SHA Claw запускает migration, concurrent duplicate-key, dangling-edge, type-mismatch, cross-run, cycle и competing-successor tests
**Then** обе версии выдают одинаковые typed результаты и graph/orphan checker подтверждает связность slice
**And** traceability связывает FR26, FR27 и FR32, а также contract-часть FR39, с NFR15-NFR25, NFR27-NFR34, NFR40-NFR41 и AR4/AR8-AR10; rollback не удаляет непустую lineage authority без проверенного replacement path.

### Story 1.6: Записывать capture evidence только через атомарный constrained writer

As an внутренний оператор/исследователь,
I want чтобы admission каждого capture evidence-объекта выполнялась одной атомарной операцией с каноническим временем,
So that частичная запись, обход graph invariants или влияние host/audit time не могли изменить evidence и последующий replay.

**Acceptance Criteria:**

**Given** открытый `CaptureRun` и валидный evidence envelope
**When** Public Capture вызывает единственный разрешённый writer contract
**Then** одна transaction блокирует требуемый run authority и атомарно проверяет root state, registry identity, logical key, semantic hash, typed edges и payload admission
**And** ошибка любого шага откатывает registry, key, edges и payload целиком без частичного durable state.

**Given** Public Capture runtime database role
**When** проверяются grants и все доступные database paths
**Then** роль имеет только минимальный `CONNECT`/`USAGE` и `EXECUTE` утверждённого writer interface
**And** direct table DML, sequence privileges, ownership, role inheritance, schema creation, alternate writer functions и обход через mutable views отсутствуют и подтверждены negative tests.

**Given** evidence envelope с `effective_at_evidence_time`, source sequence/index и `recorded_at_audit_time`
**When** вычисляется canonical semantic hash и порядок replay
**Then** hashed identity включает evidence-effective time и требуемые source identity/sequence/payload fields
**And** audit/insertion time хранится отдельно, не входит в semantic hash и не влияет на ordering, duplicate detection, economics либо deterministic output.

**Given** две записи с одинаковой semantic identity, но разным audit time, либо с одинаковым audit time и разным effective identity
**When** writer обрабатывает их последовательно или конкурентно
**Then** решение о duplicate/conflict определяется только canonical identity и declared logical-key contract
**And** изменение host clock, transaction order или retry не меняет canonical result.

**Given** clean digest-pinned PostgreSQL 16 и 17 databases
**When** exact-SHA Claw запускает writer atomicity, privilege-denial, concurrent admission, rollback-on-error и time-determinism tests
**Then** обе версии дают эквивалентные результаты без skipped database tests
**And** traceability связывает FR28 и FR34 с NFR6, NFR15-NFR24, NFR27-NFR34, NFR38-NFR41 и AR5/AR8-AR10; replacement/rollback сохраняет уже принятый append-only evidence и не открывает DML bypass.

### Story 1.7: Race-safe запечатать CaptureRun и зафиксировать terminal identity

As an внутренний оператор/исследователь,
I want атомарно закрыть capture-сессию и получить неизменяемую terminal identity,
So that последующий frozen package относится к точному завершённому node set и никакая поздняя запись не меняет исходный evidence.

**Acceptance Criteria:**

**Given** открытый `CaptureRun` с завершённым capture-owned graph
**When** оператор инициирует terminalization через утверждённый seal contract
**Then** seal блокирует ту же unpartitioned run row, что и admission writer, проверяет обязательный pre-seal capture replay-integrity receipt и graph closure
**And** записывает expected/observed counts, terminal epochs/indices, canonical time bounds, complete node-set identity и canonical capture terminal hash перед переходом root в `SEALED`.

**Given** admission и seal выполняются конкурентно
**When** обе transaction претендуют на один `CaptureRun`
**Then** admission либо полностью фиксируется до seal и входит в counts/node set/hash, либо выполняется после seal и полностью отклоняется
**And** ни один registry, logical-key, edge, payload или lifecycle write не может commit через границу terminalization.

**Given** sealed `CaptureRun`
**When** любой capture или analysis path пытается добавить либо изменить принадлежащий capture payload, registry row, logical key, edge, lifecycle record, terminal metadata или replay receipt
**Then** операция fail closed с typed post-seal reason
**And** отдельная будущая `AnalysisRun` никогда не получает ownership или append path под `CaptureRun`.

**Given** sealed `CaptureRun`, готовый к будущему export
**When** seal boundary публикует terminal identity для freeze pipeline
**Then** он выдаёт exact terminal hash и complete capture node-set identity как обязательные candidate-export inputs
**And** VERIFIED `FrozenPackageReceipt` на этом шаге не создаётся: его admission остаётся запрещённым до успешной полной semantic validation под отдельным versioned freeze contract.

**Given** clean digest-pinned PostgreSQL 16 и 17 databases
**When** exact-SHA Claw запускает seal/admission race, post-seal mutation, incomplete-closure, terminal-hash и frozen-receipt mismatch tests
**Then** обе версии демонстрируют одинаковую сериализацию и отсутствие skipped database tests
**And** traceability связывает FR29 и FR33, а также receipt-boundary часть FR30/FR39, с NFR6, NFR15-NFR24, NFR27-NFR34, NFR36-NFR41 и AR5/AR8-AR10; rollback не может удалить или reopen sealed root и сохраняет terminal evidence.

### Story 1.8: Читать capture evidence через deterministic least-privilege PostgreSQL contract

As an внутренний оператор/исследователь,
I want получать capture evidence через стабильный deterministic read-only PostgreSQL interface,
So that анализ можно воспроизвести без доступа к writer paths или зависимости от физической раскладки таблиц.

**Acceptance Criteria:**

**Given** зарегистрированный capture evidence graph
**When** canonical `EvidenceReader` читает PostgreSQL projections
**Then** versioned views возвращают manifest, control evidence, raw envelopes/batches, mapping, quality и terminal metadata в полностью определённом canonical порядке
**And** physical partition order, query plan, audit time и insertion order не меняют результат.

**Given** Analyzer database role
**When** проверяются effective privileges и reachable database objects
**Then** роль имеет только требуемые `CONNECT`, schema `USAGE` и deterministic-view `SELECT`
**And** base-table DML, sequence access, writer/seal function `EXECUTE`, ownership, inheritance, mutable views и alternate mutation paths отклоняются.

**Given** отсутствующая provenance, неизвестная schema/edge version, неполный node set либо unsealed run
**When** reader запрашивает binding dataset
**Then** reader fail closed с typed contract/integrity reason и не выдаёт частичный dataset как complete
**And** read-only failure не изменяет capture graph и не создаёт AnalysisRun.

**Given** clean digest-pinned PostgreSQL 16 и 17 databases
**When** exact-SHA Claw запускает clean migrations, deterministic-view ordering, role/grant denial и reader-contract tests
**Then** обе версии возвращают byte-equivalent canonical records без skipped integration tests
**And** traceability связывает FR17, FR35 и FR36 с NFR6, NFR15-NFR24, NFR27-NFR41 и AR5/AR8-AR10; rollback сохраняет versioned reader compatibility либо блокируется до появления replacement view contract.

### Story 1.9: Экспортировать и семантически проверить immutable frozen package

As an внутренний оператор/исследователь,
I want экспортировать sealed CaptureRun в независимо проверяемый frozen package,
So that финальный анализ опирается на переносимый tamper-evident dataset, эквивалентный PostgreSQL evidence authority.

**Acceptance Criteria:**

**Given** sealed `CaptureRun` с terminal hash, complete node set и pre-seal replay-integrity closure
**When** Public Capture export boundary создаёт frozen package
**Then** package использует canonical member names/encoding/order, связывает exact run/terminal/node-set/schema/collector/config identities и вычисляет member hashes и package root hash
**And** export не импортирует Analyzer application, не создаёт analyzer replay и не изменяет sealed CaptureRun.

**Given** candidate frozen package
**When** independent semantic validator проверяет его
**Then** он парсит каждый envelope, recomputes payload/mapping/quality hashes и проверяет run, venue, epoch, sequence/index, canonical time, counts, bounds, duplicate logical keys, lifecycle, soak, decoder-observation, connection и pre-seal replay-integrity closure
**And** missing, extra, reordered, duplicated, cross-run, out-of-bounds, hash-mismatched или malformed evidence приводит к `INVALID_DATASET`, а не к частичному успеху.

**Given** semantic validation прошла
**When** регистрируется `FrozenPackageReceipt`
**Then** отдельный immutable receipt связывает retrievable package URI/object identity, package hash, sealed capture terminal hash и complete capture node set
**And** receipt не содержит post-package analyzer replay nodes и не переносит ownership либо writer rights.

**Given** PostgreSQL reader и frozen-package reader над одним sealed run
**When** оба реализуют sole versioned `EvidenceReader` contract
**Then** они выдают эквивалентные canonical evidence streams и terminal metadata
**And** повторное чтение в fresh processes не зависит от сети, host clock, filesystem enumeration order или repository cwd.

**Given** exact-SHA Claw validation
**When** выполняются tamper corpus, semantic mismatch, database-to-package equivalence и installed-artifact tests
**Then** package/reader slice проходит на clean PostgreSQL 16/17 и в isolated credential-free sandbox
**And** traceability связывает FR17, FR29, FR30 и применимую часть FR31 с NFR6, NFR15-NFR24, NFR27-NFR41 и AR3/AR5/AR8-AR10; rollback сохраняет receipt/package и создаёт superseding export вместо перезаписи.

### Story 1.10: Разрешать retention только через verified FrozenPackageReceipt

As an внутренний оператор/исследователь,
I want удалять или отсоединять raw storage только после независимо проверенного export receipt,
So that retention никогда не уничтожает единственный воспроизводимый источник evidence.

**Acceptance Criteria:**

**Given** sealed `CaptureRun` без retrievable independently verified `FrozenPackageReceipt`
**When** запрашивается drop, detach, expire или иная loss-of-availability операция над raw partition/object
**Then** операция fail closed до любого storage mutation
**And** наличие только package path, непроверенного hash либо несвязанного receipt не удовлетворяет gate.

**Given** sealed `CaptureRun` и valid retrievable receipt
**When** авторизованный retention boundary начинает операцию
**Then** создаётся отдельный immutable `RetentionAction` root со своей registry, logical-key scope, writer privilege и state machine
**And** versioned typed edges связывают его с exact CaptureRun и receipt без ownership transfer, root reopening или append под capture namespace.

**Given** RetentionAction
**When** storage mutation завершается либо терпит частичную/полную ошибку
**Then** action записывает exact authorization, affected partitions/objects, precondition identities, result и retention-evidence hash, затем terminally seals
**And** retry является idempotent либо создаёт явно связанный новый action; он не переписывает предыдущий result.

**Given** package становится недоступен, receipt mismatch обнаружен либо affected-object set изменился до mutation
**When** retention повторно проверяет preconditions
**Then** mutation блокируется и failure evidence сохраняется append-only
**And** recovery использует сохранённый verified package или exact prior storage identity, но никогда не реконструирует историю путём изменения sealed roots.

**Given** exact-SHA Claw validation на clean PostgreSQL 16/17
**When** выполняются missing/unreachable/mismatched-receipt, unauthorized-object, retry, partial-failure и cross-root privilege tests
**Then** retention gate одинаково fail closed на обеих версиях и не затрагивает Analyzer либо unrelated services
**And** traceability связывает FR31, FR38 и оставшуюся часть FR39 с NFR6, NFR15-NFR24, NFR27-NFR41, NFR47 и AR5/AR8-AR10; rollback/recovery evidence остаётся связным и без orphan nodes.

## Epic 2: Оператор воспроизводит рынок и измеряет исполнимую cross-venue экономику

Оператор может из проверенного evidence детерминированно восстановить
экономически эквивалентные инструменты и fail-closed книги, а затем измерить
полную исполнимую стоимость входа и выхода по обеим площадкам без заявления о
жизнеспособности стратегии.

**Implementation prerequisite:** Epic 1 предоставляет verified frozen package и
sole `EvidenceReader`; exact-SHA validation продолжает использовать только M6
Task 1 trusted disposable Claw controller.

### Story 2.1: Сопоставить инструменты по exact economic identity

As an внутренний оператор/исследователь,
I want анализировать только доказанно экономически эквивалентные инструменты с точной арифметикой,
So that совпадающий ticker или float rounding не создавали ложную cross-venue возможность.

**Acceptance Criteria:**

**Given** verified evidence для Hyperliquid и Lighter instruments
**When** Read-Only Analyzer строит economic identity mapping
**Then** identity включает underlying, product/payoff kind, multiplier, price/quantity units, quote, settlement/collateral, venue instrument ID, validity interval, schema/version и provenance hashes
**And** ticker equality без полного совпадения contract fields никогда не считается достаточной mapping authority.

**Given** price, quantity, fee, funding или P&L input
**When** contracts декодируют и нормализуют значение
**Then** расчёты используют canonical exact decimal, fixed-point или rational representation с явными units и rounding rules
**And** binary floats, NaN/Infinity, ambiguous scale, unknown multiplier либо incompatible settlement fail closed до reconstruction/economics.

**Given** mapping conflict, overlapping validity, missing provenance либо несколько допустимых economic identities
**When** Analyzer выбирает identity для binding evidence
**Then** создаётся typed unresolved/conflict result и downstream book/economics admission блокируется
**And** latest-wins, ticker fallback, averaging и implicit coercion запрещены.

**Given** audited legacy analyzer fragments и PR #21 head `7fe6918690f8bc1da5826c67e3619de4126e4f54`
**When** reusable exact contracts/evidence code мигрируется в canonical Analyzer/Contracts distributions
**Then** каждый retained blob связывается с source commit/blob, stable requirement, rewrite rule и installed-namespace tests
**And** whole-branch merge, conflicting workflow/config import, duplicate `multi_exchange_engine` owner или unprovenanced copy запрещены; rejected material сохраняется как quarantined provenance.

**Given** installed Read-Only Analyzer artifact
**When** exact-SHA Claw выполняет contract, malformed-number, mapping-conflict и capability-boundary tests
**Then** artifact содержит `mee_readonly_analyzer` и pure `mee_contracts`, но не capture writer, venue network client, private/trading/n8n/Go execution capability
**And** traceability связывает FR19 и FR20 с NFR1-NFR9, NFR15-NFR24, NFR27-NFR41 и AR1-AR5/AR8-AR10; prior mapping remains provenance and correction uses explicit supersession.

### Story 2.2: Детерминированно восстановить fail-closed venue books

As an внутренний оператор/исследователь,
I want восстанавливать книгу только из authoritative snapshot и непрерывной venue-valid последовательности,
So that gaps, reconnects и malformed updates не превращались в исполнимую ликвидность.

**Acceptance Criteria:**

**Given** verified stream для одного mapped instrument/connection epoch
**When** Analyzer получает authoritative snapshot и последующие venue-valid updates
**Then** он создаёт deterministic book checkpoints только после snapshot и непрерывно применяет monotonic sequence/index transitions
**And** каждый checkpoint связан с exact envelope/node, mapping, decoder/schema и reconstruction algorithm identities.

**Given** reconstructed bid/ask levels
**When** checkpoint проходит admission
**Then** prices и quantities положительны и exact, sides строго упорядочены, duplicate levels нормализованы только по versioned venue rule, а spread не crossed
**And** invalid level, impossible deletion, unsupported transition или crossed result закрывает active reconstruction epoch.

**Given** gap, regression, duplicate с несовпадающим payload, reconnect или malformed frame
**When** transition нарушает venue sequencing contract
**Then** текущий epoch становится invalid/closed и последующие incrementals не используются
**And** reconstruction возобновляется только с новым independently valid snapshot; stale state не переносится через reconnect.

**Given** PostgreSQL и frozen readers одного evidence package
**When** fresh Analyzer processes реконструируют checkpoints
**Then** canonical checkpoints, rejection reasons и epoch boundaries byte-identical
**And** exact-SHA Claw tests связывают FR21 и FR22 с FR17/FR19/FR20, NFR6, NFR15-NFR24, NFR27-NFR41 и AR8-AR10; rollback создаёт новый versioned reconstruction projection, не переписывая evidence.

### Story 2.3: Измерить полный четырёх-leg lifecycle через full-depth VWAP

As an внутренний оператор/исследователь,
I want измерять обе venue legs при входе и выходе по фактически доступной глубине,
So that top-of-book или неполный lifecycle не выдавались за исполнимую экономику.

**Acceptance Criteria:**

**Given** valid mapped books и requested exact quantity/notional
**When** Analyzer оценивает cross-venue lifecycle
**Then** он вычисляет full-depth VWAP отдельно для leg A entry, leg B entry, leg A exit и leg B exit с exact quantity consumption и declared rounding
**And** каждый fill slice связан с конкретным checkpoint, levels consumed, timestamp/sequence и economic identity.

**Given** недостаточная depth, invalid checkpoint, crossed book, stale/closed epoch либо несовместимые units на любой из четырёх legs
**When** выполняется pricing
**Then** весь lifecycle получает typed rejection и не производит partial executable result
**And** top-of-book, last-price, extrapolation, synthetic liquidity и quantity shrinking fallback запрещены.

**Given** обе возможные cross-venue directions и несколько frozen notionals
**When** запускается measurement
**Then** каждая direction/notional оценивается независимо по одинаковому deterministic contract, включая отрицательную экономику
**And** результат остаётся economics measurement: он не называется opportunity, не создаёт strategy episode/verdict и не отправляет order command.

**Given** exact-SHA Claw validation
**When** выполняются golden depth ladders, rounding boundaries, insufficient-depth, four-leg provenance и fresh-process determinism tests
**Then** expected VWAP/rejections exact и независимы от reader/backend/host clock
**And** traceability связывает FR23 и повторно проверяет FR19-FR22 через NFR6, NFR15-NFR24, NFR27-NFR41 и AR8-AR10; algorithm replacement создаёт versioned superseding outputs.

## Epic 3: Оператор оценивает frozen shadow-стратегии с полными costs и capital constraints

Оператор может прогнать basis и realized-funding shadow-стратегии, увидеть
полные затраты, задержки, неудачные попытки, блокировки капитала, концентрацию
и диагностический paired-basis trailing, не создавая ордеров и не смешивая
карантинные стратегии с binding verdict.

**Implementation prerequisite:** Epics 1-2 предоставляют verified frozen evidence,
exact identities, fail-closed books и four-leg pricing. Все проверки выполняются
на trusted exact-SHA Claw controller; retail UI и live/private execution не входят
в scope.

### Story 3.1: Заморозить admitted strategy universe и отдельные policy contracts

As an внутренний оператор/исследователь,
I want до acquisition зафиксировать стратегии, cells, capital weights и экономические политики,
So that наблюдаемый результат не мог изменить состав или правила проверяемой гипотезы.

**Acceptance Criteria:**

**Given** owner-approved Stage-A-v2 configuration до начала evidence window
**When** создаётся strategy manifest
**Then** closed set admitted `(strategy, asset, direction)` cells, deterministic capital weights, notionals, fee cases, delays, thresholds, episode rules, residual limits и policy versions canonicalized и hash-bound
**And** разрешены binding basis convergence и realized funding carry; paired-basis trailing помечен `DIAGNOSTIC_NON_BINDING`.

**Given** strategy domain model
**When** contracts устанавливаются независимо
**Then** signal/strategy, inventory, exit, execution-counterfactual, cost и portfolio policies являются отдельными versioned contracts
**And** ни один contract не возвращает order/cancel/private command; разрешённый output type только immutable shadow simulation/evidence.

**Given** acquisition уже начался
**When** предлагается удалить/добавить cell, изменить weight/threshold/cost/baseline либо выбрать параметры по observed economics
**Then** binding configuration остаётся неизменной, а попытка fail closed либо создаёт новый future experiment identity
**And** post-hoc sensitivity допускается только как clearly labelled diagnostic, не меняющий binding aggregate/verdict.

**Given** missing approval, unknown enum, weight mismatch, duplicate cell, unsupported strategy или noncanonical numeric input
**When** manifest валидируется
**Then** acquisition/analysis admission блокируется с typed configuration reason
**And** exact-SHA Claw tests связывают FR40, FR44 и FR47 с AR4, NFR15-NFR26, NFR27-NFR41 и AR8-AR10; replacement manifest имеет новую identity и не переписывает прежний.

### Story 3.2: Атрибутировать delayed legs, failures, residuals и полный cost ledger

As an внутренний оператор/исследователь,
I want видеть полную стоимость каждой успешной и неуспешной counterfactual попытки,
So that latency, residual risk или скрытые расходы не превращали отрицательную гипотезу в положительную.

**Acceptance Criteria:**

**Given** admitted shadow attempt и frozen delay/cost policies
**When** моделируются entry и exit обеих venue legs
**Then** каждая leg выбирает собственный evidence checkpoint после declared delay и получает independent fill/rejection outcome
**And** simultaneous/atomic fill не предполагается, а missing delayed checkpoint или depth фиксируется как failed attempt.

**Given** asymmetric fills либо failed second leg
**When** возникает residual exposure
**Then** deterministic residual-neutralization/rebalance policy использует только последующий valid executable evidence, учитывает additional delay/depth/fees и записывает bounded либо unresolved residual result
**And** unresolved neutralization fail closed и не маскируется предположением о бесплатном close.

**Given** completed или failed attempt
**When** строится immutable cost ledger
**Then** отдельно атрибутируются entry/exit fees каждой leg, realized funding, forecast funding label, slippage/depth, delay decay, residual neutralization, rebalance, failed-attempt cost, holding/inventory и frozen infrastructure cost
**And** отсутствующий обязательный cost/provenance field сохраняет сам attempt и переводит весь run в `INVALID_DATASET` либо `INSUFFICIENT_EVIDENCE`; исключить attempt, заменить расход нулём или пересчитать aggregate без него запрещено.

**Given** fresh-process replay одного attempt
**When** exact-SHA Claw выполняет independent-delay, failed-leg, residual, fee-sign, cost-sum и provenance tests
**Then** ledger и reason codes byte-identical и не зависят от host clock/network
**And** traceability связывает FR41/FR42/FR49 и применимые FR40/FR44 с NFR6, NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR10; corrections supersede ledgers без rewrite.

### Story 3.3: Выделить независимые episodes и блокировать virtual capital

As an внутренний оператор/исследователь,
I want считать только независимые opportunities и не переиспользовать занятый капитал,
So that overlapping signals и duplicate frames не умножали economics искусственно.

**Acceptance Criteria:**

**Given** ordered strategy signals и frozen episode policy
**When** tracker формирует episodes
**Then** deterministic identity объединяет относящиеся к одной возможности frames/signals, а независимость определяется predeclared start/end/cooldown rules
**And** duplicate/replayed inputs не создают новый episode либо второй P&L.

**Given** несколько admitted cells конкурируют за ограниченный virtual capital
**When** начинается attempt
**Then** capital allocation использует frozen weights и deterministic priority, а allocated capital остаётся locked до exit, failed-attempt completion и residual neutralization
**And** rejected из-за capital lock signal сохраняется как attributable non-executed attempt, если это требует frozen policy.

**Given** episode завершён успешно, неуспешно либо остаётся unresolved
**When** формируется episode ledger
**Then** он содержит все attempts, time/capital bounds, cost-ledger links и typed terminal state
**And** unresolved/open episode не считается completed independent lifecycle и не исчезает из sufficiency/concentration evidence.

**Given** exact-SHA Claw validation
**When** выполняются overlap, duplicate, cooldown, priority, capital-reuse, failure и concentration-input tests
**Then** episode counts и capital timeline deterministic
**And** traceability связывает FR48 и применимую FR49 с NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR10; policy changes create superseding experiment outputs.

### Story 3.4: Оценить executable basis-convergence lifecycle

As an внутренний оператор/исследователь,
I want оценить вход и выход basis-convergence по independent delayed executable books,
So that hypothesis учитывает реальную глубину и распад edge между двумя legs.

**Acceptance Criteria:**

**Given** admitted basis cell, valid episode и frozen entry/exit policy
**When** basis signal проходит predeclared admission threshold
**Then** strategy оценивает обе directions и весь four-leg lifecycle через full-depth VWAP, independent delays и complete cost ledger
**And** result связывает signal, checkpoints, fills/rejections, capital locks, residual outcomes и policy/config hashes.

**Given** convergence, fixed-time, remaining-basis либо safety exit condition
**When** exit policy срабатывает
**Then** применяется deterministic declared precedence data/mapping invalid -> residual/margin safety -> max hold -> basis widening -> strategy exit
**And** стратегия не выбирает лучший exit задним числом и не использует future evidence.

**Given** negative edge, failed leg, insufficient depth, widened basis или expensive neutralization
**When** attempt завершается
**Then** negative/failed economics полностью сохраняется и входит в downstream aggregate по frozen policy
**And** output остаётся shadow evidence и не создаёт execution command либо eligibility for live trading.

**Given** exact-SHA Claw validation
**When** выполняются golden convergence, widening, delayed-leg, exit-precedence, negative-edge и no-lookahead tests
**Then** basis episode outputs deterministic и exact
**And** traceability связывает FR40, FR41, FR44 и применимые FR48/FR49 с NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR10.

### Story 3.5: Оценить realized-funding carry по фактическим settlements

As an внутренний оператор/исследователь,
I want отделить реализованные funding cashflows от прогнозов и полной holding economics,
So that funding hypothesis подтверждалась только фактически наблюдаемыми settlement evidence.

**Acceptance Criteria:**

**Given** admitted funding cell и signed venue settlement evidence
**When** funding lifecycle моделируется
**Then** realized cashflow связывается с exact venue/instrument, rate/amount, sign, schedule, effective interval, position/notional и evidence hash
**And** forecast/indicative rate хранится отдельным diagnostic type и никогда не заменяет realized settlement.

**Given** funding episode
**When** вычисляется net economics
**Then** ledger включает entry/exit VWAP, basis movement, holding time, fees, delay, residual/rebalance, capital locks и realized funding каждой venue leg
**And** missing/ambiguous settlement, sign, interval либо position attribution делает funding reason insufficient/invalid.

**Given** положительный forecast и отрицательный или отсутствующий realized cashflow
**When** episode/aggregate строится
**Then** forecast не создаёт positive funding P&L и не удовлетворяет funding continuation evidence
**And** completed и failed funding attempts остаются в admitted-cell slice.

**Given** exact-SHA Claw validation
**When** выполняются sign/schedule, settlement-boundary, forecast-separation, missing-cashflow, basis/holding-cost и replay tests
**Then** funding outputs deterministic и provenance-complete
**And** traceability связывает FR40, FR42, FR44 и применимые FR48/FR49 с NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR10.

### Story 3.6: Сравнить paired-basis trailing только как diagnostic

As an внутренний оператор/исследователь,
I want сравнить trailing exit по реализованной paired-basis convergence,
So that потенциальное улучшение exit policy измерялось без влияния на binding Stage-A решение.

**Acceptance Criteria:**

**Given** completed basis episodes и frozen diagnostic trailing configuration
**When** Analyzer запускает counterfactual trailing
**Then** trail отслеживает только synchronized executable paired-basis/net-capture measure с independent delayed exits и complete costs
**And** single-asset price trail, lookahead peak, unfilled top-of-book и free cancellation assumptions запрещены.

**Given** diagnostic result
**When** он сравнивается с frozen primary exits
**Then** отчёт показывает non-inferiority, tail/drawdown, missed exits и regime slices как diagnostic evidence
**And** trailing не изменяет admitted primary attempts, portfolio aggregate, sufficiency, binding reasons или verdict bytes.

**Given** отрицательный cell либо positive trailing sensitivity
**When** downstream decision consumes strategy evidence
**Then** отрицательный cell остаётся в frozen aggregate, а trailing output недоступен через binding verdict input type
**And** попытка такого import/type edge блокируется graph/capability tests.

**Given** exact-SHA Claw validation
**When** выполняются no-lookahead, delayed-exit, full-cost, binding-isolation и report-label tests
**Then** diagnostic output deterministic и физически отделён от verdict inputs
**And** traceability связывает FR43, FR44, FR47 и применимую FR49 с NFR15-NFR26, NFR27-NFR41 и AR4/AR8-AR10.

### Story 3.7: Собрать frozen-universe portfolio aggregate без masking

As an внутренний оператор/исследователь,
I want получить один reconciled aggregate по всему заранее admitted universe,
So that прибыльные survivors не скрывали missing, failed или отрицательные cells.

**Acceptance Criteria:**

**Given** frozen manifest всех admitted cells и capital weights
**When** portfolio aggregator consumes strategy episodes
**Then** он включает каждый completed и failed attempt каждого admitted cell с frozen weight и deterministic ordering
**And** observed economics не может удалить, добавить, перевзвесить или переименовать cell.

**Given** отсутствующая обязательная cell, unreconciled attempt, open residual либо incomplete required evidence
**When** aggregate строится
**Then** aggregate получает typed invalid/insufficient state и не пересчитывается по survivors
**And** negative cell сохраняется внутри aggregate, но сама по себе не создаёт отдельный binding verdict.

**Given** complete aggregate
**When** вычисляются portfolio evidence metrics
**Then** total/median net, notional cases, delay/fee cases, independent episode count, capital utilization и largest-episode concentration exact и reconciled с per-cell slices
**And** per-cell slices обязательны для объяснимости, но помечены non-binding; их сумма/weights сходятся с aggregate без остатка.

**Given** minimum episode contract
**When** проверяется episode count
**Then** minimum 20 independent episodes применяется к aggregate, если до acquisition не утверждён отдельный per-cell minimum
**And** exact-SHA Claw tests связывают FR40, FR47, FR48 и FR49 с AR4, NFR15-NFR26, NFR27-NFR41 и AR8-AR10; aggregate algorithm/version входит в provenance.

### Story 3.8: Доказать quarantine unsupported strategy runtime

As an внутренний оператор/исследователь,
I want видеть проверяемое доказательство, что импортированные и live-oriented стратегии не входят в Stage A,
So that исследовательские фрагменты не превращались в активные боты по совпадению имён или imports.

**Acceptance Criteria:**

**Given** installed Analyzer и Public Capture artifacts, manifests и runtime graph
**When** выполняется quarantine boundary scan
**Then** grid, DCA, Infinity Grid, Solana-chain runtime, maker-fill claims, legacy asset bots, private adapters и execution libraries отсутствуют из dependencies, files, imports, entry points, configuration selectors и reachable symbols
**And** research/archive nodes сохраняют provenance и явно классифицированы `QUARANTINED_HYPOTHESIS` или `ARCHIVE`, не ACTIVE.

**Given** запрос на promotion quarantined strategy
**When** отсутствует отдельный approved actor/outcome, strategy manifest, economic contract, evidence gate, security/capability review и owner approval
**Then** promotion fail closed и active graph не изменяется
**And** reuse допустим только как provenance-labelled test/research input без private protocol, wallet, signer или live authority.

**Given** maker-first, polling bot либо иной imported method
**When** отсутствуют queue/fill/cancel/adverse-selection measurements и frozen evidence contract
**Then** метод остаётся diagnostic/quarantined и не получает simulated fill либо binding economics authority
**And** отсутствие retail demand/UX не считается дефектом Stage A.

**Given** exact-SHA Claw installed-artifact validation и independent review
**When** проверяются manifests, transitive dependencies, imports, OCI layers, strings/symbols, network surface и graph ownership
**Then** capability absence доказана на собранных артефактах, а не только source grep
**And** traceability связывает FR40, FR45 и FR46 с NFR1-NFR5, NFR13-NFR26, NFR27-NFR41 и AR1-AR10; quarantine removal требует отдельной future approval chain.

## Epic 4: Оператор получает воспроизводимое Stage A решение

Оператор получает запечатанный AnalysisRun, детерминированный replay и отчёт с
одним из четырёх взаимоисключающих решений Stage A, полностью связанным с
исходным evidence, конфигурацией, кодом, exact-SHA Claw gates, release/deploy
границами и rollback evidence; решение никогда не означает разрешение live
trading.

**Implementation prerequisite:** Epics 1-3 предоставляют verified package,
reconstruction и frozen aggregate. Stage A остаётся внутренним hypothesis test;
Claw допускает realtime apply/rollback только в изолированном test scope.

### Story 4.1: Создать и изолированно запечатать immutable AnalysisRun

As an внутренний оператор/исследователь,
I want записать все derived outputs под отдельным immutable AnalysisRun,
So that результат полностью воспроизводим и никогда не изменяет исходный CaptureRun.

**Acceptance Criteria:**

**Given** sealed `CaptureRun`, verified `FrozenPackageReceipt`, exact analyzer artifact/code и frozen config identities
**When** analysis начинается
**Then** создаётся отдельный immutable `AnalysisRun` root со своей registry, logical-key scope, versioned node kinds, analysis-only writer privilege и lifecycle state machine
**And** missing/mismatched capture terminal, package, artifact, code или config identity блокирует run creation.

**Given** open AnalysisRun
**When** reconstruction, quality, economics, strategy, portfolio, decision, replay или report evidence записывается
**Then** writer принимает только ANALYSIS-owned node kinds и declared typed input/derived edges
**And** никакая function/role не изменяет capture roots, registry, payload, receipt либо retention namespace.

**Given** complete analysis graph
**When** AnalysisRun seals
**Then** terminal document canonicalizes input identities, output/node counts, canonical bounds, graph root, output digest и analysis terminal hash
**And** post-seal analysis writes отклоняются; correction/re-run создаёт новый AnalysisRun, связанный provenance edge, а не reopen/rewrite.

**Given** clean PostgreSQL 16/17 и two fresh processes
**When** exact-SHA Claw запускает create/write/seal, cross-root denial, post-seal mutation и terminal-hash tests
**Then** CaptureRun counts/hashes неизменны, AnalysisRun outputs/terminal hashes deterministic и DB tests не skipped
**And** traceability связывает FR37 и основу FR18/FR24 с NFR6, NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR11; rollback создаёт новый run с prior artifact, не меняя существующий.

### Story 4.2: Выдать один Stage-A verdict по строгой fail-closed precedence

As an внутренний оператор/исследователь,
I want получить один typed verdict из frozen predicates,
So that invalid data, недостаточность и отрицательная экономика не смешивались и не интерпретировались как успех.

**Acceptance Criteria:**

**Given** AnalysisRun inputs
**When** существует package/hash/schema/provenance/closure/replay/mapping integrity failure
**Then** decision равен `INVALID_DATASET` и содержит только ordered closed-enum `INVALID_*` reasons
**And** economics и survivor aggregate не оцениваются как binding result.

**Given** dataset valid
**When** acquisition меньше семи calendar days, complete UTC days меньше пяти, strict healthy minutes ниже 95%, required mapping/fee cases отсутствуют, aggregate independent episodes меньше 20, admitted cell incomplete либо required realized funding evidence отсутствует
**Then** decision равен `INSUFFICIENT_EVIDENCE` и содержит только predicate-specific `INSUFFICIENT_*` reasons
**And** partial boundary days и forecast funding остаются diagnostic и не удовлетворяют gate.

**Given** dataset valid и sufficient
**When** frozen portfolio aggregate имеет non-positive total или median net, non-positive USD 1,000 net, negative USD 5,000 net, не выживает 300/500 ms delay или любой frozen fee case, либо largest-episode contribution не ниже 25%
**Then** decision равен `STOP` с only `STOP_*` reasons для всех failed binding predicates
**And** отрицательный отдельный cell не является самостоятельным verdict, но остаётся внутри aggregate с frozen weight.

**Given** dataset valid/sufficient и все binding aggregate predicates проходят exact boundaries
**When** evaluator завершает precedence INVALID -> INSUFFICIENT -> STOP -> EXTEND
**Then** decision равен только `EXTEND_LONGER_SHADOW` с `EXTEND_ALL_V2_GATES_PASS`
**And** `GO`, `NO_GO`, `KILL`, `plausible`, `inconclusive`, arbitrary reasons и mixed precedence classes невозможно сконструировать.

**Given** exact threshold boundaries
**When** exact-SHA Claw выполняет individual/combinatorial predicate tests
**Then** `0.95` health и `0` USD 5,000 net проходят соответствующие inclusive gates, `0` USD 1,000 net и concentration `0.25` дают STOP, а invalid всегда имеет высший precedence
**And** traceability связывает FR1-FR3, FR7-FR12 и применимые FR5/FR24 с AR4, NFR15-NFR26, NFR27-NFR41 и AR8-AR11.

### Story 4.3: Воспроизвести byte-identical report и analysis replay receipt

As an внутренний оператор/исследователь,
I want повторить анализ в двух чистых процессах и получить одинаковый evidence-linked report,
So that Stage-A решение можно независимо проверить без сети, host clock или скрытого state.

**Acceptance Criteria:**

**Given** verified frozen package, frozen config, exact analyzer identity и одна заранее созданная/hash-bound semantic `AnalysisRun` identity
**When** два fresh processes запускают final replay без network и host-clock access
**Then** canonical reconstruction/economics/portfolio/verdict/report bytes совпадают, как и graph root, output digest и AnalysisRun terminal hash
**And** оба процесса получают одинаковые explicit `analysis_run_id`, input/algorithm/config/code identities и canonical time inputs; independently generated run IDs, `PYTHONHASHSEED`, filesystem enumeration, locale, audit time и process order не могут менять semantic output.

**Given** report
**When** оператор проверяет любой aggregate metric, per-cell slice, failed attempt, reason или decision
**Then** существует complete path к AnalysisRun, policy/config, algorithm/code/artifact, FrozenPackageReceipt, CaptureRun terminal и raw evidence hashes
**And** per-cell slices reconciled с binding aggregate, diagnostic trailing явно отделён, а missing provenance делает run invalid.

**Given** replay receipt
**When** AnalysisRun seals
**Then** receipt связывает обе process receipt hashes, frozen package digest, capture terminal, analyzer/config/code identities, canonical output digest, graph root и terminal hash
**And** receipt относится только к AnalysisRun, не записывается в CaptureRun/frozen package и не создаётся при differing outputs.

**Given** exact-SHA Claw validation
**When** выполняются fresh-process, no-network/no-clock, reversed-input, different-hashseed, tamper и provenance-closure tests
**Then** deterministic replay доказан immutable receipts
**And** traceability полностью связывает FR5, FR18, FR24 и FR37 с NFR6, NFR15-NFR24, NFR27-NFR41 и AR4/AR8-AR11; replay correction создаёт новый AnalysisRun.

### Story 4.4: Ограничить решение внутренней Stage-A гипотезой

As an внутренний оператор/исследователь,
I want видеть точный смысл и границы Stage-A результата,
So that shadow economics не выдавалась за retail demand, production profitability или разрешение торговли.

**Acceptance Criteria:**

**Given** любой из четырёх Stage-A verdicts
**When** report и machine-readable decision публикуются
**Then** primary actor указан как internal operator/researcher, а outcome — reproducible evidence-backed STOP/EXTEND research decision
**And** документ явно говорит, что результат не разрешает private API, live trading, customer rollout, custody, Telegram/web authority или revenue claim.

**Given** `EXTEND_LONGER_SHADOW`
**When** оператор читает continuation target
**Then** target immutable равен 7-14 complete UTC days и минимум 100 independent completed lifecycles
**And** EXTEND никогда не синоним `GO`; первый live behavior требует отдельной будущей architecture/security/reconciliation/human authorization chain.

**Given** historical USD 10 PUMP/DOGE KILL/EXTEND material
**When** оно появляется в provenance/research
**Then** оно помечено `SUPERSEDED`, не смешивается с Stage-A-v2 universe/thresholds и не влияет на verdict
**And** replacement edge сохраняет историю без dual-active contract.

**Given** claims об external demand, willingness to pay, revenue или production profitability
**When** они входят в graph/report
**Then** каждый claim существует только как separate unsupported falsifiable Hypothesis с отдельными actor, outcome, metric, evidence и approval requirements
**And** отсутствие retail UX, market research или monetization evidence не блокирует честное завершение internal hypothesis test.

**Given** exact-SHA Claw graph/report tests и independent product/quant review
**When** проверяются wording, enum, authority edges и unsupported claims
**Then** traceability связывает FR4, FR6, FR8, FR12-FR14 с NFR7, NFR15-NFR26, NFR27-NFR41 и AR1-AR4/AR8-AR11
**And** изменение product meaning требует нового owner approval, а не code-only commit.

### Story 4.5: Зафиксировать versioned schemas causal release graph

As an внутренний оператор/исследователь,
I want проверять каждый release phase отдельным immutable contract,
So that candidate, promotion и deployment нельзя было смешать или создать задним числом.

**Acceptance Criteria:**

**Given** release contract package
**When** schemas и validators устанавливаются
**Then** candidate receipt, app-stack DB receipt, human promotion request, realized promotion receipt, final release receipt и deployment authorization имеют отдельные closed versioned schemas
**And** каждый downstream object hash-bound ссылается на exact predecessor identities и запрещает unknown/missing/extra authority fields.

**Given** causal chain candidate -> app-stack DB receipt -> promotion request -> promotion receipt -> final release -> deployment authorization
**When** object предлагается вне порядка либо с copied/placeholder receipt
**Then** validation fail closed до build/promotion/deploy mutation
**And** candidate не является promotion, final release не является deployment authorization, а rollback identity обязательна в final release.

**Given** valid и mixed-SHA/missing-predecessor fixtures
**When** exact-SHA Claw выполняет schema/canonical-hash/causality tests
**Then** valid chain deterministic, все invalid combinations отклоняются typed reasons
**And** traceability связывает NFR18, NFR24, NFR33, NFR42-NFR49 и AR6/AR8-AR11 с schemas, validators, tests и replacement compatibility.

### Story 4.6: Собрать и просканировать exact release candidate на Claw

As an внутренний оператор/исследователь,
I want получить immutable candidate из exact validated source SHA,
So that promotion рассматривает только reproducible artifacts с доказанной capability boundary.

**Acceptance Criteria:**

**Given** exact default-branch engine SHA и successful same-SHA validation receipts
**When** Claw строит release candidate
**Then** separately installable Capture и Analyzer artifacts/OCI identities собираются с pinned build inputs, dependency locks и configuration hashes
**And** installed-file/import/dependency/entry-point/layer proof подтверждает отсутствие private/trading/n8n/Go execution capability.

**Given** built candidate artifacts
**When** SBOM, vulnerability, deterministic-build и identity gates выполняются
**Then** immutable candidate receipt связывает exact source/tree, validation receipts, locks, configs, artifact digests, SBOM и scan results
**And** failed gate не публикует promotable candidate и cleanup удаляет isolated build resources без cross-project residue.

**Given** realtime candidate iterations на Claw
**When** agent накатывает либо откатывает build inputs в test namespace
**Then** каждый attempt получает отдельную identity/receipt и не перезаписывает previous candidate
**And** traceability связывает NFR2-NFR4, NFR13, NFR18, NFR27-NFR41 и AR5/AR8-AR11; mutable tags не являются identity authority.

### Story 4.7: Материализовать exact app-stack и доказать DB contract

As an внутренний оператор/исследователь,
I want проверить точный app-stack source и database boundary до promotion,
So that release не зависит от dirty checkout или ошибочного partition contract.

**Acceptance Criteria:**

**Given** exact private app-stack SHA
**When** trusted Claw workflow materialизует source
**Then** используется authenticated exact archive с token только в step environment, traversal/link и tree identity проверяются, persisted credentials отсутствуют
**And** dirty `/home/operator/app-stack` не fetch/reset/checkout/mutate.

**Given** app-stack с fix `3ce7e1f` либо independently reviewed equivalent
**When** isolated PostgreSQL 16/17 DB contract suite выполняется
**Then** receipt связывает exact app SHA, migrations, roles/grants, relkind=`r` table-partition scans, constrained writer, views и frozen-reader evidence без skipped tests
**And** index partitions не принимаются за table partitions, а missing equivalent evidence блокирует release.

**Given** PR #42-equivalent materialization repair и PR #39-equivalent no-push control
**When** app-stack contract проверяется
**Then** trusted exact archive repair предшествует no-push validation, automatic push deploy отсутствует
**And** exact app-stack DB receipt создаётся только после independent DevOps/data review; traceability связывает NFR42-NFR49 и AR6-AR11.

### Story 4.8: Авторизовать promotion и завершить final release receipt

As an внутренний оператор/исследователь,
I want явно связать candidate и app-stack evidence перед promotion,
So that deployable release имеет неразрывную human-approved causal lineage и точный rollback target.

**Acceptance Criteria:**

**Given** valid candidate receipt и exact app-stack DB receipt
**When** owner выдаёт human promotion request
**Then** request hash-bound связывает оба inputs, target environment class, allowed artifacts и previous rollback identity
**And** отсутствующая/несовпадающая approval identity либо stale input блокирует promotion.

**Given** valid promotion request
**When** Claw выполняет promotion
**Then** realized promotion receipt фиксирует фактически promoted immutable digests/identities и не доверяет requested values без post-action verification
**And** failure/partial promotion сохраняется evidence-linked и не создаёт final release.

**Given** realized promotion receipt
**When** final release завершается
**Then** final receipt связывает source, validations, scans, artifacts, app-stack contract, human request, realized promotion, config/schema compatibility и exact prior rollback digest
**And** independent DevOps/security review подтверждает NFR18, NFR24, NFR27-NFR49 и AR5-AR11; final receipt остаётся не-deployment authorization.

### Story 4.9: Развернуть и наблюдать только mee-a2 в изолированной Claw test среде

As an внутренний оператор/исследователь,
I want развернуть exact public-capture release только в изолированном `mee-a2` test boundary,
So that можно собирать Stage-A evidence и доказать semantic progress без влияния на другие сервисы.

**Acceptance Criteria:**

**Given** final release receipt и отдельная explicit deployment authorization
**When** controlled test deployment начинается
**Then** immutable exact app-stack archive/checkout проверяет engine/app SHAs, candidate/promotion/final receipt hashes, image digest, config hash, clock и DB contract
**And** dirty `/home/operator/app-stack` не fetch/reset/checkout/mutate, automatic push trigger отсутствует.

**Given** authorized deployment
**When** Compose применяется
**Then** target ограничен project `mee-a2` и public-capture services; n8n, unrelated bots/projects, private APIs и live trading не стартуют, не останавливаются и не перенастраиваются
**And** per-run networks, database/schema, volumes, secrets, ports и evidence paths изолированы от других Claw projects.

**Given** новый capture runtime
**When** post-deploy evidence собирается после полного UTC minute и заданного soak
**Then** receipt включает health, ready, WARMING/MEASURING/terminal state, nonzero expected/reporting/valid slots, feed/ownership/database status, image/config/source identity и current-run PostgreSQL evidence
**And** process-only health или endpoint reachability без semantic progress не считается успешным rollout.

**Given** failed start, DB contract, readiness, semantic-minute, soak или identity gate
**When** rollout evaluation завершается
**Then** candidate services останавливаются внутри `mee-a2`, success deployment receipt не создаётся, а failure evidence и exact prior-release identity сохраняются для recovery
**And** Story 4.9 независимо fail closed без mutation unrelated projects; восстановление prior release выполняется отдельной recovery capability.

**Given** successful test rollout на Claw
**When** independent SRE review проверяет deployment/telemetry graph
**Then** NFR42-NFR46, NFR48-NFR49 и AR6/AR7/AR9-AR11 имеют receipts для authorization, isolation и semantic evidence
**And** никакой test receipt не трактуется как production deployment или live-trading approval.

### Story 4.10: Восстановить exact prior mee-a2 release и доказать cleanup

As an внутренний оператор/исследователь,
I want откатить неуспешный или выбранный test rollout к точному предыдущему release,
So that realtime Claw эксперименты имеют независимо проверяемую recovery boundary и не теряют evidence.

**Acceptance Criteria:**

**Given** failed start, DB contract, readiness, semantic-minute, soak или identity gate
**When** rollback срабатывает либо оператор запрашивает realtime rollback
**Then** exact prior promoted digest/config восстанавливается только внутри `mee-a2`, failed release остаётся evidence-linked, а append-only CaptureRun data не переписывается
**And** cleanup receipt доказывает отсутствие orphan containers/networks/temp DB/resources и неизменность unrelated projects.

**Given** exact prior release несовместим со schema/config или его digest/receipt недоступен
**When** recovery preflight выполняется
**Then** destructive rollback блокируется, candidate остаётся stopped, а typed manual-recovery requirement сохраняется
**And** система не выбирает mutable tag, не переписывает database evidence и не затрагивает n8n/unrelated projects.

**Given** successful rollout/rollback exercise на Claw
**When** independent SRE review проверяет recovery graph
**Then** NFR42-NFR49 и AR6/AR7/AR9-AR11 имеют receipts для prior identity, rollback action, post-rollback health/evidence и cleanup
**And** recovery receipt не является production approval, а повторный rollout требует новой deployment authorization.
