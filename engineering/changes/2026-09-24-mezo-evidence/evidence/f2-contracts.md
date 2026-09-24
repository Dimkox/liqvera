# F2 contracts evidence — static phase complete

Status: **F2 STATIC CONTRACT PHASE COMPLETE** on 2026-09-24. The overall change
remains `implementing`; F3–F7 are open and the next action is F3. This is
contract-consistency evidence, not runtime acceptance or a factory receipt.

## Approved implementation and binding

- Implementation: `3729bdc131ca4ac971ab04e735da2e113d68ad71`.
- Implementation tree: `155d7fb44f5953f814f5463c381dde14932a8ab3`.
- Graph/schema/test index fingerprint:
  `2dd9403812ddcb5b3780ae314626316ee2381e27addaf3511b2c20be83d7138a`.
- Branch: `feat/mezo-evidence-f2-contracts`, stacked on F1.
- Worktree: `/home/pall/projects/liqvera/.worktrees/mezo-evidence-f1-impl`.
- Environment: Python 3.12.3, pytest 9.1.1, Ruff 0.16.8; `.venv/bin` first on PATH.

This closure is a subsequent documentation-only commit. Verification and
independent approval bind the implementation SHA/tree above, not a future
closure commit containing its own hash. The implementation bytes remain
unchanged; the fingerprint was recomputed for closure. No factory receipt
was generated, and the absent active route was not replaced with an invented
one. Prior integration/consolidated/follow-up results below are historical,
not current receipts.

Closure documentation checks: diff checks and `make graph` passed; all 226
graph tests passed in 20.09s. A read-only Markdown check found balanced code
fences in all five changed documents and 18 existing local link targets. No
dedicated repository Markdown/link checker was present. No full-suite or
Grok rerun is claimed for the documentation-only closure.

```bash
git ls-files -s -- architecture/architecture.yaml schemas/mezo-evidence/v1 tests/contracts/mezo_evidence_support.py tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py | sha256sum
```

## Current verification — 2026-09-24

The final readiness regression first demonstrated that false payment
readiness lacked a blocker explanation. The focused test and corrected truth
table were RED before the schema's `minItems: 1` repair and GREEN afterward.

