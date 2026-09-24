# Teletype Solana arbitrage source log

Snapshot: **2026-08-10**  
Status: **research provenance; no runtime authority**

[User-needs index](README.md) · [Verified extraction](TELETYPE_SOLANA_ARBITRAGE_TECH_EXTRACTION_2026-08-10.md) · [Global source ledger](../SOURCE_LEDGER.md) · [Repository README](../../../README.md)

## Supplied Teletype URLs

| URL | Status on snapshot | Evidence class | Notes |
|---|---|---|---|
| https://teletype.in/@mr.ponder/hf7gBp40AkM | Retrieved | Tier D / practitioner discovery | Personal account of building a Solana arbitrage bot, CPI routing, third-party program use, planned Raydium/Meteora integrations and anecdotal profitability |
| https://teletype.in/@mr.ponder/cQ0fsl975Ny | Not retrievable | None | Preserved as an unresolved source. No title, claim or conclusion is inferred from the URL |
| https://teletype.in/@mr.ponder/Pv9VmWXWbOO | Retrieved | Tier D / practitioner discovery | Wallet examples, atomic-route explanation, transaction-frequency extrapolation and infrastructure recommendations |

## Related author material used only as context

| URL | Topic | Evidence class |
|---|---|---:|
| https://teletype.in/@mr.ponder/KZIeytOc5PN | MEV, priority fee, Jito, validator economics | Tier D |
| https://teletype.in/@mr.ponder/GhMWoQeDPox | DEX pricing, pools and slippage | Tier D |
| https://teletype.in/@mr.ponder/REW_gW0a_P- | CEX/DEX copy-trading experience | Tier D |

These posts are not independent corroboration because they share the same author.

## Primary technical sources

### Solana execution model

| Source | Tier | Verified claims |
|---|---:|---|
| https://solana.com/docs/core | A | Multiple instructions per transaction, transaction atomicity, 1,232-byte transaction limit, 1.4M CU maximum and CPI concept |
| https://solana.com/docs/core/transactions | A | All instructions succeed or state changes roll back; fees are charged even when a transaction fails; blockhash and transaction-size constraints |
| https://solana.com/docs/core/cpi | A | CPI privilege propagation, shared compute budget and call-depth constraints |
| https://solana.com/docs/core/fees | A | Base and prioritization fee model |
| https://solana.com/docs/core/fees/compute-budget | A | Compute-unit limits, simulation guidance and priority-fee dependence on requested CU limit |
| https://solana.com/docs/programs/limitations | A | Program and CPI execution constraints |

### Routing and composition

| Source | Tier | Verified claims |
|---|---:|---|
| https://developers.jup.ag/docs/swap/v1/build-swap-transaction | A | Client-composed swap instructions, Jupiter CPI path, transaction/account limits, simulation and landing-optimization parameters |
| https://github.com/jup-ag/jupiter-cpi-swap-example | A pending repository pin | Maintained example candidate for CPI integration review |
| https://github.com/jup-ag/sol-swap-cpi | A pending repository pin | Jupiter-linked CPI example candidate |
| https://github.com/jup-ag/sol-swap-flash-fill | A pending repository pin | Flash-fill example candidate; not approved as a dependency |

### Transaction landing and atomic bundles

| Source | Tier | Verified claims |
|---|---:|---|
| https://docs.jito.wtf/lowlatencytxnsend/ | A | Regional low-latency submission, MEV/revert protection, up-to-five-transaction atomic bundles, auction/tip model and non-guaranteed landing |

## Claim status register

| Claim from supplied material | Status | Reason |
|---|---|---|
| Multiple on-chain swaps can be atomic | Confirmed | Solana transaction/CPI and Jito bundle documentation |
| A custom contract is always required | Partially contradicted | Multiple client instructions and aggregator-built transactions can compose without a custom program |
| A contract can execute practically unlimited instructions | Contradicted | Size, compute, account, trace and CPI-depth limits |
| Failed route cannot cost money | Contradicted economically | State rolls back, but fees and other attempt costs remain |
| First input minus final output is pure profit | Contradicted | Omits fees, tips, failed attempts, rent/account effects and attribution problems |
| Sampled wallet transactions prove monthly income | Unverified | Survivorship, transfer attribution, uptime and cost gaps |
| Free RPC/local machine is enough for production | Unverified | Must be benchmarked against landing rate and net value |
| Own validator is required for competitiveness | Rejected for current scope | Lower-cost RPC/relay/Jito experiments exist; validator operation is a separate business |
| Smart contract can make CEX↔DEX execution atomic | False | A Solana program cannot control an off-chain CEX matcher or independently sequenced venue |

## Repository policy

1. Tier D material can create a research question, not a roadmap requirement.
2. Profit claims require independent transaction reconstruction and complete cost accounting.
3. Unknown or third-party program IDs fail closed.
4. A Solana execution experiment requires its own ADR and security review.
5. No source in this log authorizes live funds, flash loans, custody, Jito tips or a custom deployed program.
6. The unavailable `cQ0fsl975Ny` source remains unresolved rather than silently reconstructed from related posts.
