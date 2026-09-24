# Fixture and testnet demo

## Fixture walkthrough

The `fixture` profile is deterministic and uses `SIMULATED` evidence. It can
show the preview, read-only report structure, and offline verification. It
must not return a canonical payable x402 quote, invoke a wallet transfer, or
be presented as a live Hyperliquid snapshot. Label the screen and any
recording accordingly.

## Live-public + Mezo Testnet gate

The `live` profile permits public Hyperliquid capture and only Mezo Testnet
payment. Before presenting a paid flow, the owner must review all of these
against real evidence:

1. The gateway reports a real live-public report with retained raw response,
   provenance, valid freshness, and a passing independent offline verifier.
2. The gateway's chain probe returns `31611`; token bytecode and 18 decimals
   match MUSD `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503`; the official
   facilitator supports `eip155:31611` and the selected x402 scheme.
3. `LIQVERA_PAY_TO` is a dedicated, verified merchant test wallet address,
   distinct from the buyer. The operator has established a reviewed
   authorization identity and receipt-finality rule. A blank address or
   `FINALITY_RULE_UNVERIFIED` is a blocker, not a demo shortcut. The reserved
   `LIQVERA_FINALITY_CONFIRMATIONS` example variable is not consumed.
4. The buyer uses a separate test wallet with test BTC and test MUSD. The
   wallet is on chain `31611`. No merchant private key enters the stack.
5. The acceptance runner and security review have passed for this exact
   source SHA and image set. The owner explicitly approves the testnet
   transaction and the amount `0.01` test MUSD
   (`10000000000000000` atomic units).

The participant requests a BTC perpetual BUY or SELL quantity, reviews the
snapshot time, limitations, price, expiry, recipient, and testnet label, and
confirms in their wallet. A 402 is an authorization request, not a payment
receipt. Show the paid report only after confirmed receipt, specific MUSD
Transfer evidence, and durable entitlement. A delayed or unknown settlement
goes to [payment recovery](payment-recovery.md); do not ask the participant
to pay again. The evidence ZIP remains protected by the same entitlement and
is independently verifiable offline. Record transaction hash and sanitized
receipt evidence without signatures or wallet secrets.

If any preflight is unavailable, report `BLOCKED_EXTERNAL` or the concrete
failing gate. Do not fabricate a PASS, a transaction, or a hosted URL.
