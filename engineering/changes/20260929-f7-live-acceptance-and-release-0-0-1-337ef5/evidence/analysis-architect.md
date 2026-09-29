# F7 live acceptance and 0.0.1 release — architecture/security analysis

Route: `337ef5ec16a0`
Role: read-only architecture and security analysis
Inspected tree: `fe99c7d6a081ef503ddb8b98e22b2167ac8db38c`

No secret was read and no network, wallet, payment, Git push, tag, GitHub
Release, deployment, or other external mutation was performed for this
analysis.

## Executive ruling

This route combines four different risk classes which must not share one
blanket approval:

1. acceptance-runner repair and deterministic local verification;
2. allowlisted public read probes;
3. one explicitly confirmed Mezo Testnet payment demonstration;
4. publication of one reviewed Git commit as `v0.0.1` on GitHub.

Implement and verify them in that order. Each later phase is fail-closed on the
earlier phase and requires its own identity-bound approval record. Approval of
the design is not approval to spend test funds or publish. Approval of the
testnet transaction is not approval to push or release. Any changed HEAD,
tree, plan, external target, recipient, asset digest, amount, or limitations
invalidates the affected approval and returns to the preceding gate.

The release may truthfully contain `NOT_RUN` or `BLOCKED_EXTERNAL` rows, but it
must not be described as complete F7 acceptance unless all A01–A30 rows pass.
The release decision and acceptance verdict are separate fields: a deliberately
limited pre-1.0 source release can be published with an `INCOMPLETE` acceptance
result only if the release notes prominently preserve the exact limitations.

## Assets, actors, and trust boundaries

### Assets

- exact Git commit/tree, annotated tag, source archive and checksums;
- A01–A30 result, per-case evidence, command identities, timestamps and
  omissions;
- dedicated buyer test wallet and its test BTC/test MUSD balances;
- dedicated merchant **public** address and the resulting MUSD Transfer;
- canonical receipt, block/log identity, finality observation and entitlement;
- GitHub repository/release authority and release artifacts;
- private capabilities, wallet signatures, RPC/facilitator credentials, and
  GitHub credentials, none of which belong in repository evidence.

### Actors

- implementation owner: repairs code and prepares deterministic artifacts;
- independent code/test/security/data/release reviewers: verify one exact tree;
- repository owner: grants phase-specific external authority;
- human wallet operator: visually verifies and confirms the single testnet
  authorization/signature;
- public Hyperliquid, Mezo RPC, facilitator, Mezo explorer, and GitHub services:
  untrusted external systems whose responses require validation.

### Boundaries

- local test process -> repository-owned acceptance assertion code;
- browser/human wallet -> x402 authorization -> fixed facilitator origin;
- gateway/reconciler -> fixed Mezo Testnet RPC and local durable ledger;
- local Git -> `https://github.com/Dimkox/liqvera.git` (`Dimkox/liqvera` only);
- release builder -> checksummed artifacts -> GitHub Release `v0.0.1`.

Fetched web pages, RPC responses, facilitator responses, GitHub output, logs,
and transaction metadata are untrusted data. None may alter commands, target
URLs, approval scope, or executable plans.

## Phase plan and gates

### Phase 0 — local repair, no external access

Allowed: code/tests/docs in the approved paths, temporary local files, local
builds, deterministic fakes, and full repository verification. Forbidden:
network, Docker/service deployment, shared databases, wallet interaction,
payment, remote Git and GitHub mutation.

Repair requirements:

- Replace the generic “zero exit + matching strings = PASS” rule with a closed
  per-case semantic contract. Each case declares required claim IDs, evidence
  shape, execution class (`local`, `public_read`, `testnet_write`), and validator.
  Unknown claims/fields and missing claims fail. Arbitrary assertion commands
  cannot self-certify semantics merely by echoing the expected assertion name.
- Make result evidence create-only and content-addressed. Run each assertion in
  a new mode-0700 evidence directory, reject pre-existing/symlink/traversal
  targets, copy validated evidence into runner-owned storage with exclusive
  creation, hash and fsync it, and atomically create the result once. Never
  modify a prior result; a rerun gets a new directory/result ID.
- Bind every PASS to runner version/digest, assertion implementation digest,
  plan digest, commit, tree, normalized command identity, start/end/exit and
  evidence digest. Validate the complete 30-case inventory and overall-status
  algebra independently.
