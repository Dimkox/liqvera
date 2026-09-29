# Architecture — F3-F7 verification and defect repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

F3-F7 surfaces are integrated but unverified. Source-level F3 smoke checks pass,
while the graph reports six declared conflicts and 26 implementation orphans.
The canonical installed F3 path lacks direct coverage. The acceptance runner
emits 40-character Git object IDs while its schema requires 64-character
digests. Gateway and browser dependencies are not installed in a fresh tree.

## Proposed behavior

This tranche characterizes Phase 0 and repairs only the canonical installed F3
offline vertical. Later F4-F7 phases consume its immutable artifact contract;
they do not run in this tranche.

## Components and boundaries

- `mee_public_capture`: fixture input and strict capture identity.
- `mee_evidence_report`: exact report, deterministic bundle, atomic publisher,
  internal loopback service and offline verifier.
- acceptance schema/runner: consistent repository identity representation.
- graph/factory/resource manifests: truthful ownership and dependency evidence.
- SQLite may be used only in disposable local tests. PostgreSQL and settlement
  adapters remain outside this tranche.

## Data flow

Frozen fixture package -> strict inspection -> exact report -> temporary
report/bundle -> integrity verification -> atomic publish -> installed offline
verification. Any failure removes or quarantines the temporary output and never
changes payment or entitlement state.

## API and event contracts

F2 OpenAPI and state graphs remain unchanged. This tranche consumes the report,
bundle, reason-code and acceptance-result schemas; contract edits are limited to
repairing a demonstrated internal inconsistency.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs:
- Applicable canonical example IDs/versions:
- Open or overdue debt IDs:
- Expected governance handoff or receipt impact:

## Decisions

- No migration by default. Never edit applied `001_ledger.sql` in place.
- No network, live capture, RPC, facilitator, wallet or payment operation.
- Offline/mock results cannot satisfy live acceptance cases.
- First behavioral slice is installed canonical F3, not gateway or UI.

## Risks and mitigations

- False green from source imports: build/install artifacts and test outside the
  checkout import path.
- Partial artifact publication: inject failures at write/fsync/rename boundaries.
- Contract drift: validate every produced artifact against committed schemas.
- Scope creep into payment: hard fail on network/external-write attempts.
- Later data defect already identified (`deleted:false` recovery mismatch):
  retain as a characterized F4 follow-up, not a reason to open DB scope here.
