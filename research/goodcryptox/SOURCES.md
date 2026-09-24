# GOOD mechanics source log

Snapshot checked: **2026-08-10**. Only official goodcryptoX documentation is
used for pinned mechanics. Dynamic market price, liquidity, circulating supply,
and displayed APY are excluded.

## Primary sources

| Source | Pinned facts |
|---|---|
| https://docs.goodcrypto.app/good-token/summary | ticker, Solana chain, official mint, utility index |
| https://docs.goodcrypto.app/good-token/tokenomics | 10,000-GOOD revshare threshold, trading rewards, burn model, fixed maximum supply narrative |
| https://docs.goodcrypto.app/ecosystem/revenue-sharing | built-in-wallet threshold, 24-hour epoch, whole-epoch holding requirement, payout and auto-compound behavior, Ultimate NFT multiplier, detailed shareable-revenue wording |
| https://docs.goodcrypto.app/ecosystem/trading-rewards | weekly delivery, rates, fee-generating-volume rule, app-dashboard precedence |
| https://docs.goodcrypto.app/good-token/holding-benefits | 10,000/50,000/100,000/500,000/1,000,000 GOOD discount tiers |
| https://docs.goodcrypto.app/good-token/how-to-buy-good | official mint, Jupiter routing, external-wallet ineligibility until transfer into built-in wallet |
| https://docs.goodcrypto.app/ecosystem/dex-swap-fee | 1% spot and 0.1% futures base fee, multiplicative discounts, gross-fee revshare/burn summary |
| https://docs.goodcrypto.app/good-token/token-metrics | fixed maximum supply of 1 billion GOOD |

## Precedence policy

1. For live reward rates, the in-app dashboard wins because the official
   trading-rewards page explicitly says rates are subject to change.
2. For eligibility and epoch timing, use the dedicated revenue-sharing page.
3. For holding-discount tiers, use the holding-benefits page.
4. For token identity, require the exact Solana mint; never rely on ticker.
5. For accounting, fail closed when official pages conflict.

## Open documentation conflict

The dedicated revenue-sharing page says holders receive 50% of **shareable
revenue**, with shareable revenue calculated after token-burn and referral
revenue-share deductions. The DEX swap-fee page summarizes the allocation as
50% of collected swap fees for holders and 10% for burn.

The precise gross-to-net accounting base is therefore not stable enough to
encode as realized cash. `mechanics.json` records the conflict and requires
platform epoch evidence or a separately reviewed versioned contract before a
future engine books revenue.

## Review trigger

Create a new dated snapshot when any of these changes:

- the 10,000-GOOD threshold;
- wallet eligibility scope;
- epoch length or full-epoch rule;
- reward rates or eligible-volume definition;
- holding-discount tiers;
- base DEX fees;
- revenue-pool accounting;
- official mint or chain.
