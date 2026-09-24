# Claw Host Deployment Controller Design

## Goal

Provide the missing, approval-gated path from verified Story 1.2A source and
external input evidence to a reversible Claw engine-runner host transition.
The controller must preserve the existing WAL transaction, survive stopping
the runner that launched it, keep every GitHub credential memory-only, and
produce independently verifiable host and helper receipts before Story 1.2
self-validation can begin.

This design does not authorize host mutation. Implementation, one-time root
controller provisioning, transition execution, and later production admission
remain separate owner checkpoints.

## Considered approaches

1. An unstructured manual root invocation of
   `bootstrap-claw-engine-runner-host.sh` preserves transaction semantics but
   lacks installed-source identity, authenticated approval and recovery UX.
2. Direct `sudo bash` from a self-hosted runner is rejected. It grants a shell
   boundary, trusts runner-writable source, and the process is inside the
   service cgroup that the transition must stop.
3. The selected approach is a narrow, root-owned systemd deployment controller
   with one explicit out-of-band root bootstrap and an owner-controlled local
   finalize after reconnect. It owns durable input acquisition and the
   transaction while the engine runner is offline; the local root client asks
   GitHub only for the current runner/API projection, or a bounded timer rolls
   back. GitHub Actions is not used. The initial root checkpoint is unavoidable
   because both current runners share UID `pall`.

## Actors and trust roots

- **Repository owner:** approves D0 controller provisioning and later approves
  one exact D1 transition tuple. Approval is an immutable GitHub issue comment
  with authenticated owner login/id/association, `created_at == updated_at`, a
  one-hour expiry window, a unique nonce, and canonical closed JSON.
- **Owner-controlled Claw root console:** invokes only the installed root-owned
  client for begin/finalize/status/rollback. It supplies a bounded memory-only
  token envelope and never executes repository checkout bytes.
- **Root deployment controller:** installed from reviewed committed bytes under
  root-owned paths. It independently verifies installed hashes, GitHub
  repository/approval/release/runner identities, input bytes, journal state and
  receipt state. Runner-side verification is diagnostic only.
- **GitHub API:** authenticates repository, owner comment, release and asset
  identities, and the reconnected runner. Tokens arrive only
  through a pipe, are never persisted or included in a digest, and are dropped
  after each request.
- **Existing host transaction:** remains the only component allowed to mutate
  packages, identity/subids, runtime, systemd, runner-tree ownership, or OCI
  storage. The app-stack service and path are immutable canaries.

Root compromise is outside the threat model. A compromised `pall` process,
branch checkout, untrusted request payload, release asset, or same-UID background
process must not be able to forge approval, replace root-staged bytes, widen
the helper command, or force COMMITTED.

## Stable requirements

- **HOSTDEP-001 — Exact installed source identity.** The root begin phase
  independently fetches and binds repository default branch, controller
  SHA/tree and owner approval. Finalize, status and rollback execute only through
  the exact installed root client and bind transaction ID, installed controller
  identity, current runner ID/name/status/labels and the owner-approved tuple.
- **HOSTDEP-002 — Closed owner approvals.** D0 and D1 use different immutable
  owner comments and nonces. D1 binds source SHA/tree, policy and closure
  hashes, OCI archive hash/size/format and selected image graph, clean host
  direct-Claw inventory observation hash/time, input-bundle manifest hash, release ID/tag,
  ordered asset IDs/names/sizes/hashes, rollback deadline, and decision.
- **HOSTDEP-003 — Non-secret immutable transport.** Inputs are GitHub draft
  release assets addressed by exact release and asset IDs. A closed manifest
  names exactly ten DEBs, one fresh direct-Claw inventory observation, the
  Docker archive, OCI-layout archive, v2 evidence receipt and detached sidecar.
  Replacement is harmless because root verifies
  every approved byte hash and descriptor before mutation. The inventory asset
  contains only the closed non-secret observation; credentials, runner
  credential files and host receipts are never release assets.
  The v2 OCI receipt records archive device/inode as bounded producer-local
  diagnostics only. A verifier re-proves its own candidate as a stable regular
  single-link file and compares exact size, SHA-256 and the complete parsed
  content graph; it never equates producer filesystem IDs with verifier-host
  filesystem IDs.
