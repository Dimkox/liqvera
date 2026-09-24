# Payment recovery

`PAYMENT_UNCERTAIN` means a transfer may have been submitted. A timeout,
disconnect, process crash, or facilitator error after submission is never
proof that no charge occurred. Do not issue a second authorization, change
the nonce, resubmit `/settle`, create a replacement quote, or manually grant
an entitlement from a matching amount alone.

1. Stop new payments for the affected quote while preserving the gateway,
   PostgreSQL ledger, logs, and immutable artifacts. Identify the quote,
   payment attempt, canonical authorization identity, report digest, payer,
   receiver, network, asset, amount, and submission time from the ledger.
   Restrict access to this material; redact signatures and bearer capability.
2. If a transaction hash exists, query the approved Mezo Testnet RPC and
   inspect status, canonical block, required confirmations, and the exact
   MUSD Transfer from the quoted payer to the quoted recipient. Verify its
   binding to the retained authorization and quote; identical payer/amount
   near the same time is insufficient.
3. If there is no transaction hash, use only facilitator/chain lookup methods
   that the selected SDK actually supports and that establish the same
   authorization identity. Do not invent a facilitator status endpoint or
   infer failure from a missing response.
4. If finality and binding are proven, use the gateway's reviewed recovery
   path to atomically persist receipt and entitlement for the original
   immutable report digest. Confirm a repeated authorized GET returns that
   same report and receipt without a second settlement.
5. If receipt failed, was reverted, changed canonical chain, or conflicts
   with the ledger, keep the attempt blocked for manual review. Any refund or
   new charge is outside this runbook and needs separate authorization.

Record UTC times, source SHA, attempt ID, public tx hash, block hash/number,
transfer log index, reviewer, and the decision reason in the append-only
incident record. Do not log signatures, capabilities, secret-file contents,
or buyer email. Expiry prevents starting a new payment; it does not cancel a
previously submitted attempt. Never delete artifacts for `SUBMITTING`,
`UNKNOWN`, `PAYMENT_UNCERTAIN`, or `PAID` states.
