# Architecture analysis: live Hyperliquid report + enabled Mezo Testnet paywall

Route: `337ef5ec16a0`
Role: `architect` (read-only application-code analysis)
Scope: a bounded live-public BTC snapshot and a genuinely enabled, single-use
Mezo Testnet x402 demo. Mainnet, exchange mutation, custody, private venues and
merchant/buyer private keys remain out of scope.

## Finding

The shortest safe path is not a new subsystem. Both verticals already have
nearly all of their machinery and each is stopped by one deliberate composition
gate:

1. `evidence-capture-live` already performs exactly two credential-free POSTs
   to `https://api.hyperliquid.xyz/info`, retains the exact responses and
   timestamps, and atomically seals the capture. The report inspector validates
   freshness, ordering, BTC identity hints, book shape, exact decimals and
   hashes, but then unconditionally rejects every live package as
   `IDENTITY_UNVERIFIED`.
2. The gateway already has reviewed Permit2/EIP-2612 identity, twelve-block
   finality, official x402 SDK composition, durable payment/entitlement state,
   a one-submit grant schema, immutable grant consumption, confirm-only recovery
   and a real Mezo Testnet settlement witness. Ordinary `main.ts` deliberately
   passes `null` to `composeOfficialX402`, so the browser-facing gateway can
   never advertise `payment_ready=true`.

The bounded design is therefore to (a) make the existing live identity policy
an explicit, versioned code contract over the retained Hyperliquid bytes and
(b) give the existing ordinary gateway an opt-in secret-file composition for
one exact short-lived testnet grant. Do not route the product through the P3
acceptance CLI and do not weaken `EXTERNAL_GRANT_REQUIRED` for default startup.

## Current gaps that must not be papered over

- `packages/evidence-report/.../sealed_input.py` requires an empty live mapping
  and then always raises `IDENTITY_UNVERIFIED`; `report.py` separately rejects
  every mode other than `fixture`; `algorithm_document` says
  `live_identity_approved: false`. All three must change together with schemas
  and independent-verifier behavior. Merely changing an environment variable or
  capture response label would be a false claim.
- `main.ts` cannot consume a grant. The P3 CLI is an acceptance operator, not an
  HTTP paywall composition.
- `OfficialX402.blockers()` tests grant presence and initialization but not
  current expiry or durable consumption. A long-lived server could therefore
  report ready after the grant expires, and after one settlement it could accept
  another quote that can only become uncertain at the database consumption
  boundary.
- The current grant is buyer-specific and permits exactly one settlement. A
  global `payment_ready=true` is truthful only for that named demo buyer and
  only while the grant remains live and unconsumed. The gateway must reject a
  different `expected_payer` before creating/building a payable request.
- The live Compose networks provide egress but do not constitute an outbound
  allowlist. Production/demo deployment still needs DNS/IP-independent egress
  policy at the host/proxy layer for only Hyperliquid, the pinned facilitator,
  Mezo RPC and ACME/TLS destinations.

## Bounded target design

### Vertical 1: retained, independently recalculable live Hyperliquid snapshot

Keep the existing request surface and transport unchanged: one `meta` request
followed by one `l2Book` request for `BTC`, one shared 12-second deadline, no
credentials, no retries, no redirects, no ambient proxy, no compression and no
fixture fallback.

Add a versioned `hyperliquid-btc-linear-perpetual/v1` identity policy in the
Python evidence layer. It must derive its decision only from the exact sealed
`metadata.bin` and `book.bin` plus reviewed static semantics in source control.
For approval it must require, at minimum:

- exactly one active `universe` entry named `BTC`, integer `szDecimals` in the
  accepted range, and no delisting flag;
- book `coin == "BTC"`, a source timestamp within the existing 5-second age and
  1-second future-skew limits, ordered non-crossed sides, positive exact-decimal
  prices/sizes and bounded depth;
- a closed mapping: base BTC, quote USD, settlement USDC, linear perpetual,
  displayed size in coin, multiplier 1, quantity step derived exactly from
  `szDecimals`; no unsupported inference of fees, funding or executionability;
- an evidence document containing the policy version and SHA-256 commitments to
  both retained source responses. The mapping's `evidence_sha256` must bind that
  canonical document, and the report/bundle must carry it.

The capture service may label the result `REVIEW_REQUIRED`/`UNVERIFIED`; the
authoritative approval belongs to the report inspector, which has all sealed
bytes and the versioned reviewed policy. Prefer this over allowing the network
collector to assert economic identity. Update the capture/report schemas with
an explicit live-approved output state only if that state is emitted after
inspection, not based on configuration.

