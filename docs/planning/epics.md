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

### Epic 1: The operator obtains a reliable public evidence package

The operator can run public capture, obtain an immutable and complete
evidence set, safely seal, verify, freeze, and read it through
equivalent read-only interfaces without depending on the future analyzer.

**Implementation prerequisite:** Stories 1.1, 1.2 and 1.2A establish the
trusted source controller, disposable sandbox and reversible Claw host
transition. Story 1.3 remains blocked until their authority-NONE gates and
required self-validation evidence complete.

**Implementation prerequisite:** M0 policy/graph authority is complete before Story
1.1. Stories 1.1-1.2 create and self-validate the trusted controller/sandbox and are
mandatory prerequisites for Stories 1.3-1.10; local or historical runs are not
receipt evidence.

**FRs covered:** FR15, FR16, FR17, FR25-FR36, FR38, FR39.

### Epic 2: The operator reproduces the market and measures executable cross-venue economics

The operator can deterministically reconstruct economically equivalent
instruments and fail-closed books from verified evidence, then measure the
full executable cost of entry and exit across both venues without claiming
strategy viability.

**FRs covered:** FR19-FR23.

### Epic 3: The operator evaluates frozen shadow strategies with full costs and capital constraints

The operator can run basis and realized-funding shadow strategies, see
full costs, delays, failed attempts, capital locks, concentration,
and diagnostic paired-basis trailing without creating orders or mixing
quarantined strategies into the binding verdict.

**FRs covered:** FR40-FR49.

### Epic 4: The operator obtains a reproducible Stage A decision

The operator receives a sealed AnalysisRun, deterministic replay, and a report with
one of four mutually exclusive Stage A decisions, fully bound to
the original evidence, configuration, code, exact-SHA Claw gates, release/deploy
boundaries, and rollback evidence; the decision never authorizes live
trading.

**FRs covered:** FR1-FR14, FR18, FR24, FR37.

## Epic 1: The operator obtains a reliable public evidence package

The operator can run public capture, obtain an immutable and complete
evidence set, safely seal, verify, freeze, and read it through
equivalent read-only interfaces without depending on the future analyzer.

### Story 1.1: Bootstrap trusted default-branch PR identity controller

As an internal operator/researcher,
I want to bind validation to the exact open same-repository PR head and trusted default-branch workflow,
So that an untrusted payload or branch workflow cannot select the source to be validated.

**Acceptance Criteria:**

**Given** exact frozen Story 1.1 head and a GitHub-authenticated OWNER PR issue comment whose canonical body binds that head/tree, controller/workflow identities, all allowed paths and fixed checks
**When** owner prepares the one-time manual landing exception
**Then** trusted code re-reads the exact unmodified comment by ID, verifies OWNER identity/association and expiry, while the legacy workflow provides no bootstrap evidence and executes no Story 1.1 controller scope
**And** the non-authoritative observation remains `authority=NONE`; Story 1.2 owns atomic single-use consumption and no bootstrap evidence permits Story 1.3, release, promotion or deploy.

**Given** a repository dispatch for the new controller
**When** PR identity is resolved through the GitHub API
**Then** the controller confirms the exact repository, open PR number/state, exact current head SHA, same-repository head/base, and required ancestry/tree identity
**And** an arbitrary 40-hex commit, fork head, stale head, payload-only repository claim, or PR-local workflow authority is rejected.

**Given** validated PR identity
**When** source is materialized
**Then** the controller obtains the exact authenticated archive with the token only in the step environment, verifies traversal, links, member policy, and the exact tree, then removes response/archive credentials
**And** the source-materialization observation binds repository, PR, head SHA/tree, default-branch controller/workflow blob, action/input digests, OWNER approval-comment projection, and cleanup intent without executing untrusted project commands.

**Given** frozen Story 1.1 changes and exact 57-path review
**When** the owner comment, frozen local verification outputs/hashes, independent source/security YES and graph/governance YES are present
**Then** manual exact source-only landing installs the controller on the default branch with `authority=NONE`, while validation authority remains fail closed until Story 1.2 sandbox/self-validation
**And** traceability links NFR15-NFR21, NFR27-NFR33, NFR38-NFR41, and AR5/AR8-AR11; rollback uses the exact previous default-branch workflow identity.

### Story 1.2: Run validation in a disposable multi-project Claw sandbox

As an internal operator/researcher,
I want to run the exact materialized source in an isolated rootless sandbox with verified cleanup,
So that Claw can be fully used for realtime tests without production, cross-project, or credential authority.

**Acceptance Criteria:**

**Given** verified `authority=NONE` source-materialization observation plus a new Phase A
OWNER approval/installation evidence set (PR24 evidence is historical `RETIRED_UNUSED`)
**When** validation starts
**Then** untrusted source executes in a unique rootless Podman container/network/workspace with a pinned validation image, read-only source, dropped capabilities, no host Docker socket, and no production routes/databases
**And** registry/release/deploy/private venue credentials, n8n, live-trading authority, and dirty `/home/operator/app-stack` are inaccessible.

**Given** Claw serves multiple projects and test iterations
**When** validation applies or rolls back migrations, containers, candidate artifacts, or test configuration
**Then** mutable resources receive project/run/attempt identity, isolated database/network/paths/credentials, and a receipt-bound lifecycle
**And** test mutation does not affect unrelated projects, and sandbox policy blocks unscoped names/routes/mounts.

**Given** a validation command has completed with success or failure
**When** cleanup runs
**Then** named containers/processes/networks/workspaces are removed or confirmed absent, the validation receipt records exact inputs/commands/results/output hashes, and a separate cleanup receipt records the verified outcome
**And** the downstream gate requires both valid receipt hashes and rejects failed/unverified cleanup.

**Given** Phase A source-only controller/host-helper install landed with `authority=NONE`
**When** the installed exact Phase A controller validates a separate minimal Phase B probe PR
**Then** validation, cleanup, and self-validation receipts bind controller SHA/tree/workflow blob, sandbox policy/image, source SHA/tree, nonce consumption, and cleanup
**And** a separate Phase C1 evidence-proposal PR lands immutable external Phase B run URL/hashes with `authority=NONE`; only the subsequent Phase C2 evidence-admission PR, bound to the already existing authenticated C1 merge SHA/tree/API payload and its committer date, can authorize Story 1.3, leaves Phase B/C1 unchanged, and only then records legacy `SUPERSEDED`/disabled evidence.

**Given** repository workflows and runner labels
**When** policy tests and independent DevOps/security review run
**Then** test/validation/build/scan/promotion use only `[self-hosted, claw]`, and the PR gate has minimal read-only permissions and no deploy/promotion/private/live authority
**And** traceability links NFR15-NFR34, NFR38-NFR41, and AR5/AR8-AR11 to receipts, cleanup, and the reviewed replacement path.

### Story 1.2A: Claw engine-runner host transition

As an internal operator/researcher,
I want to carry out an owner-approved Claw engine runner transition through a root-owned
transaction controller with durable rollback,
So that rootless disposable validation receives a dedicated runner identity without
copying credentials, disrupting app-stack, or unauthorized host mutation.

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

### Story 1.3: Launch capability-isolated Public Capture from the canonical distribution

As an internal operator/researcher,
I want to run Public Capture from a separately installed artifact with a pure contract core,
So that public evidence collection is physically unable to acquire trading, private, or analytical authority.

**Acceptance Criteria:**

**Given** a modular-monorepo layout with independently installable `mee_contracts`, `mee_public_capture`, and `mee_readonly_analyzer`
**When** contracts and Public Capture distributions are built and installed in a clean environment
**Then** Public Capture runs only through the canonical `mee_public_capture` entry point and imports application code only from its own namespace and pure `mee_contracts`
**And** `mee_contracts` installs independently and passes contract tests without application, adapter, storage, network, database, or workflow dependencies.

