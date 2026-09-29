# Documentation and acceptance-evidence audit — F3–F7 verification

Analysis only. This report is not a verification receipt, does not approve either
human gate, and records no live request, payment, deployment, release, migration,
or external write.

## Source identity and scope

- Route: `f6f2495b4648`.
- Change: `20260929-f3-f7-verification-and-defect-repair-f6f249`.
- Inspected branch: `feat/f3-f7-verification`.
- Inspected HEAD: `f07562eee1a33df74768e9fa4a3b074783d8c59e`.
- Inspected Git tree: `a1df248d000718c28c565d1d5b11bd425f83a055`.
- The only worktree dirt at inspection time was the untracked active change
  package. This matters because the acceptance runner refuses any dirty tree.
- No web research was needed. The repository, canonical specification, source,
  tests, manifests, prior evidence, and route package were sufficient.

The review reconciled `README.md`, `handoff.md`,
`docs/planning/LIQVERA_FACTORY_TZ.md`, `docs/ROADMAP.md`, the original
`engineering/changes/2026-09-24-mezo-evidence/` tasks and acceptance matrix,
the active change package, the current source/test tree, Make targets, Compose,
the 156-vector inventory, and the A01–A30 runner/result schema.

## Conclusion

The integrated tree contains substantial F3–F7 implementation, but the current
documentation correctly stops short of claiming it is verified. The proper
status remains **IMPLEMENTED_UNVERIFIED**. The offline phase can verify a large
subset and repair defects, but it cannot close canonical F7 or the specification's
Definition of Done because A13/A14 require a separately approved real testnet
payment and repeat retrieval.

Four evidence defects must be resolved before an offline result is credible:

1. There is no committed acceptance plan or assertion-program suite. Running the
   documented `make liqvera-acceptance` therefore executes zero assertions.
2. The acceptance-result schema requires 64-character values for `commit` and
   `tree`, while the runner emits the repository's actual 40-character SHA-1 Git
   OIDs. A generated result cannot validate against its own canonical schema.
3. The canonical F3 modules, gateway, web application, browser behavior, and
   PostgreSQL/fault paths have little or no direct automated coverage. Builds and
   typechecks cannot substitute for the required behavior evidence.
4. The runner has only a single all-30 overall status. In offline mode it correctly
   leaves live cases blocked, then necessarily emits `INCOMPLETE` and exits 1.
   The route therefore needs a distinct, explicit definition of success for the
   authorized offline subset without relabeling the canonical all-30 result as
   `PASS`.

## Reconciled implementation state

| Area | Present in the integrated tree | Evidence actually present | Defensible status |
| --- | --- | --- | --- |
| F3 canonical evidence runtime | Canonical capture/report/bundle/verifier/service modules, schemas, CLI surfaces, and images are present | Tests cover only the earlier MVP builder/CLI plus one installed MVP demo contract; no direct canonical-runtime suite was found | `IMPLEMENTED_UNVERIFIED` |
| F4 API and ledger | Express gateway, PostgreSQL migration, quote/capability boundaries, artifact adapters, workers, and routes are present | No gateway unit or integration tests; package scripts expose build/typecheck/start/migrate only | `IMPLEMENTED_UNVERIFIED` |
| F5 settlement | x402 boundary, verify/settle/reconciliation code, state resources, and fail-closed readiness are present | No mocked replay, timeout, crash, duplicate, or unknown-settlement test suite; no live evidence | `IMPLEMENTED_UNVERIFIED`, payment disabled |
| F6 UI and operations | Vite UI, five Liqvera Dockerfiles, isolated fixture/live Compose profiles, Caddy/nginx, secrets convention, and runbooks are present | No TypeScript test files, browser-test script, or retained Compose/runtime evidence | `IMPLEMENTED_UNVERIFIED` |
| F7 acceptance | A01–A30 inventory, fail-closed runner, and result schema are present | No plan/assertion programs; all vectors remain `NOT_RUN`; prior matrix contains only historical F1 evidence | `NOT_RUN` / `INCOMPLETE` |

The repository boundary cleanup did produce useful repository-level evidence:
`1134 passed, 85 subtests`, measured coverage 36.16%, and a recurring Trivy gate
that discovered nine tracked container inputs and passed the blocking
`MEDIUM,HIGH,CRITICAL` threshold. That evidence does **not** verify F3–F7
behavior. Its change package is also still `ready` with all five final receipt
obligations recorded `not_run` after transition-only changes made the previous
receipts stale. Keep that inherited governance debt distinct from this route's
new evidence.

