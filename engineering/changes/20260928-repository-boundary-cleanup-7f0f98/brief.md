# Repository boundary cleanup

Change ID: `20260928-repository-boundary-cleanup-7f0f98`
Created: 2026-09-28T19:57:52+00:00
Risk: medium
Complexity: standard
Domains: integration, data

## Problem

Remove inherited Go Stage-0 code and replace vendored Grok/BMad factory sources with a minimal pinned external integration, while preserving Liqvera product behavior, provenance, contributor safety gates, and verification capability.

## Outcome

The active checkout contains Liqvera product code and product-specific
verification rather than an executable Go predecessor and hundreds of copied
agent-framework files. Historical material remains recoverable from immutable
Git provenance, and no product status or safety boundary is promoted.

## Scope

### In scope

- Retire the Go Stage-0 source, root Go image, and its unused Stage-0 database
  migration from the active tree.
- Preserve the five useful invariants through current Python tests and an
  immutable reference to import commit
  `8734907d489168a8a6567b93bc85920001fefd85`.
- Remove the generated BMad installation and replace it with an optional,
  integrity-pinned `bmad-method@6.10.0` local bootstrap.
- Decide whether to retire Adaptive Grok automation or retain only a minimal
  local kernel until a real external artifact exists.
- Update current graph, documentation, provenance, verification, and local
  worktree hygiene to match the chosen boundary.

### Out of scope

- F3-F7 behavior, acceptance closure, payment, deployment, or release.
- Product API, schema, vector, fixture, PostgreSQL ledger, SQLite demo, or A2
  migration changes.
- Publishing a new external factory artifact or inventing an upstream pin.
- Rewriting Git history or deleting historical planning/evidence.

## Constraints

- Backward compatibility: product packages, commands, contracts, and stored
  artifact formats remain unchanged.
- Data/privacy: no database access, DDL, backfill, credential read, or external
  mutation.
- Performance: ordinary product verification must not download agent tooling.
- Operational: shadow-only and testnet fail-closed boundaries remain intact;
  removed source remains recoverable from Git.
