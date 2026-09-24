# Story 1.1: Bootstrap trusted default-branch PR identity controller

Status: done — TOFU source-only landing completed as PR #24 at `c07f251f844d90ed2ce5c08b49a52169bc231364`

## Story

As an internal operator/researcher,
I want to bind validation to the exact open same-repository PR head and to the controller from the default branch,
so that a payload, arbitrary commit, fork, or PR workflow cannot select the source to be validated or obtain validation authority.

## Goal and outcome boundary

This Story creates only a trusted source-identity and source-materialization controller. It resolves PR identity through the GitHub API, obtains the exact authenticated archive, verifies archive/tree identity, and emits a schema-valid source-materialization observation. It **executes no commands from untrusted source** and creates no validation/cleanup/release/promotion/deployment receipt.

The disposable rootless sandbox, validation image, and execution of untrusted tests belong to Story 1.2. Story 1.3 remains blocked until two separate pieces of evidence exist: an owner-approved `TRANSITIONAL_BOOTSTRAP` receipt for Stories 1.1-1.2 and a successful self-validation receipt from the new controller/sandbox.

## Actors, ownership and approval points

| Role | Responsibility |
|---|---|
| Owner | After the implementation freeze, publishes a GitHub-authenticated OWNER PR issue comment bound to the exact `commit_id`; then manually admits the exact approved controller change as a one-time exception. GitHub does not allow a PR author to approve their own PR, so Pull Request Review authority for the bootstrap PR is technically impossible. |
| DevOps/SRE implementer | Implements the controller, archive verifier, closed schemas, fixtures, workflow, and graph updates. |
| Default-branch controller | The sole authority for PR lookup, exact identity, and archive materialization; controller code comes only from the `github.sha` of the default-branch dispatch. |
| Claw runner | Executes only the trusted controller/bootstrap scope on `[self-hosted, claw]`; receives no deploy/promotion/private/live authority. |
| Independent source-trust reviewer | Verifies identity, archive, credential cleanup, workflow pinning, and absence of untrusted-source execution; the implementation author cannot be the verifier. |
| Graph/governance reviewer | Verifies changed-node closure, ownership, the eight-conflict transition, and absence of fabricated realized receipts. |

### Two distinct approvals

1. `DESIGN_SCOPE_APPROVAL_FOR_LOCAL_IMPLEMENTATION`: **SATISFIED**. In this thread on 2026-08-11/2026-08-12 the owner directly instructed the orchestrator to select the optimal option automatically and use Claw fully for non-production testing. This textual record authorizes local implementation, tests and PR preparation within the stated exclusions. It is not cryptographic evidence, merge authorization or permission for bootstrap landing, release, deploy, private API or live trading.
2. `TRANSITIONAL_BOOTSTRAP_LANDING_APPROVAL`: **SATISFIED AND RETIRED**. PR #24 was source-only landed at `c07f251f844d90ed2ce5c08b49a52169bc231364` using GitHub-authenticated OWNER issue comment `5264583724`, canonical body SHA-256 `36b583744f7c46dee34bc713a35c978799fa58923ef7db873c1f32dd375785b3`, independent source/security YES, graph/governance YES and exact 57-path review. Its nonce expired unused and is `RETIRED_UNUSED`; it cannot authorize or be consumed by Story 1.2. No exact-SHA sandbox self-validation is claimed.

## Stable requirements

