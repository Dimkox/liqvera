# goodcryptoX / GOOD token mechanics

Snapshot: **2026-08-10**. This package records the GOOD token mechanics that
matter to Multi-Exchange Engine economics. It is research-only: it adds no
wallet, signer, purchase, swap, account, order, or live-execution capability.

## Binding revenue-share unlock

Revenue share is **not unlocked merely by trading through goodcryptoX**.
Eligibility requires all of the following:

1. at least **10,000 GOOD**;
2. held in the **built-in goodcryptoX Solana wallet**;
3. maintained for the **entire 24-hour revenue-share epoch**.

GOOD kept in Phantom, Solflare, Backpack, or another external wallet does not
count until it is transferred to the built-in goodcryptoX wallet. The official
documentation describes holding, not staking: there is no separate staking or
lock transaction in the published eligibility flow.

If the balance first reaches 10,000 GOOD during an epoch, that partial epoch is
not eligible. The first payout can occur only after the next complete eligible
epoch ends.

Implementation-oriented gate:

```text
eligible(epoch) =
    wallet_scope == GOODCRYPTOX_BUILT_IN_SOLANA_WALLET
    and balance_was_at_least_10_000_good_for_the_whole_epoch
```

Fail closed when wallet scope, continuous balance evidence, or epoch boundaries
are unavailable.

## Revenue-share calculation

The detailed revenue-sharing page states:

```text
shareable revenue = total swap fees collected
                  - token-burn allocation
                  - referral revenue-share allocation

holder pool = 50% of shareable revenue
```

Eligible wallets divide the holder pool in proportion to eligible GOOD. An
Ultimate NFT applies a `1.5x` multiplier to the wallet's GOOD balance for this
calculation.

Derived allocation model:

```text
weighted_good(wallet) = eligible_good(wallet) * nft_multiplier(wallet)

wallet_payout = holder_pool
              * weighted_good(wallet)
              / sum(weighted_good(all eligible wallets))
```

The official pages are not fully consistent about the pool base:

- the revenue-sharing page defines a narrower `shareable revenue` after burn
  and referral deductions;
- the DEX swap-fee page summarizes revenue sharing as 50% of collected swap
  fees and separately assigns 10% to burn.

Therefore the engine must **not hard-code “50% of gross DEX fees” as settled
cash accounting**. For any later integration, platform-reported epoch values or
a reviewed versioned contract must be authoritative. Forecast revshare remains
zero until actually paid or supported by immutable platform evidence.

Payouts go to the built-in goodcryptoX Solana wallet. Auto-reinvestment into
GOOD is enabled by default and can be disabled in the dashboard.

## How 10,000 GOOD can be obtained

### Purchase or transfer

GOOD can be bought inside goodcryptoX through its Solana swap flow, which uses
Jupiter routing. It can also be bought through Jupiter or Raydium outside the
app, but external holdings must then be transferred to the built-in
goodcryptoX wallet before they qualify for revenue share or holding discounts.

Official Solana mint:

```text
goodX4LG92UAcRdFRUykfP2fAfzQAVttrToEPxtxSkp
```

Never identify the token by ticker alone.

### Trading rewards

GOOD trading rewards are delivered weekly. Only fee-generating volume is
eligible; zero-fee trades and trades whose fees are rebated do not qualify.
The app dashboard overrides documentation when rates differ.

| Trading activity | Published reward | Eligible volume required for 10,000 GOOD |
|---|---:|---:|
| DEX spot | 1 GOOD per $100 | $1,000,000 |
| DEX spot in GOOD | 2 GOOD total per $100 | $500,000 |
| DEX futures | 1 GOOD per $1,000 | $10,000,000 |
| CEX spot | 1 GOOD per $1,000 | $10,000,000 |
| CEX futures | 1 GOOD per $10,000 | $100,000,000 |

Example: `$10,000` of eligible DEX-futures volume earns approximately `10
GOOD` at the published rate. That is `0.1%` of the 10,000-GOOD unlock threshold.

## GOOD holding discounts

| GOOD held in built-in wallet | DEX swap-fee discount |
|---:|---:|
| 10,000 | 10% |
| 50,000 | 20% |
| 100,000 | 30% |
| 500,000 | 40% |
| 1,000,000 | 50% |

Published base goodcryptoX DEX fees are `1%` for spot and `0.1%` for futures.
Volume, GOOD, subscription, NFT, and referral discounts multiply rather than
add.

Example with three discounts:

```text
effective_fee = base_fee
              * (1 - volume_discount)
              * (1 - good_discount)
              * (1 - subscription_discount)
```

## Multi-Exchange Engine accounting boundary

GOOD is a platform-economics input, not venue collateral and not a trading
signal. A future profitability model must keep these ledgers separate:

- venue trading fees and builder fees;
- GOOD holding discount on goodcryptoX's own DEX fee;
- GOOD trading-reward accrual;
- paid GOOD revshare;
- GOOD acquisition cost, price risk, liquidity, and opportunity cost.

Default rules for the engine:

- no verified built-in-wallet balance evidence -> no GOOD discount or revshare;
- less than 10,000 GOOD at any point in the epoch -> zero revshare for that
  epoch;
- external-wallet GOOD -> zero platform benefit;
- projected but unpaid revshare -> zero realized operator revenue;
- token price and APY are dynamic and are intentionally absent from the pinned
  mechanics file;
- changes to official rates require a new dated snapshot and review.

Machine-readable constants are in [`mechanics.json`](mechanics.json). Source
provenance and the documentation conflict are recorded in
[`SOURCES.md`](SOURCES.md).
