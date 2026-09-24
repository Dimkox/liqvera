# M0-M3 Canonical Distributions and Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the approved Stage A authority graph, three separately installable Python distributions, executable Go conformance evidence, installed-artifact capability proofs, and evidence-gated retirement of superseded runtime owners.

**Architecture:** A manifest-driven checker owns traceability, lifecycle, runtime-DAG, release, migration, and no-orphan validation. `mee_public_capture` and `mee_readonly_analyzer` are physically separate applications that depend only on pure `mee_contracts`; Go remains a test-only executable specification and is never packaged into Stage A artifacts.

**Tech Stack:** Python 3.12, hatchling, pytest, PyYAML, JSON Schema, Go 1.26.5 test-only reference, Docker/OCI inspection, GitHub Actions on `[self-hosted, claw]` only.

## Global Constraints

- Scope is migrations M0, M1, M2, M3, and M7 only; M4-M6 are prospective graph nodes, not implementation work.
- Requirements covered: `ARCH-001..009`, `ARCH-GO-001..005`, `GRAPH-001..012`, `CI-001..008`, `SEC-001..007`; acceptance gates `1..8`, `22`, and `26` where phase-applicable.
- Stage A remains public evidence and read-only analysis only; no execution artifact, signer, private/account stream, order, cancel, transfer, withdrawal, deployment, promotion, or live action is permitted.
- Authoritative validation runs only on `claw-engine-runner` / `[self-hosted, claw]`; Windows/PowerShell commands are diagnostic and never release evidence.
- Every independently reviewable task ends with its focused RED/GREEN checks, the graph/no-orphan check, an update to root `handoff.md`, and one coherent commit.
- Tests must exercise wheels installed into fresh virtual environments outside the checkout; editable installs, repository-root imports, pytest `pythonpath`, and compatibility copies are forbidden as artifact proof.
- `mee_contracts` contains no application, adapter, storage implementation, network client, database driver, or workflow dependency.
- Capture and Analyzer never import or package each other's namespace; shared imports are limited to `mee_contracts`.
- Go source, binaries, modules, build layers, entry points, and transitive dependencies are excluded from every Stage A runtime/release artifact beginning at M0.
- PR #21 is never merged or rebased wholesale; salvage is provenance-bound to head `7fe6918690f8bc1da5826c67e3619de4126e4f54` and rewritten into canonical namespaces.
- A prospective evidence type is not a receipt. Placeholder, empty, copied, synthetic, future-dated, or anticipated receipts fail closed.
- Historical Git provenance and exact rollback targets survive retirement; unresolved material is not deleted to silence an orphan check.

---

## File Structure

- `architecture/*.yaml`: approved requirements, ownership, runtime, data, strategy, release, Go-conformance, and PR #21 salvage authorities.
- `architecture/schemas/*.json`: closed schemas for manifests, conformance rows, and salvage provenance.
- `tools/graph_checker/*.py`: deterministic loading, lifecycle, traceability, runtime-DAG, release, and diagnostic logic.
- `packages/contracts/`: independently buildable pure `mee_contracts` distribution.
- `packages/public-capture/`: independently buildable public-only `mee_public_capture` distribution.
- `packages/readonly-analyzer/`: independently buildable network-free final-replay `mee_readonly_analyzer` distribution.
- `tests/graph/`, `tests/contracts/`, `tests/public_capture/`, `tests/readonly_analyzer/`, `tests/conformance/`, `tests/installed/`, `tests/artifact/`: focused source, installed, and artifact tests.
- `scripts/check-architecture-graph.py`, `scripts/build-stage-a-distributions.py`, `scripts/inspect-installed-distribution.py`, `scripts/check-stage-a-artifacts.py`, `scripts/run-go-conformance.py`, `scripts/verify-pr21-salvage.py`: Claw gate entry points.

### Task 1: M0 Version Authority Manifests and Deterministic Graph Checker

**Requirements:** `ARCH-008`, `GRAPH-001..012`; acceptance gates `1`, `2`, `5`.

**Files:**
- Create: `architecture/requirements.yaml`
- Create: `architecture/architecture.yaml`
- Create: `architecture/runtime.yaml`
- Create: `architecture/data-contracts.yaml`
- Create: `architecture/strategies.yaml`
- Create: `architecture/release.yaml`
- Create: `architecture/schemas/graph-manifest.schema.json`
- Create: `tools/graph_checker/__init__.py`
- Create: `tools/graph_checker/__main__.py`
- Create: `tools/graph_checker/model.py`
- Create: `tools/graph_checker/loader.py`
- Create: `tools/graph_checker/checker.py`
- Create: `scripts/check-architecture-graph.py`
- Create: `tests/graph/test_checker.py`
- Create: `tests/fixtures/graph/valid/architecture.yaml`
- Create: `tests/fixtures/graph/cycle/architecture.yaml`
- Modify: `pyproject.toml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: approved requirement IDs and lifecycle rules from `docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md`.
- Produces: `load_graph(manifest_root: Path) -> ArchitectureGraph`, `check_graph(graph: ArchitectureGraph, phase: Phase) -> tuple[Diagnostic, ...]`, and CLI exit codes `0` clean, `1` graph violation, `2` malformed input.

- [ ] **Step 1: Write the failing cycle and orphan tests**

```python
from pathlib import Path

from tools.graph_checker.checker import check_graph
from tools.graph_checker.loader import load_graph
from tools.graph_checker.model import Phase


def test_runtime_cycle_reports_stable_path() -> None:
    graph = load_graph(Path("tests/fixtures/graph/cycle"))
    diagnostics = check_graph(graph, Phase.PRECOMMIT)
    assert [(item.code, item.path) for item in diagnostics] == [
        ("RUNTIME_CYCLE", ("module:a", "module:b", "module:a")),
    ]


