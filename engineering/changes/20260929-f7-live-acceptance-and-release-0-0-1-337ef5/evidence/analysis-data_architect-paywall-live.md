# Data architecture: Mezo testnet paywall and live Hyperliquid report

Route: `337ef5ec16a0`
Role: `data_architect` (read-only analysis; no application-code changes)
Observed subject: `e3df683`
Scope: payment ledger/migrations, live capture/report persistence, minimum safe
state transitions, idempotency and receipt checks.

## Executive ruling

The current PostgreSQL ledger already has the right core exactly-once payment
shape. Do not replace it and do not add a new payment table. Enabling a Mezo
Testnet paywall should preserve migrations 001--005 and make the existing
`VERIFIED -> SUBMITTING` transaction the only settlement boundary. The live
grant row must be inserted in that same transaction, before the sole
facilitator call. Any response after that commit, including timeout or an
unparseable response, is spent and confirm-only.

The current Hyperliquid transport already retrieves and create-exclusively
seals public `meta` and `l2Book` bytes. The blocker is not credentials and not
snapshot persistence: `sealed_input.py` deliberately rejects every
`live-public` package as `IDENTITY_UNVERIFIED`, because live capture writes an
empty mapping snapshot. The minimum safe live-report change is therefore a
reviewed, versioned BTC perpetual identity record whose exact bytes and digest
are embedded in the sealed capture and validated by the report service. An
environment flag or an `APPROVED` string is not sufficient.

Ordinary gateway startup is also deliberately non-paying: `main.ts` passes a
null live grant to `composeOfficialX402`. The existing P3 operator is the
one-shot settlement path. A product paywall needs an explicit bounded grant
delivery mechanism or an equivalently reviewed composition; merely setting
`SOURCE_MODE=live-public` and `PAY_TO` cannot enable payment.

## Existing durable invariants to keep

### Report production

- `report_requests(scope_hash, idempotency_key)` is unique and stores the
  canonical body hash. Same key/same body returns the existing request; same
  key/different body is `IDEMPOTENCY_CONFLICT`.
- A request owns one unique `report_id`; artifacts and quotes are joined back
  to request and scope with composite foreign keys.
- Report state is monotonic: `PREPARING -> READY | REJECTED | BUILD_FAILED`.
  Publication inserts artifact and quote and advances the request to `READY`
  in one PostgreSQL transaction.
- Capture publication and report artifact publication are create-exclusive.
  Existing report bytes are reopened and verified rather than overwritten.
- The gateway rereads both report and bundle, validates report semantics,
  source mode, snapshot time and freshness before ledger publication.

### Payment

- Quote terms and artifact identity are immutable; each quote has at most one
  non-rejected attempt.
- Authorization identity is globally unique. Reuse is rejected and the
  surrounding transaction rolls back.
- `live_grant_consumptions` makes grant digest, grant UUID and payment attempt
  independently unique and append-only.
- The grant consumption and `VERIFIED -> SUBMITTING` transition occur in one
  transaction. This is the durable one-submit budget.
- `SUBMITTING` and `UNKNOWN` are the only reconciliation queue states.
  Reconciliation performs read-only confirmation and never invokes settlement.
- Chain event, receipt and entitlement are committed in one transaction;
  receipts, chain events, reconciliation events and audit events are
  append-only.
- Delivery requires a `PAID` quote plus a matching, unexpired entitlement and
  `CONFIRMED` attempt bound to scope, report ID and report digest.

## Minimum state machines

### Live report

Keep the database state graph unchanged:

```text
PREPARING
  -> READY        only after capture seal, identity verification, report/bundle
                  readback, digest checks and <=5 s sale-time freshness
  -> REJECTED     deterministic input/data/identity/freshness rejection
  -> BUILD_FAILED source, storage or artifact-integrity failure
```

Required live input identity:

1. The public capture records exact request bytes, raw response bytes, timing,
   content hashes and a manifest under a server-generated capture UUID.
2. A reviewed live mapping record binds venue `hyperliquid`, symbol `BTC`,
   base/quote/settlement assets, perpetual/linear payoff, displayed size unit,
   contract multiplier, quantity step, price constraints, min notional,
   evidence reference, evidence digest, mapping version and validity interval.
3. The capture manifest includes the mapping-evidence member and digest; the
   mapping snapshot refers to that exact member. The report service accepts no
   mapping from request body, environment, database text or remote URL at build
   time.
4. Validator requires current Hyperliquid metadata to agree with the reviewed
   mapping, the book to be non-crossed and ordered, source/receive clock bounds,
   and the mapping validity interval to cover the snapshot.
5. The artifact keeps the sealed source manifest digest and all member digests,
   so a third party can verify the exact snapshot independently of localhost.

Do not add a retry transition from `BUILD_FAILED` or `REJECTED` to `PREPARING`.
A new attempt gets a new request/idempotency key and new capture/report IDs;
immutable failed evidence remains attributable.

### Testnet payment

Preserve this minimal graph:

```text
quote READY
  + attempt RECEIVED -> VERIFIED
  + atomic grant consumption
  -> attempt SUBMITTING / quote PAYMENT_PENDING
  -> attempt CONFIRMED / quote PAID
  |  attempt UNKNOWN / quote PAYMENT_UNCERTAIN
  |     -> CONFIRMED / PAID
  |     -> MANUAL_REVIEW / MANUAL_REVIEW
  -> REJECTED only before an ambiguous external outcome
```

Rules:

- `RECEIVED -> VERIFIED` is permitted only after exact quote/report/chain/token/
  amount/payer/payee/signature-domain/expiry binding.
- `VERIFIED -> SUBMITTING` consumes the exact short-lived grant atomically.
  Commit succeeds before external I/O; failure to consume means no submit.
