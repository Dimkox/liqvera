# Blockers and dependencies

## Active blockers

### Public salvage source object unavailable

Commit `7fe6918690f8bc1da5826c67e3619de4126e4f54` is not present in the public
history. F1 Task 2 made default `make salvage` verify the pinned public target
bytes; it explicitly reports `source_objects=unavailable`. Strict source-byte
verification remains unavailable and is not claimed.

### Merchant and buyer setup absent

No operator-owned `PAY_TO`, funded buyer address, wallet signature, or testnet
transaction evidence has been supplied. Payment readiness and A13 remain
blocked. Independent F1–F5 development using mocks may proceed.

### Payment readiness remains blocked after compatibility success

The 2026-09-24 Task 4 probe returned `COMPATIBILITY_PASS_PAYMENT_BLOCKED` with
the ordered blockers `PAY_TO_MISSING` and `FINALITY_RULE_UNVERIFIED`. The exact
sanitized result is `evidence/f1-compatibility.json`. F1 does not read the
operator environment for `PAY_TO`, supply a receiver, or invent a finality
confirmation count. Technical compatibility does not authorize a paid route.

### External acceptance remains time-dependent

Hyperliquid, Mezo RPC, facilitator support, SDK registries, explorer behavior,
and competition submission rules can change. Release evidence must re-run
these checks and record `BLOCKED_EXTERNAL` rather than rely on F1 observations.

## Resolved prerequisites

- F0 public repository and provenance exist.
- Task 4 verified the locked public Hyperliquid/Mezo/facilitator/npm boundary;
  no `BLOCKED_EXTERNAL` remains from this probe. Initial local npm isolation
  failure was corrected and rerun successfully, without weakening any lock.
- The product, brand, testnet-only scope, and vertical scenario are approved.
- The public repository is clean at baseline commit
  `d7a60169985e3a697d7eb5cf29b19b00cb8c0f7a`.
