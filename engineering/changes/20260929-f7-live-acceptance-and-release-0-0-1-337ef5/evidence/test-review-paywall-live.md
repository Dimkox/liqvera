# Independent test review — live Hyperliquid and Mezo Testnet paywall

Status: **FAIL**

Reviewed base: `e3df6833e8916d01f55028e63d4db1632a805a75`
Reviewed head: `c7422080cc8ba827ca92a78600953d62161855bb`
Review role: route-selected `test_reviewer` (read-only product review)

## Scope

The review inspected the actual base-to-head diff and the surrounding tests for:

- live Hyperliquid BTC identity sealing and offline rebuild;
- private grant-file safety;
- dynamic readiness after expiry or durable grant consumption;
- expected-payer mismatch rejection;
- grant expiry/one-shot consumption;
- post-submit `UNKNOWN` and reconcile-only/no-resettlement semantics.

## Findings

### T1 — P0: the new live test does not exercise the offline artifact verifier

`tests/evidence_report/test_canonical_f3.py:63-83` is named
`test_live_btc_identity_is_digest_bound_and_offline_reproducible`, but it stops
after `build_report`. It neither publishes a live `evidence.zip` nor invokes
`verify_bundle`/`verify_bundle_bytes`, so it cannot detect a live-only omission
from the archive, a rebuild mismatch, or a verifier rejection. The nearby
offline verification assertion at lines 57-60 covers only the fixture path.

Required closure: publish the live report, verify its ZIP in the offline path,
assert exact rebuilt equality, and add a live identity-evidence/raw-digest
tamper case that fails closed.

### T2 — P0: the private grant-file boundary has no executable tests

The only changed coverage for `readPrivateGrantFile` is a source-text assertion
in `tests/contracts/test_live_grant_consumption.py:19-27`. No test calls the
loader. Therefore file mode, symlink/hard-link rejection, size bounds,
replacement races, and descriptor/metadata revalidation are not regression
protected. This is particularly important because the implementation performs
an unbounded `handle.readFile()` between a pre-read size check and the final
metadata comparison.

Required closure: add filesystem tests that call `readPrivateGrantFile` for a
private regular file and reject public modes, symlinks, multiple links, empty
and oversized files, plus deterministic replace/grow/chmod race injections (or
an equivalent bounded descriptor-read seam).

### T3 — P0: new gateway readiness and payer gates are untested

The diff adds `Gateway.currentBlockers()` and the payer comparison at
`apps/mezo-gateway/src/application/gateway.ts:16-23,46-53`, but no changed or
existing test exercises either branch through `Gateway`:

- the new expiry test at `apps/mezo-gateway/test/payment-policy.test.ts:202-212`
  checks only `OfficialX402.blockers()`, not `/readyz`/`Gateway.readiness`;
- no test inserts or fakes a matching `live_grant_consumptions` row and proves
  readiness/capabilities/new quote creation become blocked;
- no test submits a payer different from `payment.expectedPayer` and proves the
  request is rejected before `ledger.createRequest` or report work.

The pre-existing PostgreSQL one-shot tests validate ledger consumption, but
they do not validate the new dynamic gateway projection; in this review run the
six real PostgreSQL cases were also skipped because no explicitly disposable
database URL was supplied.

Required closure: add gateway-level tests for fresh, expired, consumed, and
wrong-payer grants, including side-effect assertions and readiness response
shape/blockers. Run the disposable PostgreSQL consumption suite when its
explicit test gate is available.

## Adequately covered behavior

- Grant parsing/authorization includes mismatch and expiry cases.
- Existing fake and state-machine tests cover one-shot consumption mechanics,
  post-submit uncertainty, replay without resettlement, confirm-only
  reconciliation, bounded retries, manual review, and successful entitlement.
- The focused gateway run passed those UNKNOWN/reconciliation regressions.

## Commands and current evidence

```text
.venv/bin/pytest -q tests/evidence_report/test_canonical_f3.py tests/contracts/test_live_grant_consumption.py
9 passed in 1.48s

npm test -- --test-name-pattern='live grant|settlement_pending|reconciliation'
42 passed, 6 skipped in 0.97s
```

The Node command builds and executes the gateway suite; its six skipped cases
were the explicitly gated real-PostgreSQL tests. Passing focused tests do not
close T1-T3 because those branches are absent from the executable coverage.

## Verdict

Do not record a passing `test_review` receipt for this head. The unchanged
UNKNOWN/reconcile-only behavior has credible evidence, but the new live
offline-rebuild, grant-file, dynamic-consumption-readiness, and payer-mismatch
acceptance claims need executable regression coverage first.
