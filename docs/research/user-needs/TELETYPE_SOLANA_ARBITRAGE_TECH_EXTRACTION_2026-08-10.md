# Teletype Solana arbitrage: verified technical extraction

Snapshot: **2026-08-10**  
Status: **research and roadmap-candidate analysis; not runtime authority**  

[User-needs index](README.md) · [Research index](../README.md) · [Master research](../MASTER_RESEARCH.md) · [Technical strategy](../TECHNICAL_STRATEGY.md) · [Source ledger](../SOURCE_LEDGER.md) · [Repository README](../../../README.md)

## Purpose

This document extracts potentially useful engineering and product ideas from three articles supplied by the repository owner, then checks those ideas against primary technical sources and the current Multi-Exchange Engine thesis.

The source articles are discovery material. They are not treated as proof of profitability, production safety, user demand or code quality.

## Requested source coverage

| URL | Retrieval status | Use in this review |
|---|---|---|
| https://teletype.in/@mr.ponder/hf7gBp40AkM | Retrieved | Source claims about a Solana arbitrage bot, CPI multi-hop swaps, Raydium/Meteora coverage, RPC and profitability |
| https://teletype.in/@mr.ponder/cQ0fsl975Ny | **Not retrievable during this snapshot** | URL preserved; no factual claim is attributed to it until content is recovered |
| https://teletype.in/@mr.ponder/Pv9VmWXWbOO | Retrieved | Source claims about atomic multi-hop execution, wallet-level profit estimates, infrastructure and transaction landing |

Related posts by the same author were used only as context, not as replacements for the unavailable `cQ0fsl975Ny` article:

- https://teletype.in/@mr.ponder/KZIeytOc5PN — MEV, priority fees, Jito and validators;
- https://teletype.in/@mr.ponder/GhMWoQeDPox — DEX price formation and slippage context;
- https://teletype.in/@mr.ponder/REW_gW0a_P- — copy-trading experience and trust/control claims.

## Executive verdict

The articles contain one technically real and potentially useful idea:

> A Solana route can execute multiple on-chain actions atomically, either as multiple instructions in one transaction, through cross-program invocation from a custom program, or through an atomic Jito bundle.

That idea does **not** solve the core atomicity problem of the current project:

- it cannot make a CEX order atomic with a Solana transaction;
- it cannot make Hyperliquid and Lighter order matching atomic;
- it cannot remove venue-level late fills, partial fills or unknown API states;
- it cannot replace reconciliation for off-chain or independently sequenced venues.

A Solana smart contract is therefore **not a missing core component** of the current Hyperliquid/Lighter/Bybit execution roadmap.

It may become a separate chain-specific executor for an on-chain-only strategy, but that is an isolated research lane. Building it now would be architecture drift unless shadow evidence proves that Solana atomic routes offer better risk-adjusted economics than the current cross-venue hypothesis.

## Source claim → verified reality matrix

### 1. Multiple swaps can execute atomically

**Source claim**

A route can execute two, three or more swaps in one atomic Solana transaction; if one step fails, all state changes roll back.

**Verified reality**

Confirmed. Solana transactions are the atomic unit of execution and can contain multiple instructions. A program can call other programs through CPI. Jito also supports bundles of up to five transactions that execute sequentially and atomically within one slot.

Primary sources:

- https://solana.com/docs/core
- https://solana.com/docs/core/transactions
- https://solana.com/docs/core/cpi
- https://docs.jito.wtf/lowlatencytxnsend/

**Important boundary**

Atomicity applies only to actions governed by the same Solana execution domain. It does not extend to CEX APIs, independent sequencers, Starknet, Arbitrum, Lighter or Hyperliquid.

**Decision:** `VERIFIED`, but `CHAIN-SPECIFIC`.

---

### 2. A custom smart contract is required for multi-hop execution

**Source claim**

The apparent answer to multi-hop arbitrage is a custom smart contract using CPI.

**Verified reality**

Partially true, but overstated.

A custom program is useful when the strategy requires on-chain conditional logic, PDA authority, state assertions, custom accounting or direct CPI into venue programs. It is not universally required to compose multiple instructions. A client can build a transaction from multiple instructions directly, and Jupiter exposes swap instructions and CPI integration paths.

Primary source:

- https://developers.jup.ag/docs/swap/v1/build-swap-transaction

Jupiter currently recommends CPI for many program integrations, but also documents transaction-size and account-limit constraints. Custom code should not duplicate routing already provided by a maintained aggregator without a measured reason.

**Decision:** `PARTIALLY VERIFIED`; custom program is an option, not the default requirement.

---

