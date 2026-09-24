# M6 Claw Release and mee-a2 Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an exact-SHA, graph-complete Stage A release on Claw and consume it through an explicitly authorized, `mee-a2`-only deployment that preserves evidence and the dirty app-stack worktree.

**Architecture:** Default-branch-controlled PR validation runs exact same-repository source in a disposable rootless sandbox with no production reachability. A separate trusted release workflow consumes immutable validation receipts and first emits a build/scan candidate. App-stack validation then emits its exact SHA/DB-contract receipt. A human-authorized promotion request binds those two independent inputs; promotion emits a realized receipt, and only then can the final release root be assembled. A separate deployment authorization allows the app-stack workflow to materialize an exact authenticated archive and deploy only the named Compose project.

**Tech Stack:** GitHub Actions on `[self-hosted, claw]`, rootless Podman for untrusted PR isolation, Docker/BuildKit for trusted release builds, Python 3.12, JSON Schema, Syft, Trivy, OCI images, PostgreSQL 16/17, Docker Compose.

## Global Constraints

- Requirements: `GRAPH-004`, `GRAPH-006`, `GRAPH-007`, `GRAPH-009`, `GRAPH-010`, `CI-001..008`, `SEC-003..007`, and `OPS-001..008`.
- No GitHub-hosted runner is used for test, validation, build, scan, or promotion.
- PR code receives no host Docker socket, production route, production database, registry/release credential, OIDC write authority, deployment authority, or app-stack mount.
- Promotion and deployment are distinct manual phases; a green PR cannot deploy.
- A release binds one exact engine SHA, immutable artifact digests, dependency/config hashes, Claw receipts, SBOM/scan identities, previous rollback digest, and exact app-stack SHA.
- App-stack source is an authenticated exact archive with traversal/link checks and no persisted credential.
- The dirty `/home/operator/app-stack` checkout is never fetched, reset, cleaned, copied, mounted, or used as deployment source.
- Automatic push deploy is forbidden.
- Deployment targets only Compose project `mee-a2`; n8n and unrelated bots are never enumerated as mutation targets.
- No private API or live-trading capability is introduced or exercised.
- Every commit updates `handoff.md` and passes the changed-node graph/orphan gate.

---

### Task 1: Enforce the Claw workflow and sandbox contract

**Files:**

- Create: `tests/release/test_claw_workflow_policy.py`
- Create: `tests/release/test_same_repo_pr.py`
- Create: `tests/release/test_validation_receipt.py`
- Create: `tests/release/test_validation_cleanup_receipt.py`
- Create: `ci/claw/sandbox-policy.json`
- Create: `ci/claw/run-disposable-validation.sh`
- Create: `scripts/verify_same_repo_pr.py`
- Create: `scripts/verify_validation_receipt.py`
- Create: `scripts/write_validation_cleanup_receipt.py`
- Create: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `.github/workflows/verify-a2-pr-on-claw.yml`
- Modify: `architecture/runtime.yaml`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**

- Consumes: exact same-repository PR SHA and default-branch workflow definition.
- Produces: `validation-receipt-v1.json` containing repository, head SHA,
  controller/workflow identity, run/attempt/job IDs, sandbox policy hash,
  commands, results, and cleanup requirement; plus a separate
  `validation-cleanup-receipt-v1.json` written after cleanup with the exact
  pod/workspace cleanup outcome. Both hashes are required downstream.

- [ ] **Step 1: Write the failing workflow-policy test**

```python
from pathlib import Path
import yaml


WORKFLOWS = Path(".github/workflows")


def test_every_active_validation_job_is_claw_only_and_non_deploying() -> None:
    violations: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_id, job in (doc.get("jobs") or {}).items():
            runner = job.get("runs-on")
            if runner and runner != ["self-hosted", "claw"]:
                violations.append(f"{path}:{job_id}:runner={runner!r}")
            permissions = job.get("permissions", doc.get("permissions", {}))
            if permissions not in ({}, {"contents": "read"}):
                violations.append(f"{path}:{job_id}:permissions={permissions!r}")
            text = str(job).lower()
            if any(word in text for word in ("deploy", "promotion-token", "id-token: write")):
                violations.append(f"{path}:{job_id}:deploy-authority")
    assert not violations, "\n".join(violations)


def test_pr_validation_declares_disposable_rootless_boundary() -> None:
    policy = Path("ci/claw/sandbox-policy.json").read_text(encoding="utf-8")
    for required in (
        '"rootless": true',
        '"host_docker_socket": false',
        '"production_routes": false',
        '"release_credentials": false',
        '"deployment_authority": false',
    ):
        assert required in policy


def test_dispatch_verifies_open_same_repository_pr_head() -> None:
    workflow_text = Path(".github/workflows/validate-pr-on-claw.yml").read_text(encoding="utf-8")
    assert "/pulls/${PR_NUMBER}" in workflow_text
    assert "verify_same_repo_pr.py" in workflow_text
    assert "--expected-head-sha \"${TARGET_SHA}\"" in workflow_text
    assert "--require-open" in workflow_text
```

- [ ] **Step 2: Run RED on exact-SHA Claw validation**

Run:

```bash
python -B -m pytest tests/release/test_claw_workflow_policy.py -q
```