**Given** an installed Public Capture artifact and its resolved dependency/import/file/entry-point manifests
**When** capability-boundary validation runs
**Then** the artifact contains no `mee_readonly_analyzer`, legacy `multi_exchange_engine`, Go binaries/layers, or any signer, wallet, credential, private/account, order, cancel, transfer, withdrawal, n8n, or execution capabilities
**And** forbidden imports, symbols, dependency edges, entry points, or dormant execution files fail closed with a typed boundary reason.

**Given** Public Capture configuration and runtime manifest
**When** the operator selects public Hyperliquid/Lighter feeds
**Then** the runtime allows only credential-free discovery, public streaming, and append-only capture responsibilities
**And** books, opportunities, economics, strategies, portfolio, and verdict ownership are absent from the reachable runtime graph.

**Given** retained Go reference invariants
**When** conformance/retirement status is checked
**Then** Go remains `TEST_ONLY_EXECUTABLE_SPEC`, excluded from Stage-A source closure, binaries, dependencies, and layers
**And** each retirement candidate requires the mapping invariant -> versioned contract -> Python implementation -> negative tests -> exact-SHA Claw receipt -> independent review; missing evidence blocks retirement but never makes Go deployable.

**Given** Story 1.3 changes
**When** its mandatory exact-SHA Claw validation runs
**Then** focused RED/GREEN tests, installed-artifact boundary tests, dependency-DAG/orphan checks, and independent security review complete successfully
**And** traceability links FR16, NFR1-NFR4, NFR8-NFR21, NFR27-NFR41, and AR1-AR5/AR8-AR11 to the canonical owner, tests, Claw receipt, artifact boundary, and rollback/replacement evidence.

### Story 1.4: Register immutable CaptureRun and evidence before partition admission

As an internal operator/researcher,
I want every capture session and each evidence object it owns to first receive an unambiguous unpartitioned identity,
So that partitioned payload cannot be written without a provable owner and a complete path to the original run.

**Acceptance Criteria:**

**Given** a new public capture session with exact collector/config/schema identities
**When** Public Capture opens the session
**Then** PostgreSQL creates exactly one immutable unpartitioned `CaptureRun` root in `OPEN` state with a unique `capture_run_id`
**And** registering the same session identity again either returns the same consistent root or fails closed on mismatched content; silently creating a second root is forbidden.

**Given** an evidence object owned by an open `CaptureRun`
**When** the object is admitted to storage
**Then** its immutable unpartitioned registry row with `node_id`, `capture_run_id`, node kind, schema/version, and semantic hash exists before payload insertion into any day partition
**And** foreign-key/constraint authority rejects partition payload without a registry row, with an unknown run, with a mismatched owner, or with a reused `node_id`.

**Given** a registered `CaptureRun` or capture node
**When** the runtime tries to change immutable identity, owner, schema identity, or semantic hash through direct DML or an unauthorized path
**Then** the operation is rejected atomically
**And** the Public Capture runtime role has no table ownership, direct update/delete, sequence, or schema-creation privileges.

**Given** clean digest-pinned PostgreSQL 16 and 17 databases
**When** exact-SHA Claw runs migration, schema, positive-admission, and negative-orphan tests
**Then** both versions confirm unpartitioned root/registry authority and absence of a partition-only or application-precheck bypass
**And** traceability links FR15 and FR25 to NFR6, NFR15-NFR21, NFR27-NFR34, NFR38-NFR41, and AR5/AR8-AR10; migration rollback works only before durable evidence and refuses to remove nonempty roots without an explicitly verified replacement path.

### Story 1.5: Link evidence through typed edges and global logical keys

As an internal operator/researcher,
I want the provenance, uniqueness, and supersession of each evidence object to be checked by one graph authority,
So that the dataset contains no dangling nodes, hidden duplicates, cycles, or ambiguous successors.

**Acceptance Criteria:**

**Given** two registered evidence nodes
**When** Public Capture creates an edge between them
**Then** the edge references both unpartitioned registry endpoints through foreign keys and specifies a versioned edge kind/contract
**And** a missing endpoint, forbidden combination of node kinds, incompatible contract version, or unauthorized cross-run link fails closed before the edge appears.

**Given** a node with a declared logical-key scope
**When** a logical key is registered for this node
**Then** one unpartitioned authority ensures global key uniqueness within the declared scope regardless of day partition
**And** a duplicate from another partition, concurrent transaction, or application-side precheck is rejected by the database and creates no payload or edge.

**Given** a `derived_from` or `supersedes` lineage
**When** a new lineage edge is added
**Then** the graph remains acyclic and each superseded node has at most one direct successor in the same semantic lineage
**And** an attempt to create a cycle or competing successor does not automatically select a winner, but creates typed blocking conflict evidence or rejects the entire atomic operation according to the frozen contract.

**Given** a future need to link Capture, FrozenPackageReceipt, Analysis, or Retention roots
**When** the edge kind has no previously versioned cross-root contract with allowed endpoint/root types
**Then** ownership transfer, root reopening, and implicit cross-root links are forbidden
**And** this story publishes an extensible contract interface but creates no future root tables, writers, or permissions before the corresponding capability exists.

**Given** clean digest-pinned PostgreSQL 16 and 17 databases
**When** exact-SHA Claw runs migration, concurrent duplicate-key, dangling-edge, type-mismatch, cross-run, cycle, and competing-successor tests
**Then** both versions produce identical typed results and the graph/orphan checker confirms slice connectivity
**And** traceability links FR26, FR27, and FR32, plus the contract portion of FR39, to NFR15-NFR25, NFR27-NFR34, NFR40-NFR41, and AR4/AR8-AR10; rollback does not remove nonempty lineage authority without a verified replacement path.

### Story 1.6: Write capture evidence only through an atomic constrained writer

As an internal operator/researcher,
I want admission of each capture evidence object to occur in one atomic operation with canonical time,
So that a partial write, bypass of graph invariants, or host/audit time influence cannot change the evidence and subsequent replay.

**Acceptance Criteria:**

**Given** an open `CaptureRun` and a valid evidence envelope
**When** Public Capture calls the only authorized writer contract
**Then** one transaction locks the required run authority and atomically verifies root state, registry identity, logical key, semantic hash, typed edges, and payload admission
**And** failure at any step rolls back the entire registry, key, edges, and payload without partial durable state.

**Given** Public Capture runtime database role
**When** grants and all accessible database paths are checked
**Then** the role has only minimal `CONNECT`/`USAGE` and `EXECUTE` on the approved writer interface
**And** direct table DML, sequence privileges, ownership, role inheritance, schema creation, alternate writer functions, and bypass through mutable views are absent, as confirmed by negative tests.

**Given** an evidence envelope with `effective_at_evidence_time`, source sequence/index, and `recorded_at_audit_time`
**When** the canonical semantic hash and replay order are computed
**Then** the hashed identity includes evidence-effective time and the required source identity/sequence/payload fields
**And** audit/insertion time is stored separately, excluded from the semantic hash, and has no effect on ordering, duplicate detection, economics, or deterministic output.

**Given** two records with the same semantic identity but different audit times, or the same audit time and different effective identities
**When** the writer processes them sequentially or concurrently
**Then** the duplicate/conflict decision is determined only by canonical identity and the declared logical-key contract
**And** a change to the host clock, transaction order, or retry does not change the canonical result.

