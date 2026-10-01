# Security re-review — signed v2 grant authority

## Review binding

- Commit: `87d8ac45b11910f871e303cf1115fde5dcda36c6`
- Tree: `3300e6cfef7c5a70bcd0eb05cfdc23249f167698`
- Route: `337ef5ec16a0`
- Scope: SEC-04 closure, signing key and canonicalization, runtime bindings, durable budget/replay, prior wallet fixes, historical demo integrity, CSP, and secrets.
- Constraints observed: read-only product review; no secrets, wallet actions, network calls, or external mutations.

## Verdict

**FAIL — the v2 policy correctly moves authority into signed bytes, but the signer trust root is not independently pinned.** Do not record a passing security receipt for this commit.

## Prior finding

### SEC-04 — Partially resolved

The prior ambient any-payer widening is removed from `LivePaymentGrant` and `OfficialX402`. V1 remains exact-buyer and 15-minute bounded. V2 now explicitly signs `ANY_VALID_X402_PAYER`, recipient, chain, token, exact per-payment amount, total amount, maximum submissions, one settlement per payer, validity, commit/tree/plan, database identity, facilitator, RPC, and Permit2/EIP-2612 mode.

Runtime configuration no longer directly changes those signed policy values. However, the missing independent issuer pin described below still lets the configuration authority substitute the signer and thereby mint any accepted v2 policy, so the original separation between deployment configuration and grant issuer is not fully established.

## Blocking finding

### SEC-05 — High — configured key and envelope are self-consistent but not authenticated to an approved issuer

`LIQVERA_LIVE_GRANT_PUBLIC_KEY` supplies the raw Ed25519 public key through ordinary Compose environment configuration. `LivePaymentGrant.v2()` derives `keyId = SHA256(publicKey)` and accepts the envelope when its `key_id` equals that derived value and its signature verifies under that same key.

There is no independent allowlist or immutable pin for the expected key ID/public key in code, a release-bound policy, or a separately authenticated deployment artifact. The architecture calls the key ID “allowlisted” and “pinned,” but the implementation only proves internal consistency between:

1. a mutable runtime public-key variable;
2. a key ID supplied by the envelope; and
3. a signature supplied by the envelope.

An actor able to set the runtime environment can generate a fresh Ed25519 keypair, set its public key, and sign an arbitrary otherwise schema-valid any-payer policy. That actor therefore retains the same effective ability to widen payer/count/lifetime authority that SEC-04 was intended to remove. The signature protects against grant-file modification by an actor who cannot change the environment, but it does not authenticate the grant issuer across the configuration boundary under review.

Required repair:

1. Bind accepted signer identities to an independent authority: for example, compile an allowlisted key ID into the reviewed release, or load a keyring/policy file whose digest is itself pinned by the immutable release/deployment approval.
2. Reject every v2 envelope unless its `key_id` is in that independent allowlist before constructing/verifying the supplied key.
3. Treat key rotation as a separately reviewed change with overlap/revocation rules; do not allow an arbitrary environment value to introduce a new signer.
4. Add negative tests proving that a correctly signed grant from an unapproved key fails even when its public key is supplied at runtime, and that changing only the runtime trust key cannot create authority.

## Controls that passed

### Signed policy and canonicalization

- Strict duplicate-key JSON parsing is applied to both envelope and payload.
- The payload must exactly equal its RFC 8785/JCS canonical bytes before Ed25519 verification.
- The envelope is bounded to 16 KiB; public key and signature lengths are exact; signature and key mutations fail closed.
- Signed runtime bindings cover commit, tree, plan digest, recipient, credential-free loopback database identity, Mezo chain/network, test MUSD, exact amount, Permit2/proxy, facilitator, RPC, and EIP-2612 sponsorship.
- V2 validity is ordered, not-yet-valid/expired grants fail, and signed lifetime is capped at 24 hours. V1 retains its existing 15-minute bound.

### Durable budget and replay

- Migration 006 is additive and stores immutable authority and reservation evidence without private signing material.
- Authority activation records envelope digest, policy digest, key ID, signature digest, validity, recipient, count, total, per-payer cap, and payer policy.
- `markSubmitting()` locks the authority row and atomically reserves ordinal, payer, amount, total budget, and payment attempt in the same transaction as `VERIFIED -> SUBMITTING`, before facilitator I/O.
- Unique `(grant_digest, payer)` and unique payment-attempt constraints enforce one reservation per payer and no attempt reuse. Count and total bounds are redundantly enforced by signed parsing, database checks, and transactional reservation logic.
- Reservations are append-only and survive restart; ambiguous submissions remain confirm-only. Readiness consults remaining durable validity/count/amount budget.

### Wallet and historical demo fixes

- The selected late EIP-6963 provider now owns account/chain listeners; prior listeners are removed when provider ownership changes.
- Chain add/switch continues to use pinned Mezo constants, wallet mediation, explicit user action, and post-action chain verification. Account and chain are revalidated immediately before payment.
- Historical report and ZIP bytes are both SHA-256 verified in-browser before rendering or exposing the downloaded Blob. Fetches omit credentials and reject redirects.
- Provider-controlled names and report fields are rendered with `textContent`; no new HTML injection path was introduced.

### CSP and secrets

- CSP remains deny-by-default with same-origin scripts/styles/connect, no inline-script allowance, no frames, objects, or forms, and `frame-ancestors 'none'`.
- No private signing key is present in runtime configuration or the committed tree. The public key is non-secret; grant, database password, and internal report token remain separated from browser/public containers.
- Pattern review found no committed wallet key, seed phrase, payment signature, or access-token material.

## Verification evidence

- `apps/mezo-web: npm test`: **26 passed, 0 failed**.
- `apps/mezo-gateway: npm test`: **51 passed, 0 failed, 7 skipped**. Skipped cases require an explicitly disposable PostgreSQL URL, including the real migration-006 concurrency/budget test.
- The runnable gateway suite covers signature/key-ID mutation, duplicate keys, noncanonical payloads, lifetime bounds, v1 buyer preservation, v2 quote-payer binding, and fail-closed parsing.