Expected: FAIL names the current hosted-runner workflow and missing sandbox policy.

- [ ] **Step 3: Add the fail-closed sandbox policy**

```json
{
  "schema": "mee.claw-sandbox.v1",
  "rootless": true,
  "host_docker_socket": false,
  "production_routes": false,
  "production_databases": false,
  "registry_credentials": false,
  "release_credentials": false,
  "deployment_authority": false,
  "app_stack_mount": false,
  "network_mode": "per-run-internal-only",
  "cleanup_required": true
}
```

- [ ] **Step 4: Implement sandbox preflight and execution**

Implement `verify_same_repo_pr.py` as a closed-schema check over the GitHub PR
response. It exits `1` unless all four values match exactly:

```python
def verify_pr(response: dict[str, object], repository: str, head_sha: str) -> None:
    if response.get("state") != "open":
        raise PRIdentityError("PR_NOT_OPEN")
    head = require_mapping(response, "head")
    base = require_mapping(response, "base")
    if require_mapping(head, "repo").get("full_name") != repository:
        raise PRIdentityError("FORK_HEAD_FORBIDDEN")
    if require_mapping(base, "repo").get("full_name") != repository:
        raise PRIdentityError("BASE_REPOSITORY_MISMATCH")
    if head.get("sha") != head_sha:
        raise PRIdentityError("PR_HEAD_SHA_MISMATCH")
```

Then implement sandbox preflight and execution:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${TARGET_SHA:?TARGET_SHA is required}"
: "${SOURCE_ROOT:?SOURCE_ROOT is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
: "${VALIDATION_IMAGE_REF:?immutable validation image reference is required}"
: "${RECEIPT_ROOT:?RECEIPT_ROOT is required}"
: "${CONTROLLER_ROOT:?CONTROLLER_ROOT is required}"
[[ "${VALIDATION_IMAGE_REF}" =~ @sha256:[0-9a-f]{64}$ ]]
command -v podman >/dev/null
test "$(podman info --format '{{.Host.Security.Rootless}}')" = "true"
test -z "${DOCKER_HOST:-}"

job_root="${RUNNER_TEMP}/mee-pr-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${GITHUB_JOB}"
container_name="mee-pr-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${GITHUB_JOB}"
receipt_path="${RECEIPT_ROOT}/validation-receipt-v1.json"
install -d -m 0700 "${job_root}/src" "${RECEIPT_ROOT}"
cleanup() {
  cleanup_status="success"
  if podman container exists "${container_name}"; then
    podman rm --force "${container_name}" >/dev/null 2>&1 || cleanup_status="failed"
  fi
  if podman container exists "${container_name}"; then
    cleanup_status="failed"
  fi
  rm -rf -- "${job_root}" || cleanup_status="failed"
  python "${CONTROLLER_ROOT}/scripts/write_validation_cleanup_receipt.py" \
    --status "${cleanup_status}" \
    --output "${RECEIPT_ROOT}/validation-cleanup-receipt-v1.json"
}
trap cleanup EXIT

test "$(git -C "${SOURCE_ROOT}" rev-parse HEAD)" = "${TARGET_SHA}"
podman run --rm \
  --name "${container_name}" \
  --network none \
  --read-only \
  --cap-drop all \
  --security-opt no-new-privileges \
  --userns keep-id \
  -v "${SOURCE_ROOT}:/src:ro,Z" \
  -v "${RECEIPT_ROOT}:/out:rw,Z" \
  "${VALIDATION_IMAGE_REF}" \
  /bin/sh -euc 'test ! -e /var/run/docker.sock; exec /opt/mee/validate-exact-source /src /out'
test -s "${receipt_path}"
```

The validator writes `validation-receipt-v1.json` atomically in `/out`. The
trusted controller then verifies its closed schema and exact repository,
target SHA, controller SHA/tree, workflow blob SHA, validation-image digest,
sandbox-policy hash, run/attempt/job IDs, command results, and cleanup intent.
The trap writes the separate cleanup receipt after attempting both pod and
workspace removal; any non-success cleanup receipt fails verification.
`job_root` cleanup never removes `RECEIPT_ROOT`; the workflow uploads both
verified receipts and removes the receipt directory only after upload.

The literal validation-image digest is replaced in the implementation commit
with the owner-reviewed digest recorded in `architecture/release.yaml`; a mutable
tag is rejected by the test.

- [ ] **Step 5: Replace the active hosted workflow with default-branch Claw dispatch**

The workflow must use:

```yaml
name: Validate exact PR SHA on Claw
on:
  repository_dispatch:
    types: [validate-exact-pr-sha]
permissions:
  contents: read
