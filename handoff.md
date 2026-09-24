# Multi-Exchange Engine — current handoff

**Updated:** 2026-08-21
**Current branch:** `main`
**Safety status:** public evidence and read-only analysis only; no live trading authorization

Historical continuity is preserved in
[`docs/archive/handoff/handoff-through-2026-08-09.md`](docs/archive/handoff/handoff-through-2026-08-09.md),
in the [expanded handoff before this refresh](https://github.com/Dimkox/multi-exchange-engine/blob/e0be8eb7fe45fa1759fa7298970cc84a04961eeb/handoff.md),
and in Git history.

## Current objective

Stage A remains the three separately installable distributions under `packages/`:

1. `mee-contracts` — immutable contracts and the exact domain kernel;
2. `mee-public-capture` — credential-free public capture and constrained evidence output;
3. `mee-readonly-analyzer` — deterministic reconstruction, economics, strategies and reports.

The analyzer now emits one canonical `mee-stage-a-decision/v1` JSON document
from a sealed `mee-readonly-frozen-package/v1` tree. Claimed Hyperliquid
`l2Book` envelopes and claimed Lighter `subscribed/order_book` snapshots
reconstruct fail-closed into `OrderBookSnapshot` values. Contiguous typed
Lighter `update/order_book` frames after an admitted snapshot admit further
checkpoints. A nonce gap or update-before-snapshot closes that channel's
in-memory epoch without `ReconstructionError`, so Hyperliquid books in the
same tuple still admit. Official Lighter frames that omit ticker `symbol`
reconstruct when a unique sealed Lighter mapping has `lighter_market_index`
equal to the `order_book:{n}` channel suffix; typed updates inherit the open
channel epoch's ticker. Capture does not stuff `symbol` into payloads.
Ambiguous or missing index joins stay `INVALID_RECORD`. Malformed Lighter
JSON (garbage, unknown type, malformed snapshot or update parse) stays
`INVALID_RECORD`. A malformed Hyperliquid payload or a non-unique mapping is
`INVALID_DATASET` / `INVALID_RECORD`. A reconstructed book is bound only when
sealed mapping evidence uniquely covers that book's snapshot venue, symbol,
and observation time. Lighter books persist the `order_book:{n}` channel on
`ReconstructedBook`; bind prefers the unique current APPROVED row whose
`lighter_market_index` equals that suffix, so an extra unindexed same-ticker
sibling does not `INVALID_RECORD` a correctly joined official book. Zero
indexed matches fall back to a unique unindexed ticker (stuffed-symbol tests).
Hyperliquid bind stays ticker-only. Missing, rejected-only, expired, or
ambiguous mappings are `INVALID_RECORD`. Default fixture capture dual-writes the
Hyperliquid `l2Book` envelope and an official omit-symbol Lighter
`subscribed/order_book` snapshot on `order_book:1`, with `REVIEWED_BTC` then
`REVIEWED_LIGHTER_BTC` (`lighter_market_index: 1`). Capture does not stuff
`symbol`. Those fixtures stay `INSUFFICIENT_EVIDENCE`. An in-memory full-depth VWAP sweep can consume one
reconstructed bound book for one buy or one sell only when that book is
already bound to sealed identity with `displayed_size_unit=="coin"` and
`reviewed_contract_multiplier==Decimal("1")`. Unbound, non-`coin`, and
multiplier ≠ 1 books raise `VwapError` with no fill and no `sz` conversion.
BTC coin/1 Fraction arithmetic is unchanged. Fills are not written into the
package, not printed, and are not reconstructed P&L. Verdict still does not
call VWAP. A sufficient package with a well-formed optional `economics.json`
member can be `STOP` or `EXTEND_LONGER_SHADOW`. Fixture and capture
six-member stubs stay `INSUFFICIENT_EVIDENCE`; that is not economic evidence.
`GO` is still impossible. Sealed economics still own STOP/EXTEND.
Reconstructed books are not written into the package. There is still no
`ReconstructionEvent` stream, no `economics.json` replacement, and no `GO`.

There is no Stage A execution artifact. The legacy `multi_exchange_engine`
import roots are gone. Hypothesis and conformance work executes only in Python;
Go remains `TEST_ONLY_EXECUTABLE_SPEC` and is excluded from Stage A artifacts.
`make product` builds exact-SHA wheels and the wheel-only images.
`make prod` runs the fixture capture→analyzer loop through `compose.stage-a.yml`
on volume `mee-stage-a-data`. Host D0/D1 work remains paused. No private venue
access or live trading is authorized.

## Architecture and authority boundary

Runtime code, tests, accepted ADRs, `SECURITY.md`, `docs/ROADMAP.md` and the
machine-readable architecture manifests remain authoritative for what exists
and what may execute. Research can select hypotheses and validation work; it
cannot create implementation, release, deployment, custody, private API or
trading authority.

The last recorded runtime baseline remains fail-closed. Merge policy still
requires the external Story 1.2 trust boundary rather than a local flag change.
Unresolved graph conflicts must stay explicit, and no document, package,
workflow, configuration or branch purpose may be left unbound.

## Product and market research authority

The canonical market-demand and Jobs-to-Be-Done synthesis is
[`docs/research/user-needs/README.md`](docs/research/user-needs/README.md).
It is the input for interview targets, offer tests, packaging hypotheses,
pricing hypotheses and kill criteria. It is not proof that a product surface is
implemented or legally available.

The canonical South Korea/Kakao decision is
[`docs/research/MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18`](docs/research/MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18).
Its machine-readable graph identity is `document:kakao-korea-launch-gate` in
[`architecture/strategies.yaml`](architecture/strategies.yaml). Its
primary-source register is
[`docs/research/SOURCE_LEDGER.md`](docs/research/SOURCE_LEDGER.md), and its
repository-routing evidence is
[`docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md`](docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md).

## 2026-08-18 KakaoTalk / South Korea launch gate

PR #47 landed the dated KakaoTalk/South Korea platform, legal, privacy,
security, architecture and launch analysis as merge commit
`e0be8eb7fe45fa1759fa7298970cc84a04961eeb`.

The binding product decision is:

- direct Kakao crypto trading, custody, deposits, withdrawals, exchange
  account creation, API-key linking, wallet linking, personalized signals,
  copy trading, futures promotion and referral acquisition remain `NO_GO`;
- a Telegram-style arbitrary trading mini-app inside KakaoTalk is not the
  default architecture because the reviewed official product surface does not
  establish a general Telegram Mini Apps equivalent and Kakao policy creates a
  separate virtual-asset hard stop;
- the recommended Korean discovery MVP is a standalone Korean mobile web/PWA,
  without Kakao SDK or Kakao Login, limited to delayed public evidence,
  market-structure education and non-personalized read-only comparisons;
- a KakaoTalk Channel/chatbot may be evaluated later only as a support,
  education or status surface after written Kakao classification and Korean
  legal review of the exact entity, content, links and data flow.

The project must not target Korean users as politically “vulnerable.” Market
selection must be based on measurable demand, legal eligibility, retention,
support burden and unit economics.

No Korean-facing implementation starts until unresolved evidence gates are
closed or explicitly retained as fail-closed blockers. Account creation,
successful Kakao developer registration, a generic support response or silence
is not platform approval.

## Discoverability and agent routing

The Kakao/Korea gate has direct inbound routes from:

- `README.md` and its Mermaid research/machine-graph map;
- `architecture/strategies.yaml` through `document:kakao-korea-launch-gate`;
- `docs/README.md`;
- `docs/research/README.md`;
- `docs/research/SOURCE_LEDGER.md`;
- `docs/research/REPOSITORY_CONNECTIVITY_AUDIT.md`;
- `AGENTS.md`.

The dedicated graph node is connected from `requirement:PROD-001` and
`requirement:GRAPH-005`, then to `test:graph-repository-manifests`. The existing
repository inventory continues to bind the canonical
`docs/research/MASTER_RESEARCH.md` path as documentation, while the dedicated
node makes the Kakao/Korea decision independently discoverable to any agent
that loads the architecture manifests.

`AGENTS.md` requires any agent changing South Korea targeting, Kakao
distribution, Korean localization, affiliate/referral behavior, consumer
onboarding or Korean-facing content to read the exact gate and source ledger
first. No duplicate standalone research file or unclassified path was added.

## Publication and verification state

The primary research change is merged into `main` through PR #47. PR #49
carries the machine-graph follow-up and changes only
`architecture/strategies.yaml`, the root `README.md` and this handoff. It does
not change runtime, workflows, deployment definitions, packages, secrets or
live-trading boundaries.

The graph change uses edge kinds already permitted by the closed checker matrix:
Requirement-to-ADR `specified_by` and ADR-to-TestOrEval `validated_by`, each as
aggregate semantic context rather than requirement proof. Local YAML parsing,
unique-node checks, edge-matrix assertions, non-proof scope checks, Markdown
anchor checks, final-newline checks and trailing-whitespace checks passed before
publication. GitHub reported no status checks or pull-request workflow runs for
the branch head, so no full repository graph or CI pass is claimed.

## Open work that was not merged

PR #21 is closed as a superseded historical source for the explicit analyzer
salvage manifest and was not merged wholesale. PR #23 remains separate and open.
Neither PR creates authority for Korean market implementation or live trading.

## 2026-08-20 Stage A compose production loop

`make prod` wraps `compose.stage-a.yml` only. The stack volume is named
`mee-stage-a-data`. Prepare-data wipes `/data` then chowns `65534:65534`.
Capture and analyzer run as nobody with `network_mode: none`; analyzer is
`:ro`. `write_frozen_package` clears leftover children before sealing so a
reused volume cannot brick the reader. Analyzer config rejects the same
credential-like env names as capture. Default source stays fixture.

Authority remains `NONE`. No D0/D1 or live trading.

## Next actions

1. Stage A operator paths are `make demo` (host) and `make prod` (Compose volume
   `mee-stage-a-data`, fixture only). Default fixture now seals official Lighter
   omit-symbol bytes plus the indexed Lighter mapping; the class is still
   `INSUFFICIENT_EVIDENCE`. Do not treat a sealed fixture package as economic
   evidence. Fixture `INSUFFICIENT_EVIDENCE` and synthetic `EXTEND` are not
   soak proof and are not `GO`. Public `MEE_CAPTURE_SOURCE=public` still
   fetches only Hyperliquid `l2Book` and does not live-collect Lighter.
2. Residual after contiguous Lighter updates: still without replacing
   `economics.json`, still without episode arrays, still without a
   `ReconstructionEvent` / `EPOCH_CLOSED` stream, still without `GO`. Do not
   convert `sz` through the multiplier. Do not wire VWAP into verdict. Do
   not treat VWAP fills as reconstructed P&L. No live trading.
3. Host D0/D1 stays paused. Merge stays fail-closed. No live trading.
4. Validate Korean demand with interviews, a Korean landing page or waitlist,
   comprehension tests and retention signals before building a messenger
   integration. Keep Kakao Login, custody and all trading functions excluded
   until separately approved.
