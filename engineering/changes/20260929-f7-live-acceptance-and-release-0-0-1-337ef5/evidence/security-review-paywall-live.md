# Security review — live testnet paywall

## Review binding

- Base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Reviewed head: `c7422080cc8ba827ca92a78600953d62161855bb`
- Scope: grant-file loading, grant/context binding, payer authorization, replay/exactly-once behavior, x402/Permit2 boundary, Mezo testnet confinement, logging, and fail-closed behavior.
- Constraints observed: no secret reads, no external calls, no product-code edits.

## Verdict

**FAIL — one high-severity authorization-binding defect and one medium-severity file-snapshot hardening defect.** Do not record a passing `security_review` receipt for this head.

## Findings

### SEC-01 — High — ordinary gateway activation does not bind the grant to the configured database

The grant schema makes `database_identity` and `database_host_policy=loopback-only/v1` part of the authorization envelope, but ordinary startup never derives the identity of `config.databaseUrl` and never compares it with the grant. `LivePaymentGrant.parseValue()` only checks that `database_identity` is 64 lowercase hex characters (`src/security/live-grant.ts:17-21`); `LivePaymentContext` contains only commit, tree, plan, buyer, and payee (`src/adapters/x402.ts:12`, `src/config.ts:16-17`); and `main.ts:24-27` composes live payment without a database identity check.

This is a real authority-boundary regression relative to the existing P3 operator, which derives a credential-free, loopback-only PostgreSQL endpoint identity in `p3-operator.ts:39-45` and rejects a mismatch before settlement at `p3-operator.ts:90`. A grant authorized for one database can therefore activate the ordinary gateway against another PostgreSQL endpoint. Because durable grant consumption is the replay boundary, using an unintended database can also bypass the operator's intended consumption namespace and permit the same grant bytes to be consumed once in each database.

Required repair:

1. Before live composition/initialization, derive the credential-free database identity using the reviewed `databaseIdentity()` policy (including loopback-only resolution) and compare it to `grant.raw.database_identity`.
2. Fail startup before facilitator initialization or quote issuance on mismatch or non-loopback database configuration.
3. Add production-composition tests proving mismatch, remote host, changed port/database, and matching credentials-redacted endpoint behavior. Add an integration/contract test proving the same grant cannot be activated against a differently identified ledger.

### SEC-02 — Medium — grant-file safety properties are checked on the pathname before open, not fully on the opened snapshot

`readPrivateGrantFile()` correctly uses `lstat`, rejects symlinks, requires one link/private mode/a 1..16384-byte size, and opens with `O_NOFOLLOW` (`src/security/live-composition.ts:10-16`). After opening, however, it compares only device, inode, and size. It does not re-check `isFile()`, link count, or private mode on the opened descriptor, and it does not verify that the bytes read have the stat-observed length. A concurrent metadata change (for example private mode becoming group/world-readable or a new hard link) is therefore accepted, contrary to the stated private-mode/single-link snapshot invariant.

Required repair:

1. `fstat` immediately after open and again after read; on both snapshots enforce regular file, `nlink===1`, private mode, and bounded nonzero size, plus unchanged device/inode/size and `bytes.byteLength===opened.size`.
2. Add focused tests for symlink, hard-link, permissive mode, zero/oversize input, replacement between `lstat` and `open`, and metadata/size mutation during read. If the platform cannot make same-owner in-place writes race-free, document the residual same-UID trust assumption explicitly.

## Controls that passed review

- **Testnet confinement:** network/chain/token/amount, Permit2 addresses/mode, facilitator URL, and RPC URL are closed constants in `live-grant.ts`; the receipt reader independently checks Mezo testnet chain ID and exact transfer semantics.
- **Payer authorization:** new quote creation rejects a payer different from the live grant; x402 verification, decoded Permit2/EIP-2612 authorization, grant context, quote terms, payer, payee, asset, amount, deadlines, and signatures are cross-bound before settlement.
- **Exactly once / replay:** grant digest and grant ID are unique, append-only database records. Consumption occurs in the same transaction immediately before `SUBMITTING`; only the winner can call `settle`. `SUBMITTING`/`UNKNOWN` recovery is confirm-only and does not resubmit.
- **Expiry/fail closed:** grant expiry is re-evaluated after startup and again before settlement; malformed, absent, expired, mismatched, spent, or unsupported grants prevent a new external settlement.
- **Logging/secrets:** the structured logger uses a narrow allowlist and does not serialize errors, request bodies, payment headers, URLs, wallets, signatures, or grant bytes. Startup errors are reduced to `STARTUP_FAILED`.
- **x402/Permit2 boundary:** the facilitator-supported capability must match exact v2/Mezo/Permit2/EIP-2612 metadata; responses must bind to the quote and the receipt is independently reconstructed from canonical chain data before entitlement.

## Residual notes

- Readiness/capabilities query durable grant consumption, while an already-created `READY` quote reaches `markSubmitting()` without that precheck. This can cause a losing concurrent request to obtain/verify a signature and then fail closed at the atomic consumption boundary; it does **not** create a second settlement. Treat as availability/UX debt, not a payment-authority bypass.
- No evidence in this diff logs secret grant contents or adds mainnet/exchange mutation capability.
