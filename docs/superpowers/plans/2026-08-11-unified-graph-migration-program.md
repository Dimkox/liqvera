# Unified Graph Migration Program Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the audited mixed repository into the owner-approved public-capture and read-only-analysis architecture without losing verified invariants, creating dual runtime owners, or admitting private/live capability.

**Architecture:** This program is the dependency and ownership map for four executable sub-plans. Each sub-plan produces independently reviewable software and immutable Claw evidence; later phases consume exact interfaces and receipts from earlier phases rather than relying on branch names or historical green runs.

**Tech Stack:** Python 3.12, independently installable PEP 621 distributions, PostgreSQL 16/17, Docker/OCI, GitHub Actions on self-hosted Claw only, JSON/YAML manifests, exact `Decimal`/`Fraction` arithmetic, unittest/pytest, Syft, Trivy.

## Global Constraints

- Governing specification: `docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md`, status `owner approved` at commit `a0cdbbf78a38f0bd429a45c810a5c34862a18ef1`.
- Stage A is public evidence and read-only analysis only; no live trading, signer, wallet, private/account stream, order, cancel, transfer, withdrawal, or dormant executor artifact.
- n8n, grid, DCA, Infinity Grid, maker-fill claims, Solana-chain runtime, and legacy live bots remain quarantined and runtime-unreachable.
- All test, validation, build, scan, and promotion receipts are produced only by `claw-engine-runner` / `[self-hosted, claw]`; GitHub-hosted runners are forbidden.
- Local commands are diagnostic only and never satisfy a release or merge receipt.
- Capture, analyzer, and contracts are separate installable distributions and top-level namespaces: `mee_public_capture`, `mee_readonly_analyzer`, and `mee_contracts`.
- The two legacy `multi_exchange_engine` package roots are migration inputs, never compatibility packages.
- Go is `TEST_ONLY_EXECUTABLE_SPEC`; it is excluded from every Stage A runtime/release artifact.
- Every task begins RED, reaches GREEN, runs graph/orphan checks, receives independent review, updates `handoff.md`, and commits one coherent slice.
- No task fabricates future receipts. Prospective evidence types are declarations; immutable receipts appear only after the applicable Claw phase succeeds.
- The dirty `/home/operator/app-stack` worktree is preserved and never reset, cleaned, synchronized, or used as a deployment source checkout.
- Deployment remains separately authorized and targets only Compose project `mee-a2`.

---

## Executable Sub-Plans

1. `docs/superpowers/plans/2026-08-11-m0-m3-canonical-distributions-and-graph.md`
   - M0 authority manifests, conflict graph, checker, and Claw-only policy;
   - M1 canonical distributions and bounded PR #21 salvage;
   - M2 Go conformance;
   - M3 installed-wheel/image capability proof;
   - M7 per-owner retirement eligibility.
2. `docs/superpowers/plans/2026-08-11-m4-evidence-runs-and-frozen-data.md`
   - causal PostgreSQL graph, constrained writers, terminalization;
   - deterministic read-only views, semantic frozen packages, analysis replay;
   - PostgreSQL 16/17 role, race, retention, and reader gates.
3. `docs/superpowers/plans/2026-08-11-m5-stage-a-v2-strategy-economics.md`
   - exact identity, reconstruction, VWAP, costs, episodes, capital, delays;
   - basis convergence, realized funding, diagnostic paired-basis trailing;
   - deterministic portfolio, decision, report, replay, and quarantine.
4. `docs/superpowers/plans/2026-08-11-m6-claw-release-and-mee-a2-deployment.md`
   - Task 1 bootstraps disposable exact-SHA Claw validation immediately after
     M0 policy and before any M1-M5 receipt-producing gate;
   - connected release receipt, artifact/SBOM/scan/promotion identities;
   - immutable app-stack materialization, `mee-a2`-only deployment and rollback.

## Program Interfaces

**Consumes:**

