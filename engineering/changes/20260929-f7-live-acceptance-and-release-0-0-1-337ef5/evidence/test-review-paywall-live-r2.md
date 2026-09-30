# Independent test re-review — live Hyperliquid and Mezo Testnet paywall

Status: **PASS**

Reviewed base: `e3df6833e8916d01f55028e63d4db1632a805a75`
Reviewed head: `a45f0c01587584f94467b557962b74d9a894a65a`
Prior review: `evidence/test-review-paywall-live.md` (`FAIL`)
Review role: route-selected `test_reviewer` (no product edits)

## Re-review result

The final tree closes all three prior test findings.

### T1 closed — live offline ZIP rebuild and tamper rejection

`tests/evidence_report/test_canonical_f3.py` now publishes the live report,
passes its generated `evidence.zip` through `verify_bundle` with the trusted
report digest, and asserts exact equality with the original build. It then
mutates the sealed live mapping evidence's book digest and proves report build
fails closed. This exercises the live-specific capture → report → archive →
offline rebuild path rather than relying on fixture verification.

### T2 closed — executable private grant-file safety coverage

`apps/mezo-gateway/test/payment-policy.test.ts` now directly calls
`readPrivateGrantFile` against real temporary filesystem objects. It covers the
accepted private regular file plus public permissions, hard links, symlinks,
empty and oversized inputs, mode change after open, and content replacement
after read. The implementation now performs a size-bounded descriptor read,
checks for a trailing byte, and revalidates identity, size, mode, link count,
mtime, and ctime around the read using deterministic race hooks.

### T3 closed — gateway payer, expiry, consumption and no-side-effect behavior

`apps/mezo-gateway/test/state-machine.test.ts` now exercises the gateway-level
consumed-grant projection: readiness becomes 503 with
`EXTERNAL_GRANT_REQUIRED`, both unsigned 402 and signed verify paths fail
before `requirements`/`verify`, and a payer different from the grant payer is
rejected before request persistence. Grant expiry remains time-controlled at
the `OfficialX402.blockers()` boundary consumed by `Gateway.currentBlockers`,
and its transition to `EXTERNAL_GRANT_REQUIRED` is executable.

The PostgreSQL adapter now returns explicit submission outcomes. Its gated
twenty-pool test asserts exactly one `SUBMITTING` winner, restart rejection,
transaction rollback preserving `VERIFIED`, no rolled-back consumption row,
and append-only consumption. The non-PostgreSQL suite also passed the shared
concurrent one-shot consumption test. Post-submit UNKNOWN/reconcile-only tests
continue to prove replay never settles again.

## Commands and observed results

```text
.venv/bin/pytest -q tests/evidence_report/test_canonical_f3.py tests/contracts/test_live_grant_consumption.py
9 passed in 1.67s

npm test
45 passed, 6 skipped in 0.70s
```

The gateway command rebuilt TypeScript before executing all tests. The six
skips are the documented tests requiring an explicitly disposable local
PostgreSQL URL, including the real twenty-pool race; no database authority was
available to this reviewer. This does not convert those tests into current-run
evidence. The atomic database race has an executable gated test and the changed
core `INSERT ... ON CONFLICT DO NOTHING` transaction boundary is retained, but
release evidence should continue to state the current real-PostgreSQL rerun as
`NOT_RUN` unless another fingerprint-bound run supplies it.

## Verdict

PASS for the requested test re-review at head
`a45f0c01587584f94467b557962b74d9a894a65a`. The prior coverage gaps are
closed, focused suites are green, and the remaining PostgreSQL limitation is
explicit rather than silently promoted.
