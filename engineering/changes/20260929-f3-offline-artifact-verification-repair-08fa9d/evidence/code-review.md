# Independent code review — F3 offline artifact verification repair

## Verdict

**FAIL** — one blocking contract-correctness finding remains.

Reviewed source:

- route: `08fa9d84745d`
- change: `20260929-f3-offline-artifact-verification-repair-08fa9d`
- HEAD: `7ce49b423ed8ef5f861bb4699387b539958e4a5e`
- base: `origin/main` at `f07562eee1a33df74768e9fa4a3b074783d8c59e`
- scoped initial checkpoint: `bed18457b084f9c9f15dd8bee24c31a74323e639`
- candidate tree fingerprint: `196617cb7e459c9e104361df7c26e4c543d4e60843549875b19c65d2e61fbcd0`
- private scratch: `/tmp/liqvera-code-review.IAARdc` (mode `0700`)
- reviewed-tree-modified: no

The candidate was clean at review start. Concurrent reviewer-owned report files
`evidence/data-review.md` and `evidence/test-review.md` appeared after the code
probes; they are not product changes and were excluded from this verdict. This
report is persisted only because the route coordinator explicitly requested it;
final verification must bind a fresh receipt after review reports are persisted.

## Blocking finding

### HIGH — `git_oid` and SHA-256 patterns accept a trailing newline

Location: `schemas/mezo-evidence/v1/acceptance-result.schema.json:37-38`

The new `git_oid` definition uses `^[0-9a-f]{40}$`. Under the Python regex
semantics used by `jsonschema`, `$` also matches immediately before a terminal
newline. Consequently both `commit` and `tree` accept a 41-character value made
of 40 lowercase hex characters followed by `\n`. The existing SHA-256 definition
has the same boundary error and accepts a 65-character content digest. These
values are not canonical Git object IDs or SHA-256 encodings, contradict the
change package's explicit malformed-identifier rejection requirement and
weakening provenance validation.

Action: make both definitions require the actual end of the string, for example
with the repository's established `(?![\\s\\S])` suffix (or exact `minLength` /
`maxLength` combined with the character pattern). Add regression cases for both
`repository.commit` and `repository.tree`, and for each SHA-256-bearing contract
field or a shared `$defs` boundary test. The current tests at
`tests/contracts/test_acceptance_result.py:53-96` exercise only short/long,
uppercase, and non-hex mutations, so the terminal-newline mutant survives.

Probe command (in-memory mutation; candidate files remained read-only):

```bash
.venv/bin/python - <<'PY'
# Load acceptance-result.schema.json with Draft202012Validator; construct a
# valid acceptance result; replace commit/tree with 40 hex + "\\n" and
# stdout_sha256 with 64 hex + "\\n"; inspect errors at the mutated path.
PY
```

Observed output:

```text
valid_commit ACCEPT []
commit_newline ACCEPT []
tree_newline ACCEPT []
digest_valid ACCEPT []
digest_newline ACCEPT []
```

Mutant outcome: **survived**.

## Passing review evidence

### Canonical F3 behavior and installed boundary

Command:

```bash
.venv/bin/pytest -q tests/contracts/test_acceptance_result.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/installed/test_canonical_f3_installed.py
```

Observed output: `13 passed in 8.69s`.

The tests cover deterministic canonical fixture output, exact two-file
publication, trusted-digest rejection, archive and standalone-report tampering,
duplicate UUID immutability, partial-target rejection, staged failure cleanup,
wheel installation outside the checkout, and CLI verification. Static review of
the corresponding canonical implementation found the assertions aligned with
the archive-first verification and atomic publication behavior. Mutant outcome
for the represented corruption/overwrite/substitution paths: **killed** by the
focused suite. No additional product-code regression was found.

### Dependency pin compatibility

Command:

```bash
.venv/bin/python - <<'PY'
from importlib.metadata import distribution
for name in ('hyperliquid-python-sdk', 'eth-account'):
    d = distribution(name)
    print(name, d.version)
    if name == 'hyperliquid-python-sdk':
        print(*[r for r in d.requires or [] if r.lower().startswith('eth-account')])
PY
.venv/bin/pip check
```

Observed output:

```text
hyperliquid-python-sdk 0.24.0
eth-account (>=0.10.0,<0.14.0)
eth-account 0.13.7
No broken requirements found.
```

The restored `eth-account==0.13.7` pin satisfies the direct SDK constraint;
mutating it to the prior `0.14.0` is rejected by that metadata constraint.
Mutant outcome: **killed**.

### Diff hygiene and scope

Commands:

```bash
git diff --check bed18457b084f9c9f15dd8bee24c31a74323e639..HEAD
git diff --stat bed18457b084f9c9f15dd8bee24c31a74323e639..HEAD
```

Observed output: `git diff --check` was empty. Product changes are limited to
the acceptance-result schema, the compatible dependency pin, and focused
contract/canonical/installed tests; the remaining files are scoped change
package, architecture inventory, decisions/mistakes, and handoff evidence. No
network, live execution, payment, deployment, migration, or persistent-data
behavior was introduced. Static scope claim: **unexecuted** beyond diff review;
no scope-expansion finding observed.

## Limitations

- The repository-wide verifier receipt already records `1147 passed, 85
  subtests passed` for the clean candidate fingerprint above; this reviewer did
  not rerun the full verifier because the surviving schema mutant is already a
  decisive blocker.
- The review did not exercise live services or network dependencies; those are
  explicitly outside this change package.
