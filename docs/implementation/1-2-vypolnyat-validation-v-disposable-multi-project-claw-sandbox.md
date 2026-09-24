# Story 1.2: Выполнять validation в disposable multi-project Claw sandbox

Status: in-progress

## Story

As an внутренний оператор/исследователь,
I want запускать exact materialized source в изолированном rootless sandbox с verified cleanup,
so that Claw можно полноценно использовать для повторяемых realtime-тестов без production, cross-project или credential authority.

## Current execution checkpoint — 2026-08-13

The source-only Phase A deployment controller has landed and D0 installed its
reviewed 19-artifact controller set. The first separately owner-authorized D1
`begin` stopped fail-closed at `STAGED_INPUT_VERIFY` before nonce consumption,
begin intent, host WAL or host mutation. Engine and app runners remained active
under their original identities; D1 `finalize` was not invoked.

Story 1.2A now owns the blocking installed OCI approval path correction. Its
physical root-owned file path and logical source-relative policy identity must
be supplied and verified separately under `OCIAPATH-001..005`. Story 1.2 stays
`in-progress`; Phase B, C1, C2 and Story 1.3 remain blocked until the corrected
source is reviewed and landed, a separately approved D0 update succeeds, fresh
inventory is accepted and a new D1 approval reaches its required terminal gate.

## Предпосылка и граница authority

Story 1.1 установлена вручную как `TOFU_SOURCE_INSTALL` в `origin/main` commit
`c07f251f844d90ed2ce5c08b49a52169bc231364` через PR #24 и GitHub-authenticated
OWNER issue comment `5264583724`. Это доказательство разрешило установку source с
`authority=NONE`; оно не является validation receipt и не разрешает Story 1.3.

PR #24 approval body SHA-256:
`36b583744f7c46dee34bc713a35c978799fa58923ef7db873c1f32dd375785b3`.
Его nonce истёк без controller-side consumption и имеет terminal status
`RETIRED_UNUSED`. Он является историческим landing evidence и **никогда** не может быть
consumed/replayed Story 1.2.

Story 1.2 начинается от bootstrap source `c07f251...`, но этот commit не является
Phase B controller. После Phase A landing controller SHA/tree/workflow blob динамически
читаются из `origin/main`, независимо проверяются и freeze-ятся как Phase B inputs. PR
source поступает только из проверенного Story 1.1 archive/materialization интерфейса.
Untrusted source никогда не управляет
Podman argv, mounts, image, network, receipt writer, cleanup или nonce store.

Story выполняется четырьмя последовательными PR-подфазами. Их нельзя совмещать:

1. **Phase A — `TOFU_SANDBOX_CONTROLLER_INSTALL`:** новый owner-approved PR от bootstrap
   base `c07f251...` устанавливает
   только trusted sandbox controller, fused archive materializer/extractor, policy,
   receipt verifiers, nonce ledger и reconciler. Новый exact OWNER comment имеет свой
   exact path set, expiry и nonce. Landing остаётся source-only с `authority=NONE`; PR-код
   не исполняется.
   Owner отдельно authorizes test-host provisioning root-owned helper/service/timer/sudoers
   с exact package hashes и rollback. Landing остаётся source-only.
2. **Phase B — minimal probe PR:** exact Phase A controller identity динамически читается
   из уже обновлённого `origin/main`, freeze-ится и валидирует отдельный minimal probe PR
   валидирует отдельный минимальный same-repository probe PR на dedicated Claw runner,
   consumes именно Phase A nonce и выпускает validation/cleanup/self-validation receipts.
   Phase B head после run никогда не изменяется ради admission.
3. **Phase C1 — immutable evidence-proposal PR:** отдельный PR содержит только immutable
   external Phase B run URL/receipt hashes и proposal metadata. Он lands с
   `authority=NONE`, не admits receipts, не transitions conflicts и не помечает legacy
   workflow `SUPERSEDED`.
4. **Phase C2 — evidence-admission PR:** отдельный PR связывает admission с уже
   существующим authenticated Phase C1 merge commit SHA/tree/API payload hash, выводит
   trusted cutoff из его `commit.committer.date` и после независимого review узко admits
   `SELF_VALIDATION`, transitions exact conflicts и помечает legacy workflow `SUPERSEDED`.

Первый successful Phase B self-validation должен одновременно доказать controller,
workflow, source, sandbox, validation и cleanup identities. До принятия этого receipt:

- `authority=NONE` сохраняется;
- trusted policy time и realized receipt admission запрещены;
- Story 1.3, build, scan, promotion, release и deploy заблокированы;
- legacy `.github/workflows/verify-a2-pr-on-claw.yml` не является evidence path.

## Actors, ownership и approval points

