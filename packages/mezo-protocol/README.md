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
