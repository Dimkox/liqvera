# Security re-review — live testnet paywall

## Review binding

- Base: `e3df6833e8916d01f55028e63d4db1632a805a75`
- Reviewed head: `a45f0c01587584f94467b557962b74d9a894a65a`
- Previous review: `security-review-paywall-live.md` at reviewed head `c7422080cc8ba827ca92a78600953d62161855bb`
- Scope: prior findings SEC-01/SEC-02, grant and payer authorization, replay/exactly-once, x402/Permit2, chain confinement, logs, fail-closed behavior, and live Compose wiring.
- Constraints observed: no secret reads, no external calls, no product-code edits.

## Verdict

**FAIL — both prior findings are repaired, but the Compose repair introduces a material database network-segmentation regression.** Do not record a passing `security_review` receipt for this head.

## Prior findings

### SEC-01 — Resolved — grant is bound to the actual credential-free loopback database endpoint

`main.ts:15-29` now derives `databaseIdentity(config.databaseUrl)` before live composition and supplies it in the mandatory production `LiveCompositionInput`. `LivePaymentGrant.assertContext()` compares that value with `grant.database_identity`. The reused identity policy rejects non-loopback hosts and binds protocol, host, port, and database while excluding credentials. A mismatch fails startup before facilitator initialization, quote issuance, or settlement.

Tests cover credential independence, port/database changes, remote/resolution rejection, exact production-composition match, and mismatch. This closes the cross-ledger grant reuse path identified in SEC-01.

### SEC-02 — Resolved — grant file is read as a stable private descriptor snapshot

`readPrivateGrantFile()` now validates regular-file type, single link, private mode, and the 1..16384-byte bound before open, immediately after `O_NOFOLLOW` open, and after the bounded positional read. It binds device/inode/size, rejects short reads and overflow, and rejects mode, link-count, mtime, or ctime changes before returning the copied bytes.

Focused tests exercise symlink, hard link, permissive mode, empty/oversized input, post-open chmod, and post-read content mutation. The residual same-UID actor can alter the source, but any mutation overlapping this snapshot is detected through descriptor metadata; mutation after the final descriptor check cannot alter the returned buffer.

## New finding

### SEC-03 — Medium — loopback DB binding is implemented by collapsing the PostgreSQL and gateway network boundaries

The live gateway now uses `network_mode: service:postgres-live` (`deploy/mezo-evidence/compose.yaml:362`) so that its database URL can be `127.0.0.1`. To make gateway ingress, report access, metrics, and payment egress work in that shared namespace, `postgres-live` is attached to all five gateway networks and carries the `gateway` and `gateway-metrics` aliases (`compose.yaml:292-297`). Rendered Compose confirms that PostgreSQL—not a gateway-only network endpoint—owns `edge`, `gateway_report`, `operations`, and the non-internal `payment_egress` attachment.

There is no explicit PostgreSQL `listen_addresses=127.0.0.1` confinement in this Compose service. Consequently the tree does not establish that port 5432 is restricted to loopback inside the shared namespace. Containers previously separated from `gateway_db` (edge, report, and operations peers) may reach the payment ledger if PostgreSQL listens on the namespace interfaces, while PostgreSQL also gains outbound egress. Password/SCRAM authentication is defense in depth, but it does not preserve the prior least-privilege network boundary around the authoritative grant-consumption and entitlement ledger.

Impact: compromise of a lower-trust peer has a new direct path to attack the payment database; compromise of PostgreSQL gains the gateway's external payment egress. This does not itself produce a second settlement, but it materially weakens the isolation protecting the exactly-once boundary.

Required repair:

1. Preserve a dedicated database network boundary. Prefer a narrowly scoped loopback/Unix-socket bridge whose only purpose is connecting gateway to PostgreSQL, rather than putting PostgreSQL in every gateway network namespace.
2. If the shared namespace is retained, explicitly bind PostgreSQL to loopback only and add an executable network test proving port 5432 is unreachable from edge, report, operations, and egress peers while gateway can still connect. Also document and accept the remaining shared-egress trust expansion.
3. Keep the grant's credential-free database identity aligned with the final endpoint and retain the current mismatch tests.

## Controls revalidated

- **Payer and terms:** live grant payer is enforced before persistence; facilitator verification, decoded Permit2/EIP-2612 identity, quote, payer, payee, token, exact amount, signatures, and deadlines are cross-bound.
- **Replay/exactly once:** grant digest and ID remain unique append-only records consumed transactionally before `SUBMITTING`; a loser is rejected and its quote is reopened without settlement. `SUBMITTING`/`UNKNOWN` paths remain confirm-only.
- **Expiry/fail closed:** absent, malformed, mismatched, expired, already-consumed, or unsupported authority blocks new settlement. Consumption is rechecked before payment requirements and verification.
- **Testnet/x402 confinement:** Mezo testnet chain/network, MUSD, amount, Permit2/proxy, facilitator, RPC, capability extension, finality, transfer identity, and zero buyer gas evidence remain closed and independently checked.
- **Secrets/logs:** the payment grant is a dedicated Compose secret with a private-mode target; application logging remains allowlist-only and excludes grant bytes, credentials, signatures, headers, URLs, and error objects.

## Verification evidence

- `npm test` in `apps/mezo-gateway`: **45 passed, 0 failed, 6 skipped** (the skips require an explicitly disposable PostgreSQL URL).
- Rendered `docker compose --profile live ... config --format json`: confirmed `gateway-live.network_mode=service:postgres-live` and `postgres-live` ownership of `edge`, `gateway_db`, `gateway_report`, `operations`, and `payment_egress`.
