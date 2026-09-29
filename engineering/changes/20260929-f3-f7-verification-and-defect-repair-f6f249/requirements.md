# Requirements — F3-F7 verification and defect repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] Phase 0 commands have deterministic results and every failure is either
  repaired in scope or recorded with an owner and stop condition.
- [ ] An installed canonical F3 fixture package produces exact immutable report
  and bundle artifacts that pass the installed offline verifier.
- [ ] Byte, manifest and replay tampering are rejected without publishing a
  partial artifact or silently falling back to simulated/live data.
- [ ] The acceptance result contract uses one explicit Git/tree identity format
  consistently between runner and JSON Schema.
- [ ] Full route verification and independent code, test, security, data and
  release reviews bind the final tree with zero evidence gaps.

## Failure and edge cases

- Missing resources, stale/invalid identity, crossed book, insufficient depth,
  path races, partial writes, repeated publication and verifier replay.
- Dirty worktree and absent local build dependencies must be distinguished from
  product defects.
- Live-only acceptance cases remain `BLOCKED_EXTERNAL`, never `PASS`.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: shadow-only, no-secret, immutable-artifact and
  fail-closed payment boundaries from repository policy.
- Canonical-example deviations and evidence:
- Intentional debt created, repaid, or accepted: F4-F7 runtime matrices remain
  subsequent tranches; no new debt may weaken F3 artifact integrity.

## Non-functional requirements

- Security: no external writes, wallet signing, credential reads or live HTTP.
- Reliability: atomic publication, deterministic retries and explicit errors.
- Performance: bounded fixture/artifact sizes and no unbounded retry loop.
- Observability: commands, exit codes, hashes and reason codes in evidence.
