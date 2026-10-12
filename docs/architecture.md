# Liqvera architecture

The browser and gateway are TypeScript applications. Capture, exact arithmetic, report construction and offline verification are Python packages. PostgreSQL owns durable quote, grant, payment and entitlement state. Filesystem volumes own sealed inputs and output artifacts. Caddy terminates public HTTPS; nginx serves the static browser application.

## Request and data flow

A browser discovers an EIP-6963 wallet, checks its configured Mezo network, and requests a quote scoped to the expected payer. The gateway records the request and asks the internal report service to build evidence. Capture queries the fixed public Hyperliquid endpoints, seals exact bytes and source metadata, and publishes immutable input. The report service validates that input and computes rational/exact-decimal depth results, then publishes JSON and ZIP with hashes. The gateway binds the quote and entitlement to those exact hashes.

The payment adapter validates x402 Permit2 and EIP-2612 sponsorship, recipient, amount and asset. Merchant mode requires a fresh wallet authorization; grant mode additionally requires bound external authority. PostgreSQL reserves merchant Permit2 nonces across quotes (or consumes operator authority in grant mode) and moves to SUBMITTING atomically before settlement. Unknown outcomes are confirm-only. Delivery follows canonical-chain receipt checks and at least twelve confirmations. Restart cannot grant permission to submit twice.

## Isolation

Capture receives no database, payment or report-service credentials. Report mounts capture read-only, owns output artifacts and requires an internal bearer token. Gateway reads artifacts and owns ledger transitions. Only the live-public profile has the specifically required capture, payment and TLS egress networks. Fixture services have no external egress. Metrics remain on the operations network.

The browser receives no private signing key, server credential or live authority file. The historical preview validates two pinned asset hashes and fixed report identity before rendering. Those published bytes are never rewritten during branding changes.

## Exactness and integrity

Money, prices and quantities cross JSON boundaries as strings. Calculations use exact arithmetic and explicit display rounding. Crossed, stale, malformed or insufficient data fail closed. The offline verifier validates bounded ZIP metadata, paths, members and digests before recalculating. It neither authenticates the exchange nor arms execution.

SQL migrations 001–006 and their ledger hashes remain unchanged. Forward migration 007 adds immutable per-ledger network identity and paired network/token constraints. Mainnet uses separate database state, and startup rejects the wrong ledger network. Migration 008 adds a unique merchant nonce index without rewriting historical rows. Old persisted JSON is not silently relabelled. [Migration guidance](migration.md) defines recovery and separation of historical state.

## Build ownership

Four independently installable Python packages, two Node applications and the protocol metadata package are built from this repository. A clean-source check binds release artifacts to the selected commit. No external delivery framework or private host controller is needed. Optional Getzilla auditing is invoked from an external pinned checkout and does not become an application dependency.

There is no Go application or module in this repository. The edge Dockerfile compiles the upstream Caddy proxy with patched dependencies. Runtime images carry reviewed CPython and BusyBox security backports under `deploy/security`; those are third-party fixes with regression tests, source provenance and retirement instructions. Gateway's Alpine Node LTS uses the patched system OpenSSL rather than an embedded older copy.

See [the specification](specification.md), [security](../SECURITY.md) and [validation](validation.md) for current proof and limitations.
