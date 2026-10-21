# Liqvera deployment

The source stack is under `deploy/mezo-evidence`. Use separate projects for fixture and live-public profiles. A source build is not permission to deploy to an existing service. Review [migration](migration.md), [security](../SECURITY.md), and current CVE results first.

## Local fixture composition

Prepare the fixture example environment with the exact source SHA and private local secret files as described in [startup](runbooks/startup-shutdown.md). Fixture capture is synthetic, payment readiness is false and all service networks are internal. Build images under candidate-specific names when a live stack shares the Docker daemon; never overwrite its `:local` image tags during validation.

The edge binds fixture HTTP to loopback. Check `/healthz`, `/readyz` and `/v1/capabilities`; a static HTML 200 response at another path is not gateway health. Preserve named volumes when stopping services. Never use `down --volumes` against payment or evidence state.

## Live-public operation

TLS/DNS, fixed public origin, private database and internal token files, exact source bindings and explicit payment-mode configuration are operator prerequisites. Merchant mode requires a wallet signature per purchase; grant mode additionally requires external operator authority. Existing signed operator authority expires and must never be silently renewed. The full updated stack was deployed on 2026-10-12 and all seven containers passed health checks. API liveness and payment readiness are available; merchant checkout is enabled. Gateway and browser use Mezo Testnet (31611), with the preserved `liqvera` database and 0.01 test-MUSD price. See the [Testnet deployment record](security/2026-10-12-testnet.md) and [standalone Testnet setup](runbooks/testnet-demo.md).

Back up PostgreSQL and both artifact/input volumes coherently before changes. Preserve the migration ledger, canonical payment identity and unknown outcomes. An update that changes source-bound authority needs new review; namespace migration is not authorization to mutate existing records.

The current host deployment manifest is `/home/pall/.local/share/liqvera/deploy/compose.json` (private, mode 0600). It pins the deployed image tags and references existing external networks and volumes. Use this manifest for subsequent operations; obsolete worktree manifests do not describe the current deployment. The active Testnet database volume is `liqvera-live_postgres_data`. The Mainnet volume `liqvera-live_mainnet_postgres_data_6ee3bbe_final` and stopped Mainnet application containers are retained. Testnet-switch backups are under `/home/pall/.local/state/liqvera/recovery/2026-10-12-testnet-f9ff498/`. Mainnet-switch recovery backups are under `/home/pall/.local/state/liqvera/recovery/2026-10-12-mainnet-final/`; preceding full-stack backups remain under `/home/pall/.local/state/liqvera/recovery/2026-10-12-production/`. Never commit their contents.

Merchant rollout backups are under `/home/pall/.local/state/liqvera/recovery/2026-10-12-merchant-5f87329/`. Migration 008 is additive. A rollback may run the retained previous gateway with the current database, but must not run its older migration command or restore an earlier database over subsequent purchases. Preserve and reconcile all pending or unknown payment rows.

## Wallet connection

The current application source is `1c020995adaa1a80fc8a97888aa838041d8e01d5`, deployed on claw on 2026-10-21 with corrected Python, Node and Caddy TLS trust. The browser includes the funding-layout repair and Getzilla footer link. Web image: `sha256:6b26f78a2856e7f2f5a07884249d2b45351a08b3160732ef50a5d04967e07a06`; entry: `index-Cnfn94HM.js`. All seven containers are healthy. Six application containers were replaced; the existing PostgreSQL container, WalletConnect configuration, Caddy policy, databases and historical evidence remain preserved. See [current TLS deployment evidence](security/2026-10-21-tls-deployment.md), the preceding [layout record](security/2026-10-21-layout-deployment.md) and immutable [Wave 1 deployment](security/2026-10-21-wave1-deployment.md).

Current recovery material is private under `/home/pall/.local/state/liqvera/recovery/2026-10-21-tls-1c02099/`. The six retained previous application containers have suffix `-before-tls-1c02099`. To roll back this TLS deployment:

```bash
python3 /home/pall/.local/state/liqvera/recovery/2026-10-21-tls-1c02099/rollout.py rollback
```

The command restores the preceding application containers and operational manifest without restoring a database or running migrations. Retained old images still have the previous TLS exposure. Keep all recovery generations and their records until their recovery windows are explicitly closed. Earlier layout/Wave 1 commands have exact-current-image guards and are not interchangeable with this command.

Create an owner-controlled Liqvera project in the [Reown dashboard](https://dashboard.reown.com) and allow the canonical origin `https://liqvera.site`. Set `LIQVERA_WALLETCONNECT_PROJECT_ID` to its public 32-character project ID before building the web image. Compose passes this value as a Docker build argument; local Vite builds use the same environment variable. It is public browser configuration, not a password or wallet key. Changing it requires rebuilding the static browser. Do not use an ID copied from another application or the SDK's localhost example for a public deployment.

Configured builds use a single AppKit modal for injected wallets and WalletConnect, with account management and disconnect. Builds without the variable retain injected-wallet support, but cannot pair a wallet from ordinary mobile Chrome/Safari. The default network remains Mezo Testnet; project configuration does not enable Mainnet or authorize a payment.

Deploy the matching Caddy policy as well as the browser: the earlier same-origin-only connection policy blocks WalletConnect. Preserve the old browser and edge images for rollback. Verify modal rendering and QR generation under the enforced policy, then pairing, reconnect, network selection, quote preparation and payment cancellation with a real mobile wallet. A localhost QR or a simulated provider does not establish production relay acceptance or a completed purchase. The browser never supplies a wallet private key.
