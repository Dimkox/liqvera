# Data review — PASS

## Final re-review — PASS

- Final reviewed HEAD: `a24e1ed2e373de14e45144c988a89d176384866c`
- Final tree fingerprint:
  `1e8ebe8852e4d569f7a4c6cf4b9a6a7618f540a5ee923a5bebbd0e6a81b67957`
- Repository state before this evidence-only update: clean
- Delta reviewed from the original review HEAD:
  `7ce49b423ed8ef5f861bb4699387b539958e4a5e..a24e1ed2e373de14e45144c988a89d176384866c`
- Findings: none
- Final recommendation: **PASS**

The final schema hardening adds explicit `minLength` and `maxLength` bounds to
the existing anchored patterns. Both `repository.commit` and `repository.tree`
must now be exactly 40 lowercase hexadecimal characters, including under JSON
Schema regex semantics where `$` alone can match before a trailing newline.
Every content digest (`stdout_sha256`, `stderr_sha256`, and evidence-file
`sha256`) must be exactly 64 lowercase hexadecimal characters. Tests cover both
Git identity fields, wrong lengths, uppercase/non-hex input, and trailing
newlines; all three content-digest locations have trailing-newline rejection
coverage.

The final delta contains no SQL, migration, database/store, ledger, fixture,
artifact publication, or persistent-schema change. The original F3 artifact
integrity, duplicate-publication/replay, partial-target, and atomic pre-rename
conclusions below remain unchanged.

Final commands run against the clean final HEAD:

```text
.venv/bin/pytest -q tests/contracts/test_acceptance_result.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/installed/test_canonical_f3_installed.py
21 passed in 9.05s

.venv/bin/pytest -q tests/evidence_report \
  tests/contracts/test_acceptance_result.py
32 passed in 1.08s

Draft202012Validator.check_schema(acceptance-result.schema.json)
schema-valid; explicit exact lengths confirmed

git diff --check f07562eee1a33df74768e9fa4a3b074783d8c59e..HEAD
PASS (no output)
```

The remainder of this document preserves the original review at
`7ce49b423ed8ef5f861bb4699387b539958e4a5e`.

- Route: `08fa9d84745d`
- Reviewed HEAD: `7ce49b423ed8ef5f861bb4699387b539958e4a5e`
- Review role: independent `data_reviewer`
- Repository state at review: clean
- Findings: none
- Recommendation: **PASS**

## Scope and persistent-data boundary

The reviewed change stays inside the scoped fixture-only filesystem boundary.
The diff from the route base contains no SQL, migration, database adapter,
backfill, ledger, or persistent-store implementation change. The existing A2,
gateway PostgreSQL, and local-demo SQLite migrations remain unchanged. No
database was contacted and no migration or production data operation was run.

The only contract change is
`schemas/mezo-evidence/v1/acceptance-result.schema.json`: repository `commit`
and `tree` values now use an explicit canonical 40-lowercase-hex Git object-ID
definition. Content and evidence digests remain 64-lowercase-hex SHA-256
values. Regression coverage validates both boundaries and rejects malformed
length, case, and alphabet values.

## Artifact integrity and replay review

The canonical F3 regression exercises fixture capture, exact report creation,
deterministic bundle creation, staged verification, directory publication,
immutable readback, and offline recalculation. It also confirms that fixture
output remains `SIMULATED`, non-chargeable, and has
`execution_authority=NONE`.

The reviewed coverage establishes:

- exactly `report.json` and `evidence.zip` become visible under the report UUID;
- a wrong trusted digest, altered bundle bytes, or a changed standalone report
  fails closed;
- standalone and bundled report copies cannot be accepted in split-brain form;
- duplicate publication of the same UUID is rejected for both identical and
  changed payloads, while the original bytes remain unchanged;
- a pre-existing partial target is neither merged nor replaced and is rejected
  on read;
- injected staged-verification failure occurs before rename, exposes no target,
  and leaves no staging directory;
- repeated read-only verification remains valid; replay rejection correctly
  applies to a second publication attempt, not to verification of an unchanged
  artifact;
- the installed-wheel test builds and verifies outside source-checkout import
  paths with local wheels and `PIP_NO_INDEX=1`.

The production publisher writes both files into a same-filesystem staging
directory, fsyncs each file and the staging directory, verifies the staged ZIP,
then renames the directory to the UUID target and fsyncs the parent. It checks
target absence both before staging and immediately before rename while holding
the stable report lock. This is consistent with the tested all-or-nothing
publication and immutable-UUID semantics.

## Verification evidence

Commands run against the exact reviewed HEAD:

```text
.venv/bin/pytest -q tests/contracts/test_acceptance_result.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/installed/test_canonical_f3_installed.py
13 passed in 12.11s

.venv/bin/pytest -q tests/evidence_report \
  tests/contracts/test_acceptance_result.py
24 passed in 3.30s

git diff --check f07562eee1a33df74768e9fa4a3b074783d8c59e..HEAD
PASS (no output)
```

Migration/store path inspection returned no changed paths. The route-selected
verifier receipt is maintained separately by the controller.

## Data-change assessment

- Schema before/after for persistent stores: identical.
- Data volume, distribution, query-plan, and index impact: none.
- Lock/downtime and backfill impact: none.
- Tenant, credential, payment, and production-data impact: none.
- Rollback: revert the contract/tests or discard temporary test output; no
  database rollback or forward data repair is applicable.
- Rebuild/replay: rebuild an unpublished artifact from the unchanged fixture or
  publish under a new UUID; never repair an existing UUID in place.

## Residual boundary

This PASS proves deterministic local relative integrity, immutable UUID
publication, and exact offline recalculation. It does not prove exchange
authenticity, live capture, durable multi-node storage, crash recovery across a
non-atomic filesystem, payment state, or any F4-F7 behavior. Those remain
outside this route and would require separate data and operational review.
