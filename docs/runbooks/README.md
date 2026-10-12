# Liqvera deployment runbooks

These procedures cover the current application and its isolated fixture/live-public profiles. A passing local healthcheck does not authorize payment or release. Use the [specification](../specification.md), [architecture](../architecture.md), [migration](../migration.md) and [handoff](../../handoff.md) for current boundaries and executed evidence.

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
access and writable artifact access. Capture (UID 10001), report (UID 10002),
and gateway (UID 10003) share only evidence GID 10001. Capture/report publish
directories as `0750` and files as `0640`, so the report can read captures
and the gateway can read completed artifacts without sharing a write UID.
The gateway has read-only artifact access;
it and its one-shot migration job are the only PostgreSQL clients. Report and
gateway alone receive the profile-specific internal report token file.
In the live profile, capture has public Hyperliquid egress, gateway has
payment/RPC egress, and edge has TLS egress. The fixture profile attaches none
of those external networks. Report and database have no external network.
Metrics bind only to the gateway's internal `operations` network and are not
published on the host or routed by Caddy. Network ACLs on the host
must constrain capture to approved Hyperliquid endpoints and gateway to the
approved facilitator/RPC; Compose bridge networks do not enforce destination
allowlists.

All roles drop Linux capabilities, run without root, use read-only root
filesystems, and have bounded CPU, memory, process counts, and healthchecks.
The migration job must exit successfully before the gateway starts. Persistent
named volumes hold captures, artifacts, PostgreSQL data, and
Caddy state. Base images are digest-pinned; rescan and record the built image hashes before any release.

No environment file may contain database passwords, private keys, wallet
seeds, bearer capabilities, signatures, or exchange credentials. Local
PostgreSQL and internal report-token handling are described in
[`deploy/mezo-evidence/secrets/README.md`](../../deploy/mezo-evidence/secrets/README.md).
The merchant `LIQVERA_PAY_TO` address is public configuration, never a
private key. Blank `PAY_TO`, `FINALITY_RULE_UNVERIFIED`, absent canonical authorization
identity, or unverified facilitator/chain binding keeps payment readiness
false. The fixture profile is always simulated and cannot produce a chargeable
quote.
