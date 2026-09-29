# Architecture analysis — repository boundary cleanup

Route: `7f0f98e3cdda`
Base: `0c2cb97f8048f7da8bd193634f4502f24b0e541e`
Role: read-only architecture analysis
Recommendation: delete the Go Stage-0 implementation from the active tree and
replace the vendored Grok/BMad implementation with a thin, integrity-pinned
external integration. Keep Liqvera's product verification authoritative,
repository-local, and runnable without the external factory.

## Repository facts

- The active tree has 986 tracked files. `.agents/` (253 files), `.grok/` (75),
  `.grok-stack/` (40), and `_bmad/` (15) account for 383 files (38.8%) and
  1,940,075 tracked bytes. The graph classifies all four prefixes as
  `VENDORED_TOOLING` and binds them to inactive
  `artifact:vendored-agent-tooling`.
- Go Stage-0 consists of 24 tracked Go/module files (91,315 bytes), plus the
  repository-root `Dockerfile` that builds `./cmd/engine`. No current product
  Make target, Python package, Liqvera service, or GitHub workflow builds that
  engine. `make verify` instead proves that Stage A artifacts exclude
  `cmd/**`, `internal/**`, `go.mod`, `go.sum`, and an `engine` binary.
- The Go tree is not the current runtime authority. ADR-0001 accepts Python;
  the graph calls Go `TEST_ONLY_EXECUTABLE_SPEC`; conformance executes Python
  only. The five preserved invariants already have Python contract symbols,
  negative tests, and conformance tests.
- Go is nevertheless coupled to repository metadata: the runtime node,
  `ARCH-GO-001` through `ARCH-GO-005` proof chains, inventory bindings,
  conformance `reference_source` values, retirement tests, documentation, the
  root Dockerfile, and graph-checker classifications all name it. Deletion is
  an architecture retirement, not merely a filesystem operation.
- Product verification is already independent of the factory implementation:
  `make verify` runs graph, salvage, artifact-boundary, package, conformance,
  installed-artifact, and compatibility checks without importing
  `.grok-stack`.
- Factory commands are not independent. Every `scripts/grok_*.py` wrapper
  imports `adaptive_grok` from `.grok-stack`; project hooks import the same
  implementation. Removing the vendored stack without replacing these entry
  points leaves route, receipt, verification, and hook behavior broken or
  fail-open.
- Current external identity is incomplete. The repository records Grok CLI
  `built=1.0.4`, hook-stack prose saying `v2.0.4`, and BMad `6.10.0`, but it
  does not record an immutable Adaptive Grok source/archive coordinate or
  digest. BMad's manifest says `source: built-in` and has no `repoUrl` or npm
  package. A version string or documentation link alone is not a reproducible
  pin.
- Historical recovery does not require a second in-tree archive. Import commit
  `8734907d489168a8a6567b93bc85920001fefd85` and
  `provenance/import-manifest.json` already preserve and hash the imported
  files; the provenance document identifies private baseline
  `4f6583f8590ea091d8a465de0c607e59bfe611a5`.

## Candidate designs

| Design | Active-tree clarity | Reproducibility | Offline product verification | Contributor guardrails | Main risk |
| --- | --- | --- | --- | --- | --- |
| A. Full deletion | Best | Poor for factory operations | Preserved only if `make verify` remains | Loses routing/receipt/hook policy unless reimplemented | A smaller repository can look green while factory and container gates silently disappear |
| B. Archive split | Better if external; unchanged if moved under `docs/archive/` | Medium | Preserved | Still no active integration | A tarball/archive duplicates Git history; a submodule adds availability and trust-on-first-use failure modes |
| C. Thin pinned/bootstrap integration | Best practical balance | Best once immutable coordinates and digests exist | Preserved by design | Preserved through small entry points plus mandatory product gates | Bootstrap/cache design and pin ownership must be explicit |

### A. Full deletion

Delete the Go tree, root Go Dockerfile, vendored factory/BMad directories,
root hook shims, and `scripts/grok_*`; rely on Git history for provenance and
`make verify` for product checks.

