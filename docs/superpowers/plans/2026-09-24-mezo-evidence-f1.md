# Liqvera Mezo Evidence F1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Make the Stage A baseline reproducible from a clean public clone, lock and probe the approved Hyperliquid/Mezo Testnet compatibility boundary, and accept the narrow runtime-boundary ADR without implementing payment or report delivery.

**Architecture:** F1 repairs public verification and records compatibility evidence. Existing analytical packages remain behaviorally unchanged; a stdlib-only probe checks fixed public endpoints and emits a sanitized result. No gateway, database, wallet, payment signature, report schema, or UI is introduced.

**Tech Stack:** Python 3.12, pytest, PyYAML, Ruff, hatchling 1.32.4, Git, JSON-RPC, Hyperliquid public Info API, Mezo Testnet RPC, Vativ x402 facilitator, npm registry metadata.

**Spec:** docs/superpowers/specs/2026-09-24-mezo-evidence-design.md

## Global Constraints

- Preserve Stage A INSUFFICIENT_EVIDENCE; never add or infer GO.
- Preserve the shadow-only, read-only, credential-free exchange boundary.
- Permit only Mezo Testnet eip155:31611; reject mainnet eip155:31612.
- Use MUSD 0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503 with 18 decimals.
- Use x402 v2 exact and one exact @x402/* family, initially 2.16.0.
- Do not install x402 packages, create a gateway, request a wallet key, or transfer value in F1.
- Use only fixed allowlisted URLs; accept no user-supplied URL, redirect, request body, or token address.
- Do not supply, persist, or default `PAY_TO` in F1; record `PAY_TO_MISSING` until an operator provides a non-zero merchant address through the future runtime environment.
- Do not invent a block-confirmation count: the reviewed Mezo material confirms that the facilitator waits for blockchain confirmation but does not establish the canonical finality rule required by this project, so record `FINALITY_RULE_UNVERIFIED`.
- Do not commit .venv, .env, transient prices, credentials, signatures, or capabilities.
- Keep missing private Git history explicit; target integrity is not source-byte verification.
- Update handoff.md in every commit that materially changes F1 state.

## Review Focus

- A public clone without private Git objects verifies pinned imported targets, while --require-source-objects fails closed.
- A changed imported target fails even when private source objects are unavailable.
- Wrong Mezo chain, MUSD code/decimals, facilitator asset support, or SDK version produces a sanitized failure.
- Malformed Hyperliquid data, missing BTC, or more than 20 levels per side fails closed.
- Missing `PAY_TO` and an unverified finality rule remain explicit payment-readiness blockers without failing the independent read-only compatibility probe.

---

### Task 1: Close the public publication inventory

**Files:**

- Modify: tests/graph/test_third_final_review_policy.py
- Modify: tools/graph_checker/loader.py
- Modify: architecture/architecture.yaml
- Modify: handoff.md

**Interfaces:**

- Consumes: _classify_repository_path(path: str) -> PathClass and repository_inventory.
- Produces: DOCUMENTATION classification for provenance/ and one active authority for every F0 publication file.

- [ ] **Step 1: Write the failing classifier and inventory tests**

Add this classifier case:

~~~python
(
    "provenance/import-manifest.json",
    PathClass.DOCUMENTATION,
),
~~~

Add this test:

~~~python
@pytest.mark.parametrize(
    "path",
    (
        "PROVENANCE.md",
        "docs/planning/LIQVERA_FACTORY_TZ.md",
        "docs/planning/MEE_MEZO_EVIDENCE_FACTORY_TZ.md",
        "provenance/import-manifest.json",
    ),
)
def test_liqvera_publication_files_have_document_authority(path: str) -> None:
    graph = load_graph(Path("architecture"))
    binding = next(item for item in graph.artifact_bindings if item.path == path)

    assert binding.path_class is PathClass.DOCUMENTATION
    assert binding.node_id == "document:graph-authority-handoff"
    authority = graph.node(binding.node_id)
    assert authority.kind == "ADR" and authority.active
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -B -m pytest \
  tests/graph/test_third_final_review_policy.py::test_repository_classifier_is_prefix_registry_not_extension_allowlist \
  tests/graph/test_third_final_review_policy.py::test_liqvera_publication_files_have_document_authority -q
~~~

Expected: FAIL because provenance/import-manifest.json is UNKNOWN_TRACKED and the four bindings are missing.

- [ ] **Step 3: Add the minimal path rule**

~~~python
if normalized.startswith(
    ("docs/", "engineering/changes/", "provenance/")
) or ("/" not in normalized and name.endswith(".md")):
    return PathClass.DOCUMENTATION
~~~

- [ ] **Step 4: Bind the publication files**

Add each exact path once to repository_inventory.bindings with node document:graph-authority-handoff and path_class DOCUMENTATION.

- [ ] **Step 5: Run GREEN**

~~~bash
python3 -B -m pytest \
  tests/graph/test_third_final_review_policy.py::test_repository_classifier_is_prefix_registry_not_extension_allowlist \
  tests/graph/test_third_final_review_policy.py::test_liqvera_publication_files_have_document_authority \
  tests/graph/test_repository_manifests_cli.py -q
python3 -B scripts/check-architecture-graph.py \
  --manifest-root architecture --phase precommit --allow-declared-conflicts
~~~

Expected: PASS. Declared conflict lines may print, but no repository inventory diagnostic remains.

- [ ] **Step 6: Update handoff and commit**

Record that publication inventory is repaired while salvage and toolchain remain open.

~~~bash
git add architecture/architecture.yaml tools/graph_checker/loader.py \
  tests/graph/test_third_final_review_policy.py handoff.md
git diff --cached --check
git commit -m "fix(graph): classify Liqvera publication provenance"
~~~

### Task 2: Make salvage verification honest and public-clone reproducible

**Files:**

- Modify: architecture/salvage/pr21.yaml
- Modify: architecture/schemas/salvage.schema.json
- Modify: scripts/verify-pr21-salvage.py
- Modify: tests/readonly_analyzer/test_frozen_package_tamper.py
- Modify: handoff.md

**Interfaces:**

- Consumes: source_head, source_blob_sha, target, target_sha256, and rule.
- Produces: CLI options --manifest, --repository-root, and --require-source-objects; target verification always runs.

- [ ] **Step 1: Write failing digest assertions**

Add hashlib and subprocess imports, ROOT, VERIFY_SALVAGE, and:

~~~python
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
~~~

Extend the existing manifest test:

~~~python
assert all(len(row["target_sha256"]) == 64 for row in items)
assert all(_sha256(Path(row["target"])) == row["target_sha256"] for row in items)
~~~

- [ ] **Step 2: Write failing public, tamper, and strict-source tests**

Create a helper that writes packages/readonly-analyzer/src/example.py plus a one-row manifest using SOURCE_HEAD, a 40-character source_blob_sha, the computed target_sha256, and a non-empty rule.

Invoke the real script with subprocess in three tests:

~~~python
def test_public_salvage_verifies_targets_without_private_git_objects(tmp_path):
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode == 0
    assert "targets=verified" in completed.stdout
    assert "source_objects=unavailable" in completed.stdout


def test_public_salvage_rejects_changed_target(tmp_path):
    manifest, target = _write_public_salvage_fixture(tmp_path)
    target.write_bytes(b"tampered\n")
    completed = _run_salvage(manifest, tmp_path)
    assert completed.returncode != 0
    assert "target sha256 mismatch" in completed.stderr


def test_private_salvage_mode_requires_source_objects(tmp_path):
    manifest, _ = _write_public_salvage_fixture(tmp_path)
    completed = _run_salvage(manifest, tmp_path, "--require-source-objects")
    assert completed.returncode != 0
    assert "required source objects are unavailable" in completed.stderr
~~~

_run_salvage must execute python3, VERIFY_SALVAGE, --manifest, --repository-root, and any extra arguments without mocks.

- [ ] **Step 3: Run RED**

~~~bash
python3 -B -m pytest tests/readonly_analyzer/test_frozen_package_tamper.py -q
~~~

Expected: FAIL because target_sha256 and the public-mode CLI do not exist.

- [ ] **Step 4: Pin target digests and close the schema**

Use these exact target digests:

~~~text
types.py  d6db15994e498592b7d9d32ea8cb54c0c3b49938d6ebbfa43413ffb84a5f285e
codec.py  f0260a892d62863dcd4ea491dab9f8ff7b12137056d041bfa76643280950466e
reader.py 4f5dc1182a05310b5f7db7a25b33218e707c65e59cd4c0c16ddea128d260299d
~~~

Both rows targeting reader.py use the same digest. Require target_sha256 in the JSON schema with pattern ^[0-9a-f]{64}$.

- [ ] **Step 5: Implement dual-boundary verification**

Add:

~~~python
def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_objects_available(repository_root: Path, commit: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"{commit}^{{commit}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0
~~~

Add --repository-root with default "." and --require-source-objects. Verify target existence and SHA-256 before source checks. Validate source blobs only when source objects exist. Missing objects plus strict mode exits with required source objects are unavailable; public mode prints targets=verified source_objects=unavailable.

- [ ] **Step 6: Run GREEN**

~~~bash
python3 -B -m pytest tests/readonly_analyzer/test_frozen_package_tamper.py -q
python3 scripts/verify-pr21-salvage.py --manifest architecture/salvage/pr21.yaml
make salvage
~~~

Expected: PASS with four verified rows and no private source claim.

- [ ] **Step 7: Update handoff and commit**

~~~bash
git add architecture/salvage/pr21.yaml architecture/schemas/salvage.schema.json \
  scripts/verify-pr21-salvage.py \
  tests/readonly_analyzer/test_frozen_package_tamper.py handoff.md
git diff --cached --check
git commit -m "fix(provenance): verify public salvage targets"
~~~

### Task 3: Complete the documented development toolchain

**Files:**

- Modify: pyproject.toml
- Modify: .gitignore
- Create: tests/installed/test_root_development_toolchain.py
- Modify: architecture/architecture.yaml
- Modify: handoff.md

**Interfaces:**

- Consumes: root build-system.requires and project.optional-dependencies.dev.
- Produces: a dev extra containing the exact build runner; .venv/ remains untracked.

- [ ] **Step 1: Write the failing synchronization test**

~~~python
from __future__ import annotations

import tomllib
from pathlib import Path


def test_dev_extra_contains_the_exact_root_build_backend() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    build_requirements = set(metadata["build-system"]["requires"])
    dev_requirements = set(metadata["project"]["optional-dependencies"]["dev"])

    assert "hatchling==1.32.4" in build_requirements
    assert build_requirements <= dev_requirements
~~~

- [ ] **Step 2: Run RED**

~~~bash
python3 -B -m pytest tests/installed/test_root_development_toolchain.py -q
~~~

Expected: FAIL because the dev extra omits hatchling.

- [ ] **Step 3: Add the minimal dependency and inventory entry**

Add hatchling==1.32.4 to the dev list, .venv/ to .gitignore, and bind the new test to test:runtime-boundaries as TEST_SOURCE.

- [ ] **Step 4: Run GREEN**

~~~bash
python3 -B -m pytest tests/installed/test_root_development_toolchain.py -q
python3 -B -m ruff check tests/installed/test_root_development_toolchain.py
~~~

- [ ] **Step 5: Build the ignored clean environment**

~~~bash
python3 -m venv .venv
.venv/bin/python -m pip install --disable-pip-version-check -e '.[dev]'
.venv/bin/python -m hatchling --version
git status --short
~~~

Expected: hatchling 1.32.4; .venv is absent from status.

- [ ] **Step 6: Run the baseline in the pinned environment**

~~~bash
PATH="$PWD/.venv/bin:$PATH" make verify
~~~

Expected: PASS after Tasks 1 and 2, without the ambient pytest configuration warnings.

- [ ] **Step 7: Update handoff and commit**

~~~bash
git add pyproject.toml .gitignore tests/installed/test_root_development_toolchain.py \
  architecture/architecture.yaml handoff.md
git diff --cached --check
git commit -m "build: complete the Stage A development toolchain"
~~~

### Task 4: Add the sanitized Mezo compatibility lock and probe

**Files:**

- Create: docs/compatibility/mezo-evidence-v1.json
- Create: tools/mezo_compatibility.py
- Create: scripts/check-mezo-compatibility.py
- Create: tests/compatibility/test_mezo_compatibility.py
- Create during verification: engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json
- Modify: pyproject.toml
- Modify: architecture/architecture.yaml
- Modify: handoff.md

**Interfaces:**

- Consumes: fixed compatibility JSON and fixed public services.
- Produces: verify_observations(lock: dict, observations: dict) -> dict[str, object] and a CLI that emits sanitized JSON.

- [ ] **Step 1: Create the lock and failing tests**

The lock contains exactly:

~~~json
{
  "schema": "liqvera-mezo-compatibility/v1",
  "hyperliquid": {
    "info_url": "https://api.hyperliquid.xyz/info",
    "coin": "BTC",
    "maximum_levels_per_side": 20
  },
  "mezo": {
    "network": "eip155:31611",
    "chain_id": 31611,
    "rpc_url": "https://rpc.test.mezo.org",
    "musd_address": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
    "musd_decimals": 18,
    "facilitator_url": "https://facilitator.vativ.io"
  },
  "x402": {
    "version": 2,
    "scheme": "exact",
    "typescript_version": "2.16.0",
    "packages": ["@x402/core", "@x402/evm", "@x402/express", "@x402/paywall"]
  },
  "payment_readiness": {
    "pay_to_required": true,
    "pay_to_source": "operator_environment",
    "default_pay_to_forbidden": true,
    "finality_policy_status": "UNVERIFIED"
  }
}
~~~

Write literal valid observations and assert this exact result:

~~~python
{
    "schema": "liqvera-mezo-compatibility-result/v1",
    "status": "COMPATIBILITY_PASS_PAYMENT_BLOCKED",
    "network": "eip155:31611",
    "chain_id": 31611,
    "musd_address": "0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",
    "musd_decimals": 18,
    "x402_version": 2,
    "scheme": "exact",
    "sdk_version": "2.16.0",
    "coin": "BTC",
    "bid_levels": 20,
    "ask_levels": 20,
    "payment_readiness": "BLOCKED",
    "payment_blockers": ["PAY_TO_MISSING", "FINALITY_RULE_UNVERIFIED"]
}
~~~

Add a parameterized failure test with literal mutations and reason codes:

~~~python
(
    ("wrong_chain", "MEZO_CHAIN_ID_MISMATCH"),
    ("empty_token_code", "MUSD_CODE_MISSING"),
    ("wrong_decimals", "MUSD_DECIMALS_MISMATCH"),
    ("facilitator_mainnet_only", "FACILITATOR_SUPPORT_MISSING"),
    ("missing_btc_meta", "HYPERLIQUID_BTC_MISSING"),
    ("too_many_levels", "HYPERLIQUID_DEPTH_LIMIT_EXCEEDED"),
    ("sdk_version_missing", "X402_SDK_VERSION_MISSING"),
    ("unsafe_pay_to_policy", "PAY_TO_POLICY_UNSAFE"),
    ("invented_finality_policy", "FINALITY_POLICY_UNSUPPORTED"),
)
~~~

The success-path test must also assert the exact ordered `payment_blockers` list.
No test reads `PAY_TO` from the developer environment or accepts an address in the
lock; F1 proves that no implicit/example receiver can become payment-ready.

- [ ] **Step 2: Run RED**

~~~bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/compatibility/test_mezo_compatibility.py -q
~~~

Expected: collection FAIL because tools.mezo_compatibility is absent.

- [ ] **Step 3: Implement pure validators**

Create CompatibilityError and verify_observations. Check, in order: lock schema/network; hex chain ID; non-empty code; hex decimals; facilitator version/scheme/network and matching lowercase asset/decimals; BTC metadata; two book sides with at most 20 entries; all four npm versions equal 2.16.0; and the fail-closed payment-readiness policy (`PAY_TO` required only from the future operator environment, no default, finality unverified).

Errors contain only the stable reason code. Return only the exact sanitized result above; never return raw bodies, prices, quantities, npm stderr, or URLs from responses.

- [ ] **Step 4: Implement the fixed-endpoint CLI**

The wrapper accepts only --lock and --output. It uses a redirect-blocking urllib opener with a 12-second timeout, fixed JSON-RPC calls, fixed Hyperliquid meta/l2Book BTC bodies, GET /supported, and npm view package@2.16.0 version --json. Atomic output is sorted canonical JSON plus a final newline. Failure prints one stable code and exits 1.

Add tests/compatibility to tool.pytest.ini_options.testpaths in pyproject.toml so
the default suite and grok_verify execute these tests.

- [ ] **Step 5: Bind every artifact**

~~~text
docs/compatibility/mezo-evidence-v1.json -> document:graph-authority-handoff / DOCUMENTATION
tools/mezo_compatibility.py -> runtime:public-capture / TOOL_SOURCE
scripts/check-mezo-compatibility.py -> runtime:public-capture / TOOL_SOURCE
tests/compatibility/test_mezo_compatibility.py -> test:data-contracts / TEST_SOURCE
~~~

- [ ] **Step 6: Run GREEN**

~~~bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest \
  tests/compatibility/test_mezo_compatibility.py -q
PATH="$PWD/.venv/bin:$PATH" python -B -m ruff check \
  tools/mezo_compatibility.py scripts/check-mezo-compatibility.py \
  tests/compatibility/test_mezo_compatibility.py
PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-architecture-graph.py \
  --manifest-root architecture --phase precommit --allow-declared-conflicts
~~~

- [ ] **Step 7: Run the live read-only probe**

~~~bash
PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py \
  --lock docs/compatibility/mezo-evidence-v1.json \
  --output engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json
~~~

Expected: `COMPATIBILITY_PASS_PAYMENT_BLOCKED`, with `PAY_TO_MISSING` and
`FINALITY_RULE_UNVERIFIED` preserved in the sanitized result. This is a successful
read-only compatibility probe, not authorization to expose a paid route. An external
probe failure becomes `BLOCKED_EXTERNAL` in blockers.md; do not alter the lock to
force success.

When the result file exists, bind the exact path
engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json to
document:graph-authority-handoff as DOCUMENTATION, then rerun the architecture
check from Step 6. When the probe is blocked and no file exists, do not create
or bind an empty evidence file.

- [ ] **Step 8: Update handoff and commit**

~~~bash
git add docs/compatibility/mezo-evidence-v1.json \
  tools/mezo_compatibility.py scripts/check-mezo-compatibility.py \
  tests/compatibility/test_mezo_compatibility.py pyproject.toml architecture/architecture.yaml \
  engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json \
  engineering/changes/2026-09-24-mezo-evidence/blockers.md handoff.md
git diff --cached --check
git commit -m "feat(compatibility): lock Mezo testnet boundary"
~~~

If the probe is externally blocked, omit the absent result file, commit the named
blocker with passing offline tests, and keep F1 compatibility evidence blocked. If
the probe succeeds, F1 may close with its two named payment-readiness blockers;
those blockers do not prevent independent F2 contract work.

### Task 5: Accept the ADR and close F1 with evidence

**Files:**

- Create: docs/adr/0002-liqvera-report-payment-boundary.md
- Modify: engineering/changes/2026-09-24-mezo-evidence/adr.md
- Modify: engineering/changes/2026-09-24-mezo-evidence/tasks.md
- Modify: engineering/changes/2026-09-24-mezo-evidence/acceptance-matrix.md
- Modify: engineering/changes/2026-09-24-mezo-evidence/blockers.md
- Modify: engineering/changes/2026-09-24-mezo-evidence/state.json
- Create: engineering/changes/2026-09-24-mezo-evidence/evidence/f1-verification.md
- Modify: README.md
- Modify: handoff.md
- Modify: architecture/architecture.yaml

**Interfaces:**

- Consumes: the four F1 implementation commits and fresh verification output.
- Produces: accepted ADR-0002, factual F1 evidence, updated status, and a handoff to a separate F2 plan.

- [ ] **Step 1: Accept ADR-0002**

Promote the reviewed draft with Status: accepted. Decide: Python owns capture/validation/exact analytics/report/verifier; TypeScript/Express is only the future API/x402 boundary; PostgreSQL is the future payment ledger; artifact bytes are immutable; only eip155:31611 is authorized; mainnet, custody, exchange mutation, merchant private keys, and user secrets are excluded.

Replace the change-package draft with a pointer to ADR-0002 and bind the ADR as DOCUMENTATION.

- [ ] **Step 2: Verify the stable implementation commit**

~~~bash
git rev-parse HEAD
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record
PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py \
  --lock docs/compatibility/mezo-evidence-v1.json
git diff --check
git status --short
~~~

Expected: all verification commands exit 0. A successful compatibility command
still reports `COMPATIBILITY_PASS_PAYMENT_BLOCKED`; it must not erase
`PAY_TO_MISSING` or `FINALITY_RULE_UNVERIFIED`. If compatibility is externally
unavailable, local checks pass and F1 remains `BLOCKED_EXTERNAL`.

- [ ] **Step 3: Record exact evidence**

f1-verification.md records UTC time, literal implementation SHA, Python/pytest/hatchling/npm versions, every command and exit code, compatibility evidence or blocker, the unresolved receiver/finality reason codes, and explicit confirmation that no payment, signature, private source verification, receipt, deployment, push, or release occurred.

- [ ] **Step 4: Update status**

Check completed F1 tasks and accurate A01/A27-A29 rows. Mark the F1 baseline and
compatibility package complete-with-blockers only when its evidence exists; keep
payment readiness false and all payment rows blocked/not run. Set state.json from
scoped to implementing because F2-F7 remain open, with actual UTC history. Update
README and handoff with factual F1 status, `PAY_TO_MISSING`,
`FINALITY_RULE_UNVERIFIED`, and the next F2 contract-plan action.

- [ ] **Step 5: Verify the closure delta**

~~~bash
PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-architecture-graph.py \
  --manifest-root architecture --phase precommit --allow-declared-conflicts
PATH="$PWD/.venv/bin:$PATH" python -B -m ruff check \
  tools/graph_checker tools/mezo_compatibility.py \
  scripts/check-mezo-compatibility.py tests/graph tests/compatibility \
  tests/readonly_analyzer/test_frozen_package_tamper.py \
  tests/installed/test_root_development_toolchain.py
git diff --check
~~~

- [ ] **Step 6: Commit closure**

~~~bash
git add docs/adr/0002-liqvera-report-payment-boundary.md README.md handoff.md \
  architecture/architecture.yaml engineering/changes/2026-09-24-mezo-evidence
git diff --cached --check
git commit -m "docs: record verified Liqvera F1 baseline"
~~~

- [ ] **Step 7: Re-run final verification**

~~~bash
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record
git status --short --branch
git log --oneline --decorate -6
~~~

Expected: verification exits 0 and the worktree is clean. Report the final commit separately from the implementation SHA; do not claim a factory receipt.
