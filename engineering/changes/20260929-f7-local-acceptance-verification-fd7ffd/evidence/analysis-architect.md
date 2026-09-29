# F7 architecture analysis — bounded local acceptance aggregation

Route: `fd7ffd5cc17f`
Role: read-only architecture analysis
Inspected tree: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`

## Sources inspected

- `docs/planning/LIQVERA_FACTORY_TZ.md` sections 15–18 and the A01–A30 table.
- `tools/mezo_acceptance/{runner.py,cases.py}`, `scripts/run-mezo-acceptance.py`,
  `schemas/mezo-evidence/v1/acceptance-result.schema.json`, and their contract
  tests.
- F0/F1 acceptance matrix and F3–F6 change packages, verification evidence,
  review evidence, tests, and current `ready` lifecycle states.
- The F3 canonical artifact tests, F4 adapter/PostgreSQL tests, F5 fake state
  machine suite, F6 browser/static-operations suite, competition checklist,
  demo script, release/runbook material, README, architecture, and handoff.

## Architectural ruling

F7 should be a **local result-producing verifier**, not a new payment,
deployment, or release subsystem. It may execute deterministic assertions and
aggregate already retained F0–F6 facts, but a prior stage receipt is only an
input to an F7 assertion. It is not by itself permission to change an A-row to
`PASS`. Every `PASS` must still come from a command executed by the acceptance
runner on the bound clean Git identity and from a new sanitized evidence JSON
whose observations state exactly what was checked.

The safe vertical design is:

1. Add one repository-owned, offline assertion CLI/library with a closed
   registry of locally supportable cases. It invokes commands directly as
   argument arrays (never shell text), reads only repository files and
   explicitly named local evidence, and emits the runner's existing strict
   stdout/evidence protocol.
2. Add a checked-in offline plan containing only cases that the assertion CLI
   can prove end-to-end. Its `environment` lists must be empty. Cases without
   complete current proof are omitted, producing `NOT_RUN`; the five cases
   already marked live by `CASES` (`A07`, `A13`, `A14`, `A29`, `A30`) remain
   `BLOCKED_EXTERNAL` in offline mode.
3. Run the existing A01–A30 runner in offline mode against a clean, committed
   candidate. Validate the resulting JSON against the published schema and
   independently recalculate its repository identity, case inventory, evidence
   digests, status algebra, and omission rules.
4. Derive a separate readiness summary from that result and current blockers.
   The verdict is `NO_GO` unless **all 30 rows are `PASS`**. `INCOMPLETE`,
   `NOT_RUN`, `BLOCKED_EXTERNAL`, any failed local assertion, unresolved
   `PAY_TO_MISSING`/`FINALITY_RULE_UNVERIFIED`, missing clean install, or stale
   identity all force `NO_GO`. There is no partial or weighted release verdict.

This preserves the existing contract: the runner itself does not sign,
broadcast, pay, access an RPC/facilitator, clone/publish, deploy, or release.

## Critical identity/finalization constraint

The runner rejects a dirty worktree before starting. A result committed into
the repository necessarily changes the commit it names, so a result cannot
both be a tracked member of a commit and truthfully claim that same commit as
its observed identity. Do not solve this circularity by rewriting the result or
loosening `repo_identity()`.

Finalize in this order:

1. Commit every code, plan, documentation, package, and handoff change.
2. Reach a clean candidate tree and run all required verifier/reviews.
3. As the last evidence-producing action, write the A01–A30 result and derived
   readiness report outside the tracked worktree (a mode-0700 temporary
   directory or an ignored path under Git metadata), recording their SHA-256
   and absolute diagnostic location out-of-band.
4. Make no repository change after that run. If HEAD or the tree changes,
   discard the verdict and rerun both artifacts.

The durable package may document this procedure and the schema/plan, but must
not claim that a previously generated tracked result binds the later closure
commit. If retention inside Git is required later, it is historical evidence
for the named parent candidate, not evidence for the commit containing it.

## Evidence classification and safe case mapping

The present F3–F6 suites are valuable inputs, but their own scoped contracts
explicitly state that they did not relabel frozen vectors or A26/A30 as
acceptance. F7 may promote a row only by executing a purpose-built assertion
which checks the full A-row, not by checking that a stage is `ready` or that a
review report says `PASS`.

| Group | Existing local evidence | F7 treatment |
| --- | --- | --- |
| A01 | F1 separately recorded baseline/current evidence; current pinned verification exists | New assertion must verify both retained identities/results and the final candidate verification. Otherwise `NOT_RUN`. |
| A02–A06 | Exact-kernel/vector/schema tests, with all 156 catalog vectors still `NOT_RUN` | Execute the actual local kernel and negative inputs in an F7 assertion. Never infer PASS from schema validity or change catalog runtime statuses. |
| A07 | Requires a live-public outage/no-fallback observation | `BLOCKED_EXTERNAL` offline. No fixture substitution. |
| A08–A09 | Canonical F3 tamper/replay and installed-wheel tests | Re-execute the complete tamper matrix and offline replay in fresh temp roots; assert exact digest and zero network capability. Partial F3 receipt alone is insufficient. |
| A10–A12 | Static HTTP/payment contracts and exact lock | A12 can pass only if every named projection is rechecked. A10/A11 require executed gateway behavior, headers/body withholding, and entitlement absence; contract examples alone are insufficient. |
| A13–A14 | No retained real transfer; receiver/finality/funded buyer unresolved | Always `BLOCKED_EXTERNAL` in this scope. Never use fake F5 settlement as payment evidence. |
| A15–A22 | F4 PostgreSQL and F5 fake fault slices cover useful subsets | Each row needs one assertion covering every clause. Missing DB availability or incomplete crash/artifact/scope paths means `NOT_RUN`, not PASS. Fake settlement can prove safety behavior, never chain success. |
| A23–A25 | Compatibility, readiness, redaction and static security tests cover subsets | Execute exact negative configuration and canary scans. Any untested runtime/log/browser surface keeps the row `NOT_RUN`. |
| A26 | F6 resolved-Compose static isolation checks | May pass only through a new A26 assertion whose stated scope matches the acceptance wording. If container/runtime isolation is interpreted as required, static evidence remains `NOT_RUN`; do not silently narrow the criterion. |
| A27 | Current full suite and Stage A verdict tests | Re-run on exact candidate and check `GO` remains impossible; bind command output digests. |
| A28 | No retained full clean-machine README/install/build/demo acceptance | `NOT_RUN` unless performed in a new local isolated clean tree with exact lockfiles and no network need beyond already cached artifacts. Current package evidence says this is not complete. |
| A29 | Requires anonymous public clone/provenance comparison | `BLOCKED_EXTERNAL` offline; no network call in this route. |
| A30 | F6 fake browser coverage exists, but current runner classifies A30 live and F6 explicitly leaves A30 `NOT_RUN` | `BLOCKED_EXTERNAL` offline. Keep fake-browser results as supporting non-acceptance evidence only. |

The checked-in plan should therefore be intentionally incomplete unless the
implementation owner adds full deterministic assertions for a row. An honest
`INCOMPLETE` result is the expected current outcome and is not a defect.

## Local fault and negative suite

The F7 test layer should exercise the aggregator and runner themselves in
temporary directories, without databases or external processes beyond local
test commands:

- reject duplicate/unknown case IDs, unknown plan fields, unsafe arguments,
  URLs, credential-like arguments, invalid timeouts, duplicate/invalid env
  names, and any nonempty environment list in the project-owned offline plan;
- reject dirty-tree execution, mismatched origin, reused output paths,
  symlink/absolute/traversal evidence paths, oversized evidence, invalid JSON,
  empty observations, mismatched case/assertion identity, sensitive keys and
  sensitive values;
- convert assertion timeout, nonzero exit, malformed stdout, extra/missing
  protocol fields, missing evidence, and digest mismatch into a local `FAIL`,
  never `NOT_RUN` or `BLOCKED_EXTERNAL`;
- prove that omitted offline cases are `NOT_RUN`, live cases are
  `BLOCKED_EXTERNAL`, any `FAIL` makes the overall result `FAIL`, any omission
  makes it `INCOMPLETE`, and only 30 executed passes can yield `PASS`;
- mutate one retained stage report/status/digest/HEAD and ensure aggregation
  fails closed rather than trusting filenames or prose;
- verify stable A01–A30 ordering, exact titles/assertions, 30 unique rows,
  schema validation, exact evidence digest/size, and no raw stdout/stderr or
  environment values in the result;
- verify the readiness summary refuses GO for every single-row mutation from
  PASS to `FAIL`, `NOT_RUN`, or `BLOCKED_EXTERNAL`, and for identity mismatch.

Subprocesses should receive a minimal deterministic environment and use an
explicit interpreter path. No shell, inherited proxy variables, credential
environment, network namespace, Docker, PostgreSQL, browser wallet, or RPC is
needed for this route.

## Data and contract boundaries

- `schemas/mezo-evidence/v1/acceptance-result.schema.json` remains the canonical
  result envelope. Prefer adding a separate schema for a machine-readable
  readiness summary rather than overloading acceptance rows.
- Existing stage `state.json`, review reports, and receipts are append-only
  workflow evidence. The aggregator must validate declared identities and
  digests; it must not edit prior packages or translate lifecycle `ready` into
  acceptance PASS.
- No SQL, migration, backfill, database, volume, ledger mutation, or frozen
  vector status edit is architecturally required. The data migration plan is a
  literal no-op.
- Result/evidence files contain no secrets, signatures, bearer values,
  capabilities, wallet material, environment values, or raw command output.
  Payment fields are forbidden except the runner's strict A13/A14 shapes, which
  cannot occur in this offline route.

## Competition and demo claims

The checklist must remain unchecked and the demo script must remain an
operator draft while the result is incomplete. A local `NO_GO` readiness
report may truthfully say that deterministic offline/fake/static components
passed, but must also say:

- no live Hyperliquid observation, anonymous clone, wallet interaction,
  facilitator/RPC, or testnet transfer was performed;
- A13/A14 and payment readiness remain blocked;
- fake F5 and F6 behavior is not live acceptance;
- no deployment, publication, tag, push, merge, GitHub Release, hosted URL, or
  video was produced;
- the artifact is a local candidate assessment, not release authorization.

## Gates

1. `scope_and_design_approval` is mandatory before implementation. The exact
   scope must name the allowed local assertion files, tests, plan, and
   out-of-tree result/readiness artifacts.
2. `migration_or_external_write_approval` is **not consumed** by this design:
   migration and external writes are forbidden/no-op. If implementation finds
   it needs a database, RPC, wallet, transfer, public clone, container start,
   deployment, publication, push, tag, merge, or release, stop and obtain a new
   exact approval; do not reinterpret the current local gate as authorization.
3. Independent code, test, security, data, and release reviews must inspect the
   same final candidate, followed by fresh fingerprint-bound verification.

## Rollback and stop conditions

Rollback is source-only: revert the F7 assertion/aggregation code, plan,
schemas, tests, and documentation as one coherent change, then rerun the
existing F0–F6 verifier. Generated result/readiness artifacts are immutable
evidence; supersede them with a new run instead of editing them.

Stop and return `NO_GO` if any of the following occurs: candidate identity
changes, worktree is dirty, evidence digest or assertion identity mismatches,
one local command fails/times out, a required case is omitted, a stage receipt
is stale, sensitive material is detected, a test attempts network/external
state, or any live/payment/release action would be required. No rollback may
delete or rewrite prior ledger, stage, or acceptance evidence.

## Recommendation

Proceed after the exact scope/design gate with the bounded offline assertion
registry, fail-closed readiness summarizer, mutation-heavy local tests, and an
intentionally honest result. The expected current release verdict is
**`NO_GO / INCOMPLETE`**, principally because A13/A14 and other external/live
criteria are not satisfied. That outcome successfully completes the local F7
verification boundary; it does not complete product acceptance or authorize a
release.
