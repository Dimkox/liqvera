# F5 repository exploration

Route: `583d09e0cf44`
Role: read-only `repo_explorer`
Date: 2026-09-29

## Result

The F5 runtime is present, but it has no executable gateway-owned tests. The
only two files under `apps/mezo-gateway/test/` exercise the F4 cleanup adapter
and disposable PostgreSQL ledger checks. `npm test` therefore reports 6 passes
and 5 explicitly skipped PostgreSQL cases; it does not instantiate
`Gateway.read`, `OfficialX402`, `MezoReceiptReader`, `reconcileOne`, or
`recoverUnsubmitted`.

The minimum local tranche should add an in-process fake ledger/payment/artifact
harness and characterize the existing fail-closed boundaries without enabling
the unresolved production identity or finality policies. No schema or migration
change is indicated by this analysis.

## Reproduced defect: inconsistent receipt does not enter manual review

`Gateway.read` correctly persists `SUBMITTING` before its sole `settle` call and
changes the attempt to `UNKNOWN` before confirmation. However, when the
confirmation is structurally valid but `Ledger.confirm` rejects its quote,
report, digest, attempt, network, asset, amount, payer, or receiver binding with
`PublicError('PAYMENT_REJECTED')`, the catch block only sends
`MANUAL_REVIEW` errors to `ledger.manualReview`. It converts every other error
to HTTP 202 `PAYMENT_UNCERTAIN` and leaves the quote/attempt in
`PAYMENT_UNCERTAIN`/`UNKNOWN`.

A local, import-only fake invocation of the built `Gateway` used a successful
single settlement followed by a `Ledger.confirm` binding rejection. Observed:

```json
{"error":"PAYMENT_UNCERTAIN","status":202,"settle":1,"unknown":2,"manual":0}
```

This conflicts with the frozen state graph: quote event
`inconsistent_receipt` is `PAYMENT_PENDING -> MANUAL_REVIEW`, with effects
`retain_artifacts` and `prohibit_resubmit`. The same delayed behavior exists in
`reconcileOne`: a `PAYMENT_REJECTED` from `Ledger.confirm` is swallowed until
the reconciliation count reaches ten. A receipt-binding mismatch is positive
inconsistency evidence, not a merely absent receipt, and should move both quote
and attempt to manual review immediately.

The smallest repair belongs at the two orchestration catch sites, not in SQL:
treat a `PAYMENT_REJECTED` raised after confirmation as manual-review evidence,
while preserving HTTP 202 and never calling settlement again. A regression
must prove `settle` remains exactly one call, no entitlement/delivery is
created, and both direct and reconciliation paths invoke manual review once.

## Existing safety properties to characterize

- Canonical authorization identity has a database-wide unique constraint, and
  `beginAttempt` rejects reuse before settlement with `AUTHORIZATION_REUSED`.
- The partial unique index `one_active_attempt` plus the quote row lock prevents
  concurrent active attempts for one quote.
- `markSubmitting` is the durable boundary before the only external settlement
  call. Recovery and HTTP replay contain no settlement call.
- A stale `RECEIVED`/`VERIFIED` attempt is rejected by `recoverUnsubmitted`, and
  its quote returns to `READY` or advances to `EXPIRED`.
- A `SUBMITTING`/`UNKNOWN` attempt is reconciled read-only; no confirmation
  leaves it uncertain and the tenth bounded pass advances it to manual review.
- `Ledger.confirm` writes chain event, immutable receipt, entitlement, attempt,
  quote, and audit event in one transaction. Receipt bindings are checked before
  those inserts.
- Paid reads require the exact scope/report/digest entitlement, a confirmed
  attempt, unexpired retention, current revalidation/finality, and intact
  artifact bytes. Revalidation false or a reorganization/RPC conflict withholds
  delivery and advances to manual review.
- Repeat report and evidence reads take the existing entitlement path and do not
  call `verify` or `settle` again.

## Required local tests

At minimum, the fake suite should cover:

1. duplicate canonical authorization: second use rejected, zero additional
   settlement calls;
2. failure before the durable submit boundary: stale verified attempt closes
   and quote becomes ready/expired without settlement;
3. settlement error or missing hash after `SUBMITTING`: uncertain state and no
   automatic resubmission;
4. reconciliation with no receipt: bounded retry only, settlement count stays
   unchanged;
5. mismatched receipt in direct and reconciliation paths: immediate manual
   review, no entitlement or delivery;
6. confirmed receipt: one atomic entitlement and paid state;
7. repeat access: same entitlement/receipt, zero further settlement;
8. revalidation false or `MANUAL_REVIEW` conflict: paid delivery withheld and
   manual review entered;
9. expired retention, missing entitlement, digest mismatch, and artifact read
   failure: no paid bytes;
10. finality absent versus confirmed, including exactly one matching transfer.

The fake contracts should record call counts and event ordering. They must not
initialize `OfficialX402`, contact the facilitator/RPC, use a wallet, run a
transfer, or relabel these local cases as the 156 frozen acceptance vectors.

## Verification performed

```text
cd apps/mezo-gateway && npm test
tests 11; pass 6; fail 0; skipped 5
```

The build and TypeScript compilation passed as part of that command. The five
skips are expected without an explicitly disposable PostgreSQL URL. This is a
green F4 baseline only, not F5 evidence.

## Residual boundaries

`unresolvedIdentity` and `unresolvedFinality` intentionally keep real payment
readiness false. Local fake verification must not alter those defaults or claim
facilitator, chain-finality, transfer, testnet-payment, deployment, release, or
live acceptance readiness.