def test_active_source_without_reverse_requirement_path_is_orphan() -> None:
    graph = load_graph(Path("tests/fixtures/graph/valid"))
    orphan = graph.with_node("module:orphan", kind="SourceModule", owner="capture")
    diagnostics = check_graph(orphan, Phase.PRECOMMIT)
    assert diagnostics[0].code == "IMPLEMENTATION_ORPHAN"
    assert diagnostics[0].requirement_ids == ()
```

- [ ] **Step 2: Run the RED test on Claw**

Run: `python3 -m pytest tests/graph/test_checker.py -q`

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'tools.graph_checker'`.

- [ ] **Step 3: Implement the minimal immutable graph interface**

```python
class Phase(StrEnum):
    PRECOMMIT = "precommit"
    MERGE = "merge"
    RELEASE = "release"
    PROMOTION = "promotion"
    DEPLOYMENT = "deployment"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    node_id: str | None
    path: tuple[str, ...]
    requirement_ids: tuple[str, ...]
    message: str


def check_graph(graph: ArchitectureGraph, phase: Phase) -> tuple[Diagnostic, ...]:
    diagnostics = [*_check_schema(graph), *_check_owners(graph)]
    diagnostics.extend(_check_lifecycle(graph, phase))
    diagnostics.extend(_check_traceability(graph))
    diagnostics.extend(_check_runtime_dag(graph))
    diagnostics.extend(_check_migrations(graph))
    diagnostics.extend(_check_receipts(graph, phase))
    return tuple(sorted(diagnostics, key=lambda item: (item.code, item.path)))
```

- [ ] **Step 4: Declare current baseline conflicts without resolving them**

```yaml
nodes:
  - id: conflict:duplicate-python-namespace
    kind: Conflict
    owner: architecture
    lifecycle: DECLARED
    requirements: [ARCH-001, GRAPH-011]
  - id: conflict:github-hosted-ci
    kind: Conflict
    owner: ci
    lifecycle: DECLARED
    requirements: [CI-001, CI-002]
  - id: conflict:go-stage-a-build
    kind: Conflict
    owner: runtime
    lifecycle: DECLARED
    requirements: [ARCH-GO-001, ARCH-GO-004]
```

- [ ] **Step 5: Run focused GREEN checks on Claw**

Run: `python3 -m pytest tests/graph/test_checker.py -q`

Expected: PASS.

Run: `python3 scripts/check-architecture-graph.py --manifest-root tests/fixtures/graph/valid --phase precommit`

Expected: exit `0` and `graph check passed: phase=precommit diagnostics=0`.

Run: `python3 scripts/check-architecture-graph.py --manifest-root tests/fixtures/graph/cycle --phase precommit`

Expected: exit `1` and one `RUNTIME_CYCLE module:a -> module:b -> module:a` diagnostic.

- [ ] **Step 6: Verify repository graph coverage, update handoff, and commit**

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts`

Expected: exit `0`, with the three named baseline conflicts reported as declared blockers rather than omitted nodes.

Update `handoff.md` with manifest/checker identities, focused receipt, blockers, rollback target `a0cdbbf78a38f0bd429a45c810a5c34862a18ef1`, and next task.

```bash
git add architecture tools/graph_checker scripts/check-architecture-graph.py tests/graph tests/fixtures/graph pyproject.toml handoff.md
git commit -m "feat(graph): establish versioned architecture authority"
```

### Task 2: M0 Claw-Only Gates and Go Artifact Exclusion

**Requirements:** `ARCH-GO-001`, `ARCH-GO-004`, `CI-001..008`; acceptance gates `6`, `8`, `22`.

**Files:**
- Create: `tests/graph/test_workflow_policy.py`
- Create: `scripts/cleanup-claw-workspace.sh`
- Modify: `.github/workflows/verify-a2-pr-on-claw.yml`
- Modify: `.github/workflows/build-a2-on-claw.yml`
- Delete: `.github/workflows/ci.yml`
- Modify: `architecture/runtime.yaml`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: Task 1 workflow nodes and `check_graph(..., Phase.MERGE)`.
- Produces: the Claw-only/no-Go workflow policy and default-branch workflow
  skeleton whose jobs use `[self-hosted, claw]`, minimal read-only permissions,
  isolated cleanup, and no Go Stage A build edge. M6 Task 1 is the immediate
  next DAG node and must replace the skeleton with the concrete PR-identity,
  disposable-sandbox, and persisted validation-receipt controller before any
  M1-M5 authoritative receipt is accepted.

- [ ] **Step 1: Write the failing workflow policy test**

```python
def test_all_active_gate_jobs_are_claw_only() -> None:
    workflows = load_active_workflows(Path(".github/workflows"))
    offenders = [job.path for job in workflows.jobs if job.runs_on != ["self-hosted", "claw"]]
    assert offenders == []


def test_pr_gate_has_no_mutation_authority() -> None:
    gate = load_workflow(Path(".github/workflows/verify-a2-pr-on-claw.yml"))
    assert gate.permissions == {"contents": "read"}
    assert gate.has_docker_socket is False
    assert gate.has_deploy_or_registry_step is False
