# Task analysis — repository boundary cleanup

Route: `7f0f98e3cdda`
Base commit: `0c2cb97f8048f7da8bd193634f4502f24b0e541e`
Analysis role: `task_analyst` (read-only except this report)
Date: 2026-09-28

## Executive ruling

Treat this as two repository-boundary retirements, not as a Liqvera feature or
runtime migration:

1. remove the inherited Go Stage-0 implementation from the active checkout
   while retaining its provenance and the Python safety/conformance tests that
   carry forward its useful invariants; and
2. replace copied Grok/BMad implementation payloads with a small, project-owned
   integration that identifies an immutable upstream revision and verifies it
   before use.

This change must not alter Liqvera runtime behavior, API/event/data contracts,
database migrations, settlement configuration, acceptance results, or release
authority. F3-F7 remain exactly `IMPLEMENTED_UNVERIFIED`; all 156 vectors remain
`NOT_RUN`; A13-A14 remain `BLOCKED_EXTERNAL`; payment readiness remains false
with at least `PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED`; and shadow-only
remains the safety default.

## Baseline facts

- The base tree tracks 986 files.
- The four vendored factory prefixes (`.agents/`, `.grok/`, `.grok-stack/`, and
  `_bmad/`) contain 383 tracked files (38.8% of the tracked tree), 1,940,075
  bytes, and approximately 35,342 lines.
- The active Go surface is 24 tracked files (`cmd/engine/main.go`, `go.mod`, and
  22 files under `internal/`), 91,315 bytes, and 2,938 lines. There is no tracked
  `go.sum` at the base commit.
- `architecture/runtime.yaml` still declares `runtime:go-reference` as an
  implemented `TEST_ONLY_EXECUTABLE_SPEC`, and
  `architecture/conformance/manifest.yaml` points five Python conformance rows
  at local `internal/...` Go paths. Those references would dangle if the code
  were merely deleted.
- Repository inventory is closed and exact. The graph test currently expects
  403 `VENDORED_TOOLING` exclusions and binds all tracked paths exactly once.
  Removing files without regenerating the inventory and its assertions will
  fail the graph suite.
- The current factory wrappers under `scripts/grok_*.py` import
  `adaptive_grok` by inserting the repository's `.grok-stack` into
  `sys.path`. The hooks similarly import repository-local factory code. A link
  in documentation alone is therefore not a compatible replacement for the
  current commands; the integration entrypoints must be redirected or replaced.
- The imported runtime reports Adaptive Grok Build Pro `2.0.11`, but the tree
  has no single immutable upstream source/revision/checksum declaration that
  can independently reproduce the vendored payload. The replacement must add
  that missing source-of-truth rather than infer a pin from the version string.
- Current product state is explicit in `README.md`, `handoff.md`, schemas, and
  the existing change package: F3-F7 are `IMPLEMENTED_UNVERIFIED`, all 156
  vectors in `schemas/mezo-evidence/v1/vectors.json` are `NOT_RUN`, and no
  testnet payment, deployment, or release is claimed.
- The route is medium-risk and requires base, data, and integration checks plus
  verification, code, test, security, and data review receipts. The data domain
  is incidental to repository detection; this cleanup requires no schema
  migration, SQL change, backfill, or production-data operation.

## In scope

### Go retirement

- Remove all active Go source and module markers: `cmd/engine/**`, `internal/**`,
  `go.mod`, and `go.sum` if one appears during implementation.
- Remove the active `runtime:go-reference` graph node and all active-tree
  bindings that require the deleted source to exist.
- Rebind the five conformance invariants to durable Python tests/contracts and
  to historical provenance (the imported commit/history), not to nonexistent
  local Go paths.
- Keep the invariant intent—exact arithmetic, fail-closed unknown outcomes,
  owned-order cancellation, monotonic cumulative fills, and fail-closed risk—
  in current Python tests and safety documentation.
