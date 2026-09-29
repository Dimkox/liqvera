# F7 live acceptance and v0.0.1 release analysis

Route: `337ef5ec16a0`
Change: `20260929-f7-live-acceptance-and-release-0-0-1-337ef5`
Role: read-only documentation, acceptance, competition, and release analysis
Observed HEAD: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`

## Executive finding

The requested sequence is feasible only as two separately gated phases:

1. repair and independently verify the acceptance/release machinery on a clean
   committed candidate; then
2. after exact owner approval of the final live plan, perform bounded public
   reads and one Mezo Testnet transfer before a separately reviewed publication
   step.

The repository is not release-ready at analysis time. There is no final-tree
A01–A30 result, root `VERSION`, product release artifact manifest, testnet
transaction, live demo receipt, exact web build, runtime Compose evidence, or
current anonymous-clone proof. Public read-only inspection on 2026-09-29 found
`origin/main` at `f07562e`, no remote tags, and no listed GitHub Releases. The
working branch is 40 commits ahead and has untracked change packages, so it is
not yet a publishable candidate.

## Canonical acceptance classification

`docs/planning/LIQVERA_FACTORY_TZ.md:258-332` remains authority. The runner must
not redefine a criterion merely to make it pass. The requested A30 repair is
valid because A30's required observation is local UI behavior—cancel, wallet
state change, reload, and wrong-chain handling with no implicit payment. It
does not itself require a chain transaction. A30 should therefore be locally
eligible (`live=False`) and should execute the real browser orchestration with
fakes. This does not turn A13/A14 into PASS or prove a real-wallet demo.

The truthful execution classes after that repair are:

| Class | Cases | Required treatment |
| --- | --- | --- |
| Deterministic local | A01–A06, A08–A12, A15–A28, A30 | Execute complete semantic assertions against the exact final committed tree. PASS only when the evidence document proves every part of the named criterion; partial stage evidence stays `NOT_RUN` or fails the assertion. |
| Public live read | A07, A29 | Requires explicit approval for the exact hosts/requests. Retain response identity, time, bounded transport result, and no-fixture-fallback or anonymous-clone comparison. If unavailable, use `BLOCKED_EXTERNAL`, never PASS. |
| Mezo Testnet mutation | A13, A14 | Requires the dedicated funded buyer, verified distinct merchant, exact chain/token/amount, authorization identity, finality rule, facilitator/RPC readiness, and an explicit transaction approval. A14 must reuse A13's transaction and prove one settlement. |

The existing 156 frozen vectors remain a separate runtime catalog. They may be
used as test inputs, but no bulk PASS is permitted merely because contract
tests or a route verifier passed.

### Minimum semantic content by acceptance group

- A01: retain before and final-tree checks separately, including historical
  failures; bind the final command set, commit, tree, timestamps, and exits.
- A02–A06: assert exact calculation and every named rejection plus absence of
  a chargeable quote/settlement. Merely running pytest is insufficient unless
  the assertion extracts and validates those observations.
- A08–A09: exercise all named corruption/unsafe archive branches and a truly
  isolated no-network replay with matching bytes/digest.
- A10–A12: execute the real gateway boundary; prove exact 402 headers, no body
  or entitlement on every invalid authorization, and the atomic amount through
  every layer.
- A13–A14: retain sanitized tx hash, canonical block hash, log index, distinct
  buyer/merchant, chain `eip155:31611`, MUSD
  `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`, amount
  `10000000000000000`, finality decision, entitlement, repeat report/bundle
  identity, and settlement count exactly one. Never retain keys or signatures.
- A15–A20: use real disposable PostgreSQL where persistence is part of the
  criterion; fakes may prove safety branches but cannot stand in for every
  crash/chain observation.
- A21–A25: cover scope isolation, both artifact-loss phases, wrong chain/token,
  unknown settlement, and canary redaction from logs plus the built browser
  bundle.
- A26: static Compose resolution is necessary but not sufficient. Execute the
  disposable containers and prove runtime egress/environment isolation,
  health/readiness distinction, and private metrics.
- A27: rerun Stage A on the final tree and prove `GO` remains impossible.
- A28: follow README from a clean environment using lockfiles, including exact
  Python, gateway, web, image/Compose, offline demo and verifier steps. F6's
  missing Vite 7.1.5 build must be resolved rather than omitted.
- A29: anonymously clone the public candidate after push, compare the intended
  commit/tree and provenance, and retain the observation. It cannot pass before
  publication; publication and post-publication proof must be ordered so the
  release report distinguishes pre-release approval from post-push validation.
- A30: execute production-used browser orchestration with deterministic wallet,
  API, storage, crypto and time fakes; assert zero implicit payment. A separate
  operator demo with a real wallet is useful competition evidence but is not
  required to make this local UI criterion semantically valid.

## Live/Testnet stop conditions

The live plan must be exact and reviewable before secrets are made available.
Only variable names and secret-file locations belong in plans or reports.
Required preflight comes from `docs/runbooks/testnet-demo.md`:

- public source is real and retained, not a fixture fallback;
- chain is exactly 31611; token bytecode and 18 decimals match the pinned MUSD;
- the facilitator supports the exact network/scheme;
- `LIQVERA_PAY_TO` is a reviewed dedicated merchant test address distinct from
  the buyer;
- authorization identity and finality rule are reviewed and implemented;
- the buyer is a separate test-only wallet with test BTC and test MUSD;
- readiness is true on the exact source/image set;
- the owner approves the one `0.01` test MUSD action immediately before it.

Stop without a transaction if any value differs, readiness is false, the wallet
prompts for another chain/asset/recipient/amount, the source becomes stale, or
the outcome cannot be classified. After broadcast, timeout is `UNKNOWN`: do not
retry payment; reconcile by transaction/authorization identity. Mainnet, real
funds, custody, merchant private key ingestion, exchange mutation, private
venues, withdrawals, and unrelated external writes remain forbidden.

## Version and tag naming

Current version identities are heterogeneous:

- root `pyproject.toml`: `multi-exchange-engine 0.1.0.dev0`;
- four Python runtime distributions: `0.1.0`;
- protocol, gateway, and web npm packages: `0.1.0`;
- no root `VERSION` file;
- no existing local or remote tag; no GitHub Release was listed.

Therefore “update version metadata to 0.0.1” must not be implemented as a blind
global replacement. Downgrading the seven already-`0.1.0` component packages
would change internal dependency pins, wheel names, Dockerfile COPY/install
contracts and lockfiles for no product benefit. It would also turn the root
from PEP 440 `0.1.0.dev0` into the earlier release line `0.0.1`, which needs an
explicit versioning decision.

Recommended bounded convention:

- product/repository release identity: root `VERSION` containing exactly
  `0.0.1`;
- annotated release tag and GitHub Release: exactly `v0.0.1`;
- release title: `Liqvera v0.0.1`;
- keep inherited `mee-*` identifiers and component package versions `0.1.0`
  unless the owner separately approves a coordinated package-version migration;
- README must state both identities plainly: Liqvera release `0.0.1`, component
  package versions `0.1.0`, root legacy workspace metadata as actually retained
  or deliberately changed.

If a single-version policy is required instead, stop for an explicit decision;
it is a cross-package migration, not release-paperwork cleanup. Tests must lock
the chosen VERSION/tag/release-name mapping and ensure the tag points exactly
to the reviewed release commit.

## Release artifact contract

The current factory can build Python wheels but has no Liqvera release bundle
or checksum manifest. `dist/` is ignored. GitHub-generated source archives are
not enough to prove the locally verified build. Before publication define and
test one immutable artifact set, suggested as:

- `liqvera-0.0.1.zip`: deterministic source/release bundle for the exact release
  commit, excluding `.git`, secrets, local state, caches and ignored outputs;
- `liqvera-python-0.0.1/` archive or the exact four built `0.1.0` wheels plus
  required pinned runtime wheels from `make liqvera-python`;
- built gateway and web distributable archives only after exact-lock builds;
- sanitized final acceptance JSON plus its evidence manifest;
- `SHA256SUMS` covering every uploaded asset, with stable names and sizes;
- release notes naming commit/tree, verifier fingerprint, review receipts,
  artifact digests, passed cases, `NOT_RUN`/`BLOCKED_EXTERNAL` cases, and known
  audit findings.

Container images should be referenced by immutable digest if published; a
mutable tag is not release evidence. If images are not published, say so and
attach no invented image digest. Test extraction/install/verification from the
finished assets in a fresh directory before tagging. Rebuild after any tracked
change, including README/version/evidence changes, then bind the final artifact
hashes to the final release commit.

The public release must not contain `.env`, wallet material, secret files,
capabilities, authorization payloads, signatures, cookies, raw private logs,
database dumps, or unreviewed acceptance stdout/stderr. A full-history and
artifact secret scan is required before upload.

## Publication ordering and exact Git binding

The acceptance runner currently requires a clean commit, while A29 can only
pass after that commit is public. Avoid self-referential evidence:

1. create the final release-candidate commit with version, README, code and
   deterministic local/live/testnet evidence other than post-publication A29;
2. run full verification and independent code/test/security/data/release review
   on that exact commit/tree and build immutable artifacts;
3. obtain the named publication approval and push that exact commit to `main`;
4. anonymously clone and compare commit/tree/provenance for A29;
5. do not amend the release commit to embed its own post-push result. Publish
   A29 as a release-side evidence asset or immutable GitHub Release note/asset
   bound to the release commit;
6. create annotated `v0.0.1` at the reviewed commit and verify remote tag target;
7. create GitHub Release `v0.0.1`, upload assets, then independently download
   and hash-check them.

The route task grants intent, but the named human gates still require an exact
scope/design approval and an exact external-write/payment/publication approval.
Do not treat approval of code repair as approval to broadcast a payment, push,
tag, or create a release. `scripts/grok_deploy.py` only prepares human-owned
commands and does not itself publish.

## README and competition truth

Before push, README must match the final tree and must replace its stale F6
“verification pending” text. Required claims:

- distinguish locally verified F3–F6 slices from canonical A01–A30 outcomes;
- report exact acceptance status and omissions from the final result;
- call the fixture demo `SIMULATED — NO TRANSFER`;
- claim a Mezo Testnet payment only if A13/A14 evidence exists, with sanitized
  public transaction references;
- state whether web build, containers, anonymous clone, hosted demo and release
  assets were actually executed and checked;
- retain payment/testnet-only and shadow/no-exchange-mutation boundaries;
- preserve component version distinctions and inherited `mee-*` names.

Competition materials may say “Built for The Mezo Buildathon,” but this does not
prove eligibility, submission or organizer approval. The draft description is
correct to call payment an objective until A13/A14 pass. A final submission
must add only URLs that actually exist: released commit, public code, release,
hosted demo and video. It must distinguish the imported Multi-Exchange Engine
baseline from Liqvera changes and disclose the retained proprietary metadata/no
inferred open-source license. Organizer dates, timezone, eligibility and license
requirements still need owner verification; repository planning text is not
organizer authority.

## Go/no-go recommendation

Current decision: **NO-GO** for payment, push, tag, or GitHub Release.

Move to conditional GO only when all of the following are true on one immutable
candidate: semantic runner repairs and mutation tests pass; local acceptance is
executed; the exact web and container builds pass; live/Testnet preflight is
green; A13/A14 either pass with reviewed evidence or the owner explicitly
chooses a truthful limited release whose notes do not claim F7 completion;
required independent reviews and final verifier are current; artifacts and
checksums reproduce; README/version naming is consistent; and the exact
external actions have current human approval. Any `FAIL` blocks release.
`BLOCKED_EXTERNAL` or `NOT_RUN` may appear in a deliberately limited v0.0.1
only if the owner explicitly accepts that reduced claim and the release is not
described as completed F7, payment-ready, or competition-submission-ready.
