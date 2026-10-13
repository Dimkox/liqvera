# Report preparation and network switching — deployed verification

Source: `ee2a19c48b447a52d191959424da6f55e713bd68`. Service: https://liqvera.site, Mezo Testnet 31611.

A connected payer can prepare a report and quote while its wallet is on another chain. Payment and artifact access retain the required Mezo network, exact payer binding, wallet authorization and settlement checks. The browser revalidates the chain and account immediately before signing.

The wallet adapter explicitly selects a newly added chain when needed. [EIP-3085](https://eips.ethereum.org/EIPS/eip-3085) does not guarantee selection after adding a chain. Final chain verification and cancellation are preserved. Pinned manual network settings are exposed when automatic switching fails.

Two new regressions failed before correction. All 42 web tests and the Testnet build pass. Independent read-only code and rollout reviews found no blocker. Real Chrome against the preceding deployment reproduced the screenshot state: address connected, another chain, request button disabled. Against the new deployment at a 390×844 viewport, the same state enables preparation and reaches a fresh live quote with zero signing calls and payment disabled. Adding Mezo without selecting it then triggers an explicit switch; the payment becomes available, and a rejected signature cancels before submission. The candidate also passed unsupported-network handling with manual settings shown and payment blocked. These are simulated wallet responses, not a physical Trust app or a signed purchase.

Only the browser changed. Public readiness and payment readiness remain true. The prior browser container and private manifest are retained for rollback.

Image: `sha256:3eddb87fc9b6efaad46c68d29517947e6b3f25d6b19fe9d277fb978ecc24a861`. Public asset: `index-Dw5JwIhL.js`.

npm audit and Trivy: zero findings. Grype: three reviewed CVE-2025-60876 matches on the unchanged, verified BusyBox backport binary. No new untriaged finding. The Node dependency lock is identical to 88ccb98. Scanner databases were successfully refreshed earlier in this October 13 session: Grype October 13 and latest returned Trivy October 12. Other deployed images retain their existing audits.

[Audit](2026-10-13-network-flow.json), [VEX](2026-10-13-network-flow-vex.json), [deployment/browser results](2026-10-13-network-flow-deployment.json), [raw archive](2026-10-13-network-flow-raw.tar.gz). Archive SHA-256: `d77947a0ce9ffb6f9dc1707a4eac68889c437fbad23f1aff2fa7f9f12ef30391`. All 24 member hashes verified.
