# Liqvera — handoff

Updated: 2026-09-29 (F5 closed; F6 fake/static verification and independent reviews PASS). Repository: `Dimkox/liqvera`.
Branch: `feat/f3-f7-verification` (based on merged repository-cleanup main `f07562e`).

## F7 live acceptance and release 0.0.1 — 2026-09-29

Route `337ef5ec16a0` and change package
`engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/`
are implementing approved local-only P0/P1. Four route-selected analyses were
synthesized into sequential P0–P5 gates; no network read, database/container action,
wallet interaction, payment, push, tag, release, or other external mutation
occurred. The earlier local-only route `fd7ffd5cc17f` is coherently retained as
cancelled before implementation. Current decision is **NO-GO**.

P0 repairs the A01–A30 runner's semantic validation, tamper-evident evidence, final
clean Git binding, local-vs-real A30 classification, and fault/mutation suite.
P1 executes locally eligible cases into a fresh mode-0700 out-of-tree result;
missing real prerequisites remain explicit. P2 permits only separately granted
allowlisted public reads. P3 first implements and independently reviews real
authorization identity, finality, and browser x402 wiring, then requires a new
exact grant for one human-confirmed Mezo Testnet envelope: chain 31611, pinned
MUSD, exactly 0.01 test MUSD, distinct approved buyer/payee, one submission
maximum, and a numeric test-BTC gas cap. Any possible broadcast followed by
timeout is `UNKNOWN`, never retryable; only exact confirmation reconciliation
may continue.

The first P0/P1 reviews failed because exit-zero test commands could certify
their own prose claims, the plan accepted arbitrary command capability, status
reasons were open, sealing was not atomic, and retained evidence lacked a
standalone verifier. The repair keeps only five fully configured local cases
(A01, A08, A09, A27, A30), validates a closed observation shape for each, and
gives every other local case a canonical prerequisite-specific `NOT_RUN`
reason. `BLOCKED_EXTERNAL` is restricted to non-local cases with the one
canonical missing-grant reason; live mode remains unavailable because no exact
grant contract exists.

The only executable capability is the pinned current Python running the exact
checked-in dispatcher and case ID with a constructed offline environment; plan
shells, alternate argv, environment inputs, symlinks, hardlinks, replacement,
and mutation are rejected. The runner hashes the exact parsed plan bytes,
revalidates evidence and the plan, then performs its final clean commit/tree
check immediately before atomic link publication. Results and evidence are
made read-only and are **tamper-evident, not immutable**. The standalone
verifier reloads schema and semantic algebra and rehashes the result, runner,
plan, and every evidence object while rejecting linked/replaced files.

Regression coverage includes status contradictions, generic reasons, exact
A13/A14 receipt linkage, plan/link mutation, evidence symlink/hardlink attacks,
post-seal mutation, and interrupted publication. Final clean-HEAD acceptance
and full verification must be regenerated after this repair commit. Reviews
remain failed/stale until independent rerun; P2–P5 remain gated.

The first real producer→consumer run of the repair reached all five commands
and exposed a Node 22 TAP-format boundary: npm reports `ℹ tests N`, not the
older `# tests N`, so A30's closed observation correctly rejected a zero count.
The parser now accepts both native TAP spellings. Status algebra also
distinguishes a nonzero process failure from an exit-zero semantic-validation
failure; both are FAIL, while an exit-zero timeout remains contradictory.
The next local run reached the intended 5 PASS / 4 BLOCKED_EXTERNAL / 21
NOT_RUN result. Direct invocation of the new verifier then found its script
entry point lacked the repository root on `sys.path`; the entry point now adds
the same explicit repository import root used by other checked-in scripts.

The second review rejected the remaining hard-coded semantic booleans and a
late post-publication Git race. Configured cases now retain the exact pytest or
Node TAP identities observed in process output; the consumer requires a closed
case-specific subset, binds observed subject commit/tree, and additionally
checks the frozen route baseline or vector digest/count/Go-free tree where
applicable. Five per-case unrelated-success mutants are rejected.

FAIL reasons are now a closed four-value algebra with exact exit-code/timing
relationships. Evidence directories are fsynced and sealed bottom-up mode
0500; the root is sealed only after atomic result publication. Both producer
and CLI verifier compare the current clean repository with the sealed subject.
If drift appears in the late window, the canonical result name is atomically
renamed with `.invalid` rather than left accepted. Regression tests cover that
late mutation and post-seal unlink prevention.

The third review narrowed two remaining semantic gaps. A01 now exports the
frozen route baseline to a temporary read-only candidate extraction, runs the
same bounded acceptance-contract command against baseline and current trees,
and retains separate commit/tree, argv, exit, status, and transcript hashes.
The accepted delta is exact: baseline exit 4 because it predates the F7
contract test, while the current tree passes its named checks. The temporary
extraction is removed without changing the candidate or Git metadata.

A27 now supplements its vector identities with the canonical Stage A artifact
verifier and exact CLI decision/closed-enum tests. Evidence requires the frozen
`INSUFFICIENT_EVIDENCE`/non-GO verdict and binds the retained shadow fixture's
path, byte digest, terminal digest, and 38-record count. One-sided A01 evidence
and vectors-only A27 evidence are explicit negative regressions.

The fourth review found two portability/baseline gaps. Nested A01/A27 command
evidence now records a portable CPython implementation/version/executable-byte
identity plus exact argv tail, never an absolute interpreter path. A compatible
system Python can therefore verify evidence produced through the repository
venv while a different interpreter binary still fails closed. A27 now reads
both fixture files directly from the frozen baseline commit and requires the
current byte digest, record count, and terminal digest to equal that baseline;
changing fixture and terminal together is an explicit rejected mutation.

P4 defines Liqvera product release `0.0.1` while retaining inherited/component
package and API versions `0.1.0`, and builds scanned manifest-bound artifacts
plus `SHA256SUMS` from one frozen commit. Final acceptance/evidence stays
immutable outside that subject tree. P5 requires a separate exact publication
grant for a fast-forward of `Dimkox/liqvera` main, annotated `v0.0.1`, draft
GitHub Release, allowlisted asset upload/download re-hash, and final owner
confirmation. Partial publication recovery is additive: never force-push or
move a published tag.

The user approved `scope_and_design_approval` for exact gate scope digest
`82c9cb3127d0b55ca43f34ec816c8349a1d770ef52d0e4293ace580a36820f73`;
this is distinct from the canonical spec-content digest. The external-write
gate remains pending. `migration_or_external_write_approval` is not a blanket
grant and must be
realized as short-lived exact P2, P3, and P5 action records. Any changed tree,
plan, target, envelope, amount, gas cap, artifact, limitation, or remote OID
invalidates its affected grant. Mainnet, real/user funds, custody, private keys,
exchange mutation, deployment, unrelated repositories, and secret inspection
remain forbidden.

The local-only P2/P3 prerequisite slice now adds closed public-read grants bound
to commit, tree, plan digest, case, exact HTTPS method/URL, limits and a maximum
15-minute lifetime. It rejects credential-bearing URLs, private or reserved
addresses, changed DNS answers, excess attempts/time/bytes, and unknown
destinations. No grant was issued and no read was attempted; A07/A29 remain
`BLOCKED_EXTERNAL`.