- Split A30 semantics rather than simply changing `live=True` to `False`.
  Deterministic local wallet cancel/switch/reload/wrong-chain behavior is
  locally eligible; any claim of real wallet/provider/testnet behavior remains
  a separately identified external observation. A local A30 PASS must say
  exactly that it is the canonical acceptance criterion executed through the
  production browser orchestration with a fake EIP-1193 boundary; it must not
  imply A13/A14 or a real wallet transfer.
- Add fault tests for forged semantic output, stale evidence, evidence rewrite,
  path/symlink races, duplicate claims, wrong execution class, dirty or changed
  Git identity, timeouts, partial writes, sensitive fields/values, and every
  mutation of the fail-closed verdict.

**Gate P0:** exact scope/design approval, then all focused tests, pinned full
verification, and all selected independent reviews pass on one clean commit.
No external phase begins on a dirty/stale/review-failing tree.

### Phase 1 — final local acceptance run

Execute all locally eligible cases on the clean reviewed commit in isolated
temporary roots. No case is promoted from an old F0–F6 receipt alone; each
case-specific F7 assertion re-executes or validates the full criterion. Missing
PostgreSQL/container/clean-machine prerequisites remain `NOT_RUN`, not a silent
skip or synthetic PASS. The plan has no secret environment names and no URL or
shell-controlled arguments.

**Gate P1:** the local result validates, all evidence digests resolve, no local
case is `FAIL`, the candidate identity is unchanged, and a human reviews the
remaining `NOT_RUN`/`BLOCKED_EXTERNAL` list. A local incomplete result does not
authorize external activity.

### Phase 2 — allowlisted public reads

Exact destinations and methods:

- `https://api.hyperliquid.xyz/info`: HTTPS POST of the fixed public `l2Book`
  request for canonical coin `BTC`, within the documented two-attempt/15-second
  bound. No private endpoint, key, order, cancel, trade or account action.
- `https://rpc.test.mezo.org`: JSON-RPC read methods only before payment
  (`eth_chainId`, `eth_getCode`, exact read-only `eth_call` for MUSD metadata,
  balances/nonces as needed) and receipt/block/log reads after payment. Reject
  redirects, proxies, unexpected chain ID, oversized/malformed responses, and
  any method beginning a transaction.
- `https://facilitator.vativ.io`: only documented read/verify capability probes
  whose exact method/path/body are first derived from the pinned x402 SDK and
  frozen into the approved plan. Do not invent endpoint paths or allow
  redirects to another origin. Settlement is not a read and belongs to Phase 3.
- `https://explorer.test.mezo.org`: optional human/read-only cross-check only;
  it is not authoritative over RPC receipt/log evidence.

**Gate P2:** owner approval names the origins, methods, maximum attempts,
timeouts and exact candidate identity. Stop on DNS/TLS/redirect/proxy mismatch,
rate limiting, inconsistent metadata, chain ID other than `31611`, absent or
mismatched code, MUSD decimals other than 18, unsupported exact scheme, stale
Hyperliquid evidence, or any request for credentials. External unavailability
is `BLOCKED_EXTERNAL`, not FAIL or permission to substitute fixtures.

### Phase 3 — single Mezo Testnet payment

This phase consumes a dedicated, separately recorded external-write approval.
The immutable transaction envelope must name:

- network exactly `eip155:31611` / chain ID `31611`;
- MUSD exactly `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`;
- amount exactly `10000000000000000` atomic units (`0.01` test MUSD);
- one approved dedicated merchant test address, not zero/default and different
  from the buyer;
- one dedicated test-only buyer address with no mainnet/production/custody or
  exchange authority;
- exact quote/report/request/idempotency identity, expiry and maximum one
  settlement submission;
- reviewed authorization-identity and finality-policy versions.

The human wallet operator must inspect chain, token, amount, recipient and
expiry in the wallet and explicitly confirm. The agent must never read, paste,
print, request, or export a private key, seed, signature, session, or wallet
backup. Prefer an injected wallet confirmation. If a noninteractive signer is
unavoidable, it must be a preconfigured test-only signer process outside the
agent's filesystem/process output; its secret variable/file name and custodian
may be recorded, never its value. The merchant private key is never needed.

