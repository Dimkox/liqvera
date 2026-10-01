# Architecture — F7 live acceptance and release 0.0.1

## 2026-10-01 signed v2 public-demo authority

The owner-approved public testnet demo does not weaken the one-shot v1 grant.
It uses a distinct `liqvera-mezo-payment-grant-envelope/v2`: the payload is
RFC 8785/JCS canonical JSON carried as base64url, duplicate keys and unknown
fields are rejected, and received payload bytes must equal their JCS encoding.
An Ed25519 signature is checked against a non-secret runtime public key whose
allowlisted `key_id` is the lowercase SHA-256 of the raw 32-byte key. The
private issuer key is offline and never belongs in the gateway or repository.

The signed policy binds exact commit, tree, plan, loopback database identity,
Mezo chain 31611, MUSD, 0.01 MUSD per settlement, facilitator, Permit2/EIP-2612
flow, payee, validity (at most 24 hours), `ANY_VALID_X402_PAYER`, zero buyer
native gas, count, total amount, and one settlement per payer. Migration 006 is
additive: immutable `live_grant_authorities` and `live_grant_reservations`
retain authority and permanently spent ordinals. The same transaction locks
the authority, checks time/count/sum/payer, inserts a reservation, and crosses
`VERIFIED -> SUBMITTING` before facilitator I/O. UNKNOWN never releases budget;
a transaction loser creates no reservation. Readiness derives remaining time,
count, and amount from PostgreSQL, while an already-paid delivery is independent
of later grant expiry.

`canonicalize@2.1.0` (Apache-2.0) is pinned as the small RFC 8785 serializer;
`json-dup-key-validator@1.0.3` (MIT) is pinned because ordinary `JSON.parse`
cannot detect duplicate object names before signature-policy interpretation.

## 2026-09-30 bounded extension

The sealed mapping binds raw Hyperliquid response digests and is rechecked offline. The gateway optionally reads `LIQVERA_LIVE_GRANT_FILE` through a no-follow, private-mode, single-link, size-bounded snapshot and retains the existing atomic grant-consumption boundary.

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Installer Task 5 rulings (2026-09-30)

- Lifecycle state is a separate closed `liqvera-lifecycle/v1` journal so the
  released install-state v1 contract is not overloaded. Atomic intent and phase
  markers bind candidate/prior identities, backup digest, exact migration
  ledger, migration-commit fact, Compose project and service manager.
- Release compatibility is exact 001–005 identity plus `down_migrations=false`;
  it is not a version range. A post-migration rollback is permitted only when
  the prior verified release accepts the observed exact ledger.
- Update requires a complete coherent backup receipt before candidate mutation.
  The production Compose adapter has no reviewed database-ledger/backup seam yet,
  so production update fails closed; fake-only tests prove the state machine.
- Default uninstall never removes volumes or retained data. Destructive purge
  is a separate exact-token operation over five project-bound volume names.

## Installer Task 4 rulings (2026-09-30)

- The Compose projection is shadow-only: `shadow` maps explicitly to runtime
  `fixture`. It has no egress, payment/wallet/grant inputs, or live profile.
  Only edge publishes `127.0.0.1:3000`; gateway and metrics remain internal.
- Database and report credentials are distinct private file references. The
  source manifest is `runnable=false` until Task 6 supplies reviewed image digests.
- The existing gateway migrator remains the sole SQL applier. Its reviewed
  constants, verified release-manifest migration list, mounted SQL directory,
  and raw SQL hashes must all identify exactly 001–005 before the first database
  statement; a missing, extra, or changed pending file is not self-authorizing.
  Schema before is
  any exact applied prefix of immutable migrations 001–005; after is exactly all
  five rows with source checksums. There is no new SQL, backfill, down migration,
  index impact, or business-data scan.
- The migrator validates the whole ledger before applying its missing suffix and
  uses total-deadline `pg_try_advisory_lock`; a stalled lock query destroys the
  candidate connection. Unknown, duplicate, holey, reordered,
  drifted, or post-005 rows stop. Each migration retains its own transaction and
  5-second SQL lock timeout; failure preserves the committed prefix for retry.
- Health accepts healthy containers/storage/integration with payment disabled
  only when both `SIMULATED_SOURCE` and `EXTERNAL_GRANT_REQUIRED` occur in the
  closed safe-shadow reason set, within a monotonic total deadline communicated
  to each observation. A port race, partial Compose start, or health failure
  stops only the candidate. systemd is opt-in and restricted to the exact
  private user-unit root; failure restores its prior unit and returns Compose
  fallback.

Migration-ledger volume is zero to five rows. The ordered validation query has
no meaningful query-plan or index cost. Advisory wait is bounded at 15 seconds;
stop conditions are ledger divergence, lock deadline, SQL error, unsafe health,
lost edge port, or unresolved image digest. Recovery is forward-only from the
last exact committed prefix; rollback after committed schema change is not claimed.

## Installer Task 3 rulings (2026-09-30)

- The packaged Bash launcher delegates JSON/schema/state work to a packaged,
  checksummed Python helper; Bash never parses JSON or persists state itself.
- Task 3 accepts only the frozen Linux matrix and local Docker socket. Dependency
  installation is a separate exact-argv action requiring both `--install-deps`
  and a SHA-256 approval; there is no implicit privilege escalation.
- Task 3's terminal state is `CONFIGURED`. `source_mode=shadow` remains a safety
  assertion, not permission to select a fixture or start services.
