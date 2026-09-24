# Liqvera gateway

Status: **IMPLEMENTED_UNVERIFIED**. This code has not been built, typechecked,
run, or accepted. The owner deferred execution and verification to the next
phase. F2 vectors remain `NOT_RUN`; this implementation does not establish F4,
F5, testnet settlement, or release acceptance.

The Express process owns the frozen `/v1/*` HTTP surface, PostgreSQL ledger,
and official x402 2.16.0 boundary. Python remains responsible for all analytics
and immutable report construction. `@liqvera/mezo-protocol` supplies the
provenance-backed Mezo chain, token, ABI, Transfer event, and permit metadata.

## Build and start (deferred)

After the shared protocol package has been installed and built:

```sh
npm ci
npm run build
npm run migrate
npm start
```

The build copies frozen schemas and versioned SQL into `dist/`. Migrations
use a PostgreSQL advisory lock, transaction, and checksum ledger. They create
new tables only. Do not run migrations automatically from every HTTP request.

Configuration: `DATABASE_URL` or `DATABASE_URL_FILE` (exactly one), `PAY_TO`,
`SOURCE_MODE` (`fixture` by default), `ARTIFACT_ROOT` (`/data/artifacts`),
`REPORT_SERVICE_URL` (`http://report:8082`), `PUBLIC_BASE_URL`, `CORS_ORIGINS`
(comma-separated exact origins), `HOST`, and `PORT` (`8080`). Credentials stay
in secret files or process environment. No merchant private key is accepted.
TLS terminates at the isolated edge service. `trust proxy` is disabled; socket
IP budgets cannot be reset by a forwarded header. Metrics bind only to
`127.0.0.1:9090`; never forward that port at the public edge.

`POST /internal/v1/reports` receives only `report_id`, `instrument_id`, `side`,
and canonical `quantity_base`. Its result supplies digests, lengths, snapshot
metadata and limitations. The gateway ignores returned filesystem paths and
reads only `<ARTIFACT_ROOT>/<report_id>/report.json` and `evidence.zip` using
bounded no-follow reads and digest checks. Artifacts must not be in a public
static volume. Current Python recovery is an explicit unbound adapter and
returns false; paid-artifact corruption closes new sales and stays an incident.
The artifact mount is read-only. Unpaid retention cleanup calls the isolated
report service's idempotent `DELETE /internal/v1/reports/{report_id}` and
expects `{ "report_id": "…", "deleted": true }`. It requires an internal
service token loaded from `REPORT_SERVICE_TOKEN_FILE`; the token is also sent
on build and health calls when present. Missing credentials keep retention
mutation readiness false and cleanup blocked. The gateway never writes or
deletes artifact files itself.

## Payment boundary

Bootstrap uses unresolved authorization-identity and finality policies. No
environment flag can enable them. `PAY_TO` alone never enables payments.
Readiness names all blockers; fixture reports cannot produce chargeable quotes.
An eventual reviewed policy must define SDK-specific canonical identity,
nonce/replay domain, validity horizon, quote binding and exact chain-log
correlation, plus finality and reorganization rules. The current entrypoint
does not contact the facilitator automatically.

The adapter uses official SDK requirements, codecs, verification and settlement.
It intentionally does not install automatic payment middleware: the application
persists `SUBMITTING`, performs at most one settle call, independently checks
the MUSD Transfer and finality, then atomically persists receipt, chain event,
and entitlement before returning a paid body. A SDK success boolean or matching
payer/amount is insufficient. Payloads remain transient and are never stored
or logged. Recovery never resubmits an attempt; absent transaction correlation
ends in bounded manual review. Receipt and entitlement creation are one
transaction. Every subsequent read rechecks finality and artifact integrity.

Recovery preserves all scope, authorization dedup and ledger rows indefinitely
until a reviewed deletion policy proves replay impossible. Paid artifacts are
kept at least seven days; this implementation does not automatically delete
them. Unpaid cleanup waits fifteen minutes beyond expiry and excludes every
active, uncertain or manual-review attempt. Cleanup uses the report-service
adapter under the locked ledger decision. Rollback after any payment state exists
means stop new sales and forward-fix the ledger; never drop tables or restore
an older ledger over newer authorization records.

## Deferred verification obligations

Compile and typecheck the exact lock, validate all F2 response schemas, run
real PostgreSQL migration/rollback and 20-way idempotency races, compare state
transitions with `states.json`, and execute the F2 payment/recovery vectors.
Exercise crash-before-submit, crash-after-broadcast, missing transaction hash,
settlement timeout, response loss, expiry during settlement, cross-scope reads,
artifact tampering, reorganization, and log-redaction canaries. Verify official
SDK requirements/extra fields and MUSD permit domain from pinned dependencies.
The current finality/identity policy placeholders are deliberate release
blockers, not successful mock settlement. Live network/payment tests require
the separately authorized verification phase.
