# Architecture — F6 local UI and operations verification

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

The browser already persists a capability and versioned flow in
`sessionStorage`, guards submission before calling the adapter, and recovers
identified requests/quotes/reports through the gateway. Production registers
no x402 adapter, so payment remains fail closed. These paths are concentrated
in a DOM-at-import singleton and have no executable browser harness.

The Compose file has strong process/resource controls, but shared anchors add
`capture_egress`, `payment_egress`, and `tls_egress` to fixture services. The
gateway metrics listener is process-loopback and therefore not collectible by
another internal service. Caddy has several security headers but lacks the CSP
required by the canonical specification.

## Proposed behavior

Create a small injectable boot/controller seam around the existing browser
orchestration. Production supplies current globals and keeps its null payment
adapter; tests supply deterministic wallet/API/storage/crypto/timer boundaries
and a recording adapter. The seam changes no public contract or saved-flow
format.

Split profile-specific Compose networking so only live services receive the
three egress networks. Add a dedicated internal operations network for a
bounded metrics probe path, without a host publication, edge proxy route, or
collector dependency. Add a restrictive static-app CSP verified against the
built assets. Validate both profiles through resolved Compose JSON; do not
start containers in this phase.

## Components and boundaries

- Browser controller/view: rendering, input validation, wallet events,
  session recovery pointer, and invocation gating; never payment authority.
- Fake EIP-1193 provider: deterministic accounts/chain/switch/events only.
- Fake gateway: same-origin planned responses and exact request recorder;
  rejects all unexpected or cross-origin traffic.
- Test-only x402 adapter: controlled cancel/error/success outcomes and exact
  invocation count. It is absent from production output.
- Gateway/PostgreSQL: authoritative payment/entitlement state, unchanged by
  this scope.
- Compose fixture: configuration-only validation with no external-egress
  network. No containers, schemas, or volumes are created.
- Metrics boundary: private internal network only; never edge/host accessible.
- Live profile: static resolution only; no services or network clients start.

## Data flow

On boot the UI reads capabilities and wallet facts. A saved flow recovers by
quote GET, request-status GET, or exact idempotent create replay. A READY quote
may invoke the test adapter only after all gates agree; the guard is persisted
first. Typed pre-submit cancel requires a fresh READY GET before clearing.
Every ambiguous outcome remains uncertain, while pending/manual-review/paid
reload paths use GET only. Paid bytes and evidence are accepted only after
existing receipt/report/bundle binding checks.

Static operations tests render fixture and live Compose profiles to JSON and
assert exact service/network/port/secret/resource/health topology plus metric
and CSP configuration. Rendering is read-only and does not start services.

## API and event contracts

No OpenAPI, JSON Schema, event, SQL, browser-storage, or public payload change.
Existing EIP-1193 methods/events are simulated only in tests. The metric
transport binding changes only its private operational reachability; metric
names remain bounded and Caddy exposes no `/metrics` route.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs: canonical TZ F6/A26/A30, CSP and egress requirements,
  shadow-only safety, and frozen acceptance-vector rules.
- Applicable canonical example IDs/versions: current v1 capability, gateway,
  report, receipt, bundle, and saved-flow contracts.
- Open or overdue debt IDs: A13/A14 external payment, A26 runtime isolation,
  A28 clean-machine acceptance, A30 real-wallet sequence.
- Expected governance handoff or receipt impact: local test/config evidence
  only; no acceptance row is promoted by this route.

## Bitrix-specific impact

- Modules/events/agents/components affected: none.
- Cache and managed cache impact: none.
- Installation/update/uninstall impact: none.
- Core modification: forbidden unless explicitly approved.

## Decisions

- Prefer a web-owned deterministic DOM/browser harness and the smallest
  injectable seam; do not introduce a framework rewrite.
- Keep the production x402 adapter unregistered and fixture capabilities
  unchargeable.
- Fix fixture egress at the source Compose topology and prove exact resolved
  network sets for both profiles.
- Use an internal-only metrics boundary without a public port, Caddy route, or
  collector dependency.
- Apply the canonical CSP because the Vite entry is an external module script;
  do not add `unsafe-inline` merely to make a test pass.
- Defer all container execution. The migration/external-write gate remains
  unexercised, and A26 runtime evidence remains `NOT_RUN`.

## Risks and mitigations

- Fake drift: tests drive production orchestration and public DOM state while
  recording every request/adapter invocation; independent test review probes
  no-resettlement mutants.
- Security regression from metrics/CSP: static assertions require no host/edge
  metrics route, safe labels, and restrictive directives on built assets.
- False isolation claim: fixture exact network membership is asserted, but
  static evidence is explicitly not called runtime A26 acceptance.
- Recovery regression: keep `SavedFlow.version = 1` and public APIs unchanged;
  characterize corrupt/inaccessible/session-loss behavior.
- Scope expansion: any container start, persistent write, real network client,
  or schema need stops for a new exact approval.