- Web, gateway, and metrics ports are preflight collision probes only. Task 4
  owns whether gateway/metrics remain internal and which frontend port is
  published.
- The archive contract includes `lib/{common.sh,runtime.py}` and the three closed
  schemas so the verified package contains every runtime dependency under its
  inner checksums. A standalone Python dependency/bootstrap policy remains a
  release-builder decision; Task 3 invokes only fixed `/usr/bin/python3`.

## Current behavior

The runner can accept schema-shaped but semantically dishonest inventories,
evidence is not finally re-bound/rehashed, A30 is coarsely classified live, and
no checked-in executable plan exists. Production gateway identity/finality and
browser payment wiring deliberately fail closed, so A13/A14 cannot run. No
Published `v0.0.1` remains immutable at its reviewed commit and assets. Root
VERSION now identifies the follow-up candidate as `0.0.2`; its manifest is
pending final artifact bytes and no `v0.0.2` tag or GitHub Release exists.

## Proposed behavior

Deliver six sequential fail-closed phases. P0–P1 are local. P2 public reads,
P3 testnet write, and P5 publication each consume a separate short-lived exact
grant; none inherits authority from scope approval. P4 freezes the release
candidate and artifacts before publication.

## Components and boundaries

- Acceptance producer/consumer share closed semantic validation and immutable
  evidence/result sealing.
- Production gateway/browser policy wiring is implemented and reviewed before
  any wallet boundary becomes reachable; configuration cannot bypass review.
- Browser/human wallet owns signature confirmation; the agent never handles
  key, seed, signature, session, or backup material.
- Release builder consumes only the exact clean release commit and emits a
  manifest/checksums; GitHub publication consumes only those allowlisted bytes.

## Data flow

`release commit R -> reviews/verifier -> out-of-tree acceptance/evidence ->
artifact build/checksums -> exact grants -> public read/testnet reconciliation
-> annotated tag(R) -> GitHub draft/assets/read-back -> final publish approval`.
Acceptance assets describe R and are never committed back into R.

## API and event contracts

P0 may strengthen result/evidence/plan schemas and semantic validation without
weakening A01–A30. P3 adds reviewed production x402 identity/finality/browser
adapters while preserving HTTP contracts. Migration 003 adds only an append-only
one-shot grant-consumption relation: the grant digest, grant UUID and payment
attempt are each unique. Its row is committed in the same ledger transaction
as `VERIFIED -> SUBMITTING`, before facilitator I/O, so restart and replica races
cannot create a second submission. It contains no secret or wallet material.
Migration 004 extends immutable receipts with the exact before/after native-
balance observations, their block identities, broadcaster, authorization and
transfer identities, and zero buyer-gas result. It refuses to migrate a ledger
containing legacy receipts because those facts cannot be reconstructed without
fabrication; operators must preserve evidence and stop instead.

## Governance context

Canonical governance JSON under `governance/` remains separately reviewed authority. Any rule, example, debt, or digest named here is non-authoritative context until the verifier rederives current governance evidence.

- Applicable rule IDs:
- Applicable canonical example IDs/versions:
- Open or overdue debt IDs:
- Expected governance handoff or receipt impact:

## Bitrix-specific impact

- Modules/events/agents/components affected:
- Cache and managed cache impact:
- Installation/update/uninstall impact:
- Core modification: forbidden unless explicitly approved.

## Decisions

- Root product release/tag is `0.0.1`/`v0.0.1`; component packages and inherited
  APIs remain `0.1.0`.
- Final acceptance and release evidence live immutably outside the subject tree
  and ship as checksummed release assets.
- A30 local fake-provider criterion and real-wallet observation are separate.
- Release may be deliberately incomplete only with explicit owner acceptance
  and prominent limitations; it cannot be called completed F7.
- Current decision is NO-GO for P2, P3, and P5.

## Exact Permit2 settlement authority with EIP-2612 gas sponsorship

The pinned official x402 2.16 implementation defines the selected flow as a
Permit2 witness authorization plus the `eip2612GasSponsoring` extension. The
buyer signs both authorizations off chain; the facilitator atomically calls
`settleWithPermit` on the exact proxy and pays transaction gas. No buyer chain
transaction or pre-approval is allowed. A transaction-bearing
`settlement_pending` response is therefore spent and confirm-only, never a
retry instruction. Sources:

- <https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md>
- <https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v1.md>

Accordingly, the approved `0.0001` test-BTC ceiling is a buyer-native-gas spend
ceiling, not authority over facilitator gas. This exact Permit2 path requires
buyer gas spend to equal zero and proves this conservatively with before/after
buyer native-balance observations plus `tx.from != buyer`, exact canonical
Permit2/proxy addresses, exact re-encoded `settleWithPermit` calldata, and the
MUSD `Transfer` log. Missing observations
or any buyer delta enter manual review. Migration 003 atomically consumes the
grant before the one facilitator call; pending or ambiguous outcomes remain
spent and reconciliation-only through twelve canonical confirmations.

## Risks and mitigations

- Self-certified PASS: closed per-case claims/validators and mutation tests.
- Secret leakage: allowlisted structured fields, raw-stream hashes, canaries,
  history/artifact scans, and stop-on-suspicion.
- Duplicate charge: durable submitting boundary, one-submit envelope, human
  confirmation, UNKNOWN/no-retry, canonical reconciliation.
- Partial publication: preserve pushed main, never move published tags; resume
  only missing verified step or publish a new corrective version.
- Stale authority: every grant binds exact digest, identity, targets, bounds,
  expiry, and action; any change invalidates it.
