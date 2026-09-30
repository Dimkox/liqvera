# Independent code review — live Hyperliquid snapshot and Mezo Testnet paywall

- Reviewer role: `code_reviewer` (read-only application review)
- Base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Reviewed head: `c7422080cc8ba827ca92a78600953d62161855bb`
- Scope: actual diff for sealed live Hyperliquid identity/offline reconstruction and opt-in one-shot Mezo Testnet grant/paywall
- Requirements: `requirements.md`, `architecture.md`, `test-plan.md` in this change package
- Outcome: **CHANGES_REQUIRED**

## Strengths

- Live input is sealed with the exact metadata and book bytes, their digests, a versioned mapping policy, and the mapping evidence inside the bundle. Offline inspection recomputes the expected mapping from those sealed bytes instead of trusting a caller-provided approval flag.
- The report path preserves `execution_authority: NONE`, applies freshness and clock checks, and keeps the raw payload available for independent reconstruction.
- Ordinary gateway startup remains grantless unless an explicit file and complete subject/tree/plan/buyer/payee context are configured. Expiry and payer are rechecked at use time rather than only at startup.
- The existing transaction boundary still consumes the grant atomically before `SUBMITTING`, and the settle path remains one-call with UNKNOWN/reconciliation-only behavior after possible broadcast.
- Focused verification observed during this review:
  - `.venv/bin/pytest -q tests/evidence_report/test_canonical_f3.py tests/contracts/test_live_grant_consumption.py` — 9 passed.
  - gateway test command — 42 passed, 6 explicitly skipped behind the disposable PostgreSQL gate.

## Critical

None.

## Important

### I-1 — A durably consumed grant still reaches the 402 and external verify paths

`Gateway.currentBlockers()` correctly queries `live_grant_consumptions`, but it is used only by readiness, capabilities, and new request creation. `Gateway.read()` uses synchronous `this.blockers()` at lines 87 and 98. Therefore an already-created READY quote can still receive a fresh `PAYMENT-REQUIRED` response after the one-shot grant was consumed by another quote, and a supplied signature can still reach the external facilitator `/verify` call before `markSubmitting()` eventually loses the unique-consumption race.

This contradicts the approved requirement that durable consumption fails closed and needlessly solicits/signs or verifies an authorization that cannot settle. Apply the durable blocker before emitting 402 and before verification/attempt creation (while preserving PAID entitlement reads and UNKNOWN reconciliation). Add a regression with two READY quotes sharing one grant: after the first consumption, the second must fail before `requirements()`, `verify()`, or any facilitator I/O.

Evidence: `apps/mezo-gateway/src/application/gateway.ts:16-22`, `:82-103`.

### I-2 — The private grant snapshot can accept an in-place changed or permission-weakened file

`readPrivateGrantFile()` validates mode and link count only on the pathname `lstat`, then reads from the opened descriptor and compares only device, inode, and size. An actor able to modify the secret file can rewrite same-length bytes in place during the read, or change its mode/add a hard link after the first check; the post-read state is still accepted. The function therefore does not implement the architecture's stable, private, single-link snapshot boundary.

Validate the descriptor's type/mode/link count and stable metadata both before and after reading (or use the repository's existing bounded stable-snapshot pattern), and reject any ctime/mtime/size/identity transition. Add deterministic race tests for same-size in-place rewrite, chmod, and link-count change. The current tests only assert source strings and do not execute this boundary.

Evidence: `apps/mezo-gateway/src/security/live-composition.ts:10-18`, `tests/contracts/test_live_grant_consumption.py:18-27`.

### I-3 — A successful live report makes mutually contradictory identity claims

For `live-public`, the report marks `snapshot_status` valid, emits a PASS for `live identity approval`, and sets the algorithm's `live_identity_approved` to true. The same immutable report always includes the limitation `Live identity approval is absent; live reports remain blocked.` This is not merely stale prose: limitations are part of the delivered machine-readable artifact and downstream quote preview, so a verifier cannot derive one unambiguous status from the report.

Generate mode-specific limitations. The live report should retain authenticity/execution caveats without claiming its accepted mapping is absent or blocked; fixture-only limitations should remain fixture-only. Add assertions for the complete live limitation/reason set and for absence of the blocked/fixture statements.

Evidence: `packages/evidence-report/src/mee_evidence_report/report.py:146-158`; the new live test asserts status/mapping but not limitations.

## Minor

### M-1 — Capture construction parses live metadata permissively before the strict offline inspector

`capture_members()` uses ordinary `json.loads()` and assumes a dictionary before accessing `.get()`. Duplicate JSON keys are accepted at this stage and a non-object produces an incidental `AttributeError`, although later inspection uses the strict parser. This does not make a dishonest report pass because the report inspector rejects it, but it can produce inconsistent error behavior and can seal bytes which the next stage must reject. Prefer the shared strict bounded JSON parser or explicitly reject non-object/duplicate-key metadata at capture construction.

Evidence: `packages/public-capture/src/mee_public_capture/evidence_package.py:77-84`.

## Declined to judge

- No external Hyperliquid call, Mezo RPC call, facilitator call, wallet action, or PostgreSQL mutation was performed in this review.
- The factual market semantics of Hyperliquid's current `szDecimals`, five-significant-figure price rule, minimum notional, and USDC settlement were not independently re-researched here; this review assessed code consistency with the approved package and sealed-byte behavior.
- Disposable PostgreSQL concurrency evidence and clean-host/public deployment behavior remain the responsibility of their gated integration and release reviews.
- Documentation-only installer history and unrelated verification-wrapper changes were inspected only for obvious scope interference, not re-reviewed as installer deliverables.

## Readiness

**Not ready for a passing code-review receipt.** The live snapshot/offline reconstruction implementation is directionally sound, and the existing one-submit database boundary remains intact, but I-1 and I-2 leave fail-closed payment authority gaps and I-3 makes the delivered live artifact self-contradictory. Re-review the repaired diff and add focused regressions before recording `code_review: pass`.
