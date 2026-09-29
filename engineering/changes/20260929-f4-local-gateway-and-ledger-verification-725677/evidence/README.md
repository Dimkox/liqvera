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

## Analysis synthesis

Five route-selected read-only reports initially concluded that no migration
was required. Real disposable-ledger execution later invalidated that narrow
conclusion and the user approved one forward-only 002 function repair. The
bounded change preserves migration 001 and the frozen vectors, fixes two
reproduced compile errors, and makes the gateway accept the report service's
two authoritative HTTP 200 cleanup outcomes (`deleted:true` and
`deleted:false`) only when the report ID and boolean type match. The test plan
uses loopback HTTP plus an invocation-owned disposable PostgreSQL database,
includes 20-way idempotency contention and lost-response convergence, and
keeps all payment/external boundaries fail closed. Residual build-deadline,
retryability, retention-lock-duration, and sealed-input recovery risks are
characterized rather than broadened into this repair.

## Scope amendment and TDD checkpoint

The exact gateway typecheck reproduced the two analysis errors:
`ajv-formats` was not callable under NodeNext typing, and `loadConfig` widened
`sourceMode` beyond `GatewayConfig`. Explicit CommonJS export normalization and
a typed runtime configuration repaired both without a dependency or lockfile
change. Gateway typecheck and build then passed.

The first cleanup test run reported two expected failures: `deleted:false` was
rejected, and an otherwise valid response with an unknown field was accepted.
The minimum adapter repair requires exactly `report_id` plus a boolean
`deleted`; the loopback suite reports three passing tests covering both absence
outcomes, mismatched/non-boolean/missing/extra fields, malformed JSON, and
non-200 responses.

The first disposable PostgreSQL run passed migration/checksum/append-only
checks and the 20-way idempotency race, then produced a new deterministic RED:
retention's artifact-state update failed with SQLSTATE `42703`, `record "old"
has no field "tx_hash"`. Migration 001's shared trigger function dereferences
payment-attempt fields for an artifact row. On 2026-09-29 the user explicitly
approved the required forward migration with “Делай”. That approval is bounded
to a minimal local-tested 002 function replacement; it does not authorize
editing 001, touching shared/production data, deployment, release, or any live
boundary.

## Focused green evidence

- Node `v24.21.0` / npm `11.19.0`: gateway typecheck and production build
  passed from the existing lockfile; no dependency or lockfile changed.
- Loopback cleanup contract: `3 passed`, covering exact `deleted:true` and
  `deleted:false`, mismatched/non-boolean/missing/extra fields, malformed JSON,
  and non-200 responses.
- Disposable `postgres:17-alpine` image
  `sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73`
  on Docker `29.8.1`: `5 passed`. The suite covered fresh 001-to-002 and rerun,
  an independently prepared 001-only upgrade, append-only audit enforcement,
  artifact/payment identity immutability, 20 simultaneous same-key creates,
  cross-scope/conflicting-body behavior, fail-closed `RECOVERY`, and the lost
  cleanup-response retry converging exactly once to `DELETED`.
- Migration SHA-256 values: 001
  `bc127e55c876961112f33ca2abdfac01827769d6156ddba2f42856d070c75b3b`;
  002 `981f48215e64fdd0fb72be5a6df78238cf8050de722adb454b4e28b1940ccbcb`.
  Frozen vectors remain
  `606a4a2a406c71456aa0ade984f613c10bdef46a6ac020a953b8d3b6386717cc`.
- The disposable container used no volume, bound PostgreSQL only to loopback,
  inherited no `DATABASE_URL`, and was removed; the final absence check passed.

These results are focused implementation evidence, not a full verifier receipt
or an assertion that any of the 88 F4-owned vectors changed from `NOT_RUN`.

<!-- checkpoint:initial -->
## Initial checkpoint

Local observation only; not verification or publication evidence.

```json
{
  "kind": "initial",
  "change_id": "20260929-f4-local-gateway-and-ledger-verification-725677",
  "route_id": "725677143509",
  "observed_at": "2026-09-29T08:16:51+00:00",
  "branch": "feat/f3-f7-verification",
  "head": "c30b0ffbda6cbae37b9dec16da2dec1346b0248b",
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
  "change_id": "20260929-f4-local-gateway-and-ledger-verification-725677",
  "route_id": "725677143509",
  "observed_at": "2026-09-29T08:45:23+00:00",
  "branch": "feat/f3-f7-verification",
  "head": "3f386bdbf9e2594bf541c17c2d63df573dd6859b",
  "detached": false,
  "git_available": true,
  "git_findings": [],
  "dirty_product_state": "dirty",
  "dirty_product_paths": [
    "README.md",
    "apps/mezo-gateway/.gitignore",
    "apps/mezo-gateway/README.md",
    "apps/mezo-gateway/migrations/002_fix_immutable_ledger_identity.sql",
    "apps/mezo-gateway/package.json",
    "apps/mezo-gateway/src/adapters/contracts.ts",
    "apps/mezo-gateway/src/adapters/report-service.ts",
    "apps/mezo-gateway/src/config.ts",
    "apps/mezo-gateway/test/postgres.test.ts",
    "apps/mezo-gateway/test/report-service.test.ts",
    "apps/mezo-gateway/tsconfig.test.json",
    "architecture/architecture.yaml",
    "decisions.md",
    "handoff.md",
    "mistakes.md"
  ],
  "note": "implementation started; preserve work before handoff"
}
```
