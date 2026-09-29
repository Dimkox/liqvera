# Requirements — F5 local mocked state-machine verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] AC-001: gateway-owned Node tests execute real `Gateway.read`,
  `reconcileOne`, `recoverUnsubmitted`, and frozen state guards with only
  deterministic fakes and temporary files.
- [ ] AC-002: direct and reconciliation receipt-binding `PAYMENT_REJECTED`
  paths immediately move quote and attempt to `MANUAL_REVIEW`, return no paid
  body, create no entitlement, and keep settlement count exactly one.
- [ ] AC-003: duplicate canonical use, definitive pre-submit rejection,
  post-submit unknown/no-hash outcomes, bounded reconciliation, confirmation,
  repeat reads, and reorg/finality withholding are characterized without
  resettlement.
- [ ] AC-004: exact-lock gateway build/typecheck/tests and the pinned PR
  verifier pass; frozen vectors remain byte-identical and `NOT_RUN`.

## Failure and edge cases

- A generic pre-submit throw is not proof of no broadcast; only the explicit
  stale `RECEIVED`/`VERIFIED` recovery path may reject and reopen/expire.
- Missing/non-final confirmation remains uncertain; it cannot mint an
  entitlement or release bytes.
- Receipt mismatch/reorg is retained evidence requiring manual review, not a
  retryable rejection.
- `MANUAL_REVIEW -> PAID/CONFIRMED` recovery is residual until a separately
  approved persistent/idempotent design makes it reachable.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: frozen quote/attempt/delivery transitions in
  `schemas/mezo-evidence/v1/states.json`.
- Canonical-example deviations and evidence:
- Intentional debt created, repaid, or accepted:

## Non-functional requirements

- Security: never initialize production x402/RPC/wallet adapters.
- Reliability: assert ordered calls, exact settle count, and absent delivery.
- Performance: no wall-clock sleeps; bounded deterministic tests.
- Observability: fake event traces plus exact public error/status assertions.
