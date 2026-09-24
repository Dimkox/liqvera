# Agent handoff

Updated: 2026-07-28

## Current state

- Local integration branch `main` combines the reducer/reconciliation
  correction from `0453dff` with the credential-free A1/A2 evidence work
  through `549555f`.
- The A2 branch remains public-data and shadow-only: it contains no signer,
  private venue method, order, cancellation, transfer, or live-trading path.

## Update 2026-07-27: A1 Task 7 bounded replay and golden corpus

- `shadow.tape_replay` streams required-LF binary records under the frozen
  256 MiB tape, 8 MiB line, 10,000 case, and eight-worker limits. It keeps no
  full-tape record list, bounds pending futures at twice the worker count, and
  compares evaluator projections in record-index order. Worker exceptions are
  typed `OUTPUT_MISMATCH` failures at their case index.
- The 36-case `shadow-pair-domain-golden-v1` tape uses
  `mee-a1-ndjson/v1`, `pair-domain/v1`, `pair-evaluator/v1`,
  `exact-rational-render28-half-even/v1`, `pair-reasons/v2`,
  `sha256-domain-separated/v1`, `mee-canonical-json/v1`,
  `synthetic-conformance/v1`, and `displayed-taker-entry-cost/v1`.
- The manifest reference is
  `515143b026e084e8fefbecc76f691a960f9cfd19`. The committed external anchor is
  `2b458cc42f6332bbef4def3708da552b175bd2fb1270588f7ec637f987db8d99`
  in `tests/fixtures/shadow-golden-v1.terminal.sha256`; tape bytes are in
  `tests/fixtures/shadow-golden-v1.ndjson`.
- Corpus and mutation coverage includes both directions, every quality and
  shadow reason, exact/+1 thresholds, positive/zero/negative net results,
  target/overshoot/minimum/depth edges, multipliers/lots, $10/$25/$50,
  Standard/Premium, inverse payoff, mapping/cost failures, and candidate
  inclusion/rejection. Final focused tests: 80 passed; full Python suite:
  207 passed.
- CI regenerates from the committed manifest reference into `RUNNER_TEMP` and
  byte-compares both files. `SELF_CONSISTENT` never implies trust;
  `VERIFIED` requires the caller-supplied terminal anchor.
- The evidence boundary is **pair-domain parity** only. No raw venue bytes,
  collector, stateful book reconstruction, expectancy, private transport,
  credential, signer, order, cancellation, database, or deployment path is
  covered or authorized. Next: Go pair-domain conformance; A2 raw-wire capture
  and A3 stateful reconstruction remain separate plans.

### Final whole-branch review fix

- Equal leg `mapping_id` values now fail before quantity and economics with
  `MARKET_MAPPING_REJECTED`.
- Additional costs accept only the immutable exact pairs `GAS` with
  `documented-entry-cost/v1` and `ENTRY_STRESS` with
  `synthetic-entry-stress/v1`; every other pair yields
  `COST_MODEL_INCOMPLETE`.
- Replay passes the caller's exact `TapeLimits` object through case parsing,
  domain reconstruction, and worker evaluation. A later synchronous error
  first resolves only lower-index pending cases, preserving deterministic
  first-error identity without changing normal pending bounds.
- Forbidden-import conformance scans every `shadow/tape_*.py` module and the
  generator. Two fresh 36-case generations byte-matched the committed fixture
  and sidecar. Reference commit, terminal hash, pair-domain claim boundary, and
  single-writer one-directory publication contract remain unchanged.

### Review fix: replay trust boundary and two-target publication

- External anchors must be exact built-in lowercase 64-hex strings and are
  validated before tape reads. Matching uses `hmac.compare_digest`; malformed
  values and overloaded equality cannot cross the trust boundary.
- Strict schema validation now precedes index validation for every recognized
  record. An I/O failure while proving immediate EOF is normalized to
  `TRAILER_NOT_FINAL` at the trailer index.
- The generator uses same-directory staged files, hashed prior-byte backups,
  and a durable journal created before either publication replace. It restores
  both targets on a failed second replace and deterministically recovers an
  interrupted journal at generator start, then cleans transaction artifacts.
- Fixture and sidecar targets must resolve to the same parent. Cross-directory
  targets fail deterministically before target or transaction-artifact
  mutation; multi-directory durability is not claimed.
- Corpus checks require exactly 36 cases, unique tick IDs, and exact normative
  tick-set equality. Fixture bytes and the committed terminal hash did not
  change.

## Update 2026-07-27: A1 Task 6 deterministic hash chain

- `shadow.tape_chain` computes case IDs only from canonical input mappings and
  record hashes from canonical records with the self-hash omitted. Its fixed
  byte domains are `MEE-A1-INPUT-v1\0` and `MEE-A1-RECORD-v1\0`.
- Builders derive all identities; verification recomputes them, rejects index
  gaps, broken predecessors, duplicate case inputs, reordered/omitted/
  duplicated/tampered records, and mismatched trailer count or manifest hash.
- `verify_record_chain` returns a terminal hash that is self-consistent only;
  external anchoring and `VERIFIED` classification are deliberately absent.
  No reader, replay, I/O, network, persistence, credential, collector,
  execution, order, cancellation, or deployment behavior was added.
