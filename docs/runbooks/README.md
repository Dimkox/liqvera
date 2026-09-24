# Liqvera deployment runbooks

These procedures describe the F6 code surface. The stack has not been built,
started, or accepted in this code-completion phase. F3–F7 remain
`IMPLEMENTED_UNVERIFIED`; a green container healthcheck is not release or
payment approval. Use the [canonical specification](../planning/LIQVERA_FACTORY_TZ.md)
and [ADR-0002](../adr/0002-liqvera-report-payment-boundary.md) for the safety
boundary.

| Procedure | Use |
| --- | --- |
| [Startup and shutdown](startup-shutdown.md) | Prepare files, start one profile, check liveness, stop without deleting state |
| [Testnet demo](testnet-demo.md) | Separate fixture walkthrough from a gated live-public/testnet demonstration |
| [Payment recovery](payment-recovery.md) | Handle `PAYMENT_UNCERTAIN` without a second charge |
| [Artifact recovery](artifact-recovery.md) | Preserve and inspect immutable reports and bundles |
| [Backup and restore](backup-restore.md) | Capture a consistent recovery set and restore into an isolated project |
| [Incident response](incident.md) | Contain failures while retaining evidence |
| [Observability](observability.md) | Track readiness, integrity, delivery, and recovery signals |

## Deployment contract

The deployment files live in `deploy/mezo-evidence/`. A `fixture` or `live`
Compose profile must be selected, with different project names and volumes.
The only published service is Caddy. The internal web service serves Vite
assets; it has no artifact mount. The report service has read-only raw capture
access and writable artifact access. The gateway has read-only artifact access;
it and its one-shot migration job are the only PostgreSQL clients. Capture alone has public Hyperliquid
egress; report and database have no external network. Network ACLs on the host
must constrain capture to approved Hyperliquid endpoints and gateway to the
approved facilitator/RPC; Compose bridge networks do not enforce destination
allowlists.

All roles drop Linux capabilities, run without root, use read-only root
filesystems, and have bounded CPU, memory, process counts, and healthchecks.
The migration job must exit successfully before the gateway starts. Persistent
named volumes hold captures, artifacts, PostgreSQL data, and
Caddy state. The images currently use versioned base tags; pin audited image
digests and record the built image hashes before any actual release.

No environment file may contain database passwords, private keys, wallet
seeds, bearer capabilities, signatures, or exchange credentials. Local
PostgreSQL secret-file handling is described in
[`deploy/mezo-evidence/secrets/README.md`](../../deploy/mezo-evidence/secrets/README.md).
The merchant `LIQVERA_PAY_TO` address is public configuration, never a
private key. Blank `PAY_TO`, `FINALITY_RULE_UNVERIFIED`, absent canonical authorization
identity, or unverified facilitator/chain binding keeps payment readiness
false. The fixture profile is always simulated and cannot produce a chargeable
quote.
