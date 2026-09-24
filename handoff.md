# Liqvera — handoff

Updated: 2026-09-24 (F3–F7 code and factory integrated, verification deferred). Repository: `Dimkox/liqvera`.
Branch: `feat/full-factory` (stacked on verified F2 and the local MVP).

**Market reports you can verify.** Built for [MEZO ₿](https://mezo.org/) —
[The Mezo Buildathon](https://app.akindo.io/wave-hacks/OVOO0gdrVU8379D10).

## Current state and next action

F1 is **complete-with-blockers** and F2's static contract phase is complete.
F3–F7 are now **IMPLEMENTED_UNVERIFIED**. The accepted
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
build outputs were retained. Resolution reported 32 gateway vulnerabilities
(29 moderate, 3 high) and 31 web vulnerabilities (27 moderate, 4 high). These
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
