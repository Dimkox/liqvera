# Unified Strategy, Evidence, and Graph Architecture

**Date:** 2026-08-11
**Status:** owner approved
**Owner approval recorded:** 2026-08-11, explicit `Y` in the governing Codex task
**Repository:** `Dimkox/multi-exchange-engine`
**Audited engine baseline:** `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99`
**Audited deployment baseline:** `Dimkox/openclaw-airgap-farm@7756d546ecff7826cb11c8c74d45929913944b7e`
**Baseline compliance:** not compliant; this document defines a migration target
**Target safety boundary:** public evidence and read-only analysis only; execution capability absent from every Stage A runtime and release artifact

## 1. Purpose

This specification replaces the repository's accumulated runtime ambiguity with
one coherent domain contract and four explicit graphs:

1. a connected traceability graph;
2. an acyclic runtime dependency graph;
3. an append-only evidence graph;
4. an exact-SHA release graph.

The repository has inherited useful methods and invariants from several earlier
systems, but those inputs currently coexist as partially overlapping Go,
`src/`-Python, root-Python, research, and deployment structures. This design
preserves verified value while eliminating multiple active owners for the same
concept.

The first release governed by this specification is Stage A: a credential-free
Hyperliquid/Lighter evidence and shadow-economics system. Stage A may recommend
continued observation. It cannot arm trading or produce a live-trading verdict.

## 2. Audited provenance and current conflicts

The design is grounded in these exact Git objects:

| Source | Exact identity | Architectural meaning |
|---|---|---|
| Engine origin/main | `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99` | Current canonical source baseline |
| Shadow-economics PR #21 base | `5e250e8ae2c2ec25bc0b04f29d91f0283b0befb4` | Branch point for candidate work |
| Shadow-economics PR #21 head | `7fe6918690f8bc1da5826c67e3619de4126e4f54` | Candidate contracts/evidence/frozen-package implementation |
| App-stack origin/main | `7756d546ecff7826cb11c8c74d45929913944b7e` | Current deployment-contract baseline |

The audit found these active conflicts:

- `pyproject.toml` packages only `src/multi_exchange_engine`, while the A2 image
  copies the root `multi_exchange_engine` tree;
- the accepted runtime ADR names a Python modular monolith, while Go remains an
  executable build and no conformance proof records Python parity;
- root Python, `src/` Python, and Go each contain overlapping domain, adapter,
  opportunity, execution, or safety concepts;
- `Dockerfile.a2` copies the root Python tree, and the audited root/`src/` trees
  contain private/execution source; therefore execution absence is not a current
  source-tree fact and must be proved at target artifact and reachability gates;
- PR #21 implements `multi_exchange_engine/shadow_economics` at the repository
  root although its approved design recommended the canonical `src/` package;
- PR #21 is Git-conflicting with current main and cannot be accepted by a
  whole-branch merge;
- the current generic CI workflow uses GitHub-hosted runners despite the owner
  policy requiring all test and validation gates on `claw-engine-runner`;
- app-stack contains an isolated A2 deployment path alongside unrelated legacy
  automation and live-bot systems.

These findings are inputs to the migration. They are not authority to discard
working invariants or to merge unrelated systems into Stage A.

The audited baseline is explicitly **not compliant** with this specification.
All capability-absence, package-separation, graph-completeness, data-integrity,
and Claw-isolation statements below are target invariants and acceptance gates,
not descriptions of the current checkout or deployed image.

## 3. Decision

The project is one modular monorepo and one domain contract implemented through
physically separate installable distributions with distinct top-level import
namespaces. It is not one wheel or one installed package. The canonical Stage A
namespaces are `mee_contracts`, `mee_public_capture`, and
`mee_readonly_analyzer`:

```text
public venue feeds
        |
        v
Public Capture Distribution
        |
        +--> append-only PostgreSQL evidence
        +--> immutable frozen package
                       |
                       v
             Read-Only Analyzer Distribution
                       |
                       +--> deterministic reports
                       +--> Stage A decision
```

The distributions are:

1. **Public Capture** — credential-free venue discovery and public feed access;
   the only distribution allowed to append A2 evidence.
2. **Read-Only Analyzer** — reconstruction, quality, economics, strategies,
   virtual portfolio, reports, and Stage A decision; it has no evidence mutation
   capability and final deterministic analyzer replay has no network capability.
3. **Execution** — absent. There is no Stage A execution artifact, signer,
   private/account stream, order method, cancellation method, transfer method,
   withdrawal method, or dormant execution image.

`mee_contracts` is a pure-contract distribution and the only shared import
boundary. Public Capture and Read-Only Analyzer each depend on that distribution
but never package or import the other's application layer. Physical artifact
separation is mandatory even though the source repository and domain contract
are shared. A feature flag, environment variable, unused import, or combined
wheel is not an acceptable substitute for capability absence. The legacy root
and `src/` copies of the importable `multi_exchange_engine` namespace are
eliminated through an explicit migration, not retained as parallel compatibility
copies.

## 4. Source-of-truth hierarchy

The following versioned manifests are authoritative inputs:

- requirements manifest: stable requirement IDs and approval state;
- architecture manifest: bounded contexts, canonical owners, contracts, and
  permitted dependency edges;
- runtime manifest: executable entry points and capability distributions;
- data-contract manifest: schemas, versions, provenance, and compatibility;
- strategy manifest: admitted strategies, modes, parameters, and evidence gates;
- release manifest: source SHA, dependency identities, artifact identities,
  validation receipts, configuration hashes, and deployment target.

The graph checker validates these manifests. The checker is not itself a source
of truth and may not invent ownership, infer an unstated contract, or silently
repair ambiguity.

Authority order is:

1. owner-approved requirements and architecture manifests;
2. accepted ADRs and versioned contracts;
3. reachable code and migrations;
4. tests and evaluations;
5. Claw gate definitions and receipts;
6. release and deployment evidence;
7. telemetry and generated reports;
8. research and archived material.

Generated documentation and reports are projections. They cannot override their
source manifests.

## 5. Stable requirements

### 5.1 Product requirements

- **PROD-001:** Stage A must determine whether reproducible Hyperliquid/Lighter
  strategies survive executable depth, costs, delay, data quality, and capital
  constraints.
- **PROD-002:** Stage A decisions are exactly `STOP`,
  `EXTEND_LONGER_SHADOW`, `INSUFFICIENT_EVIDENCE`, or `INVALID_DATASET`.