| Command | Exit | Result |
| --- | ---: | --- |
| `python -B -m pytest tests/contracts/test_mezo_resources.py -q -k 'unready_payment or followup_readiness_truth_table'` before repair | 1 | 9 failed, 56 passed, 65 deselected in 1.70s |
| Same focused command after repair | 0 | 65 passed, 65 deselected in 1.58s |
| `python -B -m pytest tests/contracts/test_mezo_resources.py -q` | 0 | 130 passed in 38.40s |
| Six-module contract command below | 0 | 446 passed in 193.52s |
| `make verify` | 0 | 1087 passed, 85 subtests passed in 326.32s; Stage A verification passed |
| `python -B -m pytest -q` | 0 | 1087 passed, 85 subtests passed in 327.91s |
| `make graph` | 0 | Exactly seven inherited declared conflicts; no new diagnostic |
| `ruff check tests/contracts/test_mezo_resources.py` | 0 | All checks passed |
| `git diff --check` and `git diff --cached --check` | 0 | No whitespace errors |
| `python -B scripts/grok_verify.py --mode pr --no-record` | 1 | Only inherited trivy-config failure; all other applicable checks passed |
| `trivy config --exit-code 1 .` | 1 | Exactly two inherited LOW DS-0026 findings |

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py -q
```

Grok reported profiles=base, changed=6 during the stable test wave. Its
git-diff-check, secret-scan (zero potential secrets), contract-structure (one
contract), sql-safety (zero unsafe findings), Ruff, Bandit and pytest checks
passed; coverage was explicitly skipped by existing runner policy. Subsequent
README/tasks/handoff edits recorded results only, producing seven changed
files in the implementation commit; graph/Ruff/diff checks were repeated.
The two Trivy findings are in unchanged
`deploy/images/Dockerfile.public-capture` and
`deploy/images/Dockerfile.readonly-analyzer`. No waiver, filter or artificial
healthcheck was introduced. BLOCKED_TRIVY_HEALTHCHECK_POLICY is a local policy
blocker, not an unavailable external service; it prevents a fully green Grok
result but does not conceal a new contract failure.

Session-local logs are retained under the ignored directory
`.superpowers/sdd/2026-09-24-liqvera-f2-contracts/` as `readiness-red.log`,
`readiness-green.log`, `readiness-resource.log`, `readiness-contracts.log`,
`readiness-make-verify.log`, `readiness-pytest.log`,
`readiness-grok-verify.log` and `readiness-trivy.log`. They are not published
repository-local receipts; this document records their results durably.

## Independent review outcomes

The independent session/subagent results below were consolidated by the
coordinating agent and recorded in the closure handoff. No separate final
review report files or factory receipts exist; no report path is invented.

| Review | Exact final scope | Outcome and evidence |
| --- | --- | --- |
| Code | `74a7b6f25ea4fe947eca5748481ee247aa1c8f32..3729bdc131ca4ac971ab04e735da2e113d68ad71`, surrounding readiness schema/tests | APPROVED; no Critical, Important or Minor findings; 65 passed/65 deselected and diff check passed |
| Security | Same final micro-diff and payment-readiness safety boundary | APPROVED; no findings; 78 passed/52 deselected and diff check passed |
| Edge | Same final micro-diff and readiness boundary combinations | APPROVED; remaining blocker-list finding ADDRESSED, no remaining findings; 79 focused tests, six boundary probes and diff check passed |
| Acceptance | Clean implementation SHA/tree above; artifact scope, runtime status and verification counts | APPROVED; no remaining findings (no Critical/Important); recomputed exact fingerprint and verified count/status logs |

These scoped reviews follow whole-branch review and its repair waves; they
are not claims that a reviewer reran every suite independently. Historical
review progression: at `fd672f89`, code requested the reencoding correction,
security/acceptance approved, and edge identified reencoding/readiness/
timestamp gaps. At `74a7b6f`, code/security/acceptance approved while edge found
the remaining /readyz blocker-list Minor. All four final reviews approved
`3729bdc` with no remaining findings. The writer did not approve its own work.

## Frozen scope and remaining authority

F2 freezes the eleven JSON artifacts (OpenAPI, closed schemas, reasons,
state graphs and vectors), seven test/helper files and exact graph bindings.
It includes evidence 202 recovery, scope-before-expiry behavior, fixture and
quote eligibility, exact numeric/UTC semantics, fail-closed reencoded
authorization projections and coherent readiness. All 156 vectors remain
`NOT_RUN`: static consistency, synthetic examples and retained-kernel
characterization do not prove the future HTTP/payment/runtime behavior.

- A02–A06, A10–A12 and A15–A20 remain `NOT_RUN`.
- A13–A14 remain `BLOCKED_EXTERNAL`.
- F3–F7 remain open; next is F3 report building, canonical serialization,
  immutable evidence bundles and hardened offline verification.
- Payment readiness remains false. PAY_TO_MISSING, FINALITY_RULE_UNVERIFIED,
  absent funded buyer/signature/receipt, unresolved SDK/canonical authorization
  identity, and BLOCKED_TRIVY_HEALTHCHECK_POLICY remain blockers.
- No payment, deployment, release, push, runtime acceptance or factory receipt
  is claimed. Shadow-only authority and all seven inherited graph conflicts
  are unchanged.

Rollback remains a coherent static contract/test revert. No persisted paid
state exists; future ledger recovery must retain replay protection/artifacts.

## Historical verification summary — not current receipts

| Stage | Contract tests | Full runs | Notes |
| --- | ---: | --- | --- |
| Integration `644cb702` | 329 | 970 plus 85 subtests each | State-schema RED 1 failed/21 passed, then 22 passed |
| Consolidated repair `fd672f89` | 368 | 1009 plus 85 subtests each | Targeted RED 23 failed/16 passed; GREEN 39 passed |
| Final follow-up `74a7b6f` | 445 | 1086 plus 85 subtests each | Targeted RED 8 failed/69 passed; GREEN 77 passed |

Every integrated historical run passed graph/Ruff/diff and failed Grok only
on inherited Trivy. The isolated Task 6 history below also records its then
missing integration inventory and import-order failure; those were resolved
before the reviewed implementation. The archival material below describes
its own earlier state only, including then-pending review and old fingerprints.

## Historical integration draft — superseded by closure above

Historical status: **INTEGRATION VERIFIED; INDEPENDENT REVIEW PENDING**.

The owner approved the repaired plan and parallel task implementation. All six
task slices, Task 1/3 review repairs and Task 6's complete-envelope validation
repair are integrated on `feat/mezo-evidence-f2-contracts`. The single
integration owner added exact graph bindings for 11 JSON artifacts, seven
test/helper files and this evidence file, plus current continuity records.
Both new graph nodes retain empty requirement lists and use context-only
DATA-005/validation edges; the seven inherited conflicts are unchanged.

Integration corrected Task 5's Minor description to "without paid report
fields" while preserving its JSON 202 recovery body. A direct state-schema
check also exposed the symbol pattern's rejection of `report_sha256`; a
complete-document regression failed before the pattern allowed ASCII digits
after its first letter, then all 22 state tests passed. No state transition
or payment authority changed. Independent whole-branch review is still pending.

The isolated Task 6 results below are historical task evidence, including its
then-missing graph bindings and Task 3 Ruff failure. They do not describe the
integrated tree. The final integration results follow; F2 remains open until
review and verification are assessed together.

## Integration verification — 2026-09-24

Source base: `d5216f469f0a94c169aa11d3f8963b44567f4ba6`. The last integrated
task commit before the integration-owned changes is
`0632211aa540926292ba01771d4a66cb0e3b7548`. No cherry-pick conflict occurred;
Task 2's helper extension auto-merged with Task 1's numeric repair.

Checks ran in `/home/pall/projects/liqvera/.worktrees/mezo-evidence-f1-impl`,
using its `.venv/bin` first on PATH: Python 3.12.3, pytest 9.1.1 and Ruff
0.16.8. The final checks started by `2026-09-24T20:16:55Z` and completed by
`2026-09-24T20:23:54Z` (the separate Trivy confirmation followed).

| Command | Exit | Result |
| --- | ---: | --- |
| `git diff --check` and `git diff --cached --check` | 0 | No whitespace errors |
| `make graph` | 0 | Exactly seven inherited declared conflicts; no new graph diagnostic |
| `python -B -m pytest tests/contracts/test_mezo_states.py -q` regression RED | 1 | 1 failed, 21 passed; the real document's `report_sha256` violated the symbol pattern |
| Same state regression after repair | 0 | 22 passed in 1.53s |
| Six focused contract modules, command below | 0 | 329 passed in 179.24s |
| Ruff on the helper and six F2 test modules | 0 | All checks passed |
| `make verify` | 0 | 970 passed, 85 subtests passed in 311.17s; Stage A verification passed |
| `python -B -m pytest -q` | 0 | 970 passed, 85 subtests passed in 311.25s |
| `python -B scripts/grok_verify.py --mode pr --no-record` | 1 | Only `trivy-config` failed; all other applicable checks passed; coverage explicitly skipped by runner policy |
| `trivy config --exit-code 1 .` | 1 | Exactly two LOW DS-0026 missing-HEALTHCHECK findings in the existing one-shot Stage A Dockerfiles |

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py -q
PATH="$PWD/.venv/bin:$PATH" ruff check tests/contracts/mezo_evidence_support.py tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py
```

