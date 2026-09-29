# F6 data and safety analysis

Route: `26ffb293d4ff`
Scope: read-only analysis of browser persistence/recovery, gateway interactions, and the disposable Compose boundary. No service, database, wallet, RPC, facilitator, or container was started.

## Conclusion

F6 needs no schema migration or backfill. The safe verification boundary is a deterministic browser harness with a fake EIP-1193 provider and intercepted same-origin `/v1/*` responses, plus static Compose validation. A disposable fixture Compose smoke test may be added only after the named human gate because it creates a local PostgreSQL schema and named volumes; it must use a unique project name, synthetic secrets, the `fixture` profile only, loopback exposure only, and must never load live configuration.

The browser's no-resettlement behavior is structurally fail-closed: a persisted `paymentGuard` blocks repeat payment, uncertain/pending/manual-review states offer only status recovery, reload reuses the original request identifiers and idempotency key, and the UI payment adapter is currently unregistered. The fixture gateway additionally rejects quote creation and reports `SIMULATED_SOURCE`. However, the fixture Compose topology still attaches capture, gateway, and edge services to non-internal egress networks. Therefore Compose network policy alone does **not** prove absence of external calls; no-external-I/O proof for this route must come from mocked browser tests/static inspection, or from an explicit test-only network override that removes those egress attachments.

## Browser state and recovery authority

- `apps/mezo-web/src/session.ts:3-14` stores one bearer capability and one versioned flow in `sessionStorage`. The flow contains side, quantity, payer, idempotency key, optional request/quote IDs, and `clear|started|uncertain`; it contains no wallet key, signature, receipt, or payment payload.
- `session.ts:29-37` generates 256 random bits for the capability and reuses the valid stored value. `session.ts:40-55` validates all recovered fields. Invalid/corrupt state returns `null`; inaccessible storage fails closed rather than silently creating an unrecoverable paid flow.
- `main.ts:422-457` recovers in this order: existing quote ID via GET, existing request ID via GET, otherwise exact POST replay with the original idempotency key/body. Reload therefore does not mint a second logical request when session state survives.
- `main.ts:325-343` recovers a paid delivery only through the server, verifies receipt/report binding, then clears the local guard. The server remains the entitlement/finality authority; session storage is only a locator and client-side safety latch.
- Session-storage loss (closing the tab/browser session, explicit clearing, privacy tooling) loses both capability and flow. This is an acknowledged operational limitation, not a migration problem: recovery cannot be reconstructed from public IDs because the bearer capability scopes access. Tests should state this explicitly and must not weaken it by moving the capability to durable/local storage.

## No-resettlement and wallet changes

- `main.ts:462-505` permits payment only when the quote, flow, capability, provider, account, readiness, reviewed adapter, payer/terms, and `paymentGuard === clear` all agree. The guard is persisted as `started` **before** the adapter call. Any ambiguous error becomes `uncertain`; only the typed pre-submission cancellation plus a fresh server `READY` response can clear it.
- `main.ts:346-394` treats `PAYMENT_PENDING`, `PAYMENT_UNCERTAIN`, and `MANUAL_REVIEW` as status-only recovery and never invokes the payment adapter. Paid recovery performs GETs only. The “new report” control is locked for those states (`main.ts:541-549`).
- Account/chain events refresh wallet facts without changing the saved payer (`main.ts:522-538, 576-577`). A switched account therefore cannot pay the old quote; a wrong chain disables payment and exposes the network-switch action.
- `apps/mezo-web/src/x402.ts` has no registered production adapter by default, so `x402Available()` is false and no payment submission is possible in the current build. Tests may register a fake adapter in-process solely to count calls; they must not import or initialize a live facilitator/RPC client.
- The server reinforces the boundary: fixture mode adds `SIMULATED_SOURCE` (`apps/mezo-gateway/src/application/gateway.ts:12-14`) and rejects new quote creation before ledger creation (`:38-45`). For a real READY quote, only the gateway's initial read path calls `settle`; recovery paths reconcile/read status and do not resettle (`:73-114`, plus reconciliation worker comment). Browser tests should still assert the fake adapter call count is exactly zero after cancel-before-submit and exactly one across ambiguous result, reload, account/chain changes, repeated refresh, and delivery recovery.

## Gateway API interaction matrix for browser tests

| UI event | Permitted requests | Forbidden behavior |
|---|---|---|
| Boot without saved flow | `GET /v1/capabilities` | quote POST, report GET, payment adapter call |
| Create/retry after lost response | one or repeated identical `POST /v1/report-quotes` with the same capability/body/idempotency key | new key/body, payment before READY |
| PREPARING reload | capability GET, request-status GET, then quote GET when READY | second logical quote |
| READY + pre-submit wallet cancel | fresh quote GET to prove READY | settlement call; guard clear without server proof |
| Pending/uncertain/manual-review reload | quote/status GETs only | adapter call, new-report clearing, second POST/payment |
| PAID reload | quote GET then report GET; evidence GET only on user download | any payment adapter call |
| Wallet account/chain switch | provider reads and optional `wallet_switchEthereumChain` | mutation of saved payer or quote identity |

