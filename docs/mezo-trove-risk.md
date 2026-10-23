# Mezo Trove risk

The [Testnet product](https://liqvera.site) includes read-only borrower reports,
portable evidence ZIPs and a Trove risk tab. A sealed native example is available
without a wallet; fresh web reports use the existing 0.01 test MUSD x402 flow. The
CLI remains free and does not grant web entitlements.

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
same payload and block. The adapter reports `MEZO_TROVE_SOURCE_UNAVAILABLE`; the public build exposes
`MEZO_SOURCE_UNAVAILABLE`. No retained data or fixture replaces a failed source. A first live attempt hit ConnectTimeout;
a subsequent successful capture took 4,988 ms at block 16320987, with 1,812
calls and 300 owners. The [native capture](../evidence/mezo-testnet/2026-10-23-trove-active-native.json)
replays offline with exact ICR agreement and proven redemption position 1.

Read-only snapshot analysis; not financial advice. Hashes and raw RPC observations
support internal reproducibility, not independent proof of canonical chain
inclusion or a guarantee of liquidation/redemption timing.

## CLI and offline verification

From a clean source checkout with the local packages installed, run:

```sh
python scripts/mezo-trove-risk.py <borrower> --output-root /absolute/path/to/new-artifacts
liqvera-evidence-verify /absolute/path/to/new-artifacts/<report-id>/evidence.zip --report-sha256 <reported-sha256>
```

The repository wrapper derives the actual Git revision and rejects changed code,
ABI or schema inputs. It never accepts an engine-revision override. The installed
`liqvera-trove-risk` command instead requires `--engine-commit` explicitly.
`--capture <raw-capture.json>` builds without network; `--fixture` additionally
labels output simulated and requires that file. Neither path pays or grants access.

The archive includes `mezo-troves/capture.json`, `calls.json` and the three pinned
implementation ABIs. The offline verifier replays the raw risk/queue proof and
rebuilds every report and ZIP byte; recomputing manifest hashes cannot hide altered
calls, ABIs or calculations. It prints an optional fixed-block `fetchPrice()` curl
command without running it. A trusted independent report digest still matters.

The source block time is separate from report creation. A live-source snapshot
older than 30 seconds is labelled `HISTORICAL_SNAPSHOT`; fixtures are `SIMULATED`.
The quality checks cover recalculation, contract ICR and the bounded queue policy,
not RPC authenticity. Report creation timestamps are bounded integer milliseconds.

A committed-code native CLI run at block **16323457** completed in **11,242 ms**,
including report and ZIP publication. Its [report, ZIP and timing observation](../evidence/mezo-testnet/2026-10-23-trove-risk-preview/verification.json)
are retained; both host and non-root network-disabled image verifiers reproduce
the bundle. This is one observed run, not a general latency guarantee. It submits
no payment or web entitlement; the CLI operates independently of web checkout.

## API integration

The additive API 1.1 contract accepts the closed request
`{product_id: "trove_risk", borrower: "<EIP-55 address>", expected_payer: "<address>"}`.
Gateway and report services both default `LIQVERA_MEZO_TROVES_ENABLED` to `false`;
enabling requires live public Testnet sources. Existing hash-bound requests and
artifacts remain readable when creation is disabled. No SQL migration is required.

Capture seals a separate, atomic two-file package. The report service independently
replays its raw calls, binds the borrower and rejects stale data before offering a
quote. Trove previews identify the borrower and active/inactive status. The existing
0.01 MUSD x402 terms, ledger and receipt checks apply unchanged. Creation is enabled
in the published Testnet overlay. No fresh signed Trove purchase is claimed.

## Browser and recovery

The existing application now includes a Trove risk tab, a borrower field prefilled
from the connected wallet, and a text-only risk panel. The public sealed example
uses the retained native report at block 16323457; it checks both immutable asset
hashes before displaying the historical snapshot. No payment was made for it.
New paid creation remains controlled by the backend feature flags.

Trove sessions use version 2 with product and borrower identity; existing version 1
market sessions keep their original representation. Unknown payment outcomes stay
in recovery. Both delivery paths verify the report subject against the quote before
clearing the payment guard. Rollback after exposure must retain readers **and the
new browser**; disabling creation must preserve existing report and payment recovery.

## Deployment evidence

Public native preparation, scope/input boundaries and the unpaid x402 402 response
are verified. Historical verified transfers remain the selected payment proof. [Deployment evidence](security/2026-10-23-mezo-trove-deployment.md)
separates the native blocks, timing observations, image checks and operational limits.
