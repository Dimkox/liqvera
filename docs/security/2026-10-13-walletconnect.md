# WalletConnect deployment and security audit — 2026-10-13

Source `e75ce59a87238ad91cd09ad364ef524a50828299` is deployed at **https://liqvera.site** with the owner's public Reown project ID. Browser image: `sha256:e4a2aeb5f71bcb74d747b746b9a83571e3d8ddf93d2e9ccbc26868aa597ee3f9`; public entry asset: `index-BQP4zj3R.js`. The unchanged edge image uses the matching source-bound Caddy policy. All seven service containers are healthy. Gateway, database, capture, report and network proxy were not replaced. The gateway remains on Mezo Testnet, with a 0.01 test-MUSD report price.

## Functional checks

All 49 browser tests pass. Gateway has 58 passes and 13 database-dependent skips; nine Python artifact and operations checks pass. Type checking, clean Node 22 image installation/build, documentation links and Caddy validation pass. The clean build exposed an npm 11 optional-peer lock defect; the corrected lock resolves those optional peers separately without changing Liqvera's root x402 2.16.0 payment dependencies. Independent source, lock and rollout reviews found no remaining blocker.

Real mobile-viewport Chrome verified the deployed HTTPS origin and exact public asset. The official AppKit rendered wallet selection and a QR pairing URI. The WalletConnect relay returned a successful WebSocket upgrade, with no observed relay error response, uncaught exception or CSP violation. Public site responses were fetched through the validation environment's HTTPS proxy; SDK relay and directory connections were direct. The harness initially paused dynamic imports while waiting for its modal, then passed after continuing those requests. No application change was needed for that harness correction.

Using an emulated EIP-6963 wallet through the actual SDK, the published browser prepared a fresh live-public quote on another chain without signing. An unknown network was added and then explicitly selected. Payment authorization rejection remained pre-submit cancellation. Disconnect retained the quote and disabled payment; reconnect restored readiness without signing again. Reload restored the wallet and saved quote. This proves the browser integration and public API path with simulated wallet responses; it does not prove physical mobile pairing or a real signed purchase. No payment was submitted.

## Security checks

npm audit reports **0 vulnerabilities**. OSV reports **0 affected packages across 323 unique locked package/version pairs**, including optional dependencies. Fresh Trivy and Grype scans completed for the exact browser and edge images without suppression.

| Image | Trivy raw matches | Grype raw matches |
| --- | ---: | ---: |
| Browser | 0 | 3 |
| Edge | 1 | 3 |

The three Grype matches per image are `CVE-2025-60876` package-version matches for BusyBox. Both binaries match the previously reviewed and regression-tested patched SHA-256 `4261945c0287000d3e73548d381a5afa4279eb07ed6e223ee6c5c51ba39f1642`. Corresponding patched source remains in each runtime image.

The edge's `GO-2026-5932` match concerns the unmaintained OpenPGP package. The exact edge image is unchanged from the [previous production audit](2026-10-12-production.md), whose binary/dependency analysis established that this code is absent. Its reviewed non-applicability remains bound to that image. There are **no new or untriaged findings**. This is not a claim that raw scanner output is empty or every possible vulnerability database was queried.

[Detailed results](2026-10-13-walletconnect.json) record image identities, dependency hash, database metadata and all dispositions. [Image-bound VEX](2026-10-13-walletconnect-vex.json) and the [raw archive](2026-10-13-walletconnect-raw.tar.gz) retain unsuppressed scanner output and browser evidence; archive member hashes were verified. Other runtime images retain their existing audit evidence.

## Recovery and configuration

[Deployment identity](2026-10-13-walletconnect-deployment.json) records the previous browser image, retained rollback containers and private manifest backup. Only the browser and edge container/configuration changed. The old edge retains its original bound Caddyfile; TLS volumes are preserved. Payment ledgers, unknown payment states and sealed artifacts were not migrated or recreated.

The public frontend build setting is retained in `/home/pall/.local/share/liqvera/deploy/walletconnect.env`; it contains the project ID, not a private wallet credential. The active edge binds an immutable Caddyfile snapshot beneath `/home/pall/.local/share/liqvera/deploy/config/e75ce59a87238ad91cd09ad364ef524a50828299/`. Rebuild the browser to change its project ID and deploy the matching policy. Never substitute the documentation's localhost-only project ID in a public build.
