# Release plan — F4 local gateway and ledger verification

## Deployment

None in this change. The result is local verification evidence and a bounded
source repair only. Push, release, image publication, Compose startup, testnet,
and production actions are explicitly excluded.

## Feature flags / staged rollout

No flag is introduced. Payment readiness, unresolved identity/finality gates,
fixture chargeability rejection, and shadow-only behavior remain fail closed.

## Metrics and alerts

Existing stable reason metrics and audit events remain. Verification records
adapter outcomes, one effective cleanup audit transition, database invariant
queries, and zero payment-port calls; it does not claim production telemetry.

## Go/no-go criteria

This tranche is locally green only if focused gateway build/tests, disposable
database invariants, the full pinned verifier, and independent route-selected
reviews pass on one fingerprint. It is never a deployment/payment go decision.
