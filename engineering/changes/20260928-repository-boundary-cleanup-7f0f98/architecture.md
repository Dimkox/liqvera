# Architecture — Repository boundary cleanup

## Current behavior

Go Stage-0 remains an inactive executable specification coupled to the graph
and conformance metadata. BMad and Adaptive Grok implementation payloads are
vendored as 403 tooling paths; product code does not import either layer.

## Proposed behavior

Go is absent from the active tree and referenced only by immutable historical
provenance. BMad is optional and external at exact version `6.10.0`. Product
verification stays repository-owned and offline. Adaptive Grok has no honest
external identity yet, so implementation must use one of two explicit designs:

1. retire adaptive route/receipt automation and replace its safety obligations
   with project-owned policy and verification; or
2. retain a characterization-tested minimal local kernel as temporary debt.

The owner decision is pending. A Grok CLI version, hook behavior label, or
private source commit is not an acceptable substitute for a package pin.

## Components and boundaries

- Product: unchanged Python/TypeScript packages, services, applications,
  deployment manifests, contracts, and acceptance runner.
- Historical Go: immutable import commit plus current Python characterization
  tests; no active compiler/build/image/database surface.
- BMad: exact optional npm artifact installed only by an explicit command into
  an ignored local directory.
- Adaptive workflow: either formally retired or reduced to the minimum local
  implementation that proves route/policy/receipt behavior.
- Verification: `make verify` remains independent; product Dockerfile/Compose
  scanning becomes explicit when the root Go Dockerfile disappears.

## Data flow

No runtime data flow changes. Tool bootstrap, if retained, is an explicit
developer action and cannot run from product build, import, tests, or hooks.

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
- Never infer an Adaptive Grok pin from unrelated version labels.
- Keep product verification authoritative over any optional agent framework.

## Risks and mitigations

- Lost Trivy coverage after root Dockerfile removal: explicitly enumerate all
  product Dockerfile and Compose inputs.
- Dangling graph/conformance references: retire or rebind them in the same
  coherent commit as source deletion.
- Supply-chain drift: exact package identity and integrity are mandatory;
  missing tooling fails clearly without affecting product checks.
- Status inflation: preserve `IMPLEMENTED_UNVERIFIED`, 156 `NOT_RUN` vectors,
  and all payment/acceptance blockers.
