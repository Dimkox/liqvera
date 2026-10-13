# Wallet replacement — deployed verification

Source: `88ccb983deb4dc473998ffaf2a662e86078fa823`. Public service: https://liqvera.site, Mezo Testnet 31611.

## Reproduced failure and fix

A queued or in-flight event refresh from a replaced wallet could erase the newly connected account. Chrome against source a93605d reproduced the grey Request a report button and “Connect an injected wallet to continue” after a delayed old provider response. The event binding now invalidates queued reads and suppresses both successful and failed completions after unbinding. Account/network requirements and payment guards remain unchanged.

Three new regression cases failed before correction. All 40 browser tests and the Testnet build pass. Independent read-only code and rollout reviews found no blocker. The deployed Chrome check retains the new account and enabled request button after the same delayed response; a separate check creates a fresh report, reaches the signing provider and safely handles rejection. Providers are simulated. No physical Trust app, real signature or new payment was tested. The owner's exact phone sequence remains unconfirmed; this evidence establishes the reproduced application defect only.

## Deployment and security

Only the browser was replaced. The previous container and private manifest remain available for rollback. Public readiness returns ready=true and payment_ready=true.

Image: `sha256:53975c19727f90f9da1d55920a44aeaab3a4024340c9a1455186bb234105c971`. Public asset: `index-ZwsKs2Tu.js`.

npm audit: zero advisories. Trivy: zero raw findings. Grype: three CVE-2025-60876 package matches, dispositioned as fixed using the unchanged reviewed BusyBox binary hash. No new untriaged finding. The dependency lock is byte-identical to a93605d. Scanner databases were refreshed earlier in this October 13 session: Grype October 13, latest returned Trivy October 12. Other deployed images retain their existing exact-image evidence.

[Audit](2026-10-13-wallet-state.json), [VEX](2026-10-13-wallet-state-vex.json), [deployment/browser evidence](2026-10-13-wallet-state-deployment.json), [raw archive](2026-10-13-wallet-state-raw.tar.gz). Archive SHA-256: `5b027d0f2124daa5ddbb6768d990ab61ffd657c5729e56f427033018e451612e`. All 23 member hashes verified.
