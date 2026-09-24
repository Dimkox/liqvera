# F1 verification evidence

Observed: 2026-09-24T17:27:03Z–2026-09-24T17:29:37Z (UTC).
Implementation SHA: `68dafdba76ee5aaf9dc2d5c28719f26f849bf1f6`.
Branch: `feat/mezo-evidence-f1-impl`.
The SHA was captured before documentation changes; the implementation tree
was clean before and after these checks. This report belongs to the later
documentation closure commit, not a new implementation or factory receipt.

## Result and scope

F1 is **complete-with-blockers**. Public baseline repairs and compatibility
evidence exist, but the full verification pipeline remains FAIL.
The overall change is `implementing`; F2–F7 remain open.
Payment readiness is false. No final-product acceptance or release is claimed.

The initial failures remain recorded in
[source-baseline.md](source-baseline.md) against
`d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a`.
Tasks 1–4, including reviewed fixes, end at the implementation SHA above.
The accepted [ADR-0002](../../../../docs/adr/0002-liqvera-report-payment-boundary.md)
does not freeze F2 API/database contracts.

## Environment and exact commands

Commands ran from the implementation worktree using its existing `.venv`.
The installation was not repeated during closure. Task 3's clean install
and pin repair are historical evidence, not a fresh A28 run.

| Command | Exit | Observed result |
| --- | ---: | --- |
| `git rev-parse HEAD` | 0 | 68dafdba76ee5aaf9dc2d5c28719f26f849bf1f6 |
| `date -u +%Y-%m-%dT%H:%M:%SZ` | 0 | Start 2026-09-24T17:27:03Z |
| `.venv/bin/python --version` | 0 | Python 3.12.3 |
| `.venv/bin/python -m pytest --version` | 0 | pytest 9.1.1 |
| `.venv/bin/python -c 'import importlib.metadata as m; print("hatchling " + m.version("hatchling"))'` | 0 | hatchling 1.32.4 |
| `npm --version` | 0 | 11.19.0; npm is not used by the final compatibility transport |
| `.venv/bin/python -m pip check` | 0 | No broken requirements found |
| `PATH="$PWD/.venv/bin:$PATH" make verify` | 0 | 623 passed, 85 subtests passed in 135.21s; stage-a verify passed |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record` | 1 | RESULT: FAIL; only trivy-config failed |
| `trivy config --exit-code 1 .` | 1 | Exactly two LOW DS-0026 findings; details below |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py --lock docs/compatibility/mezo-evidence-v1.json` | 0 | COMPATIBILITY_PASS_PAYMENT_BLOCKED |
| `git diff --check` | 0 | No whitespace errors |
| `git status --short` | 0 | Empty before documentation changes |
| `.venv/bin/python scripts/grok_status.py` | 0 | route=null, change=null, evidence_gaps=[]; no active factory run |

`make verify` ran graph, salvage, artifact, and full package/compatibility
tests. Graph printed seven inherited `DECLARED_CONFLICT` notices under
`--allow-declared-conflicts`; they were not resolved. Salvage reported
`items=4 targets=verified source_objects=unavailable`. Artifact validation
confirmed no Go inputs. Verdict and CLI tests retain `INSUFFICIENT_EVIDENCE`
and prohibit `GO`.

The Grok check passed git-diff-check, secret-scan (0 potential secrets),
contract-structure (0 contracts checked), sql-safety (0 unsafe findings),
Ruff, Bandit, and pytest. Coverage was explicitly skipped because pytest owns
the selected tests. Zero contracts checked is not F2 contract validation.
No receipt was recorded because `--no-record` was used and no route exists.

## Compatibility evidence binding

The fresh stdout result matched the committed sanitized result:

- `engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json`
  SHA-256: `5777229a9e303fe5f02bfeb4a04bff66dfa0b8a26f24c653106444d5fe377329`.
- `docs/compatibility/mezo-evidence-v1.json`
  SHA-256: `10b19772b6dfea7e18bdbe79eb379a921812db41de0b60443391eba127965733`.

Both digests were checked with `sha256sum` (exit 0). The public observation
confirmed chain 31611, MUSD 18 decimals, x402 v2 exact, SDK family 2.16.0,
and BTC bid/ask sides with 20 levels each. It is time-dependent compatibility
evidence, not payment acceptance. The ordered blockers remain
`PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED`; no confirmation count or
receiver was invented. A funded buyer and real transfer/receipt remain absent.

## BLOCKED_TRIVY_HEALTHCHECK_POLICY

Trivy scanned three Dockerfiles. The root Dockerfile had zero findings.
Each of the following has exactly one LOW `DS-0026` missing-HEALTHCHECK finding:

- `deploy/images/Dockerfile.public-capture`
- `deploy/images/Dockerfile.readonly-analyzer`

Read-only inspection of these Dockerfiles, both Python CLI entrypoints,
`packages/public-capture/src/mee_public_capture/runtime.py`, and
`compose.stage-a.yml` shows one-shot jobs. They return explicit exit codes;
Compose uses `service_completed_successfully` and `restart: "no"`.
No running service or readiness endpoint exists. Re-running capture would
write evidence again; checking only process existence or returning success
would not verify successful completion.

A semantically justified healthcheck cannot be inferred from this job
contract. A separately scoped and reviewed policy/job-health decision is
needed. No Dockerfile, scanner setting, ignore, severity threshold, or waiver
was changed. This is a local verification blocker, not `BLOCKED_EXTERNAL`.

## Acceptance limits and safety

A01 passes only the F1 before/after evidence requirement. A27 passes the F1
Stage A regression suite. A28 remains NOT_RUN for the full clean-machine
README/build/demo scenario; A29 remains NOT_RUN against F1 publication.
F0 publication evidence is retained separately in PROVENANCE.md.
A13–A14 are BLOCKED_EXTERNAL; all other payment acceptance remains NOT_RUN.

No payment, signature, private-source verification, factory receipt,
deployment, push, merge, tag, or release occurred. Synthetic Git fixtures
do not constitute private-source verification. No credentials or secret
stores were read. Mainnet, custody, exchange mutation, merchant private
keys, and user secrets remain excluded; shadow-only remains in force.

## Closure documentation checks

At 2026-09-24T17:35:20Z, after the closure documents were written:

| Command | Exit | Result |
| --- | ---: | --- |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts` | 0 | Only the same seven declared conflicts |
| `PATH="$PWD/.venv/bin:$PATH" python -B -m ruff check tools/graph_checker tools/mezo_compatibility.py scripts/check-mezo-compatibility.py tests/graph tests/compatibility tests/readonly_analyzer/test_frozen_package_tamper.py tests/installed/test_root_development_toolchain.py` | 0 | All checks passed |
| `git diff --check` | 0 | No whitespace errors |

The two new tracked documents (this file and ADR-0002) have exact
`DOCUMENTATION` bindings to `document:graph-authority-handoff` in
`architecture/architecture.yaml`. Closure-only checks and final commit
verification are reported separately by the Task 5 implementation report.
