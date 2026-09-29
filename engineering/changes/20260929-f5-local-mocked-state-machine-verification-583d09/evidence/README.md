# Evidence

Store human-readable review reports here. Machine receipts live under `.grok-stack/runtime/receipts/` and are bound to the current repository fingerprint.

`state.json` holds canonical local checkpoints and explicit evidence accounting. A `not_run` reason explains unfinished work; a recorded result is self-reported and does not satisfy a passing receipt. Checkpoints are observations in this worktree, and become available to another clone only when separately committed and published.

New-package and first-implementation observations are appended below by the lifecycle commands. A pending README mirror is surfaced in status and can be retried with the same explicit lifecycle command; state and README publication is not a two-file atomic transaction.

Code and test review reports perform bounded, change-relevant mutation probes in a reviewer-owned private scratch copy outside the reviewed worktree. Keep the reviewed candidate read-only; use scratch below a trusted non-sticky parent with mode `0700`. Reproduce the exact candidate (HEAD and relevant staged, unstaged, and untracked changes), record its HEAD and tree fingerprint before/after, and treat unsafe or mismatched snapshots and changed fingerprints as stale/inconclusive. Reviewer read-only configuration is not an OS-enforced isolation boundary.

Reviewers return the complete report to the coordinator out-of-band and do not write into the candidate worktree. After all reviews finish, the coordinator persists all reports here, then reruns final verification and records fresh fingerprint-bound receipts for the tree containing those reports.

Each report must include:

- source identity: HEAD and candidate tree fingerprint;
- scratch path and `reviewed-tree-modified: no`;
- each claim probed, exact command, concise observed output, and mutant outcome (`killed`, `survived`, or `inconclusive`);
- claims not executed and why; static claims without executable probes are unexecuted;
- surviving mutants as findings or explicit limitations (no blanket mutation-score threshold unless a scoped policy requires it).

## First review findings and repair

Independent review of `25c08a5` rejected three evidence gaps without changing
the reviewed tree: the test fixture replaced frozen `Contracts`/`StateMachines`
with no-ops, reconciliation did not exercise a null confirmation below and at
the returned count-ten boundary, and the mismatch trace did not prove that an
injected delivery call would be detected. The repair loads the packaged
`dist/contracts/` resources through production `Contracts.load`, proves one
valid scoped transition plus an unmet-guard `INVALID_STATE`, models the SQL
returned reconciliation count, asserts event codes at nine and ten, and makes
the mismatch trace reject any delivery. These are test-evidence repairs only;
no vector, migration, or production transition changed.

<!-- checkpoint:initial -->
## Initial checkpoint

Local observation only; not verification or publication evidence.

```json
{
  "kind": "initial",
  "change_id": "20260929-f5-local-mocked-state-machine-verification-583d09",
  "route_id": "583d09e0cf44",
  "observed_at": "2026-09-29T09:13:06+00:00",
  "branch": "feat/f3-f7-verification",
  "head": "c73b4cbdf685e213cfc856b30445b799a4c856a0",
  "detached": false,
  "git_available": true,
  "git_findings": [],
  "dirty_product_state": "clean",
  "dirty_product_paths": [],
  "note": "draft; implementation not started"
}
```

Initial evidence accounting (current records are in `state.json`):

```json
{
  "schema_version": 1,
  "obligations": [
    {
      "id": "verification",
      "kind": "receipt",
      "receipt_kind": "verification",
      "status": "not_run",
      "reason": "implementation not started"
    },
    {
      "id": "code_review",
      "kind": "receipt",
      "receipt_kind": "code_review",
      "status": "not_run",
      "reason": "implementation not started"
    },
    {
      "id": "test_review",
      "kind": "receipt",
      "receipt_kind": "test_review",
      "status": "not_run",
      "reason": "implementation not started"
    },
    {
      "id": "data_review",
      "kind": "receipt",
      "receipt_kind": "data_review",
      "status": "not_run",
      "reason": "implementation not started"
    }
  ]
}
```

<!-- checkpoint:implementation -->
## Implementation checkpoint

Local observation only; not verification or publication evidence.

```json
{
  "kind": "implementation",
  "change_id": "20260929-f5-local-mocked-state-machine-verification-583d09",
  "route_id": "583d09e0cf44",
  "observed_at": "2026-09-29T09:21:28+00:00",
  "branch": "feat/f3-f7-verification",
  "head": "4282302df0e10ffa3fe3ff96fa798615ebb51048",
  "detached": false,
  "git_available": true,
  "git_findings": [],
  "dirty_product_state": "dirty",
  "dirty_product_paths": [
    "apps/mezo-gateway/src/application/gateway.ts",
    "apps/mezo-gateway/src/workers/reconciliation.ts",
    "apps/mezo-gateway/test/state-machine.test.ts"
  ],
  "note": "implementation started; preserve work before handoff"
}
```
