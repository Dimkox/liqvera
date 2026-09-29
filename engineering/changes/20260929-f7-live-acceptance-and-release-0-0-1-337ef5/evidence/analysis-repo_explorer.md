# Repository exploration — F7 live acceptance and release 0.0.1

Route: `337ef5ec16a0`
Candidate inspected: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`
Inspection mode: read-only. No environment or secret file was read; no wallet,
RPC/facilitator transaction, container, branch, tag, release, or other external
state was mutated.

## Executive finding

The requested end state is not reachable by running the current tree as-is.
The acceptance runner has no checked-in executable plan/assertion program, and
the production gateway and browser deliberately hard-disable payment:

- `apps/mezo-gateway/src/main.ts` always installs `unresolvedIdentity` and
  `unresolvedFinality`;
- those policies have `reviewed:false`, so `OfficialX402.initialize()` cannot
  make payment ready and readiness always includes
  `AUTHORIZATION_IDENTITY_UNVERIFIED`, `FINALITY_RULE_UNVERIFIED`, and
  `PAYMENT_SERVICE_UNAVAILABLE`;
- `apps/mezo-web/src/x402.ts` has no registered production adapter, so
  `x402Available()` remains false and the browser cannot submit payment;
- no environment switch can bypass either gate, by design.

Therefore A13/A14 and a live paid demonstration must stay blocked until real,
reviewed identity/finality policies and the exact official browser-SDK binding
are implemented and independently reviewed. Supplying a pay-to address, RPC,
facilitator, or wallet alone cannot close this gap.

## Current public/release state

Safe public metadata checks observed:

- origin is the credential-free `https://github.com/Dimkox/liqvera.git`;
- GitHub repository `Dimkox/liqvera` is public and its default branch is
  `main`;
- public `main` is `f07562eee1a33df74768e9fa4a3b074783d8c59e` and is not
  branch-protected;
- the candidate branch is 40 commits ahead of the local `origin/main` ref at
  inspection time;
- no public tags and no GitHub Releases were returned;
- repository GitHub Actions are disabled;
- GitHub CLI is authenticated as `Dimkox` with repository/write-capable scopes.

The last item establishes technical capability, not approval. Both route human
gates are still pending for scope digest
`bd797c108888705a50907f2b6b2f0ba3899b8689a0affe80e05c2887f41f6672`:
`scope_and_design_approval` and `migration_or_external_write_approval`. No live
call, payment, push, tag, or release may occur before the exact gates are
recorded and rechecked after any scope-digest change.

There is also a versioning ambiguity. The root project is `0.1.0.dev0`; the
Liqvera Python packages and three Node packages are already `0.1.0`; no root
`VERSION` exists. Blindly changing all component versions to `0.0.1` would be a
semantic-version downgrade and would require lockfile consistency work. The
smallest coherent interpretation is a new root product `VERSION` of `0.0.1`
and tag `v0.0.1`, while preserving inherited/component `0.1.0` identities and
documenting that distinction. The scoped design must make that ruling explicit.

## Acceptance-runner repairs required before live execution

The earlier local reproduction at this same HEAD produced `INCOMPLETE` with
25 `NOT_RUN`, five `BLOCKED_EXTERNAL` (A07, A13, A14, A29, A30), and zero
PASS. The following are the smallest defensible repairs:

1. Add a repository-owned assertion dispatcher and checked-in deterministic
   plan. Each invocation executes the complete named criterion, creates a
   sanitized case-specific JSON evidence document, and emits the existing
   protocol object. Prior review prose alone must never cause PASS.
2. Add semantic validation beyond schema shape. A PASS must be rejected unless
   case-specific observations prove the required outcomes, including exact
   command scope, expected negative paths, no-charge/no-delivery properties,
   and required digests/identities. A generic nonempty `observations` list is
   currently enough for any non-payment case and is not trustworthy.
3. Make evidence creation immutable. Use a newly created run directory, reject
   pre-existing case files, open outputs with exclusive creation/no-follow
   semantics, hash after the assertion process closes, and prevent multiple
   cases from naming the same file. Never overwrite historical evidence.
4. Bind the final result to the exact final clean commit and tree. Build and
   commit all code/docs/version/release-note changes first, run verification
   and reviews, then produce acceptance output outside the worktree. Do not
   commit that result into the commit it identifies; doing so changes its own
   identity. Retain it as an immutable release asset with a published digest.
