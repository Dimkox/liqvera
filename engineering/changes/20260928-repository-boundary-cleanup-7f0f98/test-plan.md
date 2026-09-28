# Test plan — Repository boundary cleanup

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Active tree contains no Go or retired factory payload | tracked inventory test and graph |
| P0 | Product contracts/data remain byte-identical | base/final digest comparison |
| P0 | Python safety invariants still pass | focused conformance suite |
| P0 | Product container scan still covers every Dockerfile/Compose input | explicit-input regression plus Trivy output |
| P0 | Adaptive Grok rejects missing, dirty, or wrong-version gitlink state | launcher boundary tests |
| P1 | BMad has an exact external package identity without copied source | lock/inventory test |
| P1 | Product verification is independent of agent tooling | boundary test and product suite |

## Automated checks

- Unit: boundary classifier, lock/integrity, and fail-closed tests.
- Integration: graph, conformance, artifact boundary, and pinned gitlink.
- Contract: unchanged F2 schema/vector and migration-resource checks.
- E2E: no product acceptance claim; only clean-checkout contributor workflow.
- Static analysis: diff check, Ruff, secret scan, explicit Trivy config scan.

## Manual checks

- Compare protected path digests with base commit.
- Confirm README/handoff/provenance use current status without rewriting
  historical evidence.
- Confirm no external write, payment, deployment, push, tag, or release occurs.