## Exact stale, ambiguous, or status-sensitive documentation

### `README.md`

1. Lines 21–31 correctly say F3–F7 are implemented but unverified and all 156
   vectors are `NOT_RUN`. Preserve that until fingerprint-bound execution proves
   otherwise.
2. Line 31 says the inherited Trivy policy gate "remains open", and lines 33–39
   foreground the historical F1 failure on two LOW `DS-0026` findings. That is
   stale as a statement of the current recurring policy gate: the cleanup route
   later passed all nine tracked inputs at `MEDIUM,HIGH,CRITICAL`; LOW DS-0026 is
   retained debt, not the current blocking PR threshold. Keep the old result only
   as labeled F1 history.
3. Lines 128–131 mix F1-era clean-machine/image status with the current product
   tree. Move or label them as historical.
4. Lines 133–146 list Liqvera targets and truthfully say they had not been run in
   the code-completion phase. Once this route executes them, replace the blanket
   statement with exact final-tree commands, outcomes, and evidence links. Do not
   retain "not run" after a successful current run or imply success from an old
   tree.
5. The example at line 141 invokes `make liqvera-acceptance` without a plan. The
   target passes no `--plan`, so it produces 25 `NOT_RUN`, five
   `BLOCKED_EXTERNAL`, `overall_status=INCOMPLETE`, and exit 1. The example is an
   honest inventory command, not an acceptance command; label it that way or
   make a separate planned offline target.
6. Lines 186–192 say "Payments and live verification are not implemented." This
   is true for the local `/demo/*` prototype, but ambiguous globally because F5
   settlement code exists. Scope the sentence explicitly to the two local demos:
   the product settlement implementation exists but is unverified and disabled.
7. "The interactive implementation is factory-bound" at line 191 is vague after
   factory/tooling externalization. Prefer a concrete statement that the local
   demo is represented by project-owned Make/package/graph surfaces; it has no
   factory approval or receipt.

### `handoff.md`

1. Lines 3–4 name 2026-09-28 and branch `chore/repository-cleanup`. The current
   branch is `feat/f3-f7-verification` at the HEAD above. The handoff needs a new
   top current-state section; the cleanup narrative can remain historical below.
2. Lines 17–26 and 88–96 accurately describe cleanup verification and the later
   stale-receipt condition. Do not claim the cleanup package is closed; its
   `state.json` still records final receipt obligations as `not_run`.
3. Lines 98–100 and 102–162 are the useful current F3–F7 baseline. Preserve the
   fail-closed payment and `IMPLEMENTED_UNVERIFIED` language until this route has
   current evidence.
4. Lines 147–150 are historical for the code-completion integration. After this
   phase, label the paragraph with its old commit/date rather than leaving it as
   the reader's apparent current status.
5. Lines 158, 215–218, and the "Active blockers" item at 377–382 continue to call
   Trivy an inherited blocker. Reconcile them with the current severity policy:
   LOW DS-0026 remains visible debt; it is not a failing
   `MEDIUM,HIGH,CRITICAL` gate unless policy is explicitly changed again.
6. Historical F1/F2 command tables and review summaries are useful provenance,
   but they are not current F3–F7 receipts. Keep them under clearly historical
   headings and add final-tree evidence separately.

### Canonical specification and roadmap

1. `docs/planning/LIQVERA_FACTORY_TZ.md:23` says F1 is the current next stage.
   Actual state is F1 complete-with-blockers, F2 static contracts complete, and
   F3–F7 implemented/unverified with verification/repair next.
2. The target-area caveat at `LIQVERA_FACTORY_TZ.md:97` says the listed areas are
   not a claim they exist. They now exist. Preserve this as specification-era
   context or add an implementation-status note; do not rewrite requirements as
   if their acceptance were proven.
3. Section 15 (A01–A30), section 16 stage exits, and section 18 Definition of Done
   remain authoritative. In particular, lines 295 and 328 prohibit treating
   mocked settlement or an offline subset as A13/F7 completion.
4. Section 19 at line 338 is a bootstrap instruction to create the 2026-09-24
   package and start with the public copy/F1 baseline. That work already exists.
   Recast it as historical execution provenance or replace its "current action"
   with the active change package and route; never delete the original package.
5. `docs/ROADMAP.md:3` says F1 baseline verification is next. This is stale and
   should point to the current F3–F7 verification/repair phase while retaining
   F1/F2 history.

### Original tasks and acceptance matrix