- TDD: expected import RED; focused suite 10 and full Python suite 168 passed;
  `compileall`, 88-column scan, and diff check passed.

## Update 2026-07-26: A1 Task 5 strict tape schema and projection

- `shadow.tape_schema` freezes manifest/case/trailer records and every amended
  A1 identity/version constant. It rejects unknown or missing fields at every
  nested schema level and preserves Task 4 version-specific error codes.
- `shadow.tape_domain` uses explicit field allowlists for `PairInput` and
  `PairEvaluation`. Canonical Decimal strings cover every financial value;
  levels/additional costs reconstruct as tuples, thresholds remain immutable,
  and `raw_sha256` is projected only as `source_payload_sha256`.
- Expected reasons are ordered `{family, code}` objects. Eligibility is
  explicitly `DISPLAYED_TAKER_ENTRY_ONLY`, missing mapping objects alone may
  be `null`, and the rejection/output nullability matrix is fail closed,
  including complete after-cost economics.
- Case direction byte-matches the derived
  `buy_market.venue->sell_market.venue`; aliases and case folding are absent.
- Verification: expected missing-module RED; focused suite 20 passed; full
  Python suite 150 passed. No reader, hash chain, replay, network, persistence,
  credential, collector, execution, order, cancel, or deployment was added.

## Update 2026-07-26: A1 Task 4 canonical Decimal and JSON codec

- `shadow.tape_codec` is the untrusted-byte boundary shared by later A1 schema
  and replay work. Its Decimal codec uses `as_tuple()` only and round-trips
  exact bounded canonical coefficient/exponent text independently of the
  ambient Decimal context.
- Canonical JSON is compact, ASCII-only, key-sorted, duplicate-aware, and
  rejects floats/constants, unsafe integers, unsupported primitives, BOM,
  invalid UTF-8, embedded line endings, noncanonical bytes, excessive nesting,
  oversized strings/lines, and parser recursion breaches with typed errors.
- The trusted frozen `A1_LIMITS` profile includes 256 MiB tapes, 8 MiB lines,
  10,000 cases, 5,000 levels per side, depth 16, 1,024-byte strings, and at
  most eight replay workers. Limits are caller policy, never tape input.
- The codec receives payload bytes after Task 7 removes the required LF.
  Schema, projection, hash-chain, and evaluator behavior remain unimplemented.
  TDD: expected import RED, 19 focused and 130 full Python tests passed.

## Update 2026-07-26: A1 Task 3 versioned entry-cost evidence

- Normalized pair evaluation consumes only the immutable
  `displayed-taker-entry-cost/v1` model: buy and sell taker evidence is bound
  to its venue and the pair quote currency, with exact quote fee rounding and
  nonfuture SHA-256-backed schedules. Typed additional components use the same
  quote currency; conversions are deliberately unsupported.
- `PairEvaluation` now exposes buy fee, sell fee, their retained total, and
  additional cost. All eligibility arithmetic remains Fraction-exact until the
  established render boundary. Unknown evidence remains `None`, while an
  explicit documented Decimal zero is valid.
- Cost validation occurs after quality, mapping/payoff, quantity, depth, and
  actual-notional gates. Invalid, future, unsupported, or currency-mismatched
  evidence returns `COST_MODEL_INCOMPLETE` with no economics.
- Verification: focused provenance/pair suite 25 passed; full Python suite 111
  passed; `compileall`, changed-Python 88-column scan, and `git diff --check`
  passed. No network, credential, collector, execution, order, cancellation,
  or deployment behavior changed.

## Update 2026-07-26: A1 Task 2 reviewed market mappings and payoff boundary

- `shadow.provenance` provides frozen `MarketMappingEvidence`, explicit
  `MappingDecision`, and `validate_mapping_pair`. Evidence validates exact
  reviewed identity, venue/symbol, multiplier, displayed unit, quantity/price
  rules, minima, SHA, and closed validity interval; it never coerces inputs.
- Pair evaluation runs quality, basic input validation, mapping validation, and
  then the exact `PERPETUAL`/`LINEAR` boundary before quantity, depth, or
  economics. Missing mapping is a normal evaluator rejection, not a schema
  error. `VenueMarket.displayed_size_unit` is mandatory without a default.
- Tests: focused provenance/pair 20 passed; complete Python suite 105 passed.
  This remains credential-free public shadow logic; no collector, network,
  persistence, order, cancellation, execution, or deployment path was added.
  Next: versioned entry-cost evidence.

### Review fix: active market Decimal boundary

- `VenueMarket` now requires exact finite `Decimal` values for contract
  multiplier, quantity step, and minimum notional before positivity. Bool and
  int values cannot compare equal to reviewed evidence.
- Covering domain/provenance/pair suite: 27 passed. `compileall`, changed-file
  88-column scan, and diff check also passed.

## Update 2026-07-26: A1 Task 1 stable reasons and receive-time causality

- Canonical `shadow.reasons` now owns the seven-versioned
  `ShadowRejectCode` contract and its deterministic order; `shadow.quantity`
  keeps a compatible re-export, while pair and VWAP use the canonical import.