Grok reported `profiles=base`, `changed=9` for its integration working-diff
snapshot, and zero potential secrets. Its secret-scan result is not a new
whole-history audit. This run created no receipt. No new unresolved failure
was observed; `BLOCKED_TRIVY_HEALTHCHECK_POLICY` remains unchanged.

The code/schema/graph tree was stable during these checks. Its staged tree
before verification-record edits was
`f1d03ae65de433073e030127b462cb751bdedfcb`; later changes update only evidence
and continuity prose. A reproducible fingerprint excluding that prose is
`7c55d6f27a9a8c1f09901c14b25e0e89490cd7640251b36c5765deed7397d12d`, obtained
by the following command after staging the integration artifacts:

```bash
git ls-files -s -- architecture/architecture.yaml schemas/mezo-evidence/v1 tests/contracts/mezo_evidence_support.py tests/contracts/test_mezo_primitives.py tests/contracts/test_mezo_requests.py tests/contracts/test_mezo_resources.py tests/contracts/test_mezo_states.py tests/contracts/test_mezo_openapi.py tests/contracts/test_mezo_vectors.py | sha256sum
```

This binds contract consistency and existing-kernel characterization only.
Task 1/3 repairs passed scoped independent re-review; Task 2 was approved;
Task 4's graph/handoff gap and cross-task state validation are now addressed;
Task 5's approved Minor wording is repaired. Task 6's envelope repair is
integrated, with final independent review still pending. No F2 closure or
F3–F5 runtime PASS follows from these results.