1. `engineering/changes/2026-09-24-mezo-evidence/tasks.md:75–136` is presently
   accurate: implementation boxes are checked, canonical F3 execution, F4
   integration/fault tests, F5 mocked faults, F6 browser tests, and F7 execution
   are unchecked. Update boxes only from retained current-tree evidence, and add
   links to this route rather than overwriting the historical narrative.
2. The statement at lines 133–136 that no build/test/graph/container/browser/
   acceptance ran belongs to the original code-completion commit. Date or
   fingerprint it once this route runs checks.
3. `acceptance-matrix.md` explicitly says its A01 and A27 passes are F1-only. Do
   not copy those PASS values into F7. Add a current-run column or a superseding
   fingerprint-bound matrix. A01 and A27 must be re-executed on the final tree.
4. The matrix's F1 Trivy wording is historical. It should not be used as current
   verifier status.

## Concrete evidence and contract gaps

### Vector evidence

`schemas/mezo-evidence/v1/vectors.json` contains exactly 156 vectors and all 156
have `runtime_status=NOT_RUN`. Current acceptance bindings are:

`A02:1, A03:3, A04:55, A05:24, A06:8, A07:1, A10:2, A11:16, A12:1,
A14:12, A15:8, A16:8, A17:6, A18:1, A19:2, A20:3, A21:13, A22:2,
A24:12`.

No vector binds A01, A08, A09, A13, A23, A25–A30. Those cases require separate
assertions and evidence. A vector file being schema-valid is not runtime evidence.
Avoid manually turning source fixtures green: produce a fingerprint-bound result
ledger keyed by every vector ID, or explicitly approve another authority model.

### Test coverage

- `tests/evidence_report/` contains only `test_mvp_builder.py` and
  `test_mvp_cli.py`; the installed suite has only the MVP demo contract.
- Canonical modules such as `evidence_bundle.py`, `evidence_cli.py`,
  `evidence_io.py`, `report.py`, `schema_validation.py`, `sealed_input.py`, and
  `service.py` have no direct suite in the current tree.
- No `*.test.*` or `*.spec.*` source was found in the gateway, web app, or protocol
  package.
- Gateway scripts provide only `build`, `typecheck`, `start`, and `migrate`.
  Web scripts provide only `dev`, `build`, `typecheck`, and `preview`.
- `make verify` excludes `tests/evidence_report` and all TypeScript, PostgreSQL,
  Compose, browser, and acceptance checks. It is a Stage A regression gate, not
  a Liqvera product verification gate.

### Acceptance runner

- No `liqvera-acceptance-plan/v1` file or assertion suite exists in the tree.
- Without `--plan`, the runner executes nothing. In offline mode A07, A13, A14,
  A29, and A30 are automatically `BLOCKED_EXTERNAL`; the remaining 25 are
  `NOT_RUN`.
- A07 (unavailable-source fail-closed behavior) and A30 (wallet/UI recovery) both
  have valuable deterministic offline/mocked forms, even though the inventory
  currently marks the whole case live. Preserve the actual live acceptance
  boundary, but add offline fault/browser coverage or revise the classification
  through a reviewed contract change. Do not claim the mocked form is the live
  case.
- A14 is correctly dependent on passing A13 in the runner. Its mocked
  no-second-settlement fault test is useful F5 evidence but cannot make canonical
  A14 PASS.
- `runner.py:246–258` assigns `PASS` only if every case passes; any blocked or
  omitted case yields `INCOMPLETE` and exit 1. An offline route needs an explicit
  subset verdict while keeping the canonical result incomplete.
- `acceptance-result.schema.json` reuses a `sha256` definition for repository
  `commit` and `tree` and requires 64 lowercase hex characters. `runner.py:56–57`
  writes `git rev-parse HEAD` and `HEAD^{tree}`; both are 40 characters in this
  repository. Repair and regression-test this self-incompatibility before
  retaining any generated result.

### Build and Compose evidence

- `make liqvera-python`, `make liqvera-gateway`, `make liqvera-web`,
  `make liqvera-images`, and `make liqvera-compose` are present but have no
  current retained result.
- `make liqvera-images` is not a strict air-gapped build: Dockerfiles perform
  `npm ci` and `pip wheel` dependency resolution and require base images/cache.
  State whether "offline" means no product/live-service calls (the practical
  route scope) or a fully network-disconnected build. If strict air-gap is a
  requirement, the current build needs a preloaded dependency/base-image design.
