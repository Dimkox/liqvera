# Story 1.2A — Transactional Claw engine-runner host transition

Status: review. Authority: NONE. The installed approval-path source correction
is ready for exact-SHA security and graph source review. D0 still contains the
previous landed bytes; D1 host transition is not applied.

Portable OCI evidence v2 and its checked-in approval projection are reviewed and
remain non-authoritative: `authority=NONE`, `not_host_receipt=true`, and version
execution is still `PENDING_UNTIL_ROOTLESS_HOST_SMOKE`. D0 installed the exact
reviewed controller artifacts. The first owner-authorized D1 `begin` then failed
closed at `STAGED_INPUT_VERIFY` because the verifier compared the logical policy
path with the physical installed path. It failed before nonce consumption,
begin intent, host WAL or mutation; the engine and app runners remained active,
and `finalize` was not invoked. That approval is not reusable.

## Objective and actors

Owner approves one exact source commit, package closure, OCI archive digest and host inventory receipt. The privileged installer executes only that frozen projection. The engine runner is migrated from user `pall` to dedicated UID/GID 980 without moving or re-registering its credential-bearing install tree. The app-stack runner is an immutable canary and is never stopped or modified.

## Frozen host evidence

- Ubuntu 24.04 amd64; engine unit `actions.runner.Dimkox-multi-exchange-engine.claw-engine-runner.service`, working directory and ExecStart rooted at `/home/operator/actions-runner-engine`.
- App unit `actions.runner.Dimkox-openclaw-airgap-farm.claw-runner.service`, working directory `/home/operator/actions-runner`.
- UID/GID 980 free. Authenticated read-only observation `9b268d11a3e1a6aa08d5f7d9d035d7e1994f0e033022771c5ae00df2b0812282` proved `165536:65536` is already owned by `ii_tonya_release`; the next candidate dedicated range is `231072:65536` for both subuid and subgid and remains blocked until a new observation proves no overlap.
- Exact ten-package versions and SHA-256 values are in `ci/claw/host-package-closure.json`.

## Requirements

