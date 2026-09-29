# Test plan — F5 local mocked state-machine verification

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Direct/reconciled receipt mismatch | paired manual review; one settle; no entitlement/body |
| P0 | Unknown settlement and reconciliation | uncertain state; confirm-only recovery; no resettle |
| P0 | Duplicate canonical identity | second use rejected before settlement |
| P1 | Pre-submit stale recovery | rejected attempt; ready/expired quote; zero settle |
| P1 | Confirmation, repeat read, reorg/finality | one entitlement; replay without settle; delivery withheld on inconsistency |
| P1 | Frozen invalid guards | `StateMachines.next` rejects unmet guards |

The frozen-guard case must load the packaged production contracts rather than
constructing a test-only state machine. Null reconciliation must assert the
event code and paired state both below the bound and when the leased SQL row
returns `reconciliation_count=10`; mismatch traces must fail if delivery is
inserted anywhere. Successful reconciliation must also prove the worker cannot
demote the atomic confirmation afterward: terminal state is
`CONFIRMED`/`PAID`, one entitlement is visible, the event is `CONFIRMED`, and
an immediate second lease is empty.

## Automated checks

- Unit: focused compiled Node test file with deterministic doubles.
- Integration: none; PostgreSQL and external transports are excluded.
- Contract: real `Contracts.load`/`states.json` where applicable.
- E2E: none; all 156 vectors remain `NOT_RUN`.
- Static analysis: gateway `typecheck`, `build`, then full pinned verifier.

## Manual checks

- Inspect fake event traces for begin/submit/settle/unknown/confirm ordering.
- Confirm migrations and frozen vectors are unchanged.
