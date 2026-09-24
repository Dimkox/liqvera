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

For planned live cases, use `--mode live --authorize-live` only after the operator has authorized the exact read-only or limited testnet activity in the plan. Without both, A07, A13, A14, A29, and A30 stay `BLOCKED_EXTERNAL`. A13 additionally requires the confirmed Mezo Testnet MUSD Transfer's transaction hash, block hash, log index, distinct buyer/merchant addresses, network, asset and atomic amount. A14 must bind to the same transaction and show exactly one settlement. These fields are an evidence index, not independent chain verification; the assertion program and reviewer must check canonical receipt, finality and entitlement against the chain and ledger. The runner never signs, broadcasts, pays, trades, or substitutes fixture data for live data by itself.

The result shape is [`acceptance-result.schema.json`](../../schemas/mezo-evidence/v1/acceptance-result.schema.json). It records all thirty cases, command and environment names, start/end times, exit codes, explicit omissions, evidence digests, commit SHA and Git tree. A result with any omitted case is `INCOMPLETE`; no partial result should be described as F7 acceptance. Do not edit results to change statuses. Repeat the run after code changes and retain the prior result as historical evidence.

## Current blockers

The F1 compatibility probe found `PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED`. A funded dedicated test buyer, confirmed receipt, full canonical authorization identity and live end-to-end test are still absent from retained evidence. A13–A14 cannot pass on a fixture or mocked settlement. Existing F2 contract vectors are `NOT_RUN` at runtime. The inherited Trivy healthcheck policy findings are a local verification blocker, not an external outage. See [`handoff.md`](../../handoff.md) and the [acceptance matrix](../../engineering/changes/2026-09-24-mezo-evidence/acceptance-matrix.md) for the last recorded state.

No result file, video link, hosted-demo URL, testnet transaction, or release claim is supplied here. Add each only after it exists and has been independently checked.
