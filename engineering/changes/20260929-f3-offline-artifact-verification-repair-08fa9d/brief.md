# F3 offline artifact verification repair

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

Change ID: `20260929-f3-offline-artifact-verification-repair-08fa9d`
Created: 2026-09-29T07:23:21+00:00
Risk: medium
Complexity: standard
Domains: data

## Problem

Repair the installed canonical F3 offline artifact-verification loop using local fixtures only: characterize resource builds and acceptance identity contracts, add regression coverage for exact bundle publication plus tamper, replay, partial-publication rejection, and fix discovered defects. No network calls, persistent stores, migrations, external writes, deployment, release, or live execution.

## Outcome

An installed evidence-report package can turn a frozen local fixture into an
exact immutable report and evidence bundle, publish the pair atomically, and
verify it offline. Corruption, duplicate publication, and incomplete output
fail closed. Acceptance results identify the actual Git commit and tree using
the same object-ID contract as their schema.

## Scope

### In scope

- The canonical fixture-only F3 build, bundle, publication, readback, and
  verifier path through installed package boundaries.
- Regression coverage for tamper rejection, duplicate report UUIDs, incomplete
  publications, packaged resources, and acceptance-result Git identities.
- The smallest repairs proven necessary by failing regressions.
- Fingerprint-bound local verification and independent route-selected review.

### Out of scope

- Network, live capture, HTTP services, RPC, wallet, facilitator, payment,
  exchange, browser, Compose, deployment, release, push, or GitHub mutation.
- Database use, SQL or migration changes, retained user state, and backfills.
- Gateway/F4, settlement/F5, UI/F6, broad acceptance/F7, graph cleanup, and
  broad refactoring.

## Constraints

- Backward compatibility: preserve inherited `mee-*` APIs and all F2 schemas
  except the demonstrated acceptance-result identity defect.
- Data/privacy: deterministic fixture bytes and invocation-owned temporary
  directories only; no credentials or production data.
- Performance: preserve existing strict member, byte, and archive bounds.
- Operational: no process may require network or persistent external state.
