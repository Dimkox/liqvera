# Evidence

Store human-readable review reports here. Machine receipts live under `.grok-stack/runtime/receipts/` and are bound to the current repository fingerprint.

## Implementation checkpoint — 2026-09-28

- Adaptive Grok source: local annotated tag `v2.0.19`, gitlink commit
  `cb9af4073ba6c3d515145164d771c75ebdfa3224`, release-sidecar SHA-256
  `4176a872acdca873e840855d0b2c9e379cf8f796c9de69e5560b3e2bf85634b9`.
- BMad source: external `bmad-method@6.10.0` package with its exact npm SRI
  recorded in `tooling/tooling-lock.json`; no package source is tracked.
- TDD red: the initial boundary suite produced seven expected failures for
  retained Go, copied framework source, missing pins, and missing launcher.
- Focused green: `python3 tooling/run-adaptive-grok.py --check` accepted the
  exact clean pin; `python3 -m pytest tests/conformance tests/graph -q`
  reported `257 passed, 3 warnings`.
- Preserved files were compared to the base: A2 raw-capture migrations,
  gateway ledger migration, SQLite demo migration, import manifest, schemas,
  vectors, and fixtures remain outside the approved removal set.
- The graph diagnostic contains only the inherited 26 implementation orphans
  and six still-active declared conflicts; no cleanup inventory, dangling-Go,
  or repository-boundary diagnostic remains.

Review-repair RED reproduced nine failures: safety hooks returned success after
missing or invalid tooling, direct verification imported an unvalidated
checkout, ordinary boundary tests required a recursive clone, and the PR gate
had no explicit recurring container targets. The shared pin validator, strict
tooling suite, static ordinary boundary checks, and dynamic Trivy gate repair
those defects. Missing, wrong-lock, wrong-HEAD, and dirty/untracked checkouts
now fail before hook or verifier execution and cannot emit an allow result.

An isolated local `.venv` supplies the exact v2.0.19 runner versions plus the
declared Hatchling backend without changing the global interpreter. The stale
README and public-capture metadata assertions were corrected. The focused
aggregate before final security repair reported `272 passed`. A direct
22-worker diagnostic reported `1122 passed, 85 subtests passed in 53.38s`.

Final security re-review demonstrated a status bypass: marking
`scripts/grok_verify.py` `assume-unchanged` and modifying its bytes left status
clean and validation successful. RED also reproduced `skip-worktree`, a hidden
executable-mode change, and ignored bytecode in an import root. The validator
rejects index flags globally, independently hashes the explicit executable and
instruction trust closure, compares executable modes to HEAD, and rejects
ignored importable files in the three executable roots.

Performance review measured the all-tree validator reading 3,937 blobs / about
120.4 MB per hook, with a 0.67-second launcher baseline. After adding the two
change-spec schemas read directly by `adaptive_grok.spec`, the bounded closure
is 179 files / 1,241,709 bytes, capped structurally at 256 files / 2,000,000
bytes; three warm launcher measurements were 0.16, 0.14, and 0.13 seconds. Regression
tests prove engine/instruction/schema tamper rejection, explicit fail-closed
closure membership, and that the 14.3 MB v2.0.19 release archive is never read.
The final focused aggregate reports `282 passed`, including 21 tooling cases.

A local fresh clone of implementation commit
`058092d2c243d732eb4a44d876a46ae98b64c102`, created with
`--no-recurse-submodules`, passed
`tests/conformance/test_repository_boundary.py`: `8 passed`. The three emitted
warnings were host pytest configuration warnings for an absent optional asyncio
plugin, not test failures.

The complete-inventory measured command used 22 xdist workers and reported
`1134 passed, 85 subtests passed`, with branch-aware coverage of 36.16% across
10,413 statements. All tracked owned Python under `packages/`, `scripts/`,
`tools/`, and `tooling/` is included, including zero-covered scripts; precise
omits cover tests, the eight external Grok symlink entrypoints, generated build
paths, and the pinned submodule. The earlier 59.18% result omitted owned
scripts, standalone tools, and project-owned tooling and is invalidated. The
corrected initial gate is `fail_under=36`, the integer below observation; it
must not regress and is explicit roadmap debt to raise. A green receipt remains
pending the post-commit full verifier.

Trivy dynamically discovered nine tracked inputs: seven Dockerfiles and two
Compose files; all passed the blocking `MEDIUM,HIGH,CRITICAL` threshold. A
separate LOW audit found only the inherited `DS-0026` missing-`HEALTHCHECK`
Dockerfile finding.

Four reviewer-provided PASS reports are stored as `code-review.md`,
`test-review.md`, `security-review.md`, and `data-review.md`. Each names the
clean reviewed fingerprint `aa5925f320da68843a52362e1654549d3a658899`, reports
no findings, and preserves the reviewer's receipt-ready evidence summary. This
report-only commit changes the repository fingerprint, so all five typed
evidence obligations remain `not_run` until final verification and
fingerprint-bound receipt recording. No approval or receipt was fabricated.

## State closure

The pinned v2.0.19 change CLI advanced the durable package through
`scoped -> approved -> implementing -> verifying -> reviewing -> ready`. No
human gates are declared. The CLI generated and mirrored the clean
implementation checkpoint below at
`f7401a903d53c8ecb34415ce474a63f110a4ccdb`.

The transition history and checkpoint are repository changes, so runtime
diagnostics now correctly report all five pre-transition receipts as stale.
The typed durable obligations remain `not_run` pending a final verifier and
independent-review refresh bound to the state-close fingerprint; no receipt or
human approval was invented.

<!-- checkpoint:implementation -->
## Implementation checkpoint

Local observation only; not verification or publication evidence.

```json
{
  "kind": "implementation",
  "change_id": "20260928-repository-boundary-cleanup-7f0f98",
  "route_id": "7f0f98e3cdda",
  "observed_at": "2026-09-28T22:21:06+00:00",
  "branch": "chore/repository-cleanup",
  "head": "f7401a903d53c8ecb34415ce474a63f110a4ccdb",
  "detached": false,
  "git_available": true,
  "git_findings": [],
  "dirty_product_state": "clean",
  "dirty_product_paths": [],
  "note": "implementation started; preserve work before handoff"
}
```
