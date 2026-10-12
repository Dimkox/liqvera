# Liqvera deployment

The source stack is under `deploy/mezo-evidence`. Use separate projects for fixture and live-public profiles. A source build is not permission to deploy to an existing service. Review [migration](migration.md), [security](../SECURITY.md), and current CVE results first.

## Local fixture composition

Prepare the fixture example environment with the exact source SHA and private local secret files as described in [startup](runbooks/startup-shutdown.md). Fixture capture is synthetic, payment readiness is false and all service networks are internal. Build images under candidate-specific names when a live stack shares the Docker daemon; never overwrite its `:local` image tags during validation.

The edge binds fixture HTTP to loopback. Check `/healthz`, `/readyz` and `/v1/capabilities`; a static HTML 200 response at another path is not gateway health. Preserve named volumes when stopping services. Never use `down --volumes` against payment or evidence state.

## Linux operator

The published operator version is v0.0.2 and remains a distinct immutable release. Obtain its bootstrap, verifier, archive and independently trusted SHA-256 values from the matching release. Verify before executing; never pipe a remote script into a shell. The standard-library installer accepts only closed shadow/payment-disabled configuration and references to private secret files. It supports start, stop, status, bounded logs and uninstall; default uninstall preserves data.

Update and rollback are fail-closed with ROLLBACK_RESTORE_REQUIRED until coherent backup/restore and migration-ledger support is implemented. Local installer validation is mocked contract evidence, not clean-host proof. The historical aggregate remains 9 PASS, 21 NOT_RUN, not a single runner overall PASS.

## Live-public operation

TLS/DNS, fixed public origin, private database and internal token files, exact source bindings and explicit payment-mode configuration are operator prerequisites. Merchant mode requires a wallet signature per purchase; grant mode additionally requires external operator authority. Existing signed operator authority expires and must never be silently renewed. The full updated stack was deployed on 2026-10-12 and all seven containers passed health checks. API liveness and payment readiness are available; merchant checkout is enabled. Gateway and browser now use Mezo Mainnet (31612), with a separate `liqvera_mainnet` database. See the [Mainnet production record](security/2026-10-12-merchant.md).

Back up PostgreSQL and both artifact/input volumes coherently before changes. Preserve the migration ledger, canonical payment identity and unknown outcomes. An update that changes source-bound authority needs new review; namespace migration is not authorization to mutate existing records.

The current host deployment manifest is `/home/pall/.local/share/liqvera/deploy/compose.json` (private, mode 0600). It pins the deployed image tags and references existing external networks and volumes. Use this manifest for subsequent operations; obsolete worktree manifests do not describe the current deployment. The current Mainnet database volume is `liqvera-live_mainnet_postgres_data_6ee3bbe_final`. The Testnet database volume and stopped application containers are retained. Mainnet-switch recovery backups are under `/home/pall/.local/state/liqvera/recovery/2026-10-12-mainnet-final/`; preceding full-stack backups remain under `/home/pall/.local/state/liqvera/recovery/2026-10-12-production/`. Never commit their contents.

Merchant rollout backups are under `/home/pall/.local/state/liqvera/recovery/2026-10-12-merchant-5f87329/`. Migration 008 is additive. A rollback may run the retained previous gateway with the current database, but must not run its older migration command or restore an earlier database over subsequent purchases. Preserve and reconcile all pending or unknown payment rows.