Fund caps are fail-closed: exactly one `0.01` test MUSD transfer authorization;
no token approval transaction, no unlimited allowance, no second settlement,
no mainnet asset, and no attempt to acquire/faucet/purchase funds unless that
separate action is explicitly approved. Record an explicit maximum test BTC
gas budget in the transaction approval before signing; absence of that numeric
cap blocks the phase. Gas estimation or total cost above the approved cap
blocks signing.

After submission, timeout/transport failure is `UNKNOWN`, never rejection.
Disable any new payment attempt, reconcile the exact buyer/merchant/token/value
and transaction identity from canonical RPC evidence, and converge to confirmed
or manual review. Never retry or ask the buyer to pay again after any possible
broadcast. A13 requires one confirmed Transfer plus one entitlement; A14 must
reuse the same transaction and show settlement count exactly one.

**Gate P3:** a final “sign this exact envelope” approval immediately before
wallet confirmation. Stop on any mismatch, expired quote, changed HEAD/config,
wrong chain, wrong token/decimals, default/zero/equal recipient, insufficient
test balances, unexpected approval/transaction, ambiguous authorization
identity, unreviewed finality, duplicate attempt, receipt inconsistency, reorg,
or sensitive output. A failed pre-submit check permits no signature. An unknown
post-submit outcome permits reconciliation only.

### Phase 4 — release candidate construction

No product deployment is part of this route. After the live result is complete
or its truthful blockers are accepted, freeze the release commit. Define
`0.0.1` as the **Liqvera product release version** in an explicit root release
manifest/VERSION and README. Do not blindly rewrite inherited `mee-*` package
and API versions currently at `0.1.0`; any component-version migration requires
compatibility analysis and its own scope. Build source/archive/checksum and any
declared binaries/wheels only from the frozen commit in a clean isolated tree.

Run full-history secret scanning before publication, current-tree scanning,
dependency/image scans, exact-lock builds, acceptance-result verification and
the full pinned verifier. Release notes must list all non-PASS cases and state:
testnet only; no mainnet; no custody/trading; fake/local evidence boundaries;
no hosted deployment unless separately performed; scanner/dependency residuals;
and whether F7 is complete or incomplete.

**Gate P4:** code/test/security/data/release reviews and fingerprint-bound
receipts all pass for the exact release commit and exact artifacts. Any code,
README, version, result, evidence, or artifact change invalidates the reviews
and returns to verification.

### Phase 5 — GitHub publication

Publication authority must be split into explicit operations:

1. fast-forward `refs/heads/main` only to the approved release commit at
   credential-free canonical remote `https://github.com/Dimkox/liqvera.git`;
2. create annotated tag `v0.0.1` targeting that exact commit, with release
   artifact/result digests and limitations in the annotation;
3. push only that exact tag;
4. create a **draft** GitHub Release in `Dimkox/liqvera` for `v0.0.1`, upload
   only allowlisted artifacts/checksums, download and re-hash them, verify the
   GitHub-generated source archive resolves to the tag commit;
5. publish the draft only after a final owner confirmation of the rendered
   notes, tag target, asset names/digests and limitations.

No force push, branch deletion, merge of unrelated commits, mutable tag,
deployment, Pages enablement, package-registry publication, `latest` alias,
secret creation, repository setting, or workflow dispatch is implied.

**Gate P5:** an exact publication approval names repository, expected remote
main OID, new main OID, tag object/target, asset digests and release-note digest.
Abort if remote main moved, `v0.0.1` already exists locally/remotely/on GitHub,
branch protection requires a different reviewed path, GitHub identity/repository
does not match, credentials have broader unexpected context, or artifacts do
not re-hash exactly.

## Commit/result/tag binding

An acceptance result cannot be committed inside the same commit it claims to
observe: adding the result changes the commit. Preserve exact binding as
follows:

1. Commit all code, docs, version metadata and plans; this is release commit R.
2. On clean R, run acceptance into a fresh untracked/out-of-worktree mode-0700
   evidence directory. The result records R's commit/tree, plan, runner and
   assertion digests. Make no repository edit afterward.
3. Build release assets from R and record their digests beside the result.
4. Create annotated tag `v0.0.1` pointing to R; its annotation records the
   acceptance-result and artifact digests. A tag object does not change R.
5. Attach the immutable result/evidence archive and checksums as release assets;
   release notes repeat the tag target and digests.

