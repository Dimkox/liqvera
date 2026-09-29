# Architecture analysis — F3 offline artifact verification repair

Route: `08fa9d84745d`
Base: `f07562eee1a33df74768e9fa4a3b074783d8c59e`
Role: route-selected, read-only architecture analysis

## Decision

The smallest coherent repair is one fixture-only, installed-package vertical:

```text
local frozen fixture
  -> strict one-pass inspection
  -> exact canonical report
  -> deterministic bounded ZIP
  -> fsync + verify + atomic directory rename
  -> installed offline verifier + exact digest check
```

Do not add a second artifact implementation, a database, an HTTP service, or a
mocked live source. The existing canonical modules are the implementation under
test: `sealed_input.py`, `report.py`, `evidence_bundle.py`,
`schema_validation.py`, and `evidence_cli.py`. The old `builder.py`, `bundle.py`,
and `cli.py` fixture MVP remains compatibility coverage, not the canonical F3
acceptance path.

The tranche should first characterize the current path and then repair only a
defect demonstrated by a failing regression. No broad refactor is justified.

## Present gap and concrete contract defect

- `tests/evidence_report/` exercises only the earlier MVP. It does not directly
  exercise the canonical build, hostile-archive verifier, immutable publication,
  installed entry points, or packaged schemas/dependency lock.
- The evidence-report wheel declares `mee-evidence-build` and
  `mee-evidence-verify` and force-includes schemas, but the entry points and
  resources have not been proven from an isolated installation without source
  checkout imports.
- `tools/mezo_acceptance/runner.py` records `git rev-parse HEAD` and
  `HEAD^{tree}`. In this repository those are 40-hex Git object IDs, while
  `acceptance-result.schema.json` currently applies its 64-hex `sha256`
  definition to both fields. A genuine runner result therefore cannot validate
  against its own schema.

Repair the last item by modelling Git object identity as Git object identity,
not as SHA-256. A dedicated schema definition accepting the repository's
current 40-hex OIDs (and, if future-proofing is desired, Git's 64-hex object
format) is bounded and preserves the 64-hex requirement for actual SHA-256
evidence fields. Do not pad, hash, or otherwise relabel a Git OID as SHA-256.

## Load-bearing invariants

1. All inputs are local regular files below caller-supplied temporary roots.
   Symlinks, special files, changed-during-read content, unknown members, and
   unsafe archive metadata fail closed.
2. Fixture input remains `SIMULATED`, `chargeable=false`, and
   `execution_authority=NONE`. Verification proves relative integrity and exact
   recalculation only; it never asserts exchange authenticity.
3. Money and quantity remain exact (`ExactDecimal`/rational representations);
   no binary float conversion or display-value round trip enters calculation.
4. `report.json`, `algorithm.json`, dependency bytes, the sealed input, bundle
   manifest, and ZIP bytes are mutually bound and deterministically rebuilt.
5. A caller-supplied expected report SHA-256 is checked against recalculated
   report bytes. Changing any bound byte or declaration rejects the entire
   bundle.
6. Publication is immutable per report UUID. The target becomes visible only
   after both files are fsynced and the staged bundle verifies; failure leaves
   neither a target directory nor a READY-equivalent result.
7. Reusing the same report UUID cannot overwrite or merge with an existing
   artifact, even when request bytes differ. The original bytes remain intact.
8. The verifier performs no network, subprocess, database, environment-secret,
   wallet, RPC, facilitator, or exchange operation.
9. Tests may use temporary directories and an isolated virtual environment;
   they must not write persistent stores, apply migrations, or publish outside
   their temporary roots.

## Bounded implementation surface

Prefer a single canonical regression module plus the narrow contract test:

- add `tests/evidence_report/test_canonical_f3.py` (or equivalently narrowly
  named modules) for build, bundle, verifier, and publication behavior;
- add/extend an installed-boundary test that builds local wheels, installs only
  those exact local artifacts into a temporary environment, runs the two
  console entry points from outside the checkout, and confirms resources are
  loaded from the installed wheel;
- repair `schemas/mezo-evidence/v1/acceptance-result.schema.json` and add one
  runner/schema regression proving the runner's actual 40-hex commit/tree
  identities validate while malformed lengths do not;
- change canonical production modules only when a new failing test exposes a
  defect. Keep public CLI shape and F2 schemas stable unless the demonstrated
  defect is within them.

Do not couple the tests to `service.py`, gateway code, PostgreSQL, Compose, or
the browser. Those belong to later tranches and would obscure whether the
offline artifact boundary itself is correct.

## Required test matrix

### P0 — successful exact vertical

Using one copied deterministic fixture and fixed UUID, BUY/SELL request,
quantity, time, and 40-hex engine commit:

1. build through the installed `mee-evidence-build` entry point into an empty
   absolute temporary artifact root;
2. assert exactly `<uuid>/report.json` and `<uuid>/evidence.zip` become visible;
3. assert report schema validity, exact expected rational outputs, simulated
   boundary fields, manifest membership, deterministic ZIP metadata, and
   reported byte/digest values;
4. verify through installed `mee-evidence-verify --report-sha256 <digest>` from
   outside the checkout and assert `INTEGRITY_REPRODUCED` without authenticity
   claims;
5. rebuild independently under a different root with identical fixed inputs and
   assert byte-identical report and bundle digests.

### P0 — corruption and substitution rejection

Mutate one thing at a time and require exit 2 / `EvidenceRejected`, with no
successful artifact metadata:

- one report byte, sealed-input byte, algorithm byte, dependency byte, manifest
  digest/length/path, central-directory field, local-header field, or expected
  report digest;
- duplicate, missing, unexpected, traversal, absolute, non-canonical-order,
  compressed, ZIP64, commented, prepended/trailing, oversized, or overlapping
  archive members;
- duplicate JSON keys, floats/non-finite numbers, invalid UTF-8/non-NFC text,
  wrong identity, crossed/stale/future/insufficient-depth input;
- fixture bytes relabelled `live-public`; this must reject without any socket
  attempt.

Where equivalent cases are already proven below `read_tree` or `_read_archive`,
reuse focused parametrization rather than duplicating a combinatorial suite.

### P0 — immutable replay and partial publication

- Publish once, retain hashes, then repeat the same UUID with identical and
  differing request content. Both repeats reject and the original directory
  and hashes remain unchanged.
- Inject failures after staging creation, after the first file write, after the
  second write, during verifier execution, during staging-directory fsync, and
  before rename. Each failure must remove staging content and leave no target.
- Inject failure after the atomic rename only as a characterization probe. If
  the function reports failure while a complete target is visible (for example,
  a root-directory fsync failure), preserve the complete immutable artifact and
  document recovery semantics; never recursively delete an already renamed
  target. Any claimed success must still pass `read_published`.
- An existing file, directory, or symlink at the UUID target rejects without
  replacement. Lock files are coordination metadata and must not be interpreted
  as publication success.

The post-rename failure probe is important: atomic visibility and durable
acknowledgement are distinct states. The repair must not manufacture a false
negative that encourages a caller to overwrite or create a second logical
report; immutable retry/readback is the safe recovery path.

### P1 — acceptance identity contract

- Generate the repository identity through `repo_identity()` on a clean Git
  checkout and validate a complete result envelope against the installed
  acceptance schema.
- Assert commit/tree accept the actual Git OID length and reject non-hex,
  abbreviated, uppercase (if canonical lowercase remains required), and other
  lengths.
- Assert evidence, stdout, stderr, and artifact SHA-256 fields still require
  exactly 64 lowercase hex characters.

## Verification sequence

Run the new regression red before production edits, then:

1. focused canonical F3 and acceptance-contract tests;
2. existing evidence-report, public-capture, readonly-analyzer, and Mezo
   contract regressions;
3. isolated wheel build/install/entry-point test with no checkout import path;
4. the route-selected full PR verifier;
5. independent code, test, and data reviews against the final fingerprint.

The installed-boundary harness should deny or monkeypatch network creation and
subprocess use inside the F3 operation. Wheel construction/installation may use
only already available pinned local artifacts; missing build dependencies are a
reported acquisition blocker, not permission to install `latest`.

## Explicit exclusions

- No external HTTP, RPC, facilitator, explorer, wallet, exchange, DNS, or
  testnet call.
- No SQLite/PostgreSQL/shared filesystem state, migration application, schema
  migration, backfill, or retained user data.
- No capture/report HTTP service, gateway, x402, payment, entitlement,
  reconciliation, browser, Compose start, container runtime, deployment,
  release, tag, push, or GitHub publication.
- No live acceptance PASS and no change to A13/A14 or payment readiness.
- No attempt to resolve live identity approval, `PAY_TO_MISSING`, authorization
  identity, or finality policy.

## Rollback and recovery

Tests and the Git-OID schema repair are reverted as one coherent commit if they
break compatibility. Any canonical-code repair is separately revertible and
must preserve the pre-change CLI interface. Test artifacts live only in
temporary directories and are deleted by the harness. Since this tranche has
no migration, network, or external write, rollback has no data-recovery step.

## Exit condition

The tranche is complete only when an isolated installed wheel can build,
publish, read back, and exactly verify the fixture artifact; the negative and
failure-injection matrix demonstrates fail-closed tamper/replay/partial-state
behavior; and the acceptance runner's real Git identities validate against its
schema. This does not make F3 live-verified, authorize a payment, or advance F4
through F7.
