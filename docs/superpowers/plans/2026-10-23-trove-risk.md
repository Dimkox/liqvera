# Mezo Trove risk implementation plan

> **For agentic workers:** Use superpowers:executing-plans; one application implementation owner and independent read-only diff review.

**Goal:** Add a separately identified 0.01 MUSD Trove report to the existing web/x402 product, with fixed-block raw-call evidence and offline replay.

**Architecture:** Public capture reads the sourced Testnet proxies; report services stay offline. Reuse bounded immutable artifact publication and existing payment authorization. Introduce a discriminated request/report product without rewriting historical request or ledger records.

**Tech stack:** Existing Python exact arithmetic/httpx, TypeScript/viem, JSON Schema, current PostgreSQL ledger.

**Spec:** Owner's 2026-10-23 Task 3; canonical `docs/specification.md`; verified implementation ABI/source in `packages/mezo-protocol/vendor`.

## Global constraints

- New chain calls are eth_call at one Testnet block; metadata discovery/header recheck use that same captured block.
- `getEntireDebtAndColl`: collateral, principal, interest, pending collateral, pending principal, pending interest. First three already include pending.
- `fetchPrice()` is view; do not use nonexistent `lastGoodPrice()`.
- Read MCR, CCR and decimal precision. ICR is floor(collateral*price/debt); debt zero maps to uint256 max in the contract and a null display ratio for inactive reports.
- All reported quantities use integers/Fraction and explicit decimal displays, with Solidity overflow rejection.
- Redemption follows `getLast()` then `getPrev()`, checks reciprocal `getNext()` and skips ICR below MCR. Do not call a raw list index a redemption rank.
- A theoretical MCR crossing is not a liquidation guarantee: recovery mode and protocol eligibility matter.
- Wallet authorization, amount, receipt/finality, unknown outcomes and nonce guards are unchanged.
- No borrowing, liquidation, redemption, payment, deployment or registry transaction is authorized by tests.

## Review focus

- Principal/interest/collateral return ordering and no double counting of pending rewards.
- Inactive/zero-debt/zero-collateral positions must not divide by zero or look healthy.
- Incorrect chain/address/price/calldata, duplicate calls, neighbor cycles and nonreciprocal links reject evidence.
- List above 500 cannot imply an unproven rank; display an explicit traversal limit/unknown result, not a fabricated position.
- Legacy quote/report/grant serialization and hash-bound payment recovery remain byte-compatible.

## Steps

- [ ] Pin narrow read-only Trove protocol exports and add exact ABI/provenance tests.
- [ ] Add failing risk arithmetic tests, implement formulas/scenarios and integer ICR agreement.
- [ ] Build a bounded batched capture and offline raw-call decoder. To meet latency at 298 troves, discover active owner addresses from the manager's verified read getters, then fetch neighbors/risk fields in bounded parallel batches. The verifier follows actual links, not owner-array ordering.
- [ ] Record real fixed-block active/inactive observations and measured latency. Batch limits must be observed, not assumed.
- [ ] Add Trove ZIP/report schema and offline reconstruction with exact member allowlists and ABI resources.
- [ ] Extend request parsing, gateway presentation and source service product dispatch without touching settlement logic. Borrower API input must equal viem's EIP-55 canonical result; invalid borrower returns 400.
- [ ] Add browser product tab, wallet-address prefill, clear read-only/not-financial-advice copy and retained report rendering.
- [ ] Add integration/negative tests, independent actual-diff review, docs/handoff and a separate dependent PR. Hosted CI and deployment claims remain separate.