jobs:
  validate:
    runs-on: [self-hosted, claw]
    steps:
      - name: Materialize trusted default-branch controller
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: ${{ github.sha }}
          fetch-depth: 1
          path: trusted-controller
          persist-credentials: false
      - name: Bind trusted controller identity
        shell: bash
        run: |
          set -euo pipefail
          test "$(git -C trusted-controller rev-parse HEAD)" = "${GITHUB_SHA}"
          git -C trusted-controller rev-parse HEAD^{tree} > "${RUNNER_TEMP}/trusted-controller-tree"
      - name: Resolve and verify the open same-repository PR head
        shell: bash
        env:
          GITHUB_TOKEN: ${{ github.token }}
          EXPECTED_REPOSITORY: ${{ github.repository }}
          PR_NUMBER: ${{ github.event.client_payload.pr_number }}
          TARGET_SHA: ${{ github.event.client_payload.head_sha }}
        run: |
          set -euo pipefail
          [[ "${PR_NUMBER}" =~ ^[1-9][0-9]*$ ]]
          [[ "${TARGET_SHA}" =~ ^[0-9a-f]{40}$ ]]
          response="${RUNNER_TEMP}/pr-${PR_NUMBER}.json"
          curl --fail --silent --show-error \
            --header "Authorization: Bearer ${GITHUB_TOKEN}" \
            --header "Accept: application/vnd.github+json" \
            "https://api.github.com/repos/${EXPECTED_REPOSITORY}/pulls/${PR_NUMBER}" \
            --output "${response}"
          python trusted-controller/scripts/verify_same_repo_pr.py \
            --response "${response}" \
            --expected-repository "${EXPECTED_REPOSITORY}" \
            --expected-head-sha "${TARGET_SHA}" \
            --require-open
          rm -f -- "${response}"
          unset GITHUB_TOKEN
      - name: Materialize exact source without persisted credentials
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: ${{ github.event.client_payload.head_sha }}
          path: untrusted-src
          persist-credentials: false
      - name: Run disposable validation
        env:
          TARGET_SHA: ${{ github.event.client_payload.head_sha }}
          SOURCE_ROOT: ${{ github.workspace }}/untrusted-src
          RECEIPT_ROOT: ${{ runner.temp }}/mee-receipt-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.job }}
          CONTROLLER_ROOT: ${{ github.workspace }}/trusted-controller
        run: trusted-controller/ci/claw/run-disposable-validation.sh
      - name: Verify validation receipt
        env:
          TARGET_SHA: ${{ github.event.client_payload.head_sha }}
          RECEIPT_ROOT: ${{ runner.temp }}/mee-receipt-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.job }}
        run: |
          python trusted-controller/scripts/verify_validation_receipt.py \
            --receipt "${RECEIPT_ROOT}/validation-receipt-v1.json" \
            --repository "${GITHUB_REPOSITORY}" \
            --target-sha "${TARGET_SHA}" \
            --controller-sha "${GITHUB_SHA}" \
            --controller-tree "$(cat "${RUNNER_TEMP}/trusted-controller-tree")" \
            --cleanup-receipt "${RECEIPT_ROOT}/validation-cleanup-receipt-v1.json" \
            --require-cleanup-success
      - name: Upload verified validation receipt
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
        with:
          name: validation-receipt-${{ github.event.client_payload.head_sha }}
          path: |
            ${{ runner.temp }}/mee-receipt-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.job }}/validation-receipt-v1.json
            ${{ runner.temp }}/mee-receipt-${{ github.run_id }}-${{ github.run_attempt }}-${{ github.job }}/validation-cleanup-receipt-v1.json
          if-no-files-found: error
      - name: Remove receipt workspace
        if: always()
        run: rm -rf -- "${RUNNER_TEMP}/mee-receipt-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}-${GITHUB_JOB}"
```

The policy test rejects action version tags and requires full commit SHAs.

- [ ] **Step 6: Run GREEN and commit**

Run:

```bash
python -B -m pytest tests/release/test_claw_workflow_policy.py tests/release/test_same_repo_pr.py tests/release/test_validation_receipt.py tests/release/test_validation_cleanup_receipt.py -q
python scripts/check-architecture-graph.py --phase precommit --format text
```

Expected: PASS; graph output contains no changed workflow orphan or unauthorized capability.

```bash
git add tests/release/test_claw_workflow_policy.py tests/release/test_same_repo_pr.py tests/release/test_validation_receipt.py tests/release/test_validation_cleanup_receipt.py ci/claw/sandbox-policy.json \
  ci/claw/run-disposable-validation.sh .github/workflows/validate-pr-on-claw.yml \
  scripts/verify_same_repo_pr.py scripts/verify_validation_receipt.py scripts/write_validation_cleanup_receipt.py .github/workflows/verify-a2-pr-on-claw.yml \
  architecture/runtime.yaml architecture/release.yaml handoff.md
git commit -m "ci: isolate exact-SHA Claw PR validation"
```

### Task 2: Define and validate the connected release receipt

**Files:**

- Create: `schemas/release-receipt-v1.schema.json`
- Create: `schemas/engine-candidate-receipt-v1.schema.json`
- Create: `schemas/promotion-request-v1.schema.json`
- Create: `schemas/promotion-receipt-v1.schema.json`
- Create: `tools/release_graph/__init__.py`
- Create: `tools/release_graph/model.py`
- Create: `tools/release_graph/verify.py`
- Create: `scripts/verify-release-graph.py`
- Create: `tests/release/test_release_receipt.py`
- Create: `tests/fixtures/release/valid-v1.json`
- Create: `tests/fixtures/release/mixed-sha-v1.json`
- Create: `tests/fixtures/release/candidate-valid-v1.json`
- Create: `tests/fixtures/release/promotion-request-valid-v1.json`
- Create: `tests/fixtures/release/promotion-valid-v1.json`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**

- Consumes: exact source/config/manifest identities and phase receipts.
- Produces four non-circular immutable contracts: (1)
  `mee.stage-a.engine-candidate.v1` after validation/build/scan, (2)
  `mee.stage-a.promotion-request.v1` binding candidate plus exact app-stack/DB
  receipt and human release authorization, (3) `mee.stage-a.promotion.v1`
  emitted only after immutable promotion, and (4) the final
  `mee.stage-a.release.v1` root binding all three receipt hashes. Deployment
  consumes only the final release hash; promotion never consumes that future
  final hash.

- [ ] **Step 1: Write the failing receipt test**

```python
from dataclasses import replace
from pathlib import Path

