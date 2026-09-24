# Claw Host Deployment Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the source-only, approval-gated controller that can later perform the reversible Story 1.2A engine-runner host transition without granting `pall` a sudo boundary or treating workflow bytes as root authority.

**Architecture:** A one-time root D0 transaction installs an immutable controller, a zero-argument root client and socket/timer-activated systemd units. D1 begins only from an owner-controlled root console; the root controller authenticates GitHub approval and release assets, stages exact inputs, and drives the existing host WAL to `HOST_APPLIED_PENDING_FINALIZE`. A second owner-controlled local root invocation after runner reconnect supplies an ephemeral token; root independently verifies control-plane and host canaries before COMMITTED, otherwise the deadline reconciler rolls back. GitHub Actions is not used.

**Tech Stack:** Python 3.14 standard library, Bash, systemd units, JSON Schema, pytest, pinned actionlint for the repository's remaining workflows, existing architecture graph checker.

## Global Constraints

- Authority remains `NONE`; this plan creates source and tests only and performs no host mutation.
- D0 provisioning, D1 root begin, and post-reconnect finalize are separate owner checkpoints.
- Neither runner user receives a sudo rule and only the owner-controlled root client may start or finalize D1.
- GitHub tokens exist only in memory and bounded stdin; never argv, environment preservation, files, logs, digests, receipts or artifacts.
- Every JSON input is duplicate-key rejecting, recursively closed, bounded and typed.
- Every root mutation is WAL-backed, fsynced, idempotent and has a tested inverse; failure is `ROLLBACK_BLOCKED`, never false success.
- App-stack unit, path, MainPID, user, executable identity and health canary remain outside the mutation domain.
- No private API, n8n, device, Docker socket, application deployment or live-trading capability is introduced.
- Existing eight declared graph conflicts remain intact; no realized graph receipt is added.

## File structure

- `scripts/claw_host_deployment_contract.py`: closed request, approval, bundle and receipt parsing shared by producer and independent verifier.
- `scripts/verify_claw_host_deployment_approval.py`: root-side GitHub/source/comment/release/run-log semantic verifier.
- `scripts/claw_host_deployment_install.py`: D0 installation WAL and exact inverse operations.
- `scripts/claw_host_deployment_client.py`: zero-argument bounded-stdin client for the fixed Unix socket.
- `scripts/claw_host_deployment_controller.py`: root socket request handler, immutable acquisition, transaction orchestration, finalize and deadline rollback.
- `scripts/claw_host_bootstrap_transaction.py`: expose pending-finalize and final commit boundaries without weakening existing recovery.
- `ci/claw/install-host-deployment-controller.sh`: owner-controlled D0 entrypoint.
- `ci/claw/systemd/mee-claw-host-deploy.socket`, `mee-claw-host-deploy@.service`, `mee-claw-host-deploy-reconcile.service`, `mee-claw-host-deploy-reconcile.timer`: independent root execution and rollback deadline.
- `schemas/claw-host-deployment-*.schema.json`: closed approval/request/state/receipt contracts.
- `tests/release/test_claw_host_deployment_*.py`: semantic, fake-root, crash, leakage and local-control policy tests.

---

### Task 1: Closed deployment contracts and independent approval verifier

**Files:**
- Create: `scripts/claw_host_deployment_contract.py`
- Create: `scripts/verify_claw_host_deployment_approval.py`
- Create: `schemas/claw-host-deployment-request-v1.schema.json`
- Create: `schemas/claw-host-deployment-receipt-v1.schema.json`
- Create: `tests/release/test_claw_host_deployment_contract.py`

**Interfaces:**
- Consumes: exact repository/source/policy/closure/OCI/host-observation tuple from `HOSTDEP-001..003`.
- Produces: `load_closed_bytes(raw: bytes, *, max_bytes: int) -> dict`, `verify_request(value: dict, expected_action: str) -> dict`, and `verify_approval(api: ApiClient, request: dict, installed_identity: dict) -> ApprovedDeployment`.

- [ ] **Step 1: Write the failing closed-contract tests**