- **HOSTDEP-004 — No runner-writable authority.** The initial root controller
  downloads approved assets directly into a new root:root `0700` transaction
  directory. It opens regular single-link files with no-follow semantics,
  checks stable inode/size, copies through already opened descriptors using
  exclusive files, then fsyncs files and directories before verification.
  No input under a runner worktree or runner-owned temporary directory is used.
  GitHub Actions is not used for this transition; tests and fresh read-only
  inventory collection run directly on Claw.
- **HOSTDEP-005 — Narrow privilege boundary.** Begin and finalize are
  invoked only from an owner-controlled root console outside both runner
  cgroups; no sudo rule is granted to `pall` or `claw-engine-runner`. The
  installed root client accepts one duplicate-key-rejecting JSON envelope of at
  most 32 KiB on stdin and rejects trailing bytes, extra fields and wrong types.
- **HOSTDEP-006 — Memory-only GitHub token.** The token appears only in the
  owner-controlled process environment and stdin pipe. The client/controller never writes,
  logs, hashes, exports, returns or includes it in exceptions, journals,
  receipts or artifacts. It clears references in `finally`; no physical-memory
  zeroization claim is made.
- **HOSTDEP-007 — Installed controller identity.** D0 installs a closed manifest,
  controller sources, client, systemd service/socket/timer and rollback
  utility under exact root-owned paths and modes. The installed identity binds
  repository, default branch, controller SHA/tree and every
  installed artifact hash. D0 has its own WAL, inverse for every target, and a
  verified receipt; it cannot start the host transition.
- **HOSTDEP-008 — Self-stop-safe begin phase.** The owner-controlled root begin
  client authenticates approval, source and release assets, then submits a
  request to the systemd controller. The controller records PREPARED durably
  before acknowledging. Host mutation runs in a systemd cgroup independent of
  both runners, so stopping the engine runner cannot terminate or orphan it.
- **HOSTDEP-009 — Existing WAL is authoritative.** The controller invokes the
  existing fixed operation set and root transaction state. It never reconstructs
  rollback from caller data. Apply-only external evidence is verified before
  journal creation; resume and rollback use durable root-owned state only.
- **HOSTDEP-010 — Two-phase completion.** Host operations may reach
  `HOST_APPLIED_PENDING_FINALIZE` after local rootless smoke, engine restart and
  app canary, but not COMMITTED. A fresh owner-controlled local finalize passes
  a fresh token; root independently verifies runner API identity, labels, local
  service projection, app continuity and the
  pending transaction ID before writing COMMITTED and the host receipt.
- **HOSTDEP-011 — Automatic rollback deadline.** A root-owned monotonic timer is
  armed before stopping the engine. If finalize is missing, late, mismatched, or
  fails, the controller attempts every inverse, records all failures, restores
  the original runner service/ownership/packages/subids/runtime/OCI state, and
  reports `ROLLBACK_BLOCKED` rather than false success if equality is not proven.
- **HOSTDEP-012 — Durable idempotent commands.** Begin cannot overwrite an OPEN
  or COMMITTED transaction. Duplicate begin/finalize/status/rollback requests
  are either exact idempotent replays or fail closed. Recovery handles process
  death before and after every fsync, rename, service transition and receipt.
- **HOSTDEP-013 — Receipt separation.** The begin acknowledgement, pending-host
  state, committed host receipt, rollback receipt and later helper-install
  receipt are distinct closed schemas. Only the committed host receipt can feed
  helper installation. None is a graph `Receipt` or Story 1.3 authority until
  the later evidence-admission phase.
- **HOSTDEP-014 — Sanitized observation.** Local commands upload no mutable raw
  logs or host files. They emit only fixed status vocabulary and hashes/base64
  for closed non-secret receipts after semantic verification of the same
  in-memory bytes; local transient files are removed before return and by the
  controller recovery path.
