# Decisions

Patterns that paid for themselves. Each entry is at most three sentences.

## 2026-08-21 — Fixture dual-write official Lighter omit-symbol plus indexed mapping

Default fixture capture writes a second official `subscribed/order_book` envelope without stuffing `symbol` and a unique `lighter-btc-usd-linear-perpetual` row with `lighter_market_index: 1`. Analyzer reconstruct+bind already admits that shape; the sealed fixture class stays `INSUFFICIENT_EVIDENCE`. Capture does not guess ticker from the channel suffix.

## 2026-08-21 — Persist Lighter channel so bind repeats the reconstruct join

`ReconstructedBook.channel` keeps the Lighter `order_book:{n}` suffix after reconstruct so identity can unique-join `lighter_market_index` the same way the snapshot join already did. An extra unindexed same-ticker sibling is not a second candidate when one indexed row unique-matches. Hyperliquid books keep `channel is None` and stay ticker-only.

## 2026-08-21 — Optional lighter_market_index is not a 19th required mapping key

`lighter_market_index` is optional JSON so 18-key `REVIEWED_BTC` and `SAMPLE_MAPPING` documents still read. Lighter epochs are keyed by channel so official updates that omit `symbol` inherit the open cursor ticker. Do not guess the sole unindexed Lighter row; join requires unique index equality.

## 2026-08-21 — Typed Lighter update is epoch sequencing, not INVALID_RECORD

A well-typed Lighter `update/order_book` applies when `begin_nonce` matches the open snapshot nonce; gap and update-before-snapshot pop that symbol and ignore so Hyperliquid books in the same tuple still admit. Malformed Lighter JSON stays `INVALID_RECORD`. Do not sort after apply and do not port capture `LighterBookReducer`.

## 2026-08-21 — Analyzer Lighter snapshot decoder, not capture reducer

Admit claimed `subscribed/order_book` bytes in analyzer `reconstruction/lighter.py`; do not import or port capture `LighterBookReducer`. A claimed Lighter envelope that is not that snapshot is `INVALID_RECORD`, not skip. Required payload `symbol` is claimed-JSON only because official WS has no ticker; do not guess from `market_index`.

## 2026-08-20 — Refuse coin-unit VWAP unless the book is already bound coin/1

`sweep_depth` succeeds only on a reconstructed book already bound to sealed identity with `displayed_size_unit=="coin"` and `reviewed_contract_multiplier==Decimal("1")`. Unbound, non-coin, and multiplier ≠ 1 raise `VwapError` (not `INVALID_RECORD`, not `DepthRejected`); do not convert `sz`.

## 2026-08-20 — Bind Hyperliquid books in analyzer identity.py, not reconstruction decode

Fail-closed identity bind lives in `mee_readonly_analyzer.identity` so a missing or ambiguous Hyperliquid mapping is `INVALID_RECORD` without looking like a malformed `l2Book`. Reconstruction stays bytes-to-book; reuse sealed `MarketMappingEvidence` and do not fork M5 `EconomicIdentity`.

## 2026-08-20 — Gate BookLevel through ExactDecimal then accumulate Fraction

VWAP converts each admitted Decimal level with `ExactDecimal.from_decimal`, then accumulates `Fraction(scaled, SCALE)`. `ExactDecimal.mul`/`div` truncate toward zero and cannot represent VWAP `17/15`.

## 2026-08-20 — Parse Hyperliquid px/sz with ExactDecimal then Decimal BookLevel

Wire `px`/`sz` strings go through `ExactDecimal.parse` before `BookLevel`, so JSON numbers, scientific notation, and extra scale fail closed without forking `OrderBookSnapshot` onto ExactDecimal. `Decimal(str(exact))` keeps the landed snapshot type; later VWAP can convert those levels back.

## 2026-08-20 — Optional sealed economics member, not an episode array

STOP/EXTEND read sealed aggregate claims from optional extra hashed `economics.json` (`mee-stage-a-sealed-economics/v1`). Making that path required would INVALID every capture fixture; an episode array would pull reconstruction into this slice. Absent member keeps production INSUFFICIENT; a malformed declared member is INVALID_RECORD.

## 2026-08-20 — Map frozen-package errors in the analyzer, not contracts

Stage A reason codes live in `mee_contracts.decision` as `INVALID_*` strings. `FrozenPackageErrorCode` stays the reader exception. Mapping in `verdict.py` keeps contracts free of analyzer types while stdout still uses one reason class.

## 2026-08-18 — Keep Korean discovery outside Kakao until cleared