```

- [ ] **Step 2: Run the RED test on Claw**

Run: `python3 -m pytest tests/graph/test_workflow_policy.py -q`

Expected: FAIL listing `.github/workflows/ci.yml` jobs using `ubuntu-24.04`.

- [ ] **Step 3: Move required commands to trusted Claw workflows and remove hosted CI**

```yaml
runs-on: [self-hosted, claw]
permissions:
  contents: read
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
    with:
      persist-credentials: false
  - name: Validate architecture graph
    run: python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge
  - name: Cleanup isolated workspace
    if: always()
    run: scripts/cleanup-claw-workspace.sh "${RUNNER_TEMP}/${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
```

- [ ] **Step 4: Run GREEN policy and graph checks on Claw**

Run: `python3 -m pytest tests/graph/test_workflow_policy.py -q`

Expected: PASS.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge`

Expected: `conflict:github-hosted-ci` resolved; remaining declared migration conflicts stay blocking for later gates.

- [ ] **Step 5: Update handoff and commit**

Update `handoff.md` with the trusted workflow identities, exact test output, remaining conflicts, and rollback commit.

```bash
git add .github/workflows architecture tests/graph/test_workflow_policy.py handoff.md
git commit -m "ci: enforce Claw-only architecture gates"
```

### Task 3: M1 Pure Contracts Distribution

**Requirements:** `ARCH-001`, `ARCH-004`, `ARCH-009`, `DATA-005`, `DATA-006`; acceptance gates `3`, `4`.

**Files:**
- Create: `packages/contracts/pyproject.toml`
- Create: `packages/contracts/src/mee_contracts/__init__.py`
- Create: `packages/contracts/src/mee_contracts/exact.py`
- Create: `packages/contracts/src/mee_contracts/market.py`
- Create: `packages/contracts/src/mee_contracts/evidence.py`
- Create: `packages/contracts/src/mee_contracts/provenance.py`
- Create: `packages/contracts/src/mee_contracts/reasons.py`
- Create: `tests/contracts/test_independent_install.py`
- Create: `tests/contracts/test_purity.py`
- Create: `scripts/inspect-installed-distribution.py`
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/runtime.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: pure values from `multi_exchange_engine/domain/market.py`, `multi_exchange_engine/domain/book.py`, `multi_exchange_engine/exchange/contracts.py`, and `multi_exchange_engine/shadow/{exact,reasons,provenance}.py`.
- Produces: `EvidenceReader` protocol, immutable exact domain values, and wheel `mee_contracts`; it produces no application service or infrastructure implementation.

- [ ] **Step 1: Write the failing purity and isolated-import tests**

```python
def test_contracts_dependency_closure_is_empty() -> None:
    metadata = distribution_metadata("mee-contracts")
    assert metadata.requires_dist == ()


def test_contracts_exports_reader_protocol() -> None:
    from mee_contracts.evidence import EvidenceReader
    assert EvidenceReader.__module__ == "mee_contracts.evidence"
```

- [ ] **Step 2: Run RED from a fresh Claw venv**

Run: `python3 -m pytest tests/contracts -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'mee_contracts'`.

- [ ] **Step 3: Add minimal build metadata and protocol**

```toml
[project]
name = "mee-contracts"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling==1.31.0"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/mee_contracts"]
```

```python
@runtime_checkable
class EvidenceReader(Protocol):
    def read_capture_manifest(self, capture_run_id: UUID) -> CaptureManifest: ...
    def capture_terminal(self, capture_run_id: UUID) -> CaptureTerminal: ...
    def iter_control_evidence(self, capture_run_id: UUID) -> Iterator[ControlEvidenceRecord]: ...
    def iter_raw_batches(self, capture_run_id: UUID) -> Iterator[RawBatchRecord]: ...
    def iter_raw_envelopes(self, capture_run_id: UUID) -> Iterator[RawPublicEnvelope]: ...
    def iter_quality_minutes(self, capture_run_id: UUID) -> Iterator[QualityMinuteRecord]: ...
    def read_mapping_snapshot(self, capture_run_id: UUID) -> MappingSnapshot: ...
```

Fee cases and strategy configuration are separate analyzer inputs. They are not
methods on the capture-evidence reader and cannot make Capture the owner of an
economic decision.

- [ ] **Step 4: Build, install, and test outside the checkout on Claw**

Run: `python3 -m build --wheel packages/contracts --outdir "$RUNNER_TEMP/dist"`

Expected: one `mee_contracts-0.1.0-py3-none-any.whl`.

Run: `python3 -m venv "$RUNNER_TEMP/contracts-venv" && "$RUNNER_TEMP/contracts-venv/bin/python" -m pip install --no-deps "$RUNNER_TEMP/dist"/mee_contracts-*.whl && cd "$RUNNER_TEMP" && contracts-venv/bin/python -I -c 'import mee_contracts'`

Expected: exit `0` outside the repository.

Run: `python3 scripts/inspect-installed-distribution.py --python "$RUNNER_TEMP/contracts-venv/bin/python" --distribution mee-contracts --allow-namespace mee_contracts --forbid-namespace mee_public_capture mee_readonly_analyzer multi_exchange_engine --forbid-dependency httpx websockets psycopg asyncpg hyperliquid-python-sdk eth-account`

Expected: `installed boundary passed: mee-contracts`.

