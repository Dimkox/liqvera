# F7 data and evidence-boundary analysis

Route: `fd7ffd5cc17f`
Role: `data_architect`
Disposition: proceed only with a local, fail-closed acceptance/evidence repair. **No database, migration, container, wallet, RPC, facilitator, transfer, deployment, publication, push, tag, merge, or release action is required or authorized.**

## Executive finding

The A01–A30 runner has a useful closed command protocol, hashes retained JSON evidence, records the Git commit/tree, blocks live-marked cases without an explicit live flag, and correctly requires A14 to reuse the passing A13 transaction with one settlement. However, the result format is not yet an independently trustworthy acceptance authority:

1. the JSON Schema accepts `overall_status: PASS` with thirty duplicated `A01` rows that are all `NOT_RUN`;
2. the schema accepts a `FAIL` row with no command, execution timestamps, hashes, evidence, or omission;
3. the runner establishes clean commit/tree identity only before executing assertion programs and never proves that identity is unchanged afterward;
4. evidence is hashed when each case finishes but is not re-opened and re-hashed before the result is sealed, so a later case can overwrite an earlier evidence file; the output path itself can also be named as a case evidence file and then be replaced by the final report;
5. the runner does not validate its completed document against the published schema before writing it;
6. `Case.live` conflates external execution with UI/fault semantics. In particular A30 is deterministic fake-browser work already exercised locally, but the offline runner always labels it `BLOCKED_EXTERNAL`.

These are evidence-integrity defects, not reasons to weaken status truth. Until repaired and tested, a generated report may be useful as an observation but must not by itself support a release-candidate or competition claim.

## Reproduction evidence

Read-only local probes against HEAD `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c` produced:

```text
overall_PASS_with_30_NOT_RUN_duplicates_schema_errors= 0
FAIL_without_execution_or_omission_schema_errors= 0
```

The probe used `Draft202012Validator` with `schemas/mezo-evidence/v1/acceptance-result.schema.json`; no repository or external state was changed. The existing focused suite still passes:

```text
.venv/bin/python -m pytest -q tests/contracts/test_acceptance_result.py
14 passed in 2.55s
```

That suite currently covers exact Git OID shape and digest-string canonicality only. It has no runner fault tests for evidence replacement, post-command tree mutation, status aggregation, complete case inventory, timeouts, output collision, secret-bearing evidence, or live/offline classification.

## Result-schema and aggregation contract

The runner constructs rows in canonical `CASES` order and derives overall status correctly in-process (`runner.py:232-251`), but those invariants disappear when a stored result is consumed independently:

- `cases` only has `minItems/maxItems: 30`; it does not establish one each of A01–A30 (`acceptance-result.schema.json:34,75-101`). JSON Schema `uniqueItems` alone is insufficient because it compares whole objects rather than `case_id`.
- `overall_status` is a free enum and is not coupled to case statuses (`:33-34`). A semantic validator must enforce `FAIL` if any row fails, `PASS` only if every A01–A30 row passes, otherwise `INCOMPLETE`.
- `FAIL` has no conditional requirements. It must represent an attempted assertion and retain at least start/end, a non-null command, an exit result or timeout marker, stdout/stderr digests when a child ran, and a non-empty stable omission/reason. Setup failures belong to runner exit 2 and must not masquerade as a case failure.
- `NOT_RUN` must mean the assertion was intentionally not invoked because no approved/configured command exists. It must never absorb an execution failure or external outage.
- `BLOCKED_EXTERNAL` must identify a specific unavailable or forbidden external prerequisite. `LIVE_AUTHORIZATION_ABSENT` is an honest policy blocker for this route, but is not evidence that an external service was probed and found unavailable. The final readiness report should preserve that distinction in its omission reason.
- Stored results need a semantic validation entry point shared by producer and tests. The runner should refuse to seal a document that fails either JSON Schema or the cross-row semantic checks.

The schema should remain backward compatible at the envelope/version level if possible, but tightening previously invalid combinations is appropriate. A separate semantic validator is preferable to encoding all cross-row rules in fragile JSON Schema conditionals.

## Fingerprint and evidence binding