This correctly removes unrelated source, but it does not meet the stated
continuity requirements by itself. `AGENTS.md` currently mandates the active
route, change packages, fingerprint-bound receipts, and `grok_verify`; those
commands would no longer exist. Deleting the root Dockerfile also removes the
only path that currently makes `adaptive_grok.verification` schedule Trivy:
its discovery checks only a root `Dockerfile`/`Containerfile` or
`docker-compose*.yml`. The actual product files under `deploy/images/` and
`deploy/mezo-evidence/` would not automatically replace that trigger. A clean
result after deletion could therefore reflect less coverage, not higher
quality.

Use this design only if the repository explicitly retires the Adaptive Grok
contract and replaces the release gate with a different, reviewed contract.

### B. Archive split

Move Go and/or factory sources to a separate repository, archival branch,
release asset, or submodule and retain links from Liqvera.

This is useful for human discoverability, but not as the primary runtime
design:

- moving sources under `docs/archive/` does not reduce checkout size, scanner
  surface, or inventory complexity;
- a committed tarball duplicates history and is harder to inspect and scan;
- a submodule is absent in ordinary clones, adds its own pin/update workflow,
  and does not provide an offline fresh-clone guarantee;
- a separate archive is unnecessary for recovery because the initial import
  commit and manifest already preserve exact blobs;
- the imported baseline is marked proprietary and no tracked LICENSE/NOTICE
  was present, so republishing extracted sources separately requires an
  explicit provenance/licensing decision.

An optional read-only archival tag or repository may be added later, but it
should not be in the verification dependency chain.

### C. Thin integrity-pinned integration (recommended)

Adopt a two-layer boundary:

```text
authoritative, offline Liqvera gate
  make verify + explicit product container/config scan
                         |
                         | required before review/release evidence
                         v
thin repo integration -> verified external factory cache -> routing/reviews/receipts
  lock + bootstrap       exact artifact/version/digest    no product authority
```

The external factory may orchestrate the checks, but it must not define or
replace the checks that establish Liqvera product safety. This prevents a
missing package, unavailable network, or upstream factory change from making
the product unverifiable.

## Recommended target boundary

### Remove from the active product tree

1. `cmd/engine/`, the Go-owned portions of `internal/`, `go.mod`, and the root
   Go `Dockerfile`.
2. `.agents/`, `_bmad/`, the vendored `.grok-stack/adaptive_grok` sources and
   templates, duplicated `.grok/skills`, agent definitions, and local BMad
   installation manifests.
3. Generic root hook shims after the external integration supplies the
   supported hook entry point. Do not retain wrappers that silently allow on a
   missing implementation while documentation describes them as a safety
   gate.

### Keep or introduce as the thin integration

Names below are conceptual; the implementation owner may fit existing
repository conventions.

1. One machine-readable lock containing, separately for Adaptive Grok and
   BMad, the canonical artifact/repository coordinate, immutable revision,
   archive/package SHA-256, expected package version, and compatibility
   version. Do not accept a floating branch, unqualified URL, or version-only
   pin.
2. One small bootstrap/launcher that:
   - installs only into an ignored repository-local tool cache;
   - accepts an already-downloaded archive for offline setup;
   - verifies the archive digest before extraction/install;
   - rejects path traversal, links, unexpected top-level layout, and a runtime
     version mismatch;
   - never reads credentials or performs network access during normal
     verification;
   - requires an explicit bootstrap action for network acquisition.
3. Small project-owned policy/configuration only: route rules, protected path
   policy, required evidence kinds, and project-specific quality profiles.
   Generic agents, skills, templates, and implementation modules remain in the
   external artifact.
4. Stable repository entry points (`grok_verify`, route/status/review/deploy
   wrappers or one equivalent command) that validate the lock and delegate to
   the cached exact artifact. Missing or mismatched tooling must fail with a
   deterministic setup error; it must not manufacture a pass or receipt.
5. A cache-path ignore rule and a cache purge/rollback command. The cache is a
   derived dependency, never committed product source.

### Keep authoritative and offline

- `Makefile` product targets and repository-owned verification/checker code.
- Architecture manifests/schemas and their tests, after removing assumptions
  that vendored source prefixes must exist.
- Python conformance invariants and negative tests. Rewrite their provenance
  from live `internal/...` paths to immutable historical source identity plus
  the current Python contract symbol. The tests should prove current behavior,
  not require Go source to remain checked out.
