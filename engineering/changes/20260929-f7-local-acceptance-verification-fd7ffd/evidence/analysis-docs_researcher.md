# F7 documentation and acceptance analysis

Route: `fd7ffd5cc17f`
Change: `20260929-f7-local-acceptance-verification-fd7ffd`
Role: read-only repository evidence and claims analysis
Observed HEAD: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`

## Executive finding

The repository has strong local supporting evidence from F3 through F6, but it
does not yet have a final-commit A01–A30 acceptance result. Stage-level `ready`
receipts are not interchangeable with case-level acceptance evidence. The
canonical result runner requires a clean committed tree and per-case assertion
commands that emit bound JSON evidence; no checked-in acceptance plan or
assertion program currently turns the stage evidence into those results.

If the runner is executed now in offline mode without a plan, its exact truthful
result is `INCOMPLETE`: A07, A13, A14, A29 and A30 become
`BLOCKED_EXTERNAL` because `tools/mezo_acceptance/cases.py` marks them live;
the other 25 cases become `NOT_RUN` with
`ASSERTION_COMMAND_NOT_CONFIGURED`. Historical F1 labels for A01 and A27 do
not change that final-commit result. F7 therefore cannot be closed as a release
candidate or competition-ready product under the canonical specification.

## Authority and evidence boundary

- `docs/planning/LIQVERA_FACTORY_TZ.md:258-332` defines A01–A30, requires
  separate unit/contract/fault, PostgreSQL, offline E2E, and live/testnet levels,
  and explicitly says mocks do not replace A13.
- `tools/mezo_acceptance/cases.py` is the executable inventory. Its live set is
  exactly A07, A13, A14, A29 and A30.
- `tools/mezo_acceptance/runner.py:213-258` makes an unapproved live case
  `BLOCKED_EXTERNAL`, an unconfigured non-live case `NOT_RUN`, and the overall
  result `INCOMPLETE` unless every row is `PASS`.
- `engineering/changes/2026-09-24-mezo-evidence/acceptance-matrix.md` is an F1
  snapshot, not final-product acceptance. It says F7 must repeat acceptance
  against the final implementation.
- F3, F4, F5 and F6 package states are all `ready`, but their own requirements
  and reviews repeatedly say the frozen vectors remain `NOT_RUN` and forbid
  inference of live payment, deployment, release, or broad acceptance.

## A01–A30 evidence map before the F7 run

“Supporting evidence” below identifies reusable repository evidence. It is not
a recommendation to mark a row `PASS` without an assertion program executing
the complete named criterion on the final clean commit.

| ID | Current truthful runner status | Exact repository evidence and gap |
| --- | --- | --- |
| A01 | `NOT_RUN` | F1 retained separate baseline/current results in `evidence/f1-verification.md`; later F3–F6 verifier receipts exist. F7 still needs one assertion that binds the relevant before/after evidence to the final commit and does not hide prior failures. |
| A02 | `NOT_RUN` | Exact arithmetic and canonical fixture paths are covered by Stage A/F2/F3 tests, including the canonical F3 fixture build. No A02 assertion output proves every §7 BUY value on the final commit. |
| A03 | `NOT_RUN` | Existing analyzer/vector tests support SELL and rational arithmetic behavior, but no runner evidence binds the complete one-level/all-depth/non-terminating-fraction criterion. |
| A04 | `NOT_RUN` | Contract/analyzer rejection tests are supporting evidence. The acceptance assertion must additionally prove no chargeable quote and no settlement for every named invalid quantity/depth form. |
| A05 | `NOT_RUN` | Validation contracts/tests cover snapshot failures, but no result row demonstrates every named stale/future/crossed/instrument/metadata rejection and absence of sale. |
| A06 | `NOT_RUN` | Identity/mapping contracts are fail closed; no runner evidence executes fictitious source hash plus wrong unit/multiplier and proves the required rejection. |
| A07 | `BLOCKED_EXTERNAL` | The registry classifies this live. This route forbids live-public access, so it cannot execute the canonical no-hidden-fixture-fallback observation. Local simulation must not be relabelled A07. |
| A08 | `NOT_RUN` | F3 focused tests and independent review prove report/bundle tamper rejection, unsafe archive handling, trusted-digest rejection, and immutable publication. A dedicated final-commit assertion still must cover the complete raw/mapping/report/manifest and traversal/bomb matrix. |
| A09 | `NOT_RUN` | F3 installed-wheel test builds outside the checkout with `--no-index`, replays the fixture and verifies exact digest. This is strong reusable evidence, but F7 must run and bind the exact clean-machine/no-network criterion rather than cite it as an automatic pass. |
| A10 | `NOT_RUN` | F4 gateway/ledger tests support fail-closed protected delivery; no complete runner assertion currently proves authorized unpaid GET, exact 402 headers, and absence of paid bytes. |
| A11 | `NOT_RUN` | F2 contract examples and F5 fake state tests support invalid/duplicate handling. The full signature/network/token/amount/receiver/payer/expiry/reuse matrix with zero entitlement/body is not bound to an A11 result. |
| A12 | `NOT_RUN` | Protocol lock and runner enforce `10000000000000000` for live A13 metadata; no A12 assertion traces the same value through every contract, gateway, ledger, and UI layer. |
| A13 | `BLOCKED_EXTERNAL` | `PAY_TO_MISSING`, authorization identity, funded buyer and finality remain unresolved. There is no tx hash/block/log index for a distinct buyer-to-merchant confirmed Mezo Testnet MUSD Transfer. Mocks cannot pass this row. |
| A14 | `BLOCKED_EXTERNAL` | Depends on passing A13 and must bind the same transaction plus exactly one settlement. F5 local no-resettlement and entitlement-reuse tests are supporting fault evidence only, not real repeat access after payment. |
| A15 | `NOT_RUN` | F4 disposable PostgreSQL proves 20 simultaneous identical creates converge on one logical request/report and one budget hit. It does not execute 20 quote/payment retries or a real charge, so the broader criterion needs a deliberately scoped assertion and truthful limitation. |
| A16 | `NOT_RUN` | F4 disposable PostgreSQL verifies same-key changed-body conflict and cross-scope isolation. A final-commit runner assertion can reuse this test but must bind the exact 409/no-new-action observation. |
| A17 | `NOT_RUN` | F5 fake tests cover stale pre-submit recovery, post-submit unknown, reconciliation, confirmation and reorg withholding. They do not cover every canonical crash window with persistent PostgreSQL/chain evidence; do not claim more than the local mocked boundary. |
| A18 | `NOT_RUN` | F5 proves lost settlement response/replay without a second settle in fakes; F4 proves lost cleanup response convergence for artifacts. The canonical paid-access recovery criterion is not executed against real settlement. |
| A19 | `NOT_RUN` | F5 bounded no-hash reconciliation and no-resettlement support the safety invariant. No assertion tests multiple similar on-chain Transfers; the live ambiguity part remains absent. |
| A20 | `NOT_RUN` | Frozen contracts describe expiry semantics, but no existing retained execution proves chain-confirmed payment during expiry unlocks the original report. |
| A21 | `NOT_RUN` | F4 cross-scope idempotency and F6 session/capability tests support scope isolation. A complete foreign capability, guessed ID and public-tx-hash access matrix is not currently bound. |
| A22 | `NOT_RUN` | F3 atomic/immutable publication and F4 missing-artifact fail-closed recovery are strong support. The full before-payment no-charge and after-payment incident/no-new-payment path remains unexecuted as one criterion. |
| A23 | `NOT_RUN` | F2 compatibility lock and F6 wrong-chain UI tests support rejection; payment readiness is false. No runner assertion currently mutates RPC chain ID, registry token, and mainnet configuration across the production boundary. |
| A24 | `NOT_RUN` | F5 fake paths prove unknown/mismatched confirmation withholds delivery and entitlement. Production facilitator verify-success followed by settle-failure/unknown is not configured or executed. |
| A25 | `NOT_RUN` | Repository secret scanning, runner redaction checks, safe-label metric tests, and no-sensitive-browser-state design are supporting evidence. The required canary-in-logs-and-built-browser-bundle test has not been run as A25. |
| A26 | `NOT_RUN` | F6 static resolved-Compose tests prove fixture zero-egress topology and environment/network separation in configuration. F6 explicitly records disposable container/runtime isolation and health evidence as unrun; static YAML cannot pass runtime A26. |
| A27 | `NOT_RUN` | Historical F1 A27 passed with 641 tests/85 subtests; subsequent full verifiers passed larger suites and preserved `INSUFFICIENT_EVIDENCE`. F7 must rerun a final-commit assertion and bind unchanged Stage A verdict/fixture behavior. |
| A28 | `NOT_RUN` | F3 installed wheels and demo-related tests are partial support. The full README clean install, all lockfile builds, web exact build and offline demo were not reproduced in one clean environment; F6 could not install/build exact Vite 7.1.5 from the offline cache. |
| A29 | `BLOCKED_EXTERNAL` | `PROVENANCE.md` retains import/publication history, but the runner classifies this live and there is no fresh anonymous clone/tree comparison for the final commit. The branch is ahead of `origin/main`, so the final local tree is not the public repository identity. |
| A30 | `BLOCKED_EXTERNAL` | F6 has 14 deterministic fake-browser scenarios for cancel, switch, reload and wrong chain, with zero implicit adapter calls. The registry nevertheless classifies canonical A30 as live; the route forbids real wallet/RPC activity, and F6 itself leaves A30 `NOT_RUN`. Record the local browser suite separately; do not convert it into canonical PASS. |

The 156 frozen F2 vectors are a separate runtime catalog and remain
`NOT_RUN`. Passing focused tests or F3–F6 routes must not bulk-promote them.

## Stale or unsupported claims to repair

### README status is behind the tree

`README.md:26-31` says F6 exact-lock build, full verification and independent
review remain pending and labels `F6–F7` together as
`IMPLEMENTED_UNVERIFIED`. F6 package state is now `ready`; its full verifier
and five independent reviews passed. The truthful replacement must distinguish:

- F6 local fake/static verification: `ready`;
- exact Vite install/typecheck/build: `NOT_RUN` because the pinned tarball was
  unavailable in the authorized offline cache;
- runtime A26 and canonical/live A30: not accepted;
- F7 final acceptance and release candidacy: incomplete.

`README.md:99-106` also broadly says the components are “code-complete but
unverified.” That is too coarse after F3–F6 route closure. Describe which local
slices are verified and preserve every external/runtime omission.

`README.md:199-205` calls both local demos unverified and the interactive
implementation “not yet verified.” The demos still must be labelled
`SIMULATED — NO TRANSFER` and are not A13/A14 acceptance, but the underlying F3
canonical artifact path now has local verification. Separate demo-product
acceptance from component-level test evidence instead of using one ambiguous
“unverified” label.

### Handoff mixes superseded chronology with current instructions

The F6 section correctly ends with `ready` and no acceptance promotion, but
`handoff.md:48-59` still says the exact web build is “not yet evidenced” and a
clean rerun/reviews “remain next.” The first statement remains true only for
the exact Vite build; the second is obsolete. Similar historical “next step”
sentences remain inside closed F3–F5 narratives. The top current-state section
should name only the actual next action (F7 local acceptance aggregation) and
move failed/superseded steps under explicit history so operators do not rerun
the wrong phase.

### Acceptance matrix is intentionally historical and cannot be presented as current

The existing matrix still reports F1-era 641-test results, a failed Grok run,
and A30 `NOT_RUN`. Preserve it as F1 evidence or clearly timestamp it. F7 needs
a new final-commit result/report rather than overwriting history. The new report
must not convert stage readiness into case PASS, and it must retain omissions,
commands, environment names, timestamps, exit codes, commit and tree identity.

### Competition and release language

The files under `docs/competition/` are mostly appropriately labelled draft,
future, intended, or simulated. Keep those qualifiers. In particular:

- `docs/planning/LIQVERA_FACTORY_TZ.md:318` says “MUSD is used directly in the
  working API” as a requirement/packaging statement. Current evidence supports
  a fail-closed boundary and mocked adapter tests, not a working confirmed
  MUSD payment API. Submission copy must say “intended testnet integration”
  until A13/A14 pass.
- No hosted-demo URL, video, released commit, testnet transaction, public clone
  proof for the candidate, tag, or GitHub Release exists in retained evidence.
- “Built for The Mezo Buildathon” is truthful attribution, but it is not proof
  of eligibility, submission, acceptance, deployment, or organizer approval.
- A local simulated fixture demo may be shown only as `SIMULATED — NO
  TRANSFER`; it cannot be narrated as the canonical testnet script.
- The repository cannot be called a release candidate under the specification
  while A13/A14 are blocked, A26/A28 are unrun, A29 is not refreshed, the web
  exact build is absent, and the final A01–A30 result is incomplete.

## Required truthful F7 outputs

1. Run the result producer only after the candidate is clean and committed.
   Store a new result; never edit statuses or overwrite the F1 matrix.
2. Add narrowly scoped local assertion programs only for criteria whose whole
   named result can be proven from deterministic final-tree execution. A
   wrapper that merely checks a prior Markdown claim is insufficient.
3. Keep A07/A13/A14/A29/A30 `BLOCKED_EXTERNAL` in this no-live route. Record
   F6 fake-browser evidence as a local supporting result, not A30 PASS.
4. Leave partially covered rows `NOT_RUN` rather than weakening their canonical
   meaning. If a local sub-criterion is useful, report it outside the canonical
   status with exact limitations.
5. Produce a readiness report whose overall conclusion is
   `INCOMPLETE / NOT RELEASE-READY / NOT SUBMISSION-READY`, even if every
   authorized local assertion passes.
6. Preserve the shadow-only gate and explicitly state: no wallet, RPC,
   facilitator, transfer, testnet/mainnet payment, live-public call, shared
   environment, deployment, publication, push, tag, merge, release, or exchange
   mutation was performed.

## Recommended final status language

> F3–F6 have independently reviewed local evidence for bounded offline,
> disposable-PostgreSQL, fake-settlement, browser-fake, and static operations
> slices. The F7 acceptance result is incomplete. No confirmed testnet payment,
> repeat paid retrieval, live-source run, runtime container isolation,
> clean-machine full build/demo, refreshed anonymous clone proof, real-wallet
> run, deployment, or release has been performed. Liqvera is not release-ready
> or competition-submission-ready on this evidence.