- approved requirement IDs `PROD-*`, `ARCH-*`, `ARCH-GO-*`, `DATA-*`, `STRAT-*`, `GRAPH-*`, `CI-*`, `SEC-*`, and `OPS-*`;
- audited engine base `dd8e0f2a30ec3d58dba51bd31ecff988af41cf99`;
- PR #21 provenance head `7fe6918690f8bc1da5826c67e3619de4126e4f54` without whole-branch merge;
- audited app-stack base `7756d546ecff7826cb11c8c74d45929913944b7e`;
- app-stack DB-contract candidate `3ce7e1f33ad34663b123c9b1cb225be8767e97cf` or independently proven equivalent.

**Produces:**

- one canonical owner per active runtime/domain concept;
- separately installable and inspectable contracts, capture, and analyzer artifacts;
- sealed `CaptureRun`, verified `FrozenPackageReceipt`, sealed `AnalysisRun`, and immutable `RetentionAction` evidence roots;
- deterministic Stage-A-v2 report and one of `INVALID_DATASET`, `INSUFFICIENT_EVIDENCE`, `STOP`, or `EXTEND_LONGER_SHADOW`;
- exact-SHA Claw receipts and a connected release/deployment/rollback graph.

## Requirement Coverage Matrix

| Requirements | Owning executable plan/tasks | Verification owner |
|---|---|---|
| `PROD-001`, `PROD-002`, `PROD-003`, `PROD-004`, `PROD-005`, `PROD-006`, `PROD-007`, `PROD-008`, `PROD-009`, `PROD-010`, `PROD-011`, `PROD-012`, `PROD-013` | M5 Tasks 1–13; the M6 manual execution checklist consumes only the resulting typed decision and cannot reinterpret it | trader/quant reviewer plus product reviewer |
| `PROD-014`, `GRAPH-012` | M5 Task 13 creates explicit unsupported Hypothesis nodes with `falsified_by` edges and proves they cannot reach the Stage A Outcome, release artifact, or deployment gate | product reviewer plus graph-contract reviewer |
| `ARCH-001`, `ARCH-002`, `ARCH-003`, `ARCH-004`, `ARCH-005`, `ARCH-006`, `ARCH-007`, `ARCH-008`, `ARCH-009` | M0–M3 Tasks 1–8; M4 Tasks 1, 5, 6; M6 Tasks 1–3 | architecture reviewer plus artifact-boundary security reviewer |
| `ARCH-GO-001`, `ARCH-GO-002`, `ARCH-GO-003`, `ARCH-GO-004`, `ARCH-GO-005` | M0–M3 Tasks 1, 2, 7–9 | Go/Python conformance reviewer |
| `DATA-001`, `DATA-002`, `DATA-003`, `DATA-004`, `DATA-005`, `DATA-006`, `DATA-007`, `DATA-008`, `DATA-009`, `DATA-010`, `DATA-011`, `DATA-012`, `DATA-013`, `DATA-014`, `DATA-015`, `DATA-016`, `DATA-017`, `DATA-018`, `DATA-019`, `DATA-020`, `DATA-021`, `DATA-022`, `DATA-023`, `DATA-024`, `DATA-025` | M4 Tasks 1–8; M5 Tasks 1–4 and 12 consume immutable M4 contracts | data/PostgreSQL reviewer plus deterministic-replay reviewer |
| `STRAT-001`, `STRAT-002`, `STRAT-003`, `STRAT-004`, `STRAT-005`, `STRAT-006`, `STRAT-007`, `STRAT-008`, `STRAT-009`, `STRAT-010` | M5 Tasks 1, 4–13 | trader/quant reviewer plus independent model reviewer |
| `GRAPH-001`, `GRAPH-002`, `GRAPH-003`, `GRAPH-004`, `GRAPH-005`, `GRAPH-006`, `GRAPH-007`, `GRAPH-008`, `GRAPH-009`, `GRAPH-010`, `GRAPH-011`, `GRAPH-012` | M0–M3 Tasks 1–2 and 9; M4 Tasks 1–8; M6 Tasks 1–3 | graph/governance reviewer |
| `CI-001`, `CI-002`, `CI-003`, `CI-004`, `CI-005`, `CI-006`, `CI-007`, `CI-008` | M0–M3 Task 2; M4 Task 8; M6 Tasks 1–3 | DevOps/SRE plus security reviewer |
| `SEC-001`, `SEC-002`, `SEC-003`, `SEC-004`, `SEC-005`, `SEC-006`, `SEC-007` | M0–M3 Tasks 3–8; M4 Tasks 4–6; M5 Task 13; M6 Tasks 1–3 | independent security reviewer |
| `OPS-001`, `OPS-002`, `OPS-003`, `OPS-004`, `OPS-005`, `OPS-006`, `OPS-007`, `OPS-008` | M6 Tasks 3–5 plus the manual release/deployment execution checklist | app-stack SRE and database-contract reviewer; release and deployment require distinct named human approvals |