```python
def test_request_rejects_duplicate_extra_and_token_projection():
    with pytest.raises(ContractError, match="DUPLICATE_KEY"):
        load_closed_bytes(b'{"action":"status","action":"rollback"}', max_bytes=32768)
    value = valid_request()
    value["persisted_token"] = "forbidden"
    with pytest.raises(ContractError, match="REQUEST_FIELDS"):
        verify_request(value, expected_action="finalize")

@pytest.mark.parametrize("mutation", [
    lambda x: x.update(repository="other/repo"),
    lambda x: x.update(controller_sha="0" * 40),
    lambda x: x["assets"].reverse(),
    lambda x: x.update(host_inventory_sha256="0" * 64),
])
def test_owner_approval_tuple_is_exact(mutation):
    approval = valid_approval()
    mutation(approval)
    with pytest.raises(ApprovalError):
        verify_approval(FakeApi(), valid_request(), installed_identity(), approval=approval)
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_contract.py -q`

Expected: collection fails because `scripts.claw_host_deployment_contract` does not exist.

- [ ] **Step 3: Implement the minimal closed parser and semantic verifier**

```python
MAX_REQUEST = 32768
REQUEST_FIELDS = {"schema_version", "action", "github_token", "repository", "approval_comment_id", "release_id", "transaction_id"}

def load_closed_bytes(raw: bytes, *, max_bytes: int = MAX_REQUEST) -> dict:
    if not raw or len(raw) > max_bytes:
        raise ContractError("REQUEST_SIZE")
    value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_reject_duplicates)
    if not isinstance(value, dict) or set(value) != REQUEST_FIELDS:
        raise ContractError("REQUEST_FIELDS")
    return value
```

The verifier must require canonical immutable comment JSON, OWNER login/id/association, `created_at == updated_at`, `created_at < expires_at <= created_at + 1h`, exact source SHA/tree, policy/closure/archive/observation/bundle hashes, exact ordered asset IDs/names/sizes/hashes, unique nonce, release ID/tag/draft state, and exact direct-Claw inventory identity/time. It must fetch bounded pages and reject `Link: rel="next"`.

- [ ] **Step 4: Add closed schemas and schema/semantic parity assertions**

Every nested object uses `additionalProperties: false`; hashes use `^[0-9a-f]{64}$`, Git SHAs `^[0-9a-f]{40}$`, IDs are positive integers, and actions are `begin|finalize|status|rollback`. A bounded memory-only token is mandatory only for the network-authenticated `begin` and `finalize` actions; the local recovery actions `status` and `rollback` require literal `null` so recovery never depends on GitHub availability. Receipt status is one of `D0_VERIFIED|BEGIN_ACCEPTED|HOST_APPLIED_PENDING_FINALIZE|COMMITTED|ROLLED_BACK|ROLLBACK_BLOCKED`.

- [ ] **Step 5: Run GREEN and commit**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_contract.py -q`

Expected: all contract, replay, TTL, pagination, secret-leak and schema parity cases pass.

Commit: `git commit -m "feat(claw): add host deployment contracts"`

### Task 2: D0 root installation transaction

**Files:**
- Create: `scripts/claw_host_deployment_install.py`
- Create: `ci/claw/install-host-deployment-controller.sh`
- Create: `ci/claw/host-deployment-controller-manifest.json`
- Create: `ci/claw/systemd/mee-claw-host-deploy.socket`
- Create: `ci/claw/systemd/mee-claw-host-deploy@.service`
- Create: `ci/claw/systemd/mee-claw-host-deploy-reconcile.service`
- Create: `ci/claw/systemd/mee-claw-host-deploy-reconcile.timer`
- Create: `tests/release/test_claw_host_deployment_install.py`

**Interfaces:**
- `apply` consumes root-private verified source root, exact controller SHA/tree, D0 approval comment and repository metadata. `resume` and `rollback` consume only source root, exact controller SHA/tree and their exact mode; they use the local durable D0 journal and do not fetch/read approval or GitHub data.
- Produces: root-only `/var/lib/mee-claw-host-deploy/D0-VERIFIED.json` and installed identity; cannot start D1.

**Closed root CLI:**

```bash
# first apply only; approval verification is mandatory
ci/claw/install-host-deployment-controller.sh <source_root> <controller_sha> <controller_tree> apply <d0_comment.json> <repository.json>