On success, `build_inspected_report` accepts `live-public`, emits
`snapshot_status=VALID_FOR_SNAPSHOT_CALCULATION`, no `SIMULATED_SOURCE` reason,
and `live_identity_approved=true`. It retains the existing boundaries:
`execution_authority=NONE`, no fees/funding/net-PnL and no execution promise.
The immutable ZIP must include raw meta/book bytes, request bodies, timestamps,
capture manifest, mapping evidence, algorithm/dependency identity and report.
The standalone verifier must recompute every hash, reconstruct the book, rerun
the same policy and exact sweep, and compare the report bytes without network
access. A hosted URL is delivery only; the ZIP remains sufficient to verify.

No database migration is required for this vertical. Captures and artifacts
remain append-only files published by atomic rename; PostgreSQL stores their
identity and delivery/payment state, not their authoritative bytes.

### Vertical 2: ordinary HTTP gateway enabled for one Mezo Testnet payment

Add an opt-in runtime composition, absent by default:

- `LIQVERA_LIVE_GRANT_FILE` points to a read-only secret file, never an env
  value. Read it once with the same regular-file/no-follow/private-mode/size
  discipline used by P3.
- Bind the grant to immutable build metadata (`subject_commit`, `subject_tree`,
  reviewed plan/policy digest), the configured `PAY_TO`, the one expected buyer,
  facilitator URL, Mezo RPC URL and the active database endpoint identity.
  Supply build metadata as a digest-bound image/release manifest, not by calling
  Git inside the container.
- Feed those bytes and the derived context to the existing
  `composeOfficialX402`; keep the no-file path exactly equivalent to today's
  `null` composition and `EXTERNAL_GRANT_REQUIRED`.
- Before readiness becomes true, probe chain id 31611, MUSD bytecode/decimals,
  facilitator support for x402 v2 `exact` + Permit2 + EIP-2612 sponsorship, and
  confirm that payee differs from buyer. Bounded I/O, no redirects/retries and
  the pinned origins remain mandatory.

Grant availability must become a stateful server-side gate. Extend the payment
port/readiness path to report not-ready when the grant is expired, mismatched or
already present in `live_grant_consumptions`. Check this again transactionally
at `VERIFIED -> SUBMITTING`; the existing unique insert remains the final
one-submit authority. Reject quote creation when `expected_payer` differs from
the grant buyer. Do not turn an expired/spent grant into `PAYMENT_UNCERTAIN`
before submission; return a stable not-ready/expired outcome. Once submission
may have happened, preserve the existing spent, confirm-only behavior and never
settle again.

This produces a real browser flow: live report request -> exact quote -> 402
challenge -> wallet-generated signatures -> facilitator settlement -> durable
unknown/confirmation reconciliation -> twelve canonical confirmations -> paid
report/ZIP. Neither gateway nor browser receives a wallet private key. The
merchant address receives test MUSD; the facilitator broadcasts and sponsors
gas under the reviewed scheme.

No new payment migration is indicated: migration 003 already provides the
immutable one-grant/one-attempt budget, and 004-005 retain confirmation
provenance/count. Implementation should first prove existing schema sufficiency;
any schema change reopens the data-change gate.

## Trust boundaries and assets

| Boundary | Untrusted input / actor | Enforced invariant |
| --- | --- | --- |
| Hyperliquid public API -> capture | DNS, TLS peer, response bytes/timing | Fixed HTTPS origin/request bodies; bounded exact raw bytes; no auth/proxy/redirect/retry/fallback; source is evidence, not instruction |
| Sealed capture -> inspector | Filesystem/package producer | Closed inventory, canonical JSON, hashes, timestamps, exact decimals, reviewed identity policy; reject ambiguity/staleness/crossing |
| Inspector -> immutable artifact | Report builder | Atomic create-only publication; report binds source, mapping, algorithm and dependency digests |
| Public browser -> gateway | Request bodies, bearer scope, payer, idempotency keys, headers | Size/schema/origin/rate bounds; payer equals active grant buyer; server is authority |
| Browser wallet -> x402 | EIP-1193 account/network and opaque signatures | Chain 31611; exact terms; SDK composition; never log/reflect/reconstruct signature; account stable through submit |
| Gateway -> facilitator | Third-party supported/verify/settle responses | Pinned HTTPS origin, bounded I/O, exact capability/terms checks, at most one settle after durable `SUBMITTING` |
| Gateway -> Mezo RPC | Untrusted JSON-RPC responses/reorgs | Chain id, receipt/tx/log binding, one exact MUSD Transfer, canonical block checks, 12 confirmations, buyer gas unchanged |
| Gateway -> PostgreSQL | Concurrent requests/crash recovery | Sole writer; atomic state transition and unique immutable grant consumption; append-only audit; confirm-only after ambiguity |
| Operator -> runtime | Grant, payee, release/image/config | Secret-file references, exact digest/build/database binding, explicit testnet approval; no private keys in stack |

