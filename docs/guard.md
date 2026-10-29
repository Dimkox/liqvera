# LiqveraGuard: automatic Trove protection (design A2)

Status: Mezo Testnet only (chain 31611). The contract is not deployed. It is not audited.
This document follows the ASD-STE100 style: short sentences, one action per step.

## 1. Purpose

LiqveraGuard protects a Trove from liquidation. The user signs one Mezo operation in advance.
When the ICR falls to the trigger, a keeper calls `protect()`. The Guard executes the signed operation.

The model comes from DeFi Saver Liquity Repay and Summer.fi Stop-Loss: a ratio trigger, executed by a bot.
The `checker()` function follows the Gelato/Chainlink interface. The code is written from scratch. No code was copied from these projects.

## 2. How it works

1. The user deposits MUSD (`depositMUSD`) or BTC (`depositBTC`) into the Guard escrow.
2. The user signs a Mezo `RepayMUSD` or `AddColl` EIP-712 message.
   - Domain: `BorrowerOperationsSignatures`, version `1`, chainId 31611, contract `0xD757e3646AF370b15f32EB557F0F8380Df7D639e`.
   - The signature binds `amount`, `borrower`, `nonce` and `deadline`.
3. The user calls `arm(action, triggerICR, amount, keeperReward, deadline, signature)`.
   - The Guard verifies the signature on-chain against `getNonce(msg.sender)`.
   - The Guard checks: the trigger is in the range (MCR, 1000%], the signature deadline is at most 30 days away, the Trove is active, the escrow is sufficient, and for a repay the Trove keeps `minNetDebt`.
4. The keeper polls `checker(borrower)` every 30 seconds.
5. When `canExec == true`, the keeper calls `protect(borrower, upperHint, lowerHint)`.
6. The Guard deletes the policy, debits the escrow, calls Mezo, checks that the ICR went up, and pays the keeper reward.

One signature gives one execution. After `protect()`, the user must call `arm()` again.

### Collateral and debt values

The Guard reads the Trove with Mezo `TroveManager.getEntireDebtAndColl()`. Its first three return values
(`coll`, `principal`, `interest`) already include the pending redistribution rewards
(`pendingCollateral`, `pendingPrincipal`, `pendingInterest`). The vendored source
`packages/mezo-protocol/vendor/explorer/TroveManagerImplementation.source.testnet.json` adds them before it returns.
The Guard therefore uses `coll` and `principal + interest` directly. It does not add the last three values again.
Tests: `test_PendingRewards_NotCountedTwice_*` in `contracts/guard/test/LiqveraGuard.t.sol`.

## 3. Answers to open questions Q1–Q5

All answers are checked by the fork test `contracts/guard/test/fork/GuardFork.t.sol` against the RPC `https://rpc.test.mezo.org`.

