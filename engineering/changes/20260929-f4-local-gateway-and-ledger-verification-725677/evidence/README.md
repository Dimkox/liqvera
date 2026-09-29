# Evidence

Store human-readable review reports here. Machine receipts live under `.grok-stack/runtime/receipts/` and are bound to the current repository fingerprint.

`state.json` holds canonical local checkpoints and explicit evidence accounting. A `not_run` reason explains unfinished work; a recorded result is self-reported and does not satisfy a passing receipt. Checkpoints are observations in this worktree, and become available to another clone only when separately committed and published.

New-package and first-implementation observations are appended below by the lifecycle commands. A pending README mirror is surfaced in status and can be retried with the same explicit lifecycle command; state and README publication is not a two-file atomic transaction.

Code and test review reports perform bounded, change-relevant mutation probes in a reviewer-owned private scratch copy outside the reviewed worktree. Keep the reviewed candidate read-only; use scratch below a trusted non-sticky parent with mode `0700`. Reproduce the exact candidate (HEAD and relevant staged, unstaged, and untracked changes), record its HEAD and tree fingerprint before/after, and treat unsafe or mismatched snapshots and changed fingerprints as stale/inconclusive. Reviewer read-only configuration is not an OS-enforced isolation boundary.

Reviewers return the complete report to the coordinator out-of-band and do not write into the candidate worktree. After all reviews finish, the coordinator persists all reports here, then reruns final verification and records fresh fingerprint-bound receipts for the tree containing those reports.

The coordinator has now persisted the independent final PASS reports as
`code-review.md`, `test-review.md`, and `data-review.md`. All three bind their
review to clean HEAD `587bf5c0a5edd1712c4cd3cd3e4ade258fff8ffe` and tree
fingerprint `e88d85fbe2da4789b634f5d2c88bf73beeb9740274c566ba06297f8c1cb4c83b`,
state `reviewed-tree-modified: no`, and report no findings. They are
reviewer-provided outputs, not implementer self-review. Persisting and
registering them changes the tree fingerprint, so runtime receipts are
refreshed only after this evidence commit and again after durable state
transitions.

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

## Test-review P1 timeout repair

The independent test review identified that cleanup's two-second internal
deadline had no committed executable regression. The test-first run added a
100 ms delayed valid loopback response and attempted to inject a 20 ms cleanup
deadline. Before the production constructor accepted that deadline, `npm test
--prefix apps/mezo-gateway` failed the internal-deadline subtest with `Missing
expected rejection`; the delayed success arrived after roughly 100 ms and was
accepted. The separate caller-abort subtest rejected as expected.

The minimal repair gives `HttpReportService` a typed injectable cleanup timeout
whose production default remains 2000 ms and passes it to the existing
`boundedJson` signal composition. The focused rerun reported `11 tests`, `6
pass`, `5 skipped`, and `0 fail`; the skips are the explicit disposable-
PostgreSQL cases, while the internal-deadline and caller-abort subtests both
rejected the delayed success. Separate gateway typecheck and production build
commands exited 0. No dependency, lockfile, migration, vector, external, or
payment boundary changed. A pinned full verifier is run only against the clean
committed repair; independent review receipts remain coordinator-owned.

## Full verification

On clean implementation fingerprint
`55e3ce270b2cdc118ced8ca3daa9ab0bdab59e43`, pinned Adaptive Grok v2.0.19
reported `RESULT: PASS | mode=pr profiles=base,contracts,data | changed=70`.
Git diff, all three typed change specs, secret scan, contract structure, SQL
safety, nine `MEDIUM,HIGH,CRITICAL` Trivy targets, Ruff, Bandit, and source
stability passed. The 22-worker pytest invocation exited 0 in 71.457 seconds;
the fresh coverage invocation exited 0 in 1.255 seconds.

Persisting this report and advancing durable state changes the fingerprint, so
the verifier is rerun after the documentation-only commit. Independent code,
test, and data review remains the next coordinator-owned step; this implementer
does not self-review.

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