- Quality rejects either snapshot received after `evaluated_at_ms` with
  `BOOK_RECEIVED_AFTER_EVALUATION`, accumulating it in enum order with every
  other blocker. Do not require exchange time to be before receive time: no
  shared clock-offset model is proven; preserve future-exchange clock rejection.
- Tests: focused reasons/quality 21 passed; complete Python suite 95 passed;
  `compileall`, 88-column scan, and diff check passed. No external behavior or
  runtime path changed. Next: reviewed linear market mappings/payoff boundary.

## Update 2026-07-26: approved A1 implementation plan

- The approved TDD plan is
  `docs/superpowers/plans/2026-07-26-a1-pair-domain-parity-tape.md`.
- Execute its seven tasks in order and commit each separately. Every task gets
  a fresh implementer plus independent spec and quality review.
- Task 1 is next: centralize stable shadow reasons and reject books whose
  receive timestamp is after the evaluation tick.
- Architecture review corrections are binding: missing mapping is represented
  by `None`, `VenueMarket.displayed_size_unit` has no default, A1 costs accept
  quote currency only, replay workers are capped at eight, and CI regenerates
  from the manifest-pinned evaluator commit before byte-comparing the committed
  fixture.
- A1 stays credential-free and normalized-domain only. Do not add networking,
  persistence, collection, signing, order, cancellation, or deployment paths.

## Update 2026-07-26: Task 2 isolated Decimal rendering context

- `shadow.exact` renders non-terminating Fraction outputs inside an explicit
  copied `Context`: precision 28, `ROUND_HALF_EVEN`, `MIN_EMIN`/`MAX_EMAX`,
  clamp 0, and invalid-operation, division-by-zero, and overflow traps. Ambient
  Decimal settings cannot influence it.
- The regression enables hostile precision, rounding, exponent bounds, clamp,
  and traps around a tiny positive five-thirds times `10^-100` VWAP; rendering
  remains the configured nonzero 28-significant-digit result.
- Verification: quantity 9, VWAP 10, pair 10, full suite 92; `compileall`,
  88-column scan, and `git diff --check` passed.

## Update 2026-07-26: Task 2 exact VWAP and pair economics remediation

- Shared `shadow.exact` is the context-independent Decimal/Fraction boundary.
  It preserves terminating Decimals exactly and fixes non-terminating outputs
  at 28 significant digits with `ROUND_HALF_EVEN` under local fixed precision.
- VWAP and pair economics now use exact Fractions for all financial operations,
  including target/overshoot, gross, fees, net, and divergence. Precision-28
  large-notional regressions are covered without false shadow rejection.

## Update 2026-07-26: Task 2 adversarial arithmetic remediation

- Common quantity no longer depends on ambient Decimal precision: exact
  coefficient/exponent-to-`Fraction` math now covers LCM, ceiling, native
  quantity, and target/overshoot checks; only terminating results return Decimal.
- Both rounded top-price notionals are rechecked against target and overshoot.
  The precision-28 regression uses target `10000000000000000000000000001`.
- VWAP now validates every displayed level before it consumes a prefix, including
  tails that would otherwise be unvisited after an early complete fill.

## Update 2026-07-26: exact paired shadow-entry evaluation

- Added credential-free Task 2 contracts for common canonical quantity,
  authoritative displayed-depth VWAP, and paired entry economics. There is no
  network, credential, signer, account, order, cancellation, or deployment path.
- Arithmetic accepts only finite `Decimal`: common lot is the decimal LCM of
  `quantity_step * contract_multiplier`; requirements round up after target and
  venue minima; depth stays in supplied order and never extrapolates.
- `evaluate_pair` calls quality first, checks book-market venue/symbol plus
  reviewed identity, then uses swept notionals, explicit entry fees, and extra
  cost. Target/overshoot mismatch and non-positive net capture fail closed.
- Verification at this checkpoint: quantity 9, VWAP 9, pair 10, full suite 91;
  `compileall`, 88-column scan, and `git diff --check` passed.
- This is entry-only indicative shadow math, not lifecycle PnL, execution, or
  alpha evidence. Next action: golden-tape serialization and deterministic replay.

## Update 2026-07-26: deterministic public book quality gate

- Added immutable `BookEvidence`, immutable copied `QualityThresholds`, and
  deterministic `BookPairQuality` for credential-free public snapshots.
- Every pair accumulates stable rejection codes in enum order for mismatched
  boot IDs, gaps, inactive connections, stale venue books, source/receive
  skew, clock error, and absolute wall/monotonic drift. Invalid construction,
  missing venue limits, and future source timestamps fail closed.
- P1 regression hardening now requires an actual immutable `OrderBookSnapshot`
  and finite positive `Decimal` price/quantity values in every `BookLevel`.
- Verification: `tests.shadow.test_quality` 18 passed; full Python suite 63
  passed; `compileall`, 88-column production-line scan, and diff check passed.
- The quality gate is before VWAP/economics and adds no network, credential,
  account, signer, execution, cancellation, order, or deployment behavior.
  Next: exact displayed-depth VWAP and paired shadow economics.