# durable local recovery only; approval files and GitHub are intentionally absent
ci/claw/install-host-deployment-controller.sh <source_root> <controller_sha> <controller_tree> resume
ci/claw/install-host-deployment-controller.sh <source_root> <controller_sha> <controller_tree> rollback
```

Every form rejects missing or extra arguments and re-proves the exact Git
SHA/tree before invoking the installer. Only `apply` may consume the expiring
D0 approval; recovery is deliberately available after that approval expires or
GitHub is unavailable.

- [ ] **Step 1: Write RED tests for exact D0 operations and inverses**

```python
TARGETS = {
    "/usr/local/libexec/mee-claw-host-deploy": 0o755,
    "/etc/systemd/system/mee-claw-host-deploy.socket": 0o644,
}

@pytest.mark.parametrize("fail_after", range(1, len(TARGETS) + 5))
def test_every_d0_failure_restores_exact_baseline(fake_root, fail_after):
    before = project_tree(fake_root)
    with pytest.raises(InjectedFailure):
        install(fake_root, reviewed_source(), fail_after=fail_after)
    assert project_tree(fake_root) == before
```

Also test symlink/hardlink targets, wrong owner/mode, stale OPEN journal, short write, fsync failure, prior timer state, `systemd-analyze` failure, repeated apply/rollback, and no credential values/digests in outputs.

- [ ] **Step 2: Confirm RED**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_install.py -q`

Expected: import failure for the missing installer.

- [ ] **Step 3: Implement one OperationBackend and fsynced WAL**

```python
OPERATIONS = (
    "freeze_identity", "install_library", "install_client",
    "install_units", "daemon_reload", "enable_socket", "enable_reconciler",
    "verify_installed", "write_d0_receipt",
)
```

Each operation records PREPARED/APPLYING/APPLIED with the exact prior projection before mutation. Rollback attempts every inverse, aggregates failures, retains snapshots on `ROLLBACK_BLOCKED`, and writes `ROLLED_BACK` only after byte/metadata/unit equality. D0 rejects any pre-existing `/etc/mee-controller/github-token`, any runner sudo grant, or manifest mismatch.

- [ ] **Step 4: Add exact root-only systemd contracts**

The socket is root-owned and fixed at `/run/mee-claw-host-deploy/control.sock`. The service runs the immutable installed controller with `StandardInput=socket`, `NoNewPrivileges=true`, `PrivateTmp=true`, `ProtectHome=true`, and the exact existing runner-tree bind required by the ownership transition. `ProtectSystem=false` is explicit because the root WAL must perform the reviewed package, identity, subid, runtime, systemd and rollback mutations; the closed backend and journal, rather than a misleading read-only namespace, constrain those writes. The unit never binds `/home/operator/app-stack`, and it has no network restriction because GitHub verification/download is required. No sudoers file is installed for either runner user; Python independently rejects unexpected argv.

- [ ] **Step 5: Run GREEN, external syntax gates and commit**

Run:

```bash
python -B -m pytest tests/release/test_claw_host_deployment_install.py -q
bash -n ci/claw/install-host-deployment-controller.sh
systemd-analyze verify ci/claw/systemd/mee-claw-host-deploy*.service ci/claw/systemd/mee-claw-host-deploy*.socket ci/claw/systemd/mee-claw-host-deploy*.timer
```

Expected: all executable fake-root and syntax gates pass; environment-missing tools are reported as unrun, never claimed green.

Commit: `git commit -m "feat(claw): add deployment controller installer"`

### Task 3: Zero-argument client and root socket controller

**Files:**
- Create: `scripts/claw_host_deployment_client.py`
- Create: `scripts/claw_host_deployment_controller.py`
- Create: `tests/release/test_claw_host_deployment_controller.py`

**Interfaces:**
- Consumes: one <=32 KiB request envelope on stdin and fixed Unix socket.
- Produces: one <=8 KiB closed sanitized response containing only transaction ID, state and receipt hash; token is never returned.

- [ ] **Step 1: Write RED protocol and leakage tests**

```python
def test_client_rejects_argv_and_trailing_input(monkeypatch):
    assert client_main(["unexpected"]) == 2
    with pytest.raises(ContractError, match="TRAILING_INPUT"):
        decode_frame(b"\x00\x00\x00\x02{}x")

def test_token_never_crosses_response_or_durable_state(tmp_path, capsys):
    token = "sentinel-token-never-persist"
    response = handle_request(envelope(token), FakeGitHub(), tmp_path)
    assert token not in json.dumps(response)
    assert token not in capsys.readouterr().out + capsys.readouterr().err
    assert not [p for p in tmp_path.rglob("*") if p.is_file() and token.encode() in p.read_bytes()]
```