- **PROD-003:** Stage A must be able to complete honestly without a positive
  strategy result.
- **PROD-004:** Research, documentation, a green test, or a positive simulation
  must not authorize live trading.
- **PROD-005:** Strategy outputs are explainable from immutable input evidence,
  configuration, and code identity.
- **PROD-006:** The primary Stage-A-v2 actor is an internal operator/researcher;
  the intended outcome is a reproducible evidence package and a typed decision
  about whether continued public shadow observation is justified.
- **PROD-007:** Stage-A-v2 has `acquisition_window = 7` calendar days and
  `minimum_binding_evidence = 5` complete UTC days. Partial UTC days may support
  diagnostics but cannot satisfy the binding minimum.
- **PROD-008:** Stage-A-v2 primary venues are Hyperliquid and Lighter and primary
  market assets are BTC, ETH, and SOL. A Solana-chain strategy or execution
  runtime is distinct from observing SOL markets and remains quarantined.
- **PROD-009:** A binding dataset requires at least 95% strict healthy minutes,
  verified economic mappings, and at least 20 independent episodes. Strict
  health is computed from frozen minute-level predicates rather than readiness
  or process uptime.
- **PROD-010:** Continuation economics require positive total and median net P&L,
  survival at symmetric 300 ms and 500 ms leg delay, positive net at USD 1,000
  size, nonnegative net at USD 5,000 size, survival under both frozen fee cases,
  and largest-episode contribution below 25% of total positive net P&L.
- **PROD-011:** A funding-specific continuation reason additionally requires
  realized funding cashflows; forecasts cannot satisfy the funding verdict.
- **PROD-012:** `EXTEND_LONGER_SHADOW` names a frozen extension target of 7 to 14
  complete UTC days and at least 100 independent completed lifecycles. It is the
  only positive Stage A outcome and is never equivalent to `GO`.
- **PROD-013:** The historical USD 10, PUMP/DOGE, and KILL/EXTEND contract is
  `SUPERSEDED` for Stage-A-v2 and remains provenance only; it cannot supply
  current thresholds, assets, decisions, or acceptance evidence.
- **PROD-014:** External customer demand, willingness to pay, revenue, and
  production profitability are unsupported hypotheses, not outcomes established
  by Stage A. They require separate actors, metrics, evidence, and approval.

### 5.2 Architecture requirements

- **ARCH-001:** One modular monorepo and one domain contract own three canonical,
  separately installable distributions with distinct top-level import
  namespaces: pure `mee_contracts`, `mee_public_capture`, and
  `mee_readonly_analyzer`. The legacy duplicate root/`src/`
  `multi_exchange_engine` namespace is eliminated by migration.
- **ARCH-002:** Public Capture and Read-Only Analyzer have separate build
  metadata, dependency closures, installable artifacts, entry points, and
  independently validated capability boundaries; neither artifact contains the
  other's application layer.
- **ARCH-003:** As a target invariant, execution capability is absent from Stage
  A runtime reachability, dependencies, installed files, artifacts, entry points,
  configuration, and deployment. The audited baseline does not yet satisfy this
  invariant.
- **ARCH-004:** Shared imports are limited to the pure `mee_contracts` namespace,
  which contains the exact domain kernel and explicit versioned contracts and no
  application, adapter, storage, network, or workflow implementation. Capture
  and analyzer never import each other's namespace or application layer.
- **ARCH-005:** Venue adapters expose capability-specific contracts. Public
  market data, account/reconciliation, trading, and RFQ are not collapsed into
  one interface.
- **ARCH-006:** PostgreSQL is the authoritative durable evidence store; final
  analyzer replay authority comes from a verified frozen evidence package and
  is recorded only under its `AnalysisRun`.
- **ARCH-007:** Telegram, web, and reports are projections and never execution
  authority.
- **ARCH-008:** Every executable entry point, module, configuration, and
  workflow has one canonical owner in the architecture manifest.
- **ARCH-009:** `mee_contracts` installs, imports, and passes contract tests
  independently of Capture and Analyzer and has no application, adapter, storage
  implementation, network client, database driver, or workflow dependency.

### 5.3 Go-conformance requirements

- **ARCH-GO-001:** From migration M0, existing Go invariants are classified
  `TEST_ONLY_EXECUTABLE_SPEC` until an owner-approved Python conformance suite
  proves equivalent behavior.
- **ARCH-GO-002:** Go reference code is not removed, archived, or declared
  superseded merely because a Python type or test has the same name.
- **ARCH-GO-003:** Conformance evidence must map each retained invariant to a
  canonical contract, Python implementation, negative tests, Claw receipt, and
  explicit review result.
- **ARCH-GO-004:** Go source, binaries, build layers, modules, entry points, and
  transitive dependencies are excluded from every Stage A runtime and release
  artifact beginning at M0.
- **ARCH-GO-005:** Conformance governs whether a Go reference may be retired; it
  never makes Go deployable or packageable in Stage A. Historical provenance
  remains in Git after retirement.

Retained invariants include exact arithmetic, fail-closed unknown outcomes,
reconciliation before retry, exact order ownership, monotonic cumulative fills,
risk reservation, bounded residual exposure, append-only events, and explicit
tenant/account identity. Execution-related invariants remain test-only
specification in Stage A; target artifact gates must prove execution capability
absence independently of that reference source.

### 5.4 Data requirements

- **DATA-001:** Raw evidence is immutable, append-only, and tied to an exact run,
  connection epoch, batch sequence, ingest identity, schema version, decoder
  version, collector SHA, and payload hash.
- **DATA-002:** A2 records public wire evidence and control/quality evidence; it
  does not own normalized books, opportunities, economics, strategies, or
  verdicts.
- **DATA-003:** Analyzer input is available through an explicitly read-only,
  deterministic PostgreSQL view contract and through an immutable frozen
  package implementing the same evidence-reader contract.
- **DATA-004:** Final deterministic analyzer replay belongs exclusively to an
  `AnalysisRun`, reads only its hash-verified frozen package, uses no network or
  host clock, never mutates `CaptureRun`, and produces byte-identical canonical
  output in two fresh processes.
- **DATA-005:** Money, price, quantity, fees, funding, and P&L use exact decimal,
  fixed-point, or rational arithmetic. Ambiguous floats and non-finite values
  are rejected.
- **DATA-006:** Economic identity includes underlying, product/payoff kind,
  multiplier, quote, settlement/collateral, units, venue market ID, validity
  window, and source evidence. Ticker equality is insufficient.