| ID | Requirement |
|---|---|
| `ST11-REQ-001` | Consume exact M0 prerequisite commit `550c5f935b236c2bdd29e47a274a35b8a9db0a0a`; implementation must stop if its ancestry or graph contracts differ. |
| `ST11-REQ-002` | The bootstrap authority is an out-of-tree GitHub-authenticated OWNER PR issue comment, target-commit-specific, unmodified, expiring and replay-detectable. Story 1.1 binds a random nonce but grants `authority=NONE`; Story 1.2 owns atomic single-use consumption enforcement. It is not stored inside the PR, does not self-hash and is classified `TRANSITIONAL_BOOTSTRAP`. |
| `ST11-REQ-003` | The trusted controller resolves an open PR from the GitHub API and binds repository, PR number, exact head SHA, same-repository head/base, base `main`, exact reviewed base SHA, controller/default-branch SHA, ancestry, commit tree and current head freshness. Controller SHA equals dispatch `GITHUB_SHA`; for bootstrap the reviewed `base.sha` equals that controller SHA and is an ancestor of head SHA. |
| `ST11-REQ-004` | Arbitrary 40-hex commits, closed PRs, stale heads, fork heads, base-repository mismatch, payload-only repository claims and PR-local workflow authority fail closed with typed diagnostics. |
| `ST11-REQ-005` | Source is an authenticated exact archive. Token exists only in the materialization step environment; response/archive members, traversal, absolute paths, links, unsupported member types, member policy, expanded limits and exact Git tree are verified before extraction/use. |
| `ST11-REQ-006` | The new controller does not execute project scripts, tests, hooks, build files, package metadata or binaries from the archive. Story 1.1 may inspect bytes and Git object identity only. |
| `ST11-REQ-007` | The source-materialization observation uses a versioned closed schema and binds repository, PR, head SHA/tree, base SHA, controller SHA/tree, workflow blob SHA, action/input digests, archive digest, member-policy digest and cleanup intent/outcome. Its schema name may retain `source-materialization-receipt-v1` for planned interface compatibility, but M0 classifies it outside graph `Receipt` nodes and outside the verified receipt registry; it grants no phase authority. |
| `ST11-REQ-008` | Every action is pinned to a full commit SHA; permissions are minimal (`contents: read`, `pull-requests: read` only when API semantics require it); no OIDC write, registry, release, deploy, app-stack, private venue or live-trading authority exists. |
| `ST11-REQ-009` | Story 1.1 cannot claim graph merge GREEN and does not auto-resolve any conflict. After the explicit manual landing, only hosted controller-source identity may transition prospectively; all eight baseline conflicts remain blockers until the owning later evidence exists. |
| `ST11-REQ-010` | Rollback restores the exact previous default-branch workflow/controller identity and retires/revokes the new source-materialization contract without treating transitional evidence as reusable authority. |
| `ST11-REQ-011` | Local and current legacy Claw runs are diagnostic only. The exact GitHub OWNER issue comment plus independent source/security review authorizes only manual bootstrap landing; authoritative controller self-validation begins in Story 1.2. |
| `ST11-REQ-012` | No change touches `/home/operator/app-stack`, n8n, private APIs, live trading, production, promotion, deployment or unrelated Claw projects. |

Traceability: `ST11-REQ-001..012` refine `CI-001`, `CI-003`, `CI-005`, `CI-008`, `SEC-004`, `SEC-005`, `GRAPH-004`, `GRAPH-006`, `GRAPH-007`, `GRAPH-009`, `GRAPH-010`, NFR15-NFR21, NFR27-NFR33, NFR38-NFR41 and AR5/AR8-AR11.

## Fixed one-time transitional bootstrap contract

The bootstrap authority is an **out-of-band GitHub-authenticated OWNER PR issue comment**, not a file inside the PR, not an artifact emitted by the current workflow and not a self-digesting record. GitHub forbids a PR author from approving their own PR, so the bootstrap PR cannot use Pull Request Review authority. GitHub supplies authenticated owner identity, immutable comment ID, OWNER association and comment timestamps. The pre-post canonical closed JSON body binds the approval decision, repository, PR number, exact frozen `commit_id`, independently computed Git tree, default-branch controller SHA/tree, workflow path/blob, fixed allowed file/path/change-set, fixed closed checks, expiry and a cryptographically random replay-correlation nonce; it intentionally contains no owner-asserted `created_at`. The API projection must prove exact issue/comment URLs, OWNER association, aware UTC `created_at == updated_at`, and zero permitted future clock skew (`created_at <= controller now`). Validity is bounded by `API created_at < body expires_at <= API created_at + 1 hour` and current time must precede expiry. Atomic single-use consumption is deliberately deferred to Story 1.2.

The immutable controller-of-record at story start is:

- repository: `Dimkox/multi-exchange-engine`;
- default branch: `main`;
- default-branch controller commit: `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99`;
- trusted legacy workflow: `.github/workflows/verify-a2-pr-on-claw.yml`;
- trusted legacy workflow blob: `9ec76d2a19cbb42bcfc85316f5e01a766a74a32e`;
- event type: `a2-pr-verification`;
- runner labels: `[self-hosted, claw]`.