- [ ] **Step 5: Run graph/no-orphan check, update handoff, and commit**

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase precommit`

Expected: contracts nodes have forward/reverse requirement paths and no orphan source/test/artifact nodes.

Update `handoff.md` with wheel SHA256, isolated-import proof, purity result, and rollback commit.

```bash
git add packages/contracts tests/contracts scripts/inspect-installed-distribution.py architecture handoff.md
git commit -m "feat(contracts): add pure installable contracts distribution"
```

### Task 4: M1 Public Capture Distribution

**Requirements:** `ARCH-001..005`, `DATA-001`, `DATA-002`, `SEC-001`; acceptance gates `3`, `7`.

**Files:**
- Create: `packages/public-capture/pyproject.toml`
- Create: `packages/public-capture/src/mee_public_capture/__init__.py`
- Create: `packages/public-capture/src/mee_public_capture/__main__.py`
- Move: `multi_exchange_engine/a2/` to `packages/public-capture/src/mee_public_capture/a2/`
- Move: `multi_exchange_engine/exchange/public_hyperliquid.py` to `packages/public-capture/src/mee_public_capture/public_adapters/hyperliquid.py`
- Move: `multi_exchange_engine/exchange/public_lighter.py` to `packages/public-capture/src/mee_public_capture/public_adapters/lighter.py`
- Create: `tests/public_capture/test_installed_boundary.py`
- Modify: `tests/a2/`
- Modify: `scripts/check-a2-boundary.py`
- Modify: `Dockerfile.a2`
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/runtime.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: `mee_contracts` exact values and public evidence contracts from Task 3.
- Produces: console entry point `mee-public-capture = "mee_public_capture.__main__:main"`, credential-free public adapters, and constrained capture writer; no analyzer or execution interface.

- [ ] **Step 1: Write the failing installed-boundary test**

```python
def test_public_capture_has_only_public_entry_point(installed_distribution) -> None:
    assert installed_distribution.console_scripts == {
        "mee-public-capture": "mee_public_capture.__main__:main"
    }
    assert "mee_readonly_analyzer" not in installed_distribution.namespaces
    assert "multi_exchange_engine" not in installed_distribution.namespaces
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/public_capture/test_installed_boundary.py -q`

Expected: FAIL because distribution `mee-public-capture` does not exist.

- [ ] **Step 3: Add minimal separate package metadata and entry point**

```toml
[project]
name = "mee-public-capture"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["mee-contracts==0.1.0", "httpx==0.28.1", "websockets==17.0.1"]

[project.scripts]
mee-public-capture = "mee_public_capture.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/mee_public_capture"]
```

- [ ] **Step 4: Rewrite imports and keep forbidden capabilities absent**

```python
from mee_contracts.evidence import ControlEvidenceRecord, RawBatchRecord
from mee_contracts.market import Venue


def main() -> int:
    return run_public_capture(load_public_configuration())
```

- [ ] **Step 5: Run source, wheel, and graph GREEN checks on Claw**

Run: `python3 -m pytest tests/public_capture tests/a2 -q`

Expected: PASS.

Run: `python3 scripts/inspect-installed-distribution.py --distribution mee-public-capture --forbid-namespace mee_readonly_analyzer multi_exchange_engine --forbid-symbol signer wallet order cancel amend withdraw transfer private account`

Expected: `installed boundary passed: mee-public-capture`.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase precommit`

Expected: no Capture ownership, reachability, dependency, entry-point, configuration, test, or artifact orphan.

- [ ] **Step 6: Update handoff and commit**

Update `handoff.md` with focused suite count, wheel hash, dependency closure, unresolved legacy expiry/removal gate, and rollback commit.

```bash
git add packages/public-capture tests/a2 tests/public_capture scripts/check-a2-boundary.py Dockerfile.a2 architecture handoff.md
git commit -m "feat(capture): migrate A2 to public-only distribution"
```

### Task 5: M1 Read-Only Analyzer and Provenance-Bound PR #21 Salvage

**Requirements:** `ARCH-001..004`, `DATA-003`, `DATA-004`, `SEC-002`, `SEC-006`; acceptance gates `3`, `7`.

**Files:**
- Create: `architecture/pr21-salvage.yaml`
- Create: `architecture/schemas/salvage.schema.json`
- Create: `packages/readonly-analyzer/pyproject.toml`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/__init__.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/__main__.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/frozen_package/{codec,reader,types}.py`
- Create: `packages/readonly-analyzer/src/mee_readonly_analyzer/config.py`
- Create: `tests/readonly_analyzer/test_frozen_package.py`
- Create: `tests/readonly_analyzer/test_frozen_package_tamper.py`
- Create: `tests/readonly_analyzer/test_installed_boundary.py`
- Create: `scripts/verify-pr21-salvage.py`
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/runtime.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: the sole `mee_contracts.evidence.EvidenceReader`; eligible PR #21 immutable config/record/codec/reader blobs from exact head `7fe6918690f8bc1da5826c67e3619de4126e4f54`. PR #21 writer algorithms remain provenance for M4 Public Capture export and are not installed here.
- Produces: `FrozenPackageEvidenceReader(root: Path)` and entry point `mee-readonly-analyzer`; it produces no package writer, venue network, or capture/evidence mutation capability.

- [ ] **Step 1: Write failing provenance and tamper tests**

```python
def test_every_salvaged_blob_has_exact_source_and_rewrite_rule() -> None:
    rows = load_salvage_manifest(Path("architecture/pr21-salvage.yaml"))
    assert rows
    assert all(row.source_commit == "7fe6918690f8bc1da5826c67e3619de4126e4f54" for row in rows)
    assert all(len(row.source_blob_sha) == 40 and row.target.startswith("packages/readonly-analyzer/") for row in rows)


