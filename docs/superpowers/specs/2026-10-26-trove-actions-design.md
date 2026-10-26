# Trove report wallet actions

Approved scope: complete the existing borrower-only protection panel. Add deposit,
repayment, guarded borrowing, target-ICR rescue, exact live previews, explicit
second-click signing, receipt tracking and browser action evidence. Keep one web/API
product. Preserve x402, sealed report bytes, historical evidence and execution
boundary NONE. All UI and documentation are English.

## Decisions and BMAD review amendments

Extend the existing ethers/EIP-1193 implementation. Borrowing ships in a collapsed
section. Server action storage, withdrawColl and adjustTrove are out of scope.
A new contract and a separate application would duplicate the established protocol
and report integration; neither is needed.

All amounts and ratios in state and evidence are integer strings scaled by 1e18.
Use bigint throughout. Required rescue amounts round upward, then receive a 0.5%
upward-rounded buffer. Max amounts round downward. Validate targets against MCR +
0.05. Already-satisfied targets return zero. Repayment recommendations compare the
buffered amount to the live wallet/protocol limit.

Read all protocol parameters, system collateral/debt, per-Trove borrowing capacity,
fee exemption through the verified governance interface, price, balances, and hints at
one block. Validate price/debt and decoded values. Add only ABI fragments matching
retained verified implementation artifacts, including borrowingRate,
getBorrowingFee, withdrawMUSD and system-total reads. Do not rewrite artifacts.
Borrowing requires remaining per-Trove capacity, normal mode, after ICR >= max(1.8, CCR + 0.1), and after system
TCR >= CCR, using exact getBorrowingFee. Limits include both ICR and TCR bounds.

Reserve gas for every action. Estimate the exact deposit-Max candidate with a
bounded conservative fee/gas calculation; default reserve is 0.0001 BTC if fee
estimation is unavailable. Revalidate the exact candidate before signing. Gas and
fee caps used for the reserve travel in the submitted transaction when available.

Each debounced preview has a revision and wallet context. Input/context changes
invalidate confirmations. First submit prepares and shows an immutable summary.
Second click refreshes preparation; changed transaction terms or displayed preview require
another review click. Review precision is explicit: debt rounds upward to 0.001
MUSD, ICR downward to 0.00001, liquidation price upward to 0.01 MUSD. Sub-display
interest accrual does not force another click; every exact safety bound is still
rechecked. Exact atomic state stays in receipts. No signing occurs on preview, Max or rescue-fill clicks.

Persist an unresolved intent before opening the wallet, then the hash immediately
on return. One unresolved action per chain/borrower, including across reports,
reloads and tabs. Use a browser exclusive lock for atomic submission. Timeouts,
RPC errors and malformed receipts retain the lock and expose receipt-only recovery.
Unknown submission without hash requires manual reconciliation, never auto retry.
Poll only Mezo Testnet. Validate receipt hash/status/block. Success means first
canonical inclusion, not payment finality. Refresh state at or after receipt block;
refresh failure must not turn a successful transaction into a failed one.

Action receipts bind the verified delivery report SHA-256 passed from main.ts.
Before/after are explicitly prepared predictions. Observed post-confirmation state
is recorded separately with its block when available. Persist pending/reverted as
well as confirmed outcomes. Validate loaded records, handle corrupt/unavailable
storage, retain in-memory exports and show storage failures. If unresolved-intent
storage is unavailable, disable new signing rather than losing duplicate guards.

## Delivery

Implement in an isolated branch based on current main. Commit coherent checked
steps with handoff updates. Independent read-only diff review is required. User
subsequently authorized PR merge, web deployment, and Mezo Testnet wallet demo.
These remain separate phases, with actual CI, image and receipt evidence. Never
read secrets or signing keys, mutate market venues, or rewrite payment state.