**Given** clean digest-pinned PostgreSQL 16 and 17 databases
**When** exact-SHA Claw runs writer atomicity, privilege-denial, concurrent admission, rollback-on-error, and time-determinism tests
**Then** both versions give equivalent results with no skipped database tests
**And** traceability links FR28 and FR34 to NFR6, NFR15-NFR24, NFR27-NFR34, NFR38-NFR41, and AR5/AR8-AR10; replacement/rollback preserves already admitted append-only evidence and does not open a DML bypass.

### Story 1.7: Seal CaptureRun race-safely and record terminal identity

As an internal operator/researcher,
I want to atomically close the capture session and obtain an immutable terminal identity,
So that the subsequent frozen package refers to the exact completed node set and no late write changes the original evidence.

**Acceptance Criteria:**

**Given** an open `CaptureRun` with a complete capture-owned graph
**When** the operator initiates terminalization through the approved seal contract
**Then** the seal locks the same unpartitioned run row as the admission writer and verifies the mandatory pre-seal capture replay-integrity receipt and graph closure
**And** records expected/observed counts, terminal epochs/indices, canonical time bounds, complete node-set identity, and the canonical capture terminal hash before moving the root to `SEALED`.

**Given** admission and seal run concurrently
**When** both transactions contend for one `CaptureRun`
**Then** admission either commits completely before the seal and is included in counts/node set/hash, or runs after the seal and is rejected completely
**And** no registry, logical-key, edge, payload, or lifecycle write can commit across the terminalization boundary.

**Given** sealed `CaptureRun`
**When** any capture or analysis path tries to add or change capture-owned payload, registry row, logical key, edge, lifecycle record, terminal metadata, or replay receipt
**Then** the operation fails closed with a typed post-seal reason
**And** a separate future `AnalysisRun` never obtains ownership or an append path under `CaptureRun`.

**Given** a sealed `CaptureRun` ready for future export
**When** the seal boundary publishes terminal identity for the freeze pipeline
**Then** it provides the exact terminal hash and complete capture node-set identity as mandatory candidate-export inputs
**And** no VERIFIED `FrozenPackageReceipt` is created at this step: its admission remains forbidden until full semantic validation succeeds under a separate versioned freeze contract.

**Given** clean digest-pinned PostgreSQL 16 and 17 databases
**When** exact-SHA Claw runs seal/admission race, post-seal mutation, incomplete-closure, terminal-hash, and frozen-receipt mismatch tests
**Then** both versions demonstrate identical serialization and no skipped database tests
**And** traceability links FR29 and FR33, plus the receipt-boundary portion of FR30/FR39, to NFR6, NFR15-NFR24, NFR27-NFR34, NFR36-NFR41, and AR5/AR8-AR10; rollback cannot remove or reopen a sealed root and preserves terminal evidence.

### Story 1.8: Read capture evidence through a deterministic least-privilege PostgreSQL contract

As an internal operator/researcher,
I want to obtain capture evidence through a stable deterministic read-only PostgreSQL interface,
So that analysis can be reproduced without access to writer paths or dependence on the physical table layout.

**Acceptance Criteria:**

**Given** a registered capture evidence graph
**When** the canonical `EvidenceReader` reads PostgreSQL projections
**Then** versioned views return manifest, control evidence, raw envelopes/batches, mapping, quality, and terminal metadata in a fully specified canonical order
**And** physical partition order, query plan, audit time, and insertion order do not change the result.

**Given** Analyzer database role
**When** effective privileges and reachable database objects are checked
**Then** the role has only the required `CONNECT`, schema `USAGE`, and deterministic-view `SELECT`
**And** base-table DML, sequence access, writer/seal function `EXECUTE`, ownership, inheritance, mutable views, and alternate mutation paths are rejected.

**Given** missing provenance, an unknown schema/edge version, an incomplete node set, or an unsealed run
**When** the reader requests a binding dataset
**Then** the reader fails closed with a typed contract/integrity reason and does not present a partial dataset as complete
**And** a read-only failure does not change the capture graph or create an AnalysisRun.

**Given** clean digest-pinned PostgreSQL 16 and 17 databases
**When** exact-SHA Claw runs clean migrations, deterministic-view ordering, role/grant denial, and reader-contract tests
**Then** both versions return byte-equivalent canonical records with no skipped integration tests
**And** traceability links FR17, FR35, and FR36 to NFR6, NFR15-NFR24, NFR27-NFR41, and AR5/AR8-AR10; rollback preserves versioned reader compatibility or is blocked until a replacement view contract exists.

### Story 1.9: Export and semantically validate an immutable frozen package

As an internal operator/researcher,
I want to export a sealed CaptureRun to an independently verifiable frozen package,
So that final analysis relies on a portable tamper-evident dataset equivalent to the PostgreSQL evidence authority.

**Acceptance Criteria:**

**Given** a sealed `CaptureRun` with a terminal hash, complete node set, and pre-seal replay-integrity closure
**When** the Public Capture export boundary creates a frozen package
**Then** the package uses canonical member names/encoding/order, binds exact run/terminal/node-set/schema/collector/config identities, and computes member hashes and a package root hash
**And** export does not import the Analyzer application, create analyzer replay, or change the sealed CaptureRun.

**Given** candidate frozen package
**When** an independent semantic validator checks it
**Then** it parses every envelope, recomputes payload/mapping/quality hashes, and verifies run, venue, epoch, sequence/index, canonical time, counts, bounds, duplicate logical keys, lifecycle, soak, decoder-observation, connection, and pre-seal replay-integrity closure
**And** missing, extra, reordered, duplicated, cross-run, out-of-bounds, hash-mismatched, or malformed evidence leads to `INVALID_DATASET`, rather than partial success.

**Given** semantic validation has passed
**When** a `FrozenPackageReceipt` is registered
**Then** a separate immutable receipt binds retrievable package URI/object identity, package hash, sealed capture terminal hash, and the complete capture node set
**And** the receipt contains no post-package analyzer replay nodes and transfers no ownership or writer rights.

**Given** a PostgreSQL reader and a frozen-package reader over one sealed run
**When** both implement the sole versioned `EvidenceReader` contract
**Then** they emit equivalent canonical evidence streams and terminal metadata
**And** repeated reads in fresh processes do not depend on the network, host clock, filesystem enumeration order, or repository cwd.

**Given** exact-SHA Claw validation
**When** tamper corpus, semantic mismatch, database-to-package equivalence, and installed-artifact tests run
**Then** the package/reader slice passes on clean PostgreSQL 16/17 and in an isolated credential-free sandbox
**And** traceability links FR17, FR29, FR30, and the applicable portion of FR31 to NFR6, NFR15-NFR24, NFR27-NFR41, and AR3/AR5/AR8-AR10; rollback preserves the receipt/package and creates a superseding export instead of overwriting it.

### Story 1.10: Allow retention only through a verified FrozenPackageReceipt

As an internal operator/researcher,
I want to remove or detach raw storage only after an independently verified export receipt,
So that retention never destroys the only reproducible evidence source.

**Acceptance Criteria:**

**Given** a sealed `CaptureRun` without a retrievable independently verified `FrozenPackageReceipt`
**When** a drop, detach, expire, or other loss-of-availability operation is requested for a raw partition/object
**Then** the operation fails closed before any storage mutation
**And** a package path alone, an unverified hash, or an unbound receipt does not satisfy the gate.

**Given** a sealed `CaptureRun` and a valid retrievable receipt
**When** the authorized retention boundary starts an operation
**Then** a separate immutable `RetentionAction` root is created with its own registry, logical-key scope, writer privilege, and state machine
**And** versioned typed edges link it to the exact CaptureRun and receipt without ownership transfer, root reopening, or appending under the capture namespace.

