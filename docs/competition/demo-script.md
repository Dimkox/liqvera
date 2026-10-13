# Liqvera live demonstration

Use the current Testnet deployment and the [demo runbook](../runbooks/testnet-demo.md). The owner has authorized a 0.01 test-MUSD purchase; a real wallet signature is still needed. Show only actions actually completed.

1. Open [liqvera.site](https://liqvera.site). Show Mezo Testnet and the public, read-only Hyperliquid BTC perpetual instrument.
2. Open the wallet-free preview. Show its October 12 capture timestamp, quantity, hashes and evidence ZIP. It is a sealed historical capture, not a new payment.
3. Connect a wallet holding test MUSD, request a fresh BUY/SELL report and review the capture time, limitations, recipient and 0.01 test-MUSD price.
4. Confirm the limited wallet authorization. Wait for canonical confirmation; if the outcome is uncertain, use Check status instead of signing again.
5. Show the actual receipt and transaction hash. Download the paid report JSON and ZIP, then run the offline verifier against the receipt's report digest. Reload and retrieve the same entitlement without another payment.
6. Close with the product's value: MUSD buys a portable analytical artifact that the recipient can independently check. Reports do not place trades or guarantee execution.

Hide wallet signatures, bearer capabilities and private account views. A public wallet address or unsigned 402 response is not proof of payment. If payment is not completed, stop that segment and retain its pending status. The separate local fixture demonstration transfers no tokens and cannot replace the paid run.