| Actor | Responsibility |
|---|---|
| Owner | Утверждает Story 1.2 contract и отдельно authorizes первый follow-up dispatch; не подменяет receipt review. |
| Story 1.2 implementer | Реализует controller-owned sandbox policy, runner, schemas, writers/verifiers и TDD fixtures. |
| Default-branch controller | Разрешает exact PR/archive identity, атомарно consuming bootstrap nonce, формирует закрытый argv и проверяет receipts. |
| Dedicated Claw runner | Exact affinity: labels `[self-hosted, claw, claw-engine-runner]` и `RUNNER_NAME=claw-engine-runner`; запускает rootless Podman только в project/run/attempt namespace. Любой другой runner fail closed. |
| Untrusted validation image/process | Читает exact source read-only и пишет только bounded result files в выделенный output mount. Не получает controller/nonce/credential roots. |
| Independent DevOps/security reviewer | Проверяет rootless/isolation/mount/network/secret/cleanup failure semantics на exact SHA. |
| Graph/governance reviewer | Проверяет node closure, receipt trust context, nonce single-use и отсутствие Story 1.3 authority до self-validation success. |

Approval points: architecture/contract approval перед implementation; owner authorization
первого exact follow-up run; независимые DevOps/security и graph/governance YES перед
admission; отдельная будущая deployment authorization вне этой Story.

## Stable requirements

| ID | Requirement |
|---|---|
| `ST12-REQ-001` | Controller source, workflow and policy execute only from exact default-branch commit; payload is closed to exact PR/head/approval identifiers and cannot select commands, image, mounts, network or output paths. Story uses distinct Phase A install, Phase B probe, Phase C1 immutable evidence-proposal and Phase C2 evidence-admission PRs. |
| `ST12-REQ-002` | Reuse Story 1.1 exact same-repository PR resolver and authenticated archive/tree verifier. Source extraction occurs only after complete verification into a unique private controller-owned workspace. |
| `ST12-REQ-003` | Validation uses rootless Podman and an owner-reviewed immutable `@sha256:` image. Host Docker/Podman sockets, host/production networks, production DBs, credentials, devices, privileged mode, extra capabilities and arbitrary mounts are absent; PID, CPU, memory, time and output limits are mandatory. |
| `ST12-REQ-004` | Controller constructs one closed command set and an empty-by-default environment allowlist. Source mount is read-only; output is a separate bounded writable mount/tmpfs; controller, nonce ledger, runner state and unrelated project paths are never mounted. Image entrypoint/command are frozen and PR source cannot override them. |
| `ST12-REQ-005` | Every mutable name/path/credential is scoped by repository digest plus run ID, attempt, job and matrix shard. Sandbox policy rejects collisions, unscoped names, fixed host ports, shared DB/network names and `/home/operator/app-stack`. |
| `ST12-REQ-006` | Test services, if required, run inside the same per-run internal-only rootless Podman network with random runtime credentials unavailable to PR logs/artifacts; no route to production CIDRs/DNS/endpoints exists. Default is `--network none`. |
| `ST12-REQ-007` | Validation and cleanup produce separate canonical closed-schema receipts. Validation binds repository/PR/head/tree, controller SHA/tree, workflow path/blob, archive/materialization digest, policy digest, validation image digest, exact command-set digest, run/attempt/job/shard and bounded result hashes. Cleanup binds every named resource and verified absence outcome. |
| `ST12-REQ-008` | Cleanup executes on success, failure and cancellation; removes containers/pods/networks/processes/workspaces/output secrets and proves absence. Missing/failed cleanup makes both validation and downstream admission fail closed. |
| `ST12-REQ-009` | Phase A uses a new exact OWNER comment/nonce/path set. The trusted consumer validates the claim, but a separate trusted writer persists exactly one closed-schema consumption record before Phase B untrusted execution using `/var/lib/mee-controller` on exact `claw-engine-runner`: root-owned controller state, bounded file lock plus `O_CREAT|O_EXCL`, file fsync and directory fsync. The record binds repository/comment/body digest/nonce/Phase-A controller/Phase-B PR head/tree/run. Missing host/path/ownership/mode/lock support fails closed. PR24 nonce is `RETIRED_UNUSED` and forbidden. |
| `ST12-REQ-010` | Phase B self-validation receipt binds installed Phase A controller identity, probe source identity, exact pinned actionlint artifact/image digest and result, full graph result, sandbox policy/image, validation receipt and cleanup receipt. Only successful verified self-validation may narrowly admit these realized receipt classes and prospectively resolve controller/sandbox conflicts. |
| `ST12-REQ-011` | All tests/validation use exact dedicated affinity `[self-hosted, claw, claw-engine-runner]` and verify `RUNNER_NAME=claw-engine-runner`, with minimal read permissions, pinned actions and no OIDC write, registry/release/deploy/private API/n8n/live-trading capability. No GitHub-hosted runner is added. |
| `ST12-REQ-012` | Receipt writers/verifiers are trusted controller code, use closed schemas, stable typed diagnostics, bounded parsers and atomic writes. Untrusted output is data only and cannot assert success, cleanup or authority. |
| `ST12-REQ-013` | Multi-project safety is scoped, not global equality: controller reconciles only resources selected by exact ownership labels plus ledger records and proves negative path/mount/reference checks for forbidden/unrelated roots including `/home/operator/app-stack`. Unrelated host state is outside the equality/inventory domain and is never used as a cleanup assertion. |
| `ST12-REQ-014` | Rollback disables Story 1.2 dispatch and restores the exact pre-Phase-A bootstrap source identity `c07f251...`, retires sandbox/self-validation contracts and preserves nonce records. It never mutates app-stack/production. |
| `ST12-REQ-015` | Phase A installs a separate trusted janitor/reconciliation workflow and script. Reconciliation runs at controller startup and through trusted scheduled/manual entrypoints, acts only on exact controller ownership labels plus ledger records, and never asserts global host inventory equality. Hard runner loss blocks cleanup/self-validation receipt until a later trusted reconciliation proves absence. |
| `ST12-REQ-016` | Authenticated archive fetch, member/tree verification and atomic extraction are fused in one trusted default-branch process/private root. No archive bytes or extraction decision cross an untrusted handoff; the exact verified bytes are those atomically materialized read-only for Podman. |
| `ST12-REQ-017` | `ControllerTrustContext` is a closed graph interface implemented across loader/model/checker/CLI. Its `phase_policy_cutoff` is derived internally from the authenticated GitHub Phase C1 merge-commit API projection that already exists before Phase C2 review, never from C2's own future merge and never from free-form CLI input. Realized admission is narrowed to the exact Phase B validation, cleanup and self-validation receipt chain; all other realized receipts and untrusted phase time remain rejected. |
| `ST12-REQ-018` | Owner-authorized Phase A host provisioning installs root-owned `/usr/local/libexec/mee-controller-ledger`, a closed-command sudoers policy, systemd reconciliation service/timer and exact package artifacts by frozen SHA-256. Runner receives no broad sudo/shell/package-manager authority. Install, verification and uninstall/rollback commands are separately hashed and reviewed. |
| `ST12-REQ-019` | Phase C1 lands immutable external Phase B run URL/hashes as proposal-only evidence with `authority=NONE`. Phase C2 is the only evidence-admission mutation: it binds the already-landed authenticated C1 merge identity without modifying Phase B/C1, admits only `SELF_VALIDATION`, records conflict transitions and legacy `SUPERSEDED`, and remains independently reviewed. |