**Given** RetentionAction
**When** storage mutation completes or suffers partial/total failure
**Then** the action records exact authorization, affected partitions/objects, precondition identities, result, and retention-evidence hash, then terminally seals
**And** a retry is idempotent or creates an explicitly linked new action; it does not rewrite the previous result.

**Given** the package becomes unavailable, a receipt mismatch is detected, or the affected-object set changes before mutation
**When** retention rechecks preconditions
**Then** mutation is blocked and failure evidence is preserved append-only
**And** recovery uses the preserved verified package or exact prior storage identity but never reconstructs history by changing sealed roots.

**Given** exact-SHA Claw validation on clean PostgreSQL 16/17
**When** missing/unreachable/mismatched-receipt, unauthorized-object, retry, partial-failure, and cross-root privilege tests run
**Then** the retention gate fails closed identically on both versions and does not affect Analyzer or unrelated services
**And** traceability links FR31, FR38, and the remaining portion of FR39 to NFR6, NFR15-NFR24, NFR27-NFR41, NFR47, and AR5/AR8-AR10; rollback/recovery evidence remains connected with no orphan nodes.

## Epic 2: The operator reproduces the market and measures executable cross-venue economics

The operator can deterministically reconstruct economically equivalent
instruments and fail-closed books from verified evidence, then measure the
full executable cost of entry and exit across both venues without claiming
strategy viability.

**Implementation prerequisite:** Epic 1 provides a verified frozen package and
sole `EvidenceReader`; exact-SHA validation continues to use only M6
Task 1 trusted disposable Claw controller.

### Story 2.1: Map instruments by exact economic identity

As an internal operator/researcher,
I want to analyze only instruments proven to be economically equivalent using exact arithmetic,
So that a matching ticker or float rounding does not create a false cross-venue opportunity.

**Acceptance Criteria:**

**Given** verified evidence for Hyperliquid and Lighter instruments
**When** Read-Only Analyzer constructs an economic identity mapping
**Then** identity includes underlying, product/payoff kind, multiplier, price/quantity units, quote, settlement/collateral, venue instrument ID, validity interval, schema/version, and provenance hashes
**And** ticker equality without a complete match of contract fields is never sufficient mapping authority.

**Given** price, quantity, fee, funding, or P&L input
**When** contracts decode and normalize the value
**Then** calculations use canonical exact decimal, fixed-point, or rational representation with explicit units and rounding rules
**And** binary floats, NaN/Infinity, ambiguous scale, an unknown multiplier, or incompatible settlement fail closed before reconstruction/economics.

**Given** a mapping conflict, overlapping validity, missing provenance, or multiple acceptable economic identities
**When** Analyzer selects an identity for binding evidence
**Then** a typed unresolved/conflict result is created and downstream book/economics admission is blocked
**And** latest-wins, ticker fallback, averaging, and implicit coercion are forbidden.

**Given** audited legacy analyzer fragments and PR #21 head `7fe6918690f8bc1da5826c67e3619de4126e4f54`
**When** reusable exact contracts/evidence code is migrated to canonical Analyzer/Contracts distributions
**Then** every retained blob is bound to its source commit/blob, stable requirement, rewrite rule, and installed-namespace tests
**And** whole-branch merge, conflicting workflow/config import, a duplicate `multi_exchange_engine` owner, or an unprovenanced copy are forbidden; rejected material is preserved as quarantined provenance.

**Given** installed Read-Only Analyzer artifact
**When** exact-SHA Claw runs contract, malformed-number, mapping-conflict, and capability-boundary tests
**Then** the artifact contains `mee_readonly_analyzer` and pure `mee_contracts`, but no capture writer, venue network client, or private/trading/n8n/Go execution capability
**And** traceability links FR19 and FR20 to NFR1-NFR9, NFR15-NFR24, NFR27-NFR41, and AR1-AR5/AR8-AR10; prior mapping remains provenance and correction uses explicit supersession.

### Story 2.2: Deterministically reconstruct fail-closed venue books

As an internal operator/researcher,
I want to reconstruct a book only from an authoritative snapshot and a continuous venue-valid sequence,
So that gaps, reconnects, and malformed updates do not become executable liquidity.

**Acceptance Criteria:**

**Given** a verified stream for one mapped instrument/connection epoch
**When** Analyzer receives an authoritative snapshot and subsequent venue-valid updates
**Then** it creates deterministic book checkpoints only after the snapshot and continuously applies monotonic sequence/index transitions
**And** each checkpoint is bound to exact envelope/node, mapping, decoder/schema, and reconstruction algorithm identities.

**Given** reconstructed bid/ask levels
**When** a checkpoint passes admission
**Then** prices and quantities are positive and exact, sides are strictly ordered, duplicate levels are normalized only according to a versioned venue rule, and the spread is not crossed
**And** an invalid level, impossible deletion, unsupported transition, or crossed result closes the active reconstruction epoch.

**Given** a gap, regression, duplicate with mismatched payload, reconnect, or malformed frame
**When** a transition violates the venue sequencing contract
**Then** the current epoch becomes invalid/closed and subsequent incrementals are not used
**And** reconstruction resumes only from a new independently valid snapshot; stale state is not carried across a reconnect.

**Given** PostgreSQL and frozen readers of one evidence package
**When** fresh Analyzer processes reconstruct checkpoints
**Then** canonical checkpoints, rejection reasons, and epoch boundaries are byte-identical
**And** exact-SHA Claw tests link FR21 and FR22 to FR17/FR19/FR20, NFR6, NFR15-NFR24, NFR27-NFR41, and AR8-AR10; rollback creates a new versioned reconstruction projection without rewriting evidence.

### Story 2.3: Measure the full four-leg lifecycle through full-depth VWAP

As an internal operator/researcher,
I want to measure both venue legs at entry and exit using actually available depth,
So that top-of-book or an incomplete lifecycle cannot be presented as executable economics.

**Acceptance Criteria:**

**Given** valid mapped books and a requested exact quantity/notional
**When** Analyzer evaluates a cross-venue lifecycle
**Then** it computes full-depth VWAP separately for leg A entry, leg B entry, leg A exit, and leg B exit with exact quantity consumption and declared rounding
**And** each fill slice is bound to a specific checkpoint, levels consumed, timestamp/sequence, and economic identity.

**Given** insufficient depth, an invalid checkpoint, a crossed book, a stale/closed epoch, or incompatible units on any of the four legs
**When** pricing runs
**Then** the entire lifecycle receives a typed rejection and produces no partial executable result
**And** top-of-book, last-price, extrapolation, synthetic liquidity, and quantity shrinking fallback are forbidden.

**Given** both possible cross-venue directions and multiple frozen notionals
**When** measurement starts
**Then** each direction/notional is evaluated independently under the same deterministic contract, including negative economics
**And** the result remains an economics measurement: it is not called an opportunity, creates no strategy episode/verdict, and sends no order command.

**Given** exact-SHA Claw validation
**When** golden depth ladders, rounding boundaries, insufficient-depth, four-leg provenance, and fresh-process determinism tests run
**Then** expected VWAP/rejections are exact and independent of reader/backend/host clock
**And** traceability links FR23 and rechecks FR19-FR22 through NFR6, NFR15-NFR24, NFR27-NFR41, and AR8-AR10; algorithm replacement creates versioned superseding outputs.

## Epic 3: The operator evaluates frozen shadow strategies with full costs and capital constraints

The operator can run basis and realized-funding shadow strategies, see
full costs, delays, failed attempts, capital locks, concentration,
and diagnostic paired-basis trailing without creating orders or mixing
quarantined strategies into the binding verdict.