import pytest

from tools.release_graph.model import ReleaseReceipt, load_candidate, load_release
from tools.release_graph.verify import ReleaseGraphError, verify_candidate, verify_release


def test_release_rejects_a_receipt_from_another_source_sha() -> None:
    valid_candidate = load_candidate(Path("tests/fixtures/release/candidate-valid-v1.json"))
    mismatched = replace(
        valid_candidate,
        validation=replace(valid_candidate.validation, source_sha="0" * 40),
    )
    with pytest.raises(ReleaseGraphError, match="SOURCE_SHA_MISMATCH"):
        verify_candidate(mismatched)


def test_release_requires_previous_rollback_digest() -> None:
    valid_candidate = load_candidate(Path("tests/fixtures/release/candidate-valid-v1.json"))
    missing = replace(valid_candidate, previous_capture_digest=None)
    with pytest.raises(ReleaseGraphError, match="ROLLBACK_DIGEST_MISSING"):
        verify_candidate(missing)


def test_final_release_requires_realized_promotion_receipt() -> None:
    valid_release = load_release(Path("tests/fixtures/release/valid-v1.json"))
    missing = replace(valid_release, promotion_receipt_sha256=None)
    with pytest.raises(ReleaseGraphError, match="PROMOTION_RECEIPT_MISSING"):
        verify_release(missing)
```

- [ ] **Step 2: Run RED**

Run: `python -B -m pytest tests/release/test_release_receipt.py -q`

Expected: FAIL because `tools.release_graph` does not exist.

- [ ] **Step 3: Implement immutable receipt identities**

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArtifactIdentity:
    name: str
    oci_digest: str
    source_sha: str
    revision_label: str
    wheel_record_sha256: str
    sbom_sha256: str
    vulnerability_report_sha256: str
    boundary_receipt_sha256: str
    syft_binary_sha256: str
    trivy_binary_sha256: str
    scan_policy_sha256: str


@dataclass(frozen=True, slots=True)
class ValidationIdentity:
    source_sha: str
    graph_receipt_sha256: str
    pg16_receipt_sha256: str
    pg17_receipt_sha256: str
    analysis_replay_receipt_sha256: str
    workflow_blob_sha: str
    sandbox_policy_sha256: str
    cleanup_receipt_sha256: str


@dataclass(frozen=True, slots=True)
class EngineCandidateReceipt:
    schema: str
    source_sha: str
    dependency_lock_sha256: str
    requirements_manifest_sha256: str
    runtime_manifest_sha256: str
    data_contract_manifest_sha256: str
    strategy_manifest_sha256: str
    configuration_sha256: str
    mapping_sha256: str
    validation: ValidationIdentity
    capture: ArtifactIdentity
    analyzer: ArtifactIdentity
    previous_capture_digest: str
    previous_analyzer_digest: str
    build_workflow_blob_sha: str


@dataclass(frozen=True, slots=True)
class PromotionRequest:
    schema: str
    candidate_receipt_sha256: str
    app_stack_sha: str
    app_stack_db_contract_receipt_sha256: str
    reviewer_receipt_sha256: str
    release_workflow_blob_sha: str
    human_release_authorization_id: str


@dataclass(frozen=True, slots=True)
class PromotionReceipt:
    schema: str
    promotion_request_sha256: str
    capture_promoted_reference: str
    analyzer_promoted_reference: str
    capture_oci_digest: str
    analyzer_oci_digest: str
    previous_capture_digest: str
    previous_analyzer_digest: str
    registry_identity_sha256: str
    workflow_run_identity_sha256: str


@dataclass(frozen=True, slots=True)
class ReleaseReceipt:
    schema: str
    candidate_receipt_sha256: str
    promotion_request_sha256: str
    promotion_receipt_sha256: str
    app_stack_sha: str
    app_stack_db_contract_receipt_sha256: str
    capture_oci_digest: str
    analyzer_oci_digest: str
    reviewer_receipt_sha256: str


def load_candidate(path: Path) -> EngineCandidateReceipt: ...
def load_release(path: Path) -> ReleaseReceipt: ...
```

`verify_candidate()`, `verify_promotion_request()`, `verify_promotion()`, and
`verify_release()` validate the referenced closure rather than repairing it.
They validate exact equality of every embedded source SHA,
well-formed `sha256:<64 hex>` OCI digests, 64-hex receipt hashes, distinct
capture/analyzer artifacts, required rollback digests, and the exact app-stack
DB-contract receipt. Promotion references must equal the artifact name plus
the candidate OCI digest. Candidate binds Syft/Trivy binary hashes and scan
policy; promotion request binds the release-workflow blob and authorization;
final release binds the realized promotion receipt. No verifier accepts a
future or missing receipt.