## Source and environment

- Original source base: `d5216f4` (`docs: record F2 plan review approval`).
- Isolated branch: `feat/f2-task6-vectors`.
- Worktree: `/home/pall/projects/liqvera/.worktrees/f2-t6-vectors`.
- Dependency head before the Task 6 commit: `ccd3294` (Task 3); includes Task 1,
  its numeric-semantics review repair, Task 2, and Task 4 artifact commits.
- Verification recorded at `2026-09-24T20:04:40Z`; Python 3.12.3, original F1 venv
  `/home/pall/projects/liqvera/.worktrees/mezo-evidence-f1-impl/.venv`.
- No active route exists; `grok_status.py` returned null route/change and no
  receipt gaps. That output is not factory approval. No receipt was created.

## Artifact scope and exclusions

153 literal vectors cover exact BUY/SELL sweeps, invalid wire requests,
dataset boundaries/rejections, canonical and conflicting retries, 20-repeat
obligations, semantic payment claims, access isolation, recovery, retention,
and missing/corrupted/fictitious artifacts. Every vector is `NOT_RUN`.

The real existing `reconstruct_books`, `bind_reconstructed_books`, and
`sweep_depth` characterize four hand-derived sweep results and insufficient
depth rejection. Mapping and payload hashes derive from actual synthetic
bytes in the tests. They are SIMULATED evidence, never live provenance.
The display oracle uses 28 significant digits, HALF_EVEN, fixed-point output,
and trailing-zero normalization; canonical rational components stay exact.

Request/dataset/payment JSON text is parsed strictly, with Decimal for numeric
JSON tokens, duplicate-key and nonfinite rejection, and closed semantic claim
keys. Payment claims are synthetic semantic projections, not x402/EIP-2612/
Permit2 wire payloads. Exact atomic conversion remains blocked by unresolved
authorization identity. Synthetic addresses never become operator defaults.

The corpus preserves metadata validity's inclusive endpoints, consistent with
the retained `MarketMappingEvidence.valid_for` contract. State vectors check
actual graph edges and current joint delivery guards. The 30-day retention
floor cannot erase scope/dedup linkage while validity is unknown, still active,
or replay impossibility remains unproven.

F3 still owns canonical report serialization: sorted keys, UTF-8, compact
separators, `ensure_ascii=False`, `allow_nan=False`, exactly one final newline,
and no own digest in the report body. Its `canonical_report_bytes_reproduce`
assertion is attached to each successful sweep; this task implements no report
serializer, immutable artifact service, or offline ZIP verifier.

F4 still owns HTTP/capability enforcement, database idempotency, actual 20-way
concurrency and protected report/bundle delivery. F5 still owns SDK identity,
finality, durable settlement, real replay/concurrency/crash recovery, and
chain-correlated receipts. No mock/model result establishes those behaviors.
`PAY_TO_MISSING`, `FINALITY_RULE_UNVERIFIED`, A13–A14's `BLOCKED_EXTERNAL`, and
all other unrun runtime acceptance remain unchanged. No live probe, payment,
signature, release, deployment, or exchange mutation occurred.

## Verification evidence

Commands below use the original venv's Python, or prepend its `bin` to PATH.
The final code-artifact checks started after all needed dependency commits
were present; documentation changes do not claim a new product verification.

