# F1 verification evidence

Original observation window: 2026-09-24T17:59:23Z–2026-09-24T18:01:38Z
(UTC). Revalidated after PR history hygiene on 2026-09-24 before 18:25:49Z.
Implementation SHA: `37d3e2cf3c64ef2c5d260bccf64e4f107e3f2c25`.
Branch: `feat/mezo-evidence-f1-impl`.
The rewritten implementation SHA was checked in a clean detached worktree.
`make verify` and the live compatibility probe were repeated after replacing
a synthetic Basic Auth test literal that triggered GitGuardian; production
bytes did not change. This report belongs to a later documentation commit,
not a new implementation or factory receipt. Final independent re-review is
complete.

## Result and scope

F1 is **complete-with-blockers**. Public baseline repairs and compatibility
evidence exist, but the full verification pipeline remains FAIL.
The overall change is `implementing`; F2–F7 remain open.
Payment readiness is false. No final-product acceptance or release is claimed.

The initial failures remain recorded in
[source-baseline.md](source-baseline.md) against
`d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a`.
Tasks 1–4 and the final-review transport repair end at the implementation SHA above.
The accepted [ADR-0002](../../../../docs/adr/0002-liqvera-report-payment-boundary.md)
does not freeze F2 API/database contracts.

## Environment and exact commands

Commands ran from the implementation worktree using its existing `.venv`.
The installation was not repeated during closure. Task 3's clean install
and pin repair are historical evidence, not a fresh A28 run.

| Command | Exit | Observed result |
| --- | ---: | --- |
| `git rev-parse HEAD` | 0 | 37d3e2cf3c64ef2c5d260bccf64e4f107e3f2c25 |
| `date -u +%Y-%m-%dT%H:%M:%SZ` | 0 | Rewritten-SHA live/focused sequence: 2026-09-24T18:25:37Z–18:25:49Z |
| `.venv/bin/python --version` | 0 | Python 3.12.3 |
| `.venv/bin/python -m pytest --version` | 0 | pytest 9.1.1 |
| `.venv/bin/python -c 'import importlib.metadata as m; print("hatchling " + m.version("hatchling"))'` | 0 | hatchling 1.32.4 |
| `.venv/bin/python -m pip check` | 0 | No broken requirements found |
| `PATH="$PWD/.venv/bin:$PATH" make verify` | 0 | Rewritten clean SHA: 641 passed, 85 subtests passed in 137.64s; stage-a verify passed |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/grok_verify.py --mode pr --no-record` | 1 | Tree-equivalent predecessor: RESULT: FAIL; only trivy-config failed; final PR-integration rerun is recorded separately after main synchronization |
| `trivy config --exit-code 1 .` | 1 | 17:59:23Z–17:59:25Z: exactly two LOW DS-0026 findings; details below |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-mezo-compatibility.py --lock docs/compatibility/mezo-evidence-v1.json` | 0 | Rewritten clean SHA, 18:25:37Z–18:25:49Z: COMPATIBILITY_PASS_PAYMENT_BLOCKED |
| `PATH="$PWD/.venv/bin:$PATH" python -B -m pytest tests/compatibility/test_mezo_compatibility.py::test_ambient_proxy_credentials_never_reach_transport -q` | 0 | Rewritten clean SHA: 1 passed in 0.18s; the full 107-test compatibility directory also ran inside `make verify` |
| `git diff --check` | 0 | No whitespace errors |
| `git status --short` | 0 | Empty before documentation changes |
| `.venv/bin/python scripts/grok_status.py` | 0 | route=null, change=null, evidence_gaps=[]; no active factory run |

Dates in the table are UTC on 2026-09-24. `date -u` ran before and after the
long commands; their original exit codes were preserved by the shell wrapper.
Environment inspection, `pip check`, hashes, and Grok status ran alongside
those read-only checks. No dependency installation or npm invocation occurred.

