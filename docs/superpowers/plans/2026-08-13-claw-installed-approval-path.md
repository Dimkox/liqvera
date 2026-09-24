# Claw Installed OCI Approval Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the installed D1 OCI approval verification so physical root-owned file location and logical source-policy identity are explicit, independently validated and never compared as the same path domain.

**Architecture:** The verifier reads and hashes bytes only through required `--approval`, while required `--approval-policy-path` carries the immutable source-relative identity. The controller supplies the installed physical path and exact logical constant. The correction remains source-only until direct Claw verification, independent reviews, source merge, a separately approved D0 update, fresh inventory and a new D1 approval.

**Tech Stack:** Python 3.14 standard library, pytest, JSON, existing D0 install manifest, architecture graph checker, Bash/YAML policy checks.

## Global Constraints

- Authority remains `NONE`; implementing this plan performs no D0, D1, sudo,
  package, user, service, Podman or app-stack action.
- GitHub Actions is not used. All executable tests run directly on Claw with
  `/usr/bin/python3.14` in an isolated checkout/venv.
- The physical approval path is never policy authority. The logical policy path
  is exactly `ci/claw/oci-evidence-approval.json`.
- Missing, absolute, backslash, dot-segment, extra-field or mismatched logical
  identity fails before staging or nonce consumption.
- Existing D1 recovery remains local and approval-free; this correction must not
  add external evidence requirements to resume/rollback.
- Installed artifact hashes, graph inventory and exact source approval paths are
  refreshed after the final source bytes are frozen.
- D1 `finalize` remains separately owner-approved and out of scope.

---

### Task 1: Make the verifier distinguish physical and logical approval paths

**Files:**
- Modify: `scripts/verify_oci_evidence_approval.py`
- Modify: `tests/release/test_oci_evidence_v2.py`

- [x] **Step 1: Write the failing installed-style path tests**

```python
def test_installed_physical_approval_uses_source_relative_policy_identity(tmp_path):
    approval = copy_valid_approval_to(tmp_path / "installed" / "approval.json")
    verify_approval_cli(
        approval=approval,
        approval_policy_path="ci/claw/oci-evidence-approval.json",
    )

@pytest.mark.parametrize("logical", [
    None,
    "/ci/claw/oci-evidence-approval.json",
    r"ci\claw\oci-evidence-approval.json",
    "ci/claw/../claw/oci-evidence-approval.json",
    "ci/claw/other.json",
])
def test_logical_approval_policy_path_is_exact_and_closed(logical):
    with pytest.raises(SystemExit):
        verify_approval_cli(approval=installed_approval(), approval_policy_path=logical)
```

- [x] **Step 2: Run the focused test and confirm RED**

Run on Claw:
`python3.14 -B -m pytest tests/release/test_oci_evidence_v2.py -q`

Expected: the installed absolute physical path fails current policy equality or
the new required CLI argument is not recognized.

- [x] **Step 3: Implement the minimal dual-identity interface**

Add required CLI argument and pass it into the semantic verifier:

```python
parser.add_argument("--approval", required=True)
parser.add_argument("--approval-policy-path", required=True)

EXPECTED_APPROVAL_POLICY_PATH = "ci/claw/oci-evidence-approval.json"
if approval_policy_path != EXPECTED_APPROVAL_POLICY_PATH:
    raise EvidenceError("CURRENT_POLICY_APPROVAL_PATH")
if policy["oci_evidence_approval"] != approval_policy_path:
    raise EvidenceError("CURRENT_POLICY_BINDING")
approval = load_duplicate_safe(Path(approval_path).read_bytes())
```

Do not normalize or derive the logical identity from the physical path.

- [x] **Step 4: Run the focused tests and confirm GREEN**

Run: `python3.14 -B -m pytest tests/release/test_oci_evidence_v2.py -q`

Expected: all positive, mismatch and malformed logical-path cases pass.

---

