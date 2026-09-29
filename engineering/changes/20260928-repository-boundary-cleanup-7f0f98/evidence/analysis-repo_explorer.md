# Repository dependency map: Go Stage-0 and vendored factory

Date: 2026-09-28
Route: `7f0f98e3cdda`
Base commit: `0c2cb97f8048f7da8bd193634f4502f24b0e541e`

## Conclusion

The Liqvera product has no runtime import, build dependency, or current GitHub
workflow dependency on the inherited Go implementation or on the vendored
Grok/BMad implementation. Removing them is feasible, but it is not a
file-deletion-only change: the architecture inventory, legacy proof model,
documentation, factory entrypoints, and several policy tests encode both
surfaces as present.

The safest small boundary is:

1. remove the Go module, its root Go image, and its live graph/proof ownership;
2. preserve the safety behavior in the existing Python contracts/tests, with
   Python-native provenance instead of dead `internal/...` paths;
3. remove generic factory source and descriptors;
4. retain only a checked-in external-tool lock, project-owned configuration,
   and thin commands/hooks that invoke the pinned external installation; and
5. keep product verification independently runnable (`make verify` plus the
   Liqvera build/acceptance targets), rather than making it depend on factory
   source being copied into this repository.

There is one unresolved input: the tree records Adaptive Grok runtime version
`2.0.11`, BMad version `6.10.0`, and the generic Grok Build documentation URL,
but no authoritative package/repository URL, immutable revision, or artifact
checksum for either source. A trustworthy external pin cannot be invented from
the current repository.

## Measured inventory

At the base commit the repository has 986 tracked files.

| Surface | Files | Size/lines | Notes |
| --- | ---: | ---: | --- |
| `go.mod`, `cmd/**`, `internal/**` | 24 | 91,315 bytes; 2,938 lines | No `go.sum`; standard library only plus intra-module imports |
| `.agents/**` | 253 | 1,674,385 bytes | Generic skills, mostly BMad |
| `.grok/**` | 75 | 63,135 bytes | 42 agent descriptors, 12 hook files, 19 skills, config files |
| `.grok-stack/**` | 40 | 104,218 bytes | 14 Python runtime files, 13 config files, 12 templates, `.gitkeep` |
| `_bmad/**` | 15 | 98,337 bytes | Installer metadata/config and three helper scripts |
| `scripts/grok_*` | 8 | 8,054 bytes | Thin imports of local `adaptive_grok` |
| root hook shims | 9 | 8,676 bytes | Nine identical 964-byte dispatchers |
| complete factory exclusion set | 403 | 1,956,805 bytes | Above factory paths plus `ruff.toml`, `bandit.yaml`, `.coveragerc` |

The 403 count is also asserted verbatim by
`tests/graph/test_third_final_review_policy.py`.

## Exact Go dependency map

### Executable Go island

`go.mod` declares module `github.com/Dimkox/multi-exchange-engine`, Go 1.26.0,
toolchain 1.26.5, and no external modules. `cmd/engine/main.go` imports only
`internal/config` and `internal/httpapi`. The remaining Go imports are entirely
within `internal/{config,domain,exchange,execution,fixed,httpapi,ownership,reconcile,risk,stagea}`.
No Python, TypeScript, Compose, Liqvera service, or Mezo package imports this
module.

The root `Dockerfile` is the only active build entrypoint for the Go island. It
copies `go.mod` and the repository, runs `gofmt`, `go vet`, and `go test`, then
builds `./cmd/engine` into a shadow-mode image. `Makefile` does not invoke that
Dockerfile and no tracked `.github/workflows/**` file runs Go.

Therefore these should be treated as one removal unit:

- `go.mod`;
- `cmd/engine/main.go`;
- all 22 files under `internal/**`; and
- root `Dockerfile` (otherwise it becomes immediately broken).

### Architecture and conformance dependencies

Deletion without graph changes makes `make graph` fail because
`architecture/architecture.yaml` binds all 24 Go paths and the root Dockerfile.
The complete semantic dependency is larger:

- `architecture/runtime.yaml` declares implemented node
  `runtime:go-reference`, profile `go-test-only`, classification
  `TEST_ONLY_EXECUTABLE_SPEC`, and requirements `ARCH-GO-001..005`.
- `architecture/requirements.yaml` declares those five non-product
  requirements.
- `architecture/architecture.yaml` contains the five generated proof chains,
  aggregate edges to/from `runtime:go-reference`, the declared
  `conflict:go-stage-a-build`, and exact file bindings.
