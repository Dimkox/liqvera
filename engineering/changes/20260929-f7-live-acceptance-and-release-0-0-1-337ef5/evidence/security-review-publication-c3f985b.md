# Security review — final publication fingerprint

## Review binding

- Commit: `c3f985bd8df743d6c2c0a186dcf99c69329f6b13`
- Tree: `709a56736807b06424bb5450b893687e9d23eacf`
- Security-approved runtime ancestor: `95d438bad1e6bb56a74498c609585546c314cb38`
- Route: `337ef5ec16a0`
- Scope: publication delta, secret exposure, and signed-v2 live-acceptance evidence.
- Constraints observed: review-only; no secret reads, network calls, wallet actions, deployment, payment, push, tag, or release mutation.

## Verdict

**PASS — no blocking security findings.** The publication fingerprint preserves the previously approved runtime and adds only documentation/evidence.

## Delta classification

The complete `95d438b..c3f985b` delta contains ten text files: README, handoff, release/acceptance records, architecture inventory entries, and the five independent review reports. No application code, configuration, migration, deployment manifest, executable, dependency, browser asset, payment policy, grant parser, issuer pin, or secret-mount definition changed.

The signed-v2 security boundary therefore remains the one approved at `95d438b`: release-pinned Ed25519 issuer, strict canonical signed policy, exact Mezo testnet/payment/runtime bindings, durable count/amount/per-payer reservation, and the independent `LIQVERA_TESTNET_DEMO_ANY_PAYER=1` narrowing gate.

## Live-evidence review

The added acceptance record identifies the deployed commit/tree, bounded 23-hour authority, 20-settlement and 0.20-test-MUSD aggregate caps, one settlement per payer, report/quote/transaction/block identities, confirmation count, and report/archive SHA-256 values. The arithmetic is consistent with the signed per-payment amount: `20 × 10000000000000000 = 200000000000000000` atomic test MUSD.

The record states one encrypted-signer submission, an initial uncertain response, confirm-only reconciliation of the existing transaction, and successful entitlement delivery. It does not treat the read-only retry as another payment and does not claim mainnet, exchange mutation, custody, push, tag, or release. Public transaction hashes, UUIDs, block numbers, timestamps, confirmation counts, and content digests are identifiers/evidence, not signing or authorization capabilities.

## Secret and capability exposure

- No grant envelope/payload bytes, Ed25519 private key, wallet private key, mnemonic, payment signature, bearer token, database credential, report token, or authenticated connection string was added.
- The recorded issuer private-key filesystem location is metadata already permitted by repository policy; neither the key contents nor a derivable secret is present.
- The changed evidence does not disclose a payer address or reusable x402 authorization. It records only public-chain and artifact identities.
- References to the pinned issuer contain public-key/fingerprint facts only and do not widen the runtime trust root.

## Verification evidence

- `git diff --name-status 95d438b..c3f985b`: only the ten documentation/evidence paths described above.
- `file` classification: every changed path is ASCII or UTF-8 text; no binary or executable payload was introduced.
- Added-line targeted secret/capability scan: no private-key block, mnemonic, credential-bearing PostgreSQL URL, authorization header, API key, access token, private-key assignment, or payment-signature assignment found.
- `git diff --check 95d438b..c3f985b`: **PASS**.

No additional runtime test was required for this documentation-only delta; the fingerprint retains the independently reviewed `95d438b` product tree unchanged.
