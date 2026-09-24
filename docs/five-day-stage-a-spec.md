# Five-day Stage A public-data falsification specification

Status: approved research boundary, implementation not started.

## Decision

Run a five-complete-UTC-day, credential-free falsification screen for a
Hyperliquid/Lighter paired perpetual hypothesis. Variational is a secondary
read-only observer. The experiment does not predict token direction, simulate
maker fills, place orders, use balances, or validate a product.

Stage A has only two terminal decisions:

- `KILL`: capital, contract mapping, data quality, or modeled economics fails.
- `EXTEND`: all Stage A gates pass strongly enough to justify a longer shadow
  study.

Five days can never produce `GO`, authorize live trading, or release a Telegram
Mini App. High altcoin volatility increases observations; it does not create
independent market regimes.

## Hypothesis

For a formally equivalent perpetual contract on Hyperliquid and Lighter, a
taker-only paired lifecycle at `$10` per leg can retain positive modeled net
capture after causal delay, complete entry and exit depth, actual fee profiles,
a 10 bps adverse-price stress, and a five-second delay stress.

The measured object is a `hypothetical_shadow_lifecycle`. It is not a fill,
trade recommendation, PnL, return, profit, or evidence that funds can be
deployed safely.

## Capital and research profiles

The target-user context is `$10` total capital, notionally split as `$5` on
Hyperliquid and `$5` on Lighter. No funds are authorized for Stage A.

Research profiles are `$10`, `$25`, and `$50` notional per leg:

| Per-leg notional | Full entry+exit turnover | Turnover / `$10` capital | Status |
|---:|---:|---:|---|
| `$10` | `$40` | `4x` | product-relevant boundary |
| `$25` | `$100` | `10x` | stress diagnostic |
| `$50` | `$200` | `20x` | stress diagnostic |

At `$5` collateral per venue, a `$10` leg consumes the entire nominal capacity
at exactly `2x` before fees, reserves, funding, or adverse movement. Therefore
the `$10` profile starts as `boundary_unproven`, never `feasible`. `$25` and
`$50` cannot rescue a failing `$10` profile.

For every profile, persist:

- required margin and implied leverage per venue;
- entry fee, reserved exit fee, and stress reserve;
- remaining margin headroom;
- venue minimum-order result;
- gross lifecycle turnover and its multiple of total capital;
- withdrawal and rebalancing friction, with unknown values represented as
  `null`, never zero.

The conservative feasibility inequality is evaluated independently per venue:

```text
notional / leverage + entry_fee + exit_fee + stress_reserve <= 5 USDC
```

If `$10` cannot satisfy the inequality and both venue minimums, the capital
hypothesis is `KILL` even when the market-data experiment continues for
research.

## Instrument gate

Stage A admits at most two primary mappings:

1. Hyperliquid `PUMP` / Lighter `PUMP` as the micro-price candidate.
2. Hyperliquid `DOGE` / Lighter `DOGE` as the legacy control.

Both begin `provisional`. Collection may observe them, but lifecycle economics
remain blocked until the mapping record contains authoritative evidence for:

- venue and immutable market identifier;
- instrument type and underlying/oracle definition;
- displayed-size units and contract multiplier;
- linear or inverse payoff;
- quote/index currency and collateral;
- funding interval;
- tick size, lot size, minimum base, and minimum quote notional;
- `valid_from`, evidence URL/hash, and reviewer decision.

Ticker equality and correlated prices are corroboration, not proof.
`kBONK/1000BONK` and `kPEPE/1000PEPE` remain discovery candidates outside the
first two-mapping run. Variational `PUMPFUN` is an observer alias until proven.
The official `LILPEPE` contract is excluded because it is absent from the three
venues.

## Venue roles and feed semantics

### Hyperliquid

- Primary public L2 source: `l2Book` WebSocket snapshots.
- A message is a complete book snapshot with venue time and no continuity
  sequence. The collector must not fabricate a sequence.
- Disconnect, non-monotonic source time, invalid/crossed book, or more than two
  seconds of receive silence opens a gap.
- Only a new valid complete snapshot closes the gap.

### Lighter

- Primary public L2 source: `order_book/{market_index}`.
- Subscription begins with a full snapshot and then 50 ms delta batches.
- Continuity requires `current.begin_nonce == previous.nonce`.
- `offset` must increase within a connection but is not required to be
  continuous and is not stable across reconnects.
- On a nonce mismatch, discard deltas and resubscribe for a fresh snapshot.

### Variational

- Reference observer only, sampled every 60 seconds through public
  `GET /metadata/stats`.
