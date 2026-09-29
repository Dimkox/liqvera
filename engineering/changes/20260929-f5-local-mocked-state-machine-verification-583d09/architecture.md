# Architecture — F5 local mocked state-machine verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

`Gateway.read` durably marks `SUBMITTING` before its sole settlement call and
reconciliation never settles. However, a receipt-binding `PAYMENT_REJECTED`
raised by `Ledger.confirm` is treated as ordinary uncertainty: the direct path
and `reconcileOne` delay manual review even though frozen `inconsistent_receipt`
requires immediate escalation.

## Proposed behavior

Classify only post-confirmation `PAYMENT_REJECTED` and existing
`MANUAL_REVIEW` as inconsistent evidence at the two orchestration catch sites.
Call the existing atomic `manualReview` operation, retain the same fail-closed
HTTP response, and do not resettle or create entitlement/delivery state.

## Components and boundaries

- Production: `Gateway.read` and `reconcileOne`; no adapter/schema changes.
- Tests: structural `MemoryLedger`, scripted `PaymentPort`, test-only contracts,
  and per-test temporary `ArtifactStore`.
- Authority: the checked-in frozen `states.json` loaded by production
  `Contracts`; vectors remain descriptive `NOT_RUN` fixtures.

## Data flow

`READY -> VERIFIED -> SUBMITTING -> UNKNOWN`; authoritative confirmation may
atomically publish `CONFIRMED`/`PAID`, while a binding mismatch goes directly
to paired `MANUAL_REVIEW`. Recovery reads retained correlation and calls only
`confirm`. Paid reads revalidate before temporary artifact bytes are returned.

## API and event contracts

No public schema changes. Receipt mismatch remains public 202 uncertainty;
the repair changes durable internal classification to the frozen manual-review
state. No new event, endpoint, or database contract is introduced.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs:
- Applicable canonical example IDs/versions:
- Open or overdue debt IDs:
- Expected governance handoff or receipt impact:

## Bitrix-specific impact

- Modules/events/agents/components affected:
- Cache and managed cache impact:
- Installation/update/uninstall impact:
- Core modification: forbidden unless explicitly approved.

## Decisions

- Keep mismatch classification at orchestration boundaries; do not weaken
  `Ledger.confirm` or duplicate receipt validation.
- Use test doubles only to prove application ordering and fail-closed effects,
  not database durability or payment readiness.
- Record `MANUAL_REVIEW` recovery as unsupported residual rather than mock it
  into a false PASS.

## Risks and mitigations

- Overclaiming mock evidence: documentation explicitly preserves all 156
  vectors as `NOT_RUN` and unresolved production policies.
- Misclassifying pre-submit rejection: repair is limited to errors after an
  authoritative confirmation object reaches binding validation.
- Fake drift: tests call real gateway/reconciliation functions and frozen
  state guards, with call traces and negative assertions.
