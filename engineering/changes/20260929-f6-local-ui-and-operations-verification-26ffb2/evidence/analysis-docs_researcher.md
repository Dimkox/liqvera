# F6 documentation and acceptance analysis

Date: 2026-09-29
Route: `26ffb293d4ff`
Role: read-only documentation/acceptance analysis
Method: repository inspection only; no web request, wallet, RPC, facilitator,
transfer, live capture, deployment, release, or shared environment was used.

## Executive finding

The repository contains a substantial F6 implementation surface, but the
canonical records correctly leave F6 acceptance open. The browser implements
the intended recovery decisions in source, and Compose/runbooks describe a
plausible isolated deployment, yet there is currently no browser test harness
or retained container execution proving those claims. Accordingly A26 and A30
must remain `NOT_RUN` until this route produces deterministic browser and
disposable-container evidence. The local route may prove the UI behavior with
an injected-wallet double and a mock HTTP service; it cannot prove a real x402
payment because the reviewed browser adapter is deliberately unregistered and
payment readiness remains externally blocked.

## Canonical obligations

- The canonical TZ requires a 256-bit capability in `sessionStorage`, reload
  recovery, payer binding, no second payment after an uncertain outcome, and
  authorized report/evidence reuse (`docs/planning/LIQVERA_FACTORY_TZ.md:155-171,
  218-220`).
- The UI must show permanent testnet/read-only/data-mode boundaries and cover
  wallet cancel, account switch, wrong chain, reload, recovery, receipt/report,
  and bundle download without offering a second charge
  (`docs/planning/LIQVERA_FACTORY_TZ.md:236-244`).
- The operations boundary requires exact CORS/CSP, egress restriction,
  non-root/read-only containers, bounded resources, no public artifact mount,
  safe logs, and useful metrics (`docs/planning/LIQVERA_FACTORY_TZ.md:246-256`).
- A26 specifically requires analyzer/report processing without external egress
  and capture isolation from payment/database state. A30 specifically requires
  cancel, switch, reload, and wrong-chain behavior with no implicit payment
  (`docs/planning/LIQVERA_FACTORY_TZ.md:289-293`).
- F6's exit artifact is a browser flow plus clean installation, not source
  presence alone (`docs/planning/LIQVERA_FACTORY_TZ.md:299-310`).

## Truthful local claims already supported by source

### Browser source

- `session.ts` creates 32 random bytes, stores the URL-safe capability and a
  validated flow record in `sessionStorage`, including the idempotency key,
  request/quote IDs, payer and `paymentGuard`.
- `main.ts` disables quote creation unless capabilities say live-public and
  payment-ready, an account is connected on chain 31611, the x402 adapter is
  installed, and no saved flow is active. It renders an explicit wrong-network
  message and exposes a switch action.
- Account and chain change listeners refresh wallet state. A changed account is
  warned and cannot pay the old payer-bound quote.
- Reload recovery reuses the saved capability, idempotency key, request ID and
  quote ID. If a response was lost after create, it resends the exact create
  request with the same idempotency key rather than creating a new logical
  request.
- The source sets `paymentGuard` before invoking the payment adapter. Uncertain,
  pending and manual-review states hide/lock the new-report path, poll boundedly,
  and say not to pay again. Cancellation clears the guard only when a fresh
  quote read proves the quote is still `READY`; otherwise it remains uncertain.
- Paid recovery calls the ordinary entitled report GET, validates the receipt
  against the quote, and the evidence download uses the same entitlement.
- Product copy is English and prominently says Mezo Testnet and read-only/no
  execution. These are static source observations, not browser acceptance.

### Operations source

- Compose defines separate fixture/live services and profiles, internal
  `edge`, `gateway_db`, `gateway_report`, and `capture_report` networks, and
  separate egress networks. Capture has no database/payment network; report
  has no egress network; only gateway/migrate join the database network.
- Only the edge publishes ports. The web container has no artifact volume;
  gateway mounts artifacts read-only. Fixture edge binds to
  `127.0.0.1:8080`; live edge is distinct.
- Service definitions use numeric non-root users, read-only root filesystems,
  dropped capabilities, `no-new-privileges`, PID/CPU/memory limits, bounded
  tmpfs, healthchecks, and secret files rather than credential environment
  values.
- Fixture gateway sets `SOURCE_MODE=fixture` and blank `PAY_TO`, which is a
  fail-closed configuration. The runbooks explicitly forbid presenting the
  fixture as live/payment evidence and distinguish health from readiness.
- Runbooks cover startup/shutdown, recovery, backup/restore, incidents and
  observability with explicit no-resettlement/no-second-charge guidance.
  These remain design/configuration claims until exercised.

## Gaps and likely repair scope

### P0 — A30 has no executable browser evidence

`apps/mezo-web/package.json` has only dev/build/typecheck/preview scripts and
no test dependency, browser runner, test script, or test files. The legacy
task record is therefore accurate: F6 source exists, but cancel, wrong network,
wallet switch, reload and recovery are untested
(`engineering/changes/2026-09-24-mezo-evidence/tasks.md:122-137`).

Required local evidence should use a deterministic browser runner with:

1. an injected EIP-1193 double for `eth_accounts`, `eth_requestAccounts`,
   `eth_chainId`, `wallet_switchEthereumChain`, `accountsChanged`,
   `chainChanged`, and code `4001` cancellation;
