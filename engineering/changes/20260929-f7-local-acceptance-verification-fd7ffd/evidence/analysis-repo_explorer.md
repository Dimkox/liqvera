# Repository exploration — F7 local acceptance boundary

Route: `fd7ffd5cc17f`
Candidate inspected: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`
Scope: read-only/local-only; no container, network, wallet, RPC, payment,
publication, deployment, tag, push, or release action was performed.

## Result

The checked-in acceptance runner is fail-closed, but the repository does not
yet contain an executable A01–A30 acceptance plan or an assertion program.
Consequently the real runner cannot aggregate the already completed F3–F6
local work. On a clean detached worktree at the inspected commit it produced
an honest `INCOMPLETE` result with 25 `NOT_RUN` rows and five
`BLOCKED_EXTERNAL` rows:

- `BLOCKED_EXTERNAL`: A07, A13, A14, A29, A30;
- `NOT_RUN`: A01–A06, A08–A12, A15–A28 except the blocked rows above;
- `PASS`: none.

This is a tooling/acceptance-evidence gap, not evidence that the underlying
local behaviors failed. The focused F3–F6 tests and reviews cannot be relabelled
as acceptance PASS without executable case-specific assertions and evidence
bound to the final clean commit.

## Reproduction

The candidate worktree was dirty only because the newly routed F7 change
package was untracked, so a temporary detached Git worktree at exactly HEAD was
used to exercise `repo_identity()` without modifying the candidate. The
temporary worktree and result were removed after inspection.

```text
.venv/bin/pytest -q tests/contracts/test_acceptance_result.py
14 passed in 2.67s

python3 -B <clean-worktree>/scripts/run-mezo-acceptance.py \
  --mode offline --output /tmp/<new-result>.json
