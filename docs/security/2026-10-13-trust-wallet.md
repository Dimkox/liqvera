# Trust Wallet mobile connection — deployed Testnet verification

Source: `a93605d20224c8711d51cf5eded93cff3832727d`. Public service: https://liqvera.site, Mezo Testnet 31611. Only the browser container changed; other services and payment state remain untouched. The previous browser and private manifest are retained for rollback.

## Connection and verification

Ordinary mobile Chrome/Safari has no injected wallet provider. Connect wallet now exposes an explicit **Open in Trust Wallet** link using Trust Wallet’s [documented universal dApp link](https://developer.trustwallet.com/developer/develop-for-trust/deeplinking). It opens only the canonical public origin; session and payment data are never appended. The user continues with Connect wallet inside Trust Wallet. The application also discovers `window.trustwallet.ethereum` and requests accounts before switching networks.

Rejected reconnects now clear stale network readiness and refresh actual provider state. All 37 browser tests and the Testnet production build pass. Independent read-only code and rollout reviews found no remaining blocker.

Real Chrome against the deployed service shows the Trust link at a mobile viewport with no injected provider. A strict simulated Trust provider, exposed only through its namespace, verifies permission ordering, rejection, reconnect, fresh report creation and signature cancellation with retry. The physical Trust app handoff and a real signed payment were not tested. These checks submitted no payment.

## Exact-image security

Deployed image: `sha256:6ba39f318c349f635294eaba50c4979323ec843fd5d4ff190f7d702ef0a60505`. Public bundle: `index-C3TyJw3r.js`.

| Check | Result |
| --- | --- |
| npm audit | 0 advisories |
| Trivy | 0 raw findings |
| Grype | 3 reviewed BusyBox backport matches |
| New untriaged findings | 0 |

Grype reports CVE-2025-60876 on busybox, busybox-binsh and ssl_client. The binary matches the previously reviewed patched SHA-256 `4261945c0287000d3e73548d381a5afa4279eb07ed6e223ee6c5c51ba39f1642`, whose eight security regressions passed in the prior audit. Vendor package versions remain unchanged and raw findings are retained.

Both database refreshes succeeded on October 13. The exact deployed image was rescanned after the Grype refresh: Grype database `2026-10-13T06:35:20Z`; latest returned Trivy database `2026-10-12T13:18:23.1639207Z`. The Node dependency closure is unchanged. Other images retain their [prior exact-image evidence](2026-10-12-testnet.md); this audit covers the rebuilt browser.

[Machine-readable audit](2026-10-13-trust-wallet.json), [VEX](2026-10-13-trust-wallet-vex.json), [deployment and browser evidence](2026-10-13-trust-wallet-deployment.json), [raw archive](2026-10-13-trust-wallet-raw.tar.gz). Archive SHA-256: `ad544196ceb0e2445df3b834b8fcc2b94254f6012cc07c5ef911e63d207b73c9`. All 15 archived member hashes were checked.