- Update current-state documentation and build/classifier assertions so they
  say the Go implementation was retired from the active tree. Historical plans,
  evidence, and Git objects may continue to describe what existed at the time.

### Factory boundary replacement

- Delete copied upstream implementation content under `.agents/`, `_bmad/`,
  `.grok/agents`, `.grok/skills`, `.grok/hooks`,
  `.grok-stack/adaptive_grok`, and `.grok-stack/templates`, plus other files
  proven to be installer-managed duplicates rather than Liqvera configuration.
- Retain only a small, explicit allowlist of project-owned integration files:
  the immutable source/revision/checksum lock, Liqvera policy/configuration,
  thin entrypoints or bootstrap command, ignore rules for hydrated/cache/runtime
  content, and contributor documentation.
- The lock must identify an immutable upstream commit or release artifact and
  its integrity digest. A floating branch, `latest`, mutable URL, or version
  string without a verified digest is not an acceptable pin.
- Bootstrap/update must be explicit, idempotent, bounded, and fail closed on
  missing network, unavailable source, revision mismatch, digest mismatch,
  partial extraction, or incompatible version. It must not fall back to the old
  vendored payload, a newer revision, or an unverified local directory.
- Hydrated external code, caches, receipts, and active route state must remain
  untracked. Runtime state must not be confused with the pinned integration
  declaration.
- Preserve contributor guardrails: route selection, allowed-agent enforcement,
  single write ownership, protected/secret paths, quality-profile selection,
  fingerprint-bound receipts, and the no-deploy/no-production-write boundary.
- Preserve a working documented path for `route`, `status`, `change`, `verify`,
  `review`, and `deploy-plan` commands after a fresh bootstrap. `deploy-plan`
  may print human-owned commands; it must not deploy or publish as a side effect.
- Update the exact repository inventory/classifier and tests for the new
  boundary. Externally supplied source must never become a product artifact or
  an active architecture node.

### Continuity and documentation

- Update `README.md`, `docs/architecture.md`, `handoff.md`, `PROVENANCE.md` when
  needed, the change package, and graph documentation to distinguish:
  product code, historical imported material, and externally managed tooling.
- Preserve `AGENTS.md` safety rules or replace factory-specific mechanics with
  accurate equivalents. Do not weaken shadow-only, secret, review, receipt, or
  publication rules as a shortcut around the removed vendor tree.
- Keep inherited `mee-*` package and API identifiers unchanged.

## Explicit non-goals

- No F3-F7 implementation, verification closure, or status promotion.
- No execution of A01-A30 as product acceptance and no rewrite of their stored
  statuses. Repository tests run for this cleanup are not runtime acceptance.
- No live Hyperliquid action, facilitator/RPC mutation, wallet signature,
  MUSD transfer, testnet payment, mainnet support, custody, trading, or exchange
  mutation.
- No payment-address/finality decision and no attempt to close
  `PAY_TO_MISSING`, `FINALITY_RULE_UNVERIFIED`, canonical authorization, funded
  buyer, or receipt blockers.
- No API/OpenAPI/schema/state-machine behavior change; no PostgreSQL schema or
  migration change; no backfill and no production-data access.
- No dependency upgrade, vulnerability remediation, Docker healthcheck change,
  Trivy waiver, deployment, tag, push, GitHub Release, or publication as part
  of this cleanup.
- No renaming of Liqvera or inherited `mee-*` identifiers.
- No Git history rewrite. The removed Go and factory bytes remain recoverable
  from the base commit and repository history.
- No broad deletion of historical plans/evidence merely because they mention
  Go, Grok, BMad, or the former project. Current-state documents must be
  corrected; historical records should remain truthful to their period.
- No promise that contributors can run the external factory without first
  performing its explicit bootstrap. Product verification that does not need
  the factory should remain independent of that network step.

## Acceptance criteria

### AC-1 — active Go surface is absent