- Compose correctly separates `fixture` and `live` profiles and internal
  networks, but static config is not proof of runtime isolation. Fixture-only
  container probes are required; the live profile must not be started in this
  route.

### Active change package

The active package is still a template: `success_metric` and `target` are
`UNKNOWN`; acceptance criteria, invariants, forbidden outcomes, required
approval scopes, architecture, test plan, rollback triggers, and release
go/no-go criteria are empty. All six required evidence obligations are
`not_run`. Fill and approve the typed contract before implementation; this report
does not satisfy `scope_and_design_approval` or
`migration_or_external_write_approval`.

## Recommended acceptance criteria for this offline route

These criteria deliberately stop short of F7 completion.

1. **Frozen safety boundary.** No command uses `--authorize-live`, the live
   Compose profile, a funded wallet, facilitator/RPC settlement, deployment,
   release, production database, or exchange mutation. Payment readiness remains
   false unless a later separately approved route changes it.
2. **Stage A regression.** `make verify`, the complete configured Python suite,
   graph check, artifact boundary, and tooling trust check pass on the final tree.
   The existing `INSUFFICIENT_EVIDENCE`/no-`GO` behavior remains unchanged.
3. **F3 canonical behavior.** Direct tests execute deterministic capture,
   schema/identity rejection, exact BUY/SELL reports, bounded deterministic
   bundle creation, tamper/traversal/bomb rejection, clean offline replay,
   publication atomicity, service time/body/concurrency limits, and installed
   entry points. The suite covers canonical modules, not just the local MVP.
4. **F4 real-PostgreSQL behavior.** Against an ephemeral fixture database,
   migrations apply from empty and are safe on rerun; quote/idempotency,
   capability scope, unpaid 402/no paid body, 20-way concurrency, body conflict,
   artifact missing/corrupt, retention/reconciliation, and transaction rollback
   are proven. The gateway remains the only ledger writer.
5. **F5 mocked fault behavior.** Deterministic adapters prove wrong
   chain/token/amount/receiver/payer, expiry/reuse, verify/settle timeout,
   settle unknown, crash windows, lost response, duplicate attempt, ambiguous
   transfer, and expiry during settlement. Assertions include call counts proving
   at most one settlement and no paid-body leak. No mocked result is recorded as
   A13 or canonical A14 PASS.
6. **F6 browser and operations.** Typecheck/build plus a browser suite cover
   wallet cancel, switch, reload/recovery, wrong chain, unknown outcome, no
   automatic retry, session capability handling, CSP/CORS/cache headers, and no
   secret/payment material in logs or bundles. Fixture Compose config/build/start
   demonstrates non-root/read-only/cap-drop and network/environment isolation.
7. **All vector outcomes accounted for.** Each of the 156 IDs has an executed
   result, expected/actual comparison, command, final-tree identity, and retained
   digest. No vector remains silently `NOT_RUN`; failures remain failures.
8. **Acceptance contract is executable.** A committed offline plan and assertion
   suite cover every case that is authorized offline. Runner output validates
   against the repaired result schema. The offline-subset verifier accepts only
   the exact expected PASS/BLOCKED partition and rejects any NOT_RUN/FAIL in the
   offline subset.
9. **Honest all-30 status.** The canonical A01–A30 artifact remains
   `INCOMPLETE`, with A13/A14 and any genuinely external-only cases explicitly
   `BLOCKED_EXTERNAL`. F7, payment, release, and Definition of Done remain open.
10. **Current documentation.** README, handoff, roadmap, original tasks, and a
    superseding/current acceptance matrix all name the same final SHA/tree,
    distinguish historical evidence from current evidence, report exact omitted
    cases, and link the route reports/receipts.
11. **Independent evidence.** Required verification, code, test, security, data,
    and release reviews pass against one final fingerprint after all reports are
    persisted. A later repository change makes those receipts stale and requires
    rerun.

## Recommended command sequence

The implementation owner should make these commands real and stable. Commands
marked “new target” describe a required test surface that does not exist yet;
they are not claims about the current tree.

### 1. Identity and dependency locks

```bash
git status --short
git rev-parse HEAD HEAD^{tree}
git submodule status --cached tooling/adaptive-grok-build-pro
python3 tooling/run-adaptive-grok.py --check
```

Run acceptance only after the package and implementation are committed and
`git status --short` is empty.

### 2. Stage A and complete Python checks