**Implementation prerequisite:** Epics 1-2 provide verified frozen evidence,
exact identities, fail-closed books, and four-leg pricing. All checks run
on the trusted exact-SHA Claw controller; retail UI and live/private execution are outside
the scope.

### Story 3.1: Freeze the admitted strategy universe and separate policy contracts

As an internal operator/researcher,
I want to fix strategies, cells, capital weights, and economic policies before acquisition,
So that the observed result cannot change the composition or rules of the hypothesis being tested.

**Acceptance Criteria:**

**Given** owner-approved Stage-A-v2 configuration before the evidence window starts
**When** a strategy manifest is created
**Then** the closed set of admitted `(strategy, asset, direction)` cells, deterministic capital weights, notionals, fee cases, delays, thresholds, episode rules, residual limits, and policy versions are canonicalized and hash-bound
**And** binding basis convergence and realized funding carry are allowed; paired-basis trailing is marked `DIAGNOSTIC_NON_BINDING`.

**Given** strategy domain model
**When** contracts are installed independently
**Then** signal/strategy, inventory, exit, execution-counterfactual, cost, and portfolio policies are separate versioned contracts
**And** no contract returns an order/cancel/private command; the only allowed output type is immutable shadow simulation/evidence.

**Given** acquisition has already started
**When** removing/adding a cell, changing a weight/threshold/cost/baseline, or selecting parameters based on observed economics is proposed
**Then** binding configuration remains immutable, and the attempt fails closed or creates a new future experiment identity
**And** post-hoc sensitivity is allowed only as a clearly labelled diagnostic that does not change the binding aggregate/verdict.

**Given** missing approval, an unknown enum, weight mismatch, a duplicate cell, an unsupported strategy, or noncanonical numeric input
**When** the manifest is validated
**Then** acquisition/analysis admission is blocked with a typed configuration reason
**And** exact-SHA Claw tests link FR40, FR44, and FR47 to AR4, NFR15-NFR26, NFR27-NFR41, and AR8-AR10; the replacement manifest has a new identity and does not rewrite the previous one.

### Story 3.2: Attribute delayed legs, failures, residuals and the full cost ledger

As an internal operator/researcher,
I want to see the full cost of every successful and failed counterfactual attempt,
So that latency, residual risk, or hidden expenses do not turn a negative hypothesis into a positive one.

**Acceptance Criteria:**

**Given** an admitted shadow attempt and frozen delay/cost policies
**When** entry and exit of both venue legs are modeled
**Then** each leg selects its own evidence checkpoint after the declared delay and receives an independent fill/rejection outcome
**And** simultaneous/atomic fill is not assumed, and a missing delayed checkpoint or depth is recorded as a failed attempt.

**Given** asymmetric fills or a failed second leg
**When** residual exposure arises
**Then** deterministic residual-neutralization/rebalance policy uses only subsequent valid executable evidence, accounts for additional delay/depth/fees, and records a bounded or unresolved residual result
**And** unresolved neutralization fails closed and is not masked by assuming a free close.

**Given** a completed or failed attempt
**When** an immutable cost ledger is constructed
**Then** entry/exit fees for each leg, realized funding, forecast funding label, slippage/depth, delay decay, residual neutralization, rebalance, failed-attempt cost, holding/inventory, and frozen infrastructure cost are attributed separately
**And** a missing mandatory cost/provenance field preserves the attempt itself and moves the entire run to `INVALID_DATASET` or `INSUFFICIENT_EVIDENCE`; omitting the attempt, replacing a cost with zero, or recalculating the aggregate without it is forbidden.

**Given** fresh-process replay of one attempt
**When** exact-SHA Claw runs independent-delay, failed-leg, residual, fee-sign, cost-sum, and provenance tests
**Then** the ledger and reason codes are byte-identical and independent of host clock/network
**And** traceability links FR41/FR42/FR49 and applicable FR40/FR44 to NFR6, NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR10; corrections supersede ledgers without rewriting them.

### Story 3.3: Identify independent episodes and lock virtual capital

As an internal operator/researcher,
I want to count only independent opportunities and avoid reusing committed capital,
So that overlapping signals and duplicate frames do not artificially multiply economics.

**Acceptance Criteria:**

**Given** ordered strategy signals and a frozen episode policy
**When** the tracker forms episodes
**Then** deterministic identity groups frames/signals belonging to one opportunity, and independence is determined by predeclared start/end/cooldown rules
**And** duplicate/replayed inputs do not create a new episode or a second P&L.

**Given** multiple admitted cells compete for limited virtual capital
**When** an attempt starts
**Then** capital allocation uses frozen weights and deterministic priority, and allocated capital remains locked until exit, failed-attempt completion, and residual neutralization
**And** a signal rejected because of a capital lock is preserved as an attributable non-executed attempt if the frozen policy requires it.

**Given** an episode completes successfully, unsuccessfully, or remains unresolved
**When** an episode ledger is formed
**Then** it contains all attempts, time/capital bounds, cost-ledger links, and a typed terminal state
**And** an unresolved/open episode is not counted as a completed independent lifecycle and does not disappear from sufficiency/concentration evidence.

**Given** exact-SHA Claw validation
**When** overlap, duplicate, cooldown, priority, capital-reuse, failure, and concentration-input tests run
**Then** episode counts and the capital timeline are deterministic
**And** traceability links FR48 and applicable FR49 to NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR10; policy changes create superseding experiment outputs.

### Story 3.4: Evaluate the executable basis-convergence lifecycle

As an internal operator/researcher,
I want to evaluate basis-convergence entry and exit using independent delayed executable books,
So that the hypothesis accounts for actual depth and edge decay between the two legs.

**Acceptance Criteria:**

**Given** an admitted basis cell, a valid episode, and a frozen entry/exit policy
**When** a basis signal passes the predeclared admission threshold
**Then** the strategy evaluates both directions and the entire four-leg lifecycle through full-depth VWAP, independent delays, and a complete cost ledger
**And** the result binds signal, checkpoints, fills/rejections, capital locks, residual outcomes, and policy/config hashes.

**Given** a convergence, fixed-time, remaining-basis, or safety exit condition
**When** the exit policy triggers
**Then** the deterministic declared precedence data/mapping invalid -> residual/margin safety -> max hold -> basis widening -> strategy exit applies
**And** the strategy does not choose the best exit retrospectively or use future evidence.

**Given** negative edge, a failed leg, insufficient depth, widened basis, or expensive neutralization
**When** the attempt completes
**Then** negative/failed economics is preserved in full and enters the downstream aggregate according to frozen policy
**And** output remains shadow evidence and creates no execution command or eligibility for live trading.

**Given** exact-SHA Claw validation
**When** golden convergence, widening, delayed-leg, exit-precedence, negative-edge, and no-lookahead tests run
**Then** basis episode outputs are deterministic and exact
**And** traceability links FR40, FR41, FR44, and applicable FR48/FR49 to NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR10.

### Story 3.5: Evaluate realized-funding carry from actual settlements

As an internal operator/researcher,
I want to separate realized funding cashflows from forecasts and full holding economics,
So that the funding hypothesis is supported only by actually observed settlement evidence.

**Acceptance Criteria:**

**Given** an admitted funding cell and signed venue settlement evidence
**When** the funding lifecycle is modeled
**Then** realized cashflow is bound to exact venue/instrument, rate/amount, sign, schedule, effective interval, position/notional, and evidence hash
**And** forecast/indicative rate is stored as a separate diagnostic type and never replaces realized settlement.