Traceability: `ST12-REQ-001..019` refine `CI-001..CI-008`, `SEC-004..SEC-005`,
`GRAPH-004`, `GRAPH-006..GRAPH-010`, NFR15-NFR21, NFR27-NFR34, NFR38-NFR41
and M6 Task 1.

## Acceptance Criteria

### AC1 — trusted controller and exact source

**Given** an owner-authorized exact follow-up same-repository PR and the exact Phase A
controller SHA/tree/workflow blob dynamically read and frozen from `origin/main`
**When** validation is requested
**Then** trusted code re-verifies PR/head/tree/archive identities and materializes only
that exact source
**And** closed payload validation rejects any PR-controlled command, image, mount,
network, policy, output or receipt field with stable typed diagnostics.

### AC2 — disposable rootless isolation

**Given** verified exact source and the pinned sandbox policy/image
**When** validation executes
**Then** one unique rootless Podman sandbox runs with read-only source, dropped
capabilities, `no-new-privileges`, frozen entrypoint/argv and no host socket
**And** it has no production network/DB, registry/release/deploy/private/live credential,
n8n or app-stack reachability.

### AC3 — multi-project lifecycle isolation

**Given** concurrent Claw runs for multiple projects/attempts/shards
**When** services, migrations or test configuration are created and removed
**Then** all resources use collision-resistant project/run/attempt/job/shard identities,
random scoped credentials and internal-only networks
**And** exact ownership-label+ledger selection plus negative path/mount/reference checks
prove the run did not target unrelated resources or `/home/operator/app-stack`; no global
inventory equality is asserted.

### AC4 — validation and cleanup receipts

**Given** validation success, failure, timeout or cancellation
**When** the controller finalizes the run
**Then** it verifies a closed validation receipt and a separate controller-written cleanup
receipt binding exact identities, results and output hashes
**And** downstream verification requires both hashes and rejects missing, malformed,
mismatched or non-success cleanup.

### AC5 — Phase A install and atomic Phase B nonce consumption

**Given** PR24 nonce is terminal `RETIRED_UNUSED` and Phase A has a new exact OWNER
comment/nonce/path set
**When** the Phase B probe crosses the execution boundary on exact `claw-engine-runner`
**Then** trusted controller under `/var/lib/mee-controller` atomically persists a
target-bound consumption record through the dedicated trusted writer before
launching Podman
**And** replay, concurrent claim, identity mismatch or crash-after-claim cannot execute
again; recovery is an explicit owner-reviewed operation with separate evidence.