- [ ] **Step 2: Confirm RED**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_controller.py -q`

Expected: missing client/controller imports.

- [ ] **Step 3: Implement length-prefixed socket transport**

```python
HEADER = struct.Struct("!I")

def read_frame(stream, limit=32768):
    size = HEADER.unpack(read_exact(stream, HEADER.size))[0]
    if size < 2 or size > limit:
        raise ContractError("FRAME_SIZE")
    payload = read_exact(stream, size)
    if stream.read(1):
        raise ContractError("TRAILING_INPUT")
    return payload
```

The client checks root EUID, zero argv, socket type/owner/mode, sends one frame and prints only the sanitized response. The controller reads one request, clears the token in `finally`, maps only four actions, and writes no runner-provided path.

- [ ] **Step 4: Add peer/process and concurrency controls**

Use `SO_PEERCRED` on Linux, one root-owned nonblocking controller `flock` across every journal mutation, O_EXCL transaction IDs and nonce consumption, and bounded simultaneous requests. The request registry provides framing and per-key serialization but never caches a response. Token-free idempotency comes from the authoritative nonce, journal and receipt state: `(approval_comment_id, release_id)` for begin and `transaction_id` afterward. A mismatched replay fails; every identical replay resolves the current durable state so a later rollback cannot be hidden by an older `COMMITTED` response.

- [ ] **Step 5: Run GREEN and commit**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_controller.py -q`

Commit: `git commit -m "feat(claw): add root deployment socket controller"`

### Task 4: Root-side GitHub acquisition and immutable input staging

**Files:**
- Modify: `scripts/claw_host_deployment_controller.py`
- Modify: `scripts/verify_claw_host_deployment_approval.py`
- Create: `schemas/claw-host-input-bundle-v1.schema.json`
- Create: `tests/release/test_claw_host_deployment_acquisition.py`

**Interfaces:**
- Consumes: D1 approval comment ID, release ID and in-memory token.
- Produces: root-owned transaction input directory containing exactly 10 DEBs, one fresh direct-Claw inventory JSON, Docker archive, OCI-layout archive, v2 receipt and sidecar plus an fsynced closed manifest. The receipt's device/inode are producer-local diagnostics: the verifier still requires a stable regular single-link candidate, exact size/SHA-256 and content graph, but does not compare filesystem IDs across hosts.

- [ ] **Step 1: Write RED acquisition tests**

Cover wrong release/tag/draft, asset replacement, duplicate/missing/extra asset, redirect host, pagination, size mismatch, digest mismatch, source swap, symlink/hardlink, interrupted stream, partial fsync, token leakage and direct host-observation asset mismatch.

```python
def test_release_asset_set_is_exact():
    assets = approved_assets()
    assets.append(dict(assets[0], id=999, name="extra.deb"))
    with pytest.raises(AcquisitionError, match="ASSET_SET"):
        acquire(FakeGitHub(assets=assets), approved_tuple())
```