**Given** funding episode
**When** net economics is computed
**Then** the ledger includes entry/exit VWAP, basis movement, holding time, fees, delay, residual/rebalance, capital locks, and realized funding for each venue leg
**And** missing/ambiguous settlement, sign, interval, or position attribution makes the funding reason insufficient/invalid.

**Given** a positive forecast and negative or missing realized cashflow
**When** the episode/aggregate is constructed
**Then** the forecast creates no positive funding P&L and does not satisfy funding continuation evidence
**And** completed and failed funding attempts remain in the admitted-cell slice.

**Given** exact-SHA Claw validation
**When** sign/schedule, settlement-boundary, forecast-separation, missing-cashflow, basis/holding-cost, and replay tests run
**Then** funding outputs are deterministic and provenance-complete
**And** traceability links FR40, FR42, FR44, and applicable FR48/FR49 to NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR10.

### Story 3.6: Compare paired-basis trailing only as a diagnostic

As an internal operator/researcher,
I want to compare a trailing exit based on realized paired-basis convergence,
So that potential exit-policy improvement is measured without affecting the binding Stage-A decision.

**Acceptance Criteria:**

**Given** completed basis episodes and frozen diagnostic trailing configuration
**When** Analyzer runs counterfactual trailing
**Then** the trail tracks only a synchronized executable paired-basis/net-capture measure with independent delayed exits and complete costs
**And** single-asset price trail, lookahead peak, unfilled top-of-book, and free cancellation assumptions are forbidden.

**Given** diagnostic result
**When** it is compared with frozen primary exits
**Then** the report shows non-inferiority, tail/drawdown, missed exits, and regime slices as diagnostic evidence
**And** trailing does not change admitted primary attempts, portfolio aggregate, sufficiency, binding reasons, or verdict bytes.

**Given** a negative cell or positive trailing sensitivity
**When** downstream decision consumes strategy evidence
**Then** the negative cell remains in the frozen aggregate, and trailing output is inaccessible through the binding verdict input type
**And** an attempt to create such an import/type edge is blocked by graph/capability tests.

**Given** exact-SHA Claw validation
**When** no-lookahead, delayed-exit, full-cost, binding-isolation, and report-label tests run
**Then** diagnostic output is deterministic and physically separated from verdict inputs
**And** traceability links FR43, FR44, FR47, and applicable FR49 to NFR15-NFR26, NFR27-NFR41, and AR4/AR8-AR10.

### Story 3.7: Build the frozen-universe portfolio aggregate without masking

As an internal operator/researcher,
I want one reconciled aggregate across the entire previously admitted universe,
So that profitable survivors cannot hide missing, failed, or negative cells.

**Acceptance Criteria:**

**Given** a frozen manifest of all admitted cells and capital weights
**When** portfolio aggregator consumes strategy episodes
**Then** it includes every completed and failed attempt from every admitted cell with its frozen weight and deterministic ordering
**And** observed economics cannot remove, add, reweight, or rename a cell.

**Given** a missing mandatory cell, unreconciled attempt, open residual, or incomplete required evidence
**When** the aggregate is constructed
**Then** the aggregate receives a typed invalid/insufficient state and is not recalculated over survivors
**And** a negative cell is preserved within the aggregate but does not by itself create a separate binding verdict.

**Given** complete aggregate
**When** portfolio evidence metrics are computed
**Then** total/median net, notional cases, delay/fee cases, independent episode count, capital utilization, and largest-episode concentration are exact and reconciled with per-cell slices
**And** per-cell slices are mandatory for explainability but marked non-binding; their sum/weights reconcile with the aggregate without a remainder.

**Given** minimum episode contract
**When** episode count is checked
**Then** the minimum of 20 independent episodes applies to the aggregate unless a separate per-cell minimum was approved before acquisition
**And** exact-SHA Claw tests link FR40, FR47, FR48, and FR49 to AR4, NFR15-NFR26, NFR27-NFR41, and AR8-AR10; aggregate algorithm/version is part of provenance.

### Story 3.8: Prove quarantine of unsupported strategy runtime

As an internal operator/researcher,
I want verifiable proof that imported and live-oriented strategies are not part of Stage A,
So that research fragments do not become active bots through matching names or imports.

**Acceptance Criteria:**

**Given** installed Analyzer and Public Capture artifacts, manifests, and runtime graph
**When** a quarantine boundary scan runs
**Then** grid, DCA, Infinity Grid, Solana-chain runtime, maker-fill claims, legacy asset bots, private adapters, and execution libraries are absent from dependencies, files, imports, entry points, configuration selectors, and reachable symbols
**And** research/archive nodes preserve provenance and are explicitly classified as `QUARANTINED_HYPOTHESIS` or `ARCHIVE`, not ACTIVE.

**Given** a request to promote a quarantined strategy
**When** a separate approved actor/outcome, strategy manifest, economic contract, evidence gate, security/capability review, and owner approval are absent
**Then** promotion fails closed and the active graph does not change
**And** reuse is allowed only as provenance-labelled test/research input without private protocol, wallet, signer, or live authority.

**Given** a maker-first, polling bot, or other imported method
**When** queue/fill/cancel/adverse-selection measurements and a frozen evidence contract are absent
**Then** the method remains diagnostic/quarantined and receives no simulated fill or binding economics authority
**And** absence of retail demand/UX is not considered a Stage A defect.

**Given** exact-SHA Claw installed-artifact validation and independent review
**When** manifests, transitive dependencies, imports, OCI layers, strings/symbols, network surface, and graph ownership are checked
**Then** capability absence is proven on built artifacts, not only by source grep
**And** traceability links FR40, FR45, and FR46 to NFR1-NFR5, NFR13-NFR26, NFR27-NFR41, and AR1-AR10; quarantine removal requires a separate future approval chain.

## Epic 4: The operator obtains a reproducible Stage A decision

The operator receives a sealed AnalysisRun, deterministic replay, and a report with
one of four mutually exclusive Stage A decisions, fully bound to
the original evidence, configuration, code, exact-SHA Claw gates, release/deploy
boundaries, and rollback evidence; the decision never authorizes live
trading.

**Implementation prerequisite:** Epics 1-3 provide a verified package,
reconstruction, and frozen aggregate. Stage A remains an internal hypothesis test;
Claw permits realtime apply/rollback only within the isolated test scope.

### Story 4.1: Create and seal an immutable AnalysisRun in isolation

As an internal operator/researcher,
I want to record all derived outputs under a separate immutable AnalysisRun,
So that the result is fully reproducible and never changes the original CaptureRun.

**Acceptance Criteria:**

**Given** a sealed `CaptureRun`, verified `FrozenPackageReceipt`, exact analyzer artifact/code, and frozen config identities
**When** analysis begins
**Then** a separate immutable `AnalysisRun` root is created with its own registry, logical-key scope, versioned node kinds, analysis-only writer privilege, and lifecycle state machine
**And** missing/mismatched capture terminal, package, artifact, code, or config identity blocks run creation.

**Given** open AnalysisRun
**When** reconstruction, quality, economics, strategy, portfolio, decision, replay, or report evidence is written
**Then** the writer accepts only ANALYSIS-owned node kinds and declared typed input/derived edges
**And** no function/role changes capture roots, registry, payload, receipt, or retention namespace.

**Given** complete analysis graph
**When** AnalysisRun seals
**Then** the terminal document canonicalizes input identities, output/node counts, canonical bounds, graph root, output digest, and analysis terminal hash
**And** post-seal analysis writes are rejected; a correction/re-run creates a new AnalysisRun linked by a provenance edge, rather than reopening/rewriting.