The following focused sequence exited 0 on the tree-equivalent predecessor at
17:59:23Z–17:59:32Z, after its 107-test run. Final PR-integration checks after
main synchronization supersede this sequence for merge readiness:

```bash
PATH="$PWD/.venv/bin:$PATH" python -B -m ruff check tools/graph_checker tools/mezo_compatibility.py scripts/check-mezo-compatibility.py tests/graph tests/compatibility tests/readonly_analyzer/test_frozen_package_tamper.py tests/installed/test_root_development_toolchain.py
PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts
git diff --check
```

Ruff reported `All checks passed!`; the graph emitted only the same seven
declared conflicts, and the diff check found no whitespace errors.

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

The implementation and covering tests were also hashed with `sha256sum`
(exit 0) on the clean implementation SHA:

- `tools/mezo_compatibility.py`:
  `ce484e73f802b87a100f52767da0a6d4da4edfa69c4e5d4ad9d394d52cee79ff`.
- `tests/compatibility/test_mezo_compatibility.py`:
  `ea00ce86bbb1e9b63034e68a0daedf7b87156f2ced4dad2ea7f3611f71d313bd`.

## Final-review transport repair

A framing-only live inspection found Content-Length on nine fixed reads and
legitimate chunked transfer for Mezo `eth_getCode`. The repair therefore keeps
chunked support in a private strict reader rather than requiring a length
header that the bytecode endpoint does not supply.

The reader limits decoded payload to 2 MiB, framing to 64 KiB independently,
and each status/header/chunk-framing line to 8 KiB. Total consumed wire bytes
cannot exceed the payload plus framing budgets. Normal fixed-size stdlib
socket/TLS buffers remain. Chunk extensions, all trailers, invalid chunk-data
CRLF, and missing terminal CRLF fail closed. Proxy refusal, redirect refusal,
identity encoding, fixed URL/body/package pins, and Content-Length validation
remain intact.

One synchronous 12-second deadline covers connection/TLS, headers, body, and
chunk termination. POSIX real-time timer support, the main thread, and an
inactive caller real-time timer are required; otherwise the probe fails
closed before I/O. The previous handler is restored and the temporary timer
cleared in `finally`; an already-active caller timer is left untouched.
No background transport thread or child process is created.

Real-wire TDD reproduced the finding before repair: 10 failed and 89 passed.
The final focused suite has 107 passing tests, including large trailers,
malformed termination, independent framing/body limits, slow header/body/
chunk-ending streams, stalled TLS handshake, signal restoration, worker
cleanup, and positive bounded Content-Length/chunked responses. These are
offline or loopback checks; the separate fresh live probe confirms the
fixed endpoints still work through the repaired transport. No final-product
or payment acceptance is inferred.

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

After refreshing the closure documents, at 2026-09-24T18:05:29Z–18:05:32Z:

| Command | Exit | Result |
| --- | ---: | --- |
| `PATH="$PWD/.venv/bin:$PATH" python -B scripts/check-architecture-graph.py --manifest-root architecture --phase precommit --allow-declared-conflicts` | 0 | Same seven declared conflicts; exact bindings remain valid |
| `.venv/bin/python -m json.tool engineering/changes/2026-09-24-mezo-evidence/state.json` | 0 | Valid JSON; overall state remains implementing |
| `git diff --check` | 0 | No whitespace errors |
| `sha256sum tools/mezo_compatibility.py tests/compatibility/test_mezo_compatibility.py engineering/changes/2026-09-24-mezo-evidence/evidence/f1-compatibility.json docs/compatibility/mezo-evidence-v1.json` | 0 | All four digests still match the implementation evidence above |

This file and ADR-0002 retain their exact
`DOCUMENTATION` bindings to `document:graph-authority-handoff` in
`architecture/architecture.yaml`; no placeholder evidence or new binding was
introduced. Closure-only checks and both final fix-wave commit identities
are recorded in the Task 4 implementation report for independent re-review.