- Persist source `quotes.updated_at` and local receive time.
- Mark samples older than 600 seconds stale.
- Variational values never enter primary quantity, VWAP, fee, fill, lifecycle,
  capital, or acceptance calculations.

## Clock and data-quality contract

One process hosts both primary collectors. Persist UTC wall time, monotonic
receive offset, process boot ID, connection epoch, source time, and raw payload
hash. Never pair observations across process boot epochs.

Initial hard gates:

- Hyperliquid book age `<= 750 ms`;
- Lighter book age `<= 200 ms`;
- cross-venue source/receive-time skew `<= 250 ms`;
- recorder clock error `<= 25 ms`;
- if wall-clock delta and monotonic delta differ by more than `50 ms`, terminate
  the epoch and reopen with a gap;
- complete, sorted, positive, non-crossed books only;
- no open continuity gap;
- full displayed depth for the required quantity; no extrapolation.

Coverage is measured on one-second UTC evaluation ticks. `EXTEND` requires at
least `99.5%` valid wall-clock coverage for every admitted venue/mapping.
Stale, gapped, misaligned, incomplete, or provisionally mapped observations
produce persisted rejections, not lifecycles.

## Quantity and VWAP rule

For each direction and research notional:

1. Normalize both venue contracts into canonical underlying units.
2. Find the smallest quantity valid on both venues that meets the research
   notional and both minimum-order constraints.
3. Round upward to a common valid lot.
4. Reject if normalized quantity mismatch exceeds one common lot, either leg
   exceeds the preset by more than `2%`, or displayed depth is insufficient.
5. Sweep asks for the buy leg and bids for the sell leg. Persist VWAP, worst
   consumed price, actual notional, and consumed level count.

The normalized pair reference uses
`exact-rational-render28-half-even/v1`: eligibility comparisons remain exact
and only non-terminating display outputs round to 28 significant digits with
ROUND_HALF_EVEN. Tape JSON uses canonical Decimal strings. A production
fixed-point optimization is accepted only after byte-exact parity with the
reference corpus.

## Lifecycle rule

Evaluate both directions for every `$10/$25/$50` profile.

1. A provisional trigger requires delayed taker VWAP raw divergence of at
   least `19 bps` for Lighter Standard or `24.6 bps` for Lighter Premium.
2. Lighter entry evidence is the first valid book after its documented 300 ms
   Standard taker delay plus measured p95 transport delay.
3. Hyperliquid entry evidence is no earlier than its first fresh full-book
   observation after the decision.
4. The separate stress mark uses the first valid paired evidence at or after
   `t0 + 5 seconds`.
5. If either delayed leg lacks depth or continuity, reject the complete
   lifecycle; never claim a partial fill.
6. Close at the first valid delayed book where normalized basis is `<= 5 bps`,
   or force-close after 60 minutes.
7. Include funding in primary economics only when the modeled hold crosses an
   actual settlement boundary. Forecast funding remains a separate scenario.
8. Do not re-enter the same mapping/direction until the prior lifecycle closes
   and divergence stays below 5 bps for 60 seconds.

The primary fee floor uses Hyperliquid base perp taker fees and both Lighter
Standard and Premium scenarios. A result positive only under Standard's
zero-fee regime is `KILL` for robustness.

## Evidence and statistics gates

`EXTEND` requires all of the following:

- at least 100 independent closed lifecycles total;
- at least 30 lifecycles per admitted mapping;
- lifecycle observations on at least four of five UTC days;
- no day contributes more than 35% of samples;
- no instrument contributes more than 50%;
- the top ten lifecycles contribute no more than 25% of modeled net capture;
- calm, normal, and stressed volatility bins are represented using an
  independent trailing 30-day baseline;
- the one-sided 95% cluster/block-bootstrap lower bound of mean `$10` modeled
  net capture is positive under actual VWAP, Standard fees, measured causal
  delay, and five-second stress;
- median `$10` modeled net capture is positive;
- the result remains positive after every forced exit;
- the result does not depend on maker fills, forecast funding, zero exit cost,
  stale books, one market, or one day.

Failure of any hard item is `KILL`. Passing all items is `EXTEND`, never `GO`.
An absent volatility bin or otherwise insufficient regime coverage cannot be
upgraded beyond `EXTEND`.

## Persistence boundary

Use a separate PostgreSQL schema `stage_a` with no users, accounts,
credentials, tenants, or order tables:

- `runs`: immutable configuration and formula hashes;
- `instrument_mappings`: versioned identity evidence;
- `feed_connections`: connection epochs and gap reasons;
- `raw_l2_batches`: one-second gzip NDJSON batches plus uncompressed SHA-256;
- `evaluation_samples`: paired evidence, quality state, depth/VWAP profiles,
  and rejection code;
