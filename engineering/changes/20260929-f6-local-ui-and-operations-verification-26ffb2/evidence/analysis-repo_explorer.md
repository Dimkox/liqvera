# F6 repository exploration — route `26ffb293d4ff`

## Scope and method

Read-only inspection of the canonical F6 requirements, browser application,
Compose stack, gateway operations surface, and runbooks. I did not start a
container, contact a wallet/RPC/facilitator, or make an external request.

Commands used:

```text
rg / sed / nl over docs/planning/LIQVERA_FACTORY_TZ.md, apps/mezo-web,
deploy/mezo-evidence, apps/mezo-gateway/src, and docs/runbooks
LIQVERA_ENGINE_COMMIT=f07562e... docker compose --env-file
  deploy/mezo-evidence/env/fixture.env.example -p liqvera-f6-static
  --profile fixture -f deploy/mezo-evidence/compose.yaml config --quiet
same command with `config --format json | jq ...`
npm run build --prefix apps/mezo-web
```

The static Compose parse passed without starting anything. The web build did
not execute because this checkout has no `apps/mezo-web/node_modules` and
`tsc` was therefore not found; this is an environment precondition, not a
source failure. Use the exact lock with `npm ci --ignore-scripts` before the
focused web checks.

## Canonical boundary

The controlling requirements are specification sections 9, 11, 13–15 and
F6/A30. They require reload recovery through a session-scoped capability,
wallet cancel/wrong-chain/account-switch handling, no second payment after an
uncertain or paid outcome, isolated Compose, bounded resources/rates, health
and readiness distinction, safe metrics/logs, and accurate operator recovery.
F6 is browser-flow and clean-install evidence; it cannot relabel any of the
156 frozen vectors or establish payment/release acceptance.

## Existing behavior

### Browser

- There is no web test script, browser runner, DOM test dependency, or test
  file. `package.json` exposes only dev/build/typecheck/preview. None of the
  A30 browser behavior is executable evidence today.
- `session.ts` retains a 256-bit capability and a flow record in
  `sessionStorage`. The record carries the original idempotency key, optional
  request/quote IDs, payer, and `paymentGuard`.
- `resumeFlow()` recovers an identified quote, polls an existing request, or
  replays the exact create body with the original idempotency key after a lost
  response. Paid delivery is fetched under the original capability.
- `submitPayment()` sets the guard to `started` before invoking the adapter.
  Only the typed `X402CancelledBeforeSubmission` plus an authoritative latest
  `READY` quote clears it; every ambiguous failure changes it to `uncertain`.
  Pending/uncertain/manual-review states suppress both another payment and the
  “new report” action.
- Wrong network and account changes are represented in the UI. EIP-1193
  `accountsChanged` and `chainChanged` refresh wallet state; a quote stays
  bound to the original payer. The payment entrypoint rechecks both account
  and chain immediately before adapter invocation.
- Payment is deliberately unavailable in this tree because no reviewed x402
  browser adapter is registered. Fixture capabilities also cannot create a
  quote because the UI requires both `payment_ready` and `source_mode ===
  "live-public"`. Browser verification must therefore use deterministic fake
  gateway and EIP-1193 boundaries; it must not weaken these production gates.
- The current module is a DOM-at-import singleton with private mutable state,
  real timers, global fetch/storage/crypto, and boot at module load. This makes
  deterministic testing possible only with brittle global emulation unless a
  small injectable controller/boot seam is introduced.

### Compose and operations

- Static Compose resolution passes when `LIQVERA_ENGINE_COMMIT` is supplied.
  Only the fixture edge publishes a port and it is loopback-only
  (`127.0.0.1:8080`). All roles declare non-root users, read-only roots,
  dropped capabilities, no-new-privileges, PID/CPU/memory limits, tmpfs and
  healthchecks. Postgres/report/capture/artifact network and volume boundaries
  otherwise match the runbook.