Historical sequence completed: implementation froze PR #24 head/tree/controller/workflow and exact 57-path scope; OWNER posted comment `5264583724`; independent source/security and graph/governance reviews returned YES; the owner source-only landed exact commit `c07f251...` with `authority=NONE`. That approval was consumed only as manual landing authority. Its nonce was never consumed by controller code, expired, and is terminal `RETIRED_UNUSED`. Story 1.2 must obtain a new Phase A approval/nonce and cannot reuse this historical design path.

The legacy workflow's nested `requirements-a2.txt`, Python scripts and tests come from PR code and can execute arbitrary behavior on persistent Claw. It is therefore excluded from Story 1.1 bootstrap evidence and MUST NOT execute the new Story 1.1 tests or controller as a transitional bridge. Its historical output remains bounded diagnostics only.

The only bootstrap is an out-of-band manual owner landing after the exact GitHub OWNER issue comment plus independent source/security and graph review. New controller code produced by Story 1.1 is limited to identity/archive verification and MUST NOT invoke any project command. No legacy dispatch or workflow output can satisfy Story 1.2 self-validation, Story 1.3 admission, merge authority for later source, release, promotion or deployment.

## Acceptance Criteria

### AC1 — exact transitional authority

**Given** `ST11-REQ-001` and an owner-approved one-time record binding the exact identities above plus the frozen bootstrap PR head
**When** the owner manually lands only the exact independently reviewed commit without invoking a legacy dispatch
**Then** the GitHub OWNER issue comment—not repository workflow output—is the `TRANSITIONAL_BOOTSTRAP` authority
**And** it is target-specific, expiring, replay-detectable and non-authoritative for validation, Story 1.3, release, promotion or deploy; Story 1.2 must enforce single-use consumption.

### AC2 — exact PR identity

**Given** a dispatch containing only a PR number and expected head SHA
**When** the default-branch controller resolves the PR through the repository API
**Then** it independently proves exact repository, open state, base `main`, same-repository head/base, exact current head SHA, required ancestry and exact commit tree
**And** rejects malformed/extra payload fields, arbitrary commits, forks, stale heads, closed PRs and mismatched identities with stable typed errors.

Exact ancestry contract: dispatch controller SHA equals default-branch `GITHUB_SHA`; approved/API `base.sha` equals that controller SHA for the frozen bootstrap PR; API `head.sha` equals approved `commit_id`; base is an ancestor of head; reconstructed head tree equals the independently approved tree. Any default-branch movement after approval invalidates the exception and requires a new owner approval comment.

### AC3 — authenticated archive without credential persistence

**Given** a validated PR identity
**When** source is materialized
**Then** a step-scoped token obtains the exact archive; after stripping the one expected archive-root prefix, normalized entries are compared against the exact `git ls-tree -r` projection for modes, types, paths and blob SHAs by locally hashing canonical Git blob objects and reconstructing the tree bottom-up
**And** traversal, absolute paths, duplicate normalized paths, Unicode/case collisions, special members, size/member-policy violations, blob/tree mismatch, submodules and symlinks are rejected unless a separately frozen policy explicitly allows the latter two
**And** redirects are disabled by default; any required redirect must remain HTTPS within an exact frozen GitHub archive-host allowlist and must not forward authorization across host boundaries
**And** response, archive, extracted workspace and token-bearing environment are removed or proven absent while no credential is written to Git config, archive, receipt or artifact.

### AC4 — source-materialization observation, not realized receipt authority

**Given** successful identity and archive verification
**When** the controller writes its observation atomically
**Then** it validates against the closed versioned schema and binds all identities/digests in `ST11-REQ-007`
**And** it is excluded from graph `Receipt` nodes and the verified-receipt registry, contains no phase authority and cannot pass the M0 realized-receipt trust gate.

### AC5 — Claw and security policy

