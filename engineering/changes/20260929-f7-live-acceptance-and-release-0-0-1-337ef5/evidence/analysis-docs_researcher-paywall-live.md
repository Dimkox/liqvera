# Pinned live-source and Mezo payment inputs

Route: `337ef5ec16a0`
Scope: read-only inspection of repository-local code, contracts, runbooks, and package locks. No web request was needed and no secret file or secret value was read.

## Hyperliquid public snapshot

The implemented live capture is credential-free. `packages/public-capture/src/mee_public_capture/runtime.py` sends exactly:

- `POST https://api.hyperliquid.xyz/info`
- JSON body `{"type":"l2Book","coin":"BTC"}`
- 10-second client timeout

The same endpoint is frozen by `schemas/mezo-evidence/v1/capture-evidence.schema.json` and `tools/mezo_compatibility.py`. The response must identify `coin = BTC`, contain `time`, and contain exactly two non-empty level arrays whose `px` and `sz` values are decimal strings. The capture path retains the response bytes as the Hyperliquid envelope. The compatibility probe additionally caps accepted depth at 20 levels per side.

No Hyperliquid API key, wallet, account, exchange credential, or signing key is required. The only external input is ordinary HTTPS reachability to `api.hyperliquid.xyz`; for the acceptance runner, a short-lived, commit/tree/plan-bound public-read grant and its consumption journal are also required because the runner deliberately refuses ambient network authority.

## Pinned Mezo/x402 identities

Repository-local protocol constants in `packages/mezo-protocol/src/index.ts`, the acceptance plan, and compatibility probe agree on:

| Item | Pinned value |
| --- | --- |
| Network | `eip155:31611` / chain ID `31611` (Mezo Matsnet) |
| RPC | `https://rpc.test.mezo.org/` |
| Facilitator | `https://facilitator.vativ.io/` |
| Asset | test MUSD `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`, 18 decimals |
| Price | `0.01` MUSD = `10000000000000000` atomic units |
| x402 | v2, `exact`, `permit2` |
| Permit2 | `0x000000000022D473030F116dDEE9F6B43aC78BA3` |
| Exact Permit2 proxy | `0x402085c248EeA27D92E8b30b2C58ed07f9E20001` |
| Sponsorship | EIP-2612 `eip2612GasSponsoring`; MUSD domain `Mezo USD`, version `1` |
| Finality | 12 canonical confirmations |
| Settlement limit | exactly one facilitator submission |

Both web and gateway package manifests pin `@x402/core`, `@x402/evm`, and `@x402/paywall` to `2.16.0`; the gateway also pins `@x402/express` and `@x402/extensions` to `2.16.0`. Their package lock resolves these direct packages at 2.16.0. The unrelated nested dependency entries at other versions are not the reviewed Liqvera composition identity.

The browser composition uses the official x402 client with an injected signer and the pinned RPC. It requires both the Permit2 transfer method and the EIP-2612 gas-sponsoring extension. The gateway validates both signatures, quote/report binding, payer, recipient, token, amount, nonces/deadlines, Permit2/proxy identities, and later binds the transaction calldata and MUSD `Transfer` log. A facilitator success response alone is not a receipt.

## External inputs actually required for one live testnet payment

1. **A public merchant address** supplied as `PAY_TO` / deployment `LIQVERA_PAY_TO`. It must be non-zero, verified, dedicated to testnet, and distinct from the buyer. The merchant private key is not required by Liqvera.
2. **A separate buyer wallet/signer** on chain 31611, presented through the browser/injected signer boundary. It must hold at least 0.01 test MUSD. Repository policy expects the facilitator-sponsored path to leave buyer native-gas spend at zero; the demo runbook nevertheless asks for a buyer with test BTC as operational preparation.
3. **Human-wallet-produced authorization**, not a stored key: the SDK-produced `PAYMENT-SIGNATURE` must contain the exact Permit2 authorization and the MUSD EIP-2612 sponsorship signature. For the one-shot P3 operator this is a private, mode-0600 JSON input with fields `schema`, `quote_id`, `scope_hash`, `report_id`, `payment_signature`, `buyer`, and `pay_to`.
4. **Short-lived explicit payment authority**: the P3 grant bundle must be bound to the exact clean Git commit, tree, canonical P3 plan, buyer, pay-to address, facilitator/RPC identities, local database identity, one submission, and an expiry no more than 15 minutes away. A prior sealed grant cannot simply be reused for a changed or dirty tree.
5. **A local PostgreSQL endpoint**, provided through exactly one of `DATABASE_URL` or `DATABASE_URL_FILE`. P3 restricts it to loopback and binds a credential-free endpoint digest. Migrations 001-005 with their reviewed checksums and the quote/report/payment rows must already exist. The database credential is local runtime material, not a Mezo or Hyperliquid credential.
6. **Network reachability** to the pinned facilitator and Mezo RPC. Preflight must verify chain ID, deployed MUSD bytecode/decimals, and facilitator support for x402 v2, the network, asset, and selected scheme. Post-settlement RPC reads must produce canonical transaction, receipt, block, log, and 12-confirmation evidence.
7. **A payable immutable report and quote** whose expected payer, recipient, report ID/digest, amount, and scope match the signed payload. Report artifacts and the entitlement ledger remain local inputs to payment execution.

For the ordinary multi-service stack, PostgreSQL credentials and the internal report-service bearer token remain secret-file inputs. They are runtime infrastructure secrets, not wallet/exchange credentials. A public deployment additionally needs a real HTTPS `PUBLIC_BASE_URL`/origin and TLS/DNS, but those are not needed merely to capture Hyperliquid or execute the bounded local P3 acceptance operator.

## Inputs that are not required and must not be sought

- Hyperliquid credentials of any kind: the used `/info` endpoint is public and read-only.
- A merchant private key, seed phrase, custody key, or token-admin/mint authority.
- A buyer private key in an environment file or repository file; signing stays in the human wallet boundary.
- Mainnet RPC, real MUSD, exchange mutation authority, or a direct ERC-20 transfer constructed by Liqvera.
- An invented facilitator status endpoint or a retry authorization. After a submission becomes ambiguous, the path is confirm-only and the grant is treated as spent.

## Practical blocker diagnosis

`EXTERNAL_GRANT_REQUIRED` does not mean that unknown Hyperliquid credentials are missing. It means the normal gateway startup intentionally supplies no `LivePaymentGrant`/live composition. Enabling the reviewed payment path therefore requires fresh exact-subject grant material plus a wallet-produced payment payload and the local ledger context above. Hyperliquid live capture can proceed independently with no credentials.
