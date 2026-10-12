# ADR-0002 — Liqvera report and payment boundary

Status: accepted; current implementation clarified 2026-10-12.

Python owns public capture, identity validation, exact analytics, report construction and offline verification. The TypeScript/Express gateway owns browser delivery, the public HTTP API and official x402 composition. It never rewrites report bytes. PostgreSQL owns durable payment/entitlement state; immutable files own artifact bytes.

Only Mezo Testnet 31611 is supported. Custody, mainnet payments, exchange trading, merchant private keys and private venue credentials are outside scope. Testnet settlement requires separately reviewed authority and sponsored authorization. Unknown outcomes permit confirmation only.

These components are implemented. Historical paid delivery exists, while overall acceptance remains incomplete. See [specification](../specification.md) and [handoff](../../handoff.md) for current evidence. Local tests, source cleanup and this ADR do not authorize deployment or a fresh settlement.

Recovery preserves the ledger and artifacts. Disable new payments before repairing uncertain state; use coherent backups and reviewed forward changes rather than destructive rollback.