### 3. A contract can execute practically unlimited instructions

**Source claim**

A custom program can execute practically any number of embedded instructions.

**Verified reality**

False as stated.

Relevant limits include:

- transaction size: 1,232 bytes;
- maximum transaction compute budget: 1.4 million CUs;
- shared compute budget across CPIs;
- CPI stack-depth limits;
- account and instruction-trace limits;
- account-lock contention;
- blockhash expiry;
- address lookup table and CPI composition constraints.

Primary sources:

- https://solana.com/docs/core
- https://solana.com/docs/core/fees/compute-budget
- https://solana.com/docs/core/cpi
- https://solana.com/docs/programs/limitations

**Decision:** `CONTRADICTED`.

---

### 4. A failed atomic route cannot lose money

**Source claim**

If one swap fails, the entire route rolls back, so the trader cannot lose money on a failed route.

**Verified reality**

State changes roll back, but the economic claim is incomplete.

A failed Solana transaction still pays its transaction fee. A competitive route may also incur:

- priority fees;
- Jito tips depending on construction and landing path;
- RPC and infrastructure cost;
- failed-transaction rate cost;
- opportunity cost;
- account-creation or rent effects in successful routes;
- token transfer fees or protocol fees;
- adverse selection when repeated attempts reveal intent or arrive late.

Solana explicitly states that transaction fees are charged even when execution fails. Jito warns that bundle submission does not guarantee landing and that tips and state assertions must be designed carefully.

Primary sources:

- https://solana.com/docs/core/fees
- https://solana.com/docs/core/transactions
- https://docs.jito.wtf/lowlatencytxnsend/

**Decision:** `TECHNICALLY TRUE FOR STATE`, `FALSE FOR TOTAL ECONOMICS`.

---

### 5. First input versus final output equals pure profit

**Source claim**

For a circular route, the difference between the first input and final output is pure profit.

**Verified reality**

Insufficient accounting.

A valid realized-profit model must subtract at least:

```text
realized_net = final_output
             - initial_input
             - base_transaction_fee
             - priority_fee
             - Jito_tip
             - protocol_fees
             - flash_loan_fee
             - token_transfer_fees
             - account/rent_cost
             - infrastructure_cost_allocation
             - failed_attempt_cost_allocation
```

It must also verify that input and output are economically identical assets and decimals, not merely similarly labelled tokens.

Wallet-balance growth is not enough to attribute strategy P&L because balances may change through deposits, withdrawals, unrelated transfers, rebates, rewards or inventory repricing.

**Decision:** `REJECT AS PROFIT EVIDENCE`.

---

### 6. Observed wallets prove stable monthly income

**Source claim**

Sampling several transactions and multiplying average per-transaction gain by observed frequency can imply USD 5,000–43,000 per month; USD 20–50 daily is presented as broadly achievable.

**Verified reality**

Anecdotal and methodologically weak.

The extrapolation does not establish:

- continuous operation at the sampled rate;
- failed-transaction count;
- infrastructure and priority-fee cost;
- capital transfers;
- strategy drawdowns;
- opportunity decay;
- duplicated or unrelated transactions;
- survival after competitors copy the route;
- whether the wallet is the searcher, router, market maker or settlement account.

The articles are useful as hypothesis generators, not return evidence. Their low visible engagement also does not demonstrate buyer demand for a product.

**Decision:** `UNVERIFIED`; do not use in financial projections.

---

### 7. Free RPC and a local machine are enough for production arbitrage

**Source claim**

The bot reportedly began producing positive trades using free RPC infrastructure and a local computer.

**Verified reality**

Possible for experimentation, not sufficient as a production assumption.

Competitive landing depends on region, leader path, RPC quality, simulation latency, account subscriptions, blockhash freshness, priority fee, Jito access, transaction construction and contention. Jupiter explicitly calls landing optimization critical. Jito exposes regional low-latency endpoints and an auction model.

Primary sources:

- https://developers.jup.ag/docs/swap/v1/build-swap-transaction
- https://docs.jito.wtf/lowlatencytxnsend/

**Decision:** `EXPERIMENT-ONLY`; benchmark, do not assume.

---

### 8. Running a validator is the natural next latency step

**Source/context claim**

A related article explores owning or directly using a validator to improve transaction ordering and MEV competitiveness.

**Verified reality**

This is not a rational current roadmap item.

Operating a validator is a separate capital, stake, operations and reliability business. It does not guarantee a profitable searcher strategy. Low-latency relay, regional RPC, direct TPU paths and Jito bundles are lower-cost experiments before validator ownership.

The related article also uses simplified language about a public mempool and validator discretion that should not be copied into architecture requirements without primary-source review.

