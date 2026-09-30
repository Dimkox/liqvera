# Repository analysis: live Hyperliquid report and testnet paywall

Route: `337ef5ec16a0`  
Role: `repo_explorer` (read-only application analysis)  
Tree inspected: `/home/pall/projects/liqvera/.worktrees/repo-cleanup`

## Finding

The public Hyperliquid transport is already implemented and credential-free. The live
Compose topology is also present. The product does not currently reach a live report,
however, because the capture package deliberately omits a reviewed instrument mapping
and `sealed_input.py` unconditionally rejects every `live-public` package as
`IDENTITY_UNVERIFIED`. Independently, ordinary gateway startup deliberately composes
x402 with a `null` live grant, which deterministically emits
`EXTERNAL_GRANT_REQUIRED` (and, before initialization, payment is unavailable).

Therefore replacing the fixture MVP is not primarily a new HL adapter task. The
smallest vertical is: approve and validate an exact BTC perpetual identity mapping in
the sealed package, allow the canonical report builder to label that already-bounded
input as live, then feed the existing gateway a private short-lived testnet grant via a
reviewed startup seam. No Hyperliquid credential is needed or should be provided to the
capture service.

## Exact existing live data path

1. `packages/public-capture/src/mee_public_capture/evidence_capture.py`
   - Hard-codes `https://api.hyperliquid.xyz/info`.
   - Sends exactly two POST bodies under one 12-second deadline: `{"type":"meta"}`
     and `{"type":"l2Book","coin":"BTC"}`.
   - Uses `httpx.Client(trust_env=False, follow_redirects=False)`, bounds each response
     to 2 MiB, permits no retry or fixture fallback, and preserves raw bytes and timing.
   - This is public market data. It accepts no HL API key and has no trade method.

2. `packages/public-capture/src/mee_public_capture/evidence_service.py`
   - `POST /internal/v1/captures` calls `capture_package(...,
     source_mode="live-public")` when `LIQVERA_SOURCE_MODE=live-public`.
   - It explicitly refuses database/payment/RPC/facilitator environment variables.
   - The response truthfully reports `identity_status: "UNVERIFIED"`.

3. `packages/public-capture/src/mee_public_capture/evidence_package.py`
   - Writes immutable raw source bytes plus manifest/control/quality/envelope evidence.
   - For live mode it intentionally writes `mapping_snapshot.json` with an empty
     `mappings` array and omits `source/mapping-evidence.json`.

4. `packages/evidence-report/src/mee_evidence_report/service.py`
   - `POST /internal/v1/reports` creates a fresh capture UUID, calls the private capture
     service, then calls `build_report(capture_root / capture_id, request)` and publishes
     `report.json` plus `evidence.zip` create-only.
   - The public request is already fixed to `hyperliquid:BTC:perpetual` through
     `report.parse_request`.

5. `packages/evidence-report/src/mee_evidence_report/sealed_input.py`
   - Strictly checks manifest/member digests, exact request bodies, clocks, freshness,
     BTC coin identity, ordered non-crossed levels (1..20 per side), metadata and the
     reconstruction input.
   - Lines 185-191 are the first decisive blocker: live mode requires the mapping list
     to be empty and then unconditionally raises `IDENTITY_UNVERIFIED`.

6. `packages/evidence-report/src/mee_evidence_report/report.py`
   - A second explicit blocker remains at lines 93-96: any mode other than `fixture`
     raises `IDENTITY_UNVERIFIED`.
   - The rest of the builder already performs the exact depth sweep and emits canonical
     report bytes. Its quality/source fields are currently fixture constants and must be
     projected by mode (live should become `VALID_FOR_SNAPSHOT_CALCULATION`, without
     `SIMULATED_SOURCE`).

7. `apps/mezo-gateway/src/adapters/report-service.ts`
   - Calls the report service, accepts only `fixture` or `live-public`, validates the
     artifact metadata, and returns a closed projection to the gateway.

8. `apps/mezo-gateway/src/application/gateway.ts`
   - In live mode, `create()` admits a new request only when payment blockers are empty;
     the build worker obtains the artifact before a chargeable quote is exposed.
   - `read()` returns x402 requirements, verifies a wallet authorization, durably marks
     the attempt submitting, invokes exactly one facilitator settlement, confirms
     canonical finality, and serves report/ZIP only for a confirmed entitlement.

9. `apps/mezo-web/src/main.ts` and `apps/mezo-web/src/api.ts`
   - The browser already requires `cap.payment_ready` and `source_mode ===
     "live-public"`, creates the report request, presents test-MUSD terms, invokes the
     x402 browser adapter, and downloads/verifies the ZIP digest. No fixture UI changes
     are required for the production path.

10. `deploy/mezo-evidence/compose.yaml`
    - The `live` profile already wires `evidence-capture-live -> report-live ->
      gateway-live -> web-live -> edge-live`.
    - Capture alone receives public egress; gateway receives payment egress. Live source
      mode, report URL/token, public origin and `PAY_TO` are already projected.

The separate `make mvp` / `make mvp-web` path is not this flow. It is deliberately
fixture-only (`scripts/run-f3-mvp.py`, `scripts/run-mvp-web.py`, local SQLite simulated
unlock). Converting those scripts would duplicate the gateway/payment implementation;
the smaller product vertical is to make the existing live Compose/gateway path runnable
and retain the local demo as an explicit fixture demo.

## Smallest live-report implementation surface

Application files that must change:

1. `packages/public-capture/src/mee_public_capture/evidence_package.py`
   - Add one exact, reviewed live BTC perpetual mapping evidence document and bind it by
     digest in `mapping_snapshot.json`; do not derive identity approval merely from an
     environment flag.