The browser `fetch` wrapper uses relative `/v1/*`, `credentials: omit`, `redirect: error`, and `cache: no-store`; the capability is sent only as the Authorization bearer. The fake server should record method/path/header/body and fail the test on every unplanned request.

## Compose data, secrets, and isolation

- Static parsing passed without starting services:
  `LIQVERA_ENGINE_COMMIT=0123456789abcdef0123456789abcdef01234567 docker compose -f deploy/mezo-evidence/compose.yaml --profile fixture config --quiet` (exit 0).
- Profiles split fixture/live services and the file instructs distinct project names (`compose.yaml:3-5`). Project-name isolation is essential because the logical volume names (`captures`, `artifacts`, `postgres_data`, Caddy data/config) are shared within a project (`:364-369`). Never enable both profiles under one project.
- PostgreSQL and internal report tokens are mounted as Compose secrets (`:249-320, 354-362`). The gateway entrypoint derives `DATABASE_URL` in process memory. Test tooling must create random synthetic secret files outside tracked paths and must never inspect existing `deploy/mezo-evidence/secrets/*` values.
- Service filesystems are read-only, capabilities are dropped, `no-new-privileges` is set, and CPU/memory/PID limits plus bounded tmpfs and health checks are present for capture, report, PostgreSQL, gateway, web, and edge (`:7-196`). Only fixture edge publishes a loopback port (`:331-340`).
- Persistent writes in a fixture container run are expected only to its project-scoped captures/artifacts/PostgreSQL/Caddy volumes. A unique, clearly synthetic project name is mandatory. Cleanup may remove **only that exact verified fixture project's volumes** after confirming no live/shared project is targeted. The route's migration/external-write gate applies before such a run.
- Isolation gap: anchors attach capture to `capture_egress`, gateway to `payment_egress`, and edge to `tls_egress`; these networks are not internal (`:24-26, 95-117, 169-190, 371-378`) and anchors apply equally to fixture services. App-level fixture checks block payment, but network policy does not establish zero external traffic. Do not use ordinary `compose up` as the no-external proof. Prefer no containers for F6; if health/resource smoke is required, use a reviewed temporary override that removes all three egress attachments or an OS-enforced deny-egress sandbox, and record the rendered config.
- `restart: unless-stopped` on fixture services means an interrupted smoke run can persist. A test override should set `restart: "no"`, and teardown must be verified by exact project name.

## Deterministic fake/disposable boundary

1. Build/typecheck the web app offline from the lockfile.
2. Run browser tests against the static app with an in-process route interceptor. Stub every `/v1/*` response and reject unregistered requests. Inject a fake EIP-1193 provider implementing only `eth_accounts`, `eth_requestAccounts`, `eth_chainId`, and `wallet_switchEthereumChain`, with controlled account/chain events.
3. Use fresh isolated browser contexts for each test; seed only known `sessionStorage` keys. Count quote POSTs, idempotency keys, status/report GETs, adapter calls, and any attempted cross-origin request. Use fake timers for polling.
4. Exercise reload in the same page session and closure in a new session separately. Same-session reload must recover; new-session loss must be documented and must never cause an automatic payment.
5. Static-check the rendered Compose fixture profile for: fixture services only, loopback-only published port, distinct secrets, resource limits, health checks, read-only/cap-drop/no-new-privileges, and no live env values. Treat the existing egress attachments as a known failure if the acceptance criterion requires network-enforced isolation.
6. Do not start PostgreSQL/containers unless the migration/external-write gate explicitly approves the exact disposable fixture project. No real wallet, RPC, facilitator, transfer, testnet/mainnet payment, shared volume, or live environment belongs in F6.

## Migration and rollback assessment

- Database schema change: none.
- Browser storage migration: none. Keep `SavedFlow.version = 1`; any incompatible future state change should use a new version and fail closed.
- Backfill/index/query-plan impact: none.
- Rollback: remove only F6 test/config changes. Existing session records remain readable because runtime state format must not change.
- Validation stop conditions: any non-mocked cross-origin request, payment adapter count greater than expected, changed idempotency key/body on recovery, fixture/live service co-residence, non-loopback fixture publication, use of existing secret values, or unapproved local schema/volume creation.

## Findings for scope/design gate

1. **High — container egress gap:** fixture services inherit external egress networks. Either keep F6 entirely fake/static or approve a test-only deny-egress override before container smoke.
2. **Medium — recovery lifetime:** capability and flow survive reload only within the browser session; tab/session loss makes capability-scoped recovery unavailable. Preserve this truthful limitation in UI/runbooks.
3. **Medium — disposable persistence:** named volumes and `restart: unless-stopped` make a normal fixture stack persistent. Any approved smoke test needs a unique project name, restart-disabled override, exact teardown target, and synthetic secrets.
4. **No migration:** browser/Compose verification does not justify SQL or storage-format changes.
