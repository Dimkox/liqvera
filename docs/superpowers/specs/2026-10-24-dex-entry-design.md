# Market depth DEX entry and payment reconciliation design

## Intent

Let a user deliberately request the existing Mezo DEX comparison from the Market depth form, then expose the existing fresh-quote, wallet-signed BTC sale planner without requiring a paid report first. Keep Hyperliquid-only reports as the default and preserve all report hashes and payment guards.

## Scope and constraints

- A Mezo DEX request is available only on Mezo Testnet when both the gateway and report service are explicitly configured for DEX evidence.
- The request choice is included in the canonical quote body and the resulting report is checked for matching DEX evidence.
- The planner reads fresh Router/pool state, caps estimated impact at editable 1% per part and defaults editable minOut tolerance to 1%; each approval/swap needs a separate wallet signature.
- No transaction is signed or submitted by tests, and no keys are handled by Liqvera.
- Payment recovery remains confirm-only. A quote ID has now been supplied for the reported attempt, but production ledger access is unavailable in this source workspace; do not manually change its state.

## Approaches considered

1. Leave the report service's global DEX flag to silently add DEX to every Market depth quote. This does not give users an explicit choice and obscures disabled runtime configuration.
2. Add an opt-in DEX boolean to the closed request, expose it through capabilities, and separately surface the sale planner in the Market depth workspace. This keeps legacy requests unchanged, makes feature availability explicit, and reuses existing safe execution code. **Chosen.**
3. Create a separate website/product flow for DEX. Rejected because Liqvera must remain one web/API product and current report/evidence services already support additive DEX evidence.

## Payment incident

Public chain evidence establishes a successful transfer, not its binding to a specific authorization. Inspect the existing attempt using the supplied quote ID through the approved, redacted reconciliation workflow before changing gateway behavior or state. Never settle again or issue another payment. The previously shown MSK expiry label is incorrect per the user and is not evidence that the transaction missed the quote window.

## Implementation calls

The DEX boolean is opt-in and only literal `true` is accepted; absent means the current Hyperliquid-only behavior. A feature capability controls whether the checkbox is shown. The planner is an independent workspace panel because its quotes are fresh and it must not depend on the age or contents of a paid report.
