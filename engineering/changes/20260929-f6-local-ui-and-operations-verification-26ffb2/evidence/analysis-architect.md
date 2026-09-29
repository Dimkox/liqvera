# F6 architecture analysis — local UI and operations boundary

Route: `26ffb293d4ff`
Analysis snapshot: `4b783a2f153c96d4775eca899757f0f21f421e95`
Role: read-only architecture analysis; this report is the only file written by the analyst.

## Sources inspected

- `.grok-stack/runtime/active-route.json` and the active change package
- `docs/planning/LIQVERA_FACTORY_TZ.md`, especially sections 9–16 and A30
- `docs/adr/0002-liqvera-report-payment-boundary.md`
- `apps/mezo-web/src/{api,contracts,main,session,wallet,x402}.ts` and its package/build configuration
- `apps/mezo-gateway/src/{main,routes/app,security/observability}.ts`
- `deploy/mezo-evidence/{compose.yaml,Caddyfile,nginx-web.conf,Dockerfile.*,gateway-entrypoint.js,env/*.example}`
- all current `docs/runbooks/*.md`

## Architectural ruling

F6 should be a deterministic verification-and-repair slice around the existing browser state machine and Compose topology. It must not install a real x402 browser adapter, relax readiness, contact a wallet/RPC/facilitator, run live-public capture, create a transfer, or change the payment ledger/schema. The authoritative payment/entitlement state remains in the gateway and PostgreSQL; browser `sessionStorage` is only a capability-scoped recovery pointer and local no-resubmit guard.

The smallest coherent vertical design is:

1. Extract or expose a testable browser controller boundary without changing API payloads. Drive it with a fake EIP-1193 provider, fake fetch responses, fake storage, and a reviewed-adapter test double. Production continues to have no registered x402 adapter and therefore remains fail-closed.
2. Add deterministic browser tests for A30 and the adjacent no-resettlement invariant. Do not emulate a blockchain; assert calls and rendered state at the browser/API boundary.
3. Repair only defects proven by those tests, keeping `GET` recovery distinct from the single payment submission call.
4. Statistically validate both resolved Compose profiles, then use disposable local containers only if the environment supports them. Use unique project names and generated non-production secret files; never start `live` and never publish beyond fixture loopback.
5. Repair fixture topology so it has no public-egress network membership, and make bounded gateway metrics observable only on an internal operations boundary if a local collection test requires it. Do not route metrics through Caddy or publish it on the host.

## Existing behavior and invariants worth preserving

- Quote creation requires `payment_ready`, `source_mode === "live-public"`, an account, Mezo Testnet, no active flow, and an installed reviewed adapter (`main.ts:137-153`, `552-567`). A fixture response cannot enable quote creation even if `payment_ready` is accidentally true.
- `paymentGuard` is persisted before entering the adapter. Every generic adapter error becomes `uncertain`; only `X402CancelledBeforeSubmission` plus a fresh server-side `READY` quote clears it (`main.ts:462-505`). This is the correct conservative cancel boundary.
- Wrong network is displayed explicitly and disables creation/payment. The switch operation requests only `wallet_switchEthereumChain` for `0x7b7b` (31611), then verifies the result (`wallet.ts`).
- Account and chain changes are observed. An account differing from the saved payer renders a warning and `quoteIsPayable` disables payment; the saved quote is not rebound (`main.ts:522-532`, `569-588`).
- Reload recovery loads the same capability/flow from `sessionStorage`, retrieves the saved request or quote, and reuses the original idempotency key only when the first create response may have been lost (`main.ts:422-459`).
- Recovery paths call status/quote/report GETs; they do not call `requestPaidReport`. `PAYMENT_PENDING`, `PAYMENT_UNCERTAIN`, `MANUAL_REVIEW`, and a non-clear guard hide the new-report action and offer no pay-again action (`main.ts:137-153`, `325-395`).
- A delivered report and evidence bundle are checked against the quote/receipt and bundle digest before display/download. Evidence retrieval is entitlement-scoped and does not carry a payment signature.
- API request bodies are bounded to 16 KiB; quote/read budgets are durable database buckets and do not trust forwarded IP headers. The browser uses no-store, omits credentials, and rejects redirects.
- Compose already uses non-root users, read-only roots, dropped capabilities, `no-new-privileges`, PID/memory/CPU limits, bounded tmpfs, healthchecks, profile-specific secret names, internal service networks, and a loopback-only fixture edge.

