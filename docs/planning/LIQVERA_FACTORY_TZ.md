# Factory specification: Liqvera

**Market reports you can verify.**

Built for [MEZO ₿](https://mezo.org/) — [The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

**Version:** 1.1 (Liqvera brand and publication status) · **Date:** September 24, 2026

**Product:** verifiable market report → HTTP API → payment in test MUSD → result delivery.

**Project owner / GitHub:** Dimkox. The owner reports that AKINDO registration is complete; no repeat registration is needed. Do not include the participant's email address in public files.

**Purpose:** a separate competition version of the existing Multi-Exchange Engine. This is an implementation specification, not a claim that the service is ready.

[README](../../README.md) · [Documentation index](../README.md) · [Handoff](../../handoff.md) · [Security](../../SECURITY.md) · [Original roadmap](../ROADMAP.md)

## 0. Assignment and current status

The standalone public repository [Dimkox/liqvera](https://github.com/Dimkox/liqvera) was created from a verified technical snapshot of `Dimkox/multi-exchange-engine`. Bring exactly one vertical scenario to a reproducible demonstration. Keep the source repository private; do not change its `main`, history, unfinished branches, or existing Stage A during the transfer.

When this specification was written, the source `main` was inspected at commit `4f6583f8590ea091d8a465de0c607e59bfe611a5`, dated August 21, 2026. The inspection date was September 24, 2026. This is a fixed baseline, not a claim that all other branches have been merged.

**F0 complete:** the technical snapshot was published with a new Git history, local scanning, personal-data cleanup, and anonymous-clone verification. The source remained private and its `main` was unchanged. The project received the approved Liqvera brand; the complete application, `make verify`, and on-chain payment have not yet been verified. Transfer results are documented in [PROVENANCE](../../PROVENANCE.md); F1 is the current next stage.

The agreed scope authorizes preparation of a public copy and development of the testnet scenario. It does not authorize mainnet, user capital, trading operations, purchases of cloud services, license changes, or disclosure of secrets.

## 1. Outcome for the user and Mezo

A trading-service developer or analyst selects BUY/SELL and a BTC quantity. The service obtains a public BTC-perpetual snapshot from Hyperliquid, validates the input, and produces an immutable report. Before payment, it shows the report subject, snapshot time, validation status, available-depth limitation, and exact access price. After a confirmed transfer of test MUSD, the user receives JSON, a human-readable view, and a package for independent recalculation.

The user purchases access to an analytical artifact, not bitcoin, a trade, a trading signal, or returns. MUSD is used to pay for the API. MEZO is not needed for this MVP.

The demonstration's value is the path from raw bytes to a reproducible calculation and confirmed payment, without access to an exchange account. Testnet payments demonstrate technical integration, but not revenue, willingness to pay, or PMF.

## 2. Verified foundation and actual gaps

| Baseline component | Established fact | Implementation requirement |
|---|---|---|
| `packages/contracts` | Active `mee-contracts` package | Preserve exact numbers, types, and constraints |
| `packages/public-capture` | `source=public` requests only Hyperliquid `l2Book` for BTC | Use one live source; do not present the Lighter fixture as live |
| `packages/readonly-analyzer` | Includes a sealed-package reader, reconstruction, identity binding, and `sweep_depth` | Reuse these; do not rewrite the calculation core in JavaScript |
| `vwap.py` | BUY consumes asks, SELL consumes bids; calculations use `Fraction`; insufficient depth is rejected | Preserve mathematical semantics and full rejection when depth is insufficient |
| Identity mapping | `REVIEWED_BTC` contains `evidence_sha256 = "a" * 64`, a `reviewed/v1` reference, and static parameters | For live reports, replace nominal provenance with real, retained evidence; do not call a placeholder verification |
| Capture timing | Runtime passes `terminated_at_ms = started + 1` | Do not use this value as measured latency; record actual data receipt separately |
| `verdict.py` | Economics are read from optional `economics.json`; VWAP is not connected to the verdict | The new snapshot report must not change the old verdict or fabricate economics |
| Stage A | A family of decisions about the quality/sufficiency of sustained observation, not permission to trade | Preserve `INSUFFICIENT_EVIDENCE` where it is correct; do not create `GO` |
| Payments / API / UI | The selected end-to-end scenario is not established in the inspected baseline | Implement it and provide evidence separately |

Do not conflate two different concepts: **the snapshot is sufficient for arithmetic over the available levels** and **the observations are sufficient to draw a conclusion about a strategy**. The first may be true while the second remains `INSUFFICIENT_EVIDENCE`.

The official Hyperliquid `l2Book` returns at most 20 levels per side [S3]. The UI must say “calculation over the available snapshot depth,” not “the exchange's complete order book” or “guaranteed execution.”

## 3. MVP boundaries

Include one instrument—Hyperliquid BTC linear perpetual—one payment network—Mezo Testnet—BUY/SELL, quantity in BTC, a JSON API, a browser payment flow, an evidence bundle, and an offline verifier. The instrument name must explicitly include `perpetual` and must not suggest a spot BTC purchase.

Exclude Lighter live, cross-venue comparison, arbitrage, trades, exchange API keys, funding/net P&L, borrowing, leverage, swap routing, bridges, MEZO trading, custom smart contracts, custody, mainnet, Telegram/Kakao, email registration, CRM, paid AI services, and subscriptions. Do not rewrite the retained Go code; it is not the active runtime. Do not create GitHub Actions or automatically enable inherited workflows.

Two environments are required: `fixture` for deterministic checks without a network and `live-public + mezo-testnet` for the final demonstration. Fixture results are marked `SIMULATED`; the published paid demo configuration must not sell a fixture as live data.

## 4. F0 — safe public copy

**Status:** complete for Liqvera. The criteria below are retained to verify and reproduce the transfer.

This is a standalone repository, not a GitHub fork of a private repository: a normal fork's visibility is linked to its upstream [S4]. Do not change the source's visibility or mirror-push its history.

The factory must:

1. Verify the identity of the authorized GitHub connection and its ability to create repositories under Dimkox. Do not print tokens or passwords or ask for them to be pasted into chat. Use the authorized CLI/API available to the factory.
2. Record `git status --short`, separately `git diff --stat`, staged/untracked state, and the local source's current refs. Do not reset or include the user's unfinished changes in the publication. Create a separate working directory; do not blindly reuse old worktrees.
3. Obtain the source's full available history in a private temporary area and run a redacted secret scan over the entire history and current tree according to `SECURITY.md`. The scanner runs locally; finding values must not reach the LLM, chat, or public reports. Any active secrets found require rotation by the owner; removing them from the snapshot alone does not resolve the incident.
4. Also inspect personal contacts, private infrastructure addresses, dumps, logs, `.env`, sessions, private keys, `.gitmodules`, LFS objects, symlinks, third-party licenses, and generated archives. Do not certify the safety of the entire history from a README alone.
5. Export the technical snapshot of the fixed baseline into a new history with its own root commit. Transfer source code, tests, required documents, build configuration, and applicable notices. This must be a copy of the technical foundation, not an empty scaffold. Do not transfer `.git`, old refs, issues, PR discussions, workflow runs, secrets, or private runtime artifacts.
6. Prepare `PROVENANCE.md`: upstream, baseline SHA, import date, file/hash inventory, exclusions and reasons, and retained attribution. Keep the full private scan report outside the public repository; publish only an anonymized summary.
7. Preserve existing license/NOTICE files. The GitHub API did not recognize the source license during inspection. Do not add MIT/Apache by default or declare the project open source solely because it is publicly visible. If the competition requires a particular license, record a separate owner decision.
8. Create `Dimkox/liqvera`; before the first push, disable GitHub Actions execution at the destination if the snapshot contains workflows. Do not transfer secrets/environments. If the name is taken, verify ownership and provenance; do not overwrite another owner's or an unexpected repository.
9. After scanning, publish the clean snapshot, then this specification and documentation pointers. Separate the import and new competition changes into understandable commits. Do not claim in the README that payments are already implemented.
10. Verify `private=false` metadata, anonymous access, and a clean clone without authentication. Compare the files with the inventory. Separately confirm that the upstream remained private and this operation did not change its `main`.

If F0 is blocked, leave a local package and the precise status `PUBLICATION_BLOCKED`. Do not simulate completion by creating a link to a nonexistent repository. Independent development may continue in an isolated private working copy; public release is prohibited until F0 is closed.

## 5. Architecture and isolation

Keep Python as the analytics core. Add a TypeScript/Express gateway for the official x402 EVM SDK instead of rewriting payment cryptography. Record this decision in a separate ADR in the competition repository: JavaScript serves the payment boundary here and does not replace the active Python runtime.

Physical roles in the demo stack:

| Role | Purpose | Access |
|---|---|---|
| Gateway / UI | Public API, quotes, x402, paid-report delivery, reconciliation | Facilitator, testnet RPC, PostgreSQL; read-only access to completed artifacts |
| Public capture service | Obtain public HL data and metadata, retain the raw package | Only allowlisted public HL endpoints; write to raw volume; no payment environment |
| Read-only report service | Verify sealed input, bind identity, calculate VWAP, write a new report artifact | Raw volume read-only, output volume write; internal HTTP, no internet egress |
| PostgreSQL | Quote/payment/entitlement, idempotency, durable recovery | Gateway only; separate database and migrations |

Do not add Redis, Kafka, external object storage, Kubernetes, or a custom facilitator. Retain evidence on dedicated persistent volumes with atomic file publication. Separate internal networks and bound ports must prevent public access to capture, analyzer, and database services. Do not connect the analyzer role to a network with external egress. Keep the original `compose.stage-a.yml` and its fixture mode independent.

Recommended new areas: `apps/mezo-gateway/`, `packages/evidence-report/`, `services/evidence-capture/`, `services/evidence-report/`, `contracts/mezo-evidence/`, `deploy/mezo-evidence/`, `tests/mezo-evidence/`. These are target areas, not a claim that they exist. The factory determines the minimum files after reading existing interfaces; it must not create empty layers merely for structure.

Capture and analyzer must not receive the gateway's entire `process.env`: the source enforces checks on credential-like names. Do not weaken them for `TOKEN`, `PASSWORD`, wallet, or database variables. The gateway holds the recipient address, but not its private key; the user signs in their own wallet.

## 6. Instrument data and time boundaries

For every live report, retain the unchanged `l2Book` response bytes, public request body, verified origin, actual UTC start/receipt times, exchange timestamp, HTTP status, payload SHA-256, and associated metadata evidence. Do not retain user HTTP headers, cookies, or secrets.

The `product_kind`, base/quote/settlement asset, quantity unit, and multiplier must have verifiable provenance: an official metadata response and/or a versioned reviewed mapping with a real source reference and hash. Do not treat the string `APPROVED` as evidence or inherit a fictitious hash. Do not present automated document reading as human review. If the API lacks a required property, resolve it through separately reviewed evidence or leave the report `IDENTITY_UNVERIFIED`.

The current `sweep_depth` permits only bound identity, `displayed_size_unit=coin`, and multiplier=1. Preserve these checks. Do not convert sizes with an arbitrary multiplier. Quantity must be a positive decimal string representable in the existing exact type; reject unsupported precision instead of silently rounding. Do not claim that a hypothetical snapshot sweep satisfies every actual exchange order constraint.

Initial product policy, not protocol properties: at most 5 000 ms between source timestamp and receive timestamp; a source timestamp more than 1 000 ms in the future produces `CLOCK_SKEW`; metadata evidence must be no older than 24 hours and within its validity interval. Version all limits and test their boundaries. A quote lives for 120 seconds after the report is ready. Freshness is checked at creation; during payment the report becomes a historical snapshot, which must be clearly shown to the user.

Validate correct JSON, finite positive prices, nonnegative sizes, level ordering, instrument identity, absence of a crossed/locked book, and sufficient depth. Do not silently repair duplicates or incorrect ordering. Any normalization is allowed only under an existing verified contract and with evidence. Do not accept user-supplied URLs, file paths, market mappings, or upstream HTTP payloads.

## 7. Report contents and precision

New schema: `mee-evidence-report/v1`. Closed set of `snapshot_status` values: `VALID_FOR_SNAPSHOT_CALCULATION`, `REJECTED`, `SIMULATED`. Only the first permits a live chargeable quote; it is not a profitability assessment. Do not rename `mee-stage-a-decision/v1` or change its meaning. The new report may include the original Stage A verdict as an independent field explaining why sustained observations are insufficient.

Required fields:

| Group | Contents |
|---|---|
| Identity | `report_id`, schema version, venue, instrument id, product kind, base/quote/settlement asset, mapping version and evidence references |
| Request | side, `quantity_base` as a decimal string, BTC unit |
| Time / source | created/observed/source timestamps, build-time age, `source_mode`, payload and package hashes, actually available levels on each side |
| Calculation | requested/filled quantity, notional, VWAP, worst consumed price, consumed levels, price impact relative to the best level on the relevant side |
| Quality | `snapshot_status`, stable reason codes, checks performed and limitations, separate Stage A verdict |
| Reproducibility | engine commit, package versions, lockfile digests, calculation/policy version, input-file list and hashes |
| Conclusion boundaries | `execution_authority=NONE`, fees/funding/net P&L not calculated, no execution promise |

Do not turn the internal name `ExecutableFill` into a claim of a real fill. Use “hypothetical snapshot sweep” in the public presentation. Do not conflate the network fee for paying for a report with fees for a hypothetical exchange trade.

BUY: traverse asks in ascending order; SELL: bids in descending order. Notional is the sum of price × consumed quantity; VWAP is notional / requested quantity. If depth is insufficient, reject the entire request; do not sell a partial result as complete. BUY impact = (VWAP / best ask − 1) × 10 000 bps; SELL impact = (1 − VWAP / best bid) × 10 000 bps.

Prices, quantities, and monetary values must not pass through JavaScript `Number` or Python `float`. For non-terminating fractions, retain exact numerator/denominator values as strings; round the decimal presentation using `ROUND_HALF_EVEN` to an explicitly defined display precision. Verify the canonical calculation using fractions, not the rounded string. Store payment amounts as integer atomic units independently of exchange exact types.

Reference example: asks 100000 × 0.10 BTC and 100100 × 0.10 BTC; BUY 0.15 BTC. Notional = 15005; VWAP = 300100/3; worst price = 100100; consumed levels = 2; impact = 10/3 bps. BUY 0.21 BTC must produce `DEPTH_INSUFFICIENT`, without payment. This is a synthetic test vector, not a market quote.

Minimum reason codes: `INVALID_INPUT`, `INVALID_DATASET`, `SOURCE_UNAVAILABLE`, `STALE_SOURCE`, `CLOCK_SKEW`, `IDENTITY_UNVERIFIED`, `IDENTITY_MISMATCH`, `CROSSED_BOOK`, `DEPTH_INSUFFICIENT`, `UNSUPPORTED_INSTRUMENT`, `SIMULATED_SOURCE`. Do not hide a specific cause behind a generic “server error.”

## 8. Evidence bundle and offline verification

The bundle contains the original sealed input package, `report.json`, a separate file SHA-256 manifest, source/mapping evidence, and algorithm-version information. Do not modify the existing sealed package by adding the report inside it: retain it as a separate nested artifact so member-set validation remains intact.

Calculate `report_sha256` from the final canonical UTF-8 bytes of `report.json`; do not include its own digest in the hashed body. Version the serialization and fix key sorting, string formats, and the final newline. The receipt references the report digest; separate UI status strings must not change report bytes.

The CLI verifier works without a wallet, internet, or database. It checks the schema, allowed file names/sizes, manifest, raw payload hashes, reconstruction/identity, and recalculates values using exact arithmetic. Successful verification returns exit code 0; corruption of any meaningful field returns a nonzero code and reason. Reject ZIP path traversal, symlinks, and decompression bombs before extraction.

Honest boundary: hashes and recalculation confirm integrity relative to the received manifest and reproducibility. They do not by themselves prove that the exchange signed the data, that the operator did not fabricate the original snapshot, or that a trade can be executed now. A blockchain receipt confirms payment, not the accuracy of a market forecast. On-chain report anchoring and custom data signatures are outside the MVP.

## 9. External API contract

Before writing code, define OpenAPI and JSON Schema, error versions, and test vectors. Do not accept arbitrary fields. Include a safe `request_id` in responses and logs, without wallet secrets or payment signatures.

| Method / path | Behavior |
|---|---|
| `GET /healthz` | Liveness without private data; no payments |
| `GET /readyz` | Storage, configuration, and integration readiness; failure closes new payments and must not report a fictitious PASS |
| `GET /v1/capabilities` | Instrument, testnet, price, data mode, and limitations; no secrets |
| `POST /v1/report-quotes` | Validate the request, prepare and retain the report; only then issue a quote |
| `GET /v1/report-quotes/{quote_id}` | Authorized retrieval of status, preview, expiry, and recovery state; does not reveal the paid body |
| `GET /v1/reports/{report_id}` | 402 with x402 requirements before payment; 200 with report and receipt after confirmation |
| `GET /v1/reports/{report_id}/evidence` | Bundle under the already-paid entitlement; no second payment |

Create request: instrument id, BUY/SELL, `quantity_base`, expected payer EVM address. The server chooses source/price/payTo. `Idempotency-Key` is required when creating a quote. The same key with the same normalized body and access scope returns the same object; a changed body produces 409. A concurrent retry of a build still in progress may receive 202 with a status location.

Access to the quote/report is protected by an independent capability: before the first request, the client generates a random secret of at least 256 bits and sends it as Bearer. The browser stores it in sessionStorage for recovery after reload; an API client stores it locally. The server stores only its hash and binds objects to it. This is not a wallet private key or trading API key. The secret, quote id, and idempotency key have distinct purposes. IDs, wallet addresses, public tx hashes, and report hashes are not authorization.

The payment payer must match the quote's expected address; a valid payment signature, not a request field, establishes payer authenticity. A different access scope must not obtain the quote/status/report even when it knows the ID or tx hash. Do not place the capability in URLs, access logs, or analytics. For unauthenticated requests or another scope's resource, return a consistent 401/404 policy without leaking whether the object exists.

The preview contains only instrument/side/quantity, snapshot time, quality level, limitations, price, and expiry. The full calculation, raw bundle, and internal paths are unavailable before payment. For rejection, show a free explanation and do not create a chargeable quote.

Codes: 201 — ready quote; 200 — resource; 202 — build or uncertain settlement is still being checked; 402 — payment authorization required; 409 — conflict/inappropriate state; 410 — expired quote or documented end of retention; 422 — invalid parameters or unusable data; 429 — rate limit; 503 — unavailable upstream/storage/payment service. Do not add a second incompatible payment format to 402: follow the pinned x402 SDK.

## 10. Mezo/x402: configuration and preflight verification

According to official Mezo documentation on the inspection date [S1, S2]:

| Parameter | MVP value |
|---|---|
| Network | Mezo Testnet, chain ID `31611`, CAIP-2 `eip155:31611` |
| RPC | `https://rpc.test.mezo.org` |
| Explorer | `https://explorer.test.mezo.org` |
| MUSD | `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503` |
| Decimals | 18 |
| Facilitator | `https://facilitator.vativ.io` |
| Protocol | x402 v2, EVM `exact`; official MUSD/Permit2/EIP-2612 support |
| Headers | `PAYMENT-REQUIRED`, `PAYMENT-SIGNATURE`, `PAYMENT-RESPONSE` |
| Demo price | **0.01 test MUSD = 10000000000000000 atomic units**; a product setting, not a market valuation |

The official quickstart shows the `@x402/*` 2.16.0 package set [S2]. This is an initial reference configuration, not an unconditional instruction to use an old version. In F1, verify package existence/compatibility and network/facilitator availability; retain the exact verified versions and lockfile. Do not install `latest` at runtime, mix major versions, or copy USDC six-decimal formatting.

Before opening the payment route, verify the actual `eth_chainId`, token bytecode, `decimals`, network/scheme support through facilitator capabilities, and that the SDK registry matches the expected MUSD. Documentation does not replace this runtime verification. Do not substitute fictitious success, a homemade ERC-20, or mainnet for missing testnet support.

`PAY_TO` is required, validated, and belongs to a dedicated merchant test wallet. Do not use the recipient address from the Mezo example, the zero address, or an implicit default. The demo buyer and merchant are distinct. The gateway does not need the merchant private key. If no address is provided, payment readiness=false; this does not block analytics development.

For test MUSD, the documentation describes obtaining test BTC and minting MUSD through testnet borrowing [S2]. Do not promise a direct MUSD faucet. The operator obtains funds in a separate test wallet; lack of a balance is a named blocker, not a reason to touch real funds. Do not send payments to someone else's demo service as a hidden acceptance test.

Configuration and request checks must reject mainnet chain `31612` and every other network. A move to mainnet must not be implementable with a single environment switch: it is outside this release.

## 11. Payment protocol and recovery

Main flow:

1. The gateway creates a durable request record and initiates capture/report generation. A quote appears only after the report and bundle have been saved and read back for verification. Data or storage errors must not lead to a payment signature.
2. The quote immutably binds report id/digest, buyer, access scope, chain, asset, atomic amount, payTo, version, and expiry. Every price to be signed must match the displayed price.
3. An unpaid report GET with the correct capability returns 402 and standard requirements. The UI shows the recipient address, 0.01 test MUSD, network, and original snapshot time. The user explicitly confirms payment in their own wallet.
4. The client repeats the GET with `PAYMENT-SIGNATURE`. The server verifies signature, payer, chain, token, amount, receiver, deadlines, nonce, and compliance with the fixed terms. `verify=true` alone does not mean payment is complete.
5. Before `/settle`, retain a unique payment attempt and the authorization→quote association. Make the outbound network call after the durable commit. A quote has at most one active settlement attempt at a time.
6. After a positive settlement response, verify the chain transaction receipt, success status, canonical block, and the specific token's MUSD Transfer from buyer to merchant for the required amount. Bind the event to the specific authorization, rather than merely finding a similar transfer. Record the verified finality rule in F1; mempool acceptance alone is insufficient.
7. In one database transaction, retain the settled payment, immutable receipt, and entitlement to the specific report digest. Only then return the paid body and `PAYMENT-RESPONSE`. Do not stream the body before settlement.
8. An entitlement owner's repeat request receives the same artifact and receipt without a new signature or `/settle`. A disconnect after charging, restart, or multiple tabs must not require a second payment.

Quote/report states: `PREPARING → READY → PAYMENT_PENDING → PAID`; separate branches `BUILD_FAILED`, `REJECTED`, `EXPIRED`, and `PAYMENT_UNCERTAIN`. Payment-attempt states: `RECEIVED → VERIFIED → SUBMITTING → CONFIRMED`, or `REJECTED` / `UNKNOWN`. Record delivery separately: a server response does not prove the client received it. State transitions are atomic and checked against the permitted graph.

On a `/settle` timeout or a crash after broadcast, set `UNKNOWN` / `PAYMENT_UNCERTAIN`, not “unpaid.” Do not create a new authorization/nonce or blindly retry the charge. Recovery first checks the retained tx hash and on-chain authorization state. If no tx hash was received, use only actually supported lookup and correlation methods based on nonce/transaction evidence; do not invent a facilitator `/status` endpoint. Matching payer/amount/time is insufficient when several payments are identical. An ambiguous case remains blocked for operator recovery, without a second charge or a settlement claim.

Idempotency is enforced by the database, state locking, and on-chain authorization identity. A raw-payload hash alone is insufficient: different encoding/signatures of the same authorization must not bypass deduplication. Define canonical identity, nonce semantics, and the replay domain for the SDK actually selected. Do not assume x402 automatically cryptographically signs the report id or URL: resource binding is checked against the actual scheme and server ledger; one authorization must not serve two quotes.

Quote expiry prohibits starting a new payment but does not cancel one already started/confirmed. If broadcast occurred before expiry and payment confirmed later, deliver the original report. An already-paid historical report must not be blocked as stale or recalculated against a fresh market. After entry into `SUBMITTING`, artifact cleanup is prohibited until reconciliation.

Do not deliver the body without receipt finality, with the wrong asset/amount/payer/receiver/network, a reverted transaction, reused authorization, or failed verification. A reorganization/RPC inconsistency puts the attempt under review and must not initiate another transfer. The system does not promise distributed “magical exactly once”: it must demonstrate at-most-once charging per confirmed authorization, durable entitlement, and safe behavior under an unknown outcome.

## 12. Persistence and retention

PostgreSQL is the source of truth for payment state; versioned migrations are required. The gateway is the ledger's only writer. Do not connect capture/analyzer to the factory's existing production database.

Minimum entities: access scopes, report requests, reports/artifact manifests, quotes, payment attempts, entitlements, and append-only audit events. Foreign keys and uniqueness constraints are required for `(access_scope, idempotency_key)`; canonical authorization identity; `(chain_id, tx_hash, log_index)`; and entitlement to a quote/report. One tx may contain multiple logs—a tx hash without a log index is insufficient. Retain chain/asset/amount/payTo/payer, report digest, state, times, error/recovery code, and version, rather than substituting arbitrary JSON for all constraints.

Every capture receives its own new directory under an internal run/report id. The current package writer clears the supplied root: using one shared directory for concurrent reports or pointing the writer at a user-supplied path is prohibited. Do not call `make prod` from the API: the baseline command clears its Stage A volume.

Artifact publication: temporary directory → write and flush → hash verification → atomic rename → READY status. Detecting an unfinished write after restart must not turn it into a ready report. Never overwrite an immutable report under the same id. Before settlement, a verification read must confirm the exact bytes are present.

Initial limits: paid reports and bundles remain available for at least 7 days after payment confirmation; unpaid artifacts are deleted no sooner than 15 minutes after expiry and only when there is no pending/unknown payment. Retain UNKNOWN until resolved. Retain the ledger, access-scope binding, and dedup records for at least 30 days and never less than the authorization's validity period. Ledger deletion must not enable replay. Show actual retention periods before payment.

Loss of a confirmed artifact closes new sales and triggers recovery from the retained sealed input; regeneration is allowed only if the previous report digest matches. Do not require an additional payment for recovery. Do not add automatic refunds or a merchant signing key to the MVP; record an unrecoverable case as an incident and test its detection.

## 13. UI and demo

One page with an English interface for the judges; English is the default throughout, including operator documentation. The header always displays `TESTNET ONLY`, `READ-ONLY ANALYTICS`, and the data mode. No buy/sell execution buttons: BUY/SELL refer to the calculation, with an adjacent explanation.

Sequence: select side/quantity → connect an EVM wallet and check the network → obtain quote/preview → confirm price → sign payment → view report/receipt → download bundle → reopen without another charge. Switching wallets after a quote is issued requires payer verification, not payment of the old terms by another account.

Show snapshot time and age, sampled depth, VWAP/worst price, consumed-level count, calculation limitations, and a testnet transaction link. Do not turn `READY` into a green “ready to trade” indication. For stale/identity/depth rejection, provide a free, understandable reason. On settlement timeout, say “checking the payment already submitted,” rather than offering a “pay again” button.

No registration, email forms, seed/private-key input, user API keys, hidden automatic charges, or unlimited approvals. If the selected SDK scheme actually requires an approval, make it a separate, explicitly displayed, limited testnet operation after ADR review, not a hidden signature.

## 14. Nonfunctional requirements

One gateway replica and a small worker pool are sufficient for the MVP; payment correctness must not depend on this configuration. Transaction-safe concurrent tests with at least 20 parallel repeats of one request are required.

Initial product limits: JSON body ≤16 KiB, decoded payment payload ≤16 KiB, bundle ≤10 MiB, at most 4 concurrent builds, and 5 new quotes per minute per access scope with an additional IP/global budget. Public IDs/statuses and paid reads have a separate rate limit. Limits are configurable, documented, and must not be bypassed by a new client header.

The overall build deadline is 15 seconds, with no more than two upstream attempts within that budget. Settlement timeout limits HTTP waiting; it does not establish payment failure. Reconciliation has bounded attempts/backoff and an explicit `MANUAL_REVIEW`, not an endless loop. A ready paid artifact with healthy local storage must be served at p95 <1 second on the documented demo host; measure upstream/block latency separately and exclude it from this promise.

TLS, an exact CORS allowlist, CSP, egress restrictions, non-root containers, read-only mounts, and minimal dependencies are mandatory. Do not store bundles under a public static path. Use `Cache-Control: private, no-store` for quote/payment/report responses; CDN caching of paid bodies is prohibited. Exclude payment/capability headers from reverse-proxy, APM, and application logs. No arbitrary redirects for RPC/facilitator/upstream.

Metrics without high-cardinality wallet labels: build duration/rejections, readiness, 402 responses, verified/settled/unknown, reconciliation duration, duplicate attempts blocked, delivery failures, and artifact integrity failures. Log request/quote/payment correlation IDs and stable error codes. Do not include signatures, bearer tokens, database credentials, or the participant's email address in demo/release logs.

## 15. Tests and acceptance criteria

The original `make verify` and relevant conformance/installed tests must pass before and after the change. Do not “fix” the existing `INSUFFICIENT_EVIDENCE` to match an expected commercial answer. Go tests are not evidence for Stage A.

| ID | Check | Required result |
|---|---|---|
| A01 | Clean baseline and modified tree | Separately retained check results; pre-existing failures are not hidden |
| A02 | BUY test vector from §7 | Exact notional/VWAP/worst price/levels match |
| A03 | SELL, one level, exactly all depth, non-terminating decimal fraction | Correct sides and exact rational values |
| A04 | Insufficient depth, zero/negative, float, NaN, unsupported precision | Rejection; no chargeable quote and no settlement |
| A05 | Stale/future timestamp, crossed book, wrong instrument, metadata gap | Specific reason code; no sale of an incorrect report |
| A06 | Mapping with a fictitious source hash or wrong unit/multiplier | `IDENTITY_UNVERIFIED`/rejection; no nominal PASS |
| A07 | Live mode without HL access | `SOURCE_UNAVAILABLE`; no hidden fixture fallback |
| A08 | Raw/mapping/report/manifest corruption and ZIP traversal/bomb | Offline verifier rejects |
| A09 | Bundle recalculation on a clean machine without a network | Same exact result and digest |
| A10 | Unpaid authorized GET | 402, correct x402 headers; no paid body |
| A11 | Wrong signature/network/token/amount/receiver/payer, expired/reused authorization | Neither entitlement nor paid body |
| A12 | 18 decimals / 0.01 test MUSD | Exactly 10000000000000000 units in every layer |
| A13 | Testnet happy path, buyer ≠ merchant | One confirmed MUSD Transfer and one entitlement |
| A14 | Repeat GET and bundle download after payment | Same report/receipt, zero additional settlements |
| A15 | 20 concurrent quote/payment retries | One logical quote and at most one charge |
| A16 | Same idempotency key with a different body | 409 without a new action |
| A17 | Crash before submit, after broadcast, after chain success before database commit | Correct recovery; unknown outcome is not treated as failure |
| A18 | Client response lost after settlement | Access recovery without a new signature/payment |
| A19 | Timeout without a tx hash and multiple similar Transfers | No false CONFIRMED and no repeat charge |
| A20 | Expiry during settlement | Confirmed payment unlocks the original report |
| A21 | Another scope's capability, guessed ID, or public tx hash | No access obtained |
| A22 | Report file disappears before payment / is corrupted after payment | Before: no charge; after: recovery/incident, no additional payment |
| A23 | Substituted RPC chain ID, registry token, mainnet configuration | Payment readiness=false / rejection |
| A24 | Facilitator verify success, settle failure/unknown | Paid body withheld until confirmation |
| A25 | Raw signatures/keys/capabilities in logs and browser bundle | None found; redaction tested with canary values |
| A26 | Network/container boundaries | Analyzer has no external egress; capture cannot see payment/database environment |
| A27 | Existing Stage A verdict and fixture suite | Not changed for the new packaging; `GO` remains impossible |
| A28 | Clean installation following README | Build and offline demo reproduce from lockfiles |
| A29 | Public clone and provenance | Anonymously readable; snapshot compared; upstream privacy preserved |
| A30 | Wallet cancel, wallet switch, reload, wrong chain | No implicit payment; UI shows correct recovery |

Separate levels: unit/contract/fault tests with mocks; integration with real PostgreSQL; offline end-to-end; and a separate live-public/testnet end-to-end test. Mocked settlement does not replace A13. External unavailability produces `BLOCKED_EXTERNAL`, not PASS or a silent skip.

For A13, the operator uses a dedicated test buyer, explicitly confirms a limited amount, and retains tx hash/block/log index. No funds are transferred as part of writing this specification itself.

## 16. Factory task decomposition

| Stage | Work | Dependencies | Exit artifact |
|---|---|---|---|
| F0 | Safe snapshot, scan, and public destination | Authorized GitHub create/push | Public URL, anonymous clone proof, provenance, redacted scan summary |
| F1 | Verify baseline, live metadata, SDK/Mezo/receiver/finality; accept a narrow ADR | Read source; publication may still be blocked | Baseline results, ADR, compatibility lock, named blockers |
| F2 | OpenAPI/JSON schemas, quote/payment state graph, exact test vectors | F1 | Machine-readable contracts, invariants, failing tests |
| F3 | Real provenance and capture timing; report builder and verifier | F2 | Reproducible offline bundle and live-source validation |
| F4 | Gateway, PostgreSQL migrations, quote/capability, protected delivery without real settlement | F2–F3 | API tests; 402 and correct rejection without payment |
| F5 | x402 adapter, durable settlement, entitlement/reconciliation | F1, F4 | Replay/concurrency/crash tests, then controlled testnet payment |
| F6 | Minimal UI, isolated Compose, rate limits, runbook | F4–F5 | Browser flow and clean installation |
| F7 | Independent review, fault suite, live-public/testnet demo | F0–F6 | Acceptance report, release candidate, competition materials |

Parallelize independent research, test analysis, documentation, and review. A single write-agent owns application-code changes. Do not start F5 before quote/report contracts are stable; do not build the UI on shifting JSON. Do not declare F7 closed if either F0 or testnet payment is blocked.

Every significant stage leaves a coherent commit, updated `handoff.md`, and factual evidence with the exact commit SHA. Do not lose user changes. No force pushes, bulk deletion, fabricated CI checks, bypassing branch protection, or automatic merges into the source `main`.

## 17. Competition packaging and dates

Track: **Access and distribution**, extending an existing product. MUSD is used directly in the working API; adding a logo does not count as integration. In the submission, distinguish the imported baseline from new commits and include architecture, public code, instructions, video, and a confirmed testnet transfer. Do not present old code as written during the competition.

According to the organizer email provided: Wave 1 — October 16–26, Wave 2 — November 2–15, demonstrations/announcement — November 23. Planning assumes 2026, but the factory/owner must verify exact submission cutoffs and timezone in AKINDO. The event pages could not be independently read when this specification was prepared; these dates are not presented as reverified rules.

Internal checkpoints: Wave 1 candidate — October 25, 2026; Wave 2 candidate — November 14, 2026. These are proposed project buffers, not organizer-assigned deadlines. Do not postpone the technical baseline until Wave 1 opens; separately check the rules for eligibility of earlier competition changes and disclose them honestly.

Wave 1: one working scenario, offline verifier, actual testnet payment, and basic fault tolerance. Wave 2: address feedback and improve recovery/tests/UX. More exchanges and mainnet do not become mandatory even in the second wave.

## 18. Definition of Done and handoff

Work is complete only when all of the following exist together: a public, anonymously cloneable technical repository with provenance; an intact original Stage A; confirmed metadata/timing; a reproducible report; unpaid 402; successful test MUSD payment; repeat retrieval without repeat payment; a verifier on a clean machine; fault/security tests; startup and recovery instructions; a testnet-only UI; and retained acceptance evidence.

Final materials at the destination: README with actual status, this specification and its index, a narrow ADR, OpenAPI/JSON schemas, source/tests/migrations, lockfiles, isolated Compose, safe `.env.example` files without secret values, `PROVENANCE.md`, testnet runbook, recovery runbook, acceptance report, a short demo script, and an English competition description. Docker/lockfiles must not require private GitHub access for a public build.

The acceptance report must list each group's command, environment, time, code SHA, exit code, results, and omissions; for payment, include testnet transaction evidence without keys/signatures. Add video/hosting links only after they actually exist. Do not automatically purchase paid cloud services or enable production deployment or mainnet.

Technical kill criterion: unreliable metadata, inability to bind payment safely to entitlement, repeat charges, paid-artifact leakage, or broken Stage A block release. A minor visual defect does not justify weakening these criteria.

## 19. Factory execution instruction

Read this file, `AGENTS.md`, `README.md`, `handoff.md`, `SECURITY.md`, `docs/ROADMAP.md`, and existing exact contracts. Apply the actual factory route from `.grok-stack/runtime/active-route.json` if it has been created in the working environment; do not replace a missing route with invented receipts. Create the change package `engineering/changes/2026-09-24-mezo-evidence/` with F0–F7 tasks, source baseline, ADR, acceptance matrix, and blockers. Start with the safe public copy and baseline verification. Preserve existing changes. Implement only the approved testnet scenario. Do not ask again about product selection or registration. If authorization/merchant address/test MUSD is missing, record the specific blocker and continue independent tasks; do not substitute someone else's credentials or fictitious success. At the end, present verifiable artifacts, not just the word “done.”

## 20. Sources and verification boundaries

Technical sources were accessed on September 24, 2026. External parameters must be reverified in F1; links are not dependency pins.

- **[S1] Mezo, x402 overview:** https://mezo.org/docs/developers/getting-started/musd-payments-x402/ — network/asset, protocol, facilitator, and headers.
- **[S2] Mezo, x402 quickstart:** https://mezo.org/docs/developers/getting-started/musd-payments-x402/x402-quickstart/ — SDK reference, buyer/merchant, test MUSD acquisition, warning about the default PAY_TO. The overview and quickstart differ in their descriptions of mainnet; mainnet is not used in this testnet-only specification.
- **[S3] Hyperliquid, Info endpoint:** https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint — `l2Book`, public request, and level limit.
- **[S4] GitHub, Forks:** https://docs.github.com/en/pull-requests/reference/forks — fork visibility restrictions.
- **[S5] Source code:** https://github.com/Dimkox/multi-exchange-engine/tree/4f6583f8590ea091d8a465de0c607e59bfe611a5 — README, AGENTS, SECURITY, handoff, roadmap, architecture, research index, runtime.py, package.py, vwap.py, and a section of verdict.py were read. This was static inspection, not a full audit or an executed test run.
- **[S6] Organizer email supplied by the owner:** AKINDO / Mezo Buildathon; https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10 and https://luma.com/mezo-buildathon — scope and dates require verification before submission; the owner confirms registration.

All policy thresholds, demo price, internal dates, architectural roles, endpoints, and states in this document are project decisions/requirements, not organizer quotations or claims about an already-implemented product.