## Update 2026-07-26: credential-free public adapter split

- Added `HyperliquidPublicAdapter` and `LighterPublicAdapter` in isolated
  public modules. Their constructors accept only public read transports,
  mapping providers, and receive-time functions; they carry no account, key,
  signer, nonce, send transport, or trading method.
- The public modules import no execution domain. `HyperliquidAdapter` and
  `LighterAdapter` now subclass them and preserve private backward-compatible
  account, order, reconciliation, and fill behavior.
- CI now runs a separate pinned Python 3.12 reference-engine job.
- Verification: boundary suite 3 passed; full suite 45 passed; compileall
  passed with `python -m compileall -q multi_exchange_engine tests`.
- No network client, key use, trading call, or deployment was added. Next:
  exact shadow VWAP and data-quality domain.

## Update 2026-07-26

- Active implementation branch: `feature/python-arbitrage-engine`.
- Binding owner corrections: Python runtime, cross-exchange arbitrage, any
  formally equivalent common asset, Hyperliquid/Lighter first and arbitrary
  DEX/CEX adapters later.
- Decision record:
  `docs/adr/0001-python-universal-arbitrage-core.md`.
- Implemented Python Step 1 under `multi_exchange_engine/domain/market.py`:
  exact-decimal venue constraints and evidence-gated dynamic common-market
  discovery.
- Python Step 2 committed as `151aab7`:
  `multi_exchange_engine/domain/book.py` and
  `multi_exchange_engine/exchange/contracts.py`.
- Python Step 3 committed as `572aba7`.
- Venue price rules now support both a fixed tick and decimal/significant-digit
  constraints; this removes the false fixed-tick assumption for Hyperliquid.
- Python Step 4 added the fixture-only `HyperliquidAdapter` under
  `multi_exchange_engine/exchange/hyperliquid.py`. Its injected transports
  describe official `/info` and unsigned `/exchange` request payloads but make
  no network request or signing call themselves.
- Its dynamic `metaAndAssetCtxs` catalog fails closed on malformed shape or
  context-length mismatch. A mapping provider supplies reviewed economic
  identity, multiplier, and equivalence evidence; no symbol is asset-allowlisted
  or assigned a canonical multiplier from its name.
- `l2Book` maps exact Decimal bid/ask levels and intentionally reports no
  invented sequence. `clearinghouseState`, `frontendOpenOrders`/`orderStatus`,
  and `userFillsByTime` have authoritative private mappings. Reconciliation by
  exact CLOID is incomplete on malformed or unavailable evidence.
- Only a previously owned exact CLOID can be cancelled. API acceptance is not a
  fill; resting, filled, explicit error, malformed, and transport outcomes map
  to accepted, filled, rejected, or unknown respectively.
- Review fixes now use official `cancelByCloid`, leave `unknownOid` incomplete,
  normalize terminal cancel/reject variants, advance only complete fill cursors,
  and reject invalid CLOID/quantity/price before transport.
- Tests: 30/30 pass, plus `compileall`, line-length, and diff checks. Claw has
  Python 3.12.3, Docker 29.6.2, and Compose 5.3.1; branch-level Linux/Docker
  verification is pending. Next: fixture-driven Lighter adapter.
- Python Step 5 adds fixture-only `LighterAdapter` and `LighterBookReducer`,
  pinned to official `lighter-python` v1.1.2 commit
  `6957dd8a1b36894ca9580be0d51de30aeea3bd4a`. Perp metadata discovery derives
  Decimal ticks/minimum quote; reviewed mappings provide economic identity.
- Independent review found seven P1 defects in the first Lighter commit. The
  follow-up now accepts the official `subscribed/order_book` snapshot, verifies
  its market channel, uses the outer millisecond timestamp, and refreshes the
  local receive timestamp on every event. Continuity remains exact
  `begin_nonce == previous nonce`; `offset` is not treated as a sequence.
- Nonces no longer start from zero inside the adapter. An injected serialized
  coordinator supplies the API-key-bound authoritative nonce and receives an
  accepted/rejected/unknown acknowledgement. Signing is a separate injected
  step; its tx hash and exact ownership are retained before `sendTx`.
- `tx` lookup now uses official `by=hash,value=...`. Exact cancellation remains
  limited to the owned client index, including after reconciliation reveals a
  distinct venue order index.
- Authoritative fills use Lighter client IDs, venue IDs, maker/taker fee ticks,
  and millisecond timestamps. Order reconciliation derives average fill price
  from filled quote/base, recognizes partial fills, and no longer rejects a
  valid reduce/close-to-flat fill merely because the final position is flat.
- Both maker minimum quantity and notional are represented. Repeated pagination
  cursors and inconsistent order/trade totals fail closed.
- Tests: 42/42 pass plus `compileall`, 88-column scan, and diff check. No live
  HTTP client, SDK signer, credential, order, or deployment was added.

> Canonical complete handoff: [`../handoff.md`](../handoff.md).
> This file is retained as the historical decision log through 2026-07-21.

Updated: 2026-07-21

## Current state

- Isolated implementation branch/worktree: `stage-a-falsifier` under
  `.worktrees/stage-a-falsifier`; `main` remains the integration branch.