- `architecture/conformance/manifest.yaml` has five Python-only invariant rows
  whose `reference_source` values are `internal/fixed`,
  `internal/execution`, `internal/ownership`, and `internal/risk`.
- `tools/conformance/policy.py` defaults `reference_source` to
  `internal/fixed`; `tools/conformance/runner.py` copies these strings into
  receipts but does not verify that the referenced path exists.
- `tools/graph_checker/{model,loader,checker,retirement}.py` contains generic
  `GO_SOURCE` / `TEST_ONLY_EXECUTABLE_SPEC` classification and retirement
  policy.

The conformance behavior itself is already Python-owned. The five manifest
rows point at:

- `mee_contracts.exact.ExactDecimal` and
  `tests/conformance/test_exact_arithmetic.py`;
- Python unknown-outcome, ownership, monotonic-fill, and risk invariants and
  their corresponding tests.

Do not delete these safety tests with the Go source. Rebind their provenance to
the Python contracts/tests or to an immutable historical-source reference. If
the `internal/...` strings remain, conformance can pass while citing files that
no longer exist.

### Tests and documentation affected by Go removal

Directly coupled tests are:

- `tests/conformance/test_retirement_policy.py` (loads
  `runtime:go-reference`);
- `tests/graph/test_second_final_review_policy.py` (mutates that node and
  expects `RUNTIME_GO_PROFILE_INVALID`);
- `tests/graph/test_retirement.py` and the Go fixture helpers in
  `tools/graph_checker/retirement.py`;
- classifier/schema assertions for `GO_SOURCE` and
  `TEST_ONLY_EXECUTABLE_SPEC`.

The following negative guards remain useful after removal and should not be
mistaken for a dependency on the Go implementation:

- `Makefile` `artifacts` target;
- `scripts/check-stage-a-artifacts.py`;
- `tools/conformance/artifacts.py`;
- `tests/conformance/test_stage_a_excludes_go.py`;
- Go/foreign-namespace assertions in
  `tests/artifact/test_forbidden_capabilities.py` and
  `tests/artifact/test_wheel_boundaries.py`.

They ensure Go is not reintroduced into Python artifacts. Their messages can
be reframed as a permanent product boundary.

Current-state prose that must change includes `README.md` and
`docs/architecture.md`. Historical plans and
`docs/archive/handoff/handoff-through-2026-08-09.md` can retain factual Go
history if clearly marked archived. `provenance/import-manifest.json` should
remain an immutable inventory of the initial 815-file import; `PROVENANCE.md`
already defines it as historical. Add the later removal event to provenance
rather than rewriting the import record.

### Non-obvious verification effect

`.grok-stack/adaptive_grok/verification.py` only enables Trivy when a root file
named `Dockerfile`, `dockerfile`, or `Containerfile` (or a
`docker-compose*` file) exists. Removing the root Go `Dockerfile` makes its
Trivy check disappear even though product Dockerfiles remain under `deploy/`.
The replacement verifier must explicitly scan the product Dockerfiles/Compose
tree, or security coverage silently regresses.

Removing `go.mod` also changes factory repository detection from polyglot
Python+Go to Python, so future route selection may change. That is expected and
should be tested, not treated as incidental.

## Exact vendored-factory dependency map

### Runtime call chain

The current self-hosted factory is a closed local chain:

```text
.grok/hooks.json
  -> .grok/hooks/*.py
     -> .grok/hooks/_lib.py
        -> .grok-stack/adaptive_grok/*

root hook shims
  -> .grok/hooks/<same-name>.py

scripts/grok_{route,status,verify,review,change,deploy,doctor,approve}.py
  -> sys.path += .grok-stack
  -> adaptive_grok.*
```

Deleting `.grok-stack` alone makes all eight `scripts/grok_*` commands fail
with `ModuleNotFoundError`. Most hook paths, by contrast, intentionally fail
open: `pre_tool_use` returns allow and the stop hook returns `{}`. Thus an
uncoordinated deletion can look healthy while silently removing secret/path,
destructive-command, allowed-agent, route, fingerprint, and evidence checks.

`.agents/**` and `.grok/{agents,skills}/**` are descriptors/instructions, not
product code. `_bmad/**` supplies config and helper scripts expected by the
vendored BMad skills. Removing `_bmad` while retaining those skills breaks
their documented customization and memlog commands. Removing both together
does not affect Liqvera runtime.

No current GitHub workflow invokes `scripts/grok_*`, `.grok` hooks, `.agents`,
or `_bmad`. No product package imports `adaptive_grok`; purity tests explicitly
forbid that import in product wheels.

### Repository policy and graph dependencies

