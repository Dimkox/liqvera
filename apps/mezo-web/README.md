# Liqvera canonical browser

This Vite application is the `/v1/*` Mezo Testnet browser. The existing `/demo/*` fixture UI is a separate application. Serve this build and the gateway behind one origin; Vite's local development proxy expects the gateway at `127.0.0.1:8080`.

Install the exact package versions in `package.json`, then run `npm run build`. No wallet key, merchant secret, payment signature, or bearer capability belongs in build variables or logs. The app generates a 256-bit bearer capability and keeps its recovery record only in `sessionStorage`; closing the browser session may lose access to an existing report. The server remains the authority for entitlement, quote state, and finality.

The official x402 browser boundary is isolated in `src/x402.ts`. F1 pinned `@x402/core`, `@x402/evm`, and `@x402/paywall` 2.16.0, but did not verify a browser fetch or EIP-1193 signing API. The adapter therefore fails closed until the installed SDK API is reviewed in the deferred verification phase. The caller never constructs or replays a `PAYMENT-SIGNATURE`. Payment can be enabled only when the gateway advertises `payment_ready=true`, a live public quote matches the fixed Mezo Testnet terms, and the connected account matches the quote. After a payment request has entered a verified SDK, an unknown outcome remains locally blocked pending recovery; the UI never automatically repeats it.

Code is present but has not yet been installed, typechecked, built, browser-tested, or used for payment. The F3–F7 verification phase owns those checks and any SDK API adjustments required by the pinned installed package types.
