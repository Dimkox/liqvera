# Competition evidence and submission

Liqvera — **Market reports you can verify.** Built for MEZO ₿ at The Mezo Buildathon.

These are preparation documents, not a submission or proof of a running payment flow. The imported Multi-Exchange Engine baseline and subsequent Liqvera commits must be distinguished in the final entry. The canonical scope and acceptance criteria are in [`LIQVERA_FACTORY_TZ.md`](../planning/LIQVERA_FACTORY_TZ.md); provenance is in [`PROVENANCE.md`](../../PROVENANCE.md).

## Acceptance runner

`python3 scripts/run-mezo-acceptance.py --mode offline --output <new-result-path>` writes an A01–A30 result with no assertions run. It reports `NOT_RUN` for unconfigured offline cases and `BLOCKED_EXTERNAL` for live cases. This is useful for an honest inventory; it is not a passing report. The worktree must be clean and committed so the result can bind to an exact commit and Git tree. Each invocation requires a new output path and exits nonzero while incomplete or failed.

To execute assertions, supply `--plan <json-path>`. The plan has `schema: "liqvera-acceptance-plan/v1"` and a `commands` array. Each entry has exactly `case_id`, `argv` (an argument array, without shell evaluation or credentials), `timeout_seconds` (1–3600), and `environment` (variable names only). The runner passes only named variables plus `LIQVERA_ACCEPTANCE_EVIDENCE_DIR`. Keep credentials in the operator's secret store and never put them in the plan or command line. An assertion program must write a sanitized JSON evidence file under that directory and print one JSON object to stdout:

```json
{"case_id":"A02","assertion":"buy_exact_values","evidence_file":"evidence/A02.json"}
```

The evidence file must contain the same `case_id` and `assertion` plus a nonempty `observations` array. The runner checks that it is a regular JSON file below the evidence directory, caps it at 10 MB, rejects common secret fields and value patterns, and records its SHA-256 and size. Raw stdout, stderr, capabilities, signatures, and environment values are not copied into the result. A zero exit code and a correctly bound evidence file are both necessary for `PASS`; the assertion program remains responsible for actually testing every part of the named criterion. Review the evidence before sharing it; automated redaction cannot prove absence of every possible secret.

Live cases require exact short-lived grants and their dedicated operator paths;
a boolean does not authorize them. Retained sealed evidence now records A07,
A13, A14, and A29 PASS: A07 observed `SOURCE_UNAVAILABLE` without fixture
fallback/artifact; A13/A14 bind one confirmed Mezo Testnet MUSD transaction and
exactly one settlement; A29 is the credential-disabled anonymous recursive
clone of published v0.0.1. Alongside the five local passing cases this is a
multi-result projection of 9 PASS and 21 NOT_RUN, with zero remaining
BLOCKED_EXTERNAL. It is not a single runner overall PASS. The runner never
signs, broadcasts, pays, trades, or substitutes fixture data by itself; the
dedicated payment operator and human-held wallet remain separately gated.

The result shape is [`acceptance-result.schema.json`](../../schemas/mezo-evidence/v1/acceptance-result.schema.json). It records all thirty cases, command and environment names, start/end times, exit codes, explicit omissions, evidence digests, commit SHA and Git tree. A result with any omitted case is `INCOMPLETE`; no partial result should be described as F7 acceptance. Do not edit results to change statuses. Repeat the run after code changes and retain the prior result as historical evidence.

## Current evidence and limitations

The historical F1 blockers were later closed by sealed A07, A13, A14, and A29
evidence. Published v0.0.1 and the exact testnet transaction are indexed from
the root handoff; this document does not duplicate wallet material or raw
payloads. The follow-up v0.0.2 projection has 9 PASS, 21 NOT_RUN, zero
BLOCKED_EXTERNAL, and zero FAIL across distinct sealed results. It remains
INCOMPLETE and must not be called a single runner overall PASS. Existing F2
contract vectors remain NOT_RUN at runtime, and no hosted-demo or video claim
is supplied here. See [`handoff.md`](../../handoff.md) for exact hashes and the
current release state.
