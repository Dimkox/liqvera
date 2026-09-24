# Source baseline evidence

Observed: 2026-09-24T15:46:33Z
Repository commit: `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a`
Branch at observation: `main`
Working tree at observation: clean

## Source digests

| File | SHA-256 |
| --- | --- |
| `pyproject.toml` | `2f68390a0cbbdb06509b30c46123cefc54a1d62572dd17384a116bba25742c07` |
| `README.md` | `9eaa5e9f4579813377f930375d92c307931bfbe5c0537f18fdbf818683e7d0a5` |
| `docs/planning/LIQVERA_FACTORY_TZ.md` | `b6ae0acebe615129a4504a333f5ccc6274c985f721a4ca1d21932c7fbe4776e1` |

## Local environment

- Python `3.12.3`
- Make available
- Docker available
- Node and npm available
- Repository development dependencies were not installed or changed during
  this observation.

## Commands and results

| Command | Exit | Result |
| --- | ---: | --- |
| `make verify` | 2 | Stopped at graph check: four publication files undeclared/unclassified |
| `make salvage` | 2 | Required private-history source object absent |
| `make artifacts` | 0 | Stage A artifacts contain no Go inputs |
| `make verify-packages` | 2 | 504 passed, 5 failed, 6 errors, 85 subtests passed |

The five failures are consequences of the same incomplete architecture
inventory. The six errors are wheel-build setup failures because the current
interpreter lacks `hatchling`. Three pytest configuration warnings also show
that the ambient environment does not match the pinned development toolchain.

## Read-only external observations

- Mezo RPC returned chain ID `0x7b7b` (31611).
- The configured MUSD address returned non-empty bytecode and decimals `0x12` (18).
- Facilitator `/supported` advertised x402 v2 `exact` on `eip155:31611` with the
  configured MUSD address and EIP-2612 gas sponsoring.
- npm exposed matching `@x402/core`, `@x402/evm`, and `@x402/express` version families,
  including the official quickstart candidate `2.16.0`.
- Hyperliquid public `meta` included BTC with `szDecimals=5`; public `l2Book`
  returned BTC bids/asks with 20 levels on each side during the probe.

These are observations, not permanent guarantees or payment acceptance
evidence. Exact raw responses were not committed because they are transient;
F1 compatibility tooling will produce bounded, redacted, reproducible output.