- **HOSTDEP-015 — App-stack noninterference.** Pre-mutation app service MainPID,
  User, ExecStart-path identity, WorkingDirectory, FragmentPath, active state
  and health canary are frozen. They must remain exact through pending,
  committed and rollback states. No app-stack path, runner credential value,
  private API, n8n, device, Docker socket or trading capability enters inputs,
  mounts, argv, logs or receipts.
- **HOSTDEP-016 — No implicit production admission.** A committed host receipt
  permits only the separately reviewed helper-install transaction and Story 1.2
  Phase B probe. It does not grant Story 1.3, release, deployment, private API,
  or live-trading authority.

## Interfaces and data flow

### D0: one-time deployment-controller provisioning

An owner-reviewed source PR lands the controller. A separate exact D0 owner
comment approves only the installed controller tuple. The operator executes one
root bootstrap command against a root-private verified source archive. The D0
transaction installs:

- `/usr/local/lib/mee-claw-host-deploy/<controller-sha>/` — immutable Python and
  policy artifacts;
- `/usr/local/libexec/mee-claw-host-deploy` — zero-argument stdin helper;
- `mee-claw-host-deploy.socket`, `.service`, `.timer` — root controller and
  rollback deadline;
- `/var/lib/mee-claw-host-deploy/` — root:root `0700` WAL, installed identity
  and receipts.

D0 verifies `systemd-analyze verify`, installed hashes/modes/owners, absence of
runner sudo grants and all argument/environment variants, then emits
a D0 receipt. D0 never changes packages, users, subids, engine/app units,
runner-tree ownership or OCI storage.

The D0 root CLI is closed by mode. `apply` alone accepts exactly the root-private
source root, controller SHA/tree, `apply`, authenticated D0 comment and
repository metadata; it validates the approval before the WAL may mutate. The
`resume` and `rollback` forms accept exactly the source root, controller
SHA/tree and their mode, re-prove source identity, and recover only from the
local durable D0 journal. They neither require nor read approval/GitHub inputs,
so an expiry or GitHub outage cannot prevent rollback. All missing, extra and
unknown-mode arguments fail closed.

### D1a: owner-controlled root begin transition

The owner opens a root console that is outside both GitHub runner cgroups and
invokes the installed zero-argument begin client. One bounded stdin envelope
contains an ephemeral GitHub token, approval comment ID and approved release ID.
The client independently authenticates the GitHub source/approval/release tuple,
downloads exact assets into root-private storage, consumes the D1 nonce,
creates/arms the rollback deadline, and starts the independent controller
service. It reports only the transaction ID and `BEGIN_ACCEPTED`. It never uses
the `pall` environment, worktree, sudo timestamp or runner-owned files.

The systemd controller executes through local smoke and runner restart, then
records `HOST_APPLIED_PENDING_FINALIZE`. It cannot emit the committed receipt.

### D1b: local finalize after reconnect

The owner invokes the installed root client only after GitHub reports the exact
runner online. It submits a fresh token plus the transaction ID. Root verifies
the current GitHub runner projection, exact labels, engine systemd projection,
rootless Podman storage and pinned actionlint `--pull=never --network=none`
version result, app continuity, timer validity and journal hashes. Exact success
cancels the rollback timer, fsyncs COMMITTED, writes the host receipt last and
emits a sanitized receipt envelope. Any mismatch leaves the timer armed.

### Status, resume and rollback

Status is read-only and returns a closed sanitized state projection. Resume and
rollback carry no external artifact paths and never accept alternate commands.
Owner rollback is allowed before or after COMMITTED while the approved rollback
window remains open. Evidence needed for retry stays root-only until rollback
completes or the owner explicitly closes rollback authority.

## Failure and recovery semantics

The state machine is:

`EMPTY -> PREPARED -> INPUTS_VERIFIED -> APPLYING(op) -> APPLIED(op) ->`
`HOST_APPLIED_PENDING_FINALIZE -> FINALIZING -> COMMITTED`

