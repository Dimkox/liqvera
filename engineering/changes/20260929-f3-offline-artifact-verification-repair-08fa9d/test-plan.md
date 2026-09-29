# Test plan — F3 offline artifact verification repair

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Complete runner-shaped result accepts real Git OIDs and rejects malformed identities/digests | acceptance schema regression |
| P0 | Installed fixture -> report -> bundle -> publish -> read -> verify | isolated installed-boundary regression |
| P0 | Report/member/expected-digest tamper fails closed | verifier negative regressions |
| P0 | Duplicate UUID and partial publication cannot overwrite or expose an incomplete artifact | publication failure regressions |
| P1 | Existing report/capture/analyzer/contracts remain green | focused suites and full PR verifier |

## Automated checks

- Unit: Git OID schema boundaries; archive and publication failure branches.
- Integration: canonical F3 using fixture files under temporary roots.
- Contract: acceptance result, report, and bundle manifest JSON Schemas.
- E2E: installed local wheel entry points outside checkout imports, if local
  pinned build dependencies are available without network acquisition.
- Static analysis: route-selected PR profiles, including Ruff and Bandit.

## Manual checks

- Inspect exact artifact membership and digests. Confirm the final diff contains
  no migration, database, network, deployment, payment, or exchange change.
