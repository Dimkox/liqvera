# F3-F7 verification and defect repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f3-f7-verification-and-defect-repair-f6f249`
Created: 2026-09-29T05:39:08+00:00
Risk: high
Complexity: high-risk
Domains: security, data

## Problem

Verify and repair the already integrated Liqvera F3-F7 product engine in dependency order, beginning with factory/resource builds, typechecks, graph, canonical F3 evidence runtime, F4 gateway/concurrency/artifact-loss paths, mocked F5 settlement faults, F6 browser/Compose/security flows, and F7 offline acceptance; keep live payment, deployment, release, and exchange mutation disabled.

## Outcome

Establish a reproducible offline baseline for the integrated product engine and
repair the first canonical vertical: an installed F3 fixture package can be
strictly inspected, converted into exact report and bundle artifacts, published
atomically, verified offline, and rejected after tampering. Failures outside
this tranche remain named evidence, not inferred success.

## Scope

### In scope

- Phase 0 characterization: resource/package builds, typechecks, graph and
  acceptance-runner contract consistency.
- Phase 1A canonical installed F3 offline vertical and A08/A09 tamper/replay
  behavior.
- Minimal defects required to make those checks deterministic and fail closed.
- Documentation and evidence updates bound to the final tree.

### Out of scope

- PostgreSQL migration execution or modification of applied `001_ledger.sql`.
- F4 shared/persistent database writes; F5 live SDK/facilitator/RPC/payment;
  F6 Compose start with external services; deployment, release or merge.
- Live capture, wallet signatures, testnet funds, exchange mutation, or claims
  that offline/mocked evidence closes A07, A13, A14, A29 or A30.
- Broad refactoring or implementation of new product behavior unrelated to a
  reproduced verification failure.

## Constraints

- Backward compatibility: preserve F2 schemas and public package/API names.
- Data/privacy: fixture-only inputs; no credentials or production data.
- Performance: deterministic bounded artifacts and existing build deadline.
- Operational: ephemeral/local files only; no network or shared service write.
