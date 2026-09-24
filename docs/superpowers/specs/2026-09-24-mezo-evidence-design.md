# Liqvera Mezo Evidence — design

Date: 2026-09-24
Status: proposed for written-spec review
Change package: `engineering/changes/2026-09-24-mezo-evidence/`

## Intent

Liqvera will deliver one reproducible, read-only paid-report flow for the Mezo
Buildathon:

1. capture a public Hyperliquid BTC perpetual order-book snapshot;
2. validate source, timing, instrument identity, book shape, and available depth;
3. calculate an exact hypothetical BUY or SELL sweep without using binary floating point;
4. seal a report and independently verifiable evidence bundle;
5. expose a capability-protected quote and HTTP 402 payment boundary;
6. settle exactly 0.01 test MUSD on Mezo Testnet;
7. grant durable access to the same immutable report and bundle without a second charge.

The user purchases access to an analytical artifact. Liqvera never places an
order, accepts exchange credentials, promises execution, or represents the
report as trading advice.

## Delivery strategy

Work proceeds as seven coherent stages, with a green or explicitly blocked
exit artifact for each stage:

| Stage | Result |
| --- | --- |
| F1 | Reproducible public baseline, compatibility evidence, and accepted narrow ADR |
| F2 | Versioned OpenAPI/JSON Schemas, state graphs, exact test vectors, and failing contract tests |
| F3 | Real capture provenance/timing, immutable report builder, bundle, and offline verifier |
| F4 | Gateway, PostgreSQL ledger, capability authorization, quote creation, and unpaid 402 delivery |
| F5 | x402 verification/settlement, receipt validation, entitlement, and recovery |
| F6 | One-page testnet UI, isolated Compose stack, operational limits, and runbooks |
| F7 | Full fault/security suite, live-public/testnet acceptance, and competition package |

F0 is already complete and remains a provenance prerequisite. F5 cannot start
until F2–F4 contracts are stable. F7 remains blocked until a real controlled
testnet transfer is independently verified.

## F1 design

F1 is the first implementation unit. It does not add payment or report-serving
behavior.

### Baseline recovery

The public snapshot currently has three independent verification problems:

- four publication files are not represented in the closed architecture inventory;
- the salvage proof requires a Git object from private history that a public clone cannot contain;
- installed-wheel tests cannot run in the current interpreter because `hatchling` is absent.

F1 will first characterize each failure. It will then make the smallest
reproducibility repair:

- classify the four publication/provenance files in the architecture graph;
- replace the private-history dependency with a public-snapshot proof that validates
  the imported target files and explicitly records the weaker provenance boundary;
- create a repository-local, pinned development environment from `pyproject.toml` and
  run all baseline checks there;
- preserve the declared graph conflicts and the Stage A `INSUFFICIENT_EVIDENCE`
  semantics.

The repair must not silently skip a check, claim access to private source
objects, or convert a known failure into an unconditional pass.

### Compatibility lock

F1 records read-only probes for:

- Hyperliquid `meta` and `l2Book` for BTC;
- Mezo Testnet chain ID, MUSD bytecode, and MUSD decimals;
- facilitator `exact`/MUSD support for `eip155:31611`;
- availability and compatibility of a single `@x402/*` SDK version family.

The initial SDK candidate is `2.16.0`, matching the official Mezo quickstart.
All `@x402/*` packages must use one exact version. A newer release may replace
it only when a recorded compatibility probe demonstrates the required Mezo
Testnet registry and protocol behavior. Runtime dependencies never use
`latest` or mixed major/minor versions.

F1 does not require a merchant address, buyer key, or test MUSD. Absence of a
non-zero operator-owned `PAY_TO` keeps payment readiness false and is recorded
as an external blocker rather than populated with an example address.

### Narrow ADR

The F1 ADR will decide only the following:

- Python remains the authoritative capture, validation, exact-arithmetic, report,
  and verifier runtime;
- TypeScript/Express is limited to the browser/API/x402 boundary;
- PostgreSQL is the sole payment and entitlement state store;
- file artifacts are immutable and published by atomic rename;
- the only payment network is Mezo Testnet `eip155:31611`;
- live exchange mutation, mainnet, custody, and user keys remain impossible in
  this release.

The ADR does not accept a specific database schema or API payload before F2.

## Target architecture

### Components

`evidence-capture` has external access only to allowlisted public Hyperliquid
endpoints. It writes a per-run sealed input package containing exact response
bytes, the request body, origin, HTTP status, start/receive timestamps, exchange
timestamp, and digests. It receives no database, wallet, or payment environment.