| Question | Answer | Test |
|---|---|---|
| Q1. How to read the nonce? | The `nonces` mapping is private. `nonces(address)` reverts. Use `getNonce(address)`. The nonce is sequential and starts at 0. | `test_Q1_NonceGetter` |
| Q2. Is an MUSD approve needed? | No. BorrowerOperations burns MUSD from `_caller` (the Guard) directly. The allowance stays 0. | `test_Q2_RepayPath_NoApproveNeeded` |
| Q3. Which code is deployed? | The proxy `0xD757…` is a TransparentUpgradeableProxy. The implementation `0xEec635aB00463A4a803DE38C9d858A0FE3bdc235` is verified in Blockscout. The source matches `BorrowerOperationsSignatures.sol` at commit `da7888a`. `BorrowerOperations.borrowerOperationsSignaturesAddress()` returns this proxy. Implementation codehash: `0x9714ca105dccb830037cd8821974832a5e2a1e7822b2369654849617c6e73900`. | `test_Q3_DeployedImplementationAndDomain` |
| Q4. Is Gelato or Chainlink Automation available on Mezo? | No. Gelato Web3 Functions shut down on 2026-03-31 and did not support Mezo. Chainlink Automation does not support Mezo. A custom keeper is required. | — |
| Q5. Field order of `getEntireDebtAndColl`? | `(coll, principal, interest, pendingCollateral, pendingPrincipal, pendingInterest)`. The first three values already include the pending values (see section 2). | `test_Q5_GetEntireDebtAndCollOrder` |

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Stale nonce. Any other signed operation of the user increments the nonce. | `checker()` returns `StaleNonce`. `protect()` does not execute. The user must call `arm()` again. The escrow does not change. Test `test_FrontRun_StaleNonce`. |
| Signature front-running. The signature is visible in the `arm()` calldata. | Mezo verifies a signature that does not depend on `msg.sender`, but it takes the MUSD/BTC from the caller. A foreign call only repays the user's debt at the caller's own cost and makes the nonce stale. The escrow funds are not lost. |
| `minNetDebt` = 1800 MUSD. | `arm()` and `checker()` check: `(debt − 200 gas compensation) − amount ≥ 1800`. Otherwise the status is `BelowMinNetDebt`. Test `test_MinNetDebt_Enforced`. |
| Pending redistribution rewards. | `getEntireDebtAndColl()` already includes them. The Guard does not count them twice, so the `minNetDebt` check and the projected ICR match Mezo. Tests `test_PendingRewards_NotCountedTwice_*`. |
| Recovery Mode. | In Recovery Mode, Mezo forbids only collateral withdrawal and debt increase. Repay and addColl are allowed. Mezo liquidates only below MCR in both modes. Test `test_RecoveryMode_RepayStillWorks`. |
| MCR 110%. | The trigger must be above MCR. `checker()` returns `StillBelowMCR` if the ICR after the operation stays below MCR (Mezo reverts such a repay in Normal Mode). |
| EOA only. | The signature is verified with `ecrecover`. Smart wallets (EIP-1271) are not supported. |
| The Mezo proxy is upgradeable. | Mezo can change the implementation. Check the implementation codehash before deployment and periodically (see Q3). |
| Oracle in fork tests. | The PriceFeed reads the precompile `0x7b7c…0015`. A local fork cannot execute it. The fork test reads the price from the node with `eth_call` and pins it with `vm.mockCall`. |
| No audit. | Testnet only. An audit and Slither are required before mainnet. |

## 5. Deviation from the plan

The plan assumed one reward currency. The implementation pays the keeper reward in the currency of the operation: MUSD for `RepayMUSD`, BTC for `AddColl`. Reason: the user escrow for a policy can hold only one asset.

## 6. Keeper

Code: `services/guard-keeper`.

1. Reads the `Armed`, `Disarmed` and `Protected` events incrementally and builds the set of active policies.
2. Every 30 seconds, calls `status(borrower)` for each active policy that is not terminal.
3. Marks a policy as terminal when the status is `Expired`, `StaleNonce` or `NoPolicy`. The keeper stops polling it until a newer `Armed` event for that borrower arrives. This keeps expired or nonce-invalidated policies from delaying time-sensitive rescues.
4. For the `Ready` status, computes hints: `HintHelpers.getApproxHint` and `SortedTroves.findInsertPosition` from the NICR after the operation (`coll·1e20/principal`).
5. Simulates `protect()`. Sends the transaction only after a successful simulation.
6. Writes one JSON line per event.

The keeper stores only its own key (`KEEPER_PRIVATE_KEY` from env). The keeper does not store user keys. `DRY_RUN=1` mode sends no transactions.

## 7. Tests

```sh
cd contracts/guard
forge test                                              # unit, fuzz, invariant
MEZO_TESTNET_RPC=https://rpc.test.mezo.org forge test   # plus fork tests
cd ../../services/guard-keeper && npm ci && npm test
```

## 8. Before a testnet deployment

1. Get the owner's approval for the deployment.
2. Run Slither. Fix the findings.
3. Run `script/Deploy.s.sol` with `--broadcast --verify`. Verify the contract in Blockscout.
4. Create and fund a separate keeper wallet.
5. Add a Guard panel to the frontend (deposit, signature, arm, disarm, status).
6. Execute at least 3 real `protect()` calls on testnet and record them in the transaction ledger.
