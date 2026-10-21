# Current Liqvera verification result — 2026-10-21

Liqvera's complete native Getzilla audit passes with exit 0 and zero evidence gaps. Its five selected independent reviews pass against the exact frozen source. The four inherited TLS blockers were corrected and deployed. The optional audit tool's own full self-check fails; this report does not claim that Getzilla is fully qualified or that all results are green.

The distinction is material: Liqvera was checked with an exact locally modified Getzilla candidate whose independent reviews pass but whose self-test exceeds a time limit. Its source bundle, failed self-check and limitations are preserved below. The candidate is not published or merged as a qualified Getzilla release. Liqvera remains buildable and verifiable without an external delivery framework.

The live application remains `1c020995adaa1a80fc8a97888aa838041d8e01d5` on claw. Its funding-layout repair, checkbox prerequisite guidance and Getzilla footer are already deployed. This audit adds no rollout, quote, payment, loan or grant. The delivery source `17a70595e98aa183afac115e5b99488830fba712` also preserves corrected `pip==26.2.2` after the PR #14 dependency merge.

## Exact native results

| Candidate | Frozen report-containing commit | Result / exit | Duration | Evidence gaps |
| --- | --- | --- | --- | --- |
| Liqvera | `328dfa8f0523310e80693db606a0e737c24b2ee5` | PASS / 0 | 411.76 s | 0 |
| Getzilla | `45be42f74b5a8ee6f079f8ac55206e475936fdc6` | FAIL / 1 | 1225.84 s | 5 |