`evidence-report` has no external network access. It reads a sealed package,
validates its manifest and instrument evidence, reconstructs the book, performs
an exact sweep, and atomically writes `report.json` plus the outer evidence
bundle. It preserves the old Stage A verdict as an independent field.

`mezo-gateway` owns the public HTTP API, capability authorization, quote and
payment state machines, x402 adapter, entitlement checks, and browser assets.
It may read final artifacts but cannot mutate them. It is the only PostgreSQL
writer.

`PostgreSQL` is authoritative for access scopes, requests, reports, quotes,
payment attempts, entitlements, and append-only audit events. Files remain
authoritative for immutable artifact bytes; the ledger binds their digests to
payment and delivery state.

### Data flow

1. A client creates a random 256-bit capability and submits instrument, side,
   quantity, expected payer, and an idempotency key.
2. The gateway creates a durable `PREPARING` request.
3. Capture writes and seals a unique raw package.
4. Report service validates the package, calculates the report, and atomically
   publishes the report and bundle.
5. Gateway performs a control read and changes the quote to `READY`.
6. An authorized unpaid report request receives HTTP 402 and pinned payment
   requirements; no paid report fields are exposed.
7. The gateway persists a payment attempt before settlement. An uncertain
   result becomes `UNKNOWN`/`PAYMENT_UNCERTAIN`, never unpaid.
8. After facilitator success, the gateway independently verifies the chain,
   receipt status, token, payer, receiver, amount, transaction hash, and log
   index before creating an entitlement transactionally.
9. The entitled capability receives the exact stored report and receipt.
   Repeated reads and bundle downloads do not settle again.

### Exactness and identity

All market quantities, prices, notionals, VWAP values, and impact values use
the existing Python exact types or rational numerator/denominator strings.
JavaScript `Number` and Python `float` are forbidden at money and quantity
boundaries. Payment uses integer atomic units; 0.01 MUSD is
`10000000000000000` units.

Live identity must cite stored metadata/mapping evidence with real hashes and
validity intervals. The inherited `"a" * 64` mapping is never chargeable. A
missing or conflicting property produces `IDENTITY_UNVERIFIED` or
`IDENTITY_MISMATCH`.

### Security and failure behavior

- `PAY_TO` is required, non-zero, operator-owned, and distinct from the buyer.
- The gateway stores only the capability hash; the raw capability is never put
  in a URL, log, metric, or database row.
- Payment signatures and authorization payloads are redacted from logs.
- No paid body is streamed before durable entitlement creation.
- Settlement timeouts never trigger a blind retry or a second authorization.
- Mainnet chain ID `31612` and every non-testnet network fail closed.
- Fixture artifacts are labeled `SIMULATED` and cannot become paid live quotes.
- Bundle extraction rejects traversal, symlinks, duplicate names, oversized
  files, and decompression bombs before writing output.

## API boundary

F2 will freeze the detailed schemas before code. The stable resource model is:

- `GET /healthz`
- `GET /readyz`
- `GET /v1/capabilities`
- `POST /v1/report-quotes`
- `GET /v1/report-quotes/{quote_id}`
- `GET /v1/reports/{report_id}`
- `GET /v1/reports/{report_id}/evidence`

Unknown request fields are rejected. Quote/report access uses Bearer capability
authorization independently of the expected payer address. The resource ID,
wallet address, report digest, and transaction hash never grant access.

## Testing

Each behavior change begins with a failing contract or characterization test.
The test pyramid is:

- existing Stage A unit, conformance, graph, installed-wheel, and artifact tests;
- exact report vectors and schema tests without network access;
- tamper, authorization, replay, timeout, crash, and concurrency tests;
- PostgreSQL integration tests against real migrations;
- offline end-to-end generation and verification;
- a separately invoked live-public probe;
- a controlled operator-confirmed testnet payment for A13.

Mock settlement proves state behavior but never satisfies A13. External
unavailability is reported as `BLOCKED_EXTERNAL`, not skipped or passed.

## Rollout and rollback

Every stage is committed separately and updates `handoff.md`. The new stack is
isolated from `compose.stage-a.yml` and remains testnet-only. No deployment or
GitHub push is part of an implementation commit.

Before F5, rollback removes only new stateless services and migrations that
have not stored payments. After payment state exists, destructive rollback is
forbidden: the old artifact and ledger remain readable, new quote creation is
disabled, and recovery proceeds by forward fix.

## Success criteria

The project is complete only when A01–A30 have evidence bound to the final
commit, including one real Mezo Testnet payment with buyer different from
merchant, repeat access without another settlement, an offline verifier on a
clean machine, and no regression in Stage A behavior.