- **DATA-007:** A reconstructed book requires an authoritative snapshot,
  continuous venue-valid sequence/nonce transitions, positive finite levels,
  correct ordering, and a non-crossed spread.
- **DATA-008:** A gap, regression, reconnect, unsupported transition, or malformed
  payload closes the active reconstruction epoch until a new valid snapshot.
- **DATA-009:** Executable economics uses full-depth VWAP for both legs and both
  entry and exit. Missing depth yields rejection, never top-of-book fallback.
- **DATA-010:** Every derived checkpoint, opportunity, simulation, report, and
  decision has a complete path back to raw evidence and configuration hashes.
- **DATA-011:** Every capture session has one immutable, unpartitioned
  `CaptureRun` root and every capture-owned evidence object has one unpartitioned
  capture-node registry row bound to that root before payload storage is admitted
  to any day partition.
- **DATA-012:** Evidence edges reference the registry through typed foreign keys
  for both endpoints, declare a versioned edge kind and endpoint-type contract,
  and reject dangling, type-incompatible, or unauthorized cross-run edges.
- **DATA-013:** Logical evidence keys are globally unique within their declared
  scope through an unpartitioned uniqueness authority. A day partition, local
  partition index, or application-side pre-check is never the authority for
  uniqueness across the dataset.
- **DATA-014:** Evidence mutation uses one constrained writer contract that
  atomically enforces run-root, node-registry, typed-edge, logical-key, hash, and
  append-only invariants. Runtime writer roles cannot bypass that contract with
  direct table DML or alternate ingestion paths.
- **DATA-015:** Capture terminalization seals `CaptureRun` by recording expected
  and observed counts, terminal indices and epochs, canonical time bounds, graph
  closure, and a capture terminal hash. `FrozenPackageReceipt` is admissible only
  from a sealed `CaptureRun` and references its exact terminal hash and complete
  capture node set.
- **DATA-016:** Frozen-package semantic validation parses every raw envelope,
  recomputes payload, mapping, and quality hashes, and verifies run, venue,
  connection epoch, sequence/index, source/receive time, counts, and duplicate
  logical keys. Before `CaptureRun` seals, capture validation emits a capture-owned
  replay-integrity receipt; the seal and frozen package must close over that
  receipt plus capture lifecycle, soak, decoder-observation, and connection
  evidence. Post-package deterministic analyzer replay evidence belongs only to
  `AnalysisRun` and is never inserted into or used to reopen `CaptureRun`. Any
  mismatch or missing closure yields `INVALID_DATASET`.
- **DATA-017:** Raw evidence cannot be dropped, detached, expired, or otherwise
  made unavailable until every affected sealed `CaptureRun` has a retrievable
  verified `FrozenPackageReceipt` whose hashes and graph closure were
  independently checked. Retention is recorded under a separate
  `RetentionAction` root linked to that receipt.
- **DATA-018:** Evidence `derived_from` and `supersedes` edges form an acyclic
  derivation DAG. A superseded node has at most one direct successor in the same
  semantic lineage; competing successors create a blocking conflict rather than
  an implicit fork.
- **DATA-019:** Capture terminalization is serialized against capture admission.
  After `CaptureRun` is sealed, all new capture-owned payload, registry, logical
  key, edge, or lifecycle writes under that root are rejected; race tests prove
  capture admission cannot commit across the seal. Separate `AnalysisRun` writes
  never mutate or append nodes under `CaptureRun`.
- **DATA-020:** Canonical evidence records a hashed evidence/effective time used
  by capture integrity checks, analyzer replay, and decisions. Noncanonical
  insertion, observation, or audit time is
  stored separately, excluded from semantic hashes, and cannot affect ordering,
  economics, or deterministic output.
- **DATA-021:** Digest-pinned PostgreSQL 16 and 17 matrices run the complete
  migration chain plus schema, role/grant, writer-contract, concurrency,
  terminalization-race, deterministic-view, and frozen-reader suites from clean
  databases.
- **DATA-022:** The Analyzer database role has only the required `CONNECT`,
  schema `USAGE`, and deterministic-view `SELECT` grants. It has no table DML,
  sequence privileges, writer-function `EXECUTE`, ownership, role inheritance,
  or alternate mutation path.
- **DATA-023:** Every analysis has a separate immutable `AnalysisRun` root that
  references the exact sealed `CaptureRun`, verified `FrozenPackageReceipt`,
  analyzer artifact/code identity, and configuration identity. Reconstruction,
  quality, economics, strategy, deterministic analyzer replay, verdict, and
  report nodes belong to that root, which seals with its own counts, closure,
  and analysis terminal hash.
- **DATA-024:** Every retention operation has a separate immutable
  `RetentionAction` root referencing the sealed `CaptureRun` and verified
  `FrozenPackageReceipt`; it records the exact affected partitions/objects,
  authorization, result, and retention-evidence hash without mutating either run.
- **DATA-025:** Cross-root edges are allowed only through versioned typed
  contracts. Capture, analysis, package-receipt, and retention namespaces have
  distinct logical-key scopes, registries, writer privileges, and terminal
  state machines; an edge cannot imply ownership transfer or reopen a sealed
  root.

### 5.5 Strategy requirements

- **STRAT-001:** An active strategy consumes immutable reconstructed evidence
  and versioned configuration and emits shadow observations/simulations, never
  order commands.
- **STRAT-002:** Price/basis convergence is an active Stage A strategy. Entry and
  exit are evaluated independently on delayed executable books with full costs.
- **STRAT-003:** Realized funding carry is an active Stage A strategy. Forecast
  funding and realized settlement cashflows remain distinct, with correct sign,
  schedule, entry, exit, basis, and holding-cost attribution.
- **STRAT-004:** Paired-basis trailing is diagnostic only. It may compare a
  deterministic trailing exit policy against frozen baselines but cannot cause
  `EXTEND_LONGER_SHADOW` by itself and cannot conceal failure of active primary
  strategies.
- **STRAT-005:** Strategy, inventory, exit, execution, and portfolio policies are
  separate contracts. A trailing exit is not a venue adapter; a grid inventory
  policy is not an order transport.
- **STRAT-006:** Grid, DCA, Infinity Grid, Solana strategies, maker-fill claims,
  and asset-specific legacy bots are quarantined from Stage A runtime and
  artifacts.
