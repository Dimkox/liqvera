# Gateway startup incident — 2026-10-12

The public gateway repeatedly exited before listening, returning HTTP 502 through the edge. An isolated diagnostic using its exact image passed configuration, contract loading, read-only database connectivity, private-file validation and database identity. Payment grant composition returned `LIVE_GRANT_INVALID`. This identifies the failing stage; no grant contents were disclosed and no new grant was issued.

Source fix: `c7b19bcbd2b7774a0abd218d18dfb40bea0684b2`, published to GitHub main. Known grant-validation failures now log `PAYMENTS_DISABLED` with a bounded code and select the existing grantless adapter. Invalid authority cannot initialize new payments or activate a ledger authority. Unexpected errors still fail. Existing confirmation, delivery and workers retain their ordinary behavior.

All 61 gateway tests passed with a disposable PostgreSQL database, including real process startup with invalid authority. Independent read-only review found no blocker. The final compatible image was also checked with its historical contract set before rollout.

[Machine-readable deployment and public checks](2026-10-12-gateway-startup.json) retain image IDs, code hashes and observed endpoint results.

## Deployment and result

Only compiled `main.js` and `security/live-composition.js` were layered over the existing gateway image. Historical contracts, other services, environment, mounts and database migrations were unchanged. This compatible hotfix is separate from the complete namespace and CVE migration now published in main. It does not remediate the vulnerabilities in the historical runtime images.

- Previous image: `sha256:ebd33681d08998d85e9241f10394383f61a6ae8f1312e53d1bfd528ee192a92f`.
- Hotfix image: `sha256:5e0d12f44d5462b07d2e5fcf8a5b14f17a468a493e4f219fab5c4235a4086ddc` (`liqvera/gateway:grant-startup-fix`).
- Public landing, `/healthz`, `/v1/capabilities` and immutable preview: HTTP 200.
- `/readyz`: HTTP 503, with storage/integration/configuration ready and only payment blockers remaining.
- Gateway healthy, zero restarts after replacement. Preview report hash remains `8f8fd199de1674e5b3f154e50609792bd7bdd711e15cd8a8c15cd703bcaac7dd`.
- No new settlement, grant renewal or chain change was performed. Network remains Mezo Testnet 31611.

The replacement retains normal worker behavior, including confirmation and retention. It is not a database read-only recovery mode. Database and both evidence volumes were backed up before restoration. The original container is retained stopped for rollback.

## Operator recovery references

Private backups are located at `/home/pall/.local/state/liqvera/recovery/2026-10-12-gateway/`; contents are not in Git. The stopped rollback container is `liqvera-live-gateway-before-startup-fix`. The persistent image override is `/home/pall/grok-projects/liqvera-live-deploy/compose.startup-fix.yaml`; include it after the existing deployment Compose files on future recreations. Do not run migrations or replace historical images with the breaking namespace migration as part of this hotfix.

Rollback consists of stopping the replacement gateway, preserving its state, restoring the retained container under its original name and starting it. This returns the previous image and its known startup fault; it is a recovery option, not a working fix. Never roll back the ledger or sealed evidence independently.
