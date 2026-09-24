# F2 contracts evidence — Task 6 artifact branch draft

Status: **PARALLEL ARTIFACT BRANCH; INTEGRATION PENDING**. This document is not
whole-branch approval, a factory receipt, or F3–F5 runtime acceptance.

Task 6 owns only `vectors.schema.json`, `vectors.json`,
`tests/contracts/test_mezo_vectors.py`, and this draft. The integration owner
must update the shared graph inventory, handoff, task ledger and README, run
whole-branch verification, and obtain independent review before F2 closure.

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
