# Architecture — F3 offline artifact verification repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

The canonical F3 modules can complete a source-checkout fixture smoke path but
have no direct installed-boundary regression suite. Publication integrity,
tamper rejection, duplicate UUID behavior, and package resources are therefore
unproven. Separately, the runner records 40-hex Git OIDs while the acceptance
schema incorrectly requires 64-hex SHA-256 values for those fields.

## Proposed behavior

Characterize and test one local vertical: frozen fixture -> strict inspection
-> exact report -> deterministic bundle -> staged verification -> atomic
publication -> immutable readback -> offline recalculation. Change production
code only where a failing regression establishes a defect. Model Git identity
as a Git OID rather than relabeling or transforming it into a content digest.

## Components and boundaries

- `mee_public_capture`: local fixture package and exact manifest identity.
- `mee_evidence_report`: strict inspection, exact calculation, deterministic
  archive, atomic publisher, immutable reader, and archive-first verifier.
- `tools/mezo_acceptance/runner.py` and the acceptance-result JSON Schema:
  repository identity producer and consumer.
- Temporary test roots and an isolated package installation are the only
  writable runtime boundary. SQL stores and services are excluded.

## Data flow

Local frozen fixture -> captured byte snapshot -> canonical report resources ->
bounded deterministic ZIP -> verify staged files -> rename directory atomically
-> compare standalone report with verified bundled report -> recalculate exact
outputs. Failure before rename removes staging state and exposes no target.

## API and event contracts

Existing report, manifest, and reason-code schemas remain stable. The only
planned contract repair is an explicit Git OID definition for acceptance
`repository.commit` and `repository.tree`; true SHA-256 fields remain exactly
64 lowercase hexadecimal characters. No event, HTTP, or migration contract is
changed.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs:
- Applicable canonical example IDs/versions:
- Open or overdue debt IDs:
- Expected governance handoff or receipt impact:

## Decisions

- No migration, database, listener, network, wallet, payment, or external write.
- The canonical F3 implementation is tested; the older MVP aliases are not a
  substitute for this boundary.
- Verification proves relative integrity and exact recalculation only. Fixture
  output remains simulated, non-chargeable, and without execution authority.
- Existing complete artifacts are never repaired or overwritten in place.

## Risks and mitigations

- Source-import false green: exercise installed commands/resources outside the
  checkout import path.
- Split-brain report copies: independently tamper standalone and bundled bytes.
- Partial publication: inject pre-rename failures and assert no visible target.
- Retry ambiguity: reject duplicate publication and preserve original hashes.
- Scope expansion: migrations and external operations are explicit forbidden
  outcomes rather than test prerequisites.