The Liqvera reviewed source is `1b90f54c7ab26a7689cb892687175ac12cb7e3a4`; the Getzilla reviewed source is `3968ae4445836eda9cf377035b1d1f64fe9659b0`. Only the selected complete review report files were added after each review freeze. Both invocations use `--mode pr --full-scope --keep-going --json`, preserve clean unchanged candidates and retain their original comparison bases. The raw invocation, trees, scope selection and every check are archived. Liqvera has six fingerprint-bound passing receipts: verification and five reviews. Getzilla has a failed verification receipt and four missing review receipts; its review reports do not override the failed gate. This is a successor to the unmodified [PR #115](https://github.com/Dimkox/Getzilla/pull/115) tool, not a claim that its original failed result passed.

| Native test runner | Result | Observed summary |
| --- | --- | --- |
| Liqvera / `pytest` | pass | 956 passed, 85 subtests passed in 389.66s (0:06:29) |
| Getzilla / `python-unittest` | fail | SKIPPED [1] tests/test_stack_go_java.py:99: downloads Go from go.dev; SKIPPED [1] tests/test_stack_go_java.py:159: downloads Temurin JDK 21 from GitHub; SKIPPED [1] tests/test_stack_node.py:175: downloads Node from nodejs.org; SKIPPED [1] tests/test_stack_runners.py:152: downloads rustup and a Rust toolchain from static.rust-lang.org; SKIPPED [1] tests/test_stack_runners.py:216: downloads the .NET SDK from builds.dotnet.microsoft.com; SKIPPED [1] tests/test_stack_runners.py:293: downloads PSScriptAnalyzer and Pester from the PowerShell Gallery; SKIPPED [1] tests/test_python_test_runner.py:634: Windows Job Object; SKIPPED [1] tests/test_python_test_runner.py:607: Windows Job Object; SKIPPED [1] tests/test_python_test_runner.py:596: Windows Job Object capability; SKIPPED [1] tests/test_fsx.py:85: POSIX dir_fd calls already resolve names relative to the descriptor; SKIPPED [1] tests/test_fsx.py:92: Windows-only primitives; SKIPPED [1] tests/test_manifest_package.py:287: the refusal is for hosts without POSIX ownership and umask; SKIPPED [1] tests/test_install_scripts.py:478: downloads the OSV database, OpenGrep, the pinned workflow sources and PyPI tools; SKIPPED [1] tests/test_zero_git_platform.py:105: native Windows filesystem cases; SKIPPED [1] tests/test_zero_git_platform.py:71: native Windows filesystem cases; SKIPPED [1] tests/test_zero_git_platform.py:93: native Windows filesystem cases; SKIPPED [1] tests/test_zero_git_platform.py:79: native Windows filesystem cases; FAILED tests/test_policy_hardening.py::Review2PosixTests::test_secret_scan_is_bounded_and_fails_closed_on_a_huge_argv; 1 failed, 2277 passed, 17 skipped, 2 warnings, 3961 subtests passed in 528.96s (0:08:48) |
| Getzilla / `factory-unit` | pass | exit=0 |
| Getzilla / `factory-postgres-exit` | pass | exit=0 |

The selected executable checks include source stability, architecture/governance, specification, Git ranges, secret scanning, online dependency vulnerability scanning, OpenGrep, Ruff and Bandit. Optional or unconfigured checks retain their actual skips:

- Liqvera `architecture-inputs`: architecture authority inputs are absent; not executed
- Liqvera `architecture`: architecture is not configured
- Liqvera `governance`: governance is not configured
- Liqvera `workflow-artifacts`: workflow artifacts are not configured
- Liqvera `eu-ai-act`: EU AI Act component not installed
- Liqvera `workflow-baseline`: not an installed Getzilla project (no .getzilla/AGBP_SYNC.json): the baseline is checked where Getzilla was installed
- Liqvera `coverage`: pytest runner owns tests; measure unittest trees only
- Getzilla `workflow-artifacts`: workflow artifacts are not configured
- Getzilla `eu-ai-act`: EU AI Act component not installed
- Getzilla `workflow-baseline`: not an installed Getzilla project (no .getzilla/AGBP_SYNC.json): the baseline is checked where Getzilla was installed
- Getzilla `stack:powershell`: no changed files of this stack

Complete Getzilla code/test/security/release reviews and Liqvera code/test/security/data/release reviews are preserved with source identities and raw probes. Getzilla has no passing external acceptance recorded for this candidate; its publication status is explicit in the [JSON record](2026-10-21-getzilla-successor.json). Local receipts do not establish external acceptance.

The release review's nonblocking tool-rollback clarification is resolved in the JSON delivery mapping: integrated queue and hook-precedence commits are `4c47e7ca5cf40ed6bc3f91aa24532ad457e19cdd` and `de0ed1d9f98b21d2636deb977f0eef403529d23a`. Their patch identities equal the isolated predecessors named by the frozen package. Use delivered ancestors for a separately verified source rollback; this does not affect production recovery.

## Why the audit outcome changed

Exactly three reviewed raw findings remain visible: two public Testnet MUSD contract-address occurrences and the final blank line in immutable Wave 1 evidence. [The disposition explanation](2026-10-21-verification-dispositions.md) identifies their meaning and exact hashes. Each entry binds target bytes, the individual finding and independent review evidence. Stale or altered entries, other occurrences and genuine credential classes remain failures. The policy hash is `e0395a8b681958936fa97f552f517d77cecb49744eb33b902a3ee5c6569ef141`. Raw severity and command exits are retained separately from the effective result; no entire file or Git comparison range is suppressed.

The first successor gates also failed and remain archived. Liqvera's first run passed 956 Python tests and 85 subtests but failed required approval-scope metadata. Getzilla's first run exposed execution-environment problems, insufficient finite analyzer capacity, hook import ownership and a stale wheel inventory. Short non-Git test scratch and explicit supported Python corrected the environment. Source repairs retain finite queue limits, bind hooks to their owning package and derive the inventory from existing pins. Independent reviews found and then verified the narrow hook repair. No final-gate timeout, assertion, scanner scope or compatibility rule was weakened.

Getzilla's second full self-check remains **FAIL**: Core reports 2,277 passed, one failed and 17 skipped; Factory unit tests pass 63, and the real disposable-PostgreSQL exit suite passes 1,040 with six documented skips. Coverage reaches 81.72%, above the unchanged 74% threshold, but the coverage gate correctly fails because the tests did not all succeed. The failing Core test is `Review2PosixTests.test_secret_scan_is_bounded_and_fails_closed_on_a_huge_argv`. The native output truncation lost its original traceback, so its original assertion cannot be proven from that log alone. Two exact-source isolated replays with unchanged coverage reproduce only the elapsed-time assertion at 8.487197 and 8.3206 seconds against the 8-second limit; the protected command is denied in both. The named unittest runner and matched pytest without coverage pass. These controls do not turn the full failure into a pass. No further Getzilla repair, full rerun, qualification receipt or merge is claimed by this Liqvera delivery.

The unrelated PDF-profile prototype remains excluded after its actual compatibility failure. Existing Getzilla PDF skips, the pre-existing import-effect analyzer gap and seven supplementary all-tracked baseline heuristic observations remain disclosed in the full reports. A passing native changed-file scan does not clear those different-scope observations. These tooling limits are not new Liqvera runtime vulnerabilities and are not represented as repaired here.

## Deployed behavior and preservation

[TLS deployment evidence](2026-10-21-tls-deployment.md) retains the exact images, scanner dispositions, Docker builds, complete web/gateway checks and all 13 real disposable-PostgreSQL cases. Those results retain their original time and source. The public browser was checked at six widths from 320 to 1440 pixels, with correct funding spacing and no overflow. The checkbox requires a fresh unpaid quote with a confirmed MUSD shortfall; that prerequisite is explained in the interface.

WalletConnect configuration, the existing PostgreSQL container, databases, three confirmed and one manual-review payment attempts, four receipts/entitlements, SQL migrations and sealed evidence were preserved by the earlier rollout. This audit makes no live payment-state change. Fresh read-only public observations are bound in the JSON record. The historical report and ZIP retain SHA-256 `0ebf36b89bda183b99767cd7fedc3c956405ef4a3f195d9d73b911d2c146ccf2` and `3255a42c210c6fe6ad0020c34113988da3f1659c566a73b7729606ad65d083b0`.

The existing production recovery command remains:

```bash
python3 /home/pall/.local/state/liqvera/recovery/2026-10-21-tls-1c02099/rollout.py rollback
```

It restores retained application containers without restoring a database or running migrations. Old images retain their previous TLS exposure. Physical wallet pairing, borrowing and a new signed paid delivery were not exercised. A passing dated audit is not a guarantee against future dependency advisories or source changes.

## Evidence

[Machine-readable record](2026-10-21-getzilla-successor.json) and [complete raw archive](2026-10-21-getzilla-successor-raw.tar.gz) bind the passing Liqvera run, failed Getzilla self-check, every review wave, earlier failed gates, bounded controls, diagnoses, exact frozen Git bundles and public observations. Archive SHA-256: `355a2eed0bd4c12f2dcad232a3101c8981fa2c7126ad04e5759d497b0c3d9f3e`. All 1004 payload hashes were verified after reopening the archive. Private configuration, database dumps, wallet material, delegated grants and browser profiles are excluded.

Native JSON retains the tool's bounded subprocess-output excerpts. Separate diagnostic and reviewer logs retain their own recorded scope; the archive does not claim an unsliced log for every subprocess in the full gate.

The [initial negative audit](2026-10-21-getzilla-initial.md), [Wave 1 evidence](2026-10-21-wave1-deployment.md), [layout evidence](2026-10-21-layout-deployment.md) and [TLS deployment record](2026-10-21-tls-deployment.md) remain byte-for-byte unchanged. Their negative results remain historical facts; this document is the current successor result.