5. Replace the single `Case.live` boolean with an explicit execution class or
   equivalent rule. A30's deterministic wallet cancel/switch/reload/wrong-chain
   behavior is locally executable with the injected fake provider and should
   not be automatically `BLOCKED_EXTERNAL` in offline mode. A separate live
   wallet demonstration can remain externally gated; local A30 PASS must not be
   described as a real-wallet payment.
6. Add boundary regressions for unsafe plans/environment isolation,
   timeout/nonzero/malformed protocol, traversal/symlink/oversize/secret
   evidence, duplicate evidence names, semantic insufficiency, live
   authorization, A13/A14 payment linkage, and PASS/FAIL/INCOMPLETE reduction.
7. Allow an explicit plan through the Make target (or add a clearly named
   local/live pair) while retaining the no-plan honest-inventory behavior.

Local A26 still requires actual container/network enforcement evidence, and
A28 requires a fresh clean lockfile install/build/demo. Neither may be inferred
from a populated checkout or static Compose tests.

## Live/testnet implementation prerequisites

Before any transaction-capable run, the single write owner must implement and
test all of these rather than flipping readiness flags:

- a canonical authorization identity derived from the exact x402 v2 payload,
  with payer, nonce/replay domain, quote/resource binding, validity horizon,
  stable version, and one-to-one Transfer correlation;
- a reviewed Mezo Testnet finality policy with explicit confirmation/reorg
  behavior and deterministic tests for receipt replacement, removed logs,
  chain mismatch, and inconsistent RPC views;
- an official `@x402/paywall/2.16.0` browser adapter using the injected
  EIP-1193 provider, with a proven before-submission cancellation boundary and
  no retry after uncertain submission;
- production-wiring tests proving the real `main.ts` and browser entrypoint
  install those concrete policies/adapters, while fixture mode remains unable
  to pay;
- integration evidence for PostgreSQL durability, report/artifact services,
  reconciliation, network isolation, metrics privacy, and safe shutdown before
  exposing a live profile;
- exact preflight validation of chain 31611, MUSD contract/code/decimals,
  facilitator support, dedicated merchant address, distinct funded test buyer,
  public origin, final source SHA, image digests, backups, and stop conditions.

Configuration/secret **names only** discovered from source and runbooks:

- gateway/runtime: `DATABASE_URL` or `DATABASE_URL_FILE` (exactly one),
  `PAY_TO`, `SOURCE_MODE`, `ARTIFACT_ROOT`, `REPORT_SERVICE_URL`,
  `REPORT_SERVICE_TOKEN_FILE`, `PUBLIC_BASE_URL`, `CORS_ORIGINS`, `HOST`,
  `PORT`, `METRICS_HOST`, `METRICS_PORT`;
- service/deployment aliases: `LIQVERA_ENGINE_COMMIT`,
  `LIQVERA_SOURCE_MODE`, `LIQVERA_CAPTURE_ROOT`, `LIQVERA_ARTIFACT_ROOT`,
  `LIQVERA_CAPTURE_URL`, `LIQVERA_INTERNAL_TOKEN_FILE`,
  `LIQVERA_POSTGRES_PASSWORD_FILE`, `LIQVERA_SITE_ADDRESS`;
- documented public merchant input: `LIQVERA_PAY_TO` is mapped by deployment
  configuration to the gateway's `PAY_TO` contract;
- `LIQVERA_FINALITY_CONFIRMATIONS` is explicitly documented as unconsumed and
  must not be treated as a working policy switch.

The gateway accepts no merchant private key. The buyer action is an interactive
wallet operation. No repository script can safely supply the human's signature,
so a human must inspect the exact quote (chain, token, recipient, amount) and
explicitly confirm the capped `0.01` test-MUSD transaction. Agent automation
must stop at the wallet-confirmation boundary and resume only from sanitized
transaction/receipt evidence. Absence of the configured merchant address,
funded distinct buyer, usable injected wallet, approved policy, public origin,
or external service produces `BLOCKED_EXTERNAL`; it never authorizes using a
different wallet or fabricated evidence.

## Minimal ordered delivery

