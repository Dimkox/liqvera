# Independent code re-review R2 — live Hyperliquid snapshot and Mezo Testnet paywall

- Reviewer role: `code_reviewer` (read-only application review)
- Base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Reviewed head: `a45f0c01587584f94467b557962b74d9a894a65a`
- Repair base: `c7422080cc8ba827ca92a78600953d62161855bb`
- Scope: closure of every finding in `code-review-paywall-live.md` and regression review of the repair diff
- Outcome: **PASS**

## Prior-finding closure

### I-1 — consumed grant reached 402/external verify: CLOSED

`Gateway.read()` now checks the durable `currentBlockers()` result before both the payment-required response and signature verification. The new state-machine regression proves that a consumed grant makes readiness false and reaches neither `requirements()` nor `verify()`. The atomic `markSubmitting()` result is now typed; a losing grant attempt is rejected/reopened without settlement while expiry remains distinguishable.

Evidence: `apps/mezo-gateway/src/application/gateway.ts:82-106`, `apps/mezo-gateway/src/adapters/postgres.ts:117-138`, `apps/mezo-gateway/test/state-machine.test.ts:290-299`.

### I-2 — unstable/private grant-file snapshot: CLOSED

The reader now validates a bounded private single-link regular file on the opened descriptor, performs positional bounded reads plus an overflow probe, and rechecks identity, size, mode, link count, mtime and ctime after reading. Deterministic tests cover unsafe mode, hard link, symlink, empty/oversized input, chmod after open, and same-size content replacement after read.

Evidence: `apps/mezo-gateway/src/security/live-composition.ts:10-30`, `apps/mezo-gateway/test/payment-policy.test.ts:221-242`.

### I-3 — contradictory live report limitations: CLOSED

Limitations are now source-mode-specific. Live artifacts retain the authenticity caveat without claiming identity approval is absent or blocked; fixture-only language remains on fixture reports. The live regression checks the stale statement is absent and verifies the resulting bundle offline.

Evidence: `packages/evidence-report/src/mee_evidence_report/report.py:146-161`, `tests/evidence_report/test_canonical_f3.py:54-87`.

### M-1 — permissive metadata JSON at capture construction: CLOSED

Live metadata construction now rejects duplicate keys recursively through `object_pairs_hook` and explicitly requires a top-level object before selecting the unique BTC entry. Strict offline inspection remains the final authority.

Evidence: `packages/public-capture/src/mee_public_capture/evidence_package.py:77-94`.

## Repair-diff review

### Strengths

- Runtime grant composition additionally binds the credential-free loopback PostgreSQL endpoint identity carried by the grant. The live Compose projection supplies that boundary through a shared network namespace while keeping the database URL secret-derived in memory.
- Grant-consumption failure no longer leaves a quote stranded in `PAYMENT_PENDING`: the rejected attempt is audited and the quote is reopened, while no settle call is possible.
- The original one-submit invariant, UNKNOWN/reconciliation-only behavior, raw Hyperliquid digest bindings, offline reconstruction, and `execution_authority: NONE` boundary remain intact.
- No migrations or destructive data operations were added.

## Critical

None.

## Important

None.

## Minor

None.

## Verification observed

- `.venv/bin/pytest -q tests/evidence_report/test_canonical_f3.py tests/contracts/test_live_grant_consumption.py tests/operations/test_f6_static.py` — **13 passed**.
- `npm --prefix apps/mezo-gateway test` — build/typecheck passed; **45 passed, 6 skipped**. All six skips explicitly require an approved disposable PostgreSQL URL.

## Declined to judge

- No Hyperliquid, Mezo RPC, facilitator, wallet, Docker, or database external operation was performed by this review.
- The six disposable-PostgreSQL cases were not provisioned here; their real concurrency/migration evidence remains gated integration evidence.
- Current external Hyperliquid market-rule facts and public deployment/TLS behavior remain outside this application-code re-review.

## Readiness

**Ready for a passing code-review receipt at head `a45f0c01587584f94467b557962b74d9a894a65a`.** All prior code findings are closed, their relevant failure paths have focused regression coverage, and no new application-code blocker was found in the repair diff.
