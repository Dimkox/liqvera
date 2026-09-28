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

The final bounded PR-verifier run recorded `pytest-xdist workers=22` and passed
diff, change-spec, secret, contract, SQL, Ruff, Bandit, source-stability, and
the recurring Trivy gate. Trivy dynamically discovered nine tracked inputs:
seven Dockerfiles and two Compose files; all passed the blocking
`MEDIUM,HIGH,CRITICAL` threshold. The measured pytest process nevertheless
exited 1 after 67.786 seconds and its coverage report exited 1. The upstream
runner removed its temporary current-run artifacts, so no unsupported failure
cause or green receipt is claimed. A separate LOW audit found only the
inherited `DS-0026` missing-`HEALTHCHECK` Dockerfile finding.

Route receipts and independent reviews are still pending. A v2.0.19 state
transition reached `scoped` and then failed closed because the pre-existing
active route does not contain the gate declaration required by this newer
kernel; no approval or receipt was fabricated.