### AC6 — first controller self-validation and graph admission

**Given** pinned actionlint, full graph, exact sandbox validation and cleanup are successful
for the same exact Story 1.2 head
**When** independent DevOps/security and graph/governance review the evidence
**Then** a self-validation receipt binds controller/workflow/policy/image/source and both
receipt hashes
**And** only that verified success may admit Story 1.3 and mark the legacy workflow
`SUPERSEDED`; no release/deploy authority is created.

### AC7 — trusted reconciliation and hard-loss semantics

**Given** controller startup, schedule/manual janitor invocation or interrupted prior run
**When** reconciliation executes
**Then** it considers only exact controller ownership labels and `/var/lib/mee-controller`
ledger records, removes/proves absence for owned resources, and emits a trusted result
**And** hard runner loss or unavailable ledger leaves receipts blocked until a later trusted
absence proof; unrelated host inventory is neither enumerated as equality nor mutated.

### AC8 — narrow graph trust admission

**Given** closed Phase B receipt chain and trusted policy time
**When** graph loader/checker/CLI evaluate `ControllerTrustContext`
**Then** only exact validation+cleanup+self-validation identities become admissible
**And** missing context, other receipt kinds, arbitrary realized evidence and untrusted time
remain rejected by stable diagnostics.

### AC9 — owner-authorized host helper provisioning

**Given** Phase A source review and separate owner test-host authorization
**When** provisioning runs on `claw-engine-runner`
**Then** exact-hash packages install root-owned `/usr/local/libexec/mee-controller-ledger`,
closed sudoers commands and systemd reconciliation service/timer with verified owner/modes
**And** the runner has no broad sudo or arbitrary shell/package authority; uninstall restores
the pre-Phase-A host contract while preserving forensic nonce/receipt records as specified.

### AC10 — immutable Phase C1 proposal and Phase C2 admission

**Given** immutable successful Phase B run URL and verified receipt hashes
**When** a Phase C1 proposal lands with `authority=NONE` and a separate Phase C2
evidence-admission PR is reviewed against C1's authenticated existing merge identity
**Then** C1/C2 reference but never rewrite Phase B head/evidence, and only C2 admits
`SELF_VALIDATION`, records exact conflict transitions and legacy `SUPERSEDED`
**And** every other realized receipt class and Story 1.3/release/deploy capability remains
blocked unless separately owned by later stories.

## Tasks / Subtasks

- [ ] Task 1 — Freeze two-PR interfaces and RED security tests (AC1-AC8)
  - [ ] Record exact `c07f251...` controller SHA/tree, workflow blob, PR #24/comment `5264583724` and body SHA-256 `36b583...`; mark its expired nonce `RETIRED_UNUSED` and prove it cannot enter the consumer.
  - [ ] Freeze Phase A exact allowed-path set, new OWNER comment schema/expiry/nonce and Phase B minimal probe path set before either landing/run.
  - [ ] Add closed schemas/fixtures for sandbox policy, validation receipt, cleanup receipt, nonce-consumption record and self-validation receipt.
  - [ ] RED: payload command/image/mount/network injection; mutable image; non-rootless Podman; socket/device/capability/host-network/prod-route access; path/name collision; forged receipt; cleanup failure; nonce replay/concurrency/crash.
- [ ] Task 2 — Phase A: implement trusted controller install slice (AC1-AC3, AC7-AC8)
  - [ ] Create `ci/claw/sandbox-policy.json` with exact allowed image, argv, mounts, network and resource bounds.
  - [ ] Create `ci/claw/run-disposable-validation.sh`; it accepts only trusted environment values, validates rootless Podman, constructs exact argv and never sources/executes a PR-provided controller script.
  - [ ] Fuse authenticated archive fetch, verification and atomic extraction in one trusted default-branch process; no in-memory/archive byte handoff to PR code and no second fetch.
  - [ ] Extend `.github/workflows/validate-pr-on-claw.yml` after Story 1.1 archive verification; preserve trusted default-branch checkout, minimal permissions and final cleanup.
- [ ] Task 2A — Phase A: owner-authorized test-host provisioning (AC9)
  - [ ] Freeze `ci/claw/host-helper-manifest.json` with SHA-256 for every installed helper, systemd unit/timer and sudoers fragment; OWNER comment binds the manifest digest.
  - [ ] Install root-owned `/usr/local/libexec/mee-controller-ledger`, systemd service/timer and exact closed sudoers argv. Prove no wildcard, shell, editor, package-manager or broad sudo command is reachable.
  - [ ] Add idempotent verify and uninstall/rollback procedures with exact file hashes, owner/group/modes and forensic-state retention policy.
