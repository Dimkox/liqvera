# Test plan — F3-F7 verification and defect repair

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Resource/package/factory/graph characterization | command log and classified failures |
| P0 | Installed F3 fixture -> report -> bundle -> publish -> verify | isolated-wheel integration test |
| P0 | Tampered bytes/manifest/replay and interrupted publication | failing regression/mutation tests |
| P0 | Acceptance Git/tree identity schema consistency | schema validation test |
| P1 | Loopback capture/report service boundaries | no-network service tests |
| P1 | Existing Stage A/F2 regressions | focused and full pytest-xdist verification |

## Automated checks

- Unit: exact arithmetic, canonical serialization, hash/manifest and error paths.
- Integration: installed wheels in isolated venv; disposable temp dirs/SQLite.
- Contract: JSON Schema, package resources and acceptance-result validation.
- E2E: fixture-only offline vertical; no external service.
- Static analysis: Ruff, Bandit, graph/factory/resource inventory, typechecks
  where dependencies are installed without lifecycle scripts.

## Manual checks

- Inspect produced hashes and artifact members; confirm no network/process
  target outside declared local tools. Live acceptance remains unexecuted.