exit 1
overall INCOMPLETE
repository.commit fe99c7d6a081ef503ddb8b98e22b2167ac8db38c
repository.tree   0483ca8841e4d34432c0ffc8d8b9d8a79aa93230
statuses          NOT_RUN=25, BLOCKED_EXTERNAL=5
```

Running the same command directly in the candidate correctly exited 2 with
`commit or remove worktree changes before acceptance`. That clean-tree guard
must remain; the final result should be written outside the repository after
the last product/documentation commit so committing the result cannot invalidate
its own commit identity.

## Confirmed gaps

1. **No local acceptance plan or assertion program.** `read_plan(None)` is
   deliberately empty, `Makefile:74-77` never accepts/passes `--plan`, and a
   repository search found no `liqvera-acceptance-plan/v1` document or
   case-specific assertion executable. The only implementation is the runner,
   registry, result schema, and result-shape tests.
2. **The runner's critical trust boundary is mostly untested.** Current tests
   cover generated inventory identity and schema digest/OID rejection. There
   are no direct tests for plan allow-listing, command isolation, timeout and
   nonzero handling, evidence path/symlink/size/secret rejection, assertion
   binding, payment evidence linkage, live authorization gating, or the
   overall-status reduction. F7 should not depend on this boundary without
   those regressions.
3. **Existing acceptance state is stale by design.**
   `engineering/changes/2026-09-24-mezo-evidence/acceptance-matrix.md` binds F1
   observations to `37d3e2c` and explicitly requires F7 to repeat them. F3–F6
   reports are useful inputs for choosing fresh local assertions, but their
   prior fingerprints do not prove the final F7 tree.
4. **README state is behind the tree.** It still says F6 full verification and
   independent review are pending and calls F6 `IMPLEMENTED_UNVERIFIED`, while
   commit `fe99c7d` closed the F6 workflow. This must be corrected without
   claiming F7, payment, deployment, or release readiness.
5. **A full PASS is impossible and must remain impossible in this route.** The
   canonical specification says not to close F7 while F0 or testnet payment is
   blocked. A13/A14 lack a funded buyer, verified merchant recipient and
   approved finality evidence; A07/A29/A30 are classified live by the stable
   inventory and this route forbids their external actions. The runner must
   therefore finish `INCOMPLETE`, not PASS, even after all truthful local
   assertions run.
6. **A26 and A28 cannot be inferred from static/focused checks.** A26 requires
   runtime network/container boundaries, while this route forbids container
   execution. A28 requires a fresh clean README install/build/demo from
   lockfiles; using the already-populated working environment is not that
   observation. Leave both `NOT_RUN` unless their exact scenarios are executed
   within separately approved scope.
7. **Competition copy is appropriately cautious.** The submission checklist
   has no checked items, the demo script calls itself a future operator draft,
   and no hosted URL, video, transaction, or release claim is present. Preserve
   that wording. The final readiness report must say `not release candidate`
   while the live/payment/publication and local A26/A28 gaps remain.

## Smallest truthful repair

Implement one repository-owned, offline assertion dispatcher plus one checked-in
local plan. Each invocation should accept exactly one case ID, execute only the
bounded deterministic checks for that criterion, write a sanitized evidence
JSON below `LIQVERA_ACCEPTANCE_EVIDENCE_DIR`, and print the existing protocol
object. Do not make an assertion pass merely because an old report file exists.

The locally supportable candidate set is A01–A06, A08–A12, A15–A25, and A27,
but every row must be included only after its assertion genuinely exercises the
whole table criterion against the final tree. In particular, aggregate the
real F3 artifact/tamper/replay commands, F4 gateway/ledger fault commands, F5
mocked state-machine fault commands, F6 deterministic browser/security commands,
and the unchanged Stage A verdict suite. A01 needs both retained historical
baseline evidence and a fresh final-tree verification; it is not satisfied by
the final run alone.

Add focused runner-boundary tests before the plan is trusted. At minimum cover:

- unsafe/duplicate/unknown plan entries and environment-name isolation;
- timeout/nonzero/malformed protocol producing FAIL rather than PASS;
- traversal, symlink, oversize, empty-observation and secret-bearing evidence;
- mismatched case/assertion and digest/size capture;
- offline live rows staying `BLOCKED_EXTERNAL` even if listed in a plan;
- A13/A14 exact payment linkage and rejection of fabricated/mismatched linkage;
- overall `PASS`, `FAIL`, and `INCOMPLETE` reduction and schema validation.

Teach the Make target to accept an explicit local plan (or add a separately
named F7-local target) while retaining the existing no-plan inventory behavior.
Then, after all repository edits and reviews are committed, run the result
producer from the clean final commit with output outside the worktree. Retain
the immutable result alongside delivery evidence without committing it back
into the tree it identifies.

## Required status handling

- A07, A13, A14, A29, A30: `BLOCKED_EXTERNAL` with
  `LIVE_AUTHORIZATION_ABSENT`; do not pass a plan entry, use `--mode live`, or
  use `--authorize-live` in this route.
- A26: `NOT_RUN` (`ASSERTION_COMMAND_NOT_CONFIGURED`) because runtime
  container/network execution is excluded; F6 static topology evidence is not
  a substitute.
- A28: `NOT_RUN` unless a genuinely fresh lockfile-only clean installation and
  offline demo is performed; the present populated checkout is insufficient.
- Any other case lacking a complete executable assertion: `NOT_RUN`, never a
  PASS copied from an earlier route or inferred from implementation.
- Any configured local assertion that executes and fails: `FAIL`, not
  `NOT_RUN` or `BLOCKED_EXTERNAL`.
- Overall result: expected `INCOMPLETE` for this local-only route. The release
  candidate decision remains **NO-GO / not ready**, even if all configured
  local assertions pass.

## Residual constraints

The all-156 frozen vector runtime status remains `NOT_RUN`; the prior focused
tests must not mutate those canonical statuses. No real PostgreSQL/container
integration, live Hyperliquid source, Mezo RPC/facilitator, wallet, transfer,
anonymous GitHub clone, hosting, deployment, publication, push, tag, merge, or
release evidence was produced here.