- [ ] **Step 4: Run GREEN and negative fixtures**

Run:

```bash
python -B -m pytest tests/release/test_release_receipt.py -q
python scripts/verify-release-graph.py --candidate tests/fixtures/release/candidate-valid-v1.json
python scripts/verify-release-graph.py --promotion-request tests/fixtures/release/promotion-request-valid-v1.json
python scripts/verify-release-graph.py --promotion tests/fixtures/release/promotion-valid-v1.json
python scripts/verify-release-graph.py tests/fixtures/release/valid-v1.json
! python scripts/verify-release-graph.py tests/fixtures/release/mixed-sha-v1.json
```

Expected: tests and the complete candidate/request/promotion/final closure PASS;
mixed-SHA fixture exits `1` with `SOURCE_SHA_MISMATCH`.

- [ ] **Step 5: Commit**

```bash
git add schemas/release-receipt-v1.schema.json schemas/engine-candidate-receipt-v1.schema.json \
  schemas/promotion-request-v1.schema.json schemas/promotion-receipt-v1.schema.json tools/release_graph \
  scripts/verify-release-graph.py tests/release/test_release_receipt.py \
  tests/fixtures/release architecture/release.yaml handoff.md
git commit -m "release: define connected Stage A receipt"
```

### Task 3: Build and scan exact candidates and implement non-circular promotion

**Files:**

- Create: `.github/workflows/release-stage-a-on-claw.yml`
- Create: `ci/claw/build-stage-a-release.sh`
- Create: `ci/claw/promote-stage-a-release.sh`
- Create: `scripts/finalize-stage-a-release.py`
- Create: `tests/release/test_release_workflow.py`
- Modify: `scripts/check-stage-a-artifacts.py`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**

- Consumes: exact SHA validation plus cleanup receipts and M3/M4/M5 receipts.
- Produces during its build phase: the immutable engine-candidate receipt with
  capture/analyzer OCI digests, SBOM/vulnerability/boundary/scanner identities,
  and previous rollback digests. It also implements the separately invoked
  promotion path that later consumes a verified promotion request and emits a
  realized promotion receipt. It does not claim a final release receipt before
  app-stack validation and promotion exist.

- [ ] **Step 1: Write failing workflow tests**

```python
def test_release_workflow_is_manual_main_only_and_exact_sha() -> None:
    workflow_text = Path(".github/workflows/release-stage-a-on-claw.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in workflow_text
    assert "push:" not in workflow_text
    assert "pull_request:" not in workflow_text
    assert "runs-on: [self-hosted, claw]" in workflow_text
    assert "verify-release-graph.py" in workflow_text
    assert "promote-stage-a-release.sh" in workflow_text
    assert "${{ github.sha }}" in workflow_text
    assert "DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}" in workflow_text
    assert 'refs/heads/${DEFAULT_BRANCH}' in workflow_text
```

- [ ] **Step 2: Run RED**

Run: `python -B -m pytest tests/release/test_release_workflow.py -q`

Expected: FAIL because the release workflow is absent.

- [ ] **Step 3: Implement exact artifact build and inspection**

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${SOURCE_SHA:?SOURCE_SHA required}"
: "${RUNNER_TEMP:?RUNNER_TEMP required}"
test "$(git rev-parse HEAD)" = "${SOURCE_SHA}"

out="${RUNNER_TEMP}/mee-release-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
install -d -m 0700 "${out}"
python scripts/build-stage-a-distributions.py --source-sha "${SOURCE_SHA}" --out "${out}/dist"
docker build --pull=false --network=none \
  --label "org.opencontainers.image.revision=${SOURCE_SHA}" \
  -f deploy/images/Dockerfile.public-capture \
  -t "mee-public-capture:${SOURCE_SHA}" .
docker build --pull=false --network=none \
  --label "org.opencontainers.image.revision=${SOURCE_SHA}" \
  -f deploy/images/Dockerfile.readonly-analyzer \
  -t "mee-readonly-analyzer:${SOURCE_SHA}" .
python scripts/check-stage-a-artifacts.py \
  --image "mee-public-capture:${SOURCE_SHA}" \
  --image "mee-readonly-analyzer:${SOURCE_SHA}" \
  --receipt "${out}/artifact-boundary.json"
syft "mee-public-capture:${SOURCE_SHA}" -o cyclonedx-json="${out}/capture.sbom.json"
syft "mee-readonly-analyzer:${SOURCE_SHA}" -o cyclonedx-json="${out}/analyzer.sbom.json"
trivy image --exit-code 1 --severity CRITICAL,HIGH \
  --format json --output "${out}/capture.trivy.json" "mee-public-capture:${SOURCE_SHA}"
trivy image --exit-code 1 --severity CRITICAL,HIGH \
  --format json --output "${out}/analyzer.trivy.json" "mee-readonly-analyzer:${SOURCE_SHA}"