If the acceptance run discovers a repair, discard the candidate result, amend
through a new commit (never rewrite published history), repeat all verification
and reviews, then generate a fresh result. Do not hand-edit statuses. An
annotated tag created before final approval stays local and is deleted/recreated
only while unpublished; a published tag is never moved.

## Secrets and logging

- Never read `.env`, wallet/key stores, browser profiles, credential helpers,
  SSH keys, GitHub token files, process environments, or production dumps.
- Commands/plans contain only public identifiers and secret **variable names**;
  no secret values or URLs containing userinfo/query tokens.
- Use the OS/browser/GitHub credential boundary without echo/debug/xtrace.
  Redact authorization/payment headers, signatures, cookies, capabilities,
  database URLs, email and wallet session data from stdout/stderr/evidence.
- Acceptance stores hashes of stdout/stderr, not raw streams. Evidence permits
  public addresses, tx/block hashes and log index only in their typed fields.
- Use minimal-scope short-lived GitHub credentials able to write only
  `Dimkox/liqvera` contents/releases; verify actor/repository before mutation.
- Run pre-publication history and artifact scans. A suspected leak stops the
  release, preserves minimal incident evidence, revokes/rotates outside this
  workflow, and requires a fresh clean candidate.

## Required negative and abuse tests

- forged/missing semantic claim, malicious “PASS” command, stale receipt,
  evidence replacement/race, symlink/traversal, oversized output, duplicate
  case, wrong execution class and changed Git identity;
- SSRF/redirect/proxy/DNS target substitution, URL credentials, unexpected RPC
  method, mainnet/wrong-chain response, wrong contract code/token/decimals,
  facilitator origin/path drift and response confusion;
- wrong/equal/zero payer or merchant, changed amount, expired quote, replay,
  duplicate/parallel submit, timeout after possible broadcast, mismatched log,
  reorg and insufficient finality;
- raw signature/capability/token/cookie/private-key canaries across logs,
  acceptance evidence, bundles, browser assets and release archives;
- remote-main race, pre-existing/moved tag, asset digest mismatch, accidental
  extra refspec, wrong GitHub repository, release note omission and draft
  publication before confirmation.

## Stop conditions and truthful outcomes

Immediately stop the affected phase on any failed local assertion, stale
review/receipt, sensitive material, changed identity, unapproved destination or
method, external inconsistency, spend above the cap, ambiguous broadcast,
branch race or artifact mismatch. Record local defects as `FAIL`, absent local
preconditions as `NOT_RUN`, and unavailable/unapproved external dependencies as
`BLOCKED_EXTERNAL`. Never downgrade a failure to a blocker.

Mainnet, custody, withdrawals, exchange mutations/orders, private venue access,
real-value funds, token approval, fund acquisition, unrelated external writes,
shared production environments and deployment remain forbidden even if another
phase succeeds.

## Rollback / forward recovery

- **Local repair:** revert the coherent F7 change and rerun the prior F0–F6
  verifier. Do not edit historical evidence.
- **Public reads:** no external state should exist; stop and retain sanitized
  diagnostics.
- **Testnet payment:** the transfer is irreversible. Preserve the receipt and
  entitlement/audit trail, disable further submission, reconcile to confirmed
  or manual review, and never compensate or retry automatically.
- **Main push:** never force-reset shared history. Revert with a new reviewed
  commit if necessary.
- **Unpublished draft/tag:** a local/unpushed tag or draft release may be
  discarded after exact target verification; record what was removed.
- **Published `v0.0.1`:** never move or overwrite the tag/assets. Mark the
  release prominently affected/not recommended, disable “latest” if applicable,
  and publish a reviewed forward-fix version (for example `v0.0.2`). Security
  leakage requires credential rotation and an incident process; deleting a
  release is not treated as erasure.

## Recommendation

Approve Phase 0 only after the typed package freezes the repair design and file
scope. Record Phases 2, 3 and 5 as separate, short-lived exact grants. The most
important pre-payment blockers remain the verified merchant address,
authorization-identity rule, finality rule, funded distinct test buyer, and
numeric test BTC gas cap. The most important pre-release invariant is that
`v0.0.1`, its acceptance result and every downloadable artifact all bind the
same reviewed release commit without a post-result repository change.