**Given** clean PostgreSQL 16/17 and two fresh processes
**When** exact-SHA Claw runs create/write/seal, cross-root denial, post-seal mutation, and terminal-hash tests
**Then** CaptureRun counts/hashes remain unchanged, AnalysisRun outputs/terminal hashes are deterministic, and DB tests are not skipped
**And** traceability links FR37 and the foundation of FR18/FR24 to NFR6, NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR11; rollback creates a new run with the prior artifact without changing the existing one.

### Story 4.2: Emit one Stage-A verdict under strict fail-closed precedence

As an internal operator/researcher,
I want one typed verdict from frozen predicates,
So that invalid data, insufficiency, and negative economics are not conflated or interpreted as success.

**Acceptance Criteria:**

**Given** AnalysisRun inputs
**When** a package/hash/schema/provenance/closure/replay/mapping integrity failure exists
**Then** the decision is `INVALID_DATASET` and contains only ordered closed-enum `INVALID_*` reasons
**And** economics and a survivor aggregate are not evaluated as a binding result.

**Given** dataset valid
**When** acquisition spans fewer than seven calendar days, complete UTC days are fewer than five, strict healthy minutes are below 95%, required mapping/fee cases are missing, aggregate independent episodes are fewer than 20, an admitted cell is incomplete, or required realized funding evidence is missing
**Then** the decision is `INSUFFICIENT_EVIDENCE` and contains only predicate-specific `INSUFFICIENT_*` reasons
**And** partial boundary days and forecast funding remain diagnostic and do not satisfy the gate.

**Given** the dataset is valid and sufficient
**When** the frozen portfolio aggregate has non-positive total or median net, non-positive USD 1,000 net, negative USD 5,000 net, does not survive 300/500 ms delay or any frozen fee case, or largest-episode contribution is not below 25%
**Then** the decision is `STOP` with only `STOP_*` reasons for all failed binding predicates
**And** an individual negative cell is not an independent verdict but remains within the aggregate with its frozen weight.

**Given** the dataset is valid/sufficient and all binding aggregate predicates pass the exact boundaries
**When** the evaluator completes the precedence INVALID -> INSUFFICIENT -> STOP -> EXTEND
**Then** the decision is only `EXTEND_LONGER_SHADOW` with `EXTEND_ALL_V2_GATES_PASS`
**And** `GO`, `NO_GO`, `KILL`, `plausible`, `inconclusive`, arbitrary reasons, and mixed precedence classes cannot be constructed.

**Given** exact threshold boundaries
**When** exact-SHA Claw runs individual/combinatorial predicate tests
**Then** `0.95` health and `0` USD 5,000 net pass the respective inclusive gates, `0` USD 1,000 net and concentration `0.25` produce STOP, and invalid always has the highest precedence
**And** traceability links FR1-FR3, FR7-FR12, and applicable FR5/FR24 to AR4, NFR15-NFR26, NFR27-NFR41, and AR8-AR11.

### Story 4.3: Reproduce a byte-identical report and analysis replay receipt

As an internal operator/researcher,
I want to repeat analysis in two clean processes and obtain the same evidence-linked report,
So that the Stage-A decision can be independently verified without network, host clock, or hidden state.

**Acceptance Criteria:**

**Given** a verified frozen package, frozen config, exact analyzer identity, and one previously created/hash-bound semantic `AnalysisRun` identity
**When** two fresh processes run final replay without network or host-clock access
**Then** canonical reconstruction/economics/portfolio/verdict/report bytes match, as do graph root, output digest, and AnalysisRun terminal hash
**And** both processes receive identical explicit `analysis_run_id`, input/algorithm/config/code identities, and canonical time inputs; independently generated run IDs, `PYTHONHASHSEED`, filesystem enumeration, locale, audit time, and process order cannot change semantic output.

**Given** report
**When** the operator checks any aggregate metric, per-cell slice, failed attempt, reason, or decision
**Then** a complete path exists to AnalysisRun, policy/config, algorithm/code/artifact, FrozenPackageReceipt, CaptureRun terminal, and raw evidence hashes
**And** per-cell slices reconcile with the binding aggregate, diagnostic trailing is explicitly separated, and missing provenance makes the run invalid.

**Given** replay receipt
**When** AnalysisRun seals
**Then** the receipt binds both process receipt hashes, frozen package digest, capture terminal, analyzer/config/code identities, canonical output digest, graph root, and terminal hash
**And** the receipt belongs only to AnalysisRun, is not written into CaptureRun/frozen package, and is not created when outputs differ.

**Given** exact-SHA Claw validation
**When** fresh-process, no-network/no-clock, reversed-input, different-hashseed, tamper, and provenance-closure tests run
**Then** deterministic replay is proven by immutable receipts
**And** traceability fully links FR5, FR18, FR24, and FR37 to NFR6, NFR15-NFR24, NFR27-NFR41, and AR4/AR8-AR11; replay correction creates a new AnalysisRun.

### Story 4.4: Limit the decision to the internal Stage-A hypothesis

As an internal operator/researcher,
I want to see the exact meaning and boundaries of the Stage-A result,
So that shadow economics is not presented as retail demand, production profitability, or trading authorization.

**Acceptance Criteria:**

**Given** any of the four Stage-A verdicts
**When** the report and machine-readable decision are published
**Then** the primary actor is identified as the internal operator/researcher and the outcome as a reproducible evidence-backed STOP/EXTEND research decision
**And** the document explicitly states that the result does not authorize private API, live trading, customer rollout, custody, Telegram/web authority, or a revenue claim.

**Given** `EXTEND_LONGER_SHADOW`
**When** the operator reads the continuation target
**Then** the immutable target is 7-14 complete UTC days and at least 100 independent completed lifecycles
**And** EXTEND is never a synonym for `GO`; the first live behavior requires a separate future architecture/security/reconciliation/human authorization chain.

**Given** historical USD 10 PUMP/DOGE KILL/EXTEND material
**When** it appears in provenance/research
**Then** it is marked `SUPERSEDED`, is not mixed with the Stage-A-v2 universe/thresholds, and does not affect the verdict
**And** a replacement edge preserves history without a dual-active contract.

**Given** claims about external demand, willingness to pay, revenue, or production profitability
**When** they enter the graph/report
**Then** each claim exists only as a separate unsupported falsifiable Hypothesis with separate actor, outcome, metric, evidence, and approval requirements
**And** absence of retail UX, market research, or monetization evidence does not block honest completion of the internal hypothesis test.

**Given** exact-SHA Claw graph/report tests and independent product/quant review
**When** wording, enums, authority edges, and unsupported claims are checked
**Then** traceability links FR4, FR6, FR8, FR12-FR14 to NFR7, NFR15-NFR26, NFR27-NFR41, and AR1-AR4/AR8-AR11
**And** changing product meaning requires new owner approval, rather than a code-only commit.

### Story 4.5: Establish versioned schemas for the causal release graph

As an internal operator/researcher,
I want to verify each release phase through a separate immutable contract,
So that candidate, promotion, and deployment cannot be conflated or created retrospectively.

**Acceptance Criteria:**

**Given** release contract package
**When** schemas and validators are installed
**Then** candidate receipt, app-stack DB receipt, human promotion request, realized promotion receipt, final release receipt, and deployment authorization have separate closed versioned schemas
**And** each downstream object refers to exact predecessor identities through hash binding and forbids unknown/missing/extra authority fields.

**Given** causal chain candidate -> app-stack DB receipt -> promotion request -> promotion receipt -> final release -> deployment authorization
**When** an object is proposed out of order or with a copied/placeholder receipt
**Then** validation fails closed before build/promotion/deploy mutation
**And** a candidate is not promotion, a final release is not deployment authorization, and rollback identity is mandatory in the final release.