Removal requires coordinated edits to:

- `AGENTS.md`, whose engineering contract mandates the active route,
  `adaptive-delivery`, local `scripts/grok_*`, receipts, and release command;
- `architecture/runtime.yaml`, which declares inactive quarantined
  `artifact:vendored-agent-tooling`;
- `architecture/architecture.yaml`, which excludes exactly 403 files/prefix
  members as `VENDORED_TOOLING`;
- `tools/graph_checker/loader.py`, whose `_VENDORED_PREFIXES` and
  `_ADAPTIVE_GROK_SHIMS` special-case these paths;
- `architecture/schemas/graph-manifest.schema.json`, which permits the
  vendored path prefixes and classification;
- `tests/graph/test_contracts_distribution_classifier.py` and
  `tests/graph/test_third_final_review_policy.py`, including the exact count;
- `.coveragerc`, `ruff.toml`, and `bandit.yaml`, which are currently classified
  as vendored but can influence verification behavior;
- current-state references in `README.md`, `handoff.md`, `docs/README.md`, and
  `PROVENANCE.md`.

Historical evidence that records prior `grok_verify` commands should not be
rewritten as if those runs used the replacement. Preserve it as historical.

### Minimal retained seams

The smallest credible external integration is not a copy of the runtime. It is
a small repository-owned interface:

1. **Immutable tool lock.** Record provider/package URL, version, immutable
   commit or artifact digest, install mechanism, and compatibility versions.
   The current version strings (`2.0.11`, `6.10.0`) are insufficient alone.
2. **Project policy/config only.** Retain only Liqvera-specific route/quality
   selections and safety policy if the external tool does not supply them.
   The current routing, quality profiles, and toolchain files are generic; no
   Liqvera-specific value was found. BMad's useful project values are output
   language/path, while tracked `_bmad/config.user.toml` contains the personal
   name `Dmitry` and should not be part of a shared integration.
3. **Thin stable commands.** Either keep the eight `scripts/grok_*` names as
   tiny launchers into the pinned installed package or update all active
   instructions to the external CLI. Do not retain launchers that import the
   deleted `.grok-stack` path.
4. **Hooks that fail visibly.** Point hook configuration directly at the
   external executable/plugin. Remove the nine duplicate root shims. During
   installation diagnostics, missing external tooling should be explicit;
   fail-open policy should remain an intentional runtime policy, not mask an
   incomplete migration.
5. **Product-owned checks.** Keep `Makefile`, architecture graph checks,
   package tests, Liqvera build targets, and acceptance runner in this repo.
   Reclassify or move any still-needed Ruff/Bandit/coverage settings into
   `pyproject.toml` instead of preserving them merely as factory baggage.
6. **Runtime state seam.** The active route and receipts currently live under
   `.grok-stack/runtime`. The external integration must either continue that
   state contract or migrate it before local runtime source is removed. The
   current change cannot safely delete the state directory first and still
   satisfy its own fingerprint-bound review receipts.

## Removal order and checks

Recommended implementation order for the single write owner:

1. Add and validate the immutable external-tool lock/launcher contract.
2. Prove route/status/verification/review commands and hooks work without
   importing repository `.grok-stack` source.
3. Remove generic `.agents`, `.grok` source/descriptors, `.grok-stack` runtime
   source/templates, `_bmad` installer payload, old root hooks, and obsolete
   wrappers/config; update the graph exclusions and tests in the same step.
4. Remove the Go island and root Dockerfile; rebind Python safety invariants
   and prune the live Go graph/proof chain.
5. Verify at minimum: no tracked Go source/module, no product import of factory
   namespaces, graph inventory closure, Python conformance, full `make verify`,
   Liqvera build/typecheck/Compose targets, explicit Trivy coverage of product
   deployment files, and external route/status/receipt behavior.

Rollback is a Git revert of the coherent cleanup commit. Do not partially
restore only wrappers or hook shims: without their pinned runtime they either
crash or silently fail open.

## Evidence commands used

- `git status --short --branch`
- `git log -10 --oneline --decorate`
- `git ls-files` scoped to every target prefix and shim
- `wc -c`, `wc -l`, and tracked-file counts
- repository-wide `rg` for Go paths, factory paths, imports, commands, graph
  nodes, tests, and documentation references
- direct inspection of `README.md`, `docs/architecture.md`, `handoff.md`,
  `PROVENANCE.md`, `Makefile`, root `Dockerfile`, architecture manifests,
  conformance/graph code and tests, factory runtime/config/hooks, and active
  route/status

No application/product file was modified and no external write was performed.