The Korean discovery MVP stays outside Kakao: direct transactions, custody, account linking, personalized signals, futures promotion and referral flows remain fail-closed. Start with a standalone Korean read-only PWA and treat a Kakao Channel/chatbot only as a later support or education experiment after written Kakao classification and Korean legal review. The canonical gate is `docs/research/MASTER_RESEARCH.md#kakaotalk-south-korea-launch-gate-2026-08-18`, and root navigation, research indexes, source confidence, connectivity evidence and agent instructions must point to it.

## 2026-08-18 — Keep market synthesis on an existing graph-bound path

The canonical market-demand and JTBD synthesis lives in `docs/research/user-needs/README.md`, which was already present in the repository inventory. Reusing that path avoids creating a new orphan document or a fake runtime node; root navigation, planning, source confidence and agent instructions must point to it.

## 2026-08-17 — Hypotheses execute only in Python

Owner constraint beat the M0-M3 plan text that said `go test`. Keep Go paths as inert `reference_source` strings, set `execution_backend=python` / `go_executed=false`, and never invoke the Go toolchain. That is what made M2 land without a Go CI step or a deployable Go artifact.

## 2026-08-17 — Sidecar manifests cannot sit in architecture/*.yaml

`tools/graph_checker/loader.py` treats the top-level `architecture/*.yaml` set as closed. A conformance document belongs in a subdirectory (`architecture/conformance/manifest.yaml`) or it fails load as `unexpected`.

## 2026-08-17 — Do not name graph YAML with "contract" unless it is OpenAPI

`grok_verify` data profile treats any changed `*contract*.yaml` as OpenAPI/AsyncAPI. New TestOrEval/Contract nodes go in `architecture.yaml` or `runtime.yaml`, not `data-contracts.yaml`.

## 2026-08-17 — Do not touch verify-a2-pr-on-claw.yml for a Makefile gate

The file already contains a hex-password assignment that Adaptive Grok's generic secret regex treats as a committed secret. Adding a Python step rescans the whole workflow and fails `secret-scan`; `make verify` already runs the suite.

## 2026-08-17 — Retire only with receipts; Go stays blocked

`retirement_decision` is fail-closed. The A2 packaging owner retired after wheel-only images existed. Go `TEST_ONLY_EXECUTABLE_SPEC` stays active until conformance plus review; eligibility never sets packaging allowed.

## 2026-08-17 — Stage A images install only wheels, Alpine needs musl

`deploy/images/` Dockerfiles are `BUILD_PACKAGING`, not `deploy/` entrypoints. Hatchling `--directory` must be absolute or it writes under the package cwd. Capture on Alpine needs a `musllinux` websockets wheel or `--network=none` install fails.

## 2026-08-17 — Merge stays fail-closed until Story 1.2 trust

`PHASE_POLICY_TIME_TRUST_MISSING` is the M0 loader refusing to self-attest `policy_times_trusted`. Do not flip that flag to make `check_graph(..., merge)` exit 0. Lock the fail-closed set: the seven remaining DECLARED conflicts plus that one trust diagnostic.

## 2026-08-20 — `make prod` wraps Compose; do not keep a second docker-run stack

README claimed `make prod` and `compose.stage-a.yml` were the same loop while
Makefile used `docker run` and a different volume name. One orchestrator and one
named volume (`mee-stage-a-data`) is the only way those sentences stay true.

## 2026-08-17 — Avoid the token `order` in a test filename stem

Path classification runs execution-token checks on the stem before `tests/` is classified. `test_ownership.py` stays `TEST_SOURCE`; `test_order_ownership.py` would be `EXECUTION_SOURCE`.

## 2026-09-24 — Public Mezo repository import

Publish a privacy-reviewed source snapshot in an independent repository with a new root commit and per-file provenance. Retain technical source/tests and original proprietary metadata; keep inherited Actions disabled. This preserves a usable baseline without disclosing private Git history or claiming the Mezo application is implemented.

## 2026-09-24 — Liqvera brand

The owner selected Liqvera with the tagline "Market reports you can verify." and attribution to MEZO ₿ — The Mezo Buildathon (https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10). The canonical repository is `Dimkox/liqvera`; documentation uses the new brand while inherited runtime identifiers and the immutable import manifest remain stable. The former specification path points to `docs/planning/LIQVERA_FACTORY_TZ.md` so existing factory links keep working.

## 2026-09-24 — English is the default project language

The owner requires English throughout project documentation and product content, regardless of the conversation language. Translate inherited prose as a documentation change while preserving technical identifiers, requirements, historical statuses, and the immutable initial import manifest. Record this default in `AGENTS.md` so future contributors do not infer localization from chat.
