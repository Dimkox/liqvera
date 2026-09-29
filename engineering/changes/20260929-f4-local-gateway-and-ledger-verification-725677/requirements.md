# Requirements — F4 local gateway and ledger verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] The existing lockfile installs, the protocol prerequisite builds, and
  gateway typecheck/build pass without a dependency or lockfile change.
- [ ] A valid matching HTTP 200 cleanup body with `deleted:true` or
  `deleted:false` is authoritative evidence that the exact artifact is absent.
- [ ] Malformed JSON, missing/non-boolean fields, a mismatched report ID,
  timeout, disconnect, and non-200 responses cannot produce cleanup success.
- [ ] A lost first cleanup response followed by `deleted:false` advances only
  the matching expired/unpaid artifact to `DELETED` and records one effective
  `UNPAID_ARTIFACT_REMOVED` event while retaining scope, request, quote, and
  deduplication rows.
- [ ] A fresh disposable PostgreSQL database applies migration 001, a second
  migrator run is a checksum-valid no-op, and relevant constraints/triggers
  reject invalid mutation.
- [ ] Twenty simultaneous identical same-scope/key creates converge on one
  request/report ID and one rate-budget hit; a changed body conflicts and the
  same key in another scope remains isolated.
- [ ] Artifact-loss recovery remains fail closed: no fresh capture, settle,
  entitlement, or sale is produced from a missing/corrupt immutable artifact.
- [ ] `001_ledger.sql` and `schemas/mezo-evidence/v1/vectors.json` remain
  byte-identical to their pinned SHA-256 values.
- [ ] Focused gateway checks and the pinned full PR verifier pass on the final
  implementation fingerprint before independent review.

## Failure and edge cases

- Cleanup success whose response is lost before ledger commit.
- Already-absent exact artifact, malformed body, mismatched UUID, non-200,
  timeout, disconnect, and unavailable cleanup credential.
- Concurrent identical and conflicting idempotency requests across one and
  two capability scopes.
- Artifact read failure and unsuccessful recovery readback.
- Migration rerun/checksum protection and immutable ledger/audit constraints.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: canonical specification §§9–15, especially A15, A16,
  A21, A22 and the F4 stage boundary; ADR-0002.
- Canonical-example deviations and evidence:
- Intentional debt created, repaid, or accepted: characterize rather than fix
  equal build deadlines, erased build retryability, and retention I/O while
  holding row locks; real sealed-input recovery remains future work.

## Non-functional requirements

- Security: no external I/O or payment calls; capabilities and report IDs are
  synthetic; cleanup stays authenticated and exact-report scoped.
- Reliability: ambiguous outcomes preserve `AVAILABLE`; authoritative absence
  converges once; database identities and append-only audit evidence remain.
- Performance: 20-way contention test and existing four-build/bounded-cleanup
  limits; no scale claim beyond local disposable verification.
- Observability: retain stable reason codes, one effective removal audit event,
  exact test counts, build output, migration checksum, and disposable cleanup
  proof in evidence.
