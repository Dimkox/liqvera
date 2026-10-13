# Wallet-neutral guidance — deployed verification

Source `506b67608815b72cd906cf8ab46ae60585823732` is deployed at https://liqvera.site. Only the browser changed; the prior container and private manifest remain available for rollback.

Mobile guidance now describes the EVM wallet-browser route and labels the Trust Wallet shortcut optional. Discovery and signing remain EIP-6963/EIP-1193; the Trust namespace is a compatibility fallback. No new connector, dependency or payment behavior was introduced. WalletConnect sessions remain unimplemented.

All 42 web tests, the Testnet build and documentation checks pass. Real Chrome at a 390×844 viewport verifies the generic no-provider message. With a simulated ordinary window.ethereum provider and no Trust namespace, the deployed app prepares a fresh quote on the wrong chain with no signature, switches to Mezo after adding it, and handles signature rejection before submission. This is not a physical-wallet or real-payment acceptance.

Deployed image: `sha256:3ab707a276143dda374acd92bae5706adfcf5ced30ee6dc322ff11fc14e2efd9`. Public bundle: `index-gpixMnFZ.js`.

npm and Trivy report zero findings. Grype retains three reviewed BusyBox backport matches, verified against the unchanged patched binary. No new untriaged finding. Dependencies are byte-identical to ee2a19c. Scanner databases were refreshed earlier in this October 13 session; exact timestamps are recorded. Other deployed images retain their existing audits.

[Audit](2026-10-13-wallet-guidance.json), [VEX](2026-10-13-wallet-guidance-vex.json), [deployment/browser results](2026-10-13-wallet-guidance-deployment.json), [raw archive](2026-10-13-wallet-guidance-raw.tar.gz). Archive SHA-256: `3750b1811a0d20fd5285090cac4b54637d2caeff104d28c987e2d8b0ed380b92`. All 21 member hashes verified.