- [ ] **Step 2: Confirm RED**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_acquisition.py -q`

- [ ] **Step 3: Implement bounded authenticated downloads**

Fetch repository, commit/tree, owner comment, release and assets from the exact GitHub API host. Follow redirects only to approved GitHub asset hosts while stripping Authorization on cross-host redirects. Stream each asset through an already-open O_EXCL root file, enforce approved byte size during read, hash while streaming, fsync file, rename and fsync directory. Never rely on asset filename for identity.

- [ ] **Step 4: Verify the direct-Claw host observation asset**

Require exactly one `host_inventory` release asset whose ID, name, size and SHA are in the immutable OWNER D1 comment. Rehash its canonical bytes, require `collection_mode=DIRECT_CLAW`, exact collector/controller identities and `observed_at` within one hour before the approval comment, then independently invoke `verify_claw_host_inventory`. Reject nonempty blockers. No GitHub Actions run or log is accepted.

- [ ] **Step 5: Verify package and OCI inputs before WAL creation**

Reuse `verify_oci_evidence_approval.py`; validate every DEB hash and `dpkg-deb --show` tuple; require exact bundle manifest hash and asset projection. No journal is created until all checks pass.

- [ ] **Step 5a: Persist the host-apply intent before host apply**

After immutable acquisition and nonce consumption, write and fsync the closed
host-apply intent before calling the host transaction. It binds the exact
durable begin-intent hash and contains no token, nonce, or receipt prediction.
If host apply fails after its WAL has already reached `ROLLED_BACK`, explicit
token-free rollback and the reconciler verify this marker before creating the
null-prior-receipt rollback intent and finishing the controller rollback
receipt. A rollback after `COMMITTED` separately binds the exact committed host
receipt hash. Both paths are idempotent on exact replay.

- [ ] **Step 5b: Close the pre-marker terminal incident without fabricating provenance**

The exact historical transaction `e8725f1d09cf11696bff392912d141cf`
requires a distinct owner-approved compatibility path. Verify all root-private
begin/manifest/nonce/journal/binding bytes and identities against the reviewed
incident constants and current installed D0 identity under one controller
lock. Persist a closed compatibility authorization before creating the normal
null-prior rollback intent and rollback receipt; then persist a distinct
compatibility receipt. Do not create the ordinary host-apply marker, call the
host transaction, access GitHub/network, or mutate the journal, binding,
credential state, services, packages, users or app-stack. Replay uses the
durable compatibility record after the OWNER comment expires.

- [ ] **Step 6: Run GREEN and commit**

Run: `python -B -m pytest tests/release/test_claw_host_deployment_acquisition.py tests/release/test_oci_evidence_v2.py -q`

Commit: `git commit -m "feat(claw): acquire immutable host inputs"`

### Task 5: Pending-finalize WAL and deadline rollback

**Files:**
- Modify: `scripts/claw_host_bootstrap_transaction.py`
- Modify: `schemas/claw-host-bootstrap-receipt-v1.schema.json`
- Modify: `scripts/write_claw_host_bootstrap_receipt.py`
- Modify: `scripts/verify_claw_host_bootstrap_receipt.py`
- Create: `tests/release/test_claw_host_pending_finalize.py`

**Interfaces:**
- Consumes: root-staged immutable inputs and existing host operation backend.
- Produces: `HOST_APPLIED_PENDING_FINALIZE` state, then either COMMITTED host receipt or complete rollback.

- [ ] **Step 1: Write RED state-machine tests**

```python
def test_apply_stops_at_pending_finalize():
    journal = run_apply(FakeBackend())
    assert journal.phase == "HOST_APPLIED_PENDING_FINALIZE"
    assert not host_receipt_path.exists()

def test_deadline_without_finalize_rolls_back_every_operation():
    journal = run_to_pending(FakeBackend())
    reconcile_deadline(journal, now=journal.deadline + 1)
    assert journal.phase == "ROLLED_BACK"
```

Include kill points before/after runner stop/start, pending fsync, timer arm, finalize verification, timer cancel, COMMITTED fsync, and rollback of every operation. A rollback failure must retain snapshots and become `ROLLBACK_BLOCKED`.

- [ ] **Step 2: Confirm RED**

Run: `python -B -m pytest tests/release/test_claw_host_pending_finalize.py -q`

- [ ] **Step 3: Split apply and finalize**

Replace the final unconditional `VERIFYING -> VERIFIED -> COMMITTED` with:

```python
journal.record("HOST_APPLIED_PENDING_FINALIZE", applied, status="OPEN", deadline=deadline)
return PendingFinalize(transaction_id=journal.transaction_id, deadline=deadline)
```

Add `finalize(backend, journal, authenticated_projection)` that rehydrates durable snapshots, verifies the exact current engine/app/rootless/runner projection, records FINALIZING, cancels the deadline only after all checks, fsyncs COMMITTED, and writes the receipt last.

- [ ] **Step 4: Make deadline reconciliation authoritative**

`reconcile-deadlines` scans only root-owned closed transaction directories. Expired pending transactions call existing recovery using durable state; late finalize observes `ROLLING_BACK|ROLLED_BACK|ROLLBACK_BLOCKED` and cannot mutate it.

- [ ] **Step 5: Run GREEN and regression matrix, then commit**

Run:

```bash
python -B -m pytest tests/release/test_claw_host_pending_finalize.py tests/release/test_claw_host_transaction_matrix.py tests/release/test_claw_host_real_backend.py tests/release/test_claw_credential_commitments.py tests/release/test_claw_host_receipt_binding.py -q
```

Commit: `git commit -m "feat(claw): require post-reconnect host finalize"`

### Task 6: Authenticated local finalize/status/rollback

**Files:**
- Create: `tests/release/test_claw_host_deployment_finalize.py`
- Modify: `scripts/claw_host_deployment_controller.py`
- Modify: `scripts/claw_host_deployment_client.py`
- Modify: `scripts/claw_host_deployment_contract.py`
- Modify: `schemas/claw-host-deployment-request-v1.schema.json`
- Modify: `schemas/claw-host-deployment-response-v1.schema.json`
- Create: `schemas/claw-host-deployment-rollback-receipt-v1.schema.json`
- Modify: `ci/claw/systemd/mee-claw-host-deploy.socket`
- Modify: `ci/claw/systemd/mee-claw-host-deploy@.service`
- Modify: `ci/claw/systemd/mee-claw-host-deploy-reconcile.service`
- Modify: `ci/claw/host-deployment-controller-manifest.json`

**Interfaces:**
- Consumes: an owner-controlled local root invocation and exact transaction ID; `finalize` additionally consumes a memory-only token after the dedicated runner reconnects, while `status` and `rollback` require a null token and make no network call.
- Produces: sanitized state/receipt envelope; no artifact and no raw host output. GitHub Actions is not used.

- [x] **Step 1: Write RED local-control policy tests**

```python
def test_finalize_is_local_root_only_and_has_no_actions_surface():
    source = Path("scripts/claw_host_deployment_client.py").read_text()
    assert "repository_dispatch" not in source
    assert "workflow_run" not in source
    assert "actions/runs" not in source
    assert "FINALIZE" in source and "ROLLBACK" in source and "STATUS" in source
