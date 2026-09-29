# Requirements — F6 local UI and operations verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Acceptance criteria

- [ ] AC-001: deterministic browser tests drive the real UI orchestration with
  fake wallet/API/storage/crypto/timers and a test-only payment adapter; no
  real or cross-origin request is possible.
- [ ] AC-002: wrong-chain display and explicit switch to chain 31611 work;
  account or chain changes retain the saved payer/flow, visibly disable an
  ineligible payment, and never invoke payment implicitly.
- [ ] AC-003: a typed cancellation before submission clears the guard only
  after a fresh `READY` quote; ambiguous cancellation/error persists
  `uncertain`, hides repeat payment/new-report actions, and cannot resettle.
- [ ] AC-004: reload recovery reuses the same capability, request/quote IDs,
  body, and idempotency key; pending/uncertain/manual-review and paid recovery
  use GET paths only, with exactly zero additional adapter invocations.
- [ ] AC-005: paid report and evidence reuse validate receipt/report/bundle
  binding without a payment signature or second payment call; fixture
  capabilities remain non-chargeable even with a connected fake wallet.
- [ ] AC-006: statically resolved fixture Compose contains only fixture
  services, exact internal networks, loopback-only edge publication, separate
  synthetic-secret references, healthchecks, non-root/read-only/cap-drop
  controls, and bounded CPU/memory/PID/tmpfs; live resolution retains its
  explicitly live-only egress networks.
- [ ] AC-007: gateway metrics are reachable only from a private operations
  network, never published to the host or routed through Caddy; deterministic
  assertions cover required bounded metric names, safe labels, and the
  distinction between process health and payment readiness.
- [ ] AC-008: edge responses include the canonical restrictive CSP alongside
  existing security headers, and the built static application requires no
  unsafe inline script exception.
- [ ] AC-009: exact-lock web typecheck/test/build, focused static operations
  tests, and the pinned PR verifier pass; README, handoff, and runbooks match
  the evidence while all 156 vectors and A26/A30 remain `NOT_RUN`.

## Failure and edge cases

- Corrupt/inaccessible session storage fails closed; capability loss across a
  new browser session is documented and never triggers automatic payment.
- Lost create response may replay only the identical logical request with the
  same idempotency key. It may not mint a new request identity.
- Wallet events during guarded polling/payment update visible eligibility but
  never rebind the payer, clear uncertainty, or trigger submission.
- Cancellation clears a guard only from the typed pre-submission error plus an
  authoritative fresh `READY` GET. Failure to refresh stays uncertain.
- Every fake API handler rejects unexpected method/path/header/body and all
  cross-origin requests; adapter, POST, and recovery GET counts are asserted.
- Static Compose validation must fail on profile co-residence, external-egress
  membership in fixture, public internal ports, missing bounds/healthchecks,
  or fixture use of live values.
- The metrics endpoint must not be exposed by Caddy/host networking and must
  not include capabilities, wallet addresses, signatures, secrets, report IDs,
  or other high-cardinality sensitive labels.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: canonical TZ sections 9, 11, 13–15, F6, A26, and A30;
  shadow-only and no-second-payment invariants.
- Canonical-example deviations and evidence: production x402 remains absent;
  browser behavior is exercised through a test-only adapter and cannot prove
  real-wallet A30 acceptance.
- Intentional debt created, repaid, or accepted: runtime A26 isolation and
  disposable-container health evidence remain `NOT_RUN`; session-scoped
  capability loss remains a documented limitation.

## Non-functional requirements

- Security: CSP, loopback-only fixture edge, internal-only metrics, no fixture
  egress, no secrets, no real adapters or external requests.
- Reliability: exact invocation/request counts, bounded fake-time polling, and
  fail-closed recovery state across reload and wallet events.
- Performance: focused deterministic tests with no real sleeps; production
  bundle remains buildable without a new UI framework.
- Observability: stable bounded metric names and correlation-safe logs only;
  process health and payment readiness are tested as different signals.
