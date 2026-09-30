# Release re-review — live Hyperliquid report and Mezo Testnet paywall

Review subject: `e3df6833e8916d01f55028e63d4db1632a805a75..a45f0c01587584f94467b557962b74d9a894a65a`

Reviewer role: independent `release_reviewer` (no product edits or external calls)

Decision: **NO-GO**

The previous deployment-wiring blocker is repaired: the live profile now has an exact private grant mount, exact grant-context inputs, and a credential-free loopback database identity. One operational blocker remains: the documented rollback cannot produce a running grant-less live gateway from the checked-in Compose definition.

## Findings

### RELEASE-BLOCKER — documented grant rollback leaves an unusable live service

`docs/runbooks/testnet-demo.md:59-63` says to remove the `payment_grant_live` secret reference (or move its source file) and recreate only `gateway-live`, then expect `/readyz` to return `EXTERNAL_GRANT_REQUIRED`.

That procedure does not match `deploy/mezo-evidence/compose.yaml:335-358`:

- moving `secrets/live_payment_grant` makes Compose unable to resolve the required secret source;
- removing only the service secret reference leaves `LIQVERA_LIVE_GRANT_FILE=/run/secrets/payment_grant`, so gateway startup fails while reading the absent file;
- removing only the environment reference leaves the grant mounted but unused and requires an untracked manual Compose edit that the runbook does not specify;
- the base live profile has no checked-in grant-less override or supported operator switch.

An expired grant also cannot be relied on as the disabled state: startup parses the grant with the current time and fails before serving readiness. Therefore the stated rollback outcome—a healthy live gateway that reports `EXTERNAL_GRANT_REQUIRED`—is not reproducible from the documented command and tree.

Required correction: provide a reviewed grant-less live override/profile that removes both the secret mount and `LIQVERA_LIVE_GRANT_FILE` together, or document an exact bounded Compose override command/file committed in the repository. Add a resolved-Compose test for both enabled and disabled live modes and a runtime test that the disabled mode starts and returns `EXTERNAL_GRANT_REQUIRED`. Update `engineering/changes/20260929-f7-live-acceptance-and-release-0-0-1-337ef5/rollback.md` to name the exact supported operation.

## Closed findings from R1

- `gateway-live` alone receives `payment_grant_live` at `/run/secrets/payment_grant`, with UID 10003 and private mode declared.
- The exact subject commit, tree, plan digest, buyer, and payee inputs are supplied to the live gateway.
- `gateway-live` shares `postgres-live`'s namespace and uses `127.0.0.1:5432/liqvera`; the derived credential-free identity is checked against the grant before facilitator initialization.
- `postgres-live` carries the edge, report, operations, database, and payment-egress networks and aliases needed by the shared gateway namespace.
- Fixture services do not receive the payment grant or payment egress.
- The runbooks now describe secure grant provisioning, exact context values, pre-payment readiness, one-shot consumption, and UNKNOWN confirm-only behavior.

## Truthfulness and evidence status

- `handoff.md:3-9` truthfully says no external call or payment was made for this change.
- README retains the historical settlement as historical evidence and does not claim a new hosted deployment, live capture, or payment for this head.
- Clean-host/hosted/live-payment evidence remains `NOT_RUN`; tests and historical A13/A14 evidence must not be promoted into a fresh demonstration claim.
- `python3 scripts/grok_status.py` reports a clean product tree at `a45f0c0`, but human gates and all review receipts remain stale after repository changes. Final fingerprint-bound verification and the complete review wave are still required after any repair.

## Verification sampled during re-review

- `.venv/bin/python -m pytest tests/operations/test_f6_static.py tests/contracts/test_live_grant_consumption.py tests/evidence_report/test_canonical_f3.py -q` — **13 passed**.
- Gateway focused test invocation covering grant, spent-grant, concurrency, and database identity paths — **45 passed, 6 skipped, 0 failed**. PostgreSQL-backed cases were skipped because no explicitly disposable database URL was supplied.
- No external Hyperliquid, facilitator, RPC, hosted deployment, or payment call was made.

## Go/no-go matrix

| Area | Result |
| --- | --- |
| Live grant mount/context | PASS |
| Credential-free DB namespace binding | PASS |
| Fixture/default isolation | PASS |
| Enabled-mode operator preflight | PASS |
| Disabled-mode rollback | FAIL |
| Documentation truthfulness | PASS |
| Fresh hosted/live/payment evidence | NOT_RUN |
| Final fingerprint/review closure | NOT READY |

Release recommendation: add and test an exact grant-less live rollback path, update the rollback instructions, then rerun fingerprint-bound verification and all independent reviews. Until then, do not release or demonstrate this tree as an operationally recoverable enabled paywall.