```

The workflow pins Syft, Trivy, build image, base images, and actions by reviewed
digest/full commit SHA. It records those identities in the candidate receipt.
Its first trusted step asserts `GITHUB_REF` equals
`refs/heads/${DEFAULT_BRANCH}`; dispatch from any other ref fails.

- [ ] **Step 4: Implement fail-closed immutable promotion**

`promote-stage-a-release.sh` must verify the candidate receipt and promotion
request first, prove that the request binds the exact app-stack SHA/DB-contract
receipt plus human release authorization, resolve the two image IDs/digests,
record the currently promoted digests as rollback inputs, and update promotion
references by immutable digest. It atomically emits
`promotion-receipt-v1.json`. A separate finalization command then creates and
verifies `release-receipt-v1.json` from candidate, request, and realized
promotion hashes. If the local registry does not expose immutable digests,
promotion exits nonzero instead of treating a mutable `candidate` tag as a
release.

- [ ] **Step 5: Run GREEN on Claw**

Run:

```bash
python -B -m pytest tests/release/test_release_workflow.py tests/release/test_release_receipt.py -q
python scripts/check-architecture-graph.py --phase release-candidate --format text
python scripts/verify-release-graph.py --candidate "${RUNNER_TEMP}/mee-release-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}/engine-candidate.json"
```

Expected: PASS for one exact SHA candidate and promotion/finalization contract
tests; no registry mutation occurs in this PR gate. Any mixed receipt, mutable
artifact reference, unscanned image, absent rollback digest, or missing
AnalysisRun replay receipt fails.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/release-stage-a-on-claw.yml ci/claw/build-stage-a-release.sh \
  ci/claw/promote-stage-a-release.sh tests/release/test_release_workflow.py \
  scripts/finalize-stage-a-release.py scripts/check-stage-a-artifacts.py architecture/release.yaml handoff.md
git commit -m "release: build candidates and gate immutable promotion"
```

### Task 4: Validate app-stack bootstrap and exact archive materialization

**Repository scope:** `Dimkox/openclaw-airgap-farm` in a fresh isolated worktree; never `/home/operator/app-stack`.

**Owner:** app-stack DevOps/SRE implementer. **Independent verifier:** security/release reviewer who did not author the workflow or archive verifier. **Handoff output:** exact app-stack PR head, archive member-verification receipt, credential-persistence denial receipt, and a separate no-push-trigger diff receipt.

**Files:**

- Modify: `.github/workflows/validate-pr-on-claw.yml`
- Modify: `.github/workflows/deploy.yml`
- Create: `scripts/materialize-exact-archive.sh`
- Create: `scripts/verify_archive_members.py`
- Create: `tests/test_exact_archive_contract.py`
- Create: `tests/test_archive_members.py`
- Modify: `handoff.md`

**Interfaces:**

- Consumes: app-stack PR #42 head `27860091fc01e61b00707cf178fbdc06250af7d7`, PR #39 head `d733925d1371286ffff45e3ffffb9997220dcae3`, and independently fetched current origin metadata.
- Produces: exact-head validation receipts, deterministic dependency/ancestry decision, no-push deploy workflow, and authenticated archive receipt without persisted credentials.

- [ ] **Step 1: Fetch current PR metadata read-only in an isolated app-stack checkout**

Run through the trusted repository API/tooling, never `/home/operator/app-stack`:

```bash
test "$(git remote get-url origin)" = "https://github.com/Dimkox/openclaw-airgap-farm.git"
git status --porcelain
```

Expected: isolated checkout is clean. Record current main, PR heads, base SHAs,
mergeability, workflow identities, and ancestry as evidence; any drift from the
audited SHAs creates a conflict node and stops this task.

- [ ] **Step 2: Write failing archive-contract tests**

```python
def test_private_archive_uses_step_scoped_token_and_never_git_credentials(script: str) -> None:
    assert "Authorization: Bearer ${GITHUB_TOKEN}" in script
    assert "git clone" not in script
    assert "git credential" not in script
    assert "http.extraheader" not in script
    assert "archive traversal" in script
    assert "symbolic link" in script
```

- [ ] **Step 3: Implement authenticated exact archive materialization**

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${EXPECTED_HEAD_SHA:?EXPECTED_HEAD_SHA required}"
: "${GITHUB_TOKEN:?GITHUB_TOKEN required}"
[[ "${EXPECTED_HEAD_SHA}" =~ ^[0-9a-f]{40}$ ]]
archive="${RUNNER_TEMP}/app-stack-${EXPECTED_HEAD_SHA}.tar.gz"
dest="${RUNNER_TEMP}/app-stack-${EXPECTED_HEAD_SHA}"
curl --fail --silent --show-error --location \
  --header "Authorization: Bearer ${GITHUB_TOKEN}" \
  --header "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/Dimkox/openclaw-airgap-farm/tarball/${EXPECTED_HEAD_SHA}" \
  --output "${archive}"
python scripts/verify_archive_members.py \
  --archive "${archive}" --reject-traversal --reject-links