def test_reader_rejects_changed_member(valid_package: Path) -> None:
    member = valid_package / "quality_minutes/records.ndjson"
    member.write_bytes(member.read_bytes() + b"\n")
    with pytest.raises(FrozenPackageError, match="MEMBER_HASH_MISMATCH"):
        FrozenPackageEvidenceReader(valid_package)
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/readonly_analyzer -q`

Expected: FAIL with missing `mee_readonly_analyzer` and salvage manifest.

- [ ] **Step 3: Record exact salvage rows before rewriting code**

```yaml
source_pr: 21
source_head: 7fe6918690f8bc1da5826c67e3619de4126e4f54
items:
  - source_path: multi_exchange_engine/shadow_economics/_frozen_reader.py
    source_blob_sha: 9fc5061ba602d4362593527a89e48540a0df07e8
    target: packages/readonly-analyzer/src/mee_readonly_analyzer/frozen_package/reader.py
    rule: rewrite imports to mee_contracts and keep final replay network-free
```

The recorded blob is the exact value returned by `git rev-parse 7fe6918690f8bc1da5826c67e3619de4126e4f54:multi_exchange_engine/shadow_economics/_frozen_reader.py`; the verifier rejects any mismatch.

- [ ] **Step 4: Implement the minimal rewritten boundary**

```toml
[project]
name = "mee-readonly-analyzer"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["mee-contracts==0.1.0"]

[project.scripts]
mee-readonly-analyzer = "mee_readonly_analyzer.__main__:main"
```

```python
from mee_contracts.evidence import EvidenceReader


class FrozenPackageEvidenceReader(EvidenceReader):
    def __init__(self, root: Path) -> None:
        self._root = require_verified_frozen_root(root)
```

- [ ] **Step 5: Run GREEN salvage, tamper, installed, and graph checks on Claw**

Run: `python3 scripts/verify-pr21-salvage.py --manifest architecture/pr21-salvage.yaml`

Expected: every source blob resolves at the exact PR head and every target has one rewrite rule.

Run: `python3 -m pytest tests/readonly_analyzer -q`

Expected: PASS, including tamper rejection.

Run: `python3 scripts/inspect-installed-distribution.py --distribution mee-readonly-analyzer --forbid-namespace mee_public_capture multi_exchange_engine --forbid-dependency httpx websockets hyperliquid-python-sdk eth-account --forbid-symbol signer wallet order cancel amend withdraw transfer private write_frozen_package atomic_write`

Expected: `installed boundary passed: mee-readonly-analyzer`.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase precommit`

Expected: no Analyzer or salvage-provenance orphan.

- [ ] **Step 6: Update handoff and commit**

Update `handoff.md` with accepted/rejected salvage boundaries, exact blobs, test receipt, and rollback commit.

```bash
git add architecture packages/readonly-analyzer tests/readonly_analyzer scripts/verify-pr21-salvage.py handoff.md
git commit -m "feat(analyzer): salvage frozen evidence into read-only distribution"
```

### Task 6: M1 Eliminate Both Legacy Python Namespace Owners

**Requirements:** `ARCH-001`, `ARCH-002`, `GRAPH-005`, `GRAPH-011`; acceptance gates `2`, `3`.

**Files:**
- Delete: `multi_exchange_engine/`
- Delete: `src/multi_exchange_engine/`
- Move: `tests/domain/`, `tests/exchange/`, `tests/shadow/`, and `tests/unit/` to their canonical distribution test trees.
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `Dockerfile.a2`
- Modify: `.dockerignore`
- Modify: `scripts/*.py`
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/runtime.yaml`
- Create: `tests/installed/test_no_legacy_namespace.py`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: all migrated canonical symbols and passing installed tests from Tasks 3-5.
- Produces: exactly three top-level Stage A import namespaces and no compatibility import/re-export/path shim for `multi_exchange_engine`.

- [ ] **Step 1: Write the failing tracked-source and fresh-process tests**

```python
def test_legacy_namespace_is_absent_from_git() -> None:
    tracked = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    assert not any(path.startswith(("multi_exchange_engine/", "src/multi_exchange_engine/")) for path in tracked)


