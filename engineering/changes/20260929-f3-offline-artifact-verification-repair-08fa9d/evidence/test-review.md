# Test review — PASS after repair

## Final re-review

- Reviewed HEAD: `a24e1ed2e373de14e45144c988a89d176384866c`
- Reviewed tree fingerprint: `1e8ebe8852e4d569f7a4c6cf4b9a6a7618f540a5ee923a5bebbd0e6a81b67957`
- Scratch path: `/tmp/liqvera-test-rereview-08fa9d.sQtHXx`
- Reviewed-tree-modified: no product or test source modified by the reviewer; this report update is the only candidate-tree write
- Findings: none open; the prior P1 finding is closed
- Status: **PASS**

The repaired regression parametrizes both `repository.commit` and
`repository.tree` across 39-byte, 41-byte, uppercase, non-hex, and
newline-suffixed values and asserts the exact failing path. SHA-256 coverage
separately rejects trailing newlines on stdout, stderr, and evidence digests,
so the Git-OID repair cannot weaken content-digest identity.

Focused command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/contracts/test_acceptance_result.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/installed/test_canonical_f3_installed.py -q
```

Observed: `21 passed in 11.23s`.

Mutation probes in the private scratch copy:

1. Replaced only the `tree` Git-OID reference with unconstrained string.
   Acceptance suite result: `5 failed, 9 passed`; all five malformed tree
   cases failed their exact-path assertion. Mutant outcome: **killed**.
2. Removed `minLength`/`maxLength` from SHA-256 while retaining the `$`-ended
   pattern. Acceptance suite result: `3 failed, 11 passed`; stdout, stderr,
   and evidence trailing-newline cases failed. Mutant outcome: **killed**.

The full verifier receipt at
`.grok-stack/runtime/receipts/08fa9d84745d/verification.json` is `pass` and its
tree fingerprint exactly matched the independently recomputed reviewed
fingerprint before this report update. It records pytest-xdist with 22 workers,
tests exit 0, coverage exit 0, Trivy over 9 targets PASS, and source stability
PASS. Persisting this final verdict changes the fingerprint; the coordinator
must rerun verification and record refreshed receipts after all reports are
persisted.

## Initial review history — FAIL

- Reviewed HEAD: `7ce49b423ed8ef5f861bb4699387b539958e4a5e`
- Reviewed tree fingerprint: `196617cb7e459c9e104361df7c26e4c543d4e60843549875b19c65d2e61fbcd0`
- Scratch path: `/tmp/liqvera-test-review-08fa9d.CUb2rK`
- Reviewed-tree-modified: no product or test source modified by the reviewer; this report is the only candidate-tree write
- Findings: 1
- Status: **FAIL**

## Original finding (closed)

### P1 — malformed `repository.tree` Git OIDs have no negative regression

`tests/contracts/test_acceptance_result.py` parametrizes malformed values only
for `repository.commit`. The positive runner-shaped result proves that a valid
40-hex `tree` is accepted and would catch the original 64-hex mismatch, but it
does not fail if the tree constraint is later removed or weakened.

Mutation probe in the private scratch copy changed only:

```json
"tree": {"$ref": "#/$defs/git_oid"}
```

to:

```json
"tree": {"type": "string"}
```

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 /home/pall/projects/liqvera/.worktrees/repo-cleanup/.venv/bin/python \
  -m pytest tests/contracts/test_acceptance_result.py -q
```

Observed: `6 passed in 0.16s`. Mutant outcome: **survived**.

Required repair: exercise each malformed OID against both `commit` and `tree`
(or equivalently parametrize the repository field) and assert the error path
names the mutated field. This is acceptance-criterion coverage, not a defect in
the current schema implementation.

## Passing evidence

### Focused current-tree tests

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/contracts/test_acceptance_result.py \
  tests/evidence_report/test_canonical_f3.py \
  tests/installed/test_canonical_f3_installed.py -q
```

Observed: `13 passed in 9.01s`.

- Canonical source boundary builds the frozen fixture, publishes exactly
  `report.json` and `evidence.zip`, reads them back, reproduces exact report
  bytes, and verifies the trusted report digest.
- Installed boundary builds and installs all four wheels without index access,
  proves imports resolve from the isolated venv rather than the checkout, then
  runs the installed build and verifier entry points.
- Tamper coverage rejects a wrong trusted digest, altered archive bytes, and a
  standalone report split from its verified bundle.
- Replay/partial-publication coverage rejects both identical and changed
  duplicate UUID publication, preserves original bytes, rejects an existing
  partial target, and proves a staged verification failure exposes no target.

### Full verifier receipt

Receipt:
`.grok-stack/runtime/receipts/08fa9d84745d/verification.json`

- status: `pass`
- receipt/tree fingerprint:
  `196617cb7e459c9e104361df7c26e4c543d4e60843549875b19c65d2e61fbcd0`
- independently recomputed pre-report fingerprint: exact match
- `python-unittest`: PASS, `pytest-xdist workers=22`, exit 0
- coverage: PASS, exit 0
- Trivy: PASS, 9 tracked targets
- source stability: PASS

The receipt is valid for the reviewed pre-report tree. Persisting this report
changes the tree fingerprint, so verification and all review receipts must be
refreshed after the test repair and final report persistence.

## Unexecuted / limitations

- No network, database, deployment, payment, or live-source test was run; the
  route explicitly limits this repair to local offline fixtures.
- Archive-format branches beyond the named canonical regressions were reviewed
  statically rather than mutation-probed in this review.