**Given** all Story 1.1 workflow changes
**When** malicious identity/archive fixtures, workflow-policy tests, pinned `actionlint`, graph diagnostics and independent source-trust review run on the exact SHA on Claw
**Then** the new controller itself is archive-only, pinned and least-privilege, and the legacy nested PR-code execution is excluded from bootstrap evidence
**And** the historical graph merge blockers did not prevent the explicitly reviewed source-only TOFU landing; no validation/receipt/release authority was granted. Story 1.2 remains the separate owner of sandbox self-validation.

The one-time transition is `TOFU_SOURCE_INSTALL`: manual exact fast-forward/landing installs source only and preserves `authority=NONE`. Its inputs are the exact OWNER comment on the frozen bootstrap PR, frozen local verification outputs/hashes, independent source/security YES, graph/governance YES and exact 57-path review. The comment's closed checks list names the two independent reviews. Immediately afterward, a Story 1.2 exact follow-up PR uses the now-default-branch controller on Claw for the first exact-SHA Claw/actionlint/sandbox self-validation. Until that passes, there is no validation receipt, trusted policy time, Story 1.3 admission, release, promotion or deployment authority.

### AC6 — graph-complete handoff and rollback

**Given** the changed files and review evidence
**When** graph closure is evaluated
**Then** each changed node has owner, requirement, contract, test/gate, evidence plan, handoff verifier and rollback/replacement edge; there are no orphans, cycles, dual owners or fabricated receipts
**And** no conflict is auto-resolved; every baseline declared conflict remains visible and blocks normal merge/release until its owning later evidence exists.

## Tasks / Subtasks

- [x] Task 1 — Freeze contract and RED tests (AC1-AC5)
  - [x] Re-verify HEAD descends from `550c5f935b236c2bdd29e47a274a35b8a9db0a0a`; record current default-branch controller/workflow/blob identities above.
  - [x] Add a parser/verifier contract for the out-of-band GitHub OWNER issue-comment projection and a closed schema for source-materialization observation; do not add a bootstrap record to the PR.
  - [x] Add RED malicious fixtures for malformed/extra payload, closed/stale/fork PR, repo/base/head/ancestry/tree mismatch, archive traversal/absolute/link/special/duplicate/size/member-policy cases, credential persistence and project-command execution.
  - [x] Add workflow RED tests for default-branch authority, full action pins, minimal permissions, Claw-only jobs and no deploy/private/live capabilities.
- [x] Task 2 — Implement exact PR resolver (AC2)
  - [x] Create `scripts/verify_same_repo_pr.py` as library + CLI with closed inputs and stable typed diagnostics.
  - [x] Verify API response shape, current open head, same repository/base, base `main`, exact head SHA, ancestry and commit-tree identity; do not accept branch workflow logic.
- [x] Task 3 — Implement authenticated exact archive materialization (AC3)
  - [x] Create a trusted materializer and archive-member/tree verifier under controller-owned paths; use step-scoped token and atomic private temp paths.
  - [x] Verify archive before use by local Git blob/tree reconstruction against the exact API/`git ls-tree -r` projection; scrub API response, archive, extracted workspace and token context on success/failure.
  - [x] Prove no Git credential helper, persisted checkout credential, hook, package/build/test command or archive executable runs.
- [x] Task 4 — Implement non-authoritative observation and out-of-band bootstrap review (AC1, AC4)
  - [x] Add versioned schemas and atomic canonical writers/verifiers; bind exact controller/workflow/action/input/archive/member-policy identities and cleanup.
  - [x] Add the owner-approval checkpoint: frozen head/tree/57-path set was approved by OWNER issue comment `5264583724`; canonical body SHA-256 `36b583744f7c46dee34bc713a35c978799fa58923ef7db873c1f32dd375785b3`.
  - [x] Ensure replay against any other PR/head/controller/workflow/expiry identity fails and emit the nonce for Story 1.2 consumption enforcement.
- [x] Task 5 — Install default-branch controller workflow without execution authority (AC2-AC5)
  - [x] Create `.github/workflows/validate-pr-on-claw.yml` with `repository_dispatch`, closed payload parsing, trusted default-branch checkout, API resolution and archive-only materialization.
  - [x] Modify `.github/workflows/verify-a2-pr-on-claw.yml` only as required for the fixed transitional contract; preserve existing A2/PostgreSQL gates and exact cleanup semantics.
  - [x] Do not add sandbox execution; leave Story 1.2 interfaces explicit and fail closed.