```bash
PATH="$PWD/.venv/bin:$PATH" make graph
PATH="$PWD/.venv/bin:$PATH" make verify
PATH="$PWD/.venv/bin:$PATH" make verify-tooling
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest -q
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/evidence_report -q
PATH="$PWD/.venv/bin:$PATH" python -B -m ruff check packages tests tools scripts
PATH="$PWD/.venv/bin:$PATH" python -B -m mypy
PATH="$PWD/.venv/bin:$PATH" make liqvera-python
```

The current `tests/evidence_report` command is only an MVP check; it becomes F3
evidence only after the canonical-runtime scenarios above are added.

### 3. TypeScript build and tests

For a cache-backed network-disconnected dependency install:

```bash
npm ci --ignore-scripts --offline --prefix apps/mezo-gateway
apps/mezo-gateway/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
npm run --prefix apps/mezo-gateway typecheck
npm run --prefix apps/mezo-gateway build
npm ci --ignore-scripts --offline --prefix apps/mezo-web
apps/mezo-web/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
npm run --prefix apps/mezo-web typecheck
npm run --prefix apps/mezo-web build
```

Then add and run stable scripts (new targets):

```bash
npm test --prefix apps/mezo-gateway
npm run --prefix apps/mezo-gateway test:integration
npm test --prefix apps/mezo-web
npm run --prefix apps/mezo-web test:browser
```

If the npm cache is not prepopulated, `--offline` must fail rather than silently
contacting a registry. A separately disclosed dependency-fetch step is not
product/live acceptance.

### 4. Fixture-only PostgreSQL and Compose

Static rendering, never the live profile:

```bash
LIQVERA_ENGINE_COMMIT="$(git rev-parse HEAD)" \
  docker compose -f deploy/mezo-evidence/compose.yaml --profile fixture config --quiet
```

The route should add one fixture integration target that provisions only
test-local secret files and an ephemeral project/volume namespace, starts
`--profile fixture`, runs health/network/environment/artifact probes, and always
tears that namespace down. Do not use `--profile live`, live env files, or real
credentials. A suitable stable interface is:

```bash
make liqvera-fixture-integration
```

This is a new target; its implementation must make cleanup bounded and must not
reuse operator or production volumes.

### 5. Planned offline acceptance

Commit a plan and assertion programs at stable paths, for example
`tests/acceptance/offline-plan.json` and `tests/acceptance/assertions/`. Then run
from a clean committed tree with output outside the repository:

```bash
acceptance_dir="$(mktemp -d)"
PATH="$PWD/.venv/bin:$PATH" python3 -B scripts/run-mezo-acceptance.py \
  --mode offline \
  --plan tests/acceptance/offline-plan.json \
  --output "$acceptance_dir/result.json"
```

Under the current all-30 semantics this is expected to exit 1 with
`overall_status=INCOMPLETE` because live cases remain blocked. Add a separate
offline-subset validator (new target) and run it against the retained result:

```bash
PATH="$PWD/.venv/bin:$PATH" python3 -B scripts/verify-mezo-offline-acceptance.py \
  "$acceptance_dir/result.json"
```

That validator may exit 0 only when every authorized offline case passed, the
external-only set is exactly the reviewed blocked set, there are no offline
`NOT_RUN`/`FAIL` rows, evidence files and hashes exist, and the result validates
against the schema. It must not rewrite `overall_status` or call F7 complete.

### 6. Final route verification and reviews

After persisting all implementation and review reports, and again after any
subsequent repository change:

```bash
PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record
git diff --check
git status --short
git rev-parse HEAD HEAD^{tree}
```

Record the route-selected verification, code review, test review, security
review, data review, and release review receipts only when each report and the
verification result bind to the same final fingerprint.

## Required documentation handoff after verification

When evidence exists, update documentation in this order:

1. Add a current acceptance matrix bound to final SHA/tree; preserve the old
   F1 matrix as historical evidence.
2. Check only the original task boxes actually satisfied and link this route's
   evidence.
3. Update `README.md` with current commands/results, the precise offline/live
   boundary, and the repaired Trivy wording.
4. Put the current route/branch/fingerprint and next action at the top of
   `handoff.md`; move cleanup and F1/F2 narratives under dated history.
5. Update the canonical specification's status/bootstrap notes and
   `docs/ROADMAP.md` without weakening A01–A30 or the Definition of Done.

The truthful end state for a successful route is: **F3–F6 offline-verified to
the documented extent; offline F7 subset passed; canonical A01–A30/F7 remains
INCOMPLETE pending separately authorized external/testnet cases.**
