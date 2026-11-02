# LiqveraGuard: automatic Trove protection (design A2)

Status: deployed on Mezo Testnet only (chain 31611). It is not audited. Do not use it on mainnet.

## Deployment (Mezo Testnet)

| Item | Value |
|---|---|
| Contract | [`0x61e12BDDFa62adF0Ffa89544153954a2420cF37a`](https://explorer.test.mezo.org/address/0x61e12BDDFa62adF0Ffa89544153954a2420cF37a) (source verified in Blockscout) |
| Deploy transaction | [`0x8fb90b1f369dae3041892f378c2b153533bfdd499a04ce439710ac569cf81175`](https://explorer.test.mezo.org/tx/0x8fb90b1f369dae3041892f378c2b153533bfdd499a04ce439710ac569cf81175) |
| Block | 16524690 (2026-11-02 10:22:57 UTC) |
| Deployer | `0xF63F28B90f7075a640BC0911467Fa3FDbc436bf6` (Liqvera test wallet) |
| Source | commit `020ec53`, solc 0.8.24, optimizer 200 runs, evmVersion london |
| Constructor | signatures `0xD757e3646AF370b15f32EB557F0F8380Df7D639e`, borrowerOperations `0xCdF7028ceAB81fA0C6971208e83fa7872994beE5`, troveManager `0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0`, priceFeed `0x86bCF0841622a5dAC14A313a15f96A95421b9366`, MUSD `0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503` |

The on-chain runtime code matches the compiled `deployedBytecode` of `script/Deploy.s.sol` byte for byte, except the immutable slots.
The keeper is not running yet. No `protect()` call has been executed yet.
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

7. Serves only Troves with an active **Guard Watch** subscription (see section 6b). Ready Troves without a subscription are logged as `skip_unsubscribed`. `protect()` stays permissionless, so anyone, including the borrower, can still execute them.

### Running the keeper on Mezo Testnet

```sh
cd services/guard-keeper && npm ci && npm run build
DRY_RUN=1 MEZO_RPC_URL=https://rpc.test.mezo.org \
GUARD_WATCH_FREE_TRIAL=1 GUARD_WATCH_PAY_TO=0xd7f52d1ddb5dc8678191f14e439fc5db67541535 \
GUARD_WATCH_CORS_ORIGIN=http://localhost:5173 npm start
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `CHAIN_ID` | `31611` | Anything else is rejected. The RPC chain id is checked at startup. |
| `GUARD_ADDRESS` / `GUARD_DEPLOY_BLOCK` | `0x61e12BDD…F37a` / `16524690` | The deployed Guard. |
| `DRY_RUN` | `1` | `0` sends `protect()` transactions and requires `KEEPER_PRIVATE_KEY`, a separate wallet funded with testnet BTC for gas. |
| `POLL_INTERVAL_MS` | `30000` | |
| `GUARD_WATCH_ENFORCE` | `1` | `0` serves every Ready Trove. |
| `GUARD_WATCH_FREE_TRIAL` / `GUARD_WATCH_TRIAL_DAYS` | `0` / `30` | Testnet free trial, counted from the borrower's first `Armed` event. |
| `GUARD_WATCH_PAY_TO` | none | Merchant address for subscriptions. Without it, the checkout is disabled. |
| `GUARD_WATCH_HTTP_HOST` / `GUARD_WATCH_HTTP_PORT` | `127.0.0.1` / `8795` | Guard Watch API. |
| `GUARD_WATCH_CORS_ORIGIN` | none | One origin, or a comma-separated allowlist. |
| `GUARD_WATCH_FACILITATOR_URL` | `https://facilitator.vativ.io/` | x402 facilitator. |

In dry-run mode the keeper logs `dry_run_ready` with the hints it would use. To submit, it needs a funded `KEEPER_PRIVATE_KEY`, and that wallet does not exist yet.

## 6b. Guard Watch subscription (proposal)

**Status: proposal pricing, testnet only.** Guard Watch is the paid keeper service on top of the permissionless Guard contract.

- **Price:** 2 MUSD per Trove per 30 days. Payments stack: each full 2 MUSD transfer adds 30 days. Transfers below 2 MUSD, such as 0.01 MUSD report payments, buy nothing.
- **Payment:** the same x402 flow as Liqvera reports: the `exact` scheme on `eip155:31611`, MUSD, Permit2 with EIP-2612 gas sponsorship, and the facilitator settles. The payer must be the borrower.
  - `GET /v1/guard-watch/troves/<borrower>/subscribe` returns `402` with `PAYMENT-REQUIRED`.
  - Retrying with `PAYMENT-SIGNATURE` verifies and settles. The response carries `x-liqvera-payment-tx`.
- **Entitlement:** the keeper never trusts its own HTTP records. It derives subscriptions from on-chain MUSD `Transfer(borrower → payTo)` logs, so a restart or a second keeper reaches the same answer.
- **Free trial (testnet):** `GUARD_WATCH_FREE_TRIAL=1` grants `GUARD_WATCH_TRIAL_DAYS` from the first `Armed` event.
- **Read endpoints:** `GET /healthz`, `GET /v1/guard-watch/plan`, and `GET /v1/guard-watch/troves/<borrower>`.

## 6c. Guard panel (web app)

`apps/mezo-web` has a **LiqveraGuard** panel (`src/guard-panel.ts`, `src/guard.ts`, `src/guard-watch.ts`):

1. It shows the connected wallet's Trove (collateral, debt, ICR, MCR, price), its Guard status, policy, escrow and Mezo signature nonce.
2. **Inputs:** asset (BTC collateral or MUSD repay), trigger ICR, target ICR, keeper reward and validity (≤ 30 days).
   - The top-up is sized with the existing `computeRescue` at the price where ICR equals the trigger, so firing the protection lifts the ICR to the target.
3. **Deposit escrow:** `depositBTC`, or `approve` + `depositMUSD`. Only the shortfall over free escrow is deposited.
4. **Sign authorization:** EIP-712 `AddColl` / `RepayMUSD` for `BorrowerOperationsSignatures` (chain 31611).
   - The signature is checked locally the same way the Guard checks it: 65 bytes, v 27/28, low s, signer = borrower.
   - The local digest equals the deployed contract's `digest()`, checked against the live testnet contract on 2026-11-02.
5. **Arm:** re-checks the Mezo nonce and the deadline, then calls `arm`.
6. **Execute protect() now:** offered only when `status()` is `Ready`. It uses fresh hints.
7. Other actions: **Disarm**, **Withdraw free escrow**, and the **Guard Watch** status with an x402 **Subscribe** button.
8. **Safety checks:** every transaction is simulated with `eth_call` before the wallet prompt, and the wallet must be on chain 31611.

Build-time setting: `LIQVERA_GUARD_WATCH_API=http://127.0.0.1:8795`. Without it, the panel says the keeper API is not configured, and `protect()` stays available.

### Running the panel locally against the testnet gateway

The report and sale flow call the frozen `/v1` gateway API through the Vite proxy. That proxy defaults to a local gateway on `127.0.0.1:8080`, and when nothing is listening there `/v1/capabilities` returns HTTP 500 and "Request a report" stays disabled. To use the deployed Mezo Testnet gateway and the local keeper together:

```sh
cd apps/mezo-web
LIQVERA_GUARD_WATCH_API=http://127.0.0.1:8795 npm run build
LIQVERA_API_PROXY=https://liqvera.site LIQVERA_GUARD_WATCH_API=http://127.0.0.1:8795 npx vite preview --host 127.0.0.1 --port 4173
```

The proxy removes `Origin`/`Referer` because the gateway rejects origins that are not on its allowlist. The browser itself stays same-origin. Guard Watch payments go from the browser to the keeper API, which verifies and settles them through the public facilitator `https://facilitator.vativ.io/` (no API key). A rejection returns the facilitator's reason, for example `permit2_insufficient_balance`.

## 6d. Team test wallets (disclosure)

All testnet activity for the Guard demo comes from **team-owned test wallets**: derived accounts in one MetaMask controlled by the founder. They are **not users**.

| Wallet | Address | Demo scenario |
| --- | --- | --- |
| Liqvera test wallet (Account 1) | `0xF63F28B90f7075a640BC0911467Fa3FDbc436bf6` | Guard deploy, protection on its own Trove, funder of the others |
| Liqvera Test 2 | `0x08F27Cd554F3CF57AD1317A4fc9b0fCaA9B176fe` | Protection on a second Trove |
| Liqvera Test 3 | `0xFe4481d57670991e52141f6Be026B342Ef28E169` | Sale: paid report + BTC→MUSD DEX sale |
| Liqvera Test 4 | `0x06A252C33e07Ce05a03CfAE9333d02F1D1f57605` | Guard Watch subscription (2 MUSD via x402) |

Transactions from these addresses are demos and must never be reported as user adoption.

## 7. Tests

```sh
cd contracts/guard
forge test                                              # unit, fuzz, invariant
MEZO_TESTNET_RPC=https://rpc.test.mezo.org forge test   # plus fork tests
cd ../../services/guard-keeper && npm ci && npm test
cd ../../apps/mezo-web && npm ci && npm test && npm run build
```

## 8. Before a testnet deployment

1. Get the owner's approval for the deployment.
2. Run Slither. Fix the findings.
3. Done (2026-11-02): deployed and verified in Blockscout. See "Deployment" above.
4. Create and fund a separate keeper wallet (still open: the keeper runs in dry-run mode).
5. Done: Guard panel in the frontend (deposit, signature, arm, protect, disarm, withdraw, status, Guard Watch).
6. Execute at least 3 real `protect()` calls on testnet and record them in the transaction ledger.