The gateway now has explicit EIP-3009 identity and a twelve-confirmation
canonical Mezo Testnet finality policy. A separate exact payment grant binds
chain 31611, pinned MUSD, exactly 0.01 test MUSD, distinct buyer/payee, candidate
commit/tree/plan, one settlement submission, a 15-minute ceiling and maximum
`100000000000000` wei (0.0001 test BTC) gas. Ordinary startup supplies no grant,
performs no facilitator call, and reports `EXTERNAL_GRANT_REQUIRED`. The browser
registers the pinned official core/EVM x402 client against an injected wallet;
an ambiguous post-signature result returns only recovery and is never retried.
No network, wallet, RPC, facilitator, payment, database, release, or secret action
occurred. A13/A14 remain blocked pending independent review and a new exact grant.

The follow-up security repair removes process-local grant consumption. Migration
003 adds an append-only one-to-one grant-digest/grant-ID/payment-attempt relation;
the ledger consumes it atomically with `VERIFIED -> SUBMITTING`, before the sole
facilitator call. A conflict leaves the attempt unsubmitted, while any committed
row remains spent across restart and replicas. The reviewed EIP-3009 binding now
decodes the exact `transferWithAuthorization` selector and all nine ABI words,
including the signature commitment, rather than accepting a nonce substring.
Grant expiry is rechecked during initialization, verification and immediately
before settlement. Ordinary startup still composes `null` authority and performs
no external call. The migration was authored and tested structurally but not
applied to any database in this local-only phase.

The subsequent activation audit found the pinned facilitator SDK exposes only
opaque `settlePayment()`, not a prepared request/transaction that can be gas-
estimated and then proven byte-identical at submission. Caller-reported gas is
therefore rejected as authority: even a structurally valid grant now stops with
`LIVE_GAS_ENFORCEMENT_UNAVAILABLE`. P3 is technically blocked until a reviewed
prepare → estimate → identical-submit API exists and durable concurrency is
behaviorally proven against a disposable local database. The transaction
adapter now also has restart/concurrency coverage against a shared in-memory
transactional store; no disposable PostgreSQL URL was available or inspected,
so that test profile remains skipped and cannot activate P3.

The runner now exposes the same closed live-case orchestration used by the fake
end-to-end suite. Its authority envelope binds the current commit/tree, an
internally derived canonical plan, expiry, exact A07/A29 request bodies and
bounds, and one shared A13/A14 payment grant. A13 executes once; A14 can only
reuse its confirmed transaction, while UNKNOWN remains spent and blocks A14 in
confirm-only state. The CLI accepts only `--live-grants`, never a boolean. With
a valid exact bundle it can now execute only A07/A29 through the bounded
production public-read transport and seal closed subject/plan/grant/target/
response observations; A13/A14 remain `BLOCKED_EXTERNAL` with
`LIVE_GAS_ENFORCEMENT_UNAVAILABLE`. Offline results remain externally blocked.
Public-read grants now carry a canonical UUID and a digest derived from their
entire closed grant document. The executor derives the one-shot marker name
itself inside a mode-0700 state directory and fsyncs both marker and directory;
operators can no longer select an alternate marker filename to replay a grant.
Browser transport bounds are executable tests: timeout, redirect rejection,
credentials omission, and declared/streamed response caps all fail closed.
The first full verifier after adding these four files exposed only the expected
repository-inventory omissions (five graph tests); all four paths are now bound
to their existing runtime owners and the focused graph checks pass 5/5.
After that repair, the pinned PR verifier passed: 1,217 Python tests plus 85
subtests, coverage, secret scan, SQL safety, Ruff, Bandit and configuration
scan. Focused evidence also includes 68 acceptance/contract tests, 17 browser
tests and 24 gateway tests (five disposable-PostgreSQL tests intentionally
skipped). No public read, payment, database migration, secret access or other
external action occurred.

The P2 semantic repair removes the earlier transport-only interpretation.
A successful Hyperliquid response can no longer pass A07: the runner builds and
invokes the real gateway `HttpReportService.build` adapter against a controlled
503, requires canonical `SOURCE_UNAVAILABLE`, and proves no fixture fallback or
artifact. A29 no longer claims PASS: Git/libcurl does not expose a sufficiently
reviewer-verifiable preemptive network-byte counter. Hard wall-time, process
memory, stdout/stderr, single-file and aggregate-disk envelopes are implemented
and tested, but the runner reports `A29_NETWORK_BYTE_CAP_UNENFORCEABLE`.
Per-case errors become sealed FAIL rows rather than aborting the whole result.

Live operators must provide three explicit inputs: `--live-grants` pointing to
the exact current-subject bundle, `--operator-state-dir` pointing to a
pre-existing external mode-0700 directory, and a new external `--output` path.
The create-once mode-0400 journal identity file contains an issuer-approved
UUID; its exact digest and UUID are bound into the P2-only bundle and both P2
grants. The CLI validates it before case execution, and marker names derive
from grant UUID plus full grant digest. A different journal fails pre-I/O.
Browser payment deadlines now
remain active through complete body streaming; a stalled-body regression is
covered. P3 remains blocked by `LIVE_GAS_ENFORCEMENT_UNAVAILABLE`.
Focused repair checks pass: 69 acceptance/contract tests, 18 browser
tests, and 24 gateway tests with five explicitly disposable-PostgreSQL skips.
The full pinned PR verifier remains to be refreshed on the final clean commit.
No public read, clone, payment, database migration, secret access or other
external action occurred.

## F6 local UI and operations verification — 2026-09-29

Route `26ffb293d4ff` and change package
`engineering/changes/20260929-f6-local-ui-and-operations-verification-26ffb2/`
have completed the four route-selected read-only analyses. The approved design is
strictly local: a deterministic browser harness with fake EIP-1193, same-origin
API, storage, crypto, timers and test-only adapter; the smallest injectable UI
seam; fixture-egress correction with resolved-profile assertions; internal-only
metrics observability; the canonical restrictive CSP; and exact README,
runbook, handoff and acceptance truth.

The repository owner re-approved current exact scope digest
`20d2f1aae1a80242fa6b178e0416a1831dee03948c7f740cadf3ecea6a1ccb99`
after the typed evidence paths changed,
and the package is `approved`. The recorded migration plan is explicitly a
no-op: this phase does not start containers, create a database/schema/volume,
or perform an external write. Any later need for those actions stops for a new
exact approval.

