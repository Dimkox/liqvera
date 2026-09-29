# Requirements — F3 offline artifact verification repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] An isolated installed canonical F3 package builds a deterministic exact
  report and bundle from the frozen fixture, publishes exactly two files, and
  passes the installed offline verifier with the expected report digest.
- [ ] Tampered report/bundle members and an incorrect trusted digest reject
  without claiming authenticity or execution authority.
- [ ] Reusing a report UUID or presenting a partial target rejects without
  replacing the original artifact; failures before atomic rename leave no
  visible target.
- [ ] A complete runner-shaped acceptance result containing the repository's
  real 40-hex Git commit and tree OIDs validates, while malformed OIDs and
  malformed 64-hex content digests reject.
- [ ] Focused checks and the full route verifier pass before independent code,
  test, and data review evidence is recorded.

## Failure and edge cases

- Missing/extra/unsafe archive members, report-vs-bundle split brain, duplicate
  publication (identical and differing input), existing partial targets,
  failures during staging/verification/rename, and invalid Git OID lengths.
- Repeated read-only verification is permitted; "replay rejection" means an
  attempt to publish the same report UUID again.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: fixture-only, immutable artifact, shadow-only,
  no-secret, and fail-closed verification boundaries in repository policy.
- Canonical-example deviations and evidence:
- Intentional debt created, repaid, or accepted: installed F3 fixture coverage
  does not establish live-source F3 acceptance or any F4-F7 completion.

## Non-functional requirements

- Security: no socket, subprocess-driven live operation, credential access,
  database, wallet, payment, or exchange mutation.
- Reliability: deterministic bytes, immutable UUID publication, atomic target
  visibility, and explicit rejection on integrity failure.
- Performance: retain bounded member count, member size, aggregate size, and
  archive structure checks.
- Observability: retain exact digests, reason codes, command exit status, and
  verification receipts tied to one tree fingerprint.