1. Freeze typed acceptance criteria, threat model, version ruling, exact live
   endpoints/assets/amount, stop conditions, and rollback; obtain the current
   scope/design gate.
2. Repair the runner/semantic/evidence boundary and implement deterministic
   local assertions, including local A30. Run focused tests and full pinned PR
   verification on a clean coherent commit.
3. Implement reviewed authorization/finality/browser bindings test-first; run
   fake, fault, PostgreSQL, container/isolation, clean-install, and security
   suites. Any failed local assertion is `FAIL`, not blocked.
4. Dispatch the route's independent code, test, security, data, and release
   reviews on the exact candidate. Persist reports, rerun verification, and
   refresh fingerprint-bound receipts.
5. Prepare a clean release candidate: root product version `0.0.1` under the
   approved version ruling, README/handoff/current-status corrections, release
   notes, reproducible artifacts and SHA-256 manifest. No push yet.
6. Obtain/record the external-write approval for the exact current digest and
   exact actions: bounded public read probes, one capped Mezo Testnet payment,
   branch update, annotated `v0.0.1` tag, and GitHub Release/assets. A changed
   digest or target invalidates the approval.
7. Execute preflight read probes first. Start only the isolated approved
   profile; require readiness and exact identities. Stop without a transaction
   on any mismatch. The human confirms the single test-wallet action.
8. Reconcile the transaction to canonical receipt/finality and durable
   entitlement; prove repeat report/bundle retrieval causes zero additional
   settlement. Run live A07/A13/A14 and the separate real-wallet portion of
   A30. A29 can pass only after the final public commit is anonymously cloned
   and compared.
9. Generate the final acceptance result from the exact clean commit outside
   the tree, independently review it, and declare NO-GO if any required case is
   FAIL/NOT_RUN/BLOCKED. Truthful limitations may accompany a release, but the
   canonical spec forbids claiming F7 complete while testnet payment is blocked.
10. Before push, refresh README as required by repository policy. Recheck that
    public main and `v0.0.1` have not moved/appeared. Push the exact authorized
    fast-forward main commit, create/push the tag, and create the GitHub Release
    with immutable artifacts and digests. Verify public commit/tag/assets by
    anonymous reads; do not deploy unrelated infrastructure.

`python3 scripts/grok_deploy.py` only prepares human-owned commands and never
executes tag, push, or release. Actual publication must use the explicitly
approved exact commands and be followed by public read-back verification.

## Stop conditions and rollback/forward recovery

Stop before transaction on any wrong chain/token/amount/recipient/payer,
unreviewed identity/finality, unhealthy storage/source, facilitator/RPC
disagreement, missing artifact integrity, unavailable backup, or dirty/mismatched
Git identity. After a signature may have been submitted, never retry payment;
record `PAYMENT_UNCERTAIN`, preserve ledger/artifacts/logs, query canonical chain
state, reconcile to confirmed or manual review, and do not ask the buyer to pay
again.

Application rollback is disable-new-sales/stop gateway plus forward-fix. Do not
drop/rewind the ledger, delete volumes, erase authorization identities, or
replace immutable artifacts after any payment state exists. Preserve the
receipt and reconciliation audit trail.

Publication recovery is additive:

- before push/tag/release, simply stop and repair locally;
- if main push succeeds but tag/release fails, do not rewrite public history;
  repair the missing publication step after verifying the pushed SHA;
- if an incorrect tag/release is published, do not force-move or silently
  replace it; mark it superseded and publish a new corrected version after a
  fresh gate/review;
- never force-push main. Because public main is currently unprotected, enforce
  explicit fast-forward and remote-SHA checks in the release procedure.

## Present blockers

- both required human gates are pending;
- authorization identity, receipt finality, and browser payment adapter are
  intentionally unimplemented in production wiring;
- merchant address, funded distinct buyer, wallet availability, and test-fund
  balances were not inspected and must be established by the operator;
- no executable acceptance plan/assertion program exists;
- A26 runtime isolation and A28 fresh clean-install evidence do not exist;
- public `main` is 40 commits behind the candidate and unprotected;
- no `v0.0.1` tag or release exists;
- version semantics must be frozen to avoid downgrading existing `0.1.0`
  component packages;
- README and component READMEs contain stale F5/F6 verification state and must
  be reconciled before publication.