## Program Dependency DAG

```text
M0 approval/manifests/conflicts
  -> M0 graph checker
  -> M0 Claw-only PR policy
  -> M6 Task 1 trusted exact-SHA disposable controller
  -> M1 mee_contracts
       -> M1 mee_public_capture
       -> M1 mee_readonly_analyzer + bounded PR21 salvage
            -> M1 remove both legacy package roots
            -> M2 Go conformance
            -> M3 installed wheel/image boundary proof
                 -> M4 evidence roots + writer/seal contract
                 -> M4 deterministic readers/frozen validation/replay
                      -> M5 exact economics/strategies/decision
                           -> M6 Tasks 2-5 connected release graph
                                -> app-stack DB contract
                                -> app-stack immutable deploy contract
                                -> explicit human authorization
                                -> mee-a2-only deploy/observe/rollback receipt
                                     -> M7 bounded owner retirement
```

No edge may be bypassed. Parallel development is allowed only where the
sub-plan declares immutable consumed interfaces and separate file ownership.

### Task 1: Freeze program state and changed-node ownership

**Files:**

- Modify: `handoff.md`
- Create: the four executable sub-plans listed above

**Interfaces:**

- Consumes: approved architecture commit `a0cdbbf78a38f0bd429a45c810a5c34862a18ef1`.
- Produces: a versioned planning graph whose every executable task has owner, verifier, inputs, outputs, RED/GREEN gate, commit, and rollback.

- [ ] **Step 1: Verify exact planning base**

```bash
test "$(git rev-parse HEAD)" = "a0cdbbf78a38f0bd429a45c810a5c34862a18ef1"
test -z "$(git status --porcelain)"
```

Expected: both commands exit `0` before plan files are created.

- [ ] **Step 2: Validate the four plan paths and mandatory header**

```python
from pathlib import Path

PLAN_NAMES = (
    "2026-08-11-m0-m3-canonical-distributions-and-graph.md",
    "2026-08-11-m4-evidence-runs-and-frozen-data.md",
    "2026-08-11-m5-stage-a-v2-strategy-economics.md",
    "2026-08-11-m6-claw-release-and-mee-a2-deployment.md",
)
root = Path("docs/superpowers/plans")
for name in PLAN_NAMES:
    text = (root / name).read_text(encoding="utf-8")
    assert "# " in text.splitlines()[0]
    assert "> **For agentic workers:**" in text
    assert "## Global Constraints" in text
    assert "**Interfaces:**" in text
    assert "Run:" in text or "```bash" in text
```

Expected before all four files exist: failure naming the missing plan. Expected after authoring: exit `0`.

- [ ] **Step 3: Reject placeholders and forbidden release shortcuts**

```bash
python - <<'PY'
from pathlib import Path

files = sorted(Path("docs/superpowers/plans").glob("2026-08-11-*.md"))
forbidden = ("T" + "BD", "TO" + "DO", "implement " + "later", "fill in " + "details", "REPLACE" + "_WITH")
for path in files:
    text = path.read_text(encoding="utf-8")
    hits = [token for token in forbidden if token in text]
    if hits:
        raise SystemExit(f"{path}: forbidden plan tokens {hits}")