- [ ] Task 3 — Phase A: install ledger and trusted reconciliation (AC5, AC7)
  - [ ] Add controller-owned `scripts/consume_bootstrap_nonce.py`, a separate `scripts/write_bootstrap_nonce_consumption.py`, independent `scripts/verify_bootstrap_nonce_consumption.py`, and the closed `schemas/bootstrap-nonce-consumption-v1.schema.json` contract under root-owned `/var/lib/mee-controller`. The consumer validates eligibility; only the writer owns lock/exclusive-create/fsync persistence; the verifier independently re-reads schema and bound identities. Verify exact host, owner/group/mode and dedicated runner; use bounded file lock, exclusive create, file+directory fsync and deterministic replay diagnostics.
  - [ ] Consume before Podman launch; never mount consumption state into sandbox and never delete it during ordinary cleanup/rollback.
  - [ ] Install separate `.github/workflows/reconcile-claw-sandboxes.yml` and `ci/claw/reconcile-owned-resources.sh`; invoke at controller startup and scheduled/manual trusted entrypoints. Select resources only by exact ownership labels plus ledger, never global inventory equality.
  - [ ] Encode hard runner-loss as blocking state until later reconciliation/absence receipt.
- [ ] Task 4 — Phase A: graph interfaces, review and source-only landing (AC8)
  - [ ] Implement closed `ControllerTrustContext` in `tools/graph_checker/model.py`, `loader.py`, `checker.py`, `__main__.py` and `scripts/check-architecture-graph.py`; add focused CLI/fixture tests.
  - [ ] Keep realized admission disabled in Phase A. Obtain new exact OWNER comment and two independent reviews; manually land only frozen Phase A source/host-helper definitions with `authority=NONE`.
  - [ ] After landing, read exact Phase A commit SHA/tree/workflow blob from `origin/main`, independently verify ancestry/content and freeze them for Phase B. Never substitute `c07f251...` as Phase B controller.