```

Also require root peer credentials, exact installed source identity, bounded duplicate-safe stdin, exact dedicated runner identity/labels from the GitHub API, token non-persistence/leakage, and no sudo rule for either runner user.

- [x] **Step 2: Confirm RED**

Run on Claw with `/usr/bin/python3.14`: `python -B -m pytest tests/release/test_claw_host_deployment_finalize.py -q`

- [x] **Step 3: Implement the installed local commands**

The zero-argument root client reads one duplicate-safe canonical bounded request from its root-console stdin, sends it over the root:root `0600` Unix socket, validates the returned closed response in memory and emits only the closed response fields. The controller accepts only the exact `begin|finalize|status|rollback` action enum and maps each value to a fixed runtime method. Token references are dropped in `finally` and never persisted.

- [x] **Step 4: Add authenticated runner checks to root finalize**

Root requires the installed controller SHA/tree, pending transaction ID, exact current runner ID/name/status and required labels. It independently verifies the online runner API projection before COMMITTED.

Successful rollback durably binds the prior committed-host receipt hash and the terminal rollback journal in a separate `claw-host-deployment-rollback-receipt-v1`; `ROLLBACK_BLOCKED` retains the prior receipt and rollback intent and emits no success receipt. Global runner-count drift is outside the dedicated-runner equality domain, while runner ID/name/status/labels and unique matching count remain exact.

- [x] **Step 5: Run GREEN on Claw**

Run:

```bash
/usr/bin/python3.14 -B -m pytest tests/release/test_claw_host_deployment_finalize.py -q
```

The source commit remains part of the single Task 7 source-only commit after full gates and review.

### Task 7: Graph binding, full gates and source-only release

**Files:**
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/requirements.yaml`
- Modify: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `tests/graph/test_third_final_review_policy.py`
- Modify: `docs/implementation/1-2a-claw-engine-runner-host-transition.md`
- Modify: `handoff.md`
- Modify: `ci/claw/host-helper-manifest.json` for every installed artifact hash.

**Interfaces:**
- Consumes: all Tasks 1-6 committed source.
- Produces: exact inventory/proof lanes for `HOSTDEP-001..016`, source-only approval scope and reviewable D0/D1 operational handoff.

- [x] **Step 1: Add graph RED assertions**

Require every new path exactly once, map contract/runtime/test/evidence/rollback artifacts to HOSTDEP requirements, forbid realized receipt nodes, retain authority NONE and all eight conflicts, and assert controller allowed paths equal the entire `c07f251...HEAD` change set within the cap.

- [x] **Step 2: Confirm RED**

Run: `python -B -m pytest tests/graph/test_third_final_review_policy.py tests/release/test_claw_source_controller_policy.py -q`

- [x] **Step 3: Add inventory, requirements and exact approval paths**

