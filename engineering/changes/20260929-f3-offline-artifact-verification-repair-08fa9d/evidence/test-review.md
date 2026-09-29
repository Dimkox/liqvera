# Test review — FAIL

- Reviewed HEAD: `7ce49b423ed8ef5f861bb4699387b539958e4a5e`
- Reviewed tree fingerprint: `196617cb7e459c9e104361df7c26e4c543d4e60843549875b19c65d2e61fbcd0`
- Scratch path: `/tmp/liqvera-test-review-08fa9d.CUb2rK`
- Reviewed-tree-modified: no product or test source modified by the reviewer; this report is the only candidate-tree write
- Findings: 1
- Status: **FAIL**

## Finding

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