- [ ] Task 5 — Phase B: execute minimal exact probe and verify outputs (AC2-AC5)
  - [ ] Use an immutable validation image recorded in `architecture/release.yaml`; no runtime pull by mutable tag.
  - [ ] Pin actionlint `v1.7.12` Linux amd64 archive SHA-256 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8` in policy/release graph; run it and complete graph/tests through the frozen validation entrypoint. Bounded stdout/stderr remain runner logs, not trusted receipts.
  - [ ] Treat PR-produced result files as untrusted input; trusted controller independently validates/hashes them.
- [ ] Task 6 — Phase B: cleanup and receipt chain (AC4, AC7)
  - [ ] Add atomic trusted writers/verifiers for `validation-receipt-v1` and `validation-cleanup-receipt-v1`.
  - [ ] Trap cleanup across success/failure/signals; enumerate exact container/pod/network/process/workspace resources, remove them, prove absence, then write cleanup receipt.
  - [ ] Verify receipt identity/hash linkage; upload only the closed verified receipts after cleanup proof. Never upload raw logs, source, credentials, runtime env or untrusted arbitrary files.
- [ ] Task 7 — Phase B: freeze immutable external evidence (AC6)
  - [ ] Add self-validation schema/verifier linking actionlint, full graph, controller/workflow, policy/image, source and both receipt hashes.
  - [ ] Independent DevOps/security and graph/governance review exact immutable Phase B head/run; record URL/ID and hashes. Do not amend Phase B head after execution.
- [ ] Task 8 — Phase C1: immutable evidence-proposal PR (AC8, AC10)
  - [ ] Land only a closed `phase-c1-evidence-proposal-v1` document containing external immutable Phase B receipts/run URL and proposal metadata with `authority=NONE`; contain no sandbox implementation or admission changes and never rewrite B.
  - [ ] After landing, authenticate and freeze exact C1 merge SHA/tree, canonical GitHub commit API payload hash and `commit.committer.date` for C2 input.
- [ ] Task 9 — Phase C2: evidence-admission PR (AC8, AC10)
  - [ ] Supply closed `ControllerTrustContext` bound to the already-existing authenticated C1 merge identity; never bind trust to C2's own future merge.
  - [ ] Admit only `SELF_VALIDATION`; update architecture manifests/receipt registry/handoff, exact conflict transitions and legacy `SUPERSEDED`. Keep unrelated conflicts visible.
  - [ ] Story becomes `done` only after Phase C2 independent review and landing.

## Exact files and interfaces

### Reuse without replacement

- `.github/workflows/validate-pr-on-claw.yml`
- `scripts/verify_github_bootstrap_approval.py`
- `scripts/verify_same_repo_pr.py`
- `scripts/materialize_exact_source_archive.py`
- `scripts/verify_source_archive.py`
- `scripts/write_source_materialization_receipt.py`
- `schemas/source-materialization-receipt-v1.schema.json`
- `scripts/cleanup-claw-workspace.sh`

### Expected NEW

- `ci/claw/sandbox-policy.json`
- `ci/claw/run-disposable-validation.sh`
- `ci/claw/reconcile-owned-resources.sh`
- `ci/claw/host-helper-manifest.json`
- `ci/claw/install-controller-host-helper.sh`
- `ci/claw/uninstall-controller-host-helper.sh`
- `ci/claw/systemd/mee-controller-reconcile.service`
- `ci/claw/systemd/mee-controller-reconcile.timer`
- `ci/claw/sudoers/mee-controller-ledger`
- `.github/workflows/reconcile-claw-sandboxes.yml`
- `schemas/validation-receipt-v1.schema.json`
- `schemas/validation-cleanup-receipt-v1.schema.json`
- `schemas/bootstrap-nonce-consumption-v1.schema.json`
- `schemas/controller-self-validation-receipt-v1.schema.json`
- `schemas/phase-c1-evidence-proposal-v1.schema.json`
- `schemas/controller-trust-context-v1.schema.json`
- `scripts/consume_bootstrap_nonce.py`
- `scripts/write_bootstrap_nonce_consumption.py`
- `scripts/verify_bootstrap_nonce_consumption.py`
- `scripts/materialize_verified_source_tree.py`
- `scripts/verify_validation_receipt.py`
- `scripts/write_validation_receipt.py`
- `scripts/write_validation_cleanup_receipt.py`
- `scripts/verify_validation_cleanup_receipt.py`
- `scripts/write_controller_self_validation_receipt.py`
- `scripts/verify_controller_self_validation.py`
- `scripts/write_phase_c1_evidence_proposal.py`
- `scripts/verify_phase_c1_evidence_proposal.py`
- `scripts/write_controller_trust_context.py`
- `scripts/verify_controller_trust_context.py`
- `tests/release/test_claw_workflow_policy.py`
- `tests/release/test_disposable_claw_sandbox.py`
- `tests/release/test_validation_receipt.py`
- `tests/release/test_validation_cleanup_receipt.py`
- `tests/release/test_bootstrap_nonce_consumption.py`
- `tests/release/test_controller_self_validation.py`
- `tests/release/test_phase_c1_evidence_proposal.py`
- `tests/release/test_controller_trust_context.py`
- `tests/release/test_claw_host_helper_policy.py`
- `tests/release/test_claw_reconciliation.py`
- bounded malicious fixtures under `tests/release/fixtures/`

### Expected UPDATE

- `.github/workflows/validate-pr-on-claw.yml`
- `.github/workflows/verify-a2-pr-on-claw.yml` only to retire/supersede it after successful self-validation; never use it as Story 1.2 evidence
- `architecture/architecture.yaml`
- `architecture/runtime.yaml`
- `architecture/release.yaml`
- `architecture/requirements.yaml`
- `architecture/schemas/verified-receipt-registry-v1.schema.json` only when the new receipt class has a verified trust context
- `tools/graph_checker/model.py`
- `tools/graph_checker/loader.py`
- `tools/graph_checker/checker.py`
- `tools/graph_checker/__main__.py`
- `scripts/check-architecture-graph.py`
- `tests/graph/test_receipt_identity.py`
- `tests/graph/test_authority_policy.py`
- `tests/graph/test_checker.py`
- `tests/graph/test_repository_manifests_cli.py`
- `tests/graph/test_workflow_policy.py`
- `tests/graph/test_receipt_trust_context.py`
- `tests/graph/test_third_final_review_policy.py`
- `handoff.md`
- `docs/implementation/sprint-status.yaml`

Interfaces are closed JSON/CLI contracts. No generic `command`, `script`, `args`, `image`,
`mount`, `network`, `path` or environment map is accepted from dispatch or PR source.
All digests are lowercase full SHA-256; Git identities are exact lowercase 40-hex SHA-1
where current GitHub API contracts require them.

### Closed `ControllerTrustContext` contract

`controller-trust-context-v1.json` has `additionalProperties: false` and exactly:

- `schema_version="controller-trust-context-v1"`, `repository`;
- `controller_sha`, `controller_tree`, `workflow_path`, `workflow_blob_sha` from exact
  installed Phase A default branch;
- `source_sha`, `source_tree` for immutable Phase B probe;
- `phase_a_approval_comment_id`, `phase_a_approval_body_sha256`,
  `phase_a_nonce_consumption_receipt_sha256`;
- `phase_b_validation_receipt_sha256`, `phase_b_cleanup_receipt_sha256`,
  `phase_b_self_validation_receipt_sha256`, `phase_b_run_id`, `phase_b_run_attempt`,
  `phase_b_run_url`, `phase_b_completed_at` from authenticated GitHub Phase B
  `workflow_run.completed_at`;
- trusted `controller_started_at` and `controller_completed_at` read from GitHub run API,
  plus `runner_monotonic_started_ns`, `runner_monotonic_completed_ns` with positive bounded
  duration and API ordering checks;
- `phase_policy_cutoff_source_kind="GITHUB_PHASE_C1_MERGE_COMMIT_COMMITTER_DATE"`,
  `phase_policy_cutoff_source_url`, `phase_policy_cutoff_source_id`,
  `phase_policy_cutoff_api_payload_sha256`, `phase_c1_merge_sha`, `phase_c1_merge_tree`,
  `phase_c1_proposal_completed_at` from the authenticated GitHub C1 workflow-run API,
  `phase_c1_merge_committer_at`, derived `phase_policy_cutoff`, and
  `phase_c2_controller_verification_completed_at` written only by the trusted
  default-branch controller after all C2 verification checks complete and bound to its
  monotonic completion value;
- `runner_name="claw-engine-runner"`, `sandbox_policy_sha256`,
  `validation_image_digest`, `actionlint_artifact_sha256`, `full_command_set_sha256`;
- `status="SELF_VALIDATION_VERIFIED"`.

The trusted writer accepts a fully verified typed object only and atomically writes mode
`0600`. The verifier fetches the authenticated GitHub commit API projection for the exact
bound repository/default branch/already-existing Phase C1 merge SHA, verifies its merge
tree, hashes the
canonical API payload, and derives `phase_policy_cutoff` exactly from
`commit.committer.date`. It proves UTC equality after RFC3339 normalization, proves
`phase_b_completed_at <= phase_policy_cutoff == phase_c1_merge_committer_at <= phase_c2_controller_verification_completed_at`,
also proves `phase_c1_proposal_completed_at <= phase_c1_merge_committer_at`, and
rejects any manifest phase timestamp later than the derived cutoff. It also re-hashes all
referenced receipt bytes, checks the external verified receipt registry, exact GitHub API
run identity/times, monotonic bounds and cross-field identities. No receipt, manifest or
caller may assert its own trust context or supply trusted policy time.

Exact CLI boundary:

```text
scripts/verify_controller_trust_context.py
  --context PATH --verified-receipt-registry PATH
  --repository OWNER/REPO --controller-sha SHA --controller-tree SHA
  --workflow-path .github/workflows/validate-pr-on-claw.yml --workflow-blob-sha SHA
  --source-sha SHA --source-tree SHA --phase-b-run-id POSITIVE_INT
  --default-branch BRANCH --phase-c1-merge-sha SHA
  --output PATH