Given the final tracked tree, when tracked paths are enumerated, then there are
no `*.go`, `go.mod`, or `go.sum` files and no active `cmd/engine` or Go-only
`internal` implementation paths. Repository detection no longer reports Go or
classifies Liqvera as polyglot solely because of Stage-0.

### AC-2 — Go provenance and invariants survive retirement

Given a reader or maintainer needs the retired baseline, when they follow
current provenance/architecture documentation, then they can identify the
import origin and an immutable repository commit containing the removed code.
The five Python conformance tests remain present and passing, and the
conformance manifest has no dangling `internal/...` references.

### AC-3 — no copied factory implementation remains tracked

Given the final tracked tree, when the former vendor prefixes are inspected,
then no upstream agent catalogue, BMad workflow bodies/assets, Grok hook
implementation, Adaptive Grok Python runtime, or factory templates remain.
Every retained tooling file is on a documented minimal allowlist and is either
Liqvera configuration, a lock, or a thin integration entrypoint.

### AC-4 — external tooling is immutable and integrity checked

Given a clean checkout and empty tool cache, when the documented bootstrap is
run, then it obtains exactly the locked upstream revision/artifact, validates
its digest before activation, installs/hydrates outside the tracked product
tree, and reports the resolved identity. A checksum/revision mismatch or
partial/unavailable acquisition exits nonzero without activating any payload.

### AC-5 — integration commands and safety gates still work

Given the exact locked tooling is available, when route/status/change/verify/
review commands are exercised in a disposable checkout, then they use the
project policy and preserve allowed-agent selection, one write owner,
protected/secret-path controls, selected profiles, and fingerprint-bound
receipts. No command performs a deployment, publication, or external system
write during this test.

### AC-6 — bootstrap is not an implicit product-side effect

Given the locked tooling is absent, when ordinary product import/build/test
commands run, then they neither download nor execute remote factory code. A
factory-specific command gives a concise, deterministic bootstrap instruction
or fails closed. Hooks must not silently fetch or run an unverified newer copy.

### AC-7 — product contracts and data are unchanged

Given base commit `0c2cb97f8048f7da8bd193634f4502f24b0e541e`, when final
changes are reviewed, then runtime product sources, OpenAPI/JSON schemas,
Mezo vectors/state graphs, gateway migrations, Stage-A migrations, Compose
runtime definitions, and acceptance runner behavior are byte-for-byte
unchanged except for separately justified repository-boundary metadata. No SQL
migration or backfill exists in the cleanup diff.

### AC-8 — product status is not promoted

Given the final README, handoff, change package, and machine-readable vectors,
when status claims are inspected, then F3-F7 still read
`IMPLEMENTED_UNVERIFIED`; exactly 156 vectors still read `NOT_RUN`; A13-A14
remain `BLOCKED_EXTERNAL`; payment readiness remains false; the existing
payment/finality blockers remain recorded; and no live payment, deployment,
release, or product acceptance is claimed.

### AC-9 — repository graph is exact after deletion

Given the final tracked tree, when the graph/inventory suite runs, then every
tracked path is represented exactly once, deleted vendored and Go paths are not
expected, no dangling node/binding/exclusion remains, and the external tool
lock/integration files have a truthful non-product classification.

### AC-10 — verification is honest and reviewable

Given the final fingerprint, when the route-selected verification and focused
cleanup tests run, then the commands execute through the new boundary and
produce evidence tied to that fingerprint. Existing unrelated Trivy findings,
if still present, are reported as blockers rather than waived or hidden; this
cleanup does not claim a green product release from a tooling smoke test.
Independent code, test, security, and data reviews inspect the same final tree.

### AC-11 — repository reduction is measurable

Given the baseline measurements above, when final inventory is reported, then
active Go count/bytes are zero and the 383-file/1,940,075-byte factory payload
is replaced by the explicit minimal allowlist. The change evidence records the
before/after file count and byte count; generated cache/runtime files are not
counted as tracked integration files.

### AC-12 — clean checkout and rollback are reproducible

