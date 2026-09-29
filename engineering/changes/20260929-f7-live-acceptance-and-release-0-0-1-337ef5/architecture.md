# Architecture — F7 live acceptance and release 0.0.1

> Typed authority: [`change-spec.yaml`](change-spec.yaml). This Markdown explains context and cannot override typed IDs, risk, acceptance criteria, forbidden outcomes, or approval scopes.

## Current behavior

The runner can accept schema-shaped but semantically dishonest inventories,
evidence is not finally re-bound/rehashed, A30 is coarsely classified live, and
no checked-in executable plan exists. Production gateway identity/finality and
browser payment wiring deliberately fail closed, so A13/A14 cannot run. No
root VERSION, release manifest, `v0.0.1`, or GitHub Release exists.

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

## Exact EIP-3009 settlement authority

The official x402 exact-EVM specification defines EIP-3009 as a gasless buyer
authorization: the buyer signs `transferWithAuthorization` fields and the
facilitator broadcasts the transaction and pays its gas. A transaction-bearing
`settlement_pending` response is therefore spent and confirm-only, never a
retry instruction. Sources:

- <https://github.com/x402-foundation/x402/blob/main/specs/schemes/exact/scheme_exact_evm.md>
- <https://github.com/x402-foundation/x402/blob/main/specs/x402-specification-v1.md>

Accordingly, the approved `0.0001` test-BTC ceiling is a buyer-native-gas spend
ceiling, not authority over facilitator gas. The exact EIP-3009 path requires
buyer gas spend to equal zero and proves this conservatively with before/after
buyer native-balance observations plus `tx.from != buyer`. Missing observations
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