- Confirmed isolation defect: resolved **fixture** services still attach
  `evidence-capture-fixture` to `capture_egress`, `gateway-fixture` to
  `payment_egress`, and `edge-fixture` to `tls_egress`. These are non-internal
  bridge networks. Blank `PAY_TO` and fixture source mode fail closed at the
  application layer, but the claimed isolated fixture profile retains outbound
  network capability. The anchors put these networks on both profiles.
- Confirmed observability gap: the gateway creates Prometheus text metrics on
  `127.0.0.1:9090` inside its container, but Compose supplies no collector,
  sidecar, health probe, or internal route to that loopback listener. The
  observability runbook says to collect the metrics but provides no executable
  collection path. Public exposure would be inappropriate; a local-only
  container probe or explicitly isolated collector path is needed for evidence.
- Gateway rate limiting exists (`quote-global`, quote-IP and read-IP buckets)
  and the OpenAPI describes 429/Retry-After, but there is no F6 operations test
  binding configured values/behavior to the runbook. Resource limits and
  profile topology likewise have no dedicated static test.
- Startup/shutdown and payment-recovery runbooks correctly distinguish
  health/readiness, preserve uncertain state, forbid `down --volumes`, forbid
  blind resettlement, and require distinct project names. They presently
  overstate fixture isolation and actionable metric collection as noted above.

## Smallest coherent verification/repair vertical

1. Add a web-owned deterministic test harness (prefer Vitest + jsdom or an
   equivalently small locked setup) and extract only the browser orchestration
   seam needed to inject fetch/API, EIP-1193, storage, crypto, timers and the
   reviewed payment adapter. Keep validation and production gates unchanged.
2. Add RED browser tests for: user cancel before submission; wrong chain and
   switch; account switch after quote; reload from request ID and quote ID;
   create-response loss using the same idempotency key; uncertain recovery;
   paid reload/entitlement retrieval; and assertions that none of the latter
   invoke the payment adapter a second time. Include visible text/button state,
   not only internal values.
3. Add a deterministic Compose topology test over rendered fixture/live JSON.
   Split egress attachment by service/profile so fixture capture, gateway and
   edge have no non-internal egress networks. Preserve live profile networks,
   loopback-only fixture publishing, secret separation, limits, healthchecks,
   mounts and distinct project-name instructions.
4. Make metric verification executable without public exposure (for example a
   container-local probe/test of 9090 plus a documented operator command), and
   test health vs readiness, resource limits, rate-limit configuration and
   required safe metric names statically/deterministically.
5. Update startup/observability runbooks to match the resulting topology and
   exact local commands. Do not start the live profile or register a synthetic
   production payment adapter.

## Focused commands after implementation

```text
npm ci --ignore-scripts --prefix apps/mezo-web
npm run typecheck --prefix apps/mezo-web
npm test --prefix apps/mezo-web
npm run build --prefix apps/mezo-web

LIQVERA_ENGINE_COMMIT=$(git rev-parse HEAD) docker compose \
  --env-file deploy/mezo-evidence/env/fixture.env.example \
  -p liqvera-f6-static --profile fixture \
  -f deploy/mezo-evidence/compose.yaml config --format json

# repository-owned static topology/runbook test to be added by the write owner
python3 -m pytest <focused-f6-operations-test> -q
python3 scripts/grok_verify.py --mode pr
```

If disposable-container execution is later approved within this route, use a
unique fixture project and temporary secret files only, never the live profile;
assert all healthchecks, fail-closed readiness, metrics reachability through
the documented local path, and teardown without volume deletion. Static and
fake-browser coverage is sufficient to repair the confirmed gaps without that
optional container run.

## Constraints and residuals

- No database migration or persistent-data change is indicated by this
  exploration. The route's migration/external-write gate is not needed for the
  proposed source/test repairs; it remains fail-closed if scope expands.
- Do not convert fixture mode into a chargeable quote, install an unreviewed
  x402 adapter, use a real wallet/RPC/facilitator, or infer payment readiness.
- Browser tests do not prove the official SDK binding, settlement, finality,
  testnet acceptance, deployment, or release. All 156 frozen vectors remain
  `NOT_RUN` unless their canonical runner is separately executed.
