# Repository exploration — F3–F7 verification

Route: `f6f2495b4648`
Bound HEAD: `f07562eee1a33df74768e9fa4a3b074783d8c59e`
Branch: `feat/f3-f7-verification`
Role: read-only repository exploration; only this report was added

## Result

The current tree has one immediately reproducible repository-level failure:
the precommit architecture graph exits 1 with six declared conflicts and 26
F3–F7 implementation orphans. The Python and acceptance factories stop even
earlier in this routed worktree because they require an exactly clean HEAD and
the untracked change package makes the tree dirty. Gateway and web typechecks
cannot yet classify product code because their locked dependencies are not
installed (`tsc: not found`). Compose renders successfully once its required
immutable engine-commit variable is supplied.

The canonical fixture-only F3 path itself completed a safe local smoke probe:
capture package -> strict report build -> atomic publish -> offline bundle
verification. The resulting report was `SIMULATED`; report SHA-256 was
`705162ea5e76e926822ded927676568b0bfbeb1e77291d47b943d912dd988df6`.
This is characterization, not acceptance evidence: the probe used source-tree
imports and temporary files, and most canonical F3 behavior has no checked-in
test coverage.

No live source, facilitator, wallet, Mezo RPC, payment, deployment, migration,
or external write was invoked. The two route gates remain prerequisites:
`scope_and_design_approval` before implementation and
`migration_or_external_write_approval` before applying any migration or making
any external write.

## Exact observations

