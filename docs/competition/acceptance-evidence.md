# Competition acceptance evidence

## Acceptance runner

`python3 scripts/run-mezo-acceptance.py --mode offline --output <new-result-path>` writes an A01–A30 result with no assertions run. It reports `NOT_RUN` for unconfigured offline cases and `BLOCKED_EXTERNAL` for live cases. This is useful for an honest inventory; it is not a passing report. The worktree must be clean and committed so the result can bind to an exact commit and Git tree. Each invocation requires a new output path and exits nonzero while incomplete or failed.

To execute assertions, supply `--plan <json-path>`. The plan has `schema: "liqvera-acceptance-plan/v1"` and a `commands` array. Each entry has exactly `case_id`, `argv` (an argument array, without shell evaluation or credentials), `timeout_seconds` (1–3600), and `environment` (variable names only). The runner passes only named variables plus `LIQVERA_ACCEPTANCE_EVIDENCE_DIR`. Keep credentials in the operator's secret store and never put them in the plan or command line. An assertion program must write a sanitized JSON evidence file under that directory and print one JSON object to stdout:

```json
{"case_id":"A02","assertion":"buy_exact_values","evidence_file":"evidence/A02.json"}
```

The evidence file must contain the same `case_id` and `assertion` plus a nonempty `observations` array. The runner checks that it is a regular JSON file below the evidence directory, caps it at 10 MB, rejects common secret fields and value patterns, and records its SHA-256 and size. Raw stdout, stderr, capabilities, signatures, and environment values are not copied into the result. A zero exit code and a correctly bound evidence file are both necessary for `PASS`; the assertion program remains responsible for actually testing every part of the named criterion. Review the evidence before sharing it; automated redaction cannot prove absence of every possible secret.

The historical live acceptance operator uses short-lived grants and its dedicated paths. Current merchant checkout instead requires an explicit owner-authorized run and a fresh buyer wallet signature. The acceptance runner does not create either authority. Retained sealed evidence now records A07,
A13, A14, and A29 PASS: A07 observed `SOURCE_UNAVAILABLE` without fixture
fallback/artifact; A13/A14 bind one confirmed Mezo Testnet MUSD transaction and
exactly one settlement; A29 is the credential-disabled anonymous recursive
clone of published v0.0.1. Alongside the five local passing cases this is a
multi-result projection of 9 PASS and 21 NOT_RUN, with zero remaining
BLOCKED_EXTERNAL. It is not a single runner overall PASS. The runner never
signs, broadcasts, pays, trades, or substitutes fixture data by itself; the
dedicated payment operator and human-held wallet remain separately gated.

The result shape is [`acceptance-result.schema.json`](../../schemas/mezo-evidence/v1/acceptance-result.schema.json). It records all thirty cases, command and environment names, start/end times, exit codes, explicit omissions, evidence digests, commit SHA and Git tree. A result with any omitted case is `INCOMPLETE`; no partial result should be described as F7 acceptance. Do not edit results to change statuses. Repeat the run after code changes and retain the prior result as historical evidence.


## Retained native Mezo extension: A31/A32

The optional `mezo-readonly` suite is separate from the immutable A01–A30 contract.
A31 reproduces the native DEX comparison and A32 reproduces the native Trove report
from their retained ZIPs. Both are offline snapshot checks; PASS does not claim a
fresh paid purchase, production deployment or overall live acceptance.

```sh
.venv/bin/python scripts/run-mezo-acceptance.py --suite mezo-readonly \
  --mode offline --plan acceptance/mezo-readonly-plan.json --output /absolute/new/result.json
.venv/bin/python scripts/verify-mezo-acceptance.py --suite mezo-readonly \
  /absolute/new/result.json --sha256 <independently-recorded-result-digest>
```

Keep the adjacent `result.json.evidence` directory with the JSON. Verification checks
its exact member set, pinned native bundle/report digests, raw-call reconstruction,
block identity, call count and source engine. Existing core commands remain unchanged.

The [October 23 source gate](2026-10-23-mezo-trove/api/verification.json) records a
successful complete offline run and independent source review. Its adjacent
[acceptance result](2026-10-23-mezo-trove/api/acceptance.json) pins A31/A32 and includes
both native ZIPs. Its source is `268078c8ad86a4891ad13e7532287a1d629841ee`; use
`--allow-detached-subject` when verifying that historical result from a later commit.
The independent [native smoke](../../evidence/mezo-testnet/2026-10-23-live-smoke/result.json)
records fresh Testnet raw-call observations at blocks 16324346 and 16324347. It is
separate from the retained preview blocks and does not assert a paid purchase.
