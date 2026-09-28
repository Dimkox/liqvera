# Architecture — Repository boundary cleanup

## Current behavior

Go Stage-0 was an inactive executable specification coupled to the graph and
conformance metadata. BMad and Adaptive Grok implementation payloads were
vendored as hundreds of tooling paths; product code did not import either
layer.

## Proposed behavior

Go is absent from the active tree and referenced only by immutable historical
provenance. BMad is optional and external at the exact `bmad-method@6.10.0`
npm identity and SRI recorded in `tooling/tooling-lock.json`. Product
verification stays repository-owned and offline.

Adaptive Grok is a submodule/gitlink at
`tooling/adaptive-grok-build-pro`, pinned to annotated tag `v2.0.19` and
commit `cb9af4073ba6c3d515145164d771c75ebdfa3224`; `.gitmodules` uses the
portable public repository URL. The pinned object was selected from the local
repository without reading its dirty working tree. Version 2.0.19 is required
because it supplies the bounded parallel pytest verifier; older releases run
verification sequentially and are materially slower.

`tooling/adaptive_grok_pin.py` is the shared project-owned trust boundary. Both
`tooling/run-adaptive-grok.py` and the direct `tooling/grok-verify.py`
entrypoint validate the lock, parent gitlink, submodule HEAD, tag target,
VERSION, and clean checkout before importing the framework. The launcher then
executes only an allowlisted Grok command or hook. Thin symlinks retain script,
hook, agent, and skill discovery without retaining copied framework
implementation.

Clean status is diagnostic, not the integrity root: Git index optimization
flags are forbidden globally. The validator independently compares the bounded
runtime/instruction trust closure's blob hashes and executable modes with HEAD:
the engine, Grok scripts/hooks/config/templates/agents/skills, root policy, and
VERSION. Historical packages/distributions/release evidence stay outside the
per-hook hash set while global dirty/untracked checks still cover them. Closure
file and byte ceilings fail closed on unexpected growth. Ignored
Python/importable files are forbidden under `.grok-stack`, `scripts`, and
`.grok/hooks`; both entrypoints disable bytecode generation before framework
import or execution.

## Components and boundaries

- Product: unchanged Python/TypeScript packages, services, applications,
  deployment manifests, contracts, and acceptance runner.
- Historical Go: immutable import commit plus current Python characterization
  tests; no active compiler/build/image/database surface.
- BMad: exact optional npm artifact identity; installation is outside product
  builds and verification and no generated package payload is tracked.
- Adaptive workflow: immutable external gitlink plus a small fail-closed
  Liqvera launcher and compatibility symlinks.
- Verification: ordinary product tests remain independent of initialized
  tooling; `make verify-tooling` is the explicit strict integration suite.
  Every PR run discovers and scans all tracked Dockerfile/Compose inputs after
  the root Go Dockerfile disappears.

## Data flow

No runtime data flow changes. Submodule initialization is an explicit
developer action and cannot run from product build, import, or tests. Grok
hooks use only the validated pinned checkout.

## API and event contracts

No API, event, payment, state-machine, or artifact contract changes.

## Bitrix-specific impact

- Modules/events/agents/components affected: none.
- Cache and managed cache impact: none.
- Installation/update/uninstall impact: none.
- Core modification: forbidden unless explicitly approved.

## Decisions

- Preserve `provenance/import-manifest.json` byte-for-byte as the initial-import
  ledger.
- Remove only `migrations/000001_init.*`; retain A2
  `migrations/000002_a2_raw_capture.*` and every Liqvera migration.
- Pin Adaptive Grok `v2.0.19` because it is the first selected release with
  bounded parallel verification; validate the commit and version at runtime.
- Keep product verification authoritative over any optional agent framework.

## Risks and mitigations

- Lost Trivy coverage after root Dockerfile removal: explicitly enumerate all
  product Dockerfile and Compose inputs.
- Dangling graph/conformance references: retire or rebind them in the same
  coherent commit as source deletion.
- Supply-chain drift: exact package/git identities and integrity are mandatory;
  missing, dirty, or wrong-version tooling fails clearly without affecting
  product checks.
- Status inflation: preserve `IMPLEMENTED_UNVERIFIED`, 156 `NOT_RUN` vectors,
  and all payment/acceptance blockers.
