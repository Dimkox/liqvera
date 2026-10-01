# Security re-review — pinned signed-grant issuer

## Review binding

- Commit: `95d438bad1e6bb56a74498c609585546c314cb38`
- Tree: `419edfbc6ba05109fa63e4be522087475f68ca1c`
- Route: `337ef5ec16a0`
- Scope: final SEC-04/SEC-05 closure, independent issuer allowlist, signer/grant substitution, operator any-payer gate, and previously reviewed payment-security controls.
- Constraints observed: read-only product review; no secrets, wallet actions, network calls, or external mutations.

## Verdict

**PASS — no blocking security findings. SEC-04 and SEC-05 are closed at this tree.**

## Prior findings

### SEC-04 — Resolved

Any-payer authority is present only in the canonical, Ed25519-signed v2 policy. The signed bytes bind `ANY_VALID_X402_PAYER`, exact per-payment amount, total/count/per-payer budgets, validity interval, recipient, Mezo testnet chain and MUSD asset, Permit2/EIP-2612 mode, facilitator/RPC endpoints, commit/tree/plan, and credential-free loopback database identity. V1 remains buyer-bound and retains its 15-minute lifetime.

The operator flag is now a second, narrowing gate rather than an authority source: `main.ts` propagates `testnetDemoAnyPayer`, and `composeOfficialX402()` rejects every v2 grant unless `LIQVERA_TESTNET_DEMO_ANY_PAYER=1`. Setting the flag cannot widen a v1 grant, alter signed v2 fields, introduce another issuer, or bypass v2 verification. Missing/zero/malformed configuration fails closed.

### SEC-05 — Resolved

`live-grant-issuers.ts` contains the release-reviewed key-ID to raw-public-key pin. `LivePaymentGrant.parseBytes()` checks the envelope `key_id` and runtime public key against that independent compiled allowlist before v2 parsing and signature verification. The runtime `LIQVERA_LIVE_GRANT_PUBLIC_KEY` can therefore select only the already approved key; it cannot introduce a trust root.

Key rotation now requires a reviewed source/release change. A correctly signed envelope from a newly generated but unapproved key is rejected with `LIVE_GRANT_ISSUER_UNAPPROVED`, as is substitution of only the runtime public key. The approved fixture also proves that signature tampering is rejected. Existing strict duplicate-key parsing, exact JCS canonical-byte comparison, Ed25519 verification, key-ID derivation, and exact field-set validation remain intact.

## Security controls rechecked

- The approved allowlist contains only a public Ed25519 key. No signing private key is committed or accepted by runtime configuration.
- Grant-file loading remains bounded to 16 KiB and rejects symlinks, non-regular files, hard links, group/other permission bits, inode/device/size changes, partial/extended reads, and metadata/content changes across the open/read window.
- Durable v2 authority activation and reservation remain bound to grant/policy/signature/key digests. Count, total amount, and one-per-payer limits are reserved transactionally before facilitator I/O; replay and ambiguous submissions remain fail-closed/confirm-only.
- Mezo testnet, chain `31611`, test MUSD, exact `0.01` MUSD, recipient, Permit2 proxy, zero buyer native-gas authority, facilitator, and RPC bindings remain exact.
- The selected wallet provider owns account/chain listeners; account and chain are revalidated before payment. Historical report/ZIP integrity checks, deny-by-default CSP, text-only untrusted rendering, and browser secret separation are unchanged from the prior review.

## Verification evidence

- `apps/mezo-gateway: npm test`: **51 passed, 0 failed, 7 skipped**. The skipped integration cases require an explicitly disposable PostgreSQL URL; the runnable suite includes approved/unapproved issuer substitution, runtime-key substitution, signature tampering, v2 operator-gate rejection, v1 buyer preservation, exact signed bindings, grant-file TOCTOU checks, replay behavior, and payment-policy checks.
- `git diff --check 87d8ac4..95d438b`: **PASS**.
- Review found no committed private signing key, wallet key, seed phrase, payment signature, or access-token material in the changed runtime surface.

## Non-blocking note

The human-readable JSON allowlist duplicates the compiled TypeScript pin but is not a runtime trust input. Keeping an automated equality check between those two release artifacts would prevent documentation drift; current values match exactly and this does not weaken the enforced trust boundary.