scripts/check-architecture-graph.py
  --manifest-root architecture --phase merge
  --controller-trust-context PATH --verified-receipt-registry PATH
  --format text
```

`tools/graph_checker/loader.py` accepts only an externally supplied, already verified
context whose internally derived cutoff and source projection are intact; it accepts no
separate cutoff value. `model.py` represents its closed fields; `checker.py` narrows
realized admission solely to receipt kind `SELF_VALIDATION` with all three exact receipt
hashes; `__main__.py` and CLI reject partial/extra/context-free inputs. Phase A and B cannot
self-assert this context. Phase C1 supplies immutable proposal evidence with
`authority=NONE`; Phase C2 supplies the closed trust context after authenticating the
already-landed C1 merge and completing independent reviews.

### Receipt writer/verifier pairs

Each receipt has a distinct schema, atomic trusted writer, independent verifier and exact
contract test linkage:

| Receipt/schema | Writer | Verifier | Contract test |
|---|---|---|---|
| `bootstrap-nonce-consumption-v1` / `schemas/bootstrap-nonce-consumption-v1.schema.json` | `scripts/write_bootstrap_nonce_consumption.py` | `scripts/verify_bootstrap_nonce_consumption.py` | `tests/release/test_bootstrap_nonce_consumption.py` |
| `validation-receipt-v1` / `schemas/validation-receipt-v1.schema.json` | `scripts/write_validation_receipt.py` | `scripts/verify_validation_receipt.py` | `tests/release/test_validation_receipt.py` |
| `validation-cleanup-receipt-v1` / `schemas/validation-cleanup-receipt-v1.schema.json` | `scripts/write_validation_cleanup_receipt.py` | `scripts/verify_validation_cleanup_receipt.py` | `tests/release/test_validation_cleanup_receipt.py` |
| `controller-self-validation-receipt-v1` / `schemas/controller-self-validation-receipt-v1.schema.json` | `scripts/write_controller_self_validation_receipt.py` | `scripts/verify_controller_self_validation.py` | `tests/release/test_controller_self_validation.py` |

No verifier trusts a status/digest produced only by untrusted probe output. Cleanup receipt
is written after reconciliation/absence proof and self-validation links the verified bytes of
both prior receipts.

### Plan precedence and resolved drift

M6 Task 1 snippets are scaffolding, not permission to weaken the approved design:

- do not checkout PR source; consume Story 1.1 authenticated archive/tree identity and add
  a verifier-owned extraction stage;
- do not upload a PR-controlled directory or raw log; only trusted-controller-generated,
  schema-verified receipt files may be transported after cleanup proof;
- cleanup covers every scoped container/pod/process/network/workspace/test-service and
  secret, not only one container and directory;
- `configuration:claw-disposable-pr-sandbox` remains `DECLARED`; an existing
  `resolved_by` reference is prospective and cannot close a conflict before self-validation.

## TDD and verification gates

Implementation order is strict RED → GREEN → security review → graph review. At minimum:

```bash
python -B -m pytest \
  tests/release/test_claw_workflow_policy.py \
  tests/release/test_disposable_claw_sandbox.py \
  tests/release/test_validation_receipt.py \
  tests/release/test_validation_cleanup_receipt.py \
  tests/release/test_bootstrap_nonce_consumption.py \
  tests/release/test_controller_self_validation.py \
  tests/release/test_phase_c1_evidence_proposal.py \
  tests/release/test_controller_trust_context.py \
  tests/release/test_claw_reconciliation.py \
  tests/release/test_claw_host_helper_policy.py -q
