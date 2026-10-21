# Liqvera Testnet demo

The public demo at https://liqvera.site uses **Mezo Testnet, chain 31611**. Each fresh report costs **0.01 test MUSD**. Market data comes from public Hyperliquid endpoints; payment uses test tokens. The wallet-free preview is a separately labelled sealed report.

## Present the demo

1. Open the site and connect an EVM wallet that supports Mezo Testnet. Select **Connect wallet** to use an injected browser wallet or WalletConnect through the AppKit wallet selector. Mobile browsers can use the wallet handoff; desktop browsers can display a pairing QR. Preparing the quote can precede switching networks; payment requires Mezo Testnet.
2. Enter a BUY or SELL quantity. Request a report and review the fresh snapshot, limitations, hashes, recipient and 0.01 test-MUSD price.
3. Confirm the payment in the wallet. The official x402 flow requests limited Permit2/EIP-2612 signatures; the facilitator sponsors settlement gas.
4. Wait for confirmed delivery, then download the JSON and evidence ZIP. Repeated retrieval uses the same entitlement and does not require another payment.
5. Verify the ZIP offline against the report digest. Preserve the transaction hash and receipt as acceptance evidence.

A 402 challenge is a request for payment, not a receipt. If settlement is uncertain, use **Check status**; do not submit a second payment. The gateway reconciles the existing attempt and requires at least twelve canonical confirmations. See [payment recovery](payment-recovery.md).

The wallet must hold test MUSD. The official [faucet](https://faucet.test.mezo.org/) supplies test BTC/MEZO; test MUSD is available through [Mezo Testnet borrowing](https://testnet.mezo.org/feature/borrow). Never enter wallet keys or seed phrases into Liqvera. The site receives signatures, not private keys.

## Deploy from this repository

Use Docker Compose 2.24.4 or later. Prepare the database and internal report secret files described in [startup](startup-shutdown.md), and set `LIQVERA_ENGINE_COMMIT`, `LIQVERA_PUBLIC_ORIGIN`, `LIQVERA_SITE_ADDRESS` and `LIQVERA_PAY_TO`. The recipient must be distinct from the buyer. These settings are public metadata, not private keys.

For a new Testnet deployment:

```sh
cd deploy/mezo-evidence
docker compose -p liqvera-testnet --profile live \
  -f compose.yaml -f compose.testnet-demo.yaml config --quiet
docker compose -p liqvera-testnet --profile live \
  -f compose.yaml -f compose.testnet-demo.yaml up -d --build
```

The explicit override selects Testnet in the gateway and browser, enables merchant checkout and removes operator-grant variables and mounts. Every purchase still needs a valid buyer signature. The default configuration retains the separate grant workflow; fixture services cannot make payments.

For an existing deployment, use its retained operational manifest and reviewed recovery procedure. Do not create a new project over existing volumes or point Testnet at a Mainnet ledger. Preserve historical SQL migration bytes, apply forward migrations through 008, and keep all pending/unknown records. Merchant startup rejects a missing nonce index or wrong ledger network. Back up durable state before migration; never restore an earlier database over later purchases.

## Acceptance and current evidence

Check `/healthz`, `/readyz` and `/v1/capabilities`: readiness must be HTTP 200, network `eip155:31611`, token `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`, price `0.01`, and `payment_ready=true`.

The [current deployment record](../security/2026-10-12-testnet.md) covers exact images, CVE scans, fresh public-report generation, payment challenge and browser checks. Historical paid Testnet delivery exists. A new successful payment must be recorded with its own transaction, confirmed receipt and verified downloads; historical receipts and unsigned browser tests do not prove that new run.