2. `packages/evidence-report/src/mee_evidence_report/sealed_input.py`
   - Validate the live mapping and its evidence byte-for-byte/digest-for-digest, while
     retaining the existing raw payload, timing, freshness, order and metadata checks.
   - Remove only the unconditional live rejection after that evidence validates.

3. `packages/evidence-report/src/mee_evidence_report/report.py`
   - Admit validated `live-public` inspected input and project live quality fields and
     limitations instead of the fixture constants. Keep execution authority `NONE`.

No analyzer, gateway API, ledger schema, web flow, or HL transport rewrite is needed.

Focused test minimum:

- Extend/add public-capture package tests (currently coverage is concentrated under
  `tests/public_capture/`) to assert the exact live mapping evidence and prove no fixture
  fallback/credential input.
- Extend `tests/evidence_report/test_canonical_f3.py` with a deterministic injected live
  capture package and assert a schema-valid live report plus exact recalculation/bundle
  reproduction.
- Add negative cases for missing, changed, duplicated, expired/mismatched live mapping;
  stale/future/crossed/depth cases remain fail-closed.
- Add a service-level test proving a live capture can pass capture -> report publication
  and that `SOURCE_UNAVAILABLE` still emits no artifact.
- Existing gateway live-source state-machine tests remain useful; one vertical test
  should assert that the resulting `live-public` artifact creates a READY quote only
  when payment readiness is true.

## Exact `EXTERNAL_GRANT_REQUIRED` path

1. `apps/mezo-gateway/src/main.ts:24-28` explicitly calls
   `composeOfficialX402(..., null)` on every ordinary startup.
2. `apps/mezo-gateway/src/security/live-composition.ts:8-14` maps that `null` to an
   `OfficialX402` with no grant/context.
3. `apps/mezo-gateway/src/adapters/x402.ts:75-81` adds
   `EXTERNAL_GRANT_REQUIRED` when either the grant or live context is absent, and adds
   `PAYMENT_SERVICE_UNAVAILABLE` until SDK initialization succeeds.
4. `Gateway.blockers()` also adds `PAY_TO_MISSING` when unset and `SIMULATED_SOURCE` in
   fixture mode. New report requests and paid reads fail with `PAYMENT_NOT_READY` while
   any blocker remains.

The live-grant parser already exists in
`apps/mezo-gateway/src/security/live-grant.ts`. It enforces a private, short-lived exact
grant bound to commit, tree, acceptance-plan digest, buyer, recipient, Mezo Testnet
chain 31611, test MUSD, Permit2/EIP-2612 sponsorship, facilitator/RPC identities,
loopback database identity, one settlement submission and a gas ceiling. The separate
`p3-operator.ts` consumes the same authority for the sealed acceptance run, but it is
not connected to ordinary web/gateway startup.

## Smallest paywall implementation surface

Application/configuration files that must change:

1. `apps/mezo-gateway/src/config.ts`
   - Add private-file-only grant input and the exact non-secret context identities needed
     by `LivePaymentContext`. Reuse the repository's no-symlink/private/single-link,
     bounded-byte snapshot rules rather than accepting grant JSON in an environment
     variable or CLI argument.

2. `apps/mezo-gateway/src/main.ts`
   - Supply the validated bytes/context to `composeOfficialX402` in the explicit live
     profile; keep `null` for fixture/default startup. Initialization then performs the
     bounded facilitator capability check already implemented by `OfficialX402`.

3. `deploy/mezo-evidence/compose.yaml` (and installer projection if this path must ship
   in v0.0.2)
   - Mount a dedicated grant secret only into `gateway-live` and project the exact
     commit/tree/plan/buyer identifiers. Do not mount wallet private keys; the buyer
     signs in the browser and the facilitator broadcasts.

4. Potential small refactor: move/reuse the hardened private-file reader currently in
   `p3-operator.ts` so runtime config does not regress its TOCTOU/permissions checks.

Focused test minimum:

- Extend `apps/mezo-gateway/test/payment-policy.test.ts` for live startup composition:
  valid private grant clears `EXTERNAL_GRANT_REQUIRED` after mocked SDK initialization;
  absent, malformed, expired, mismatched, linked/world-readable/replaced grant stays
  fail-closed without facilitator settlement.
- Add config tests for live-only grant/context projection and fixture refusal/ignore.
- Extend `apps/mezo-gateway/test/state-machine.test.ts` with one end-to-end mocked
  READY -> 402 -> verified -> single settle -> 12-confirmation -> report/ZIP entitlement
  path and replay/no-second-settlement assertions (many component assertions already
  exist).
- Extend Compose contract tests to prove the grant secret reaches only `gateway-live`,
  never capture/report/web, and fixture remains grantless.

## Operational and security notes

- Hyperliquid snapshot capture needs no credentials. Existing wallet/RPC/facilitator
  material must not be passed to capture or report services.
- The user-authorized scope permits Mezo Testnet payment. The current grant is designed
  for one exact short-lived settlement; enabling it is not equivalent to enabling
  mainnet or exchange mutations.
- A previously sealed 0.01 test-MUSD settlement proves the P3 operator path, not ordinary
  gateway readiness. Reusing that expired/consumed grant must remain impossible.
- `PUBLIC_BASE_URL` and `CORS_ORIGINS` already require HTTPS away from loopback. A public
  deployment still needs an actual hostname/TLS endpoint and durable Postgres/artifact
  storage; that is deployment evidence, not a code gap in the HL/report path.
- No application code or credentials were read or modified during this analysis.

