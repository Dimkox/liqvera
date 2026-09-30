# Release review — live Hyperliquid report and Mezo Testnet paywall

Review subject: `e3df6833e8916d01f55028e63d4db1632a805a75..c7422080cc8ba827ca92a78600953d62161855bb`

Reviewer role: independent `release_reviewer` (read-only product review)

Decision: **FAIL / NO-GO for a live-paywall release or demonstration**

The implementation keeps the default grant-less path fail-closed and does not claim that a new hosted deployment, live Hyperliquid capture, or Mezo Testnet payment occurred. However, the only documented deployment path cannot provide the newly required payment authority, so the paywall is not operator-runnable from this tree.

## Findings

### RELEASE-BLOCKER — live Compose cannot supply the grant or its bound context

`apps/mezo-gateway/src/config.ts:41-46` requires `LIQVERA_LIVE_GRANT_FILE`, `LIQVERA_SUBJECT_COMMIT`, `LIQVERA_SUBJECT_TREE`, `LIQVERA_PLAN_SHA256`, and `LIQVERA_LIVE_BUYER` before ordinary gateway composition can activate the exact grant. `apps/mezo-gateway/src/main.ts:24-28` then reads that file and initializes the official payment adapter.

The `gateway-live` service in `deploy/mezo-evidence/compose.yaml:305-332` mounts only the PostgreSQL and report-token secrets and passes none of those five inputs. No grant file is mounted. The documented operator command in `docs/runbooks/startup-shutdown.md:119-124` therefore starts a live profile that always takes the null composition and retains `EXTERNAL_GRANT_REQUIRED`. This is safe, but it does not realize the requested enabled testnet paywall.

Required correction: add an explicit, secret-file-only live grant mount and the exact non-secret subject/tree/plan/buyer bindings to the live profile (without changing fixture defaults), document how the operator creates/selects them, and add a resolved-Compose/runtime test proving the grant is present only in the live gateway. The grant value must remain outside Git and logs.

### HIGH — rollout and rollback instructions do not describe the implemented operator interface

`docs/runbooks/testnet-demo.md:11-32` lists conceptual preconditions but does not name the new grant file or exact commit/tree/plan/buyer inputs. `docs/runbooks/startup-shutdown.md:119-142` tells the operator to start the live profile but cannot lead to payment readiness. Conversely, `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/rollback.md` says to remove the grant mount/reference even though no such deployment mount/reference exists.

Required correction: document preflight, secure file ownership/mode, exact required variables, readiness expectations before and after one-shot consumption, and the concrete restart/disable procedure against the actual Compose wiring. Preserve consumed rows and UNKNOWN/reconcile-only behavior as already stated.

### HIGH — current evidence is insufficient for a live release claim

The new handoff entry truthfully says no secret value or external payment was used and that final fingerprint verification remains to be rerun (`handoff.md:3-7`). Existing project documentation also truthfully keeps clean-host Docker acceptance `NOT_RUN` and makes no new hosted deployment claim. `python3 scripts/grok_status.py` at review time reports stale human gates and stale code/test/security/data/release review evidence after repository changes.

Required correction: after the wiring/docs repair, rerun fingerprint-bound verification and all selected independent reviews. A release may describe the code path as implemented only after those pass. Do not describe a live Hyperliquid snapshot, public hosted verifier, payment readiness, or a new Mezo settlement as demonstrated until separate external evidence exists. The earlier sealed 0.01 test-MUSD settlement is historical evidence, not evidence for this head or this operator path.

## Positive release properties

- Default startup remains fail-closed: absence or invalidity of a grant yields `EXTERNAL_GRANT_REQUIRED`.
- Grant input is read through a bounded no-follow private-file path; no credential value is committed in this diff.
- The diff does not add a mainnet, custody, private-venue, or exchange-mutation path.
- Durable grant consumption is checked before new quote creation; rollback text preserves consumption/audit rows and UNKNOWN confirm-only semantics.
- Handoff and README do not falsely claim that this change performed a hosted deployment, a fresh live capture, or a fresh payment.
- No schema migration is introduced; the documented rollback correctly avoids destructive down-migration or payment retry.

## Go/no-go checklist

| Area | Result | Evidence |
| --- | --- | --- |
| Default safety gate | PASS | Null/invalid/expired/consumed grants remain blocked. |
| Live Hyperliquid code path | CONDITIONAL | Offline tests exist; no live capture for this head was reviewed. |
| Testnet payment code path | FAIL | Application seam exists, but documented Compose cannot inject its required authority. |
| Operator inputs/runbook | FAIL | Required grant/context inputs and secure mount are absent from deployment instructions. |
| Rollback/forward recovery | CONDITIONAL | Data semantics are sound; operational grant-removal step is not wired. |
| Documentation truthfulness | PASS WITH LIMITATION | Non-execution is disclosed; operational enablement instructions are incomplete. |
| Fingerprint/review closure | FAIL | Status reports stale gates/review receipts; final verification is not bound to this reviewed tree. |
| Hosted/live/payment evidence | NOT_RUN | Must remain an explicit limitation, never inferred from tests or the historical settlement. |

Release recommendation: repair the deployment/operator vertical, rerun verification and reviews on the final clean commit, then perform separately authorized public-read and Mezo Testnet checks if the release intends to claim demonstration evidence. Until then, keep the release NO-GO for an enabled live paywall.