The implementation adds production-used browser policy and orchestration seams
with fourteen deterministic Node scenarios for wrong chain/switch, payer-preserving account
and chain changes, typed pre-submit cancellation, ambiguous outcomes, exact
reload request/idempotency identity, fixture gating, and one-call
no-resettlement. The orchestration harness records the real recovery/payment
decision path through fake API, session persistence, notices, wallet events,
and adapter calls. Wallet events now bind through a provider-to-state-sink
module whose production dependency surface has no payment callback; account or
chain events can only refresh wallet state. A wallet revalidation failure is
handled before the guarded submission try: it preserves the clear guard,
persists nothing, invokes no adapter, and renders a no-payment warning.
The production composition is structurally locked to the direct state-only
sink call, so wrapping an event with `submitPayment` fails the focused suite.
A provider rejection now applies fail-closed disconnected state without an
unhandled rejection, resolves the serialized event queue, and permits the next
wallet event to recover normally. Four static operations tests resolve both Compose profiles
and assert exact services, networks, loopback publication, per-profile secret
identity, exact users/tmpfs/mount modes/resources, healthchecks, internal
metrics, and CSP. Fixture capture,
gateway, and edge no longer inherit live egress networks. Gateway metrics bind
only to `gateway-metrics` on an internal operations network, accept only
`GET /metrics`, and have no host/Caddy route. Two executable gateway telemetry
tests assert the exact label-free metric set, no high-cardinality identifiers,
404 for other paths, and readiness independent of health. Caddy sends the exact
canonical restrictive CSP including `frame-ancestors 'none'`, without
`unsafe-inline`; source HTML has no incompatible inline script/style.

The exact web install/build is not yet evidenced: an offline
lifecycle-disabled install stopped because the exact Vite 7.1.5 tarball is
absent from the local npm cache, and this no-external route does not authorize
a registry request. The first full pinned verifier completed its checks but
could not record a receipt because the typed spec used symbolic test labels;
v2.0.19 requires existing repository paths. Those evidence references now
point to the real browser and operations test files. A clean rerun and
independent route reviews remain next. The subsequent full run reached the
Python suite and exposed only missing architecture-inventory ownership for the
new F6 package and tests: 1153 tests and 85 subtests passed, while five graph
policy tests failed on the undeclared paths. The inventory now binds every F6
package file and both new test/source artifacts; the exact five-test graph
regression slice passes, and the repaired tree then passed the full pinned PR
verifier before the first reviews. Those reviews correctly rejected helper-only
browser coverage and shallow operations assertions. The current repair binds
the harness to production `resumeFlow`, `submitPayment`, and wallet listeners;
it also closes exact Compose, telemetry, and CSP mutation gaps. Final clean
HEAD `f1667511149c5062443cd2c518ce40d8492b7507` passed the full pinned verifier
at fingerprint `292558635bb303d8cf302468899eba4ac82d2d742ccff8e4939e8cfe886c970b`.
Independent code, test, security, data, and release reviewers all returned
PASS with no findings on that exact fingerprint and did not modify the tree.
Their reports are stored and registered, and the package advanced through
`verifying` and `reviewing` to `ready` with `evidence_gaps: []`. The tracked
state-close commit requires one final verifier and receipt refresh. Production's
x402 adapter remains deliberately unregistered and fixture payment remains
fail closed. This route will not use a real wallet, RPC, facilitator, transfer,
testnet/mainnet payment, live capture/profile, shared environment, deployment,
release, exchange mutation, or push. Static evidence cannot establish runtime
A26 acceptance: all 156 frozen vectors and A26/A30 remain `NOT_RUN`; A13/A14
remain externally blocked.

## F5 local mocked state-machine verification — 2026-09-29

Route `583d09e0cf44` and change package
`engineering/changes/20260929-f5-local-mocked-state-machine-verification-583d09/`
are implementing a strictly fake-only Node vertical with no database, migration,
RPC, facilitator, wallet, transfer, exchange, deployment, release, or push.
Four read-only analyses froze the scope; route `c3dad647a9f8` was cancelled
before implementation because keyword routing attached inapplicable external
write gates to the same local-only intent.

RED tests reproduced that an authoritative confirmation rejected by
`Ledger.confirm` as `PAYMENT_REJECTED` remained ordinary uncertainty in both
`Gateway.read` and `reconcileOne`: neither entered manual review immediately.
The minimal repair distinguishes a confirmation already observed from earlier
payment failures and treats only its binding rejection (plus the existing
manual-review error) as frozen `inconsistent_receipt` evidence. Both paths
retain the fail-closed 202 response, enter paired `MANUAL_REVIEW`, create no
entitlement or delivery, and never settle again.

Nine deterministic scenarios execute real gateway/reconciliation/recovery
orchestration with a structural in-memory ledger, scripted payment port, and
per-test temporary artifacts: direct and reconciled mismatch, post-submit lost
response and HTTP replay, canonical duplicate use, stale verified pre-submit
recovery, bounded null-confirm reconciliation, packaged frozen-state guards,
successful confirm-only reconciliation, entitlement reuse, and reorganization
withholding. The worker success case asserts terminal `CONFIRMED`/`PAID`, one
entitlement, ordered `unknown -> confirm -> CONFIRMED event`, zero settle or
delivery, and no second eligible lease; this kills the test-reviewer's late
`unknown` mutation. After the first reviewers
rejected the original no-op contract double, the fixture now loads production
`Contracts` and packaged `states.json`; it validates receipt shape, a valid
scoped transition, and an unmet-guard `INVALID_STATE`. Reconciliation models
the count returned by the leasing update, records `PAYMENT_UNCERTAIN` below ten
and `MANUAL_REVIEW` at ten, and mismatch tests assert ordered trace plus absent
delivery so the earlier review mutation is killed. The focused file passes 9
tests; the complete gateway suite passes 15 and skips the five
explicitly disposable-PostgreSQL F4 cases when no database URL is supplied.
`MANUAL_REVIEW -> PAID/CONFIRMED` recovery remains an explicit residual: the
worker cannot lease that state and the adapter lacks an idempotent restore-only
operation, so this route does not mock a false PASS. Production identity and
finality remain unresolved, and all 156 frozen vectors remain `NOT_RUN`.

Pinned full verification passed clean implementation HEAD `72ba728092e4041ba0b37f23baa5c6373dbd28f9`
with fingerprint `b467a6f9c3312a70f0a7ae946750c1a5405afa29e6bdab7509e8aaac482c2db1`:
1155 pytest tests and 85 subtests passed together with change-spec, diff,
secret, contracts, SQL, nine Trivy targets, Ruff, Bandit, coverage, and source
stability. Independent code, test, and data reviewers all returned PASS with
no findings on that exact fingerprint and did not modify the candidate. Their
reports are stored in this change package and were registered after the
report-bearing tree passed full verification. With no human gate, the durable
package advanced through `verifying` and `reviewing` to `ready`. The tracked
state-close commit requires one final verifier and receipt refresh on its exact
fingerprint. Do not infer testnet payment, persistence, acceptance, deployment,
or release readiness.

The pre-review pinned verifier execution completed its configured checks but could
not record a receipt because the new typed acceptance entries used the
unsupported key `verification`; the v2.0.19 schema requires `evidence`. After
that correction, the verifier correctly rejected the superseded red-risk
package's untouched generated `UNKNOWN` placeholders even though its lifecycle
state was cancelled. Both packages now have schema-valid typed evidence; the
superseded package remains cancelled and grants no approval. The corrected
packages passed exact validation in the final verifier.

## F4 local gateway and ledger verification — 2026-09-29