## Defects and gaps to prove before repair

### P0 — fixture profile inherits three external-egress attachments

The `x-capture`, `x-gateway`, and `x-edge` anchors include `capture_egress`, `payment_egress`, and `tls_egress` respectively. The fixture services inherit them unchanged. Consequently the supposedly deterministic fixture stack has routes to non-internal Docker networks even though its capture is simulated, payment is disabled, and its edge uses plain loopback HTTP. This conflicts with the requested fixture-profile isolation and with the fail-closed intent of A26/F6.

Bounded repair: override `networks` on each fixture service so capture has only `capture_report`, gateway has only `edge`, `gateway_db`, and `gateway_report`, and fixture edge has only `edge`. Retain the egress networks exclusively on the corresponding live services. Add a static resolved-Compose assertion that every fixture service has the expected exact network set and no service from the other profile is materialized.

### P1 — metrics exist but have no collection boundary

The gateway metrics server listens on `127.0.0.1:9090` inside the gateway container. It is neither exposed to another internal service/network nor reachable from the host, while the runbook says to collect the listed metrics. This makes the metrics contract aspirational rather than locally verifiable. Logs remain available through container stdout and are correctly allowlisted.

Bounded choices for the implementation owner:

- Preferred if local metrics collection is in this slice: bind metrics to a dedicated configured internal address/port, expose it only to a private operations network or a same-profile local collector, never Caddy/host; test that Caddy cannot route `/metrics` and the rendered metrics have no high-cardinality or secret labels.
- Otherwise document the current metrics endpoint as process-local and explicitly record external collection as not implemented. Do not claim observability PASS from metric definitions alone.

This choice belongs within the scope/design gate because adding a collector is a topology change. A collector dependency is not justified merely to close F6; a direct internal probe from a disposable test container is sufficient.

### P1 — no browser test harness or existing A30 evidence

`apps/mezo-web/package.json` has build/typecheck only and no browser/component tests. The UI logic is concentrated in a side-effectful `main.ts`, so the safety behavior is reviewable but not deterministic evidence. Add the smallest browser-capable test harness already acceptable to the repository (for example Vitest + jsdom for controller behavior, with Playwright only for the critical rendered flow if available). Do not add a broad UI framework or copy the app.

### P1 — operational assertions are prose-only

Resource bounds, healthchecks, only-one-profile isolation, no published internal ports, and fixture non-chargeability are not backed by static tests. Compose rendering should be tested without starting live services. A disposable fixture-container smoke may check edge `/healthz`, gateway `/readyz` fail-closed, capabilities fixture/non-payable, and cleanup, but a green liveness response must not be called payment readiness.

### P2 — security headers are incomplete at the edge

The specification requires CSP. Caddy sets nosniff, no-referrer and deny-frame headers but no CSP. This is adjacent to F6 browser/operations scope and can be repaired by a restrictive static-app CSP after confirming the Vite output needs no unsafe inline script. Keep API responses `private, no-store` at the gateway. This must be covered by a deterministic header assertion rather than visual inspection.

### Residual, not an F6 repair

- The production x402 browser adapter is deliberately unregistered; F6 must not implement or authorize it. Deterministic tests may register a local test double only.
- `sessionStorage` recovery ends with the browser session by design. Closing the session can lose the capability; do not silently broaden persistence to localStorage.
- Compose bridge networks do not enforce destination allowlists. Host egress ACLs remain a live-deployment prerequisite, not something disposable fixture tests can prove.
- Base images are tag-pinned, not digest-pinned, and current npm audit findings remain release blockers. Do not mislabel a local F6 pass as release readiness.
- Real A13/A14/A30 live-payment evidence remains `BLOCKED_EXTERNAL`; local mocks can validate UI behavior but cannot turn those acceptance rows into live PASS.

## Deterministic scenario contract