Add `requirement:HOSTDEP-001` through `requirement:HOSTDEP-016` as DECLARED/NON_PRODUCT with owner `operations` or `security`, and bind every file to the narrowest proof lane. Do not create a realized graph Receipt.

- [x] **Step 4: Refresh installed hashes and documentation**

Regenerate the helper/controller manifest from committed source bytes using the repository's deterministic manifest test. Document exact D0 inputs, D1 owner tuple, root-console command shape without a token value, status/finalize/rollback commands, maintenance window, expected receipts and recovery decision tree.

- [x] **Step 5: Run complete verification**

```bash
python -B -m pytest tests/release -q
python -B -m pytest tests/graph -q
python -B -m pytest tests/a2 -q
python -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --format text --allow-declared-conflicts
python -B scripts/check-architecture-graph.py --manifest-root architecture --phase merge --format text
python -m py_compile scripts/claw_host_deployment_*.py scripts/verify_claw_host_deployment_approval.py scripts/claw_host_bootstrap_transaction.py
bash -n ci/claw/*.sh
git diff --check
```

Expected: release/graph/A2 pass; precommit exits 0 with exactly eight declared conflicts; merge remains fail-closed on those eight plus `PHASE_POLICY_TIME_TRUST_MISSING`; syntax and diff checks pass.

- [ ] **Step 6: Obtain independent exact-commit reviews**

Security review covers token non-persistence, root trust, same-UID boundary, artifact provenance, WAL/deadline recovery, app noninterference and receipt truth. Graph/governance review covers exact inventory, proof lanes, authority NONE, conflict retention and source approval scope. Both must return YES with no P0/P1.

- [ ] **Step 7: Commit and prepare source-only PR**

Commit: `git commit -m "feat(claw): add host deployment controller"`

The PR owner comment explicitly says `SOURCE_ONLY`, `host_mutation=NOT_AUTHORIZED`, and binds exact head SHA/tree/path set and the two independent reviews. Host execution begins only after this source lands and a separate exact D0 approval is issued.

### Task 8: Close real runner-tree metadata and pre-snapshot recovery

**Files:**
- Modify: `scripts/claw_host_bootstrap_transaction.py`
- Modify: `tests/release/test_claw_host_real_backend.py`
- Modify: `tests/release/test_claw_credential_commitments.py`
- Modify: `tests/release/test_claw_host_pending_finalize.py`
- Modify: `tests/release/test_claw_runner_host_bootstrap.py`
- Modify: `ci/claw/host-deployment-controller-manifest.json`
- Modify: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: an exact runner-tree root containing regular files, directories and symlinks whose resolved targets remain within that root.
- Produces: `tree_metadata_projection(root)`, `restore_tree_metadata(root, projection)`, link-aware `CredentialCommitments`, and token-free convergence from pre-snapshot `ROLLING_BACK`.

- [ ] **Step 1: Write RED tests for internal and escaping symlinks**

Create a real temporary runner tree with a regular file and a relative internal
symlink. Require `closed_tree` and credential create/verify to accept it, then
require an absolute or relative escape, a dangling link and link-target drift to
fail without following the link.

- [ ] **Step 2: Run the symlink tests and observe the current rejection**

Run: `python -B -m pytest -c /dev/null tests/release/test_claw_credential_commitments.py -q`

Expected: the contained-symlink case fails with `RUNNER_TREE_ESCAPE` or
`RUNNER_TREE_INVALID`; existing escape cases remain fail-closed.

- [ ] **Step 3: Implement closed link inventory and HMAC binding**

Add a distinct `LINK` HMAC domain and canonical link records. Use `lstat`,
`readlink` and resolved-root containment; never open or hash through a symlink.
Verification requires the exact link set, literal target, metadata and approved
owner (link ownership itself remains unchanged) and uses `hmac.compare_digest`.

- [ ] **Step 4: Write RED metadata snapshot/restore tests**

Require round-trip equality for files, directories, xattrs and internal links;
require added/removed/retargeted members and type changes to fail closed. Assert
that RealBackend no longer invokes `getfacl` or `setfacl`.

- [ ] **Step 5: Implement Python-native metadata snapshot/restore**

