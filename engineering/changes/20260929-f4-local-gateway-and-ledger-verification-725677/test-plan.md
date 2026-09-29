# Test plan — F4 local gateway and ledger verification

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Reproduce both compile errors, then pass protocol/gateway typecheck and build from the existing lock | build log |
| P0 | Matching HTTP 200 cleanup with `true` and `false`; reject malformed, mismatched, non-200 and timeout | adapter regression |
| P0 | Lost first response then already-absent retry advances ledger once | disposable PostgreSQL retention regression |
| P0 | Fresh 001→002 apply, 001-only upgrade, rerun/checksums and selected invariants | disposable PostgreSQL suite |
| P0 | 20-way same-scope/key/body convergence, conflicting body, cross-scope isolation | disposable PostgreSQL race test |
| P1 | Missing/corrupt artifact stays fail closed in `RECOVERY` with zero payment/build action | characterization test |
| P1 | Existing contracts/conformance and full selected PR profiles remain green | pinned verifier |

## Automated checks

- Unit: config typing and strict cleanup-response parsing through real adapter.
- Integration: real Ledger/retention behavior on a uniquely disposable
  PostgreSQL instance; in-process boundary fakes only.
- Contract: frozen OpenAPI/resource error behavior plus private cleanup
  request/status/body semantics.
- E2E: local gateway build and migrator; no live/public/testnet end-to-end.
- Static analysis: TypeScript strict typecheck, repository verifier, migration
  and vector digest checks, diff/secret/SQL/contract gates.

## Manual checks

- Confirm the disposable database/container no longer exists after the test.
- Inspect the final diff for only the approved 002 migration, no 001/vector/
  lockfile change, no external URL, and no weakening of payment or shadow-only
  gates.
- Record Node/npm/PostgreSQL identities and exact pass/fail counts without
  marking frozen vectors `PASS` unless they were actually executed and mapped.