- Stage 0 foundation is implemented and validated.
- Runtime remains strictly `shadow`; live execution is rejected by configuration.
- Task 1 Stage A is implemented through `eb31b39` as a separate credential-free public config/model/capital gate. RED/GREEN ran on Claw in a cached verifier with `--network none`; `gofmt`, `go vet`, and the full Go suite passed. Independent review is clean. PUMP and DOGE Hyperliquid/Lighter mappings remain provisional with empty evidence hashes, so lifecycle admission remains blocked.
- The n8n `2.31.3` checkpoint at `deploy/n8n/stage-a-orchestrator.workflow.json` was imported on Claw as `stageAOrchestrator01` and independently exported/verified with `active=false`, nine allowlisted nodes, and zero credentials. It is control-plane only: five internal GET checks plus a fail-closed revenue/execution gate. The deterministic Go falsifier remains the sole evidence, persistence, and decision authority; Task 9 must add `/v1/business/operator-revenue` before this orchestration can pass or be considered for activation.
- Local ignored `.env` contains venue and Telegram credentials. Secret values are not tracked.
- Lighter account association and dedicated API key index 4 were verified previously through the mainnet read API.

## Reducer and reconciliation correction branch

This separate Go branch reimplements the verified reducer/reconciliation findings from the 2026-07-27 external cross-check. External commit `692bcdb` and the downloaded ZIP trees were not applied or copied.

- A pending second-leg submission preserves aggregate `partially_filled`; only a submission from `reserved` advances the group to `submitting`.
- Positive cumulative-fill replay is state-aware: consistent `open`/`partial`, filled-terminal, and partial-cancel evidence is idempotent, while `submitted` with a stored positive fill, zero-fill, regressive, overfill, rejected, unknown, and other state-contradictory evidence fails closed.
- A first acknowledgement after an early partial or full fill must carry the group-owned client order ID before the reducer attaches a venue order ID. Exact duplicate IDs are no-ops and conflicting IDs are rejected.
- Open-order reconciliation now matches tenant, account, venue, client order ID, instrument, side, and exact total base quantity; only `open` and `partial` statuses are adoptable; both fill quantities are bounded and must agree exactly.
- The restart regression test serializes and restores the pure `Group` domain state before replaying duplicate and out-of-order events. It does not establish durable event-journal or persistence E2E behavior.

Go is not installed in the current Windows shell. The RED and GREEN test commands both stopped because `go` was not recognized, so `gofmt`, `go vet ./...`, `go test ./...`, and `go test -race ./...` remain unverified toolchain gates for this branch. Static review and `git diff --check` are the only local verification available here.

## Product decision

The user selected **Telegram Mini App beta** as the MVP boundary.

This is not yet an approved implementation design. It must be decomposed before coding because it contains three independently testable contours:

1. Read-only cross-venue data and shadow opportunity engine.
2. Telegram Mini App control-plane experience and reporting.
3. Future execution canary, which remains outside the beta unless separately approved.

## Required next action

Do not start Task 2 until the operator-revenue contract is resolved. The owner
clarified that earning commission is the primary business criterion; the
current Stage A specification measures trader-side economics but does not yet
model operator revenue. Record the exact source and rate contract (venue
referral/builder rebate or an owner-charged fee), turnover basis, payouts, and
infrastructure cost, then add an explicit operator-revenue `KILL` gate. Keep
live trading out of scope.

The owner selected both revenue channels: venue builder/referral cash plus an
owner-charged turnover fee. Current official terms make venue revenue
unproven: Hyperliquid builder fees require at least `$100` builder-account
value and explicit user approval; creating a Hyperliquid referral code requires
`$10,000` prior volume; Lighter documents referral/points APIs but no cash
referral rate, while Standard trading fees are zero. Do not count points or an
undocumented payout as revenue. The remaining blocking input is the exact
owner-fee rate and collection mechanism.

## Parallel-agent findings

On 2026-07-21 three read-only agents reviewed architecture, trader/risk evidence, and Product/UX scope.

Consensus:

- Reuse the Hyperliquid bot as a source of safety invariants, fixtures, and acceptance scenarios, not as a service copied into the new runtime.
- Port stable fill identity, event deduplication, fill watermarks, causal snapshot metadata, deterministic client order IDs, exact-order ownership, fail-closed unknown outcomes, and restart/cancel-fill-race tests.
- Reject the legacy Python live monoliths, n8n/cron as a trading or market-data plane, embedded SQL, `float` price/size boundaries, broad cancel semantics, DOGE grid constants, and candle-touch replay assumptions. n8n is permitted only as the inactive GET-only Stage A control plane described above.
- First vertical slice: Hyperliquid + Lighter public read-only books, fixed-point normalization, persisted observations, executable VWAP/cost calculation, shadow opportunity lifecycle, read-only API, and Mini App projection.
- Mini App must label results as indicative shadow candidates or market divergence, never as actionable trades, real P&L, buy/sell advice, or guaranteed profit.
- Live execution, private account streams, user trading keys, billing, referrals, deposits, and strategy configuration remain non-goals for this beta.

Open product choice:

1. Reuse ExtendedBoost almost entirely — fastest UI work, highest conceptual and data-model coupling.
2. Build a separate thin Mini App while reusing Telegram shell/UI primitives — recommended balance.
3. Build an internal single-screen dashboard — fastest data validation, weak commercial-product validation.

Decision recorded 2026-07-21:

- Selected approach: **3 — internal single-screen dashboard**.
- Primary venues: **Hyperliquid and Lighter only**.
- The dashboard validates market-data quality, depth-adjusted indicative shadow calculations, candidate lifecycle, and operational health for an internal operator.
- Executable VWAP is calculated for selectable shadow notional presets: **$100, $500, and $1,000**.
- External-user onboarding, billing, tenant switching, account connection, and live execution remain outside this MVP.

Adversarial trader/risk review recorded 2026-07-21 — **APPROVE WITH CHANGES**:

- Public L2 output must be labelled `depth-adjusted indicative shadow candidate`, never executable/actionable opportunity or paper PnL.
- Each preset is one target notional converted to a canonical base quantity; actual rounded notionals and quantity mismatch are shown for both legs, and material mismatch fails closed.
- Candidate creation requires formal instrument equivalence, continuous valid books, full observed depth without extrapolation, explicit observation timestamps, book-age and cross-venue-skew gates. Initial conservative gates are 500 ms maximum venue age and 250 ms maximum cross-venue skew, subject to measured calibration.
- Economics are separated into entry edge, versioned entry+exit fee/stress scenario, optional funding scenario with explicit horizon, and closed shadow lifecycle result. Forecast funding is never treated as settled income.
- The first shadow model is taker/IOC-only. Maker fills, queue probability, post-only assumptions, trade CTAs, and live-order semantics are excluded.
- A candidate must remain positive in USD and above a conservative stressed bps floor; `> 0` alone is insufficient. Start with a 10 bps experimental floor and expose p95/p99 stress assumptions.
- Permanent no-execution is a CI-enforced invariant: GET-only shadow API, no signing/trading SDK, no private-key environment contract, no live mode, append-only versioned evidence.
- Until 7–14 days and at least 100 closed paired shadow lifecycles pass deterministic and data-quality gates, the UI says `market divergence`, `EXPERIMENTAL`, `NO EXECUTION`, and `NOT A RECOMMENDATION` rather than `opportunity`.

Second, deliberately adversarial trader/risk review recorded 2026-07-21 — **NARROW; default outcome KILL**:

- Stop treating the Mini App as an MVP. Run a 14-day falsification experiment on Hyperliquid↔Lighter public data first; do not build Telegram, execution, billing, multi-tenancy, RFQ, or private-account paths during it.
- There is no demonstrated user problem, willingness to pay, retention, or proof that the dashboard changes a decision. The current internal dashboard is a research instrument, not product validation.
- Public-book time asymmetry, fill uncertainty, round-trip costs, legging risk, basis exit, funding forecast error, separate collateral, and operational overhead can erase a small apparent edge. `$100` is research-only; `$500` is unlikely to justify operations; `$1,000` is the first preset worth measuring but still unproven.
- The old Hyperliquid bot contributes safety/reconciliation invariants and tests only. Its strategy, replay results, UI activity, and one small profitable cycle are not evidence of positive expectancy.
- Kill the project if any agreed gate fails after 7–14 full days and at least 100 independent closed taker-only shadow lifecycles: lower 95% CI of net expectancy is non-positive; full fees/measured latency/entry+exit erase the result; median divergence lifetime is below p95 executable delay; the result requires maker fills, forecast funding, zero-fee-only assumptions, or omitted exit cost; continuous valid coverage is below 99.5%; stale/gapped/misaligned books materially drive candidates; returns are concentrated in one market/day; 10 bps or 5-second stress erases expectancy; presets fail quantity/depth/minimum gates; or projected absolute income at `$1,000` misses the owner's predeclared floor.
- Two-week sequence: freeze formulas and kill criteria; collect immutable public books/funding/trades; run causal taker-only entry+exit replay; stress Standard/Premium fee scenarios, latency and concentration; publish one go/kill report.
- Pending owner decision: choose a falsifiable research experiment with a real obligation to kill on failure, or product development before economic proof. The trader verdict for the second choice is KILL.

Owner decision recorded 2026-07-21:

- Selected the **14-day falsification experiment**. Product implementation stays paused until its go/kill report.
- User reported approximately **$20 on Hyperliquid and $3+ on Lighter**. These balances are contextual only and are not authorized for use.
- The smaller Lighter balance constrains any real paired position and is insufficient evidence of deployable `$100/$500/$1,000` presets. The experiment therefore remains public-data, credential-free, and shadow-only.
- `$100/$500/$1,000` remain normalized research notionals for depth/cost comparison, not live capital or an execution instruction.

Public API and capital check recorded 2026-07-21:

- The selected 14-day experiment requires **$0 exchange capital** and no private credentials. Hyperliquid exposes public `candleSnapshot`/candle WebSocket data; Lighter exposes public `GET /api/v1/candles`. Candles are secondary regime/context evidence, not a substitute for L2 executable-depth evidence.
- Hyperliquid's official API documents a $10 minimum perp order value. A live public Lighter `orderBooks?filter=perp` read reported `min_quote_amount=10` for sampled BTC and ETH on this date; this was an endpoint check only, not instrument selection.
- The experiment instrument universe remains unselected. BTC and ETH were not proposed or approved by the owner.
- Legacy context: the main live Hyperliquid bot traded DOGE perpetual; HTX DOGE was reference-only, and kSHIB belonged to simulation/research. This does not automatically approve DOGE for the new experiment, but it is the existing strategy hypothesis that must be evaluated first if the owner confirms it.
- A live public Lighter metadata read confirmed a DOGE perpetual market (`market_id=3`, `min_quote_amount=10`) on this date. This establishes venue availability only; owner selection is still pending.
- The reported `$20` Hyperliquid and `$3+` Lighter balances do not support a meaningful paired live validation. Leverage may make a minimum-size order technically possible, but it does not validate the `$100/$500/$1,000` profiles and adds liquidation/legging fragility.
- Do not request or add funds for the public-data experiment. Any later live canary requires a separate explicit owner authorization and budget decision after a positive go report.

Variational observer scope recorded 2026-07-21:

- Add Variational to the 14-day experiment only as a secondary, read-only market-discovery and reference-statistics witness. Hyperliquid and Lighter remain the primary DEX pair; Variational is neither an execution adapter nor a third executable leg.
- Variational's documented public quotes may be cached for up to 600 seconds. They must never enter executable VWAP, fill, or PnL calculations. Persist `quotes.updated_at` and observation time with every sample, and reject stale reference samples from cross-venue comparisons.
- A credential-free public snapshot at `2026-07-21T00:05:19Z` found three normalized micro-price candidates common to all three venues: Hyperliquid `PUMP` / Lighter `PUMP` / Variational `PUMPFUN`, `kBONK` / `1000BONK`, and `kPEPE` / `1000PEPE`. Symbol matching is provisional until contract and payoff equivalence are formally verified.
- In that snapshot, Variational reported 24-hour volume of about `$2.067M` for `PUMPFUN`, `$1.103M` for `1000BONK`, and `$0.275M` for `1000PEPE`; quote ages were 74.5, 89.5, and 74.4 seconds respectively. Across the three venues, the minimum reported 24-hour volume was about `$2.041M`, `$1.103M`, and `$0.275M` respectively, making PUMP the current observation leader, not an approved trading instrument or a signal.
- The exact official `LILPEPE` contract was absent from Hyperliquid, Lighter, and Variational. It is not a tradable experiment candidate.

Five-day Stage A decision recorded 2026-07-21:

- The owner shortened the first evidence window to five complete UTC data days. Stage A may conclude only `KILL` or `EXTEND`; it can never produce `GO`, live authorization, or a product release.
- Target-user capital is now `$10` total, notionally `$5` per primary venue. Research notionals are `$10/$25/$50` per leg, replacing the earlier `$100/$500/$1,000` product profiles.
- `$10` per leg at exactly `2x` consumes the complete `$5` venue allocation before fees or reserve and is therefore `boundary_unproven`, not feasible. `$25/$50` are stress diagnostics and cannot rescue a failing `$10` profile.
- The initial instrument allowlist is limited to provisional PUMP and DOGE mappings. PUMP is the micro-price candidate; DOGE is the legacy control. No lifecycle is admitted until authoritative contract and oracle equivalence is recorded.
- The experiment specification is `docs/five-day-stage-a-spec.md`. It freezes the taker-only lifecycle, capital, latency, stress, data-quality, statistics, persistence, API, and no-execution CI gates.
- Future target regions are Bangladesh, India, the Philippines, Nigeria, and Pakistan. Expected bot-farm/Sybil traffic belongs to a future threat model only; economics depending on wash volume, referral abuse, multi-account farming, or control evasion are an automatic product `KILL`.

Stage A implementation-plan checkpoint recorded 2026-07-21:

- The task-by-task TDD plan is `docs/superpowers/plans/2026-07-21-five-day-stage-a.md`. It contains ten independently reviewable tasks from the strict public configuration/capital gate through Claw warm-up and the exact five-day clock gate.
- Network dependencies are limited to `github.com/coder/websocket v1.8.15` and `github.com/jackc/pgx/v5 v5.10.0`; no venue trading SDK is allowed.
- Go is not installed in the current Windows shell. This is an environment fact, not a project failure; implementation verification must use the pinned Docker builder or Claw.
- The repository is a normal `main` checkout rather than an isolated worktree. Before production-code execution, create an isolated Stage A worktree/branch after owner consent, then use subagent-driven TDD and independent task reviews.

Claw container-network invariant recorded 2026-07-21:

- Stage A containers must not attempt direct outbound Internet access. They must reuse the existing `/home/operator/app-stack` proxy/network contract read-only, fail closed if it is absent, and must not modify `app-stack`, its dirty `glider.conf`, containers, or files. Credentials must not be copied into the project or committed.

## Continuity requirement

Every significant completed step must end in a verified Git commit that also updates this handoff when project state changes materially.