| Probe | Result | Classification |
| --- | --- | --- |
| `python3 tooling/run-adaptive-grok.py --check` | PASS; the initialized submodule matches its exact locked commit/tag/version | Tooling pin is healthy |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts` | Exit 1: 6 `DECLARED_CONFLICT`, 26 `IMPLEMENTATION_ORPHAN` | Reproducible repository/governance integration failure; not an environment failure |
| `python3 -B scripts/build-liqvera-python-distributions.py --source-sha HEAD --out /tmp/liqvera-f3f7-analysis-wheels` | Exit 1: `working tree is dirty`; no output produced | Workflow precondition: the active untracked change package makes the routed tree non-clean |
| `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run-mezo-acceptance.py --mode offline --output /tmp/liqvera-f3f7-analysis-acceptance.json` | Exit 2: clean-worktree requirement; no output produced | Same workflow precondition |
| `npm run --prefix apps/mezo-gateway typecheck` | Exit 127: `tsc: not found` | Environment/dependency acquisition; `apps/mezo-gateway/node_modules` is absent |
| `npm run --prefix apps/mezo-web typecheck` | Exit 127: `tsc: not found` | Environment/dependency acquisition; `apps/mezo-web/node_modules` is absent |
| `docker compose -f deploy/mezo-evidence/compose.yaml config --quiet` | Exit 1 because `LIQVERA_ENGINE_COMMIT` is required | Expected fail-closed environment requirement |
| `LIQVERA_ENGINE_COMMIT=$(git rev-parse HEAD) docker compose -f deploy/mezo-evidence/compose.yaml config --quiet` | PASS | Compose syntax/render closure is healthy with the required immutable input |
| focused `tests/evidence_report` plus `tests/installed/test_f3_mvp_demo_contract.py` | 15 passed | Existing legacy MVP tests are green |
| focused `tests/public_capture` | 19 passed | Public-capture package/boundary tests are green |
| canonical temporary fixture capture/build/publish/verify probe | PASS | Canonical F3 happy path works from source; installed-boundary and negative behavior remain unproved |

The graph failures cover these F3–F7 nodes: all five `artifact:liqvera-*`
nodes; evidence-report, gateway, protocol, web, and deployment configurations;
acceptance, evidence-runtime, and gateway-ledger contracts; the deployment and
F3–F7 documentation nodes; evidence capture/report services; factory,
local-demo, acceptance, gateway, protocol, and web runtimes; and
`test:liqvera-local-mvp`. The six declared conflicts are inherited graph
conflicts, but they are still emitted as blocking nodes by this command.

## Current F3–F7 surfaces and coverage

### F3 — capture and evidence report

Canonical implementation is present in:

- `packages/public-capture/src/mee_public_capture/evidence_capture.py`
- `packages/public-capture/src/mee_public_capture/evidence_package.py`
- `packages/public-capture/src/mee_public_capture/evidence_service.py`
- `packages/evidence-report/src/mee_evidence_report/evidence_io.py`
- `packages/evidence-report/src/mee_evidence_report/sealed_input.py`
- `packages/evidence-report/src/mee_evidence_report/report.py`
- `packages/evidence-report/src/mee_evidence_report/evidence_bundle.py`
- `packages/evidence-report/src/mee_evidence_report/schema_validation.py`
- `packages/evidence-report/src/mee_evidence_report/evidence_cli.py`
- `packages/evidence-report/src/mee_evidence_report/service.py`

The evidence-report distribution declares canonical build, verifier, service,
and demo entry points and includes schemas/resources. However,
`tests/evidence_report/` exercises the older fixture MVP modules
(`builder.py`, `bundle.py`, `cli.py`) rather than the canonical modules above.
The installed F3 test is also a static legacy-MVP contract. Public-capture
tests mainly cover its package model, installed boundary, and runtime package;
there is no full installed canonical capture-to-verifier test.

### F4/F5 — gateway, ledger, workers, and settlement

The gateway contains HTTP/config/security code, domain model/state logic,
artifact/report/contract/PostgreSQL/x402/Mezo-RPC adapters, and build,
reconciliation, retention, and scheduling workers under
`apps/mezo-gateway/src/`. Migration `001_ledger.sql` defines 11 tables,
including report requests, artifacts, quotes, payment attempts, chain events,
receipts, entitlements, delivery/reconciliation/audit events, and rate buckets,
plus queue indexes, constraints, and triggers.

`apps/mezo-gateway/package.json` has `build`, `typecheck`, `start`, and
`migrate`, but no test script. There are no gateway `*.test.ts` or `*.spec.ts`
files. No checked-in integration test currently proves schema application,
locking/concurrency, idempotency, artifact-loss handling, payment uncertainty,
crash recovery, or mocked settlement. The migration must not be applied until
the named gate is recorded, and then only to an isolated disposable local
database.

### F6 — browser and deployment

`apps/mezo-web/src/` contains API/contract/session/wallet/UI code. Its package
has `build`, `typecheck`, `dev`, and `preview`, but no test script and no
Playwright, Cypress, Vitest, or Jest surface. Browser cancellation, reload,
wrong-chain, paid/unpaid rendering, and fake-wallet flows are therefore not
currently executable as tests.

Deployment includes five Dockerfiles, Compose, Caddy/nginx configuration,
environment examples, secret guidance, and runbooks under
`deploy/mezo-evidence/`. Static Compose rendering passes with
`LIQVERA_ENGINE_COMMIT`. Images and a running stack were deliberately not
built/started: they mutate local Docker state, can require external base/package
downloads, and runtime network denial has not yet been established.

### F7 — acceptance

`tools/mezo_acceptance/` and `scripts/run-mezo-acceptance.py` provide the
A01–A30 inventory and a fail-closed command orchestrator. Five cases are live:
A07, A13, A14, A29, and A30. Offline mode correctly leaves them
`BLOCKED_EXTERNAL`.

There is no checked-in assertion plan or A01–A30 assertion-program suite.
`make liqvera-acceptance` does not pass `--plan`; after the worktree is clean it
will therefore record non-live cases as `NOT_RUN`, live cases as
`BLOCKED_EXTERNAL`, and return `INCOMPLETE`, not PASS. This is a verification
wiring gap, not an environment issue. Mocked lower-level F5/F6 tests must not
be relabeled as live A13/A14/A30 acceptance.

## Dependency-ordered verification commands

The following is the smallest safe order. Commands marked **gate** or
**acquisition/mutation** were not run by this exploration.

### 0. Bind identity and obtain a clean baseline

```bash
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git status --short
git submodule status -- tooling/adaptive-grok-build-pro
python3 tooling/run-adaptive-grok.py --check
```

Commit the approved change-package/spec step before factory execution; merely
creating the route package makes both the Python factory and acceptance runner
reject the worktree.

### 1. Frozen contracts, repository policy, and graph

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -p no:cacheprovider \
  tests/contracts tests/conformance -q
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/check-architecture-graph.py \
  --manifest-root architecture --phase precommit --allow-declared-conflicts
```

Stop on the graph failure. Its F3–F7 nodes need approved reverse paths; do not
hide them by weakening orphan/conflict policy.

### 2. Python factory and installed canonical F3 boundary

```bash
python3 -B scripts/build-liqvera-python-distributions.py \
  --source-sha "$(git rev-parse HEAD)" --out dist/liqvera/python
```

This command builds four project wheels and then uses `pip download` for exact
`jsonschema==4.23.0` and `referencing==0.35.1` runtime pins. It mutates the
output directory and may require registry reads if artifacts are not cached.
Afterward, inspect wheel metadata/resources and install all artifacts into an
isolated temporary environment. Run canonical entry points there with no
checkout packages on `PYTHONPATH`; then execute deterministic fixture
capture/build/verify/rebuild and tamper tests. Source-tree smoke alone is not
sufficient.