python -B -m pytest tests/graph -q
python -B -m pytest tests/a2 -q
python scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --format text --allow-declared-conflicts
python scripts/check-architecture-graph.py --manifest-root architecture --phase merge --format text
actionlint .github/workflows/*.yml
git diff --check
```

The frozen `full_command_set_sha256` is the canonical SHA-256 of the exact ordered argv
list above and therefore necessarily includes `test_phase_c1_evidence_proposal.py` and
`test_claw_reconciliation.py`; omission,
reordering or substitution invalidates Phase B self-validation.

The authoritative run of these commands is the exact-SHA Claw self-validation run from
the installed default-branch controller. Local GREEN is diagnostic only. Merge graph may
remain RED for unrelated declared conflicts, but `trusted-controller-authority`,
`controller-self-protection`, `full-graph-suite-controller-gate` and
`ci-008-host-docker-boundary` transition only with exact verified evidence.

## Failure semantics and rollback

- Missing/malformed trusted input, mutable image, rootless/preflight failure, resource
  collision, receipt mismatch, nonce replay or cleanup uncertainty stops before admission.
- Validation failure still requires successful cleanup receipt; it never becomes a successful
  validation or self-validation receipt.
- Timeout/cancellation uses final always-cleanup plus a subsequent independent absence check.
- Raw logs and PR files are never receipt authority or uploaded evidence.
- Rollback disables Story 1.2 dispatch and restores exact `c07f251...` archive-only workflow;
  Phase A/Phase B nonce state and review evidence are retained, not reset. PR24 nonce stays
  `RETIRED_UNUSED`.
- No step touches app-stack, production, private APIs, n8n or live trading.

## References

- [Source: docs/planning/epics.md#Story-12-Выполнять-validation-в-disposable-multi-project-Claw-sandbox]
- [Source: docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md#Task-1-Enforce-the-Claw-workflow-and-sandbox-contract]
- [Source: docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md#57-CI-and-Claw-requirements]
- [Source: docs/implementation/1-1-bootstrap-trusted-default-branch-pr-identity-controller.md]
- [Source: .github/workflows/validate-pr-on-claw.yml]
- [Source: architecture/runtime.yaml]
- [Source: architecture/release.yaml]
- [Source: handoff.md#Story-11-trusted-source-controller-handoff-local-implementation]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex story-author agent; planning only.

### Debug Log References

- Canonical source: branch `codex/story-1-2-claw-sandbox`, HEAD `c07f251f844d90ed2ce5c08b49a52169bc231364`.
- Story 1.1 landing: PR #24, OWNER issue comment `5264583724`, body SHA-256 `36b583744f7c46dee34bc713a35c978799fa58923ef7db873c1f32dd375785b3`, exact landing commit `c07f251...`; expired nonce is `RETIRED_UNUSED`.
- No code, workflow execution, commit, push, dispatch, sandbox, receipt or external mutation occurred during Story 1.2 authoring.

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created.
- Story preserves the Story 1.1 archive-only trust boundary and makes single-use nonce consumption explicit.
- Story separates untrusted validation results from trusted validation, cleanup and self-validation receipts.
- Phase A source-only controller slice implemented on `codex/story-1-2-claw-sandbox` with `authority=NONE`: fused archive verification/extraction, immutable sandbox policy, closed receipt/nonce interfaces, label+ledger reconciler and exact-hash host-helper package definitions.
- The root verifier consumes the short-lived workflow token only through bounded stdin; no PAT or GitHub token is persisted in controller state, receipts or ledger records.
- Host bootstrap is a separate reviewed Ubuntu 24.04 transition with dedicated runner identity, preserved legacy home, pinned rootless-Podman dependencies, app-stack invariance checks and an explicit rollback script; it is not executed by Phase A.
- No host helper was installed and no Claw dispatch, Podman execution, realized receipt, push, merge, production, private API, n8n, live-trading or app-stack mutation occurred.

### File List

- `docs/implementation/1-2-vypolnyat-validation-v-disposable-multi-project-claw-sandbox.md`
- `docs/implementation/sprint-status.yaml`