- **STRAT-007:** Quarantined material may be used only as provenance-labelled
  research or test-case input. Promotion requires a separate approved strategy
  manifest, economic contract, evidence gate, and boundary review.
- **STRAT-008:** Parameters, thresholds, cost assumptions, and comparison
  baselines are frozen before the binding evidence window. Post-hoc tuning may
  appear only as clearly labelled diagnostic sensitivity output.
- **STRAT-009:** Independent episodes, capital locks, deterministic prioritization,
  and concentration reporting prevent duplicate opportunity counting.
- **STRAT-010:** Failed attempts, residual-neutralization cost, rebalance cost,
  fees, delay decay, and infrastructure allocation are attributable rather than
  omitted from successful-path economics.

### 5.6 Graph requirements

- **GRAPH-001:** The traceability graph connects every active requirement through
  contract, reachable code/dataflow, tests/evaluations, Claw gate, artifact,
  deployment boundary, telemetry/evidence, and rollback.
- **GRAPH-002:** The runtime dependency graph is a directed acyclic graph. Cycles
  across bounded contexts or application layers block commit.
- **GRAPH-003:** The evidence graph is append-only. Corrections supersede prior
  nodes with provenance edges; they do not rewrite recorded evidence.
- **GRAPH-004:** The release graph binds exact source SHA, dependency locks,
  configuration hashes, tests, scans, artifact digest, promotion receipt,
  deployment identity, health evidence, and rollback target.
- **GRAPH-005:** No active file, module, configuration, workflow, document,
  branch purpose, state, migration, test, or artifact may be orphaned.
- **GRAPH-006:** A checker validates graph completeness, ownership, reachability,
  acyclicity, compatibility, and allowed edges from versioned manifests.
- **GRAPH-007:** A checker failure blocks commit and merge. Checker bypasses are
  not a valid release path.
- **GRAPH-008:** Every graph node has lifecycle state `DECLARED`, `IMPLEMENTED`,
  `VERIFIED`, `REALIZED`, or `RETIRED`, plus optional orthogonal classification
  `MIGRATING` or `QUARANTINED`; allowed transitions are versioned and fail closed.
- **GRAPH-009:** Pre-commit requires a complete declared prospective traceability
  path for every changed node. Actual receipts are required only for gates
  applicable to the node's current lifecycle phase; a planned gate names an
  expected evidence type and is never represented as a receipt.
- **GRAPH-010:** Merge, release, promotion, and deployment progressively require
  actual immutable receipts for their phase-applicable gates. Placeholder,
  synthetic, future-dated, empty, or copied receipts are forbidden.
- **GRAPH-011:** A migration has exactly one active canonical owner. The replaced
  owner is classified `MIGRATING`, is runtime-unreachable, and has a declared
  expiry, removal gate, rollback edge, and blocking conflict if the expiry is
  exceeded; dual active ownership is forbidden.
- **GRAPH-012:** Product traceability connects `Actor -> Outcome -> Requirement ->
  AcceptanceCriterion/KillCriterion -> Metric -> Contract -> DataFlow ->
  TestOrEval -> ClawGate -> Artifact -> Evidence`, with Hypothesis nodes linked
  separately and never promoted to Outcome without falsifiable evidence.

### 5.7 CI requirements

- **CI-001:** All test, validation, build, scan, and promotion gates run only on
  `claw-engine-runner` / `[self-hosted, claw]`.
- **CI-002:** No GitHub-hosted runner is an automatic or required project gate.
- **CI-003:** Trusted PR validation is anchored in the default branch, accepts an
  exact same-repository PR SHA, uses minimal read-only permissions, and persists
  no checkout credentials.
- **CI-004:** Workspaces, virtual environments, test databases, evidence output,
  and temporary files are isolated by run/attempt/job and cleaned deterministically.
- **CI-005:** A PR validation gate has no deploy, promotion, registry mutation,
  venue credential, private API, or live-trading authority.
- **CI-006:** Actions, base images, PostgreSQL versions, scanners, and build
  inputs are version/digest pinned.
- **CI-007:** A release receipt is produced only after all required graph,
  contract, test, `AnalysisRun` deterministic-replay, SBOM, vulnerability, and
  artifact-identity gates succeed for the same exact SHA.
- **CI-008:** Claw PR validation runs in a disposable sandbox isolated from the
  host Docker socket, production networks, production databases, registry or
  release credentials, and deployment authority. Test services use per-run
  credentials and isolated networks that cannot route to production.

### 5.8 Security requirements

- **SEC-001:** Public Capture contains no signer, wallet, venue credential,
  private/account selector, order, cancel, transfer, or withdrawal capability.
- **SEC-002:** Read-Only Analyzer cannot mutate capture evidence; its final
  `AnalysisRun` replay has no direct venue network client.
- **SEC-003:** Stage A artifacts do not package private trading adapters, legacy
  live bots, n8n workflows, or execution libraries.
- **SEC-004:** Secrets are never committed, logged, embedded in manifests, copied
  into artifacts, or exposed in error representations.
- **SEC-005:** Read-only and public-only boundaries are proved by static scans,
  dependency inspection, negative mutation tests, artifact inspection, and an
  independent security review.
- **SEC-006:** Missing provenance, fee evidence, mapping evidence, capability
  classification, or contract version fails closed.
- **SEC-007:** Artifact-boundary proof inspects the built and installed file
  manifests, resolved import graph, transitive dependency closure, entry points,
  image layers, forbidden capability symbols/strings, network-capability surface,
  database grants, and negative mutation tests. Source-layout inspection alone
  is insufficient.

### 5.9 Operations requirements

- **OPS-001:** App-stack consumes only an exact promoted image digest plus a
  verified release receipt and configuration hash.
- **OPS-002:** Deployment materializes an immutable exact app-stack commit in an
  isolated checkout and never syncs, resets, cleans, or overwrites the dirty
  `/home/operator/app-stack` worktree.
- **OPS-003:** Controlled deployment targets only the `mee-a2` Compose project and
  cannot start, stop, or reconfigure n8n, unrelated bots, or other app-stack
  services.
- **OPS-004:** Start requires explicit deployment authorization, exact engine
  revision, approved run ID, validated registry, clock evidence, DB contract,
  and candidate receipt.
- **OPS-005:** Health, readiness, soak state, image identity, configuration
  identity, and current-run PostgreSQL evidence are captured after deployment.
- **OPS-006:** Rollback targets an exact previously promoted digest and preserves
  append-only evidence; rollback never rewrites the source dataset.