- [x] Task 6 — Graph, handoff, review and rollback (AC5-AC6) — source-only TOFU landed
  - [x] Update `architecture/runtime.yaml`, `architecture/release.yaml` and any required authority edges with one owner per changed node and no realized receipt.
  - [x] Update `handoff.md` with implementer, independent source-trust reviewer, graph reviewer, exact input/output identities, completed landing evidence, rollback and unresolved conflicts.
  - [x] Run focused local diagnostics, full graph suite, changed-node/orphan check and `git diff --check`; freeze evidence, obtain exact OWNER comment and land PR #24 source-only. Pinned actionlint and exact-SHA sandbox self-validation remain Story 1.2 work.

## Files and interfaces

### Expected NEW files

- `tests/release/test_claw_source_controller_policy.py`
- `tests/release/test_same_repo_pr.py`
- `tests/release/test_exact_source_archive.py`
- `tests/release/test_source_materialization_receipt.py`
- `tests/release/fixtures/**` for malicious PR/API/archive cases
- `schemas/source-materialization-receipt-v1.schema.json`
- `scripts/verify_github_bootstrap_approval.py`
- `scripts/verify_same_repo_pr.py`
- `scripts/materialize_exact_source_archive.py` or equivalently bounded controller-owned entrypoint
- `scripts/verify_source_archive.py`
- `scripts/write_source_materialization_receipt.py`
- `.github/workflows/validate-pr-on-claw.yml`

### Expected UPDATE files

- `.github/workflows/verify-a2-pr-on-claw.yml`: preserve current default-branch identity check, PostgreSQL 16/17 matrix, fixed A2/shadow scope, evidence and cleanup; add only closed transitional binding needed for AC1.
- `architecture/runtime.yaml`: declare source-controller/materialization configuration without sandbox execution capability.
- `architecture/release.yaml`: declare prospective bootstrap/source-materialization contracts, tests, gate, evidence plan and rollback; no receipt node.
- `architecture/architecture.yaml` only to declare prospective controller/source nodes and edges; do not mutate the M0 conflict allowlist or claim conflict resolution.
- `handoff.md`: exact ownership, independent verification and rollback evidence.

Do not create `ci/claw/sandbox-policy.json`, `ci/claw/run-disposable-validation.sh`, validation/cleanup receipt writers or validation image contract in this story; those belong to Story 1.2 even though the older M6 Task 1 plan grouped them.

## Current-state preservation

- Preserve the current `repository_dispatch` owner-only gate, exact PR API lookup, same-repository/open/head checks and pinned `actions/checkout` behavior until the transitional replacement proves equivalence.
- Preserve dynamic PostgreSQL 16.11/17.7 service ports and run/attempt/job/shard isolation in the legacy bootstrap workflow.
- Preserve graph merge check, workflow policy check, A2/replay/fault/boundary/conditional shadow gates, non-secret evidence upload and scoped workspace cleanup.
- Do not weaken M0: realized receipts remain rejected because the trust anchor is prospective; `--allow-declared-conflicts` remains precommit-only and closed to the exact M0 baseline.

## Eight declared conflicts at prerequisite HEAD

The M0 diagnostic baseline at `550c5f9` is exactly:

1. `conflict:a2-private-production-image`
2. `conflict:ci-008-host-docker-boundary`
3. `conflict:controller-self-protection`
4. `conflict:duplicate-python-namespace`
5. `conflict:full-graph-suite-controller-gate`
6. `conflict:go-stage-a-build`
7. `conflict:retained-promotion-entrypoint`
8. `conflict:trusted-controller-authority`

Story 1.1 does not auto-resolve any conflict. `conflict:controller-self-protection` and `conflict:full-graph-suite-controller-gate` remain wholly active until Story 1.2 self-validation. `conflict:trusted-controller-authority` remains active through implementation and manual landing; only the hosted controller-source identity may transition prospectively after landing, without admitting realized receipts. All eight remain visible and cannot be waived at merge by repository code.

## TDD and verification gates