- `quality_minutes`: expected/received frames and quality ratios;
- `variational_samples`: observer timestamps and values;
- `shadow_lifecycles`: immutable opening, delayed, stress, exit, and model
  evidence;
- `stage_decisions`: append-only `KILL|EXTEND` decision and report hashes.

Raw batches retain seven complete days; evaluation/observer/lifecycle evidence
retains 30 days; mappings, summaries, run hashes, and decisions are retained.
No partition is removed during an active run. The application role cannot
update or delete evidence.

## Runtime and API boundary

The Stage A binary is `cmd/falsifier`. Its dependency graph is isolated under
`internal/stagea/*` and excludes existing execution, ownership, risk,
reconciliation, trading, and RFQ packages.

Only read-only endpoints are permitted:

- `GET /healthz`;
- `GET /readyz`;
- `GET /v1/meta`;
- `GET /v1/experiment/status`;
- `GET /v1/ops/adapter-runs`;
- `GET /v1/ops/data-quality`;
- `GET /v1/shadow/lifecycles` and `GET /v1/shadow/lifecycles/{id}`;
- `GET /v1/shadow/rejections`;
- `GET /v1/observers/variational/samples`.

Every `/v1/*` response declares:

```json
{
  "mode": "public_data_falsification",
  "execution_available": false,
  "recommendation": false,
  "generated_at": "RFC3339Nano UTC",
  "data": {}
}
```

Unknown decimals are `null`, never zero. Rejected or insufficient evidence is
a successful fail-closed evaluation and returns HTTP 200. Invalid filters
return 400, missing stable IDs return 404, and unavailable storage/read models
return 503.

Allowed terms are `raw divergence`, `delayed executable-book spread`,
`modeled entry/exit cost`, `modeled closed-lifecycle net capture`, `funding
scenario`, and `observer deviation`. Do not publish `PnL`, `profit`, `ROI`,
`APY`, `win rate`, `actionable`, `executable arbitrage`, or `earnings`.

## CI proof of no execution

CI must build and test `./cmd/falsifier` independently and fail when its
dependency closure includes execution, ownership, risk, reconciliation,
trading/RFQ contracts, wallet/signing libraries, Telegram, or exchange SDKs.

CI also rejects Stage A environment names containing `PRIVATE_KEY`, `SECRET`,
`API_KEY`, `TOKEN`, `WALLET`, `MNEMONIC`, or account identifiers; forbids
place/cancel/sign/withdraw/transfer routes and private/account channels; proves
all mutating HTTP methods return 404/405; and runs deterministic replay,
reconnect, duplicate, nonce-gap, clock-step, stale, skew, and partial-depth
tests.

Stage A configuration contains only public venue URLs, `DATABASE_URL`, HTTP
address, instrument-manifest path, retention, and quality thresholds. The
existing credential-bearing `.env.example` is not part of the falsifier
runtime contract.

## Five-day sequence

1. Day 1: freeze capital formula, contract mappings, reason codes, schemas,
   negative CI, and immediately evaluate the `$10` feasibility gate.
2. Day 2: PostgreSQL batching/replay and fake-feed clock/gap tests.
3. Day 3: Hyperliquid full-snapshot collector.
4. Day 4: Lighter snapshot/delta reconstruction and causal pairing.
5. Day 5: Variational observer, integrity/statistics report, and append-only
   `KILL|EXTEND` decision.

The five-day observation clock starts only after both primary collectors,
storage, replay, mappings, and quality monitors pass a 60-minute warm-up. The
implementation days do not count toward the five complete data days.

## Future product threat model

The stated future audience includes low-capital users in Bangladesh, India,
the Philippines, Nigeria, and Pakistan, with expected bot-farm/Sybil traffic.
This does not change Stage A market microstructure.

A future product is `KILL` if its economics require wash/self-trading,
artificial volume, Sybil or multi-account farming, referral abuse, or evasion
of venue KYC, regional, rate-limit, or anti-abuse controls. Stage A collects no
identity, geography, account data, or credentials and implements none of those
behaviors.

## Primary sources

- [Hyperliquid WebSocket subscriptions](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions)
- [Hyperliquid fees](https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees)
- [Lighter WebSocket](https://apidocs.lighter.xyz/docs/websocket-reference)
- [Lighter account types](https://apidocs.lighter.xyz/docs/account-types)
- [Variational public API](https://docs.variational.io/technical-documentation/api)