Route `725677143509` and change package
`engineering/changes/20260929-f4-local-gateway-and-ledger-verification-725677/`
are `approved` with no human gate. Five route-selected read-only analyses agree
on the bounded implementation: repair the two reproduced TypeScript build
errors, add a gateway-owned Node test harness, and prove cleanup/idempotency
semantics against loopback HTTP and a uniquely disposable PostgreSQL database.

The confirmed recovery defect is cross-component, not schema-level: the report
service documents HTTP 200 `deleted:false` as authoritative already-absent
success after a lost response, while the gateway currently accepts only
`deleted:true`. The adapter regression reproduced that mismatch and acceptance
of an unknown field. The minimum repair now accepts either boolean only in an
exact matching two-field HTTP 200 body. The two reproduced TypeScript errors
are repaired. A test-review P1 then exposed missing executable coverage for
the adapter's internal deadline: the test-first loopback run accepted a valid
response delayed beyond an injected 20 ms deadline because the constructor
still hard-coded 2000 ms. `HttpReportService` now accepts a typed injectable
cleanup timeout while retaining 2000 ms as the production default. The focused
suite reports 6 passes and 5 explicit disposable-PostgreSQL skips, including
fail-closed internal-deadline and caller-abort subtests; typecheck and build
also pass.

The first disposable PostgreSQL run passed migration/rerun and 20-way
idempotency, then exposed SQLSTATE `42703`: migration 001's shared immutable
identity function dereferences `OLD.tx_hash` for an artifact row, preventing
the intended `AVAILABLE -> DELETED` update. The user explicitly answered
“Делай”, approving only the required forward-only 002 function repair and
local disposable verification. Migration `001_ledger.sql` and the frozen
vector catalog remain byte-identical. The repaired disposable suite reports
five passes: fresh 001-to-002 and rerun, 001-only upgrade, 20-way idempotency,
fail-closed recovery, and lost-response convergence with artifact/payment
immutability checks. No dependency upgrade, other migration,
shared database, facilitator, RPC, wallet, chain, exchange, live capture,
deployment, release, or payment action is in scope. The next step is the pinned
route-selected independent code, test, and data reviews.

The pinned v2.0.19 full verifier previously passed clean implementation fingerprint
`55e3ce270b2cdc118ced8ca3daa9ab0bdab59e43`: all diff/spec/secret/contract/SQL,
nine Trivy, Ruff, Bandit, 22-worker pytest, coverage, and source-stability gates
passed. The timeout repair changes that fingerprint; its pinned full verifier
is therefore run only after the coherent repair is committed and clean. Runtime
status is authoritative, and no receipt is treated as current across a tracked
change. Independent code, test, and data reviewers then returned PASS with no
findings on clean HEAD `587bf5c0a5edd1712c4cd3cd3e4ade258fff8ffe` and tree
fingerprint `e88d85fbe2da4789b634f5d2c88bf73beeb9740274c566ba06297f8c1cb4c83b`.
Their coordinator-provided reports are persisted in the active change evidence
directory and registered in the architecture inventory. The report-bearing
tree passed pinned verification, and its exact report paths were recorded as
PASS receipts. With no human gate, the v2.0.19 change CLI advanced the durable
package through `reviewing` to `ready`. That tracked state-close change makes
the preceding receipts stale by design, so the verifier and all three review
receipts are refreshed once more after this commit. The implementation owner
does not self-review.

## F3 offline artifact verification repair — 2026-09-29

Route `08fa9d84745d` and change package
`engineering/changes/20260929-f3-offline-artifact-verification-repair-08fa9d/`
are `ready` with no human gate because the scope is fixture-only and explicitly
forbids migrations and external writes. The superseded broad route
`f6f2495b4648` was cancelled before implementation: its task wording introduced
an inapplicable migration/external-write gate even though its approved scope
excluded both. Four read-only analyses are retained in the active package.

Implementation remains limited to failing-regression-first coverage of the
installed canonical F3 fixture-to-report/bundle/publish/verifier loop, tamper rejection,
duplicate report UUIDs, incomplete publication, packaged resources, and the
confirmed acceptance contract defect. A regression first reproduced rejection
of the runner's real 40-character Git OIDs; the schema now uses a dedicated
40-hex `git_oid` definition while true content digests remain 64-hex SHA-256.
Canonical source tests cover exact build/publish/read/verify, bundle and report
tamper, matching and differing duplicate UUID publication, partial targets, and
pre-rename verification failure. A no-index wheel test installs all four local
packages into an isolated environment, proves imports come from that install,
then exercises both installed F3 commands outside the checkout. The new focused
slice reports 13 passed; the surrounding capture/analyzer/contracts slice
reports 738 passed and 85 subtests. The full PR verifier exposed and now has
repairs for whitespace, typed evidence paths, and graph inventory ownership of
the new package/tests. The final committed-tree run passes diff, both change
specs, secret, contract, SQL, all nine Trivy targets, Ruff, Bandit, and source
stability. The apparent parallel factory/import collisions were reproduced and
are not shared-state races: the failing command used `/usr/bin/python3`, which
lacks the project packages and Hatchling. The same complete 20-test factory,
installation, and canonical F3 slice passes with 22 workers in the pinned local
environment. Hyperliquid SDK 0.24.0 declares `eth-account>=0.10.0,<0.14.0`, and
the provisioned compatible version is 0.13.7, so the stale project pin was
repaired from 0.14.0 to 0.13.7; its characterization and `pip check` now pass.
The final full verifier run from the pinned environment passes: 22 workers ran
`1147 passed, 85 subtests passed` in 67.24 seconds, coverage passed, and diff,
both change specs, secret, contract, SQL, all nine Trivy targets, Ruff, Bandit,
and source stability are green. A final receipt refresh after this handoff
commit is required; route-selected independent code, test, and data review is
the next coordinator action and has not been performed by the implementation
owner.

The first independent code and test reviews then found that JSON Schema's `$`
accepted a terminal newline and that malformed `repository.tree` values lacked
negative coverage. Both `git_oid` and `sha256` now combine their lowercase-hex
patterns with exact `minLength`/`maxLength`; commit and tree share the complete
short, long, uppercase, non-hex, and terminal-newline matrix, while stdout,
stderr, and evidence digests each reject terminal newlines at their exact error
paths. The repaired focused slice reports `21 passed`. The original FAIL review
reports are preserved as evidence; full verification and independent re-review
must bind the new tree before closure. The first post-review full run otherwise
passed 1150 tests and coverage, but correctly rejected the three newly tracked
review reports until their graph inventory ownership was declared.

Independent code, test, and data re-reviews all PASS the repaired candidate
`a24e1ed` at fingerprint
`1e8ebe8852e4d569f7a4c6cf4b9a6a7618f540a5ee923a5bebbd0e6a81b67957`
with no open findings. Their complete reports preserve the original failures,
the repair probes, scratch identities, and `reviewed-tree-modified: no` claims.
The final reports were persisted in `8fc0d3b`; the pinned verifier then passed
`1155 passed, 85 subtests passed` in 66.13 seconds, plus coverage and every
configured PR check. The package progressed through `verifying`, `reviewing`,
and `ready`. Because those durable transitions change the tree fingerprint,
the untracked runtime verification and review receipts are refreshed once more
after committing this state; `scripts/grok_status.py` is authoritative for
their fingerprint currency.
Gateway/F4 through F7, graph orphan cleanup,
network, database, RPC/facilitator/wallet/payment/exchange actions, Compose
start, deployment, release, and push remain outside this route. All 156 broad
acceptance vectors remain `NOT_RUN`.