- HOST-001: Verify the closed host inventory, realpaths, ownership, modes, unit fragments, ExecStart, working directories, UID/GID and subordinate-range non-overlap before mutation.
- HOST-002: Accept only a root-owned reviewed package directory and OCI archive whose bytes exactly match closed manifests. Copy regular non-symlink inputs into root-only transaction state, fsync file and directory, then install offline without repository downloads. The frozen Claw inventory requires every closure package absent before mutation; a present closure member fails closed, preventing any unreviewed upgrade/downgrade restoration path.
- HOST-003: Preserve `.runner`, `.credentials`, `.credentials_rsaparams` and every discovered credential/config member byte-for-byte and metadata/ACL-equivalent. Never copy, move, print, hash into durable receipts, deregister or expose them.
- HOST-004: Use separate HOME `/var/lib/claw-engine-runner`, fixed UID/GID 980, subordinate IDs `231072:65536` only after authenticated non-overlap evidence, user-runtime-dir 980, cgroup v2 and rootless Podman storage/runroot. Engine WorkingDirectory/ExecStart remain unchanged.
- HOST-005: Model every mutation through one `OperationBackend`. Each operation defines `prepare`, `apply`, `verify`, and idempotent `rollback`; the same ordered operation list drives real and fake backends.
- HOST-006: Journal the exact append-only phase vocabulary `PREPARED -> APPLYING(name) -> APPLIED(name) -> VERIFYING -> VERIFIED -> COMMITTED`, or `ROLLING_BACK -> ROLLED_BACK|ROLLBACK_BLOCKED`, atomically. The operation snapshot is durable before `current` enters `APPLYING(name)`; a prepare failure never invokes that operation's inverse. `resume` recovers an existing OPEN journal into rollback, while explicit `rollback` accepts OPEN or COMMITTED state and never overwrites a journal.
- HOST-007: Operation acceptance is bound by the stable names `freeze_inputs`, `snapshot_host`, `install_packages`, `create_identity`, `configure_subids`, `configure_runtime`, `stop_engine`, `transfer_ownership`, `install_dropin`, `load_oci`, `rootless_smoke`, `host_capability_precondition`, `start_engine`, `runner_api_canary`, and `app_canary`. Ordering in a list is not an operation identity. All offline OCI, rootless and host-capability checks precede engine start; helper installation is a separate post-receipt action.
- HOST-008: Inverses restore package set after an offline reverse-dependency simulation, identity, subordinate files, linger/runtime/storage, exact unit/drop-in, ACL/metadata ownership and original engine state. Packages present in the baseline are never removed. If a transaction-created package gains a new external reverse dependency, rollback becomes nonterminal `ROLLBACK_BLOCKED`; all other inverses are still attempted, and the dependency is never removed automatically. They never touch the app unit or app tree.
- HOST-009: The host transaction verifies only the frozen helper-install inputs and writes its host receipt after every rootless, engine, GitHub and app canary passes. Helper installation is a distinct post-host-receipt transaction: it consumes the verified host receipt and emits a separate root-owned helper-install receipt. Neither receipt contains a credential digest, token, secret or content-derived credential identifier.
- HOST-010: The app canary binds unit fragment, User, ExecStart, WorkingDirectory, active state and MainPID continuity. Any drift triggers rollback.
- HOST-011: The GitHub token is ephemeral bounded stdin only; runner API must prove the same runner identity, online state and exact `self-hosted`, `claw`, `claw-engine-runner` labels.
- HOST-012: The nonzero OCI archive approval remains `authority=NONE` and cannot authorize host apply by itself. D1 requires exact reviewed source/controller identity, authenticated inventory, owner tuple, root-side rehash, rootless offline load and version smoke, plus independent security and graph review.
- HOST-013: Before ownership mutation, the root transaction creates a complete ordinal inventory and domain-separated keyed-HMAC commitment set for every regular file in the closed runner tree. The binding includes transaction ID, controller SHA and policy SHA. A random per-transaction key and commitment map are separate root-owned `0600` single-link files under a root-owned `0700` directory; inputs are streamed through `O_NOFOLLOW` descriptors with stable pre/post stat and constant-time verification. Neither credential bytes, plain digests, key, HMAC nor commitment paths enter the journal, receipt, logs or workflow artifacts. State is retained through OPEN, VERIFIED, COMMITTED and every ROLLBACK_BLOCKED state. It is logically unlinked with directory fsync only after byte-and-metadata-equal ROLLED_BACK or a separate explicit owner rollback-window closure. Root compromise is outside this threat model.

Installed path correction is additionally governed by the controller-design
requirements `OCIAPATH-001..005`: physical root-owned `--approval` supplies
bytes, while logical `--approval-policy-path` is exactly
`ci/claw/oci-evidence-approval.json`. Omissions, absolute paths, backslashes,
dot-segments and mismatches fail before staging, nonce consumption or WAL
creation.

## Acceptance and verification

Binding-fix checklist: (1) graph inventory closure; (2) HOST-001..013 graph requirements and proof lanes plus `OCIAPATH-001..005`; (3) host receipt before helper install; (4) HMAC retention through COMMITTED/rollback window; (5) absent identity snapshot and created-only inverse; (6) safe resume and OPEN-journal overwrite refusal; (7) credential/ACL equality before rollback closure; (8) offline OCI/rootless/capability validation before engine start plus pre-mutation app baseline; (9) exact offline APT and baseline/manual-auto restoration; (10) exact subid metadata and runtime ledger/final equality; (11) OCI baseline and transaction-created-only inverse; (12) host-state-bound receipt; (13) semantic receipt verifier and post-receipt helper gate; (14) installed physical/logical approval path separation blocks D1 until corrected source and D0 update are separately approved.

