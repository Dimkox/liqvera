# Mezo Trove risk core

This branch contains read-only capture, offline raw-call verification and exact
risk arithmetic. The paid product, browser tab and Trove evidence ZIP integration
are still in progress. The public site does not expose this feature yet.

The three sourced Testnet proxies and narrow ABIs are exported from
`packages/mezo-protocol`. TroveManager's verified tuple is collateral, principal,
interest, pending collateral, pending principal and pending interest. The first
three values already contain pending rewards; debt is principal plus interest.
`fetchPrice()` is view. MCR, CCR, decimal precision, gas compensation and system
totals are read at the same captured block as each borrower and list node.

The offline decoder checks exact calldata/destinations, one block before/after,
chain identity, raw output lengths, uint256 arithmetic and the contract ICR/TCR.
Owner-array discovery supplies batch targets, while actual `getPrev/getNext`
links prove list ordering, completeness and reciprocity. Redemption rank starts
at `getLast()` and skips ICR below MCR. A paused system or ineligible borrower
has no fabricated rank. Above 500 nodes, the result explicitly marks
`TRAVERSAL_LIMIT` and leaves position/debt-ahead unknown.

Debt ahead includes the complete snapshot debt of eligible predecessors. The
separate redeemable-debt estimate subtracts each captured liquidation reserve.
Neither promises an exact future redemption threshold: eligibility, interest,
protocol state and pending rewards can change.

Risk calculations use exact integers/Fraction. The displayed ICR is the
contract's truncated 18-decimal ratio. `buffer_pct` is a percentage, equal to
100 × (price / theoretical MCR crossing − 1). The crossing holds debt and
collateral constant. Recovery-mode rules and other protocol conditions can
change liquidation eligibility. Price scenarios reduce the captured price by
10%, 20% and 30%; they do not forecast future prices.

Native capture uses at most four concurrent 64-call batches under a shared
12-second deadline. Transient connection/read failures may retry once with the
same payload and block. Exhaustion fails `MEZO_TROVE_SOURCE_UNAVAILABLE`; no
retained data or fixture replaces it. A first live attempt hit ConnectTimeout;
a subsequent successful capture took 4,988 ms at block 16320987, with 1,812
calls and 300 owners. The [native capture](../evidence/mezo-testnet/2026-10-23-trove-active-native.json)
replays offline with exact ICR agreement and proven redemption position 1.

Read-only snapshot analysis; not financial advice. Hashes and raw RPC observations
support internal reproducibility, not independent proof of canonical chain
inclusion or a guarantee of liquidation/redemption timing.