def test_legacy_import_fails_in_fresh_installed_environment(installed_python: Path) -> None:
    result = subprocess.run(
        [str(installed_python), "-I", "-c", "import mee_contracts"],
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "ModuleNotFoundError" in result.stderr
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/installed/test_no_legacy_namespace.py -q`

Expected: FAIL listing tracked legacy roots and successful incidental legacy import.

- [ ] **Step 3: Rewrite every consumer and remove both roots atomically**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-m 'not live'"

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["mee_contracts", "mee_public_capture", "mee_readonly_analyzer"]
```

- [ ] **Step 4: Run GREEN namespace and full distribution checks on Claw**

Run: `git grep -n -E '(^|[[:space:]])(from|import)[[:space:]]+multi_exchange_engine' -- ':!docs/archive/**'`

Expected: exit `1`, no active import matches.

Run: `git ls-files 'multi_exchange_engine/**' 'src/multi_exchange_engine/**'`

Expected: no output.

Run: `python3 -m pytest tests/contracts tests/public_capture tests/readonly_analyzer tests/installed -q`

Expected: PASS.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge`

Expected: duplicate-owner conflict resolved; predecessor nodes are `RETIRED` with provenance and rollback edges.

- [ ] **Step 5: Update handoff and commit**

Update `handoff.md` with eliminated paths, replacement namespaces, regression output, and rollback commit.

```bash
git add -A multi_exchange_engine src tests pyproject.toml README.md docs/architecture.md Dockerfile.a2 .dockerignore scripts architecture handoff.md
git commit -m "refactor(packaging): eliminate duplicate legacy namespaces"
```

### Task 7: M2 Go Test-Only Executable Conformance

**Requirements:** `ARCH-GO-001..005`; acceptance gate `6`.

**Files:**
- Create: `architecture/go-conformance.yaml`
- Create: `architecture/schemas/go-conformance.schema.json`
- Create: `scripts/run-go-conformance.py`
- Create: `tests/conformance/test_exact_arithmetic.py`
- Create: `tests/conformance/test_fail_closed_unknown.py`
- Create: `tests/conformance/test_order_ownership.py`
- Create: `tests/conformance/test_monotonic_fills.py`
- Create: `tests/conformance/test_risk_reservation.py`
- Create: `tests/conformance/test_retirement_policy.py`
- Modify: `.github/workflows/verify-a2-pr-on-claw.yml`
- Modify: `architecture/runtime.yaml`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: named Go tests under `internal/**`, canonical Python contract/implementation tests, exact source SHA, and independent review result.
- Produces: immutable conformance receipt rows with `invariant_id`, `go_test`, `contract_symbol`, `python_test`, `negative_tests`, `claw_gate`, `source_sha`, `review_result`, and retirement state `BLOCKED|ELIGIBLE|RETIRED`.

- [ ] **Step 1: Write the failing retirement-policy test**

```python
def test_same_named_python_test_never_makes_go_reference_eligible() -> None:
    row = conformance_row(review_result=None, claw_receipt=None)
    assert retirement_state(row) == "BLOCKED"


def test_complete_exact_sha_evidence_is_eligible_not_deployable() -> None:
    row = conformance_row(review_result="APPROVED", claw_receipt=receipt_for_head())
    assert retirement_state(row) == "ELIGIBLE"
    assert row.stage_a_packaging_allowed is False
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/conformance/test_retirement_policy.py -q`

Expected: FAIL because conformance manifest and policy do not exist.

- [ ] **Step 3: Declare retained invariants and fail-closed eligibility**

```yaml
invariants:
  - invariant_id: GO-EXACT-001
    go_test: ./internal/fixed
    contract_symbol: mee_contracts.exact.ExactDecimal
    python_test: tests/conformance/test_exact_arithmetic.py
    negative_tests: [reject_nonfinite, reject_binary_float]
    claw_gate: go-conformance
    retirement_state: BLOCKED
    stage_a_packaging_allowed: false
```

- [ ] **Step 4: Implement exact-SHA conformance receipt generation**

```python
def run_conformance(manifest: Path, source_sha: str, output: Path) -> None:
    require_clean_exact_head(source_sha)
    results = run_named_go_and_python_tests(load_manifest(manifest))
    receipt = canonical_receipt(source_sha=source_sha, results=results)
    output.write_bytes(canonical_json(receipt))
```

- [ ] **Step 5: Run RED/GREEN conformance and artifact-exclusion checks on Claw**

Run: `python3 scripts/run-go-conformance.py --manifest architecture/go-conformance.yaml --source-sha "$(git rev-parse HEAD)" --output "$RUNNER_TEMP/go-conformance.json"`

Expected: named Go and Python cases pass; rows lacking independent review remain `BLOCKED`.

Run: `python3 -m pytest tests/conformance -q`

Expected: PASS.

Run: `python3 scripts/check-stage-a-artifacts.py --forbid-path 'cmd/**' 'internal/**' 'go.mod' 'go.sum' --forbid-binary engine`

Expected: Stage A artifacts contain no Go input, binary, entry point, layer, or dependency.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge`

Expected: Go is `TEST_ONLY_EXECUTABLE_SPEC`; conformance edges target tests/review only, never artifacts.

- [ ] **Step 6: Record independent review, update handoff, and commit**

The domain/safety reviewer records an explicit result per invariant; missing tenant/account or bounded-residual parity remains `BLOCKED`.

Update `handoff.md` with receipt hash, blocked/eligible rows, reviewer identity/result, and rollback commit.

```bash
git add architecture/go-conformance.yaml architecture/schemas/go-conformance.schema.json scripts/run-go-conformance.py tests/conformance .github/workflows/verify-a2-pr-on-claw.yml architecture/runtime.yaml architecture/release.yaml handoff.md
git commit -m "test(conformance): map Go invariants to canonical Python contracts"
```

### Task 8: M3 Installed-Artifact and OCI Capability Proof

**Requirements:** `ARCH-002..004`, `SEC-001..007`; acceptance gates `3`, `4`, `7`, `22`.

**Files:**
- Create: `scripts/build-stage-a-distributions.py`
- Create: `scripts/check-stage-a-artifacts.py`
- Create: `tests/installed/test_three_fresh_environments.py`
- Create: `tests/artifact/test_wheel_boundaries.py`
- Create: `tests/artifact/test_entry_points.py`
- Create: `tests/artifact/test_dependency_closure.py`
- Create: `tests/artifact/test_forbidden_capabilities.py`
- Create: `deploy/images/Dockerfile.public-capture`
- Create: `deploy/images/Dockerfile.readonly-analyzer`
- Delete: `Dockerfile.a2`
- Modify: `.github/workflows/build-a2-on-claw.yml`
- Modify: `.dockerignore`
- Modify: `architecture/runtime.yaml`
- Modify: `architecture/release.yaml`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: exact-SHA wheels from Tasks 3-5 and Go-exclusion policy from Task 7.
- Produces: separate wheel/image receipts containing source SHA, artifact SHA256/digest, installed `RECORD`, import graph, dependency closure, entry points, image layers, forbidden scans, network surface, negative mutation result, and graph gate result.

- [ ] **Step 1: Write the failing three-environment artifact test**

```python
@pytest.mark.parametrize(
    ("distribution", "allowed", "forbidden"),
    [
        ("mee-contracts", {"mee_contracts"}, {"mee_public_capture", "mee_readonly_analyzer"}),
        ("mee-public-capture", {"mee_contracts", "mee_public_capture"}, {"mee_readonly_analyzer"}),
        ("mee-readonly-analyzer", {"mee_contracts", "mee_readonly_analyzer"}, {"mee_public_capture"}),
    ],
)
def test_fresh_install_contains_only_allowed_namespaces(distribution, allowed, forbidden, artifact_env) -> None:
    installed = artifact_env.install_one(distribution)
    assert installed.namespaces == allowed
    assert installed.namespaces.isdisjoint(forbidden | {"multi_exchange_engine"})
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/installed tests/artifact -q`

Expected: FAIL because isolated artifact builder/receipt interfaces do not exist.

- [ ] **Step 3: Implement deterministic wheel build and inspection**

```python
def build_all(source_sha: str, output: Path) -> tuple[BuiltArtifact, ...]:
    require_clean_exact_head(source_sha)
    return tuple(build_wheel(path, output) for path in (
        Path("packages/contracts"),
        Path("packages/public-capture"),
        Path("packages/readonly-analyzer"),
    ))
```

```python
def inspect_installed(python: Path, distribution: str) -> ArtifactReceipt:
    return ArtifactReceipt(
        distribution=distribution,
        files=read_distribution_record(python, distribution),
        dependencies=resolved_dependencies(python, distribution),
        entry_points=console_entry_points(python, distribution),
        imports=resolved_import_graph(python, distribution),
    )
```

- [ ] **Step 4: Build images only from wheels**

```dockerfile
FROM python:3.12.13-alpine3.23@sha256:601d3d3797e90e2534782e69c85fafb7971b43f24c7b1b079b7e48dd435e458d
COPY dist/mee_contracts-0.1.0-py3-none-any.whl /wheels/
COPY dist/mee_public_capture-0.1.0-py3-none-any.whl /wheels/
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels mee-public-capture==0.1.0
ENTRYPOINT ["mee-public-capture"]
```

Record this existing repository-approved immutable Python base identity in `architecture/release.yaml`; the graph checker rejects unpinned image references.

- [ ] **Step 5: Run authoritative wheel and image GREEN checks on Claw**

Run: `python3 scripts/build-stage-a-distributions.py --source-sha "$(git rev-parse HEAD)" --out "$RUNNER_TEMP/dist"`

Expected: exactly three wheels and three SHA256 identities.

Run: `python3 -m pytest tests/installed tests/artifact -q`

Expected: PASS in three separate fresh venvs outside the checkout.

Run: `docker build --network=none -f deploy/images/Dockerfile.public-capture -t mee-public-capture:"$(git rev-parse HEAD)" . && docker build --network=none -f deploy/images/Dockerfile.readonly-analyzer -t mee-readonly-analyzer:"$(git rev-parse HEAD)" .`

Expected: both images build only from exact wheels; no repository source copy layer exists.

Run: `python3 scripts/check-stage-a-artifacts.py --dist "$RUNNER_TEMP/dist" --image mee-public-capture:"$(git rev-parse HEAD)" --image mee-readonly-analyzer:"$(git rev-parse HEAD)" --receipt "$RUNNER_TEMP/artifact-boundary.json"`

Expected: `artifact boundary passed` with no cross-application namespace, Go content, execution symbol/dependency/entry point, analyzer network client, or Capture analysis module.

- [ ] **Step 6: Run release-phase graph check without promoting**

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase release --receipt "$RUNNER_TEMP/artifact-boundary.json"`

Expected: exact-SHA artifact nodes verify; promotion/deployment nodes remain prospective and no receipt is fabricated.

- [ ] **Step 7: Update handoff and commit**

Update `handoff.md` with exact wheel/image identities, installed/import/dependency/entry-point/layer/negative-test evidence, remaining M4-M6 blockers, and rollback digests.

```bash
git add scripts/build-stage-a-distributions.py scripts/check-stage-a-artifacts.py tests/installed tests/artifact deploy/images .github/workflows/build-a2-on-claw.yml .dockerignore architecture Dockerfile.a2 handoff.md
git commit -m "test(artifacts): prove separate Stage A capability boundaries"
```

### Task 9: M7 Evidence-Gated Retirement of Superseded Owners

**Requirements:** `ARCH-GO-002..005`, `GRAPH-003`, `GRAPH-005`, `GRAPH-011`; acceptance gates `2`, `5`, `6`, `26`.

**Files:**
- Create: `tools/graph_checker/retirement.py`
- Modify: `tools/graph_checker/checker.py`
- Modify: `tests/conformance/test_retirement_policy.py`
- Create: `tests/graph/test_retirement.py`
- Modify: `architecture/architecture.yaml`
- Modify: `architecture/runtime.yaml`
- Modify: `architecture/go-conformance.yaml`
- Modify: `docs/architecture.md`
- Modify: `README.md`
- Modify: `handoff.md`

**Interfaces:**
- Consumes: exact-SHA conformance and artifact receipts, explicit independent review result, migration expiry/removal gate, provenance edge, and rollback target.
- Produces: `retirement_decision(graph: ArchitectureGraph, node_id: str, receipts: ReceiptSet) -> RetirementDecision`; only `ELIGIBLE` nodes may transition to `RETIRED`, and retirement never changes `stage_a_packaging_allowed=False`.

- [ ] **Step 1: Write failing eligibility and provenance tests**

```python
def test_retirement_fails_without_every_required_receipt() -> None:
    decision = retirement_decision(graph_with_go_reference(), "go:fixed", ReceiptSet())
    assert decision.allowed is False
    assert decision.reason_codes == ("CONFORMANCE_RECEIPT_MISSING", "REVIEW_RESULT_MISSING")


def test_retirement_preserves_provenance_and_rollback() -> None:
    retired = apply_retirement(eligible_graph(), "legacy:a2-root")
    node = retired.node("legacy:a2-root")
    assert node.lifecycle == Lifecycle.RETIRED
    assert retired.has_edge("legacy:a2-root", "derived_from", "git:a0cdbbf")
    assert retired.has_edge("legacy:a2-root", "rolled_back_by", "git:a0cdbbf")
```

- [ ] **Step 2: Run RED on Claw**

Run: `python3 -m pytest tests/graph/test_retirement.py tests/conformance/test_retirement_policy.py -q`

Expected: FAIL because retirement decision logic does not exist.

- [ ] **Step 3: Implement fail-closed retirement decision**

```python
def retirement_decision(graph: ArchitectureGraph, node_id: str, receipts: ReceiptSet) -> RetirementDecision:
    required = graph.required_retirement_evidence(node_id)
    missing = tuple(code for code, predicate in required if not predicate(receipts))
    if missing:
        return RetirementDecision(False, missing)
    if graph.runtime_reachable(node_id):
        return RetirementDecision(False, ("OWNER_STILL_REACHABLE",))
    return RetirementDecision(True, ())
```

- [ ] **Step 4: Retire one owner per independently reviewable commit**

Order: legacy root/`src` Python owners, superseded A2 Docker/workflow owner, then only Go invariant owners whose rows are `ELIGIBLE`. Go rows still lacking exact parity or review remain active test-only references and artifact-unreachable.

- [ ] **Step 5: Run GREEN retirement, graph, and artifact checks on Claw**

Run: `python3 -m pytest tests/graph/test_retirement.py tests/conformance/test_retirement_policy.py -q`

Expected: PASS.

Run: `python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge`

Expected: no expired migration, dual owner, orphan, missing provenance, or missing rollback edge.

Run: `python3 scripts/check-stage-a-artifacts.py --receipt "$RUNNER_TEMP/artifact-boundary.json"`

Expected: retirement does not reintroduce Go, legacy namespaces, or execution capability.

- [ ] **Step 6: Update handoff and commit each retirement**

Update `handoff.md` with node ID, exact conformance/artifact/review receipts, preserved Git provenance, rollback target, and remaining blocked retirements.

Run one of these exact commits only after its matching manifest node is eligible; never combine them:

```bash
git add tools/graph_checker tests/graph tests/conformance architecture docs/architecture.md README.md handoff.md
git commit -m "refactor(retirement): retire legacy Python namespace owners"
```

```bash
git add tools/graph_checker tests/graph tests/conformance architecture docs/architecture.md README.md handoff.md
git commit -m "refactor(retirement): retire superseded A2 packaging owner"
```

```bash
git add tools/graph_checker tests/graph tests/conformance architecture docs/architecture.md README.md handoff.md
git commit -m "refactor(retirement): retire eligible Go reference owner"
```

## Migration and Rollback Contract

- M0 adds authorities and checker behavior without claiming baseline compliance; rollback is the exact pre-M0 commit.
- M1 keeps exactly one active canonical owner. A predecessor becomes runtime-unreachable `MIGRATING`, names an expiry/removal gate, and retains a rollback edge until its separately reviewed retirement.
- Package rollback reverts the complete coherent migration commit and restores the prior verified artifact identity; it never restores only one duplicate import root.
- M2 conformance receipts are append-only exact-SHA evidence. Re-running creates a new receipt; it never edits an old result.
- M3 rollback names exact prior wheel/image digests and does not deploy them. No source reset, force update, registry mutation, or app-stack action belongs in this plan.
- M7 preserves historical Git objects, review results, and rollback edges. A node that cannot be retired safely remains `TEST_ONLY_EXECUTABLE_SPEC`, `MIGRATING`, or `QUARANTINED` with a blocking conflict.

## Ownership and Verification Responsibility

- Architecture owner: approves manifest schema, node/edge ownership, lifecycle transitions, and migration expiry/removal gates.
- Graph implementer: owns deterministic checker code and fixture evidence; cannot approve their own no-orphan semantics.
- Package implementers: separately own Contracts, Capture, and Analyzer migrations and their focused tests.
- Domain/safety reviewer: owns Go invariant mapping and retirement eligibility results.
- Security/boundary reviewer: owns installed-file, import, dependency, entry-point, image-layer, forbidden-capability, network, and negative-mutation review.
- CI/release reviewer: owns Claw isolation, exact-SHA binding, immutable receipt shape, cleanup, and absence of promotion/deployment authority.
- Task implementer updates `handoff.md`; independent reviewer records the task result before the next dependent task starts.

## Final Verification on Claw

```bash
python3 -m pytest tests/graph tests/contracts tests/public_capture tests/readonly_analyzer tests/conformance tests/installed tests/artifact -q
python3 scripts/check-architecture-graph.py --manifest-root architecture --phase merge
python3 scripts/run-go-conformance.py --manifest architecture/go-conformance.yaml --source-sha "$(git rev-parse HEAD)" --output "$RUNNER_TEMP/go-conformance.json"
python3 scripts/build-stage-a-distributions.py --source-sha "$(git rev-parse HEAD)" --out "$RUNNER_TEMP/dist"
python3 scripts/check-stage-a-artifacts.py --dist "$RUNNER_TEMP/dist" --receipt "$RUNNER_TEMP/artifact-boundary.json"
git diff --check HEAD^ HEAD
```

Expected: all focused suites pass; graph has no orphan, cycle, expired migration, dual owner, fabricated receipt, or unresolved phase-applicable conflict; three independently installed artifacts pass capability inspection; Go remains absent from Stage A artifacts; no promotion, deployment, or live action occurs.