## Trusted self-hosted PR verification gate — 2026-08-09

- Added a bootstrap-only `repository_dispatch` gate with the exact
  `a2-pr-verification` event type for an operator-supplied open PR number and
  exact lowercase head SHA. GitHub therefore loads the gate definition only
  from the default branch; a PR ref cannot replace its own validation guards.
  The job also rejects dispatches whose authenticated actor is not the
  repository owner before allocating the persistent Claw runner.
- The gate validates the PR through GitHub before checkout: base `main`, same
  repository, open state, and exact head SHA. It then checks out that SHA without
  persisted credentials and runs the pinned PostgreSQL 16.11/17.7 A2 test matrix
  in a unique temporary virtual environment.
- The workflow is verification-only. It has no PR/push trigger, write or OIDC
  permission, Docker build, scanner, candidate, promotion, registry, deployment,
  or app-stack path. Evidence is non-secret, retained for 14 days, and temporary
  files are removed on every outcome.
- This commit only defines and locally verifies the gate. It does not push,
  dispatch, merge, promote, or deploy anything.
- PowerShell invocation after the trusted workflow reaches the default branch:

  ```powershell
  & 'C:\Program Files\GitHub CLI\gh.exe' api --method POST 'repos/Dimkox/multi-exchange-engine/dispatches' -f 'event_type=a2-pr-verification' -F 'client_payload[pr_number]=10' -f 'client_payload[target_sha]=<lowercase-40-hex-pr-head-sha>'
  ```

- Live run `31320046383` proved that the trusted pre-check executes before any
  PR checkout, but the first revision called an unavailable `python` command on
  Claw and exited `127`. The pre-check now uses the host's verified `python3`;
  no PR code ran during the failed attempt.
- Live run `31320350368` then passed the trusted pre-check and exact checkout,
  but exposed the same unavailable bare command in venv creation. All host
  interpreter entry points in this gate now use `python3`; venv-contained
  commands continue to use their exact `${venv_dir}/bin/python` path.
- Build run `31320762359` passed both PostgreSQL verification matrices, then
  failed closed in the Docker verify stage because the new trusted workflow was
  absent from the allowlisted build context. The verify stage and `.dockerignore`
  now include that single workflow; the production stage remains unchanged.

## M0 graph-authority final-review correction — 2026-08-11

- The six repository manifests now use only the closed specification node and
  edge vocabularies. Product traceability includes Actor, Outcome, Approval,
  Acceptance/Kill criterion, Metric, Contract, SourceModule, DataFlow, test,
  gate, artifact, evidence, and rollback; paths cannot cross another
  Requirement and negative conflict relations never establish positive proof.
- The precommit checker deterministically inventories 164 Git-tracked
  runtime/source/workflow/config/entrypoint artifacts. Exactly 142 are bound to
  graph nodes and 22 test/research/legacy-n8n artifacts have exact, reasoned
  exclusions. A newly tracked in-scope artifact is blocking until declared.
- M0 does not claim `REALIZED`, a trusted receipt, Claw execution, build,
  release, promotion, or deployment. `REALIZED` is always rejected in M0;
  lifecycle/phase receipt declarations are mandatory when due, and prospective
  receipts do not satisfy later-phase gates.
- The three printed precommit conflicts remain declared and are waived only by
  their full immutable node identities. Merge and later phases remain blocking.
  Go remains `TEST_ONLY_EXECUTABLE_SPEC`; the execution artifact remains
  inactive and `QUARANTINED`.

## M0 graph-authority third final-review correction — 2026-08-11

- The deterministic Git-index inventory now covers 356 relevant tracked paths
  across code, tests, workflows, configuration, documentation, packaging,
  migrations, fixture data, PowerShell, and research. It has 292 exact typed
  bindings and 64 exact `RESEARCH_ONLY` exclusions bound to an active ADR.
  Runtime/workflow/deploy/package/PowerShell classes cannot be excluded.
  Root `README.md` and `SECURITY.md` have explicit documentation bindings to
  the active graph-authority ADR.
- Private/execution sources, the promotion script, inactive n8n workflow, and
  mutation PowerShell remain bound only to the inactive `QUARANTINED` execution
  artifact. `Dockerfile.a2` is an active packaging artifact but is explicitly
  blocked by `conflict:a2-private-production-image`; the retained promotion
  path is blocked separately. The exact precommit waiver reports five declared
  conflicts and never authorizes merge or a public/read-only claim.
- Evidence derivation is a DAG, semantic replacement has one successor,
  phase-policy times are monotonic, and merge or later phases trust time only
  when it came from the complete six-file `architecture/` directory tracked at
  the actual Git top level; copied manifest sets remain untrusted. Single-file
  graphs are available only through explicit fixture mode/path.
- Local diagnostics passed the third-wave regressions 43/43, graph tests
  157/157, and deployment-contract tests 11/11. Precommit reports exactly five
  allowlisted conflicts; merge remains fail-closed. The full pytest collection
  still has the same nine pre-existing root/src namespace and missing-Pydantic
  environment errors.
- No trusted receipt, Claw run, build, release, promotion, deployment, private
  API, n8n activation, or live action was produced by this correction.