install -d -m 0700 "${dest}"
tar --extract --gzip --file "${archive}" --directory "${dest}" --strip-components=1
unset GITHUB_TOKEN
test "$(git -C "${dest}" rev-parse --is-inside-work-tree 2>/dev/null || true)" != "true"
```

- [ ] **Step 4: Validate PR #42 before using it to bootstrap PR #39**

The default-branch trusted workflow must independently execute the archive
contract tests against exact PR #42. Only after that receipt may #42 merge.
Redispatch PR #39 against the repaired default-branch workflow, validate its
exact head, then merge #39 only if it removes automatic push deployment without
weakening manual `mee-a2` controls.

- [ ] **Step 5: Commit app-stack changes through their own reviewed PRs**

Commit #42-equivalent material separately from #39-equivalent material. Do not
combine bootstrap authentication and deployment-trigger semantics into one
unreviewable conflict resolution.

```bash
git add .github/workflows/validate-pr-on-claw.yml scripts/materialize-exact-archive.sh \
  scripts/verify_archive_members.py tests/test_exact_archive_contract.py \
  tests/test_archive_members.py handoff.md
git commit -m "ci(claw): materialize exact authenticated app archive"

git add .github/workflows/deploy.yml handoff.md
git commit -m "ci: remove automatic push deployment"
```

Expected: two reviewable commits and two verifier handoffs. The second commit
cannot merge until the first commit's exact-head Claw receipt is attached.

### Task 5: Prove the app-stack DB contract and mee-a2-only deployment boundary

**Repository scope:** `Dimkox/openclaw-airgap-farm` in a fresh isolated worktree; the dirty production checkout remains untouched.

**Owner:** app-stack deployment engineer. **Independent verifier:** PostgreSQL/SRE reviewer who did not author the bootstrap or deploy scripts. **Handoff output:** table-partition regression receipt, immutable-release denial receipt, planned-resource closure, full-minute evidence schema, and exact rollback contract.

**Files:**

- Modify: `scripts/a2_db_bootstrap.sh`
- Create: `scripts/verify_mee_a2_release.py`
- Create: `scripts/deploy-mee-a2.sh`
- Create: `scripts/rollback-mee-a2.sh`
- Create: `scripts/capture-mee-a2-evidence.py`
- Modify: `compose.mee-a2.yaml`
- Create: `tests/test_a2_db_partition_contract.py`
- Create: `tests/test_mee_a2_release_contract.py`
- Create: `tests/test_mee_a2_scripts_contract.py`
- Create: `tests/test_mee_a2_workflow_contract.py`
- Create: `tests/test_mee_a2_compose_contract.py`
- Create: `tests/test_mee_a2_rollback_contract.py`
- Create: `tests/fixtures/deploy-request-valid.json`
- Modify: `.github/workflows/deploy-a2.yml`
- Modify: `handoff.md`

**Interfaces:**

- Consumes while validating the contract: exact app-stack SHA containing
  `3ce7e1f33ad34663b123c9b1cb225be8767e97cf` or a reviewed equivalent plus an
  engine-candidate fixture. At realized deployment it consumes only the final
  release receipt created after app-stack DB validation and promotion, a
  distinct deployment authorization ID, and the previous rollback receipt.
- Produces: preflight, deployment, observation, or rollback receipt for Compose project `mee-a2` only.

- [ ] **Step 1: Write the failing partition regression**

```python
def test_partition_scan_targets_table_partitions_only(bootstrap_script: str) -> None:
    scans = [line for line in bootstrap_script.splitlines() if "relispartition" in line]
    assert len(scans) == 3
    assert all("relkind = 'r'" in line or 'relkind=\'r\'' in line for line in scans)
```

Run: `python -B -m pytest tests/test_a2_db_partition_contract.py -q`

Expected before the exact fix/equivalent: FAIL on index partitions. Expected after: PASS.

- [ ] **Step 2: Write release-consumer denial tests**

```python
import copy
import json
from pathlib import Path

from scripts.verify_mee_a2_release import verify_request


def load_valid_request() -> dict:
    return json.loads(Path("tests/fixtures/deploy-request-valid.json").read_text(encoding="utf-8"))


def test_deploy_rejects_mutable_image_reference() -> None:
    request = copy.deepcopy(load_valid_request())
    request["capture_digest"] = "mee-public-capture:candidate"
    assert verify_request(request).code == "IMMUTABLE_DIGEST_REQUIRED"


def test_deploy_rejects_non_mee_a2_service() -> None:
    request = copy.deepcopy(load_valid_request())
    request["compose_services"] = ["a2-collector", "n8n"]
    assert verify_request(request).code == "FOREIGN_SERVICE_FORBIDDEN"