RED must demonstrate each intended typed rejection before implementation. GREEN is necessary but not a receipt. Frozen local verification supports only `TOFU_SOURCE_INSTALL`; the first authoritative exact-SHA Claw commands run from the installed default-branch controller in Story 1.2. At minimum the story-specific evidence must include:

```bash
python -B -m pytest \
  tests/release/test_claw_source_controller_policy.py \
  tests/release/test_same_repo_pr.py \
  tests/release/test_exact_source_archive.py \
  tests/release/test_source_materialization_receipt.py -q
python -B -m pytest tests/graph -q
python scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --format text --allow-declared-conflicts
python scripts/check-architecture-graph.py --manifest-root architecture --phase merge --format text
git diff --check
```

The current legacy workflow executes PR-controlled scripts, tests and dependencies. It must not run Story 1.1 controller tests or provide bootstrap evidence. Do not smuggle a generic command/script path through payload and do not label the run sandboxed. Manual landing is allowed only by the separate exact GitHub OWNER issue comment plus independent source/security and graph reviews; otherwise this is a typed bootstrap blocker.

The M0 graph checker stays realized-fail-closed: `tools/graph_checker/loader.py` continues to load untrusted policy time and `tools/graph_checker/checker.py` continues to reject every realized receipt. Story 1.1 adds only source-materialization observation schema/verification outside the graph Receipt registry. `ControllerTrustContext`, trusted phase-time admission and nonce-consumption evidence belong to Story 1.2 self-validation.

The merge graph command is expected to remain fail-closed while unrelated declared conflicts exist; the handoff must distinguish expected blockers from test failures. Story 1.1 local/landing success means frozen local outputs/hashes, the exact OWNER comment, two named independent YES reviews and exact source-only landing. Story 1.2 authoritative success separately requires the first exact-SHA Claw/actionlint/sandbox self-validation from the installed default-branch controller.

## Security and failure semantics

- API and archive parsers use closed schemas, bounded input sizes and deterministic canonicalization.
- All identity comparisons are exact and case/encoding behavior is explicit; no prefix SHA, branch-name fallback, redirect-to-other-host or mutable action tag.
- Archive extraction cannot precede complete member validation. Symlinks, hardlinks, devices, FIFOs, traversal and ambiguous normalized names are rejected.
- Tokens, auth headers and API responses are never logged or embedded in receipts/artifacts. Cleanup runs on success, failure and cancellation.
- A cleanup failure, missing field, stale API result, archive/tree mismatch, missing review or graph gap leaves the controller/source gate blocked.
- The controller never interprets success as authorization for release, promotion, deployment or live trading.

## Rollback

Rollback is data-bound, not “re-run latest main”:

1. restore default-branch workflow/controller to commit `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99` and workflow blob `9ec76d2a19cbb42bcfc85316f5e01a766a74a32e`;
2. disable the new dispatch identity and mark its prospective source-materialization contract `RETIRED`/superseded with a typed rollback edge;
3. delete the GitHub approval comment or mark its nonce unusable before consumption; preserve comment ID/body digest without treating it as reusable authority;
4. run the M0 graph/workflow policy on Claw and record independent rollback review;
5. do not touch app-stack or any production/live resource.

## Exclusions

- No rootless Podman sandbox or execution of untrusted source (Story 1.2).
- No canonical distributions/public capture/evidence DB (Stories 1.3+).
- No validation, cleanup, build, scan, SBOM, promotion, release, deploy or production receipt.
- No live trading, private/account API, signer, wallet, order/cancel/transfer/withdrawal capability.
- No n8n, retail UI, app-stack change, `/home/operator/app-stack` access or unrelated Claw project mutation.

## Handoff contract

Implementation output is one reviewable exact-SHA slice with:

- GitHub issue-comment ID `5264583724`, authenticated OWNER identity, exact `commit_id` `c07f251...`, canonical body SHA-256 `36b583...`; expired nonce status `RETIRED_UNUSED`;
- exact repository/PR/head/tree/controller/workflow/action/member-policy identities;
- source-materialization observation schema and negative-fixture results;
- exact source-only landing identities and local observation hashes, explicitly labelled non-authoritative; no archive execution run is claimed;
- implementer, independent source-trust reviewer and graph reviewer results;
- conflict transitions plus all still-active blockers;
- exact rollback identity above.