Failure before COMMITTED enters `ROLLING_BACK`; exact equality produces
`ROLLED_BACK`. Any inverse or equality failure produces terminally honest
`ROLLBACK_BLOCKED` with retryable root-only evidence. A crash between mutation
and journal outcome reconciles the current operation from observed state and
its durable snapshot. A crash after host apply but before finalize is recovered
by the armed timer. A late finalize can never cancel or overwrite an active
rollback. COMMITTED is written only after every local and authenticated
control-plane proof succeeds.

The controller durably creates a closed `host-apply-intent` before invoking the
host apply entrypoint. It binds the transaction to the already-fsynced begin
intent without predicting whether a committed host receipt will later exist.
If host apply reaches its own automatic `ROLLED_BACK` state and then returns an
error, the reconciler or explicit token-free rollback must first verify that
pre-host marker and only then create the null-prior-receipt rollback intent. A
later owner rollback after `COMMITTED` instead creates the rollback intent from
the exact existing host receipt hash. These two evidence roles may not be
collapsed: doing so would either permit invented terminal recovery or make a
valid post-commit rollback reject its committed receipt.

One historical transaction, `e8725f1d09cf11696bff392912d141cf`, reached a
semantic terminal rollback before the host-apply marker contract existed. It
may be closed only through the exact one-time legacy recovery entrypoint. That
path accepts a fresh immutable OWNER comment, binds the reviewed begin,
manifest, nonce-record, journal, credential-binding, old-controller and
installed recovery-controller hashes, and emits separate root-private
`RETROSPECTIVE_COMPATIBILITY_RECOVERY` authorization and receipt artifacts.
It never creates an ordinary host-apply marker, calls `host.main`, uses a token
or accesses the network, and must prove the terminal journal and singleton
binding byte-identical before and after. It is authority `NONE`, not a host
receipt, not reusable for another transaction and not ordinary pre-host proof.

## Verification and release gates

- Pure duplicate-safe parsers and schema parity for every request, identity,
  manifest, journal and receipt.
- Fake-root and PATH-stub tests for D0/D1 apply, every inverse, idempotent replay,
  short writes, fsync ordering, symlink/hardlink/path swaps and partial files.
- Process-kill matrix before/after every mutation and WAL transition, including
  runner self-stop, pending-finalize timeout, late finalize and rollback retry.
- GitHub API fixtures for wrong repository/default branch, owner/comment/TTL/nonce,
  release/asset replacement, runner identity/labels,
  pagination and insufficient token.
- Leakage scans proving sentinel tokens, auth headers, credential bytes and
  credential-derived digests are absent from stdout/stderr/journals/receipts,
  controller output and external evidence definitions.
- `systemd-analyze verify`, ShellCheck/actionlint, focused release
  tests, full release/graph suites, exact declared-conflict precommit, diff and
  syntax checks.
- Independent security and graph/governance YES on exact source SHA/tree and
  exact D0/D1 approval tuples. D0 provisioning and the root D1 begin each require
  a separate explicit owner checkpoint. First host execution uses a named
  maintenance window and retains rollback evidence until owner closure. The
  initial root-console checkpoint is not automated away until after UID
  separation has been proven by the committed host receipt.

## Non-goals

This controller does not deploy application code, run A2/private/live trading,
change the app-stack runner, provision generalized remote shell access, store a
GitHub credential, create a reusable package repository, or admit Story 1.3.
GitHub draft release assets are transport only; exact root-side verification,
not release mutability claims, supplies input integrity.

## Installed OCI approval path correction

### Status and incident

The owner approved design option 1: an explicit logical approval identity
separate from the physical installed file path. This is a source-only defect
correction and grants no D0, D1, finalize or other host authority.