- Once `SUBMITTING` is durable, no code path may return the quote to `READY`,
  create a second active attempt, or call the facilitator again.
- A definitive local/pre-submit rejection may become `REJECTED`; any timeout,
  disconnect, malformed facilitator response, transaction hint, or uncertain
  broadcast becomes `UNKNOWN` and reconciliation-only.
- `MANUAL_REVIEW -> CONFIRMED/PAID` is allowed only by the same canonical
  receipt validator and atomic entitlement commit, never by an operator toggle.

## Idempotency and concurrency checks

These are release blockers for the enabled vertical:

1. Same report idempotency key and byte-identical canonical body returns the
   same request/report/quote; changed body returns 409 and creates nothing.
2. Concurrent builders can claim a request once; only one immutable artifact
   directory and one quote appear. A losing worker cannot mark a completed
   request failed.
3. Repeated capture/report calls with the same generated IDs return verified
   existing bytes or conflict; they never overwrite.
4. Duplicate authorization identity, duplicate grant digest, duplicate grant
   UUID and duplicate payment attempt each cause zero facilitator calls beyond
   the first committed submit.
5. Crash before `SUBMITTING` is recoverable by rejecting the stale unsubmitted
   attempt and reopening an unexpired quote. Crash after `SUBMITTING` is
   confirm-only, including when `tx_hash` is null.
6. Two reconcilers use row locking/skip-locked and may commit at most one chain
   event, receipt and entitlement. Replaying an already confirmed request
   returns the stored receipt and cannot create another settlement.
7. Report and bundle delivery reuse one entitlement and do not increment the
   settlement count. Delivery is denied after retention expiry or any identity
   mismatch.

## Canonical receipt admission

Entitlement may be committed only when all of the following are rederived from
Mezo Testnet RPC and match immutable ledger terms:

- network `eip155:31611`, chain ID `31611`;
- exact pinned MUSD contract and amount `10000000000000000` atomic units;
- exact quote ID, report ID, report SHA-256 and payment-attempt ID;
- expected payer and distinct exact payee;
- transaction hash, canonical block hash/number and unique log index;
- exactly one matching canonical MUSD `Transfer` for this settlement identity;
- authorization identity and transfer identity matching the signed payload and
  transaction calldata;
- canonical Permit2/proxy/broadcaster identity and `tx.from != buyer`;
- buyer native-balance before/after observations on named canonical blocks,
  equality of those balances and persisted buyer gas spend `0`;
- at least 12 confirmations under the pinned finality-policy version, with the
  receipt block still canonical at admission time.

Wrong chain/token/amount/payer/payee, multiple matching transfers, missing log,
changed block hash, reorg, missing balance observation, nonzero buyer delta or
calldata mismatch must not entitle. If a transaction may have happened, route
to `MANUAL_REVIEW`; do not reject-and-retry.

## Schema and migration ruling

No migration is required for the minimum vertical as currently scoped. Tables
001--005 already model the necessary request, artifact, quote, attempt, grant,
chain-event, receipt and entitlement identities. Prefer application and
contract work for the reviewed live mapping and bounded grant composition.

If implementation discovers a fact that cannot be represented without JSON
inside `correlation` or `metadata`, stop and propose an additive migration with
an explicit uniqueness/check constraint. Do not repurpose mutable JSON as the
source of settlement authority. Migrations 004 and 005 intentionally refuse a
ledger containing receipts; retain that zero-receipt precondition for a fresh
environment and never fabricate provenance for an old receipt.

Before enabling against a retained database, verify exact migration checksums
001--005, no gaps/duplicates/unknown versions, and inspect:

```sql
SELECT state, count(*) FROM report_requests GROUP BY state;
SELECT state, count(*) FROM quotes GROUP BY state;
SELECT state, count(*) FROM payment_attempts GROUP BY state;
SELECT count(*) FROM live_grant_consumptions;
SELECT count(*) FROM chain_events;
SELECT count(*) FROM receipts;
SELECT count(*) FROM entitlements;
```

Counts must reconcile one-to-one for confirmed attempts, chain events,
receipts and entitlements. Every grant consumption must name one attempt that
is `SUBMITTING`, `UNKNOWN`, `MANUAL_REVIEW` or `CONFIRMED`; no consumed grant
may belong to `RECEIVED`, `VERIFIED` or `REJECTED`.

## Focused tests required

- Live HL capture with fixture transport: exact bytes seal successfully with a
  reviewed mapping; missing/expired/changed mapping evidence fails
  `IDENTITY_UNVERIFIED`; stale/future/crossed/reordered/malformed books fail
  closed and publish no artifact or quote.
- Capture/report crash and race tests: no partial target is treated as ready,
  existing targets are never overwritten, and digest readback detects mutation.
- PostgreSQL concurrency tests for duplicate request, builder claim,
  authorization, grant consumption, submit crash, reconciliation race and
  repeated confirmation/delivery.
- Receipt mutation matrix covering every identity field above, a reorg between
  observations, 11 versus 12 confirmations, duplicate Transfer logs and
  nonzero buyer native delta.
- End-to-end counter assertion: one grant row, one facilitator submission, one
  chain event, one receipt and one entitlement across report plus bundle reads.

## Operational stop conditions

Stop without a second submit when the durable attempt is `SUBMITTING` or later
and confirmation cannot be proved. Stop sale of a report if source freshness or
mapping validity cannot be proved, but retain already paid immutable historical
delivery while its entitlement is valid and artifact hashes still match.
Database, artifact storage, mapping identity, report readback, payment policy or
canonicality failure keeps readiness false.

This analysis did not read credential values, call Hyperliquid, call Mezo,
apply migrations, mutate a database or edit application code.