Given a clean disposable checkout, when the contributor instructions are
followed, then both ordinary Liqvera checks and the separately bootstrapped
factory smoke path behave as documented. Given the cleanup commits are
reverted, the prior vendor and Go trees can be recovered entirely from Git
without a database rollback or external-system mutation.

## Failure and edge cases to test

- Locked upstream revision is unavailable, moved, or private.
- Download succeeds but archive/repository digest differs from the lock.
- Existing cache contains the right version with modified bytes.
- Interrupted acquisition leaves a partial directory.
- Two bootstrap processes start concurrently.
- Contributor is offline after a previously verified bootstrap.
- Tool cache is read-only or cannot be created.
- Invocation occurs from a subdirectory/worktree rather than repository root.
- Runtime route/receipt directory is absent, stale, or ignored.
- A future update changes the lock but not the checksum, or vice versa.
- An upstream payload attempts to place files outside its cache/install root.
- Removed Go paths remain referenced in manifests, current docs, Make targets,
  test parameters, or package/artifact allow/deny lists.
- Graph counts are mechanically lowered while a new unknown tracked path is
  omitted from inventory.
- Cleanup tests pass but someone changes a product schema/migration/vector in
  the same diff.
- README wording accidentally upgrades `IMPLEMENTED_UNVERIFIED`, converts
  `NOT_RUN`/`BLOCKED_EXTERNAL` to PASS, or implies a testnet payment/release.
- Factory verification fails only on the known inherited Trivy findings; the
  result must remain visible and must not trigger an unrelated policy edit.

## Recommended sequencing and commit boundaries

1. **Freeze characterization evidence.** Record the exact baseline file/byte
   counts, Go list, vendor list, product-path hashes, 156-vector status count,
   graph result, and current documented blockers. Add negative tests for
   floating pins, unverified cache use, and product-status drift before removal.
2. **Introduce the pinned boundary before deleting its predecessor.** Add the
   project-owned lock/bootstrap/adapter and test it in a disposable empty-cache
   checkout. Keep the old vendor only long enough to compare command behavior;
   never allow fallback to it in the new path.
3. **Retire the factory payload coherently.** Remove copied sources, redirect
   wrappers/hooks, add ignore rules, and regenerate inventory/classifier
   declarations. Run focused bootstrap, route/status, fail-closed, graph, and
   secret-path tests. Commit with `handoff.md` updated to the true intermediate
   state.
4. **Retire Go coherently.** Delete Go/module paths, rebind invariant provenance,
   update graph/current docs/tests, and run the conformance plus artifact and
   graph suites. Commit with the handoff update. This may be swapped with step 3
   if the write owner can still produce final route evidence; in either order,
   do not leave a commit with dangling graph or conformance paths.
5. **Run final regression and boundary verification.** Confirm product-path
   hashes, vector/blocker/status counts, `make verify`, focused integration
   tests, a clean-checkout bootstrap smoke, and the route's PR verification.
   Record known failures honestly; do not reinterpret unit/static checks as
   F3-F7 runtime acceptance.
6. **Independent reviews and fingerprint binding.** Run the route-selected code,
   test, security, and data reviews only after the final tree stops changing.
   Bind receipts to that tree; any subsequent repository edit invalidates them.

Each significant passing step should be a coherent commit. `handoff.md` must be
updated in the same commit whenever the current boundary, checks, blockers, or
next action changes materially. Do not publish, push, tag, or release under this
route without separate authority.

## Rollback and recovery

### Triggers

- product-path hash changes outside the approved metadata set;
- a Liqvera regression or changed contract/migration/vector;
- inability to reproduce or integrity-check the external tool pin;
- route/status/verification commands silently bypass project safety policy;
- fresh checkout cannot run ordinary product verification without downloading
  factory code;
- graph inventory is incomplete or conformance references dangle; or
- current docs imply F3-F7 verification, payment, deployment, or release.

### Action

