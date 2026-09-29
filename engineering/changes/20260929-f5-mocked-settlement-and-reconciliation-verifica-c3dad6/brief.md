# F5 mocked settlement and reconciliation verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f5-mocked-settlement-and-reconciliation-verifica-c3dad6`
Created: 2026-09-29T09:12:46+00:00
Risk: high
Complexity: high-risk
Domains: security, data

## Problem

Verify and repair the Liqvera F5 local mocked settlement and reconciliation boundary: exercise deterministic authorization reuse, pre-submit failure, unknown outcome, retry prohibition, receipt mismatch, reorganization, finality, entitlement, and recovery state transitions using in-process fakes and disposable local ledger state only. No wallet, chain RPC, facilitator, transfer, shared environment, deployment, release, exchange, or live execution.

## Outcome

Describe the observable user or business result.

## Scope

### In scope

-

### Out of scope

-

## Constraints

- Backward compatibility:
- Data/privacy:
- Performance:
- Operational:
