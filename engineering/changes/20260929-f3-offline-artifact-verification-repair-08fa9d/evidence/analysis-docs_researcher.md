# Documentation and contract analysis — F3 offline acceptance identity

Route: `08fa9d84745d`  
Role: `docs_researcher` (read-only analysis)  
Scope: acceptance identity and executable-plan coverage relevant to the local,
offline F3 tranche.

## Executive finding

The acceptance result producer and its published JSON Schema disagree on both
repository identity fields. The runner writes the Git commit and tree object
IDs returned by `git rev-parse`, which are 40 lowercase hexadecimal characters
in this SHA-1 repository. The schema requires both fields to match its
64-character `sha256` definition. Consequently, a result produced by the
canonical runner cannot validate against the schema named by the documentation.

The acceptance runner also has no checked-in executable acceptance plan or
assertion program. The `liqvera-acceptance` Make target does not accept or pass a
plan, so it intentionally produces only an honest `INCOMPLETE` inventory. That
behavior matches the current documentation, but it cannot provide F3 runtime
acceptance for A02–A09 without additional, explicitly bounded offline assertion
coverage.

## Evidence

### 1. Git/tree identity length mismatch — confirmed defect

- `tools/mezo_acceptance/runner.py:53-58` fills `repository.commit` with
  `git rev-parse HEAD` and `repository.tree` with
  `git rev-parse HEAD^{tree}`.
- `git rev-parse --show-object-format` reports `sha1` for this repository.
- At analysis HEAD, the emitted values are
  `bed18457b084f9c9f15dd8bee24c31a74323e639` and
  `2caf0e76a1abc52c1952503fecd0ae6436d6e448`, each 40 characters.
- `schemas/mezo-evidence/v1/acceptance-result.schema.json:18-19` references
  `#/$defs/sha256` for both fields; line 37 defines that as exactly 64 lowercase
  hexadecimal characters.
- `docs/competition/README.md:21` identifies that schema as the authoritative
  result shape, so this is not merely an unused-schema inconsistency.
- The runner serializes the result directly at `runner.py:248-256`; it does not
  validate its own output against the published schema. No test under `tests/`
  invokes `repo_identity`, `read_plan`, or the acceptance runner, or validates a
  produced result against `acceptance-result.schema.json`.

Required repair: define Git object IDs separately from content SHA-256 digests.
For this canonical repository, the minimal compatible contract is a lowercase
40-hex Git OID for `commit` and `tree`. If intentional SHA-256-repository support
is required, name the definition `git_oid`, permit only the explicitly supported
40/64 forms, record/detect the object format, and test both. Do not hash the
40-character Git IDs into unrelated 64-character strings: that would no longer
identify the commit/tree Git objects.

Required regression: generate a result from a clean temporary Git repository
using the supported object format, validate the complete document against the
published schema, and assert that the recorded commit/tree equal `rev-parse`
exactly. Also mutate either identity to wrong length/non-hex and require schema
rejection.

### 2. No executable offline acceptance plan — confirmed coverage gap

- `runner.py:62-95` supports an explicit
  `liqvera-acceptance-plan/v1`, but `read_plan(None)` returns an empty command
  set.
- `runner.py:237-247` turns every unconfigured offline case into `NOT_RUN` and
  the aggregate into `INCOMPLETE`.
- `Makefile:74-77` invokes offline mode with an output path only; it has no
  `ACCEPTANCE_PLAN` input and never supplies `--plan`.
- `docs/competition/README.md:9-17` accurately describes this inventory-only
  behavior and the external assertion-program protocol.
- Repository search found no plan JSON and no acceptance assertion program;
  the only acceptance implementation files are the runner, case registry,
  wrapper, and result schema.

This is not evidence that the generic runner is wrong. It is evidence that the
factory target cannot currently execute a single F3 assertion. The current
tranche should not pretend to complete A01–A30 or F7. A bounded F3 plan may run
only offline/local cases for which actual assertion programs exist. At minimum,
the artifact vertical directly maps to:

- A08: corrupted raw/mapping/report/manifest data and unsafe ZIP input are
  rejected by the installed offline verifier;
- A09: a clean installed replay, without network access, reproduces the exact
  report and bundle digests.

A02–A06 may be added only where the canonical installed F3 runtime genuinely
executes the exact/rejection behavior and retains concrete evidence. A07 is
marked live in the case registry and must remain `BLOCKED_EXTERNAL` in this
no-network tranche. A01 requires separately retained before/after checks and
cannot truthfully be collapsed into one post-change command.

Recommended factory repair: add an optional `ACCEPTANCE_PLAN` variable that is
passed as `--plan` only when explicitly set, preserving the no-plan inventory
mode. Check in a fixture-only F3 plan and assertion program(s) only if they are
deterministic, network-disabled, installed-artifact based, and produce reviewed
evidence documents. Do not make the broad `liqvera-acceptance` target imply all
30 cases passed when later-stage and external cases remain unexecuted.

### 3. Documentation is honest but must stay stage-specific

The canonical specification assigns F3 the reproducible offline bundle and
live-source validation exit artifact (`LIQVERA_FACTORY_TZ.md:301-310`) and lists
A08/A09 explicitly (`:271-272`). It also says separate test levels are required
and external unavailability is `BLOCKED_EXTERNAL`, not PASS (`:295`). The
competition README likewise states that a result with omissions is incomplete.

Therefore the correct documentation outcome for this tranche is narrow:

- claim installed, fixture-only F3 offline bundle/verifier coverage only for
  the exact cases actually executed;
- keep live-source validation, full A01–A30, F7, payment, deployment, and
  release incomplete;
- bind any evidence to exact Git commit/tree OIDs after repairing the schema;
- retain the existing rule that the runner itself never signs, broadcasts,
  pays, trades, or substitutes fixture evidence for live evidence.

## Suggested implementation order

1. Add a failing schema-validation regression that exposes the 40-vs-64 Git
   OID mismatch.
2. Repair the identity schema/naming and make a generated result validate.
3. Add unit coverage for plan parsing, no-plan inventory semantics, unsafe
   arguments, evidence binding, and result schema validation.
4. Add narrowly scoped installed F3 assertion programs and a fixture-only plan
   for A08/A09 (and only other F3 cases actually proven).
5. Wire an optional plan through the Make target; retain explicit output and
   fail-closed/nonzero incomplete behavior.
6. Update the competition README and handoff with observed case statuses, never
   with a blanket F3/F7 completion claim.

## Scope and safety ruling

All findings and suggested checks are offline and local. They require no
network, database, migration, external write, payment, wallet, deployment, or
release action. The report makes no runtime PASS claim; it identifies one
contract defect and one execution-coverage gap for the implementation owner.
