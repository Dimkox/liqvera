# Test plan — F6 local UI and operations verification

## Risk-based scenarios

| Priority | Scenario | Evidence |
| --- | --- | --- |
| P0 | Typed pre-submit cancel clears only after READY refresh; ambiguous cancel/error stays uncertain | DOM state, session guard, API trace, adapter count |
| P0 | Reload/create-loss recovery preserves capability/body/idempotency and never resettles | exact request trace and zero additional adapter calls |
| P0 | Pending, uncertain, manual review, and paid recovery use GET-only paths | method/path trace, hidden controls, report/evidence binding |
| P0 | Wrong network, explicit switch, account switch, and chain switch preserve payer and never submit implicitly | fake EIP-1193 trace and rendered state |
| P0 | Fixture resolved profile has exact services/internal networks and no egress membership | parsed Compose JSON assertions |
| P1 | Resource, secret, mount, health, loopback-port, and profile separation invariants | static topology test |
| P1 | Metrics are internal-only, bounded, safely labelled, and distinct from readiness | source/config assertions and synthetic rendering |
| P1 | Edge CSP is restrictive and compatible with built Vite assets | header/config assertion plus built-index inspection |
| P1 | Runbooks/README/handoff preserve all local-only non-claims | documentation assertions and independent review |

## Automated checks

- Unit: session parsing/corruption, wallet provider behavior, controller guards,
  fake timer polling, exact adapter/request counters.
- Integration: browser DOM with fake same-origin gateway, EIP-1193 provider,
  session storage, test adapter, reload, report and evidence paths.
- Contract: no public API/schema/storage-version changes; validate request
  bodies, authorization placement, no credentials, no redirects, no cache.
- E2E: deterministic local DOM/browser flow only. No real browser wallet,
  external HTTP, container, RPC, facilitator, or transfer.
- Static analysis: resolved fixture/live Compose JSON; exact networks, ports,
  secrets, mounts, limits, healthchecks, users and security options; Caddy CSP
  and absence of a metrics route; safe metric names/labels.
- Focused commands: exact-lock web install with lifecycle scripts disabled,
  web typecheck/test/build, focused F6 operations pytest, then pinned
  `python3 scripts/grok_verify.py --mode pr` after implementation.

## Manual checks

- None required for scoped behavior; visual/manual observations are not used as
  acceptance evidence. Human approval is required before implementation, and
  independent route-selected reviews bind the final tree.
- Container runtime, real wallet/payment, and live profile checks are expressly
  not run. Their canonical rows remain unchanged.

## Stop conditions

- Any unmocked/cross-origin request, real provider discovery, second adapter
  call, changed recovery idempotency/body, fixture egress network, public
  metrics route, secret read, container start, volume/schema creation, or
  shared/live-system contact stops the route.