**Market reports you can verify.** Built for [MEZO ₿](https://mezo.org/) —
[The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

## Repository boundary cleanup — 2026-09-28

Branch `chore/repository-cleanup` is an isolated worktree based on merged main
commit `0c2cb97f8048f7da8bd193634f4502f24b0e541e`. Route
`7f0f98e3cdda` and change package
`engineering/changes/20260928-repository-boundary-cleanup-7f0f98/` cover a
repository-only retirement of inherited Go Stage-0 and vendored agent tooling.
Six parallel read-only analyses and the route-selected implementation are
complete. Full route verification passed at clean fingerprint
`aa5925f320da68843a52362e1654549d3a658899`. Independent code, test, security,
and data re-reviews all passed that same fingerprint with no findings; their
reviewer-provided summaries are stored under the active change package. The
v2.0.19 change CLI advanced the durable package through `approved`,
`implementing`, `verifying`, and `reviewing` to `ready`; no human gates are
declared. It generated and mirrored a clean implementation checkpoint at
`f7401a903d53c8ecb34415ce474a63f110a4ccdb`. These transition-only repository
changes make the five pre-transition receipts stale, so final verifier and
independent-review refresh remains pending for the state-close fingerprint.
No product runtime, payment, deployment, release, or acceptance status has
changed.

The retired Go unit is `go.mod`, `cmd/`, `internal/`, the root Go
`Dockerfile`, and the historical Stage-0-only `migrations/000001_init.*`.
Its five useful safety invariants remain covered by Python characterization
tests and the immutable public import commit
`8734907d489168a8a6567b93bc85920001fefd85`. The A2
`migrations/000002_a2_raw_capture.*`, gateway ledger, SQLite demo, schemas,
vectors, fixtures, and `provenance/import-manifest.json` remain unchanged.

BMad is externalized at the exact `bmad-method@6.10.0` npm identity and SRI in
`tooling/tooling-lock.json`; no BMad factory payload remains copied into the
repository. Adaptive Grok is a portable gitlink at
`tooling/adaptive-grok-build-pro`, pinned to local tag `v2.0.19` and commit
`cb9af4073ba6c3d515145164d771c75ebdfa3224`. Version 2.0.19 was chosen
specifically for its bounded parallel pytest verifier; the older releases run
the suite sequentially and are materially slower. Both project-owned execution
entrypoints fail closed unless the gitlink, HEAD, tag, VERSION, and clean
checkout all match the shared lock validator. Hooks no longer synthesize
allow/empty output after validation failure; thin symlinks preserve hook and
skill discovery without copying framework source.

Ordinary product/conformance tests validate the static lock and gitlink and do
not require an initialized submodule. The separately invoked
`make verify-tooling` suite exercises the initialized runtime, missing,
wrong-lock, wrong-HEAD, and dirty/untracked states, direct execution, hooks,
and dynamic Trivy discovery. A final security re-review then demonstrated that
Git's `assume-unchanged` flag could hide modified verifier bytes from status.
The shared validator rejects all index optimization/state flags globally and
hashes the explicit runtime/instruction trust closure against HEAD, including
engine, Grok scripts/hooks/config/templates/agents/skills, root policy, and the
two change-spec schemas loaded by `spec.py`. It also rejects ignored importable
code in Python execution roots. Historical
packages, distributions, and release evidence remain subject to global
dirty/untracked detection but are not reread for every hook. The bounded
closure contains 179 files / 1,241,709 bytes (limits: 256 / 2,000,000), reducing
warm launcher validation from 0.67 seconds to 0.13–0.16 seconds. Entry points
disable bytecode generation so validation does not create its own ignored
code. The final focused aggregate reports `282 passed`, including 21 strict
tooling cases. The graph CLI still reports only the inherited 26
`IMPLEMENTATION_ORPHAN` findings plus six active declared conflicts; it has no
cleanup-specific inventory, dangling-reference, or retired-Go error.

A local `git clone --no-recurse-submodules` of implementation commit
`058092d2c243d732eb4a44d876a46ae98b64c102` passed the ordinary repository
boundary suite: `8 passed`. This proves fresh ordinary checks do not require an
initialized Adaptive Grok checkout; strict runtime checks remain explicit.

An isolated repository-local `.venv` supplies the exact v2.0.19 runner
versions and declared build backend without changing the global interpreter.
The stale README heading and public-capture metadata expectations are repaired.
A complete-inventory 22-worker measured diagnostic reports
`1134 passed, 85 subtests passed` and 36.16% branch-aware coverage across
10,413 statements. The denominator includes all tracked Python below
`packages/`, `scripts/`, `tools/`, and `tooling/`, including zero-covered owned
modules; it omits only tests, the eight external Grok symlink entrypoints,
generated build paths, and the pinned submodule. The prior 59.18% result is
invalid because it omitted owned scripts, standalone tools, and project-owned
tooling. The truthful initial floor is 36%, the integer below the observed
result; it must not regress and is roadmap debt to raise with targeted tests.
The full PR verifier passed the committed denominator baseline at fingerprint
`aa5925f320da68843a52362e1654549d3a658899`; the recurring
gate dynamically found nine tracked container inputs (seven Dockerfiles and
two Compose files) and passed all at the explicit
`MEDIUM,HIGH,CRITICAL` threshold. A separate LOW audit retains the inherited
`DS-0026` missing-`HEALTHCHECK` finding on each Dockerfile. Four route-selected
independent re-reviews passed with no findings. Their reports are stored. The
durable change package is now `ready`; its transition-only fingerprint still
requires a final verifier and review-receipt refresh before closure.

F3 is locally verified and `ready`; F4 has focused local evidence but awaits
full verification/review. F5–F7 remain `IMPLEMENTED_UNVERIFIED`; all 156
vectors remain `NOT_RUN`,
A13–A14 remain `BLOCKED_EXTERNAL`, payment readiness remains false, and no
testnet payment, deployment, release, or publication is claimed.

## Current state and next action

F1 is **complete-with-blockers** and F2's static contract phase is complete.
F4 is **FOCUSED-VERIFIED / ROUTE-UNVERIFIED** and F5–F7 remain
**IMPLEMENTED_UNVERIFIED**. The accepted
[ADR-0002](docs/adr/0002-liqvera-report-payment-boundary.md) fixes only runtime,
ledger, immutable-artifact, and testnet authority. It does not freeze API
payloads or database schemas and does not authorize payment or release.

The integrated tree now contains:

- pinned official `mezo-org/musd` material plus recorded `mezod` and
  documentation revisions in `packages/mezo-protocol`;
- fixed public Hyperliquid capture, strict evidence inspection, exact report
  assembly, deterministic bounded bundles, offline verification, atomic
  publication, and internal capture/report services;
- the F2 Express API, PostgreSQL ledger/migration, capability and idempotency
  boundaries, immutable artifact adapters, reconciliation/retention workers,
  and official x402 adapter boundary;
- the Mezo Testnet Vite browser application, isolated Compose/images, Caddy,
  environment examples, secret-file conventions, and operations runbooks;
- the result-producing A01–A30 acceptance runner and honest competition
  drafts; and
- exact architecture inventory bindings plus separate `liqvera-python`,
  `liqvera-gateway`, `liqvera-web`, `liqvera-images`, `liqvera-compose`, and
  `liqvera-acceptance` targets. Existing `wheels`/`product` Stage A semantics
  remain the original three Python distributions and two images.

The earlier fixture MVP evidence remains historical and unchanged: its focused
slices reported 6 builder, 6 CLI/bundle, and 3 demo-contract tests passing;
`make mvp` exited 0 for BUY `0.15`, VWAP `1.1`, notional `0.165`,
`snapshot_status=SIMULATED`, and `execution_authority=NONE`. That run produced
report SHA-256 `998ada1362a523f8abfbbddd26bd43f04d08a5d0388c35837fc084c215dcf0f3`
and ZIP SHA-256 `e320026264d42046b39650a7e1376430891ece631dd722a6f160603db449fda1`.
It does not verify the newer canonical F3–F7 code or factory integration.

The evidence-report wheel now carries its schemas, SQLite demo migration,
runtime dependency declaration, and local demo web assets. Gateway builds copy
their schema and migration resources; web builds retain their Vite-owned static
bundle. Gateway and web `package-lock.json` files were generated using
`npm install --package-lock-only --ignore-scripts`; no `node_modules` trees or
build outputs were retained. The current gateway audit observation is 32
advisories (28 moderate, 4 high); the retained web observation is 31 (27
moderate, 4 high). These
counts are unresolved audit input for the deferred verification phase, not a
security acceptance result.

Per the owner's instruction, no graph command, Python test, typecheck, wheel or
web build, Docker build, Compose render/start, acceptance execution, live
capture, facilitator/RPC mutation, testnet payment, Grok receipt, independent
review, deployment, release, or push ran for this code-completion integration.
The next action is the deferred verification and defect-repair phase in
dependency order: factory/resource builds, typechecks, graph, focused/full
tests, browser, Compose/security/fault checks, then separately authorized live
acceptance.

Payment remains deliberately disabled. `PAY_TO_MISSING`, canonical
authorization identity, facilitator compatibility, `FINALITY_RULE_UNVERIFIED`,
funded buyer/signature/receipt evidence, and inherited Trivy findings remain
open. All 156 vectors remain `NOT_RUN`; A13–A14 remain `BLOCKED_EXTERNAL`.
Fixture reports remain `SIMULATED`, non-chargeable, and
`execution_authority=NONE`. Unknown settlement remains `PAYMENT_UNCERTAIN`,
and no second payment may be offered.

The owner approved the repaired [F2 implementation plan](docs/superpowers/plans/2026-09-24-liqvera-f2-contracts.md)
after its independent re-review at `50f16225c23f5fde046b483321f86bb7d6bbf4f1`
and authorized parallel implementation in isolated task worktrees. The six
artifact slices and Task 1/3 review repairs are now integrated in task order;
one integration owner maintains the shared graph, handoff and task records.
The published contracts cover closed schemas/OpenAPI, public reasons,
request/quote/payment/delivery states, exact BUY/SELL vectors, and payment
atomic-unit/idempotency/auth obligations. They add no runtime service.

Task 1's three Important numeric-semantics findings and Task 3's HTTPS
evidence-reference finding passed scoped re-review after repair. Task 2 was
approved. Task 4's artifacts were found coherent; integration supplied its
shared graph/handoff bindings and verified state/vector linkage. Task 5 was
approved with one Minor wording issue;
the 202 description now says "without paid report fields" and retains the
JSON recovery error body. Its existing response-schema assertion covers that
body, so no prose-matching test was added. Task 6 review found one Important
gap in validating the on-disk vector envelope; its test-only repair is now
integrated. Integration also reproduced and repaired a state-schema symbol
pattern that rejected its own `report_sha256` field, adding full document
validation and unsafe-name regressions. Both repairs were included in the
reviewed integration snapshot.

Independent whole-branch review of `644cb702ae879b9d7c8acac1039eb8c5bf37d2aa`
identified cross-contract safety/standards gaps. The consolidated repair adds
evidence GET 202 recovery, expired-quote 410 after scope checks, fixture-source
rejection after more specific reasons, eligible-only quote previews, exact UTC
fractional expiry comparisons, unresolved reencoded-authorization assertions,
mathematically integral JSON number validation, and coherent readiness gates.
The approved plan now reflects those corrections; simulated offline reports
remain valid and no runtime layer or SDK identity rule was introduced.

F2 is **static-contract complete**. The fixture CLI, local browser MVP, and
separate Liqvera factory are integrated; verification, hardening, and defect
cleanup remain without treating implementation as canonical F3 acceptance.
The [final F2 evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md)
binds implementation `3729bdc131ca4ac971ab04e735da2e113d68ad71`, tree
`155d7fb44f5953f814f5463c381dde14932a8ab3`, and fingerprint
`2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a`.
This closure commit changes documentation only; it does not rebind product
verification to its own future hash or manufacture a factory receipt.

Independent session/subagent code, security, edge and acceptance reviews all
APPROVED the final implementation with no remaining findings. Code/security/
edge inspected `74a7b6f..3729bdc`: code ran 65 focused tests (65 deselected),
security 78 (52 deselected), and edge 79 plus six boundary probes; all passed
their diff checks. Acceptance inspected the clean final SHA/tree, recomputed
the fingerprint and verified scope/status/count logs. These results were
consolidated by the coordinating agent; no separate final-review report files
or repository-local receipts exist, and the writer did not self-approve.

All 156 vectors remain `NOT_RUN`. A02–A06/A10–A12/A15–A20 remain `NOT_RUN`;
A13–A14 remain `BLOCKED_EXTERNAL`. Payment readiness remains false, with
PAY_TO_MISSING, FINALITY_RULE_UNVERIFIED, funded buyer/signature/receipt,
SDK/canonical authorization identity and inherited Trivy blockers unchanged.
No runtime acceptance, payment, deployment, release or push is claimed.

Documentation-only closure checks passed: `git diff --check`, `make graph`
(the same seven inherited conflicts), all 226 graph tests in 20.09s, and
balanced-fence/local-link checks across five Markdown files (18 local links).
The implementation fingerprint is unchanged. No new full-suite or Grok run
is claimed for this documentation-only commit.

Edge re-review of `74a7b6f25ea4fe947eca5748481ee247aa1c8f32` found that
readiness still admitted payment_ready=false without a blocker explanation.
The micro-fix adds the missing nonempty-blocker constraint and corrects the
truth table; the focused regression and eight affected combinations failed
before implementation. Healthy future readiness remains representable and
the final scoped re-reviews confirmed this finding is addressed.

Readiness micro-fix verification: targeted RED exited 1 with nine failures,
56 passes and 65 deselected in 1.70s; GREEN exited 0 with 65 passes and 65
deselected in 1.58s. Resource tests passed 130 in 38.40s; all six F2 modules
passed 446 in 193.52s. `make verify` passed 1087 tests and 85 subtests in
326.32s; bare pytest passed the same counts in 327.91s. Graph (the same seven
inherited conflicts), Ruff and diff checks exited 0. Grok `--mode pr
--no-record` exited 1 only for inherited Trivy; all other applicable checks
passed, with coverage explicitly skipped by runner policy. Direct Trivy
again found exactly two inherited LOW DS-0026 Dockerfile findings (exit 1).
The stable pre-verification-record staged tree was
`a6598b786db2ac3b5bf60457c3c69e127df14f1b`; its graph/schema/test index
fingerprint is
`2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a`.
Only verification prose changed afterward. Runtime remains NOT_RUN and no
new unresolved failure or factory receipt is claimed.

### Historical repair waves — not current receipts

Scoped review of `fd672f89c6bde8d1b1170b2e7a8c631ebed4d793` found three
remaining edge cases. The final follow-up now binds the reencoding scenario
and flag in both directions, preserves exact timestamp fractions beyond
Python's decimal-string integer conversion limit, and closes readiness truth
tables in both directions. Capabilities require an explanation when blocked
and cannot report payment readiness for fixture data; overall readiness must
equal all gates plus no blockers. The targeted regressions went from eight
failures to 77 passes. Code/security/acceptance approved `74a7b6f`; edge
identified the final blocker-list issue fixed and approved at `3729bdc`.
The historical counts below do not replace the final implementation evidence.

Final follow-up verification on 2026-09-24: targeted RED exited 1 with eight
failures, 69 passes and 118 deselected (5.23s); GREEN exited 0 with 77 passes
and 118 deselected (5.19s). Both affected modules passed 195 tests in 189.25s;
all six F2 modules passed 445 in 195.59s. `make verify` passed 1086 tests and
85 subtests in 328.48s; bare pytest passed the same counts in 329.68s. Graph
(the same seven inherited conflicts), Ruff and diff checks exited 0. Grok
`--mode pr --no-record` exited 1 only for Trivy; every other applicable check
passed, with coverage explicitly skipped by existing runner policy. Direct
Trivy exited 1 for exactly the two inherited LOW DS-0026 Dockerfile findings.
The stable pre-verification-record staged tree was
`8fb46171a70190217b60170eb50967da52955f40`; its graph/schema/test index
fingerprint is
`a5654aacb56cce7d1087f6df000ea14dba97c6fa0d17da2920aa366b607cc84a`.
Subsequent changes only record results in continuity prose. No new failure,
factory receipt, runtime acceptance or external mutation is claimed.

Consolidated repair verification on 2026-09-24: the new focused regressions
first failed as expected (23 failed, 16 passed, 219 deselected), then passed
(39 passed, 219 deselected in 5.87s). The final six-module contract suite
passed 368 tests in 191.16s. `make verify` passed 1009 tests and 85 subtests in
322.79s; bare pytest passed the same counts in 323.83s. Graph, changed-Python
Ruff, and staged/unstaged diff checks passed. Grok `--mode pr --no-record`
exited 1 only for Trivy, with every other applicable check passing and coverage
explicitly skipped by runner policy. Direct Trivy again found exactly the two
inherited LOW DS-0026 findings. No new unresolved failure or receipt exists.

The stable pre-verification-record staged tree was
`c4a5bd7764e3b65def7251064b7f1a0739bd9fa5`; the graph/schema/test index
fingerprint (using the command in the existing evidence draft) is
`a6c58a366d7b0354013f615f93a41862d4d34416d07a30212fc9bd514565cf7a`.
Later edits only recorded verification in continuity prose; the final approval
and evidence binding above supersede this historical repair snapshot.
Runtime acceptance stays `NOT_RUN`, with
A13–A14 `BLOCKED_EXTERNAL`; F1 payment/finality and Trivy blockers remain.

Pre-repair integration verification on 2026-09-24 passed `git diff --check`, `make graph`
(the same seven declared conflicts), changed-Python Ruff, all six F2 contract
modules (329 passed in 179.24s), `make verify` (970 passed and 85 subtests in
311.17s), and bare pytest (970 passed and 85 subtests in 311.25s). Grok PR
verification with `--no-record` exited 1 only for Trivy; every other applicable
check passed, zero potential secrets were reported, and coverage was skipped
by runner policy. Direct Trivy inspection confirmed exactly two inherited LOW
DS-0026 findings. No waiver or artificial healthcheck was added. See the
[F2 evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/f2-contracts.md)
for the final artifact fingerprint and historical isolated-task results.

Planning verification: `git diff --check`, authoring-placeholder scan and
`make graph` passed for the repair; graph
verification retains the seven inherited declared conflicts. The new plan has
an exact DOCUMENTATION inventory binding. No product files changed and no
new `make verify`, Grok receipt, runtime acceptance, payment, or release result
is claimed by this planning step.
The repair's 11 JSON snippets parse; all nine primitive patterns reject the
four tested trailing line terminators (LF, CRLF, U+2028 and U+2029). These are
plan-snippet checks, not implemented API or payment acceptance.
Documentation-only review closure also passed `git diff --check` and
`make graph`, with the same seven inherited declared conflicts.

The full delivery sequence is contracts → verifiable report → API/ledger →
testnet settlement → UI/operations → acceptance. The canonical specification
is `docs/planning/LIQVERA_FACTORY_TZ.md`; its legacy filename remains a
compatibility pointer. Preserve inherited `mee-*` names.

No active `.grok-stack/runtime/active-route.json` exists in this public
worktree. `grok_status.py` reports null route/change and no receipt gaps,
which is not factory approval. No factory receipt was created or claimed.
F1 Tasks 1–5 and the final whole-branch transport repair passed independent
review. No Critical or Important finding remains open from F1.

## Verified F1 implementation

Evidence is bound to literal implementation SHA
`37d3e2cf3c64ef2c5d260bccf64e4f107e3f2c25`, captured before the refreshed
closure documentation edits. The rewritten implementation commit passed a
clean detached-worktree verification before 18:25:49Z. See
[F1 verification](engineering/changes/2026-09-24-mezo-evidence/evidence/f1-verification.md)
and [compatibility result](engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json).

Fresh commands on 2026-09-24:

| Command | Exit | Result |
| --- | ---: | --- |
| `PATH="$PWD/.venv/bin:$PATH" make verify` | 0 | 641 tests, 85 subtests; Stage A verification passed |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record` | 1 | Only Trivy failed; all other applicable checks passed; coverage explicitly skipped by runner policy |
| `trivy config --exit-code 1 .` | 1 | Exactly two LOW DS-0026 missing-HEALTHCHECK findings |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py --lock docs/compatibility/mezo-evidence-v1.json` | 0 | COMPATIBILITY_PASS_PAYMENT_BLOCKED |
| `.venv/bin/python -m pip check` | 0 | No broken requirements |
| `PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/compatibility/test_mezo_compatibility.py -q` | 0 | 107 focused tests |

Python 3.12.3, pytest 9.1.1, Hatchling 1.32.4. npm is not used by the probe.
Seven inherited declared graph conflicts remain; the precommit graph check
permits their explicit declaration and does not resolve them.
The exact architecture inventory, focused Ruff checks, and `git diff --check`
passed against the implementation tree. Existing DOCUMENTATION bindings are
unchanged. Final review found no remaining Critical or Important issue.

PR integration merge `94cb8ab2ccba21dfcb8c902814ed3728ba42ab7d`
incorporates the English-documentation baseline from `origin/main`. A fresh
`make verify` passed 641 tests and 85 subtests in 129.26 seconds. The Grok PR
profile reported zero potential secrets and passed every applicable check
except the already named Trivy policy blocker. The synthetic proxy credential
fixture is assembled at runtime; the Basic Auth-shaped literal and its old
introducing commit are absent from the rewritten PR history.

PR #2 (`feat/mezo-evidence-f1-impl` into `main`) is open and mergeable. The
local branch, remote branch, and pull-request head were verified at rewritten
pre-handoff snapshot `237ecbc21901ca7045663b090a537a1ad824a36d` after the
guarded force-push; later commits in this section only record that result.
GitHub reported `MERGEABLE`, and the rerun GitGuardian Security Checks
conclusion was `SUCCESS` (completed 2026-09-24T18:36:51Z). No PR merge was
performed.

## Active blockers and limits

- `BLOCKED_TRIVY_HEALTHCHECK_POLICY`: Trivy rejects both one-shot Stage A
  Dockerfiles for LOW `DS-0026`. Their CLI exit codes and Compose
  `service_completed_successfully` conditions express job completion.
  No long-running readiness contract exists. A meaningful policy decision
  requires separate scope and review; no artificial healthcheck, ignore,
  waiver, or severity filter was added. The full pipeline remains FAIL.
- `PAY_TO_MISSING`: no non-zero operator-owned merchant receiver supplied.
- `FINALITY_RULE_UNVERIFIED`: no approved finality rule or confirmation count.
- A funded buyer, signature, testnet transfer, and receipt evidence are absent.
  Payment readiness is false; A13–A14 remain blocked and other payment rows
  remain not run. Compatibility is public technical evidence only.
- Private salvage source commit
  `7fe6918690f8bc1da5826c67e3619de4126e4f54` remains unavailable. Public
  verification proves target bytes, not private provenance.
- Docker image builds, full clean-machine README/demo acceptance, and fresh
  anonymous publication checks were not run in Task 5. A28/A29 are not passed.
  F7 must rerun acceptance against its final commit.
- Public endpoints and SDK registry availability can change; later external
  unavailability must become `BLOCKED_EXTERNAL`, not an inferred pass.
- The live transport requires POSIX `setitimer`, the main thread, and no
  active caller real-time timer; unsupported contexts fail closed before I/O.
  It is a synchronous CLI probe, not a background transport service.

No payment, signature, private-source verification, factory receipt,
deployment, PR merge, tag, or release occurred during F1 closure. The F1
branch was pushed only to open and repair PR #2. Mainnet, custody, exchange
mutation, merchant private keys, user secrets, and exchange credentials remain
excluded. Shadow-only and the old Stage A verdict remain unchanged. Synthetic
timing and placeholder live identity still require F3.

## Completed F1 work and historical evidence

Initial public baseline `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a` failed:
four publication paths were absent from graph inventory, salvage required a
private Git object, and wheel tests lacked Hatchling. Its recorded suite had
504 passed, 5 graph failures, 6 wheel errors, and 85 subtests; artifacts passed.
[Initial evidence](engineering/changes/2026-09-24-mezo-evidence/evidence/source-baseline.md)
is preserved separately from the current results.

- Task 1, `37d193b`: exact publication/provenance inventory bindings and graph
  classification; 22 focused tests passed.
- Task 2, `14b2ea4` and `4f8b0d7`: closed-schema salvage manifest verifies
  four pinned target entries, including two entries for one reader file.
  Default result is `items=4 targets=verified source_objects=unavailable`.
  Strict mode requires actual source blob bytes; synthetic Git fixtures test
  missing/corrupt payloads without private objects.
- Task 3, `282616d`: pinned Hatchling 1.32.4 in the development extra,
  ignored local environment, and compatible `eth-account==0.13.7` with
  `hyperliquid-python-sdk==0.24.0`. The initial clean resolver rejected
  eth-account 0.14.0; the corrected clean install and pip check passed.
  The then-current suite passed 534 tests and 85 subtests.
- Task 4, `3c09b44` and `df70f93`: sanitized closed compatibility lock and
  stdlib probe. Review found ambient proxies, npm redirects, and incomplete
  HTTP framing. The approved repair uses four literal registry URLs,
  disabled proxies, redirect refusal, identity encoding, bounded reads, and
  strict Content-Length validation. 89 focused tests passed; final full
  suite at that point had 623 tests and 85 subtests. No npm subprocess/cache remains.
- Final review repair, `37d3e2c`: the public bytecode endpoint legitimately
  uses chunked transfer. A private strict response reader now limits decoded
  data to 2 MiB, framing to 64 KiB, and each framing line to 8 KiB; it rejects
  chunk extensions, all trailers, and malformed/missing CRLF. One 12-second
  total deadline covers connection/TLS, headers, body, and chunk termination,
  restores the prior signal handler, and creates no background worker.
  Real-wire regression RED was 10 failed/89 passed; the final focused suite
  has 107 tests and the full suite has 641 tests plus 85 subtests. The renewed
  live probe passed with byte-identical sanitized evidence and mandatory
  payment blockers. No release or payment gate changed.

The live probe confirms Mezo Testnet 31611, MUSD 18 decimals, x402 v2 exact,
SDK family 2.16.0, and BTC book sides with 20 levels each. It stores no raw
market values, HTTP bodies, credentials, or capabilities and never reads
`PAY_TO`. Its two payment blockers remain mandatory.

## Public snapshot continuity

F0 imported upstream technical snapshot
`4f6583f8590ea091d8a465de0c607e59bfe611a5` into independent public history.
The specification came from
`97f4c7c3b9e1783f4a898412b538a4d6310b902a` (upstream PR 55).
[PROVENANCE.md](PROVENANCE.md) and the import manifest preserve source hashes,
privacy transformations, publication checks, and scan limits. Upstream refs,
secrets, environments, and private history were not imported. Inherited
Actions were disabled at publication; F1 did not change remote settings.

The final F0 secret scan had two reviewed digest false positives and no
unresolved findings. Its publication checks are historical F0 evidence,
not current F1 application or payment verification. Root project metadata is
`0.1.0.dev0`; Stage A packages are `0.1.0`; no root VERSION file exists.
Historical documentation remains context; use this handoff, README,
the change package, runtime tests, and accepted ADRs for current state.