- FakeBackend executes every operation and records exact inverse order. A parameterized failure is injected before and after every operation; terminal state is ROLLED_BACK and initial snapshot is equal.
- RealBackend command tests use PATH stubs and `MEE_ROOT`; no test uses sudo, systemd, apt, Podman or network.
- Negative cases cover symlinks, path escape, changed credentials, package/hash/metadata mismatch, UID/subid collision, app drift, engine mismatch, OCI mismatch, cgroup/runtime/storage failure, runner reconnect mismatch and interrupted rollback resumption.
- Full release, graph and A2 suites pass; strict merge remains fail-closed until trusted policy time and declared conflicts are resolved.

## Implementation plan

1. Replace the current state-only prototype with `Operation`, `Snapshot`, `Journal`, `FakeBackend`, and `RealBackend` interfaces.
2. Implement pure closed-manifest and host-inventory validation.
3. Implement operations and idempotent inverses one at a time using RED/GREEN tests.
4. Implement durable journal recovery and crash-resume tests.
5. Implement verification receipt schema/writer/verifier and helper-install precondition.
6. Bind source, schemas, tests, scripts and rollback artifacts into the architecture graph and exact approval path set.
7. Run independent security and graph reviews; commit only after both return YES.

## Approval and rollback boundary

The owner approval point is the tuple `(source SHA/tree, policy hash, package closure hash, OCI archive SHA-256, host inventory receipt hash)`. Any difference requires a new approval. Rollback is automatic before COMMITTED and manually repeatable afterward from root-only transaction state. Production/app-stack, n8n, private APIs and trading are outside scope.

The OCI v2 builder performs checkout self-consistency checks only and is not an approval authority. The independent verifier's explicit expected origin, commit, tree and source-image arguments form the external authority boundary; builder success remains local evidence only.

OCI descriptor media types remain exact. Docker Hub HTTP responses are separately closed to the observed protocol projection: the manifest must use the OCI manifest media type; config and layer blob responses may use only `application/octet-stream` or their exact descriptor media type. Arbitrary or HTML response types fail closed.

The checked-in `oci-evidence-approval.json` approves only the external v2 receipt/archive tuple; v1 is explicitly excluded. This changes the source gate to `PRE_HOST_OCI_EVIDENCE_APPROVED` without granting authority. Real apply must independently verify the externally supplied receipt, sidecar, archive and layout before staging. The installed physical/logical path correction is specified in `docs/superpowers/specs/2026-08-13-claw-host-deployment-controller-design.md` and planned in `docs/superpowers/plans/2026-08-13-claw-installed-approval-path.md`. Actionlint version execution, rootless host smoke, authenticated host inventory and fresh explicit owner authorization remain mandatory later gates.

## Installed approval-path source review checkpoint — 2026-08-13

The source correction and final-review fix wave now pass the direct Claw 3.14.6
gates. The D0 install manifest binds all 19 installed artifacts exactly; the
final wave refreshed the changed installed verifier SHA-256. The
source-controller allowlist equals the full 22-path diff from landed base
`c70bd2090e89bbcc749ca4b678ec3e22b338ef05`, contains no duplicates, and every
path is inventoried exactly once. The complete release split reported `320`
unprivileged plus `14` isolated root credential-state tests; full graph reported
`196 passed`. `OCIAPATH-001..005` now have exact singleton DECLARED proof lanes,
with zero realized receipts and zero OCIAPATH conflict nodes.
Precommit retained exactly eight `DECLARED_CONFLICT` diagnostics, while merge
remained fail-closed on those eight plus
`PHASE_POLICY_TIME_TRUST_MISSING`. Python compilation, YAML parsing, Bash syntax,
manifest binding and diff checks passed. GitHub Actions was not used.

This checkpoint is source evidence only. Exact-SHA security and graph reviews
remain required before source landing. It does not authorize or execute a D0
update, fresh inventory collection, new D1 `begin`, D1 `finalize`, Story 1.3,
host mutation, app-stack access or production activity. The expired D1 approval
must not be reused; every later step remains a separate owner checkpoint.