Story 1.1 is terminal `done`: PR #24 landed at `c07f251...` after exact OWNER comment and two independent reviews. The historical bootstrap design is superseded, its nonce is `RETIRED_UNUSED`, and it grants no continuing authority. Story 1.2 owns new Phase A approval, trusted self-validation and its own nonce-consumption receipt.

## References

- [Source: docs/planning/epics.md#Story-11-Bootstrap-trusted-default-branch-PR-identity-controller]
- [Source: docs/planning/implementation-readiness-report-2026-08-11.md#Final-Readiness-Decision]
- [Source: docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md#8-Graph-model]
- [Source: docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md#9-Conflict-and-automatic-resolution-model]
- [Source: docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md#Task-1-Enforce-the-Claw-workflow-and-sandbox-contract]
- [Source: docs/superpowers/plans/2026-08-11-unified-graph-migration-program.md#Program-Dependency-DAG]
- [Source: .github/workflows/verify-a2-pr-on-claw.yml]
- [Source: architecture/architecture.yaml]
- [Source: architecture/runtime.yaml]
- [Source: architecture/release.yaml]
- [Source: handoff.md]

## Dev Agent Record

### Agent Model Used

GPT-5 Codex development agent using strict local TDD.

### Debug Log References

- Story author diagnostic: `python -B -m pytest tests/graph -q` — 186 passed at prerequisite HEAD.
- Story author diagnostic: precommit graph with closed M0 waiver — exactly eight declared conflicts listed above.
- RED: initial controller modules/workflow were absent; independent review then exposed seven operational review/ordering failures.
- GREEN: the corrected focused release suite covers realistic GitHub OWNER issue-comment bodies, exact identities, archive attacks, cleanup ordering and non-authoritative observation writing; full gate counts are recorded in the implementation handoff.
- Frozen local verification evidence: release plus workflow policy 63 passed; `tests/graph` 188 passed; deployment contract 11 passed; precommit retains exactly eight conflicts and merge remains fail-closed. Local `actionlint` is unavailable and is not claimed; actionlint belongs to the first Story 1.2 exact-SHA Claw self-validation after landing.
- Bootstrap scope correction: the frozen `allowed_paths` projection contains all 57 paths in `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99...HEAD`, including prerequisite M0, planning, graph, workflow and Story 1.1 changes. A release-policy test derives the same Git diff and fails on omission, addition or drift; the controller rejects scopes above 64 paths.

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created.
- Story intentionally splits archive-only source authority (1.1) from disposable execution/sandbox authority (1.2).
- No implementation, commit, dispatch, receipt, deploy or production mutation was performed while authoring this story.
- Implemented an archive-only default-branch controller. It validates exact PR identity, reconstructs the Git tree from archive bytes, rejects ambiguous/special members and writes only an `authority=NONE` observation.
- GitHub OWNER comment `5264583724` and PR #24 landing at `c07f251...` are completed source-only TOFU evidence. The approval nonce expired unused and is `RETIRED_UNUSED`; Story 1.1 is done and grants no validation/sandbox/Story 1.3 authority.

### File List

- `docs/implementation/1-1-bootstrap-trusted-default-branch-pr-identity-controller.md`
- `docs/implementation/sprint-status.yaml`
- `.github/workflows/validate-pr-on-claw.yml`
- `.github/workflows/verify-a2-pr-on-claw.yml`
- `architecture/architecture.yaml`
- `architecture/release.yaml`
- `architecture/runtime.yaml`
- `schemas/source-materialization-receipt-v1.schema.json`
- `scripts/materialize_exact_source_archive.py`
- `scripts/verify_github_bootstrap_approval.py`
- `scripts/verify_same_repo_pr.py`
- `scripts/verify_source_archive.py`
- `scripts/write_source_materialization_receipt.py`
- `tests/release/test_claw_source_controller_policy.py`
- `tests/release/test_exact_source_archive.py`
- `tests/release/test_same_repo_pr.py`
- `tests/release/test_source_materialization_receipt.py`
- `tools/graph_checker/loader.py`
- `tests/graph/test_third_final_review_policy.py`
- `handoff.md`
