# Wallet-signed Trove and DEX actions deployed — October 24, 2026

The Mezo Testnet browser at [liqvera.site](https://liqvera.site) now includes wallet-signed Trove protection and a BTC-to-MUSD sale planner. Source is main commit `573f1c3f3f520b391865668fc0b320816bbf92e5`, tree `de0648f36a98ef451dcb5f07608db4b849cd79a2`. The exact same tree passed [PR CI](https://github.com/Dimkox/liqvera/actions/runs/40041952415) and [post-merge main CI](https://github.com/Dimkox/liqvera/actions/runs/40042762708).

## Runtime change

Only `web-live` was replaced. Its image is `sha256:82fb7a75dc3631838054d84e2579dae690c5835aa120c4117863fe2d23f6779e`; the previous image `sha256:b0187e736edb7f09c9135b1fe8b73df90f8ae29e41e54b4ace2aaa2abd950b19` remains available locally. The other six service images and containers remain unchanged and healthy. The web service has no mounted volumes or service dependencies; no database migration, restore, payment operation or live wallet transaction occurred.

The public site returned HTTP 200 and loaded `assets/index-CnFIyK5k.js`, which contains the deployed labels **Protect this Trove**, **Deposit BTC**, **Repay MUSD** and **Plan BTC sale on Mezo**. The site index is served dynamically and references the new content-hashed asset. A connected wallet must match the borrower on an active Trove report for the protection controls to appear. Deployment verification did not connect a wallet, sign a transaction or exercise a live swap.

The Trove controls fetch fresh state and insertion hints, simulate the exact `BorrowerOperations` call and request the user's wallet signature. The DEX planner uses fresh Mezo Testnet reserves, an editable 1% per-part price-impact cap and editable 1% `minOut` tolerance by default. Approval and every swap require separate wallet signatures; the next part waits for a successful receipt. Splitting adds gas and does not guarantee lower total price impact.

## Health and security

All seven Liqvera containers were healthy after rollout. The public asset check found the expected feature strings. Browser wallet paths remain untested against a live wallet; transaction tests use mocked wallet providers.

Fresh scans bind to the deployed web image: Trivy 0 findings; Grype 4 raw occurrences, identical to the previous web image. The three BusyBox package matches (`busybox`, `busybox-binsh`, `ssl_client`, CVE-2025-60876) correspond to the reviewed patched binary and bundled corresponding source. The remaining High match is `curl` 8.22.0-r0, CVE-2026-92392; curl is inactive in this static nginx runtime. This is an applicability/configuration disposition, not a patched-package or zero-raw claim. No new image finding was introduced.

The deployed `/bin/busybox` SHA-256 is `4261945c0287000d3e73548d381a5afa4279eb07ed6e223ee6c5c51ba39f1642`, matching the previously reviewed patched binary. Its corresponding source remains packaged in the image.

The dependency gate also reported zero known vulnerabilities for both Python lockfiles and both npm applications. Zod was pinned to 4.6.6 in web and gateway dependency overrides, and the web/gateway locks were generated with the pinned Node 22/npm 10 runtime. Web tests/build and gateway tests/typecheck passed locally; hosted CI passed the full product gate.

## Recovery

The private pre-rollout Compose manifest and image binding are retained under `/home/pall/.local/state/liqvera/recovery/2026-10-24-web-wallet-actions-573f1c3/` (directory mode 0700, files mode 0600). The manifest SHA-256 is `b154d862191e10d0d6fb331ca638047c9a3d7afe72758625be30567d92f1df67`. To restore the previous web image and Compose configuration without touching data volumes:

```sh
install -m 0600 /home/pall/.local/state/liqvera/recovery/2026-10-24-web-wallet-actions-573f1c3/compose.before.json /home/pall/.local/share/liqvera/deploy/compose.json
docker compose -f /home/pall/.local/share/liqvera/deploy/compose.json up -d --no-deps --pull never web-live
```

Compose removed three stale stopped web-only rollback containers while recreating `web-live`; the previous image and original manifest are retained for recovery. No database, payment state, sealed bundle, artifact volume or published release asset was changed.