Primary assets are immutable report bytes and provenance, the payment
authorization (secret until submitted), test MUSD, entitlement correctness,
the single-settlement budget, PostgreSQL audit history and the bearer recovery
capability. Logs/metrics must contain only request/grant IDs or digest
commitments, never payment signatures, DB credentials, report tokens or wallet
secrets.

## Failure semantics and observability

- Hyperliquid timeout, malformed/stale/crossed book, missing identity evidence or
  capture/report disagreement: no report, no quote and no payment challenge.
- Facilitator/RPC/capability failure before verification: readiness false, no
  settlement. Failure after `SUBMITTING`: `PAYMENT_UNCERTAIN`, grant remains
  spent, reconciliation only.
- Report/artifact readback failure: no settlement; after entitlement, quarantine
  artifact and retain ledger/payment evidence.
- Emit low-cardinality metrics/events for capture result/reason, report build
  result/reason, grant state (`absent`, `active`, `expired`, `consumed`,
  `mismatch`), payment state transitions, facilitator/RPC latency/error and
  confirmation depth. Never put addresses/signatures/tokens in metric labels.

## Rollout and rollback

Roll out in two independently reversible gates:

1. Deploy live capture/report with payment disabled. Produce one fresh BTC ZIP,
   verify it offline from a separate checkout/runtime, and expose only after the
   exact report and public URL pass review. Rollback is selecting the fixture
   profile or disabling new live requests; retain sealed captures/artifacts.
2. Mount one short-lived testnet grant and enable the gateway only for its exact
   buyer/payee/amount. Exercise one payment and recovery path. Rollback is remove
   the grant mount and restart so `EXTERNAL_GRANT_REQUIRED` returns. This stops
   new settlements but preserves PostgreSQL, artifacts, consumed grant and any
   unknown attempt; reconciliation continues read-only/confirm-only.

Never roll back payment migrations or delete volumes after any attempted
settlement. If application rollback cannot read the current ledger, keep the
gateway payment-disabled and forward-fix. Never delete a capture/artifact tied
to a quote, attempt, entitlement or unresolved recovery. Mainnet configuration,
exchange-order methods and wallet-key ingestion stay structurally absent.

## Acceptance slice

The change is complete only when the final clean commit proves all of the
following on its exact build identities:

1. A fresh network capture retains the two real Hyperliquid responses and
   produces a `live-public` BTC report; malformed, stale, crossed, wrong-coin,
   duplicate-BTC and transport-failure cases fail without fixture fallback.
2. An independent offline verifier, with network disabled, reproduces the live
   report and validates the ZIP from its public URL.
3. Default/fixture startup still advertises `EXTERNAL_GRANT_REQUIRED` and cannot
   return a payable challenge.
4. The opted-in live gateway reports ready only for a live, matching,
   unconsumed grant and exact buyer; expiry, mismatch and prior consumption fail
   closed before settlement.
5. One wallet-approved 0.01 test MUSD flow reaches confirmed entitlement with
   exactly one facilitator submission, exact Transfer evidence, 12 canonical
   confirmations and zero buyer native-gas spend. Retry/timeout/restart paths do
   not resettle.
6. Removing the grant disables new payments while the paid report and any
   unknown attempt remain recoverable. No mainnet call, exchange mutation,
   credential read or wallet-key ingestion occurs.

## Human gates

The route names `scope_and_design_approval` and
`migration_or_external_write_approval`. Code can be implemented after scope
approval, but the actual Hyperliquid probe, facilitator/RPC calls and Mezo
Testnet transfer require the explicit external-write approval bound to the
exact commit/tree, buyer, payee, amount, grant expiry, database identity and
testnet endpoints. Reading credential *locations* is sufficient for design;
agents must not inspect `.env`, private keys or credential values.