| Check | Exit/result |
| --- | --- |
| Initial `python -B -m pytest tests/contracts/test_mezo_vectors.py -q` | 1; 9 assertion failures for missing vectors, covering all eight families plus exact SELL |
| Expanded RED, same command before artifacts | 1; 22 missing-vector assertion failures |
| Additional Task 2 corpus-coverage RED | 1; 12 required adversarial records absent, then added and checked GREEN |
| Final focused vector suite | 0; 40 passed in 24.21s |
| `ruff check tests/contracts/test_mezo_vectors.py` | 0; all checks passed |
| `git diff --check` | 0 |
| `make verify` | 2; stops at shared graph inventory: 13 dependency artifacts lack bindings in this intentionally isolated branch |
| Final full `python -B -m pytest -q` | 1; 943 passed, 85 subtests passed, 5 graph-inventory failures in 185.45s |
| `python -B scripts/grok_verify.py --mode pr --no-record` | 1; Trivy, repository Ruff and pytest fail; other applicable checks pass; 0 potential secrets; coverage explicitly skipped by runner policy |
| `trivy config --exit-code 1 .` | 1; exactly two LOW DS-0026 findings, in `deploy/images/Dockerfile.public-capture` and `deploy/images/Dockerfile.readonly-analyzer` |

The five final full-suite failures are:

- `tests/graph/test_final_review_policy.py::test_declared_conflict_waiver_is_closed_to_precommit_m0_baseline`
- `tests/graph/test_repository_manifests_cli.py::test_cli_reports_declared_baseline_conflicts_without_blocking_when_allowed`
- `tests/graph/test_repository_manifests_cli.py::test_merge_stays_fail_closed_on_declared_conflicts_and_untrusted_policy_time`
- `tests/graph/test_repository_manifests_cli.py::test_repository_script_runs_from_the_repository_root`
- `tests/graph/test_third_final_review_policy.py::test_repository_inventory_covers_all_tracked_paths_exactly_once`

All five report `REPOSITORY_ARTIFACT_UNDECLARED`, with 13 tracked dependency
artifacts not yet bound by the integration owner. The repository-wide Ruff
failure is Task 3's `tests/contracts/test_mezo_resources.py:3` (`I001`, import
ordering); Task 6's own Ruff check passes. This was reported to the integration
owner without changing another task's file. The pre-existing
`BLOCKED_TRIVY_HEALTHCHECK_POLICY` remains a release blocker; no waiver or
artificial healthcheck was added.

An earlier exploratory full run overlapped incoming dependency commits and
is not final-tree verification: 775 passed, 85 subtests passed, 9 failed in
134.24s. Four failures used missing Task 2/3/4 interfaces; five were the shared
graph-inventory failures. No failure is reclassified as a pass.

The 12 concrete mutation checks reject changed side/fraction, missing required
assertion, wrong atomic amount, PASS runtime status, wrong owner, duplicate ID,
duplicate/unknown assertion, extra input/expected keys, and wrong version.
Every assertion in the exact F3/F4/F5 registry has a vector.

## Code-artifact fingerprint and closure

Pre-commit SHA-256 fingerprints of the three owned code/contract artifacts:

The staged code/artifact tree before adding this new evidence document is
`731b2174e2c5294980109616da806c4a82027edd` (`git write-tree`). This explicitly
excludes this draft to avoid a self-referential fingerprint; the separate
handoff report records the resulting full commit/tree.

```text
f195e7e5cc806426f9c3a0967b1855ecc4f240eeaedcbcf78b4e74549e37f02f  schemas/mezo-evidence/v1/vectors.schema.json
f2377bd3bb895316695c19b2d6a3497d9bc35cf300c0ebc41158c0d23cc33058  schemas/mezo-evidence/v1/vectors.json
730aac8d2bf43182216f35e9246a1fdb542d32eb423812ecc7bf2cb885a15d6c  tests/contracts/test_mezo_vectors.py
```

These fingerprints bind the focused evidence only; no independent reviewer has
approved this artifact branch yet. Integration must record its final tree
fingerprint and resulting implementation SHA after shared-file reconciliation.
The separate Task 6 handoff report records this task's resulting commit SHA.

Rollback is a coherent revert of these static contracts/tests. No persisted
payment state exists. Future ledger recovery must preserve replay protection
and retained artifacts; deleting ledger records is not a rollback strategy.