### 3. Protocol, gateway, then web compile closure

Use this dependency-explicit order (it adds standalone typecheck evidence to
the Makefile's `npm ci` -> protocol `tsc` -> package `build` sequence):

```bash
npm ci --ignore-scripts --prefix apps/mezo-gateway
apps/mezo-gateway/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
npm run --prefix apps/mezo-gateway typecheck
npm run --prefix apps/mezo-gateway build

npm ci --ignore-scripts --prefix apps/mezo-web
apps/mezo-web/node_modules/.bin/tsc -p packages/mezo-protocol/tsconfig.json
npm run --prefix apps/mezo-web typecheck
npm run --prefix apps/mezo-web build
```

The explicit `typecheck` lines should precede build for evidence clarity,
although each package build invokes TypeScript again. `npm ci` is
**acquisition/mutation** and was not run; use the committed lockfiles and a
verified cache or record dependency acquisition as blocked. A compile pass
only proves type/resource closure because neither application has tests.

### 4. Canonical F3 behavior

Add failing/characterization tests first, then run installed-wheel tests for:
fixture-only capture, canonical BUY/SELL report bytes, bundle reproduction,
tamper/path/symlink/size/duplicate rejection, atomic publication, duplicate
IDs, cleanup, service body/auth/deadline limits, and explicit rejection of
fixture-as-live. All external sockets must be denied. This phase provides the
stable artifact bytes/digests consumed by F4.

### 5. F4 database/gateway behavior — **gate**

After `migration_or_external_write_approval`, create a fresh disposable local
PostgreSQL instance, apply only:

```bash
npm run --prefix apps/mezo-gateway migrate
```

Then test schema constraints/triggers, scope isolation, idempotency conflicts,
20-way request/quote concurrency, leasing/restart, unpaid 402 response, and
artifact loss before payment. Inject report/artifact/payment ports and forbid
all external network. Do not use a shared or persistent database.

### 6. F5 mocked settlement

With the disposable database, inject in-process fake x402/RPC/finality ports.
Test invalid authorization, exact amount/network/asset/receiver, ambiguous and
lost responses, crash windows, expiry, replay, reconciliation, artifact loss,
and 20-way payment concurrency. Assert at most one fake settle call and never
turn `UNKNOWN` into a second settlement. Production identity/finality defaults
must remain unresolved and live calls disabled.

### 7. F6 browser and deployment shell

Run browser tests against a fake local API and injected fake wallet. Then
validate configuration before image construction:

```bash
LIQVERA_ENGINE_COMMIT="$(git rev-parse HEAD)" \
  docker compose -f deploy/mezo-evidence/compose.yaml config --quiet
```

Only after static/config/browser checks pass should a separately authorized
local fixture stack or image build run. `make liqvera-product` currently orders
`liqvera-images` before `liqvera-compose`; reverse that order so an invalid
configuration fails before costly/mutating image builds. Scan every Dockerfile
and Compose input with the pinned Trivy policy before declaring deployment
closure.

### 8. F7 offline acceptance

Create a reviewed plan that maps each offline A-case to a checked-in assertion
program and writes sanitized JSON evidence. Then run on a clean committed tree:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run-mezo-acceptance.py \
  --mode offline --plan <reviewed-offline-plan.json> \
  --output <new-result.json>
```

Do not use `--authorize-live`. A07/A13/A14/A29/A30 remain
`BLOCKED_EXTERNAL`; the expected offline acceptance outcome must explicitly
account for those blocked cases rather than claiming full A01–A30 PASS.

### 9. Repository verification and routed reviews

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/grok_verify.py --mode pr
```

Then run every route-selected independent review and record the required
verification, code, test, security, data, and release receipts against the
final unchanged fingerprint. Any later repository change makes the receipts
stale.

## Verification wiring defects to resolve first

1. The graph blocks `make verify` before tests and leaves all F3–F7 active
   implementation nodes orphaned.
2. `make verify-packages` omits `tests/evidence_report`, so even the existing
   15 MVP tests are not part of that target.
3. Gateway and web expose no test scripts or runtime test suites.
4. `make liqvera-acceptance` supplies no explicit plan and therefore cannot
   produce a PASS on a clean tree.
5. `make liqvera-product` builds Docker images before validating Compose.
6. The Python factory can require package-index access through `pip download`;
   offline reproducibility depends on a verified cache that is not expressed
   by the target.

These are distinct from the current environmental blockers (dirty route
package, absent Node installations, and missing Compose variable) and should
be repaired with separate regression evidence rather than one broad change.