Capture a canonical bounded member projection without file contents. Restore
root and member device/inode identity, ownership, modes for non-links and
xattrs without following links; verify the complete projection after restore.
Transfer and restore open the exact root and every directory component with
directory descriptors and no-follow semantics, validate the snapshotted inode
before each mutation, and reject root/member swaps before changing the
replacement object.

- [ ] **Step 6: Write RED pre-snapshot rollback tests**

Start from a journal with only `freeze_inputs` applied and no credential-state
directory. Recovery must reach `ROLLED_BACK`. Key-only/map-only or foreign state
must remain `ROLLBACK_BLOCKED` with evidence intact.

- [ ] **Step 7: Implement idempotent not-yet-created credential close**

Allow terminal close only when both key and map and the state directory are all
absent. Preserve fail-closed handling for every partial or foreign state.

- [ ] **Step 8: Run complete Claw gates and exact reviews**

Run focused transaction/credential/install/controller tests, all release tests,
all graph tests, graph precommit/merge diagnostics, manifest/allowlist/inventory
closure, Python/YAML/Bash syntax and `git diff --check` on Claw Python 3.14.6.
Obtain independent security and graph YES before source-only merge. After merge,
refresh D0, recover the existing transaction token-free, then create a new D1
inventory/release/OWNER approval; never replay the consumed nonce.

### Task 13: Reconcile a completed rollback binding before the next apply

**Files:**
- Modify: `scripts/claw_host_bootstrap_transaction.py`
- Modify: `tests/release/test_claw_credential_commitments.py`
- Modify: `ci/claw/host-deployment-controller-manifest.json`
- Modify: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: the singleton root-owned credential binding, its referenced terminal journal, current policy hash and credential-state directory.
- Produces: a new-apply initialization boundary that releases only a proven terminal `ROLLED_BACK` binding and preserves all other states.

- [x] **Step 1: Write the failing next-apply regression**

Create a terminal `ROLLED_BACK` journal and matching binding, invoke the real
`main()` apply initialization for a different transaction with downstream
operations isolated, and require return zero plus an exact new binding. Preserve
the old journal as evidence.

- [x] **Step 2: Run the regression and observe the O_EXCL failure**

Run: `python -B -m pytest -c /dev/null tests/release/test_claw_credential_commitments.py -q`

Expected: the next-apply case fails because `create_credential_binding` sees the
old singleton binding and `main()` returns `2`.

- [x] **Step 3: Implement closed terminal-binding reconciliation**

Before new binding creation, validate the old binding and its referenced journal
against the current policy, require exact `ROLLED_BACK` terminal state and absent
credential-state, then use `durable_unlink`. Do not delete or mutate the old
journal or rollback receipt.

- [x] **Step 4: Add fail-closed state-table regressions**

Require missing/corrupt/OPEN/COMMITTED/ROLLBACK_BLOCKED journals, policy drift,
partial key/map, empty or foreign credential-state, and invalid transaction IDs
to preserve the existing binding and reject the new apply.

Initialization recovery must additionally require the exact initial journal
projection (schema v1, `PREPARED`, history `[PREPARED]`, `OPEN`, empty
collections and null operation/deadline/finalize fields). Mutating any closed
field must preserve both the current journal and prior binding.

Before releasing the prior binding, validate the referenced `ROLLED_BACK`
journal semantically by replaying the ordered `APPLYING`/`APPLIED`, post-apply,
rollback, blocked-retry and terminal transitions. Snapshot/result objects must
bind to actually attempted/completed operations, and verified result status is
exact. Empty applied/current/snapshot terminal markers and retained deadline or
finalize projections remain closed. Type corruption, impossible ordering or
unknown nested bindings must preserve all recovery evidence.

`ROLLBACK_BLOCKED` is legal only after an operation was attempted or completed;
an empty PREPARED rollback cannot have an operation failure and must not be
accepted as terminal semantic evidence.

The replay must accept a canonical full apply/finalize `COMMITTED` history that
later enters owner-authorized `ROLLING_BACK -> ROLLED_BACK`; committed rollback
is an existing controller contract, not an impossible transition.

- [ ] **Step 5: Run exact Claw release, graph and source-closure gates**

Run the focused regression, complete release/graph suites, manifest and exact
allowlist/inventory checks, precommit/merge diagnostics, syntax checks and diff
check on Claw Python 3.14.6. Obtain independent source reviews before landing,
then refresh D0 and recover the already-created PREPARED D1 journal without a
token before generating a new inventory/release/approval tuple.