| Scenario | Stimulus | Required observable result | Forbidden call |
| --- | --- | --- | --- |
| Cancel before submission | adapter throws `X402CancelledBeforeSubmission`; GET quote returns `READY` | guard returns to `clear`; cancel message; same quote remains payable | settlement retry or new quote |
| Ambiguous cancel/error | cancel/error plus quote refresh unavailable or non-READY | guard becomes `uncertain`; pay button absent; check-status guidance | second adapter invocation |
| Wrong network | provider reports any chain except 31611 | explicit wrong-network text and switch action; create/pay disabled | create quote or payment adapter |
| Network switch | provider accepts switch and then reports 31611 | Mezo label and normal controls, subject to all other gates | implicit payment |
| Account switch | `accountsChanged` differs from saved payer | warning; old quote remains bound; pay disabled | quote rebinding or new settlement |
| Chain switch away | `chainChanged` reports non-31611 | wrong-network warning; pay disabled; flow preserved | payment adapter |
| Reload before create response | saved flow has no IDs | same body/capability/idempotency key is submitted once to recover server result | new idempotency key |
| Reload with request/quote | saved request or quote ID | GET status/quote/report; same flow rendered | POST quote or settlement |
| Pending/uncertain/manual review | server returns those states | no new-report/pay action; “do not pay again” recovery text | payment adapter |
| Paid reload | quote is `PAID`, entitlement GET succeeds | same report/receipt displayed; bundle GET available | payment signature or settlement |
| Wallet events during busy work | account/chain changes while polling/payment is guarded | final controls reflect current wallet and saved payer; guard remains conservative | implicit resubmit |
| Fixture profile | resolved Compose fixture config | no public egress memberships, loopback-only edge, blank `PAY_TO`, fixture source | live services or live source |
| Health/limits | resolved config and disposable fixture smoke | all services bounded; health distinct from readiness; readiness stays false for payment | readiness fabricated true |
| Observability | synthetic safe events/metrics | stable counters/correlation IDs and no secrets/wallet labels | public metrics route or sensitive values |

Count adapter invocations, quote POSTs, quote/status/report GETs, and evidence GETs explicitly. “No resettlement” is proven only when the fake adapter is called once and subsequent recovery uses GET endpoints exclusively.

## Component and contract boundaries

- **Browser view/controller:** owns rendering, input validation, wallet event response, local recovery pointer, and invocation gating. It never invents entitlement or receipt truth.
- **EIP-1193 adapter:** read account/chain and request an explicit chain switch. No test may use a real injected wallet.
- **x402 boundary:** production remains absent/fail-closed. The deterministic fake returns controlled success/recovery/cancel outcomes and records invocation count; it must never form a real `PAYMENT-SIGNATURE`.
- **Gateway HTTP API:** existing OpenAPI/state contracts remain unchanged. Recovery must use existing GET endpoints and the original bearer capability.
- **Compose fixture:** disposable, simulated, non-chargeable, no external egress, loopback edge only. Database/files exist solely in unique local project volumes and are removed after evidence capture.
- **Live profile:** static render validation only in this route. No container start, DNS, TLS, RPC, facilitator, capture, wallet, or payment.

No database migration, backfill, schema edit, or external write is architecturally necessary for this repair.

## Human gates

1. `scope_and_design_approval` is required by the route before the write owner changes product files. The approval should bind specifically to deterministic browser fakes, static Compose checks, optional disposable fixture containers, and the exact no-live exclusions above.
2. `migration_or_external_write_approval` is not triggered by the proposed design because it requires no migration and no external write. It must remain unexercised/fail-closed. Any discovery requiring schema mutation, real network activity, a shared environment, or a payment must stop and request a new exact approval; it cannot be inferred from scope approval.

## Rollback and forward recovery

- Browser test/controller/config changes are stateless and can be reverted as one coherent commit after rerunning the pre-F6 build/typecheck.
- Compose topology/header changes are reverted at source and validated by rendering both profiles. Disposable fixture containers use a unique project name and contain no accepted payment state; clean them up only after saving test evidence. Never apply `down --volumes` to any non-disposable or ambiguous project.
- No ledger migration means no data rollback. If a test unexpectedly touches a real/shared endpoint, stop immediately, preserve logs and project identity, and treat it as an incident rather than deleting evidence.
- If the observability topology is changed, rollback is source-only; metrics loss must not affect gateway payment correctness or readiness.

## Recommended acceptance boundary for F6

F6 may be called locally verified only when deterministic browser tests, web build/typecheck, static resolved-Compose assertions, safe header/observability checks, and any authorized disposable fixture smoke all pass on the same tree; selected independent reviews and the full repository verifier then bind the evidence. This does not authorize deployment/release, enable the x402 adapter, or satisfy live A13/A14/A30.