**Decision:** `REJECT FOR CURRENT ROADMAP`.

## What the project can reuse now

### A. Atomicity must be modelled as a venue capability

Add the concept to architecture, not as a universal promise:

```text
AtomicityScope =
    NONE
    SINGLE_TRANSACTION
    SAME_SLOT_BUNDLE
    RFQ_QUOTE_ACCEPTANCE
    VENUE_NATIVE_BATCH
```

This prevents the engine from treating all multi-leg workflows as equivalent.

For Hyperliquid/Lighter/Bybit, atomicity remains `NONE` across venues. Reconciliation and residual hedging remain mandatory.

**Status:** `PROMOTE TO DOMAIN MODEL WHEN AN ON-CHAIN EXECUTOR IS ADDED`; no immediate runtime requirement.

### B. Simulation evidence should be first-class

A chain transaction candidate should store:

- quote timestamp;
- slot/blockhash;
- instruction/program IDs;
- account list hash;
- simulated units consumed;
- simulated output;
- slippage guard;
- base/priority/tip assumptions;
- simulation error;
- last-valid block height;
- final landing and realized output.

The current evidence-first architecture already points in this direction. Solana material strengthens the requirement for reproducible preflight evidence.

**Status:** `PROMOTE AS GENERAL EVIDENCE PRINCIPLE`.

### C. Failed-attempt cost belongs in strategy P&L

The shadow engine should not model only successful paths. For any venue or chain, track:

- attempted submissions;
- failed submissions;
- paid fees on failure;
- time lost;
- opportunity decay;
- retry count;
- duplicate-prevention state.

This directly supports the current full-cycle economics gate.

**Status:** `PROMOTE`.

### D. Landing quality is a measured distribution

For an on-chain executor, record:

- quote-to-sign latency;
- sign-to-submit latency;
- submit-to-land latency;
- landed slot;
- failure reason;
- priority fee;
- Jito tip;
- region/endpoint;
- bundle auction outcome where available.

Do not encode “paid RPC is faster” as a fact. Measure endpoints under controlled tests.

**Status:** `EXPERIMENT`.

### E. Program provenance and allow-listing

The first article says the author initially used a third-party smart contract. That is a major trust boundary.

Any future Solana executor must require:

- exact program ID;
- source repository and pinned commit where available;
- upgrade authority status;
- verified deployment or reproducible build evidence;
- audit status;
- allowed CPI targets;
- owner/authority review;
- emergency disable switch.

Unknown third-party programs must fail closed.

**Status:** `PROMOTE IF SOLANA EXECUTION IS PROTOTYPED`.

### F. Route replay and wallet analysis are useful research tools

The articles correctly emphasize transaction-level inspection. A useful research component could ingest confirmed transactions and reconstruct:

- input/output asset and amount;
- programs invoked;
- route hops;
- fees and tips;
- account changes;
- failed attempts;
- realized balance delta;
- recurring route families.

This is useful for falsification and competitor/strategy research. It is not proof that copying the route remains profitable.

**Status:** `EXPERIMENT`, preferably read-only.

## What should not enter the current roadmap

- A custom Solana arbitrage smart contract as a core product dependency.
- A custody or shared-user vault.
- Automatic flash-loan strategies.
- Own-validator deployment.
- A Jupiter competitor or general liquidity aggregator.
- Direct Raydium/Meteora program support before a measured routing gap exists.
- Marketing claims based on sampled wallet profits.
- “Atomic cross-exchange arbitrage” wording for CEX/DEX or Hyperliquid/Lighter execution.
- Copy-trading as a product pivot based on one personal anecdote.

## Smart-contract wedge assessment

### Where a smart contract can create real value

- all legs are on Solana;
- all required programs are composable;
- route fits account, size and compute limits;
- state assertions can reject non-profitable execution;
- the strategy benefits from one-transaction or same-slot atomicity;
- the engine can price fees, tips and failure probability;
- program risk is acceptable and auditable.

### Where it cannot help

- one leg is a CEX order;
- one leg is Hyperliquid, Lighter, Extended or another independently sequenced venue;
- funds are held in separate venue margin accounts;
- order acknowledgements and fills arrive asynchronously;
- liquidation and margin engines differ;
- capital must be moved across chains or custodians.

### Product conclusion

A Solana contract is more likely to be an **internal proprietary strategy component** than a defensible user-facing product. Its atomicity can reduce one class of execution risk, but the route logic and contract are reproducible by sophisticated competitors. Durable advantage would come from search quality, landing infrastructure, evidence, capital allocation and execution data—not merely owning a program.

## Proposed isolated experiment

