# Security review — wallet, public demo, and testnet payment authority

## Review binding

- Commit: `cba005b1c07aafadb4dd15743b7184143143dcf5`
- Tree: `75151ba8b154b72fd77d3df844beb4d3eca89dac`
- Route: `337ef5ec16a0`
- Scope: wallet discovery, Mezo add/switch flow, payment grant and entitlement behavior, public historical demo assets, CSP, and secret handling.
- Constraints observed: review-only; no application code, secrets, wallet actions, network calls, or external mutations.

## Verdict

**FAIL — one high-severity payment-authority escalation.** Do not record a passing security receipt for this commit.

## Finding

### SEC-04 — High — an environment flag expands a signed buyer-bound grant into seven-day any-payer authority

The checked grant schema still contains an exact `buyer`, an exact expiry, and `maximum_settlement_submissions: 1`. The new `LIQVERA_TESTNET_DEMO_ANY_PAYER=1` configuration is not part of those signed/hashed grant bytes, but it changes their authorization semantics:

- `config.ts:49-51` accepts the ambient flag whenever a live grant file exists.
- `main.ts` copies the flag into the authorization context.
- `live-grant.ts:23-24,42-50` ignores `grant.buyer` when the flag is set and raises the accepted grant lifetime from 15 minutes to seven days.
- `x402.ts:60-63,111-118` removes the expected-payer readiness binding and accepts the payer from each quote instead of the payer authorized by the grant.

This makes deployment configuration an authority amplifier: unchanged grant bytes issued for buyer A and a duration rejected by the normal policy can be accepted for unrelated buyer B for up to seven days. No field inside the grant authorizes this mode or lifetime. A test explicitly demonstrates that the same buyer-bound grant becomes valid for a different buyer when the ambient flag is enabled, confirming the bypass rather than preventing it.

The durable ledger still prevents two successful settlements with the same grant digest/ID, so this is not an unlimited-spend bug. It is nevertheless a material authorization violation: the identity of the one payer permitted to consume the grant, and the time window in which consumption is permitted, are changed outside the grant authority.

Required repair:

1. Remove ambient `demoAnyPayer` authority widening. Default behavior must continue to bind `grant.buyer` and the 15-minute lifetime.
2. If public any-payer demos are required, introduce a versioned grant schema/mode that explicitly authorizes `payer_policy: any`, its exact maximum lifetime, settlement count/budget, recipient, chain, asset, amount, commit/tree/plan, and database identity. The grant issuer—not an environment variable—must select that authority.
3. Keep the runtime configuration fail-closed: configuration may select only a mode already encoded in the grant and may never widen its payer, duration, count, amount, chain, token, or recipient.
4. Add negative tests showing that a buyer-bound grant remains buyer-bound and 15-minute-bounded under every environment setting, plus schema tests for any separately approved public-demo grant.

## Controls that passed

### Wallet discovery and chain management

- EIP-6963 discovery uses provider objects received from the provider store, deterministically sorts choices, and uses legacy `window.ethereum` only as fallback.
- Provider names are inserted with `textContent`, preventing provider-announcement HTML injection.
- Late discovery is triggered only by the explicit Connect action. Account access, chain switch, and chain addition are wallet-mediated user actions; error `4902` is the only path to `wallet_addEthereumChain`.
- Added-chain parameters come from pinned Mezo protocol constants. The client re-reads `eth_chainId` and fails unless it is chain 31611.
- Payment revalidates both account and chain immediately before invoking the reviewed x402 adapter. Account/chain events only update state and cannot submit payment.

### Payment, replay, and entitlement

- Quote terms, expected payer, Permit2/EIP-2612 signatures, MUSD token, exact `0.01` test MUSD amount, recipient, Mezo chain, and facilitator capability remain cross-bound before settlement.
- Grant consumption remains an atomic durable boundary before `SUBMITTING`; ambiguous outcomes remain confirm-only and browser recovery does not resettle.
- A transient incomplete RPC observation now preserves the paid entitlement and returns `PAYMENT_UNCERTAIN`; a positive mismatch still enters manual review. This avoids destructive entitlement loss without weakening canonical revalidation.

### Public historical demo and CSP

- The public report and ZIP hashes match the pinned identities in `historical-demo.ts`.
- The archive contains only deterministic report/algorithm/public Hyperliquid capture evidence; member names are relative and bounded. Review scans found no private key, seed, payment signature, bearer capability, password, or authentication secret.
- The UI labels the asset historical, dated, public, non-fresh, non-executable, and payment-free. It does not confer paid entitlement or enter the payment state machine.
- CSP remains `default-src 'none'`, same-origin scripts/styles/connect, no inline script allowance, no frames/objects/forms, and `frame-ancestors 'none'`. External links use `noopener noreferrer`.
- Runtime containers remain non-root/read-only with dropped capabilities. The web build's temporary root phase only normalizes permissions on the two immutable public demo assets before returning to UID 101.

### Secrets

- The committed tree contains no detected private-key, seed, access-token, or payment-signature material.
- Grant, PostgreSQL password, and report token remain separate file-backed secrets excluded by Docker build contexts; browser/public containers receive none of them.

## Verification evidence

- `apps/mezo-web: npm test`: **25 passed, 0 failed**.
- `apps/mezo-gateway: npm test`: **51 passed, 0 failed, 6 skipped**; skips require an explicitly disposable PostgreSQL URL.
- `apps/mezo-web: npm run build`: typecheck completed, then Vite failed because existing `node_modules/.vite-temp` was not writable (`EACCES`). This is a local workspace-permission limitation, not evidence against SEC-04 and not a passing build claim.
- Public asset SHA-256: report `8f8fd199de1674e5b3f154e50609792bd7bdd711e15cd8a8c15cd703bcaac7dd`; ZIP `a6cc771d3fb8428325d32855fef53417f7da25c893db3a99b49802f482adc4fc`.
