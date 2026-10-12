# Liqvera engineering decisions

- Use the complete latest main baseline for cleanup; confirm refs, tags and worktrees before changing product scope.
- Keep runtime building and testing independent of external delivery tooling. Getzilla can audit from a separate exact checkout.
- Treat the approved technical rename as a breaking 0.2.0 component migration. Preserve sealed historical bytes, SQL migration hashes, upstream notices and consumed payment authority.
- Remove unused browser paywall and Express integration packages: the application composes the official core/EVM client and server directly. Preserve reviewed x402 protocol versions and payment constraints.