The first authorized D1 begin against source
`c70bd2090e89bbcc749ca4b678ec3e22b338ef05` stopped fail-closed at
`STAGED_INPUT_VERIFY`, before nonce consumption or host WAL creation. The
installed policy records source identity
`ci/claw/oci-evidence-approval.json`, while the controller opens the installed
bytes at
`/usr/local/libexec/mee-claw-host-deploy-lib/oci-evidence-approval.json`.
`verify_oci_evidence_approval.py` currently compares those different path
domains directly and therefore rejects the real installed invocation.

### Considered approaches

1. **Selected:** add an explicit logical-path argument while retaining the
   existing physical-path argument. This makes both identities independently
   visible and testable.
2. Recreate a source-shaped installed directory or symlink and pass a relative
   physical path. This couples verification to process working-directory state
   and expands path-containment obligations.
3. Rewrite the installed policy to contain an absolute path. This mutates the
   reviewed policy bytes during installation and creates a second policy hash
   domain.

### Stable correction requirements

- **OCIAPATH-001 — Closed dual identity.** The verifier accepts physical bytes
  through required `--approval` and logical source identity through required
  `--approval-policy-path`. No fallback or implicit conversion is allowed.
- **OCIAPATH-002 — Canonical logical value.** The logical value must equal the
  literal `ci/claw/oci-evidence-approval.json`, and the current policy field
  `oci_evidence_approval` must equal that same literal. Absolute paths,
  backslashes, dot segments, alternate spellings and extra arguments fail.
- **OCIAPATH-003 — Installed physical boundary.** Production controller code
  passes the literal root-owned installed physical path and the literal
  canonical logical identity separately. Neither value comes from caller input
  or a runner-writable path.
- **OCIAPATH-004 — No semantic relaxation.** Receipt SHA, detached sidecar,
  archive bytes, source image/commit/tree, policy and closure projections,
  manifest/config/layers/rootfs/executable, pending rootless smoke, authority
  NONE and not-host-receipt checks remain exact.
- **OCIAPATH-005 — Recovery and release closure.** Changed installed bytes are
  rebound in the D0 install manifest and source approval allowlist. A landed
  source change requires a separate D0 owner approval/update, fresh direct-Claw
  inventory and a new immutable D1 owner approval. The failed D1 comment is
  never reused.

### Corrected interface and data flow

The complete verifier CLI remains the existing evidence interface plus one
required logical identity argument:

```text
verify_oci_evidence_approval.py \
  --policy <physical policy file> \
  --approval <physical installed approval file> \
  --approval-policy-path ci/claw/oci-evidence-approval.json \
  --receipt <v2 receipt> \
  --receipt-sha256 <detached sidecar> \
  --archive <Docker archive> \
  --layout <verified OCI layout> \
  --closure <physical package closure> \
  --origin https://github.com/Dimkox/multi-exchange-engine.git
```

The controller supplies both approval arguments as fixed source constants. The
verifier first closes argument and policy-path identity, then opens and verifies
the physical bytes through the unchanged evidence chain. The logical path is
never used for filesystem access.

### Failure, testing and acceptance

Any missing, duplicate, absolute, noncanonical or mismatched logical path fails
before OCI evidence can be accepted. A failed staged-input verification remains
pre-nonce and pre-host-WAL. Existing token-free status/rollback and D0 recovery
semantics are unchanged. The empty forensic transaction directory from the
failed begin contains no inputs, intent, nonce or journal and is not an active
transaction; manual root-state surgery is not part of this fix.

Implementation follows TDD:

1. RED proves the current real installed-style absolute physical path cannot
   coexist with the source-relative policy identity.
2. GREEN accepts that exact dual identity while retaining complete evidence
   verification.
3. Negative cases reject missing logical identity, absolute/backslash/dot-path
   variants, policy drift, physical-byte substitution and extra arguments.
4. A controller behavior test asserts both exact arguments and the installed
   physical path.
5. Install-manifest, source allowlist, graph, focused release, syntax and diff
   gates run directly on Claw Python 3.14.6 without GitHub Actions.

Completion is source readiness only. D0 update and D1 begin remain separate
owner checkpoints; D1 finalize always requires its own later confirmation.

## Real runner-tree metadata and pre-snapshot recovery addendum

