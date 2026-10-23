# Mezo Testnet integration

Liqvera keeps one web/API product. MUSD x402 purchases and the DEX extension are deployed on liqvera.site.
The [October 23 deployment record](security/2026-10-23-mezo-dex-deployment.md)
binds source, images, immutable preview URLs and verification scope.
All new chain calls target Testnet 31611 at a captured block number. No swap,
borrow, redemption or new payment is submitted by capture or verification.

## DEX evidence

The public capture service reads token identity, reserves, BTC decimals and
`PoolFactory.getFee(pool,false)`, then cross-checks the requested quote through
both Pool and Router. Capturing Mezo before Hyperliquid keeps the order-book
snapshot fresh at report construction. The private report service has no RPC
access. Enable new live builds with `LIQVERA_MEZO_DEX_ENABLED=true` on the report
service; the Testnet deployment override selects it. Do not enable this setting
for the fixture profile. Missing Mezo evidence fails with
`MEZO_SOURCE_UNAVAILABLE`; no retained snapshot or fixture replaces a failure.
Existing report IDs always retain their original immutable evidence.

`report.mezo_dex` includes the block number/hash, exact atomic amounts, prices,
impact, fee and five reserve-derived depth points. The requested quote is
cross-checked on-chain; the ladder is calculated offline. `venue_comparison`
compares a Hyperliquid perpetual USD quote with a Mezo spot MUSD quote and
explicitly identifies this difference. It excludes gas, Hyperliquid fees and
funding. The pool fee is included in the Mezo quote.

The observed pool fee on October 23 is **4 bps**, not the generic documented
30 bps. The verified Pool subtracts a truncated fee before division. The buy
calculation finds the smallest integer input whose exact-input quote reaches
at least the requested output. It checks the same uint256 intermediate bounds
as Solidity; mathematical results that would revert are rejected.

New ZIPs retain `mezo-dex/capture.json`, `mezo-dex/calls.json` and the three
verified DEX ABIs with manifest SHA-256. The verifier decodes raw calldata and
results, verifies the captured request, recalculates the report and rebuilds
all archive bytes offline. It prints a fixed-block curl command for optional
manual online comparison, without executing it. Existing ZIPs remain valid.
This is an additive v1 schema extension; Mezo fields are optional on legacy
reports. A trusted independent report digest remains necessary to detect an
attacker replacing an entire internally consistent bundle. RPC observations
and a block hash are not cryptographic chain-inclusion proofs.

## Reproduce from source

Install Python 3.12+ and the four local packages:

```sh
python -m pip install ./packages/contracts ./packages/public-capture ./packages/readonly-analyzer ./packages/evidence-report
liqvera-evidence-verify path/to/evidence.zip
```

Success is `INTEGRITY_REPRODUCED` with exit 0. Verification performs no network
request. For an explicit fresh public read:

```sh
.venv/bin/python scripts/capture-mezo-dex.py --live --side SELL --quantity 1 --output /absolute/new/capture.json
```

The output path must be new. A single transient native-transport capture failed
closed during development; subsequent native SELL and BUY captures succeeded.
Both native and separately identified curl captures are retained under
[evidence/mezo-testnet](../evidence/mezo-testnet/). Live observations do not
establish wallet-paid acceptance or a deployed source version.

## Protocol and payments

[Protocol provenance](../packages/mezo-protocol/README.md) lists source locks,
proxy distinctions and verified ABI observations. The historical payment
[explorer responses](../evidence/mezo-testnet/2026-10-23-payment-explorer.json)
show three successful 0.01 MUSD transfers to the operator-configured merchant.
They remain historical transactions; new paid acceptance requires a new
wallet-authorized purchase after the separately reviewed rollout.

For Trove work, the verified implementation differs from the draft ABI:
`getEntireDebtAndColl()` returns collateral, principal, interest, pending
collateral, pending principal and pending interest. The first three values
already include pending rewards. `fetchPrice()` is view; `lastGoodPrice()`
reverts. The redemption walk starts at `getLast()` and follows `getPrev()`,
skipping ICR below MCR. A list index alone is not a proven redemption position.
Trove report delivery remains a subsequent implementation step.

## Published public preview (October 23)

The source preview contains a real SELL 1 BTC comparison captured on October 23,
with Mezo block 16321216 and engine commit
`65ee000377028e3909a72402a5341ff4ddd56c1a`. Its report SHA-256 is
`d58728bd3df4b79c43bb2e742225e5b8f879eb0ec292213ffd3941f0f8778753`;
its ZIP SHA-256 is
`0c20f41f845bd39c88286b52a64d1dad53713fd215507f611fab51d29896f51f`.
These digests are pinned by the browser before rendering. The previous preview
remains byte-for-byte in `apps/mezo-web/public/demo/archive/0ebf36b89bda183b/`.
The published pair reproduces offline. Historical payments are used for this
update at the owner's request; no fresh paid purchase is claimed.

The browser requests both preview assets from `/demo/snapshots/<report-sha256>/`,
so a CDN cannot combine a newly deployed JSON with a cached ZIP from an older
release. The mutable `latest-live` directory remains a compatibility alias;
verification and download links use the immutable snapshot path.
