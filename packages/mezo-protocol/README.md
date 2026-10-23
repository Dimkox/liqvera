# `@liqvera/mezo-protocol`

Pinned, typed Mezo Testnet protocol metadata shared by the Liqvera gateway and
browser application.

```ts
import {
  MEZO_TESTNET,
  MUSD_ABI,
  MUSD_PERMIT,
  MUSD_TESTNET,
  MUSD_TRANSFER_EVENT,
  assertMezoTestnetChainId,
} from "@liqvera/mezo-protocol";
```

The stable exported constants cover Mezo Matsnet chain `31611` / CAIP-2
`eip155:31611`, the official testnet MUSD token, a narrow read-only ABI,
`Transfer` event metadata, and the EIP-2612 domain and typed-data fields.

`assertMezoTestnetChainId` intentionally accepts only the numeric literal
`31611`. Wallet-provided hexadecimal chain IDs must be decoded and validated by
the wallet adapter before calling it; this prevents a string from being treated
as a verified chain identifier.

Payment signing and settlement are outside this package. Consumers must use the
official x402 SDK and retain Liqvera's fail-closed payment-readiness gates. The
full pinned upstream deployment artifact is available only for provenance and
contract inspection at `@liqvera/mezo-protocol/vendor/MUSD.matsnet.json`.

## Mainnet selection

`mezoNetwork("mainnet")` returns the official Mainnet31612 chain, MUSD asset and public RPC; `mezoNetwork("testnet")` retains the original Testnet metadata. Unknown selections throw. The vendored Testnet deployment artifact remains unchanged; Mainnet metadata is documented in [network configuration](../../docs/mainnet.md) and independently checked against the live public contracts before deployment.

## Testnet analytics provenance (2026-10-23)

`MEZO_TESTNET_DEX` pins the basic-pool Router, PoolFactory, MUSD/BTC pool and
BTC token. Narrow exported Pool/Router/Factory ABIs contain only read methods.
The full verified ABIs are in `vendor/*.testnet.json`; the existing MUSD
artifact remains byte-identical. `source-lock.json` records explorer URLs,
retrieval timestamps, ABI SHA-256 and retrieved source hashes. Explorer API
uses `api.explorer.test.mezo.org`, separately from the browser explorer host.

TroveManager, SortedTroves and PriceFeed proxy ABIs are preserved separately
from their implementation ABIs. Explorer implementation metadata is an
observation at retrieval time, not proof of the implementation at every
historical block. PoolFactory exposes the factory ABI despite explorer's
`basic_implementation` classification pointing at its Pool implementation.

The fixed-block [protocol probe](../../evidence/mezo-testnet/2026-10-23-protocol-probe.json)
contains raw calls and block metadata. The observed volatile pool fee is **4 bps**,
not the generic documentation's 30 bps; consumers must read `getFee(pool,false)`
at the captured block. BTC decimals are 18. Pool and router quotes for selling
1 BTC agree exactly. Fee calculation subtracts `floor(amountIn*fee/10000)`
before the constant-product division. `fetchPrice()` is view in the observed
PriceFeed implementation; `lastGoodPrice()` reverts. MCR and CCR are 110% and
150%. These observations do not establish independently authenticated chain
inclusion, paid delivery, deployed analytics or historical archive support.