- Revert the cleanup commits in reverse order to restore the exact base-tree
  files. Do not rewrite history and do not fetch an unpinned replacement as an
  emergency workaround.
- Delete only the specifically documented ignored hydration/cache directory if
  it was created by the bootstrap; preserve route/change evidence needed for
  diagnosis. No database, chain, wallet, or external-system rollback is needed
  because the change must perform no such writes.
- If the factory replacement alone fails, restore the last reviewed vendored
  tooling commit temporarily while keeping product status unchanged. If the Go
  retirement alone fails, restore the Go paths and old graph bindings from the
  base commit. The two rollback units should remain separable.

### Post-rollback proof

- tracked file hashes for restored paths match the base commit;
- graph/conformance and `make verify` return to the recorded baseline behavior;
- all 156 vectors remain `NOT_RUN`, A13-A14 remain `BLOCKED_EXTERNAL`, payment
  readiness is false, and no deployment/release/payment claim appears; and
- `git status` contains only intentional diagnostic/runtime evidence.

## Success metrics

| Metric | Baseline | Required outcome |
| --- | ---: | --- |
| Active tracked Go files | 24 | 0 |
| Active tracked Go bytes | 91,315 | 0 |
| Vendored factory files under four prefixes | 383 | Only the documented project-owned allowlist; no upstream implementation trees |
| Vendored factory bytes | 1,940,075 | Post-cleanup count recorded and materially reduced to the allowlist |
| Dangling Go conformance references | 5 local `internal/...` references | 0 |
| Runtime vectors | 156 `NOT_RUN` | Exactly 156 `NOT_RUN` |
| F3-F7 status | `IMPLEMENTED_UNVERIFIED` | Unchanged |
| A13-A14 | `BLOCKED_EXTERNAL` | Unchanged |
| Payment readiness | false | false |
| Product API/data migrations in cleanup | 0 intended | 0 |
| Unpinned/floating tool sources | Current pin not independently reproducible | 0; one immutable source plus verified digest |
| Silent bootstrap/fallback paths | Not applicable to vendored runtime | 0 |
| Graph inventory gaps/duplicates | 0 | 0 |
| External writes/payments/deployments | 0 | 0 |

## Residual risks and review focus

- **Supply chain:** replacing reviewed local bytes with fetched bytes creates a
  new acquisition boundary. Security review should concentrate on pin strength,
  digest verification order, extraction traversal/symlinks, cache poisoning,
  executable activation, and update behavior.
- **Availability:** an external source can disappear. The immutable identifier,
  checksum, and documented cache/export strategy provide reproducibility, but
  must not become an excuse for committing the full payload again.
- **Policy drift:** project-local safety policy can be lost if all `.grok*`
  content is indiscriminately removed. Review the retained allowlist against
  `AGENTS.md`, especially protected paths, one writer, reviews, receipts, and
  deployment prohibitions.
- **Historical ambiguity:** old plans and evidence will still mention Go and
  vendored tooling. Current architecture/README/handoff must clearly label them
  historical without rewriting those records.
- **False verification claim:** a successful factory smoke test only proves the
  tooling boundary. It does not close F3-F7, A01-A30, payment, deployment,
  acceptance, or release gates.

## Evidence commands for the write owner

The exact bootstrap command depends on the chosen upstream distribution, but
the final evidence should include equivalents of:

```bash
git ls-files '*.go' go.mod go.sum
git ls-files .agents .grok .grok-stack _bmad
git diff --check
make graph
python3 -m pytest tests/conformance tests/artifact tests/graph -q
make verify
python3 scripts/grok_status.py
python3 scripts/grok_verify.py --mode pr --no-record
```

Also record a machine-produced before/after inventory, product-path hash
comparison, clean-checkout/empty-cache bootstrap result, digest-mismatch
negative test, and the exact vector/status/blocker assertions. Run commands
that require the external factory only after its pin has been verified; never
substitute a floating installation already present on the machine.