- **OPS-007:** Automatic push deployment is forbidden.
- **OPS-008:** Deployment is blocked until app-stack includes database-contract
  fix `3ce7e1f` or an independently reviewed equivalent with the same migration,
  role, partition, writer, and frozen-reader evidence bound to its exact SHA.

## 6. Canonical bounded contexts and dependency direction

```text
Pure Contracts distribution / `mee_contracts`
  exact arithmetic, economic identity, evidence interfaces, provenance,
  reason codes; no application or infrastructure code
             ^                                      ^
             |                                      |
Public Capture distribution              Read-Only Analyzer distribution
`mee_public_capture`                      `mee_readonly_analyzer`
  Public Venue Adapters                     PostgreSQL/frozen readers
           |                                         |
  Capture Application                      Reconstruction -> Quality/VWAP
           |                                         |
  constrained A2 writer                    Economics -> Strategies -> Portfolio
                                                     |
                                             Decision / deterministic report
```

Each box is an independently installable distribution and each label names a
distinct top-level import namespace. Permitted direction is from
application-specific distributions toward `mee_contracts`. The contracts
distribution imports no adapter, storage implementation, strategy, application,
workflow, or deployment code. There is no dependency edge between the two
application distributions.

`mee_public_capture` must not import or package reconstruction, economics,
strategies, portfolio, decision, or analyzer modules.
`mee_readonly_analyzer` must not import or package capture applications, writers,
venue network adapters, or mutation capabilities. App-stack must not become a
source-code dependency of any engine distribution.

## 7. Graph model

### 7.1 Traceability graph

Required node kinds:

```text
Actor
Outcome
Hypothesis
Metric
Requirement
AcceptanceCriterion
KillCriterion
Approval
ADR
Contract
SourceModule
DataFlow
Configuration
Migration
TestOrEval
ClawGate
Artifact
Deployment
Telemetry
Evidence
Rollback
Conflict
```

Required edge kinds include:

```text
serves
intends
measured_by
falsified_by
approved_by
specified_by
owned_by
implements
consumes
produces
validated_by
gated_by
packaged_in
deployed_by
observed_by
evidenced_by
rolled_back_by
supersedes
conflicts_with
resolved_by
derived_from
```

Every active requirement must have at least one complete forward path from
approval to operational evidence and rollback. Every active implementation node
must have a reverse path to an approved requirement.

The complete product path begins with an internal Actor and intended Outcome,
then passes through Requirement, AcceptanceCriterion or KillCriterion, Metric,
Contract, reachable DataFlow, TestOrEval, ClawGate, Artifact, and realized
Evidence. Unsupported external-demand or revenue claims remain Hypothesis nodes
connected by `falsified_by`; they are not silently treated as product outcomes.

Each node has exactly one lifecycle state:

```text
DECLARED -> IMPLEMENTED -> VERIFIED -> REALIZED -> RETIRED
```

`MIGRATING` and `QUARANTINED` are orthogonal classifications, not alternative
proof states. A transition may skip no required phase gate. `RETIRED` nodes keep
provenance and rollback edges but are inactive. A migration declares exactly one
active canonical owner, an expiry, and a removal gate; its predecessor is
runtime-unreachable while classified `MIGRATING`.

### 7.2 Runtime dependency DAG

The dependency graph contains only runtime-reachable modules, entry points,
configurations, migrations, and external capabilities. It must be acyclic and
must prove both positive reachability and capability absence.

Tests, docs, research, and archived code are classified separately and cannot
make a runtime capability appear absent merely because it is not called in one
test.

### 7.3 Append-only evidence graph

Each evidence node has:

```text
schema_id
record_id
producer_identity
source_commit_sha
configuration_hash
input_hashes
effective_at_evidence_time
recorded_at_audit_time
payload_hash
predecessor_or_supersedes_edges
```

`effective_at_evidence_time` is canonical and hashed. `recorded_at_audit_time` is
noncanonical, unhashed audit metadata. Replay, ordering, derivation, economics,
terminal hashes, and decisions use only canonical evidence time plus declared
canonical sequence/index fields; audit time cannot break ties or change output.

A corrected mapping, fee schedule, decoder, or report creates a new node. The
old node remains addressable. Binding analyzer replay selects exact node
identities from the frozen manifest into its `AnalysisRun`.

`derived_from` and `supersedes` must remain acyclic. Supersession has one direct
successor per semantic lineage; a second candidate is a blocking conflict node
until deterministic resolution selects one successor.

The durable topology uses separate immutable roots and namespaces:

```text
CaptureRun --sealed_by--> capture_terminal_hash
    |
    +--exported_as--> FrozenPackageReceipt
                            |
                            +--input_to--> AnalysisRun
CaptureRun --------------------------^       |
                                            +--produces--> reconstruction /
                                              economics / deterministic replay /
                                              verdict / report
                                            +--sealed_by--> analysis_terminal_hash

CaptureRun + FrozenPackageReceipt --authorize--> RetentionAction
```

Each root has an unpartitioned registry and typed foreign-key edges. Partitioned
payload tables are storage projections, not identity or uniqueness authorities.
Cross-root edges exist only through declared typed contracts. Sealing a
`CaptureRun` rejects later capture-owned admission, while an `AnalysisRun` and a
`RetentionAction` append only within their own namespaces and never mutate the
capture root. The only replay-related capture node is the capture replay-integrity
receipt admitted before the capture seal. Post-package deterministic replay is an
`AnalysisRun` node. Global logical-key admission, both run closures, frozen
export, semantic validation, and retention evidence remain enforceable
independently of partition day.

### 7.4 Release graph

An admissible release is a connected subgraph containing:

```text
source SHA
dependency locks
contract/schema versions
Claw validation receipts
AnalysisRun deterministic replay receipt
SBOM and vulnerability result
artifact digest and labels
promotion receipt
app-stack SHA
deployment authorization
runtime image/config identity
health/readiness/soak/DB evidence
rollback digest
```

Missing or mismatched nodes make the release inadmissible.

## 8. Conflict nodes and deterministic resolution

A conflict is a first-class blocking graph node, not an informal merge note.

```text
ConflictNode {
  conflict_id
  kind
  left_provenance: repository, commit, blob, path, contract
  right_provenance: repository, commit, blob, path, contract
  canonical_owner
  compatibility_result
  deterministic_resolution_rule
  required_validation
  resolution_evidence
  state
}
```