**Given** valid and mixed-SHA/missing-predecessor fixtures
**When** exact-SHA Claw runs schema/canonical-hash/causality tests
**Then** the valid chain is deterministic, and all invalid combinations are rejected with typed reasons
**And** traceability links NFR18, NFR24, NFR33, NFR42-NFR49, and AR6/AR8-AR11 to schemas, validators, tests, and replacement compatibility.

### Story 4.6: Build and scan an exact release candidate on Claw

As an internal operator/researcher,
I want an immutable candidate from the exact validated source SHA,
So that promotion considers only reproducible artifacts with a proven capability boundary.

**Acceptance Criteria:**

**Given** the exact default-branch engine SHA and successful same-SHA validation receipts
**When** Claw builds a release candidate
**Then** separately installable Capture and Analyzer artifacts/OCI identities are built with pinned build inputs, dependency locks, and configuration hashes
**And** installed-file/import/dependency/entry-point/layer proof confirms absence of private/trading/n8n/Go execution capability.

**Given** built candidate artifacts
**When** SBOM, vulnerability, deterministic-build, and identity gates run
**Then** an immutable candidate receipt binds exact source/tree, validation receipts, locks, configs, artifact digests, SBOM, and scan results
**And** a failed gate does not publish a promotable candidate, and cleanup removes isolated build resources without cross-project residue.

**Given** realtime candidate iterations on Claw
**When** an agent applies or rolls back build inputs in the test namespace
**Then** each attempt receives a separate identity/receipt and does not overwrite a previous candidate
**And** traceability links NFR2-NFR4, NFR13, NFR18, NFR27-NFR41, and AR5/AR8-AR11; mutable tags are not identity authority.

### Story 4.7: Materialize the exact app-stack and prove the DB contract

As an internal operator/researcher,
I want to verify the exact app-stack source and database boundary before promotion,
So that the release does not depend on a dirty checkout or an incorrect partition contract.

**Acceptance Criteria:**

**Given** exact private app-stack SHA
**When** the trusted Claw workflow materializes source
**Then** it uses an authenticated exact archive with the token only in the step environment, verifies traversal/links and tree identity, and leaves no persisted credentials
**And** dirty `/home/operator/app-stack` is not fetched/reset/checked out/mutated.

**Given** app-stack with fix `3ce7e1f` or an independently reviewed equivalent
**When** the isolated PostgreSQL 16/17 DB contract suite runs
**Then** the receipt binds exact app SHA, migrations, roles/grants, relkind=`r` table-partition scans, constrained writer, views, and frozen-reader evidence with no skipped tests
**And** index partitions are not treated as table partitions, and missing equivalent evidence blocks release.

**Given** PR #42-equivalent materialization repair and PR #39-equivalent no-push control
**When** the app-stack contract is checked
**Then** trusted exact archive repair precedes no-push validation, and automatic push deploy is absent
**And** an exact app-stack DB receipt is created only after independent DevOps/data review; traceability links NFR42-NFR49 and AR6-AR11.

### Story 4.8: Authorize promotion and complete the final release receipt

As an internal operator/researcher,
I want to explicitly bind candidate and app-stack evidence before promotion,
So that a deployable release has an unbroken human-approved causal lineage and an exact rollback target.

**Acceptance Criteria:**

**Given** a valid candidate receipt and exact app-stack DB receipt
**When** the owner issues a human promotion request
**Then** the hash-bound request binds both inputs, target environment class, allowed artifacts, and previous rollback identity
**And** missing/mismatched approval identity or stale input blocks promotion.

**Given** valid promotion request
**When** Claw performs promotion
**Then** the realized promotion receipt records the immutable digests/identities actually promoted and does not trust requested values without post-action verification
**And** failure/partial promotion remains evidence-linked and creates no final release.

**Given** realized promotion receipt
**When** the final release completes
**Then** the final receipt binds source, validations, scans, artifacts, app-stack contract, human request, realized promotion, config/schema compatibility, and exact prior rollback digest
**And** independent DevOps/security review confirms NFR18, NFR24, NFR27-NFR49, and AR5-AR11; the final receipt still does not constitute deployment authorization.

### Story 4.9: Deploy and observe only mee-a2 in an isolated Claw test environment

As an internal operator/researcher,
I want to deploy the exact public-capture release only within the isolated `mee-a2` test boundary,
So that Stage-A evidence can be collected and semantic progress proven without affecting other services.

**Acceptance Criteria:**

**Given** a final release receipt and separate explicit deployment authorization
**When** controlled test deployment starts
**Then** the immutable exact app-stack archive/checkout verifies engine/app SHAs, candidate/promotion/final receipt hashes, image digest, config hash, clock, and DB contract
**And** dirty `/home/operator/app-stack` is not fetched/reset/checked out/mutated, and no automatic push trigger exists.

**Given** authorized deployment
**When** Compose is applied
**Then** the target is limited to project `mee-a2` and public-capture services; n8n, unrelated bots/projects, private APIs, and live trading are not started, stopped, or reconfigured
**And** per-run networks, database/schema, volumes, secrets, ports, and evidence paths are isolated from other Claw projects.

**Given** a new capture runtime
**When** post-deploy evidence is collected after a complete UTC minute and the specified soak
**Then** the receipt includes health, ready, WARMING/MEASURING/terminal state, nonzero expected/reporting/valid slots, feed/ownership/database status, image/config/source identity, and current-run PostgreSQL evidence
**And** process-only health or endpoint reachability without semantic progress does not count as a successful rollout.

**Given** a failed start, DB contract, readiness, semantic-minute, soak, or identity gate
**When** rollout evaluation completes
**Then** candidate services stop within `mee-a2`, no success deployment receipt is created, and failure evidence and exact prior-release identity are preserved for recovery
**And** Story 4.9 independently fails closed without mutating unrelated projects; restoration of the prior release is performed by a separate recovery capability.

**Given** a successful test rollout on Claw
**When** independent SRE review checks the deployment/telemetry graph
**Then** NFR42-NFR46, NFR48-NFR49, and AR6/AR7/AR9-AR11 have receipts for authorization, isolation, and semantic evidence
**And** no test receipt is interpreted as production deployment or live-trading approval.

### Story 4.10: Restore the exact prior mee-a2 release and prove cleanup

As an internal operator/researcher,
I want to roll back a failed or selected test rollout to the exact previous release,
So that realtime Claw experiments have an independently verifiable recovery boundary and do not lose evidence.

**Acceptance Criteria:**

**Given** a failed start, DB contract, readiness, semantic-minute, soak, or identity gate
**When** rollback triggers or the operator requests realtime rollback
**Then** the exact prior promoted digest/config is restored only within `mee-a2`, the failed release remains evidence-linked, and append-only CaptureRun data is not rewritten
**And** a cleanup receipt proves absence of orphan containers/networks/temp DB/resources and that unrelated projects remain unchanged.

**Given** the exact prior release is incompatible with schema/config or its digest/receipt is unavailable
**When** recovery preflight runs
**Then** destructive rollback is blocked, the candidate remains stopped, and a typed manual-recovery requirement is preserved
**And** the system does not select a mutable tag, rewrite database evidence, or affect n8n/unrelated projects.

**Given** a successful rollout/rollback exercise on Claw
**When** independent SRE review checks the recovery graph
**Then** NFR42-NFR49 and AR6/AR7/AR9-AR11 have receipts for prior identity, rollback action, post-rollback health/evidence, and cleanup
**And** a recovery receipt is not production approval, and a repeated rollout requires new deployment authorization.