```

Add executable/static contract tests that also prove:

- `deploy-a2.yml` is manual-only, validates the authorization and exact release
  receipt before mutation, and has no push trigger;
- `compose.mee-a2.yaml` resolves only resources labelled for project `mee-a2`
  and the deployment command names only `a2-collector`;
- deploy, capture, and rollback scripts never reference `/home/operator/app-stack`,
  n8n, broad `compose down`, mutable tags, or an unverified digest;
- every post-start failure invokes the exact rollback request and the rollback
  test verifies prior digests plus backward schema readability;
- evidence capture rejects a partial UTC minute, wrong run identity, zero
  expected/reporting/valid slots, absent current-run rows, and changed semantic
  image/config identity;
- retry is idempotent and sealed CaptureRun/AnalysisRun evidence is unchanged.

- [ ] **Step 3: Implement fail-closed preflight**

`verify_mee_a2_release.py` verifies engine/app exact SHAs, release receipt hash,
two OCI digests, config/mapping hashes, approved run ID, registry receipt, clock
evidence, DB-contract receipt, previous rollback digest, and authorization ID.
It emits canonical planned resources and rejects every service, network, volume,
or container not labeled for project `mee-a2`.

- [ ] **Step 4: Implement narrow deploy and evidence capture**

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${DEPLOY_REQUEST:?DEPLOY_REQUEST required}"
python scripts/verify_mee_a2_release.py "${DEPLOY_REQUEST}"
docker compose -p mee-a2 -f compose.mee-a2.yaml config --quiet
docker compose -p mee-a2 -f compose.mee-a2.yaml up --detach --no-build a2-collector
python scripts/capture-mee-a2-evidence.py \
  --project mee-a2 \
  --require-health \
  --require-ready \
  --require-full-utc-minute \
  --require-current-run-postgres \
  --output "${RUNNER_TEMP}/mee-a2-deployment-receipt.json"
```

If any post-start gate fails, the workflow invokes the exact rollback request;
it never runs broad `compose down`, mutates another project, or rewrites evidence.

- [ ] **Step 5: Implement exact rollback**

Rollback verifies prior capture/analyzer digests and configuration from the
release graph, checks schema backward readability, changes only `mee-a2`, keeps
sealed CaptureRuns untouched, and records a new rollback receipt. Analyzer
rollback produces a new AnalysisRun over the same verified frozen package.

- [ ] **Step 6: Run contract GREEN on Claw and commit**

Run:

```bash
python -B -m pytest tests/test_a2_db_partition_contract.py \
  tests/test_mee_a2_release_contract.py tests/test_mee_a2_scripts_contract.py \
  tests/test_mee_a2_workflow_contract.py tests/test_mee_a2_compose_contract.py \
  tests/test_mee_a2_rollback_contract.py -q
actionlint
shellcheck scripts/a2_db_bootstrap.sh scripts/deploy-mee-a2.sh scripts/rollback-mee-a2.sh
```

Expected: PASS in an isolated non-production test project. No deploy command is
executed by PR validation.

```bash
git add scripts/a2_db_bootstrap.sh scripts/verify_mee_a2_release.py \
  scripts/deploy-mee-a2.sh scripts/rollback-mee-a2.sh \
  scripts/capture-mee-a2-evidence.py compose.mee-a2.yaml \
  tests/test_a2_db_partition_contract.py tests/test_mee_a2_release_contract.py \
  tests/test_mee_a2_scripts_contract.py tests/test_mee_a2_workflow_contract.py \
  tests/test_mee_a2_compose_contract.py tests/test_mee_a2_rollback_contract.py \
  tests/fixtures/deploy-request-valid.json \
  .github/workflows/deploy-a2.yml handoff.md
git commit -m "deploy: enforce exact mee-a2 release graph"
```

Expected: one app-stack commit whose independent handoff names the exact test
project, PostgreSQL contract receipt, changed-resource set, and rollback digest.

## Manual Release/Deployment Execution Checklist

**Files:**

- Evidence only: immutable Claw validation, release, promotion, deployment, observation, and rollback receipts.

**Interfaces:**

- Consumes: all earlier exact-SHA receipts plus explicit human deployment authorization.
- Produces: realized release/deployment graph or a typed blocker without widening scope.

- [ ] **Step 1: Validate exact engine SHA on Claw**

Expected: graph, installed distributions, PG16/17, deterministic AnalysisRun
replay, quarantine, capability, and negative tests all pass for one SHA.

- [ ] **Step 2: Build and scan exact immutable candidates**

Expected: candidate verifier accepts both artifact digests, scan/SBOM/boundary
identities, validation/cleanup receipts, and previous rollback digests. No
promotion or final release is claimed yet.

- [ ] **Step 3: Validate exact app-stack SHA and DB contract**

Expected: app-stack receipt proves no automatic push deploy, exact archive
materialization, DB-contract equivalence, and `mee-a2`-only mutation scope.

- [ ] **Step 4: Authorize, promote, and finalize the connected release**

Expected: a named human release authorization creates a promotion request that
binds the candidate and app-stack receipt. Immutable promotion emits its own
receipt. `finalize-stage-a-release.py` then verifies the complete closure and
emits the final release receipt; neither request nor candidate is accepted as a
deployment input.

- [ ] **Step 5: Deploy only after a distinct named deployment approval**

Expected: only `mee-a2` resources change; `/home/operator/app-stack`, n8n, other
bots, private APIs, and live trading remain untouched.

- [ ] **Step 6: Capture a full UTC minute and current-run PostgreSQL evidence**

Expected: health/readiness are necessary but insufficient; receipt also records
nonzero expected/reporting/valid slots, semantic run/config/image identity,
current-run rows after a full UTC minute, and sustained soak state.

- [ ] **Step 7: Append deployment evidence or execute exact rollback**

Expected: successful evidence closes the release graph. Any mismatch triggers
the predeclared `mee-a2` rollback and records its receipt without rewriting raw
or analysis evidence.