PY
```

Expected: exit `0`. References explaining removal of the current hosted runner use the exact phrase `GitHub-hosted runner` instead of embedding an allowed-looking runner value.

- [ ] **Step 4: Verify requirement coverage**

```bash
python - <<'PY'
import re
from pathlib import Path

spec = Path("docs/superpowers/specs/2026-08-11-unified-strategy-evidence-graph-design.md").read_text(encoding="utf-8")
owned_names = {
    "2026-08-11-unified-graph-migration-program.md",
    "2026-08-11-m0-m3-canonical-distributions-and-graph.md",
    "2026-08-11-m4-evidence-runs-and-frozen-data.md",
    "2026-08-11-m5-stage-a-v2-strategy-economics.md",
    "2026-08-11-m6-claw-release-and-mee-a2-deployment.md",
}
plans = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted(Path("docs/superpowers/plans").iterdir())
    if path.name in owned_names
)
required = set(re.findall(r"\*\*([A-Z]+(?:-[A-Z]+)?-\d{3}):\*\*", spec))
missing = sorted(requirement for requirement in required if requirement not in plans)
if missing:
    raise SystemExit("requirements missing from executable plans: " + ", ".join(missing))
print(f"covered={len(required)}")
PY
```

Expected: `covered=98`.

- [ ] **Step 5: Update handoff and commit the plan checkpoint**

```bash
git add docs/superpowers/plans/2026-08-11-*.md handoff.md
git diff --cached --check
git commit -m "docs: plan unified graph migration"
```

Expected: one documentation-only commit; `git status --porcelain` is empty afterward.

### Task 2: Execute sub-plans through phase gates

**Files:**

- Modify: only the files owned by the currently executing sub-plan task.
- Verify: `architecture/**`, task-focused tests, trusted Claw workflow receipt, `handoff.md`.

**Interfaces:**

- Consumes: the exact prior task commit and its phase-applicable receipts.
- Produces: one reviewable commit and the prospective/realized graph edges declared by that task.

- [ ] **Step 1: Select the first uncompleted DAG node**

```bash
python scripts/check-architecture-graph.py --phase precommit --format json
```

Expected after M0 checker exists: deterministic diagnostics identify the first blocked owner/conflict path. Before the checker exists, begin only with M0 Task 1 from the canonical-distributions plan.

- [ ] **Step 2: Run the task's focused RED on Claw**

Use the exact command and expected diagnostic stated by the selected sub-plan task. A missing expected failure blocks implementation because the test is not proving the intended contract.

- [ ] **Step 3: Implement only the selected task and reach GREEN**

Use the exact code, migration, workflow, or manifest steps in that task. Do not start a neighboring DAG node in the same commit.

- [ ] **Step 4: Run changed-node closure and independent review**

```bash
python scripts/check-architecture-graph.py --phase precommit --format text
git diff --check
```

Expected: no changed-node orphan, cycle, expired migration, dual owner, unresolved semantic conflict, or phase-applicable missing receipt. A reviewer other than the implementer records the verification result.

- [ ] **Step 5: Update handoff and use the selected task's literal commit block**

Run the selected sub-plan task's explicit `git add` and `git commit` commands
without adding neighboring-task paths. Then run:

```bash
git status --porcelain
git show --stat --oneline HEAD
```

Expected: status is empty and the commit contains one independently rejectable
deliverable plus its `handoff.md` update.

## Program Stop Conditions

Stop the affected branch, keep its conflict node blocking, and continue only on
independent DAG nodes when any of these occurs:

- a semantic parameter has more than one valid meaning and lacks owner approval;
- full-depth or mapping evidence is incomplete but code attempts a fallback;
- a workflow needs a GitHub-hosted runner, host Docker socket, production route,
  registry credential, deployment authority, private API, or live-trading capability;
- a migration cannot preserve sealed evidence or deterministic reader parity;
- an artifact contains the other application's code or any execution/private capability;
- the graph checker would need to invent ownership or fabricate a future receipt;
- app-stack exact SHA, PR ancestry, DB-contract equivalence, or explicit deployment authorization is missing.

These are typed blockers, not permission to weaken the contract.
