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

## Wallet payments

Set `LIQVERA_PAYMENT_MODE=merchant` for ordinary report purchases. Keep the approved recipient in `PAY_TO`; the price remains 0.01 MUSD. Merchant mode requires `SOURCE_MODE=live-public` and rejects all operator-grant environment variables. Do not mount a payment grant in this mode. Each purchase still requires the buyer's wallet signatures; the facilitator verifies them and sponsors settlement gas. The server has no buyer wallet key.

The browser signs the selected chain and token. The gateway validates payer, recipient, exact amount and expiry, reads both artifact hashes, and durably reserves the Permit2 nonce before its sole settlement submission. Migration 008 prevents nonce reuse across different quotes, including concurrent requests. Repeated purchases by one wallet use new nonces. Unknown outcomes are confirm-only; delivery requires the confirmed on-chain transfer and matching report bytes.

The default `LIQVERA_PAYMENT_MODE=grant` retains the bounded operator workflow. Its external grant must bind network, token, RPC, recipient, source, plan and database; expired or mismatched grants keep payments disabled. `LIQVERA_ANY_PAYER=1` applies only to signed v2 grant policies, not merchant mode. Fixture mode can never enable payments.

## Build and recovery

Build the gateway normally and set `LIQVERA_NETWORK=mainnet` in its runtime environment. Build the web image with `--build-arg LIQVERA_NETWORK=mainnet`. Run migrations on the new database, verify the ledger identity and use the same unchanged 0.01 MUSD price and approved recipient.

Preserve the previous gateway/web images and Testnet database for rollback. Reverting requires restoring the matching application network and database together; never relabel existing receipts or sealed reports.

## Public demo network

The public demo currently runs on **Mezo Testnet (31611)** at the owner's request. Mainnet remains a supported configuration, with its separate database and recovery containers retained. The current [Testnet deployment record](security/2026-10-12-testnet.md) identifies exact images and checks; the [demo guide](runbooks/testnet-demo.md) explains wallet checkout and test-token setup. Earlier Mainnet records describe their dated deployment, not the active demo.