`repo_identity()` checks a clean worktree and records `HEAD`/`HEAD^{tree}` only once (`runner.py:34-59,222`). Assertion commands then execute with repository working directory and ordinary filesystem authority (`:169-209`). There is no post-run identity comparison before the report is written. A command can therefore change tracked/untracked repository state or move HEAD while the result continues to claim the earlier clean identity.

Minimum repair:

1. capture the initial identity;
2. execute the planned cases;
3. before sealing, recalculate identity and require the same commit, tree, canonical origin, and clean status;
4. place output/evidence outside the repository, or define and enforce an explicit excluded output root. For F7, an OS temporary directory outside the worktree is the simpler non-circular boundary;
5. reject evidence paths that resolve to the final output path or a runner temporary-file namespace;
6. require a unique evidence path per passing case and re-open/re-hash every referenced file after all commands finish and immediately before atomically replacing the result;
7. bind each evidence document to at least `case_id`, exact assertion, subject commit, and subject tree. The top-level result alone is not enough if evidence files are copied or aggregated separately;
8. preserve the command stdout/stderr SHA-256 fields, but do not claim those streams are independently reviewable unless sanitized bytes are actually retained. Hash-only command output is provenance metadata, not review evidence.

The result itself can be retained outside Git and bind the final clean commit without recursion. If copied into a later commit, it remains evidence about its recorded subject commit; it must not be relabelled as evidence for the report-bearing commit.

## Evidence retention, overwrite, and secret boundaries

`evidence_reference()` usefully restricts evidence to regular JSON below the selected directory, caps it at 10 MiB, requires case/assertion/observations, hashes exact bytes, and recursively rejects sensitive-looking field names and several raw-value patterns (`runner.py:99-130`). Residual boundaries are:

- hashes are checked only at ingestion, not at final sealing or later consumption;
- no per-case path uniqueness or immutable creation rule prevents later overwrite;
- no retention manifest states where the result/evidence set lives, how long it is retained, or whether every referenced digest still resolves;
- field-name filtering is heuristic. It must be defense in depth, not the proof for A25. A25 needs explicit canary tests against application/proxy/browser artifacts and logs, with only sanitized absence observations retained;
- secret values may be supplied only through explicitly named environment variables. The report may retain names, never values. No test may read `.env`, deployed secret files, wallet material, credential stores, or ambient production configuration;
- evidence JSON must exclude raw headers, cookies, bearer capabilities, signatures, seed phrases, private keys, database credentials, payment payloads, and participant email. Transaction hashes, block hashes, log indexes, and public addresses are permitted only for separately authorized A13/A14 execution, which this route forbids.

For the local F7 artifact, use a fresh `0700` temporary evidence directory, exclusive file creation, deterministic filenames (`A01.json` …), a final manifest/re-hash pass, and cleanup only after the reviewed result/evidence bundle has been copied to its explicitly approved durable location. Do not delete or rewrite any F0–F6 source evidence while aggregating it.

Product retention remains a separate unresolved runtime obligation. The contract requires paid artifacts for at least seven days; unpaid cleanup no earlier than the 15-minute grace and never while payment is pending/unknown; ledger, scope binding, and dedup for at least 30 days and through authorization validity; and replay protection until reviewed evidence proves reuse impossible (`LIQVERA_FACTORY_TZ.md:222-232`, `states.json:75-76`). F5 explicitly left this persistent-store behavior unproved. F7 may report it `NOT_RUN`/residual; it must not infer PASS from static schema constants or temp-file tests.

## Truthful mapping of existing evidence

All 156 frozen vectors still declare `runtime_status: NOT_RUN` (39 F3, 88 F4, 29 F5). Their schema/contract tests prove inventory consistency, not runtime execution. Do not bulk-edit those statuses from F3–F6 focused tests.

Existing evidence may be consumed only through a case-specific assertion command that verifies the exact retained file/digest and explains what it does and does not prove. Suggested treatment:

| Cases | Local F7 treatment |
| --- | --- |
| A01 | May PASS only if the assertion verifies separately retained baseline and current-final-commit results; old prose alone is insufficient. |
| A02–A06, A08–A12, A15–A25, A27–A28 | Eligible for deterministic local execution where the exact acceptance assertion is covered. Focused stage tests are inputs, not automatic PASS. Uncovered acceptance semantics remain NOT_RUN. |
| A07 | Keep BLOCKED_EXTERNAL under this no-live-public route. A deterministic no-fallback fault test may be retained as local supporting evidence but cannot replace the specified live-source condition. |
| A13–A14 | BLOCKED_EXTERNAL: no merchant/finality approval, funded buyer, wallet, RPC, transfer, or testnet authorization. Mock settlement never satisfies either case. |
| A26 | Static Compose/network assertions are supporting evidence only. Without an approved container/network-isolation execution, the full acceptance case remains NOT_RUN. |
| A29 | BLOCKED_EXTERNAL because this route forbids publication/anonymous network checks; historical provenance does not become a fresh final-commit clone check. |
| A30 | Should be locally executable with the deterministic fake-browser harness and no wallet/network. Remove its blanket `live=True` classification or split local UI recovery from any separately external demo assertion. |

The final aggregate will therefore be `INCOMPLETE`, not `PASS`, while any required case is `NOT_RUN` or `BLOCKED_EXTERNAL`. `FAIL` is reserved for an executed assertion that disproves the requirement or cannot complete after starting; it is not a synonym for an unavailable approval.

## Deterministic local fault-test matrix

The write owner should add regression tests before repair and keep all subprocesses/fakes local:

| Fault/probe | Required observation |
| --- | --- |
| 30 duplicate A01 rows, overall PASS with non-PASS rows, missing A30 | semantic validation rejects |
| FAIL row without attempted command/reason | validation rejects |
| assertion exits nonzero | row FAIL; exit/hash/timestamps retained; overall FAIL |
| assertion times out | row FAIL with stable timeout omission; no PASS evidence |
| malformed/oversized stdout or wrong case/assertion | row FAIL; no evidence admitted |
| evidence symlink, traversal, oversized JSON, sensitive key/value | row FAIL |
| two cases reuse/overwrite one evidence path | final sealing rejects stale/duplicate reference |
| evidence path equals final output path | setup/sealing rejects; original evidence cannot be replaced by report |
| assertion modifies a tracked file, creates an untracked file, or moves HEAD | final identity check aborts result publication |
| evidence bytes change after case return | final re-hash aborts publication |
| A14 without passing A13 or with different tx/more than one settlement | FAIL |
| offline run with A13/A14/A29 | explicit BLOCKED_EXTERNAL with precise policy reason, no command execution |
| offline A30 fake-browser assertion | locally executable, no live authorization required, zero wallet/RPC/network calls |
| no plan | exactly 30 canonical rows, truthful INCOMPLETE, schema plus semantic validation PASS |

Tests should use `tmp_path`, monkeypatched `ROOT`/Git identity where necessary, tiny local helper processes, and synthetic canaries. They must not read secrets, start PostgreSQL/Compose, or make network calls.

## Migration and recovery assessment

- Schema migration/backfill/index/query-plan impact: **none**. The only schema in scope is the JSON acceptance-result contract, not a database schema.
- Data mutation: new temporary assertion evidence and a final local report only. Existing F0–F6 evidence is read-only.
- Rollback: revert runner/schema/tests/report-documentation changes and discard only the exact F7 temporary output directory. Never delete prior stage evidence or product persistence.
- Forward recovery: a rejected/stale report is regenerated from a clean exact subject commit after fixing the assertion or evidence binding; statuses are never hand-promoted.
- Stop conditions: any request for wallet/RPC/facilitator/transfer, external/live-public access, shared environment, database/container startup, secret-file access, publication/deploy/push/release, evidence overwrite, changed subject tree, or attempted conversion of mocked/static evidence into A13/A14/runtime-vector PASS.

## Recommended bounded implementation

Use the existing single write owner to add semantic result validation, post-run Git identity verification, collision-free immutable evidence references with a final re-hash, and focused deterministic fault tests. Correct A30's local/external classification and produce a truthful F7 readiness report whose overall status remains `INCOMPLETE` with explicit blockers. Do not alter migrations, ledger data, frozen vector runtime statuses, payment readiness, unresolved identity/finality flags, or any external system.