2. a same-origin HTTP fake for capabilities, create/status/quote/report and
   evidence endpoints;
3. a reviewed-adapter test double registered only in the test bundle;
4. assertions over `sessionStorage`, exact request count/idempotency key,
   displayed warnings, disabled controls, reload recovery, payer switching,
   bounded polling, and zero extra adapter/settlement invocations.

The browser suite should cover at least:

- wrong-chain initial state and successful switch to chain 31611;
- account switch after quote: old quote remains bound and payment is disabled;
- cancel proven before submission: quote remains `READY`, guard clears, and
  zero settlement is recorded;
- ambiguous/error cancellation: guard becomes/stays uncertain and no second
  payment control appears;
- reload before request response, during PREPARING, with READY quote, during
  uncertain settlement, and after PAID delivery;
- response loss after quote create: same capability/body/idempotency key and
  one logical quote;
- paid report and evidence reuse with zero adapter/settlement calls;
- fixture capabilities: no payable UI even if a mock wallet is present.

### P0 — the real browser payment sequence is intentionally unavailable

`apps/mezo-web/src/x402.ts` initializes its reviewed adapter to `null`; no
production module registers one. Thus `x402Available()` is false in the shipped
application and the wallet-payment button cannot be used. This is consistent
with current blockers and safe for this route, but it means source/browser
tests can establish recovery behavior only through a test adapter. They must
not claim the canonical real-wallet sequence, A13/A14, SDK compatibility, or
testnet payment. A production adapter requires separate exact SDK/API and
payment-safety review.

### P0 — A26 still needs static resolution plus disposable runtime proof

The Compose topology appears aligned with A26, but static YAML does not prove
resolved profiles or runtime isolation. Required evidence is:

- `docker compose config` for fixture and live with sanitized dummy secret
  files/values, asserting service membership, internal flags, mounts, users,
  limits, healthchecks and published ports;
- a disposable fixture project with unique project name and temporary secret
  files/volumes;
- healthy process checks plus `/healthz`, `/readyz`, and capabilities through
  the fixture edge;
- negative connectivity checks proving report cannot egress, capture cannot
  reach PostgreSQL/gateway payment surfaces, and the web service cannot read
  artifact/database volumes;
- teardown/absence proof without touching shared volumes or environments.

Do not relabel A26 `PASS` from config inspection alone. If local Docker is
unavailable, retain the static result and record the runtime portion as
`NOT_RUN`, not `BLOCKED_EXTERNAL`.

### P1 — runbook statements need execution reconciliation

The runbook header still says the stack has never been built or started. After
successful local disposable execution, update it narrowly to identify what
was exercised and what remains unverified. Keep live/testnet instructions
conditional. Validate all command lines against the actual working directory,
profile resolution, required four secret files, health endpoints and cleanup.

### P1 — README/handoff status is stale

README currently says F5 verification/review remains pending while handoff
records F5 review PASS. The F6 change should reconcile current status without
promoting frozen vectors: all 156 remain `NOT_RUN`, A13/A14 remain externally
blocked, A26/A30 change only if their exact evidence is produced, and no
deployment/release/payment claim is permitted.

### P1 — observability acceptance must distinguish docs from runtime

The observability runbook names the required metrics and alerts, but this
analysis found no retained runtime scrape/dashboard/log-redaction evidence for
F6. Static configuration can validate routing and safe labels; runtime claims
need local requests and sanitized outputs. Do not infer payment readiness from
container health.

## Acceptance-matrix ruling

| Item | Current defensible status | What can change in this route |
| --- | --- | --- |
| A26 | `NOT_RUN` | May become PASS only with resolved-config assertions plus disposable runtime isolation/health evidence. |
| A30 | `NOT_RUN` | May become PASS for deterministic local browser recovery only if the matrix clearly scopes the evidence; it cannot imply a real testnet payment. |
| A13–A14 | `BLOCKED_EXTERNAL` | No change: test adapter/container fixture evidence is not a real transfer or repeat-access payment proof. |
| A28 | `NOT_RUN` | A disposable local build can add partial F6 evidence, but a full clean-machine README acceptance remains a separate F7 claim unless run exactly. |
| Other frozen vectors | unchanged | No browser/config test should relabel unrelated vectors. |

## Browser/config evidence boundaries

Browser evidence may prove UI state, request construction, persistent session
recovery and absence of a second adapter invocation. It cannot prove wallet
signature semantics, facilitator behavior, chain receipt finality or transfer
uniqueness. Static Compose evidence may prove declared topology and limits;
only a disposable runtime can prove instantiated connectivity and health. Host
firewall destination allowlists remain an operator requirement because the
runbook correctly states that Compose bridge networks do not implement them.

## Recommended bounded implementation order

1. Freeze typed F6 criteria around A26/A30 and the explicit non-claims above.
2. Add the deterministic browser harness and failing A30 regressions first.
3. Apply only defects exposed by those tests; retain the null production x402
   adapter and fail-closed fixture behavior.
4. Add static Compose assertions, then use a uniquely named disposable fixture
   project if the local Docker environment supports it.
5. Reconcile runbooks, README, handoff and the acceptance matrix to exact
   evidence, leaving every unexecuted/live requirement unchanged.

No data migration, shared database, real wallet, RPC, facilitator, transfer,
live capture, deployment, release, or external network evidence is required or
authorized for this F6 route.