Conflict kinds include Git text, add/add, ownership, package root, runtime,
dependency, data schema, contract, strategy semantics, state transition,
workflow policy, artifact, and deployment authority.

Automatic resolution is permitted only when a versioned rule has exactly one
result, for example:

- byte-identical or semantic-hash-identical nodes are deduplicated;
- a generated projection is regenerated from its canonical manifest;
- a path move is rewritten through an approved one-to-one path map and all
  imports/reachability tests pass;
- disjoint additive fields are combined only when the owning schema explicitly
  declares them compatible and ordering is deterministic;
- a stale documentation pointer is replaced with its declared active owner;
- workflow changes are composed only when all mandatory gates, minimal
  permissions, exact-SHA validation, and Claw-only policy remain satisfied.

Automatic resolution is forbidden when the result depends on business meaning,
strategy formula, threshold choice, state-machine semantics, schema meaning,
runtime ownership, security authority, or deployment intent. Such ambiguity
leaves the conflict in `BLOCKED`; commit and merge remain forbidden until an
owner-approved decision and validation evidence resolve it.

Line-level Git merge success does not resolve a semantic conflict.

## 9. No-orphan rule and commit definition of done

Before every commit, the project must remain a fully connected
traceability/runtime graph. A changed node must have a complete prospective path
declared even when later release or deployment evidence cannot yet exist. The
minimum chain is:

```text
requirement/spec
-> ADR/contract
-> reachable code/dataflow
-> tests/evaluations
-> Claw gate
-> artifact/deployment boundary
-> telemetry/evidence
-> rollback
```

Pre-commit checks require real evidence for gates applicable to the node's
current lifecycle state and declared future gate/evidence types for later
states. They never require fabricated future receipts. Merge requires actual
implementation and verification receipts; release/promotion requires actual
artifact, `AnalysisRun` replay, scan, and promotion receipts; deployment requires actual
authorization, identity, health, evidence, and rollback receipts. A placeholder,
empty, copied, synthetic, or merely anticipated receipt blocks the transition.

A commit is blocked by any:

- active module or file without canonical ownership and reachability;
- config key without a declared consumer, schema, and test;
- workflow without an approved trigger, owner, consumer, and evidence output;
- document that claims current authority without an active truth edge;
- branch or PR without a requirement/conflict/migration target;
- unreachable or untested state-machine state/transition;
- test or evaluation not included in a Claw gate;
- artifact not bound to the tested exact SHA;
- deployment without telemetry and rollback;
- unresolved conflict node;
- dependency cycle;
- runtime capability not declared in the artifact manifest;
- dual active owners or a `MIGRATING` node past its declared expiry/removal gate;
- a lifecycle transition lacking its phase-applicable immutable receipts.

The graph checker must report the orphan path and blocking requirement. It may
not auto-delete the orphan or rewrite manifests to make the check pass.

## 10. Stage A strategy and decision contract

### 10.1 Stage-A-v2 binding scope and thresholds

The internal operator/researcher acquires public Hyperliquid and Lighter evidence
for BTC, ETH, and SOL over seven calendar days. Binding evaluation requires at
least five complete UTC days; partial boundary days are diagnostic only. The
frozen acceptance predicate requires all of:

- at least 95% strict healthy minutes over the binding window;
- verified economic mappings for every evaluated venue/market pair;
- at least 20 independent completed episodes;
- positive total net P&L and positive median episode net P&L;
- positive net at USD 1,000 size and nonnegative net at USD 5,000 size;
- survival under symmetric 300 ms and 500 ms leg delays;
- survival under both frozen fee cases;
- largest-episode contribution below 25% of total positive net P&L;
- realized funding cashflows for any funding-specific verdict.

All predicates use frozen definitions, mappings, costs, fee cases, delay models,
episode independence, and rounding. Passing them supports only
`EXTEND_LONGER_SHADOW`, whose stated target is 7 to 14 complete UTC days and at
least 100 independent completed lifecycles. It does not support `GO`.

The former USD 10, PUMP/DOGE, and KILL/EXTEND contract is `SUPERSEDED`; it is
retained only as provenance and cannot be mixed into Stage-A-v2 evaluation.

### 10.2 Active primary strategies

**Price/basis convergence** evaluates executable delayed entry and executable
exit on both venues. Funding is reported separately from price edge.

**Realized funding carry** evaluates actual signed funding settlements, entry
and exit costs, basis movement, and holding cost. Forecast funding is retained
as ex-ante evidence and cannot replace realized cashflow.

### 10.3 Diagnostic strategy

**Paired-basis trailing** is a counterfactual exit-policy diagnostic over the
same frozen episodes and executable books. Its configuration must state:

- activation condition;
- high-water/low-water basis definition;
- trail distance;
- minimum hold and maximum hold;
- delayed independent leg exits;
- full exit costs and residual-neutralization assumptions;
- deterministic tie and missing-book behavior.

It cannot change primary evidence sufficiency or issue a Stage A continuation
decision alone.

### 10.4 Quarantine

Grid, DCA, Infinity Grid, Solana-chain programs/strategies, maker-fill
simulations, live Hyperliquid bots, and asset-specific legacy strategies remain
outside the active dependency DAG, artifacts, CI matrix, and deployment graph.
Observing the SOL market on the primary venues does not admit Solana-chain
runtime. Quarantined files may remain in Git history or a provenance-labelled
research/archive area, but they are not active modules.

### 10.5 Stage A decisions

Decision predicates are disjoint and evaluated in this strict precedence:

1. `INVALID_DATASET` when any integrity, provenance, schema, terminal-closure,
   frozen-package semantic-validation, graph-closure, or `AnalysisRun`
   deterministic-replay
   invariant fails. Reasons use typed `INVALID_*` codes.
2. Otherwise `INSUFFICIENT_EVIDENCE` when the acquisition window, complete UTC
   days, strict-health coverage, verified mappings, episode count, frozen fee
   cases, or required realized funding evidence is incomplete. Reasons use typed
   `INSUFFICIENT_*` codes.
3. Otherwise `STOP` when any frozen Stage-A-v2 economic, delay, size, fee,
   concentration, total-net, or median-net acceptance predicate fails. Reasons
   use typed `STOP_*` codes naming each failed predicate.
4. Otherwise `EXTEND_LONGER_SHADOW` with `EXTEND_ALL_V2_GATES_PASS` and an
   immutable extension target of 7 to 14 complete UTC days and at least 100
   independent completed lifecycles.

