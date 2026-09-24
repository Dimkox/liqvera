# Blockers and dependencies

## Active blockers

### Public salvage source object unavailable

`make salvage` requires commit `7fe6918690f8bc1da5826c67e3619de4126e4f54`,
which is not present in the public repository history. F1 must replace this
with an honest public-snapshot proof or keep the limitation explicit. It must
not claim to revalidate private source bytes.

### Merchant and buyer setup absent

No operator-owned `PAY_TO`, funded buyer address, wallet signature, or testnet
transaction evidence has been supplied. Payment readiness and A13 remain
blocked. Independent F1–F5 development using mocks may proceed.

### External acceptance remains time-dependent

Hyperliquid, Mezo RPC, facilitator support, SDK registries, explorer behavior,
and competition submission rules can change. Release evidence must re-run
these checks and record `BLOCKED_EXTERNAL` rather than rely on F1 observations.

## Resolved prerequisites

- F0 public repository and provenance exist.
- The product, brand, testnet-only scope, and vertical scenario are approved.
- The public repository is clean at baseline commit
  `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a`.