Do not add live execution. Create a research issue only after the current public-data gate is stable.

### Objective

Compare three ways to express the same test route:

1. client-composed multi-instruction transaction;
2. Jupiter-provided route/instructions;
3. minimal custom CPI program or maintained example program.

### Environment

- local validator or devnet first;
- no production keys;
- no borrowed or user funds;
- fixed known pools and test assets;
- deterministic transaction fixture where possible.

### Required evidence

- complete instruction/program list;
- transaction size;
- account count;
- simulated and actual CUs;
- simulated output and slippage guard;
- failure rollback test;
- fee charged on failure;
- blockhash-expiry test;
- duplicate-submit behavior;
- landed-slot and latency measurements;
- exact final token balances.

### Acceptance criteria

- failure leaves no partial token-state mutation;
- all non-state costs are measured and included;
- result is reproducible from stored evidence;
- unknown program IDs or mutable upgrade authority fail policy checks;
- no claim of profitability is made without at least 7–14 days of mainnet read-only route observation and a separate live-arming review.

### Kill criteria

Stop the lane if:

- Jupiter already supplies equivalent routing and execution quality;
- custom CPI does not improve landed net value after fees/tips;
- opportunities disappear before transaction construction;
- required accounts or compute make routes unreliable;
- program/audit risk exceeds the expected edge;
- the lane distracts from the Hyperliquid/Lighter evidence and reconciliation gates.

## Roadmap promotion decisions

| Candidate | Decision | Reason |
|---|---|---|
| Full failed-attempt cost accounting | **PROMOTE** | Applies to all venues and improves falsifiable net economics |
| Simulation and preflight evidence schema | **PROMOTE** | Consistent with current evidence-first architecture |
| Atomicity-scope capability field | **VALIDATE DESIGN** | Useful only when a composable on-chain venue enters scope |
| Jito/RPC landing benchmark | **EXPERIMENT** | Measure before infrastructure commitment |
| Read-only Solana transaction/route reconstruction | **EXPERIMENT** | Useful research tool, not proven product |
| Custom Solana CPI arbitrage program | **RESEARCH-ONLY** | Technically valid but outside current core and PMF unproven |
| Direct Raydium/Meteora router | **RESEARCH-ONLY** | Duplicates mature routing unless a measured gap exists |
| Own validator | **REJECT** | Capital/operations distraction without validated advantage |
| Smart contract for CEX↔DEX atomicity | **REJECT** | Cannot make an off-chain CEX leg atomic |
| Wallet-profit extrapolation | **REJECT** | Incomplete attribution and survivorship bias |

## User-need impact

The Teletype material adds technical option value, but weak user-demand evidence.

It supports an operator job:

> “When I execute multiple composable on-chain legs, either all state transitions should settle under explicit guards or none should.”

It does not independently prove that users will pay for:

- a Solana arbitrage smart contract;
- a Telegram interface;
- a general arbitrage bot;
- copy-trading;
- a liquidity aggregator.

Before promotion into a customer roadmap, the project still needs interviews or usage evidence showing that a target buyer experiences a material loss from non-atomic on-chain workflows and cannot solve it through Jupiter, Jito or existing bots.

## Source-quality assessment

| Source category | Confidence | Use |
|---|---:|---|
| Official Solana/Jupiter/Jito documentation | High | Protocol capabilities, limits, fees and submission behavior |
| Retrieved Teletype articles | Low-to-medium | Practitioner hypotheses and architecture discovery |
| Wallet examples and profit arithmetic in articles | Low | Leads for independent chain analysis only |
| Related author posts | Low-to-medium | Context; not independent corroboration |
| Unretrieved `cQ0fsl975Ny` page | None | URL only until recovered |

## Primary verification sources

- Solana core concepts: https://solana.com/docs/core
- Solana transactions: https://solana.com/docs/core/transactions
- Solana fees: https://solana.com/docs/core/fees
- Solana compute budget: https://solana.com/docs/core/fees/compute-budget
- Solana CPI: https://solana.com/docs/core/cpi
- Solana program limitations: https://solana.com/docs/programs/limitations
- Jupiter transaction composition and CPI: https://developers.jup.ag/docs/swap/v1/build-swap-transaction
- Jito low-latency send and atomic bundles: https://docs.jito.wtf/lowlatencytxnsend/

## Repository truth boundary

This document does not authorize a Solana smart contract, live transaction submission, flash loans, Jito tips, custody, user funds or a roadmap pivot. Any implementation requires an accepted ADR, an explicit roadmap gate, code review, tests and the security boundary in [`SECURITY.md`](../../../SECURITY.md).