Generic `plausible`, `inconclusive`, or `operational kill` reasons are invalid.
Every emitted reason code maps to a frozen predicate, metric node, and evidence
path. Multiple reasons may be reported only within the single highest-precedence
decision class reached.

There is no `GO` and no live-canary decision in Stage A.

## 11. PR #21 salvage policy

PR #21 is not merged as a branch and is not rebased wholesale. Its exact commits
and blobs remain provenance inputs.

Candidate material eligible for semantic salvage after review:

- immutable scenario/configuration contracts;
- evidence-reader protocol and immutable records;
- frozen-package canonical encoding, writer, reader, hashes, and tamper tests;
- public-only boundary additions that remain compatible with this specification.

Salvage rules:

1. map each retained requirement and blob to this specification;
2. rewrite into the canonical distribution namespace and bounded context;
3. remove duplicate owners rather than retain compatibility copies indefinitely;
4. keep analyzer verification separate from the Public Capture production
   artifact;
5. regenerate projections such as handoff from canonical evidence rather than
   merge conflicting narrative state;
6. run focused tests, full regressions, graph checks, artifact-boundary checks,
   and independent review on Claw;
7. record source commit/blob and rewrite rule in resolution evidence.

PR #21 material is rejected or blocked when provenance is missing, an active
owner already exists, a contract is incompatible, or a deterministic rewrite is
not possible.

## 12. Migration sequence

This is an architectural migration sequence, not an implementation task plan.

### M0 — freeze authority and policies

- version and approve the manifests defined here;
- record all current package/runtime/workflow conflicts as blocking nodes;
- classify Go as `TEST_ONLY_EXECUTABLE_SPEC` and exclude Go source, binaries,
  build layers, dependencies, and entry points from all Stage A runtime and
  release artifacts;
- require Claw-only validation;
- prohibit automatic deployment and preserve dirty app-stack state.

### M1 — establish canonical distributions and graph

- establish the modular-monorepo layout for separately installable
  `mee_contracts`, `mee_public_capture`, and `mee_readonly_analyzer`
  distributions, each with its own build metadata and top-level namespace;
- make tests and entry points exercise the installed distribution they claim to
  validate rather than an incidental repository path;
- migrate required legacy code from the root and `src/`
  `multi_exchange_engine` trees into its one canonical bounded context, then
  eliminate both legacy import roots without compatibility copies;
- permit only one active canonical owner during each migration and bind the
  runtime-unreachable predecessor to an expiry and removal gate;
- introduce graph validation and explicit quarantine classification.

### M2 — preserve and prove domain invariants

- establish exact kernel and evidence contracts;
- map Go invariants to executable conformance specifications;
- use conformance only to govern Go reference retirement, never Stage A artifact
  inclusion or deployability.

### M3 — separate capability distributions

- publish and independently validate the pure Contracts, Public Capture, and
  Read-Only Analyzer distributions, dependency closures, and artifact manifests;
- prove that Capture and Analyzer artifacts neither contain nor import the
  other's application layer and share code only through `mee_contracts`;
- prove absence of execution capability from both;
- inspect installed files, imports, dependencies, entry points, image layers,
  forbidden symbols/strings, network capabilities, database grants, and negative
  mutation behavior rather than trusting source manifests;
- keep database writer and reader privileges physically distinct.

### M4 — unify evidence and analyzer dataflow

- establish separate `CaptureRun`, `AnalysisRun`, and `RetentionAction` roots,
  their registries, terminal hashes, writer privileges, and only the declared
  typed cross-root edges;
- bind each `FrozenPackageReceipt` to the exact sealed `CaptureRun`, and bind each
  `AnalysisRun` to that capture root, receipt, analyzer/code identity, and
  configuration before reconstruction, economics, verdict, and report output;
- require the capture replay-integrity receipt before `CaptureRun` seal and keep
  every post-package deterministic analyzer replay exclusively in `AnalysisRun`;
- stabilize raw evidence, read-only views, frozen package, reconstruction,
  economic mapping, quality, VWAP, costs, episodes, virtual portfolio, and
  decision provenance as one connected causal graph without reopening capture;
- prove clean PostgreSQL 16 and 17 migrations, roles, writer serialization,
  terminal races, deterministic views, and frozen readers on digest-pinned
  databases;
- semantically salvage compatible PR #21 material.

### M5 — admit Stage A strategies

- admit price/basis and realized funding as primary strategies;
- admit paired-basis trailing as diagnostic only;
- keep all quarantined strategies unreachable.

### M6 — release and controlled deployment

- validate, build, scan, and promote exact SHA on Claw;
- consume the exact receipt in an immutable app-stack checkout;
- require app-stack DB-contract fix `3ce7e1f` or a reviewed evidence-equivalent
  exact commit before deployment authorization;
- deploy only `mee-a2` after explicit authorization;
- capture current-run operational and PostgreSQL evidence.

### M7 — retire superseded runtime owners

- remove active reachability only after parity/conformance and graph evidence;
- preserve historical Git provenance and rollback targets;
- do not delete unresolved material merely to satisfy an orphan check.

## 13. Rollback and operational recovery

Rollback is part of the release graph, not a return to ambiguous source state.

- Each release names the previous verified artifact digest, configuration hash,
  schema compatibility, and app-stack SHA.
- Public Capture rollback must preserve sealed `CaptureRun` roots, their terminal
  hashes, and already committed append-only evidence; it cannot reopen a root.
- Analyzer rollback creates a new `AnalysisRun` over the same verified
  `FrozenPackageReceipt` with the prior compatible analyzer artifact and produces
  a separately identified report and terminal hash; it never mutates the prior
  analysis or capture root.
- Retention rollback cannot recreate deleted raw data by rewriting evidence. It
  records a new `RetentionAction` or restoration action linked to the verified
  package receipt and preserves the original retention evidence.
- A schema migration must define forward compatibility, rollback feasibility,
  and evidence preservation before release.
- If rollback cannot preserve or read the evidence contract, deployment is
  blocked before mutation.
- Rollback operates only on the `mee-a2` project and does not touch unrelated
  app-stack services or the dirty `/home/operator/app-stack` worktree.
- Source rollback is an explicit Git change through the same graph and Claw
  gates, never a hidden reset or force update.

## 14. Non-goals

This specification does not authorize or include:

- live orders, cancellation, amendment, transfers, or withdrawals;
- exchange credentials, wallets, signers, private/account streams, or private
  APIs;