- Publication, source, and artifact-boundary checks.
- A direct product-container scan whose input list names the actual
  `Dockerfile.a2`, `deploy/images/Dockerfile.*`,
  `deploy/mezo-evidence/Dockerfile.*`, and relevant Compose manifests. Do not
  rely on root-file auto-discovery.

## Go retirement model

Preserve history in metadata while removing active source:

1. Record `runtime:go-reference` as `RETIRED`, inactive, with no active file
   bindings or runtime dependencies.
2. Preserve an explicit `derived_from`/`rolled_back_by` edge to the import
   commit (or a dedicated archival tag bound to that commit). This is recovery
   provenance, not a build dependency.
3. Mark the five conformance rows `RETIRED` only after the Python tests pass on
   the cleanup tree and independent review approves the retirement. Keep
   `stage_a_packaging_allowed: false`.
4. Replace `reference_source: internal/...` with a stable historical reference
   that includes the import commit and original path, or split it into
   structured `historical_source` fields if the schema is revised. A bare
   deleted path is ambiguous.
5. Keep artifact tests that assert no Go inputs or engine binary enter product
   artifacts. After deletion these tests remain valuable regression guards,
   but assertions that Go must remain `TEST_ONLY_EXECUTABLE_SPEC` should be
   changed to assert the retired state and absence from the active inventory.
6. Remove the root Go Dockerfile from product/workflow inventory and bind the
   replacement explicit container-scan configuration before accepting the
   removal of the current Trivy trigger.

## Contributor and release invariants

The implementation should not be accepted unless all of these hold:

1. A clean clone without network access can run the full Liqvera product gate
   after normal product dependencies are present; factory bootstrap is not in
   this path.
2. A contributor without the external factory gets a clear setup error only
   for factory operations, not for `make verify`.
3. An installed factory must match the committed digest and compatibility
   version before it may write route state or receipts.
4. Verification receipts bind the final repository fingerprint and identify
   both the external factory digest and the repository policy/config digest.
5. No live exchange, payment, deployment, release, or push authority is added;
   shadow-only and testnet fail-closed boundaries remain unchanged.
6. The bootstrap never mutates global user tooling by default and never needs
   secrets. Network download is explicit, bounded, and integrity-verified.
7. Product container scanning remains required after the root Go Dockerfile is
   gone and names product manifests directly.
8. The archive/history reference is read-only and cannot be resolved as an
   active runtime dependency.

## Cutover sequence

1. Establish authoritative external coordinates and digests. This is the only
   unresolved design input: the current repository does not contain enough
   provenance to synthesize a trustworthy Adaptive Grok artifact pin.
2. Add characterization tests for lock parsing, digest mismatch, offline-cache
   operation, absent-cache failure, receipt binding, and explicit container
   scan inputs.
3. Add the thin integration and prove it against the currently vendored
   behavior before deleting the vendor directories.
4. Retire Go in the graph and conformance metadata; delete its source and root
   Dockerfile in the same coherent step. Run focused conformance, artifact,
   graph, and container policy checks.
5. Remove the vendored factory/BMad source and obsolete graph exclusions. Run
   product verification from a clean clone without the factory cache, then run
   factory routing/receipt verification with a pre-populated, digest-matched
   cache.
6. Run the route's independent code, test, security, and data reviews. Bind
   all receipts after the final tree change; any subsequent edit invalidates
   them.

## Rollback

- Product rollback is a revert of the cleanup commit; no database, API, event,
  or user-data migration is involved.
- Tooling rollback changes the lock to a previously reviewed immutable digest
  and clears the derived cache. Never fall back to an unpinned latest version.
- Go recovery uses the recorded import commit/tag and selected paths. Do not
  keep a second active-tree copy merely for rollback.

## Decision

Choose design C. It removes unrelated implementation source, retains exact
historical recovery through Git/provenance, keeps the Liqvera safety gate
offline and repository-owned, and reduces the external factory to a pinned
orchestrator. Design A is acceptable only if the factory contract is formally
retired; design B may be a documentation convenience but should not become an
execution dependency.

The implementation must stop before claiming reproducible bootstrap if an
immutable Adaptive Grok artifact coordinate and digest cannot be established.
Grok CLI `1.0.4`, hook prose `2.0.4`, and BMad `6.10.0` are useful compatibility
facts, but they are not sufficient supply-chain identity.
