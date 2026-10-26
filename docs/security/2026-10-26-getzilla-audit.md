# Getzilla 2.3.1 audit of Liqvera — 2026-10-26

Liqvera `main` `23e28c454238cb2478c11903f7af8a16c8f605a7` passes every selected check of the current Getzilla `main` (`a5fcc3a4`, VERSION 2.3.1) except one test that fails only because the audit ran as root. With root's permission override removed, that test passes. No product change is needed.

This is a source audit only. It adds no rollout, quote, payment, signature or deployment, and it does not change the live application.

## Method

| Item | Value |
| --- | --- |
| Liqvera source | `main` `23e28c454238cb2478c11903f7af8a16c8f605a7`, full history (363 commits) |
| Getzilla source | `main` `a5fcc3a4` (2.3.1), installed into a disposable copy only; nothing was added to this repository |
| Command | `getzilla_verify.py --mode pr --full-scope --keep-going --json` |
| Comparison base | the installation commit itself, so the whole Liqvera tree is checked, not the installation diff |
| Liqvera configuration | Liqvera's own `ruff.toml`, `bandit.yaml` and `.coveragerc` (the installer replaces them; they were restored before the run) |
| Dependency data | offline OSV mirror (the online OSV API was not reachable from the audit host) |
| Host | cloud container, 4 CPUs, Python 3.13 virtual environment `.venv` from `requirements-dev.lock`, run as root |

## Results

| Check | Result |
| --- | --- |
| git diff check, diff risk, cost guard, hook health | pass |
| Secret scan | pass — 0 potential secrets |
| SQL safety, contract structure | pass |
| Known vulnerabilities | pass — 0 in 482 pinned dependencies |
| OpenGrep (Getzilla taint rules, v1.30.1) | pass — 0 findings |
| Ruff (Liqvera configuration) | pass |
| Bandit (Liqvera configuration) | pass |
| `pytest` | 1058 passed, 1 failed, 85 subtests passed (298 s) |
| Quality gate QG-01 | pass |
| Architecture, governance, workflow artifacts, EU AI Act | not configured in Liqvera; skipped |

The one failure is `tests/contracts/test_acceptance_result.py::test_sealed_tree_blocks_unlink_and_has_nonwritable_directories`. It expects `PermissionError` when it removes a file from a read-only sealed tree; root bypasses directory permissions. Rerun with `setpriv` removing `CAP_DAC_OVERRIDE`, `CAP_DAC_READ_SEARCH` and `CAP_FOWNER`, the same test passes (1 passed). The 21 October audit ran as an ordinary user and did not meet this.

## Findings that were not Liqvera's

A first run with Getzilla's default `ruff.toml` and `bandit.yaml` reported two Ruff E702 lines in `tests/evidence_report/test_canonical_f3.py:110` and one Bandit B606 (Low) in `scripts/verify-mezo-acceptance.py:20`. Liqvera's own configuration excludes those paths or rules, and its own `ruff check .` passes. They came from the installer replacing the project's configuration, which is a Getzilla defect, not a Liqvera finding.

## Evidence

- [Machine-readable report](2026-10-26-getzilla-audit.json): the unmodified `getzilla_verify.py --json` output of the final run. Its `git_head` is the disposable audit commit (installation plus restored Liqvera configuration) on top of the source above.
- Previous audits: [21 October successor](2026-10-21-getzilla-successor.md) and [initial](2026-10-21-getzilla-initial.md).