- an execution artifact, disabled executor, or live-canary path;
- n8n in the engine data, strategy, execution, or deployment authority path;
- grid, DCA, Infinity Grid, maker execution, volume generation, or asset-specific
  live bot behavior;
- Solana programs, RPC ingestion, Jupiter/Jito/Raydium execution, flash loans, or
  atomic-arbitrage claims;
- Telegram or web product development;
- production RFQ or CEX execution;
- customer-demand or profitability claims from shadow output;
- threshold tuning after binding evidence is observed;
- a microservice split without a measured isolation or scaling requirement.

## 15. Acceptance gates

The architecture migration is acceptable only when all applicable gates pass:

1. **Current-state gate:** the audited baseline remains marked noncompliant and
   every current capability, package, workflow, and data conflict is a blocking
   graph node until resolved by evidence.
2. **Authority/lifecycle gate:** every node has one owner, valid lifecycle state,
   and complete prospective path; phase-applicable receipts are real, migrations
   have expiry/removal gates, and placeholder receipts or dual owners are absent.
3. **Distribution gate:** pure Contracts, Public Capture, and Read-Only Analyzer
   install as separate distributions and namespaces; tests execute installed
   artifacts, cross-application packaging is absent, and legacy duplicate roots
   are eliminated.
4. **Contracts-independence gate:** `mee_contracts` installs, imports, and tests
   alone with no capture, analyzer, adapter, storage implementation, network,
   database-driver, or workflow dependency.
5. **Graph gate:** product traceability is complete, runtime and evidence DAGs
   are acyclic, supersession has one successor, releases are connected, and
   there are no orphans, expired migrations, or blocking conflicts.
6. **Go-specification gate:** Go is `TEST_ONLY_EXECUTABLE_SPEC`, excluded from all
   Stage A runtime/release artifacts and entry points; conformance evidence
   governs only reference retirement.
7. **Artifact/execution-absence gate:** installed files, imports, transitive
   dependencies, entry points, image layers, forbidden symbols/strings, network
   capabilities, DB grants, and negative mutation tests prove public-capture or
   read-only-analyzer boundaries and absence of private/trading capability.
8. **Claw sandbox gate:** exact-SHA PR validation runs only on Claw in a disposable
   sandbox isolated from the Docker socket, production networks/DB, release or
   registry credentials, and deployment authority.
9. **Causal data-topology gate:** separate unpartitioned `CaptureRun`,
   `AnalysisRun`, and `RetentionAction` roots and registries, typed cross-root
   foreign keys, and global logical-key uniqueness are proven independently of
   day partitions.
10. **Capture terminal-race gate:** constrained writer and concurrency tests prove
    serialization of capture admission against seal, rejection of every
    post-terminal capture-owned write, and inability of AnalysisRun to mutate
    CaptureRun.
11. **Terminal/export gate:** `FrozenPackageReceipt` references the exact sealed
    CaptureRun terminal hash and complete capture node set, including the required
    pre-seal capture replay-integrity receipt; AnalysisRun records exact capture/
    receipt/analyzer/config/code identities and seals its distinct output graph
    with an analysis terminal hash.
12. **PostgreSQL matrix gate:** digest-pinned PostgreSQL 16 and 17 both pass the
    full clean migration, schema, contract, writer, concurrency, terminal-race,
    deterministic-view, role/grant, and frozen-reader suites.
13. **Analyzer-role gate:** denial tests prove Analyzer has only CONNECT, schema
    USAGE, and deterministic-view SELECT, with no DML, sequence privilege,
    writer-function EXECUTE, ownership, inheritance, or mutation bypass.
14. **Frozen semantic-validation gate:** every envelope is parsed; payload,
    mapping, and quality hashes are recomputed; run/venue/epoch/index/canonical
    time/count/key invariants and capture lifecycle/soak/decoder/connection plus
    pre-seal capture replay-integrity closure are verified. No post-package
    analyzer replay node is present in CaptureRun or its frozen package.
15. **Retention gate:** raw mutation requires a verified retrievable package
    receipt and a separate RetentionAction referencing CaptureRun and receipt,
    with exact authorization, affected objects, result, and evidence hash.
16. **Data-semantics gate:** canonical effective time is hashed and solely orders
    replay; audit time is unhashed and nonsemantic; reconstruction, identity,
    VWAP, costs, derivation, and lineage are deterministic and fail closed.
17. **Stage-A-v2 product gate:** seven calendar acquisition days, at least five
    complete UTC binding days, HL/Lighter BTC/ETH/SOL scope, at least 95% strict
    healthy minutes, verified mappings, and at least 20 independent episodes are
    proved under frozen definitions.
18. **Economics gate:** total and median net are positive, USD 1,000 is positive,
    USD 5,000 nonnegative, symmetric 300/500 ms and both fee cases survive,
    largest episode is below 25%, and funding reasons use realized funding.
19. **Strategy gate:** only price/basis and realized funding are primary;
    paired-basis trailing is diagnostic and quarantined strategies are unreachable.
20. **Decision gate:** strict precedence is INVALID, INSUFFICIENT, STOP, EXTEND;
    typed predicate-linked reasons are complete, old KILL/EXTEND is superseded,
    and no `GO` or vague reason can be emitted.
21. **Analysis replay gate:** two fresh-process deterministic analyzer replays
    over the same frozen package belong only to AnalysisRun, never mutate
    CaptureRun, and produce byte-identical canonical outputs and matching analysis
    terminal hashes.
22. **CI/release gate:** every required exact-SHA test, evaluation, build, scan,
    SBOM, dependency, artifact-identity, and promotion gate ran on Claw with
    minimal permissions and immutable receipts.
23. **App-stack DB gate:** exact app-stack contains fix `3ce7e1f` or an
    independently reviewed evidence-equivalent before deployment authorization.
24. **Deployment gate:** an immutable app-stack checkout consumes the exact
    promoted digest and targets only `mee-a2` after explicit authorization.
25. **Operations gate:** health, readiness, soak, image/config identity,
    current-run PostgreSQL evidence, and rollback target are recorded.
26. **Independent review gate:** architecture, security/boundary, data/economics,
    trading interpretation, and release evidence have named independent review
    results.

Failure of any mandatory gate blocks merge, promotion, or deployment. Missing
economic evidence produces `INSUFFICIENT_EVIDENCE`; integrity, capture
replay-integrity, or `AnalysisRun` deterministic-replay failure produces
`INVALID_DATASET`. Neither condition is converted into a
positive decision by diagnostics.