### Task 2: Bind the installed controller invocation to both identities

**Files:**
- Modify: `scripts/claw_host_deployment_controller.py`
- Modify: `tests/release/test_claw_host_deployment_acquisition.py`
- Modify: `tests/release/test_claw_host_deployment_finalize.py` if recovery coverage needs an explicit regression

- [x] **Step 1: Write the failing controller invocation test**

```python
def test_staged_input_verifier_passes_physical_and_logical_approval_paths(fake_run):
    controller.verify_staged_inputs(staged_root(), installed_identity())
    argv = fake_run.single_argv("verify_oci_evidence_approval.py")
    assert argv[argv.index("--approval") + 1] == str(installed_approval_path())
    assert argv[argv.index("--approval-policy-path") + 1] == (
        "ci/claw/oci-evidence-approval.json"
    )
```

Also assert resume/rollback do not require the external approval path.

- [x] **Step 2: Run and confirm RED**

Run: `python3.14 -B -m pytest tests/release/test_claw_host_deployment_acquisition.py tests/release/test_claw_host_deployment_finalize.py -q`

Expected: controller argv lacks `--approval-policy-path`.

- [x] **Step 3: Pass the exact logical identity**

```python
argv.extend([
    "--approval", str(installed_root / "oci-evidence-approval.json"),
    "--approval-policy-path", "ci/claw/oci-evidence-approval.json",
])
```

The value must come from trusted controller source or a closed installed
identity field, never from D1 request, release metadata or owner comment text.

- [x] **Step 4: Run focused controller tests and confirm GREEN**

Run: `python3.14 -B -m pytest tests/release/test_claw_host_deployment_acquisition.py tests/release/test_claw_host_deployment_finalize.py -q`

---

### Task 3: Close installed artifacts, governance and exact source review

**Files:**
- Modify: `ci/claw/host-deployment-controller-manifest.json`
- Modify: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `architecture/architecture.yaml` only if the final changed path set introduces new files
- Modify: `tests/release/test_claw_source_controller_policy.py`
- Modify: `docs/implementation/1-2a-claw-engine-runner-host-transition.md`
- Modify: `docs/implementation/sprint-status.yaml`
- Modify: `handoff.md`

- [x] **Step 1: Refresh exact installed hashes after code is frozen**

Update only artifact SHA-256 values whose installed bytes changed. Run the
repository manifest binding test and require 19/19 exact matches.

- [x] **Step 2: Freeze the exact source approval path set**

Make workflow `--allowed-path` entries exactly equal the source PR diff. Keep
the existing test bound to the current landed base and reject missing, extra or
duplicate paths.

- [x] **Step 3: Run direct Claw verification**

```bash
/usr/bin/python3.14 -B -m pytest -q \
  tests/release/test_oci_evidence_v2.py \
  tests/release/test_claw_host_deployment_acquisition.py \
  tests/release/test_claw_host_deployment_finalize.py \
  tests/release/test_claw_host_deployment_install.py \
  tests/release/test_claw_source_controller_policy.py \
  tests/graph
python3.14 -m py_compile scripts/verify_oci_evidence_approval.py scripts/claw_host_deployment_controller.py
git diff --check
```

Expected: focused/release/graph checks pass; graph precommit retains exactly the
existing eight declared conflicts; strict merge remains fail-closed on those
eight plus `PHASE_POLICY_TIME_TRUST_MISSING`.

- [ ] **Step 4: Obtain independent reviews on the exact source SHA**

Security review owns physical/logical path separation, staging-before-nonce and
recovery. Graph review owns inventory, manifest, exact approval scope and the
absence of Story 1.3 authority. Both must return YES.

- [ ] **Step 5: Stop at source readiness**

After source merge, do not reuse the expired D1 approval. Prepare separate
owner checkpoints for the D0 update, fresh read-only inventory, new D1 `begin`
and later D1 `finalize`.
