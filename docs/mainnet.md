# Mezo Mainnet configuration

Gateway runtime and browser build select the payment network with `LIQVERA_NETWORK=mainnet`. The default remains `testnet` for existing fixture and local workflows. Unknown values fail closed. Both components must use the same selection.

| Setting | Mainnet |
| --- | --- |
| Network | `eip155:31612` |
| MUSD | `0xdD468A1DDc392dcdbEf6db6e34E89AA338F9F186` |
| Decimals | 18 |
| Report price | 0.01 MUSD (`10000000000000000` atomic) |
| RPC | `https://mezo-mainnet.boar.network` |
| Explorer | `https://explorer.mezo.org` |
| Facilitator | `https://facilitator.vativ.io/` |

These values follow the official [network configuration](https://mezo.org/docs/users/getting-started/connect) and [x402 integration](https://mezo.org/docs/developers/getting-started/musd-payments-x402/). Read-only preflight verified the actual chain, token metadata, EIP-712 domain, settlement contracts and facilitator support.

## Ledger separation

Use a new database **name**, not merely a replacement volume at the same endpoint. Preserve the Testnet database and its unresolved payment records. Migration 007 adds paired network/token constraints and an immutable single-network ledger identity; migrations 001–006 retain their original checksums. Startup binds an empty ledger to the selected network and rejects a mismatched ledger before enabling workers or payments. The browser uses separate Mainnet session keys and retains Testnet recovery state.

## Payment authority

Keep the owner's approved recipient in `PAY_TO`. Mainnet moves real MUSD. An external grant must bind the selected network, token, RPC, amount, recipient, source commit/tree, plan digest and new database identity. Existing Testnet or expired authority cannot enable Mainnet payments. `LIQVERA_ANY_PAYER=1` permits a valid signed v2 policy; its budget, expiry and issuer checks still apply. The old Testnet-only environment flag is rejected on Mainnet.

The API and public preview remain available without a valid grant, while payment readiness remains false. Switching network configuration is not evidence of a successful payment. Paid acceptance requires an owner-authorized wallet signature, confirmed settlement and delivery of the exact report/ZIP; unknown outcomes remain confirm-only.

## Build and recovery

Build the gateway normally and set `LIQVERA_NETWORK=mainnet` in its runtime environment. Build the web image with `--build-arg LIQVERA_NETWORK=mainnet`. Run migrations on the new database, verify the ledger identity and use the same unchanged 0.01 MUSD price and approved recipient.

Preserve the previous gateway/web images and Testnet database for rollback. Reverting requires restoring the matching application network and database together; never relabel existing receipts or sealed reports. The published v0.0.2 installer remains a separate Testnet operator and does not install this Mainnet configuration.

## Public deployment

The public gateway and browser run this Mainnet configuration as of October 12, 2026, from source `6ee3bbe`. The existing recipient and 0.01 MUSD price are unchanged. All seven containers are healthy; HTTPS and browser checks confirm the Mainnet identity and working wallet-free preview. Payment authority is absent, so new payments remain disabled. The [deployment and security evidence](security/2026-10-12-mainnet.md) identifies exact running images, ledger separation and retained recovery state.