The first landed-source D1 run that passed staged-input verification proved two
previously unmodelled target facts before any package, identity, subid, unit or
runner mutation: the registered runner tree contains ordinary internal symlinks
and the host does not provide `getfacl`/`setfacl`. The transaction MUST NOT add
an unreviewed package to the frozen closure or copy the credential-bearing tree.

`closed_tree` therefore accepts a symlink only when it is relative or absolute
to a target that resolves inside the exact runner-tree root. It rejects dangling
links, loops, absolute/out-of-tree targets and any concurrent member replacement.
The root-only credential commitment map binds every accepted link's relative
path, literal target and lstat type/mode/uid/gid/xattrs. Link ownership is not
changed because the link itself is not required for traversal. Regular files remain streamed through `O_NOFOLLOW`; directories and
links have separate HMAC domains.

Ownership rollback uses a Python-native, canonical root-only metadata snapshot
instead of external ACL commands. The snapshot covers the closed member set and
each member's type, relative path, mode, uid, gid, xattrs and literal symlink
target. POSIX ACLs are preserved through their system xattrs. Restore is
leaf-first for ownership and xattrs, never follows symlinks, rejects any changed
member set/type/target, and verifies exact equality before terminal rollback.
Every mutation rebinds the configured root to the snapshotted device/inode,
opens descendant directories component-by-component from that root descriptor
with no-follow semantics, and checks every final device/inode before mutation.
A swapped root, intermediate symlink, member replacement or set drift therefore
fails before the replacement object can be changed.
The journal retains only the bounded snapshot needed for deterministic recovery;
no credential bytes or content-derived plaintext digest is added.

If failure occurs after `freeze_inputs` but before credential key/map creation,
rollback treats an entirely absent credential-state directory as not-yet-created
and closes normally. A key-only, map-only, nonempty foreign directory or binding
mismatch remains fail-closed as `ROLLBACK_BLOCKED`. Token-free recovery must
converge the observed `ROLLING_BACK` journal before any new D1 tuple is accepted.

## Terminal credential-binding reuse addendum

The root transaction directory has one active `credential-binding.json`, so a
new D1 apply must never overwrite or silently reuse it. Before creating the new
binding, the controller may durably unlink an existing binding only when all of
these facts are proven from root-owned state: its closed transaction and policy
fields are valid, the referenced journal exists and is exactly terminal
`ROLLED_BACK`, and `credential-state` is absent. Missing journals, policy drift,
OPEN/COMMITTED/ROLLBACK_BLOCKED journals, partial credential state, or foreign
state remain fail-closed.

The referenced terminal journal is semantic evidence, not only a physical
file. Its history is replayed through the same ordered operation lifecycle:
each fixed operation has an `APPLYING`/`APPLIED` pair unless rollback begins,
post-apply phases follow their canonical order, rollback requires
`ROLLING_BACK` and may repeat or resume after `ROLLBACK_BLOCKED`; a blocked
record additionally requires at least one attempted/completed operation that
could have failed. No state
may follow terminal `ROLLED_BACK`. Owner rollback may start from a fully
`COMMITTED` lifecycle while the separately approved rollback window remains
open. Current/snapshot are null; applied is empty;
snapshot and verified-result maps bind each object to an actually attempted or
completed operation, with verified status exact; and any retained deadline or
finalize value passes its existing closed validator. A physically private but
semantically impossible terminal journal cannot release the binding.

The new journal remains the first durable initialization record. Initialization
cleanup is permitted only for the exact initial projection: schema v1, phase
`PREPARED`, history exactly `[PREPARED]`, status `OPEN`, empty applied,
snapshots and verified-results collections, and null current, snapshot,
deadline and finalize projection. Any other closed or malformed state is not a
fresh journal and remains fail-closed. If power is lost after the old terminal
binding is removed but before the new binding is created, this exact
PREPARED/no-binding rollback path removes the new journal and permits a clean
retry. Old terminal journals and rollback receipts remain immutable evidence;
only the singleton active-binding pointer is released.
